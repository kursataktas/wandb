package api

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/wandb/wandb/core/internal/settings"
)

// CredentialProvider adds Credentials to HTTP requests.
type CredentialProvider interface {
	// Apply sets the appropriate authorization headers or parameters on the
	// HTTP request.
	Apply(req *http.Request) error
}

// NewCredentialProvider creates a new credential provider based on the SDK
// settings. Settings for JWT authentication are prioritized above API key
// authentication
func NewCredentialProvider(
	settings *settings.Settings,
) (CredentialProvider, error) {
	if settings.GetIdentityTokenFile() != "" {
		return NewOAuth2CredentialProvider(settings)
	}
	return NewAPIKeyCredentialProvider(settings)
}

var _ CredentialProvider = &apiKeyCredentialProvider{}

// APIKeyCredentialProvider implements a credentials provider that authenticates
// requests using an API Key passed via HTTP Basic Authentication.
type apiKeyCredentialProvider struct {
	// The W&B API key
	apiKey string
}

// NewAPIKeyCredentialProvider ensures an API key exists and creates a new
// APIKeyCredentialProvider if so
func NewAPIKeyCredentialProvider(
	settings *settings.Settings,
) (CredentialProvider, error) {
	if err := settings.EnsureAPIKey(); err != nil {
		return nil, fmt.Errorf("couldn't get API key: %v", err)
	}

	return &apiKeyCredentialProvider{
		apiKey: settings.GetAPIKey(),
	}, nil
}

// Apply supplies the API key via the Authorization header to the request.
// The API key is supplied as the password, while the username field is left empty.
func (c *apiKeyCredentialProvider) Apply(req *http.Request) error {
	req.Header.Set(
		"Authorization",
		"Basic "+base64.StdEncoding.EncodeToString(
			[]byte("api:"+c.apiKey)),
	)
	return nil
}

var _ CredentialProvider = &oauth2CredentialProvider{}

func NewOAuth2CredentialProvider(
	settings *settings.Settings,
) (CredentialProvider, error) {
	return &oauth2CredentialProvider{
		baseURL:               settings.GetBaseURL(),
		identityTokenFilePath: settings.GetIdentityTokenFile(),
		credentialsFilePath:   settings.GetCredentialsFile(),
		mu:                    &sync.Mutex{},
	}, nil
}

// OAuth2CredentialProvider implements a credentials provider that exchanges a JWT
// for an access token via an authorization server. The access token is then used
// to authenticate API requests by including it in the Authorization header as a
// Bearer token.
//
// The JWT is supplied via a file path that is passed in as an environment
// variable. Once the token is received, it is persisted in the credentials file
// along with its expiration. The expiration is checked each time the access
// token is used, and refreshed if it is at or near expiration.
type oauth2CredentialProvider struct {
	// The URL of the W&B API
	baseURL string

	// The file path to the JWT
	identityTokenFilePath string

	// The file path to the access token and its metadata
	credentialsFilePath string

	// The access token and its metadata
	token tokenInfo

	mu *sync.Mutex
}

// ExpiresAt is a custom type representing a time.Time value. It is used to handle
// expiration times in a specific string format when serializing/deserializing JSON data.
type ExpiresAt time.Time

const expiresAtLayout = "2006-01-02 15:04:05"

func (e *ExpiresAt) UnmarshalJSON(data []byte) error {
	var timeString string
	if err := json.Unmarshal(data, &timeString); err != nil {
		return err
	}

	parsedTime, err := time.Parse(expiresAtLayout, timeString)
	if err != nil {
		return err
	}

	*e = ExpiresAt(parsedTime)
	return nil
}

func (e ExpiresAt) MarshalJSON() ([]byte, error) {
	formattedTime := time.Time(e).Format(expiresAtLayout)
	return json.Marshal(formattedTime)
}

type tokenInfo struct {
	// The time at which the token will expire
	ExpiresAt ExpiresAt `json:"expires_at"`

	// The access token to use for authentication
	AccessToken string `json:"access_token"`
}

func (c *tokenInfo) IsTokenExpiring() bool {
	return time.Until(time.Time(c.ExpiresAt)) <= time.Minute*5
}

