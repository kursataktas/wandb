package runbranching

import (
	"fmt"
	"strings"

	"github.com/wandb/segmentio-encoding/json"

	"github.com/wandb/wandb/core/internal/filestream"
	"github.com/wandb/wandb/core/internal/gql"
	"github.com/wandb/wandb/core/internal/runconfig"
	"github.com/wandb/wandb/core/pkg/observability"
	"github.com/wandb/wandb/core/pkg/service"
)

type Bucket = gql.RunResumeStatusModelProjectBucketRun

type Mode uint8

const (
	NoResume Mode = iota
	Must
	Allow
	Never
)

type ResumeState struct {
	State
	resume Mode
	logger *observability.CoreLogger
}

func ResumeMode(mode string) Mode {
	switch mode {
	case "must":
		return Must
	case "allow":
		return Allow
	case "never":
		return Never
	default:
		return NoResume
	}
}

func NewResumeState(
	project string,
	runId string,
	config *runconfig.RunConfig,
	tags []string,
	mode Mode,
	logger *observability.CoreLogger,
) *ResumeState {
	State := NewState(None, project, runId, config, tags)
	return &ResumeState{
		State:  *State,
		resume: mode,
		logger: logger,
	}

}

func RunHasStarted(bucket *Bucket) bool {
	// If bucket is nil, run doesn't exist yet
	// If bucket is non-nil but WandbConfig has no "t" key, the run exists but hasn't started
	// (e.g. a sweep run that was created ahead of time)
	return bucket != nil && bucket.WandbConfig != nil && strings.Contains(*bucket.WandbConfig, `"t":`)
}

func (r *ResumeState) Update(data *gql.RunResumeStatusResponse) (*service.RunUpdateResult, error) {

	var bucket *Bucket
	if data.GetModel() != nil && data.GetModel().GetBucket() != nil {
		bucket = data.GetModel().GetBucket()
	}

	// If we get that the run is not a resume run, we should fail if resume is set to must
	// for any other case of resume status, it is fine to ignore it
	// If we get that the run is a resume run, we should fail if resume is set to never
	// for any other case of resume status, we should continue to process the resume response
	switch {
	case !RunHasStarted(bucket) && r.resume != Must:
		return nil, nil
	case !RunHasStarted(bucket) && r.resume == Must:
		message := fmt.Sprintf(
			"You provided an invalid value for the `resume` argument."+
				" The value 'must' is not a valid option for resuming a run"+
				" (%s/%s) that has never been started. Please check your inputs and"+
				" try again with a valid value for the `resume` argument.\n"+
				"If you are trying to start a new run, please omit the"+
				" `resume` argument or use `resume='allow'`",
			r.Project, r.RunId)
		result := &service.RunUpdateResult{
			Error: &service.ErrorInfo{
				Message: message,
				Code:    service.ErrorInfo_USAGE,
			}}
		err := fmt.Errorf(
			"sender: Update: resume is 'must' for a run that does not exist")
		return result, err
	case r.resume == Never && RunHasStarted(bucket):
		message := fmt.Sprintf(
			"You provided an invalid value for the `resume` argument."+
				" The value 'never' is not a valid option for resuming a"+
				" run (%s/%s) that already exists. Please check your inputs"+
				" and try again with a valid value for the `resume` argument.\n",
			r.Project, r.RunId)
		result := &service.RunUpdateResult{
			Error: &service.ErrorInfo{
				Message: message,
				Code:    service.ErrorInfo_USAGE,
			}}
		err := fmt.Errorf(
			"sender: Update: resume is 'never' for a run that already exists")
		return result, err
	default:
		if err := r.update(bucket); err != nil && r.resume == Must {
			message := fmt.Sprintf(
				"The run (%s/%s) failed to resume, and the `resume` argument"+
					" was set to 'must'. Please check your inputs and try again"+
					" with a valid value for the `resume` argument.\n",
				r.Project, r.RunId)
			result := &service.RunUpdateResult{
				Error: &service.ErrorInfo{
					Message: message,
					Code:    service.ErrorInfo_UNKNOWN,
				},
			}
			return result, err
		}
		r.Type = Resume
		return nil, nil
	}
}

