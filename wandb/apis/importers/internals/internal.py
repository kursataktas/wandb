import itertools
import json
import logging
import math
import os
import queue
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from unittest.mock import MagicMock

import numpy as np
from google.protobuf.json_format import ParseDict
from rich.logging import RichHandler

from wandb import Artifact
from wandb.proto import wandb_internal_pb2 as pb
from wandb.proto import wandb_settings_pb2
from wandb.proto import wandb_telemetry_pb2 as telem_pb
from wandb.sdk.interface.interface import file_policy_to_enum
from wandb.sdk.interface.interface_queue import InterfaceQueue
from wandb.sdk.internal import context
from wandb.sdk.internal.sender import SendManager
from wandb.sdk.internal.settings_static import SettingsStatic
from wandb.sdk.internal.writer import WriteManager
from wandb.util import coalesce, recursive_cast_dictlike_to_dict

from .protocols import ImporterRun

# silences the internal messages; set to INFO or DEBUG to see them
logging.basicConfig(
    level=logging.WARN,
    handlers=[
        RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
    ],
)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)


@dataclass(frozen=True)
class SendManagerConfig:
    """Configure which parts of SendManager tooling to use."""

    use_artifacts: bool = False
    log_artifacts: bool = False
    metadata: bool = False
    files: bool = False
    media: bool = False
    code: bool = False
    history: bool = False
    summary: bool = False
    terminal_output: bool = False