// CredentialsFile is used when serializing/deserializing JSON data from the
// credentials file
type CredentialsFile struct {
	Credentials map[string]tokenInfo `json:"credentials"`
}

// Apply checks if the access token is expiring, and fetches a new one if so.
// It then supplies the access token to the request via the Authorization header
// as a Bearer token
func (c *oauth2CredentialProvider) Apply(req *http.Request) error {
	if c.token.IsTokenExpiring() {
		if err := c.loadCredentials(); err != nil {
			return err
		}
	}
	req.Header.Set(
		"Authorization",
		"Bearer "+c.token.AccessToken,
	)
	return nil
}

// loadCredentials attempts to load an access token from the credentials file.
// If the credentials file does not exist, it creates it.
func (c *oauth2CredentialProvider) loadCredentials() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	_, err := os.Stat(c.credentialsFilePath)
	if os.IsNotExist(err) {
		err = c.writeCredentialsFile()
	}
	if err != nil {
		return err
	}

	return c.loadCredentialsFromFile()
}

// loadCredentialsFromFile loads the access token from the credentials file. If
// the access token does not exist for the given base url, or the token is
// expiring, it fetches a new one from the server, and saves it to the credentials file
func (c *oauth2CredentialProvider) loadCredentialsFromFile() error {
	file, err := os.ReadFile(c.credentialsFilePath)
	if err != nil {
		return fmt.Errorf("failed to read credentials file: %v", err)
	}

	var credsFile CredentialsFile
	if err := json.Unmarshal(file, &credsFile); err != nil {
		return fmt.Errorf("failed to read credentials file: %v", err)
	}

	if credsFile.Credentials == nil {
		credsFile.Credentials = make(map[string]tokenInfo)
	}

	creds, ok := credsFile.Credentials[c.baseURL]

	if !ok || creds.IsTokenExpiring() {
		newCreds, err := c.createAccessToken()
		if err != nil {
			return err
		}
		credsFile.Credentials[c.baseURL] = *newCreds
		updatedFile, err := json.MarshalIndent(credsFile, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to update credentials file: %v", err)
		}
		err = os.WriteFile(c.credentialsFilePath, updatedFile, 0600)
		if err != nil {
			return fmt.Errorf("failed to update credentials file: %v", err)
		}
		c.token = *newCreds
	} else {
		c.token = creds
	}

	return nil
}

// writeCredentialsFile obtains an access token from the server and saves it
// to a credentials file
func (c *oauth2CredentialProvider) writeCredentialsFile() error {
	token, err := c.createAccessToken()
	if err != nil {
		return err
	}

	data := CredentialsFile{
		Credentials: map[string]tokenInfo{
			c.baseURL: *token,
		},
	}

	file, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to write credentials file: %v", err)
	}

	err = os.WriteFile(c.credentialsFilePath, file, 0600)
	if err != nil {
		return fmt.Errorf("failed to write credentials file: %v", err)
	}

	return nil
}

// createAccessToken reads the identity token from a file and exchanges it for
// an access token from the authorization server using the JWT Bearer flow defined
// in OAuth 2.0. The access token is then returned with its expiration time.
func (c *oauth2CredentialProvider) createAccessToken() (*tokenInfo, error) {
	token, err := os.ReadFile(c.identityTokenFilePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read identity token file: %v", err)
	}

	url := fmt.Sprintf("%s/oidc/token", c.baseURL)
	data := fmt.Sprintf("grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=%s", token)
	req, err := http.NewRequest("POST", url, strings.NewReader(data))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return nil, fmt.Errorf("failed to retrieve access token: %v", err)
		}
		return nil, fmt.Errorf("failed to retrieve access token: %s", string(body))
	}

	var tokenResponse struct {
		AccessToken string `json:"access_token"`
		ExpiresIn   int    `json:"expires_in"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&tokenResponse); err != nil {
		return nil, fmt.Errorf("invalid response from auth server: %v", err)
	}

	// calculate the time at which the token will expire from the expires_in seconds
	// from the response
	expiresAt := time.Now().UTC().Add(time.Duration(tokenResponse.ExpiresIn) * time.Second)

	return &tokenInfo{
		AccessToken: tokenResponse.AccessToken,
		ExpiresAt:   ExpiresAt(expiresAt),
	}, nil
}