func (r *ResumeState) update(bucket *Bucket) error {
	var isErr bool

	r.AddOffset(filestream.HistoryChunk, *bucket.GetHistoryLineCount())
	if err := r.updateHistory(bucket); err != nil {
		r.logger.Error(err.Error())
		isErr = true
	}

	r.AddOffset(filestream.EventsChunk, *bucket.GetEventsLineCount())

	if err := r.updateSummary(bucket); err != nil {
		r.logger.Error(err.Error())
		isErr = true
	}

	r.AddOffset(filestream.OutputChunk, *bucket.GetLogLineCount())
	if err := r.updateConfig(bucket); err != nil {
		r.logger.Error(err.Error())
		isErr = true
	}

	if err := r.updateTags(bucket); err != nil {
		r.logger.Error(err.Error())
		isErr = true
	}

	if isErr {
		err := fmt.Errorf("sender: update: failed to update resume state")
		return err
	}

	return nil
}

func (r *ResumeState) updateHistory(bucket *Bucket) error {

	resumed := bucket.GetHistoryTail()
	if resumed == nil {
		err := fmt.Errorf(
			"sender: updateHistory: no history tail found in resume response")
		return err
	}

	var history []string
	if err := json.Unmarshal([]byte(*resumed), &history); err != nil {
		err = fmt.Errorf(
			"sender: updateHistory:failed to unmarshal history tail: %s", err)
		return err
	}

	if len(history) == 0 {
		return nil
	}

	var historyTail map[string]any
	if err := json.Unmarshal([]byte(history[0]), &historyTail); err != nil {
		err = fmt.Errorf(
			"sender: updateHistory: failed to unmarshal history tail map: %s",
			err)
		return err
	}

	if step, ok := historyTail["_step"].(float64); ok {
		// if we are resuming, we need to update the starting step
		// to be the next step after the last step we ran
		if step > 0 || r.GetFileStreamOffset()[filestream.HistoryChunk] > 0 {
			r.StartingStep = int64(step) + 1
		}
	}

	if runtime, ok := historyTail["_runtime"].(float64); ok {
		r.Runtime = int32(runtime)
	}

	return nil
}

func (r *ResumeState) updateSummary(bucket *Bucket) error {

	resumed := bucket.GetSummaryMetrics()
	if resumed == nil {
		err := fmt.Errorf(
			"sender: updateSummary: no summary metrics found in resume response")
		r.logger.Error(err.Error())
		return err
	}

	// If we are unable to parse the summary, we should fail if resume is set to
	// must for any other case of resume status, it is fine to ignore it
	// TODO: potential issue with unsupported types like NaN/Inf
	var summary map[string]interface{}
	if err := json.Unmarshal([]byte(*resumed), &summary); err != nil {
		err = fmt.Errorf(
			"sender: updateSummary: failed to unmarshal summary metrics: %s",
			err)
		return err
	}

	record := service.SummaryRecord{}
	for key, value := range summary {
		valueJson, _ := json.Marshal(value)
		record.Update = append(record.Update, &service.SummaryItem{
			Key:       key,
			ValueJson: string(valueJson),
		})
	}
	r.Summary = &record
	return nil
}

// Merges the original run's config into the current config.
func (r *ResumeState) updateConfig(bucket *Bucket) error {
	resumed := bucket.GetConfig()
	if resumed == nil {
		err := fmt.Errorf("sender: updateConfig: no config found in resume response")
		return err
	}

	// If we are unable to parse the config, we should fail if resume is set to
	// must for any other case of resume status, it is fine to ignore it
	// TODO: potential issue with unsupported types like NaN/Inf
	var cfg map[string]any

	if err := json.Unmarshal([]byte(*resumed), &cfg); err != nil {
		err = fmt.Errorf(
			"sender: updateConfig: failed to unmarshal config: %s", err)
		return err
	}

	deserializedConfig := make(map[string]any)
	for key, value := range cfg {
		valueDict, ok := value.(map[string]any)

		if !ok {
			r.logger.Error(
				fmt.Sprintf(
					"sender: updateConfig: config value for '%v'"+
						" is not a map[string]any",
					key,
				),
			)
		} else if val, ok := valueDict["value"]; ok {
			deserializedConfig[key] = val
		}
	}

	r.Config.MergeResumedConfig(deserializedConfig)
	return nil
}

func (r *ResumeState) updateTags(bucket *Bucket) error {
	resumed := bucket.GetTags()
	if resumed == nil {
		return nil
	}
	// handle tags
	// - when resuming a run, its tags will be overwritten by the tags
	//   passed to `wandb.init()`.
	// - to add tags to a resumed run without overwriting its existing tags
	//   use `run.tags += ["new_tag"]` after `wandb.init()`.
	if r.Tags == nil {
		r.Tags = append(r.Tags, resumed...)
	}
	return nil
}