@dataclass
class RecordMaker:
    run: ImporterRun
    interface: InterfaceQueue = InterfaceQueue()

    @property
    def run_dir(self) -> str:
        p = Path(f"./wandb-importer/{self.run.run_id()}/wandb")
        p.mkdir(parents=True, exist_ok=True)
        return f"./wandb-importer/{self.run.run_id()}"

    def make_artifacts_only_records(
        self,
        artifacts: Optional[Iterable[Artifact]] = None,
        used_artifacts: Optional[Iterable[Artifact]] = None,
    ) -> Iterable[pb.Record]:
        """Escape hatch to add extra artifacts to a run (e.g. run history artifacts)."""
        if used_artifacts:
            for art in used_artifacts:
                yield self._make_artifact_record(art, use_artifact=True)

        if artifacts:
            for art in artifacts:
                yield self._make_artifact_record(art)

    def make_records(
        self,
        config: SendManagerConfig,
    ) -> Iterable[pb.Record]:
        """Make all the records that constitute a run."""
        yield self._make_run_record()
        yield self._make_telem_record()

        has_artifacts = config.log_artifacts or config.use_artifacts
        yield self._make_files_record(
            config.metadata,
            has_artifacts,
            config.files,
            config.media,
            config.code,
        )

        if config.use_artifacts:
            if (used_artifacts := self.run.used_artifacts()) is not None:
                for artifact in used_artifacts:
                    yield self._make_artifact_record(artifact, use_artifact=True)

        if config.log_artifacts:
            if (artifacts := self.run.artifacts()) is not None:
                for artifact in artifacts:
                    yield self._make_artifact_record(artifact)

        if config.history:
            yield from self._make_history_records()

        if config.terminal_output:
            if (lines := self.run.logs()) is not None:
                for line in lines:
                    yield self._make_output_record(line)

    def _make_fake_run_record(self):
        """Make a fake run record.

        Unfortunately, the vanilla Run object does a check for existence on the server,
        so we use this as the simplest hack to skip that check.
        """
        # in this case run is a magicmock, so we need to convert the return types back to vanilla py types
        run = pb.RunRecord()
        run.entity = self.run.run.entity.return_value
        run.project = self.run.run.project.return_value
        run.run_id = self.run.run.run_id.return_value

        return self.interface._make_record(run=run)

    def _make_run_record(self) -> pb.Record:
        # unfortunate hack to get deleted wandb runs to work...
        if hasattr(self.run, "run") and isinstance(self.run.run, MagicMock):
            return self._make_fake_run_record()

        run = pb.RunRecord()
        run.run_id = self.run.run_id()
        run.entity = self.run.entity()
        run.project = self.run.project()
        run.display_name = coalesce(self.run.display_name())
        run.notes = coalesce(self.run.notes(), "")
        run.tags.extend(coalesce(self.run.tags(), []))
        run.start_time.FromMilliseconds(self.run.start_time())

        host = self.run.host()
        if host is not None:
            run.host = host

        runtime = self.run.runtime()
        if runtime is not None:
            run.runtime = runtime

        run_group = self.run.run_group()
        if run_group is not None:
            run.run_group = run_group

        config = self.run.config()
        if "_wandb" not in config:
            config["_wandb"] = {}

        # how do I get this automatically?
        config["_wandb"]["code_path"] = self.run.code_path()
        config["_wandb"]["python_version"] = self.run.python_version()
        config["_wandb"]["cli_version"] = self.run.cli_version()

        self.interface._make_config(
            data=config,
            obj=run.config,
        )  # is there a better way?
        return self.interface._make_record(run=run)

    def _make_output_record(self, line) -> pb.Record:
        output_raw = pb.OutputRawRecord()
        output_raw.output_type = pb.OutputRawRecord.OutputType.STDOUT
        output_raw.line = line
        return self.interface._make_record(output_raw=output_raw)

    def _make_summary_record(self) -> pb.Record:
        d: dict = {
            **self.run.summary(),
            "_runtime": self.run.runtime(),  # quirk of runtime -- it has to be here!
            # '_timestamp': self.run.start_time()/1000,
        }
        d = recursive_cast_dictlike_to_dict(d)
        summary = self.interface._make_summary_from_dict(d)
        return self.interface._make_record(summary=summary)

    def _make_history_records(self) -> Iterable[pb.Record]:
        for metrics in self.run.metrics():
            history = pb.HistoryRecord()
            for k, v in metrics.items():
                item = history.item.add()
                item.key = k
                # There seems to be some conversion issue to breaks when we try to re-upload.
                # np.NaN gets converted to float("nan"), which is not expected by our system.
                # If this cast to string (!) is not done, the row will be dropped.
                if (isinstance(v, float) and math.isnan(v)) or v == "NaN":
                    v = np.NaN

                if isinstance(v, bytes):
                    # it's a json string encoded as bytes
                    v = v.decode("utf-8")
                else:
                    v = json.dumps(v)

                item.value_json = v
            rec = self.interface._make_record(history=history)
            yield rec

    def _make_files_record(self, metadata, artifacts, files, media, code) -> pb.Record:
        files = self.run.files()
        metadata_fname = f"{self.run_dir}/files/wandb-metadata.json"
        if files is None:
            metadata_fname = self._make_metadata_file()
            files = [(metadata_fname, "end")]

        files_record = pb.FilesRecord()
        for path, policy in files:
            if not metadata and path == metadata_fname:
                continue
            if not artifacts and path.startswith("artifact/"):
                continue
            if not media and path.startswith("media/"):
                continue
            if not code and path.startswith("code/"):
                continue

            # DirWatcher requires the path to start with media/ instead of the full path
            if "media" in path:
                p = Path(path)
                path = str(p.relative_to(f"{self.run_dir}/files"))

            f = files_record.files.add()
            f.path = path
            f.policy = file_policy_to_enum(policy)

        return self.interface._make_record(files=files_record)

    def _make_artifact_record(self, artifact, use_artifact=False) -> pb.Record:
        proto = self.interface._make_artifact(artifact)
        proto.run_id = str(self.run.run_id())
        proto.project = str(self.run.project())
        proto.entity = str(self.run.entity())
        proto.user_created = use_artifact
        proto.use_after_commit = use_artifact
        proto.finalize = True

        aliases = artifact._aliases
        aliases += ["latest", "imported"]

        for alias in aliases:
            proto.aliases.append(alias)
        return self.interface._make_record(artifact=proto)

    def _make_telem_record(self) -> pb.Record:
        telem = telem_pb.TelemetryRecord()

        feature = telem_pb.Feature()
        feature.importer_mlflow = True
        telem.feature.CopyFrom(feature)

        cli_version = self.run.cli_version()
        if cli_version:
            telem.cli_version = cli_version

        python_version = self.run.python_version()
        if python_version:
            telem.python_version = python_version

        return self.interface._make_record(telemetry=telem)

    def _make_metadata_file(self) -> str:
        missing_text = "This data was not captured"

        d = {}
        d["os"] = coalesce(self.run.os_version(), missing_text)
        d["python"] = coalesce(self.run.python_version(), missing_text)
        d["program"] = coalesce(self.run.program(), missing_text)
        d["cuda"] = coalesce(self.run.cuda_version(), missing_text)
        d["host"] = coalesce(self.run.host(), missing_text)
        d["username"] = coalesce(self.run.username(), missing_text)
        d["executable"] = coalesce(self.run.executable(), missing_text)

        gpus_used = self.run.gpus_used()
        if gpus_used is not None:
            d["gpu_devices"] = json.dumps(gpus_used)
            d["gpu_count"] = json.dumps(len(gpus_used))

        cpus_used = self.run.cpus_used()
        if cpus_used is not None:
            d["cpu_count"] = json.dumps(self.run.cpus_used())

        mem_used = self.run.memory_used()
        if mem_used is not None:
            d["memory"] = json.dumps({"total": self.run.memory_used()})

        fname = f"{self.run_dir}/files/wandb-metadata.json"
        with open(fname, "w") as f:
            f.write(json.dumps(d))
        return fname


def _make_settings(
    root_dir: str, settings_override: Optional[Dict[str, Any]] = None
) -> SettingsStatic:
    _settings_override = coalesce(settings_override, {})

    default_settings: Dict[str, Any] = {
        "files_dir": os.path.join(root_dir, "files"),
        "root_dir": root_dir,
        "sync_file": os.path.join(root_dir, "txlog.wandb"),
        "resume": "false",
        "program": None,
        "ignore_globs": [],
        "disable_job_creation": True,
        "_start_time": 0,
        "_offline": None,
        "_sync": True,
        "_live_policy_rate_limit": 15,  # matches dir_watcher
        "_live_policy_wait_time": 600,  # matches dir_watcher
        "_async_upload_concurrency_limit": None,
        "_file_stream_timeout_seconds": 60,
    }

    combined_settings = {**default_settings, **_settings_override}
    settings_message = wandb_settings_pb2.Settings()
    ParseDict(combined_settings, settings_message)

    return SettingsStatic(settings_message)


def send_run(
    run: ImporterRun,
    *,
    extra_arts: Optional[Iterable[Artifact]] = None,
    extra_used_arts: Optional[Iterable[Artifact]] = None,
    config: Optional[SendManagerConfig] = None,
    overrides: Optional[Dict[str, Any]] = None,
    settings_override: Optional[Dict[str, Any]] = None,
) -> None:
    if config is None:
        config = SendManagerConfig()

    # does this need to be here for pmap?
    if overrides:
        for k, v in overrides.items():
            # `lambda: v` won't work!
            # https://stackoverflow.com/questions/10802002/why-deepcopy-doesnt-create-new-references-to-lambda-function
            setattr(run, k, lambda v=v: v)

    rm = RecordMaker(run)
    root_dir = rm.run_dir

    settings = _make_settings(root_dir, settings_override)
    sm_record_q = queue.Queue()
    wm_record_q = queue.Queue()
    result_q = queue.Queue()
    interface = InterfaceQueue(record_q=sm_record_q)
    context_keeper = context.ContextKeeper()
    sm = SendManager(settings, sm_record_q, result_q, interface, context_keeper)
    wm = WriteManager(
        settings, wm_record_q, result_q, sm_record_q, interface, context_keeper
    )

    records = rm.make_records(config)
    if extra_arts or extra_used_arts:
        extra_art_records = rm.make_artifacts_only_records(extra_arts, extra_used_arts)
        records = itertools.chain(records, extra_art_records)

    for r in records:
        # Write out to a transaction log
        # In a future update, we might want to make the incremental upload use the transaction log
        # and only send missing records.  For now, the transaction log just shows history of what
        # was sent to the server.
        wm.write(r)

        # Send to server
        sm.send(r)

    sm.finish()
    wm.finish()
