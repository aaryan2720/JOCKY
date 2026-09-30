package transport

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// HTTPTransport implements the Transport interface via authenticated HTTP REST endpoints.
type HTTPTransport struct {
	BaseURL    string
	AuthToken  string
	HTTPClient *http.Client
}

// NewHTTPTransport creates a new HTTP transport instance with standard timeouts.
func NewHTTPTransport(baseURL string, authToken string) *HTTPTransport {
	baseURL = strings.TrimRight(baseURL, "/")
	return &HTTPTransport{
		BaseURL:   baseURL,
		AuthToken: authToken,
		HTTPClient: &http.Client{
			Timeout: 15 * time.Second,
		},
	}
}

// Register sends enrollment request to the management server.
func (t *HTTPTransport) Register(ctx context.Context, req RegisterRequest) (*RegisterResponse, error) {
	url := fmt.Sprintf("%s/api/v1/agents/register", t.BaseURL)
	bodyBytes, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal register request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, fmt.Errorf("failed to create http request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")
	if t.AuthToken != "" {
		httpReq.Header.Set("Authorization", "Bearer "+t.AuthToken)
	}

	resp, err := t.HTTPClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("registration request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("server returned error status %d during registration: %s", resp.StatusCode, string(respBody))
	}

	var regResp RegisterResponse
	if err := json.NewDecoder(resp.Body).Decode(&regResp); err != nil {
		return nil, fmt.Errorf("failed to decode register response: %w", err)
	}

	return &regResp, nil
}

// SendHeartbeat dispatches a presence ping to the server for an enrolled agent.
func (t *HTTPTransport) SendHeartbeat(ctx context.Context, agentID string, req HeartbeatRequest) (*HeartbeatResponse, error) {
	url := fmt.Sprintf("%s/api/v1/agents/%s/heartbeat", t.BaseURL, agentID)
	bodyBytes, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal heartbeat request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, fmt.Errorf("failed to create http request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")
	if t.AuthToken != "" {
		httpReq.Header.Set("Authorization", "Bearer "+t.AuthToken)
	}

	resp, err := t.HTTPClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("heartbeat request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("server returned error status %d for heartbeat: %s", resp.StatusCode, string(respBody))
	}

	var hbResp HeartbeatResponse
	if err := json.NewDecoder(resp.Body).Decode(&hbResp); err != nil {
		return nil, fmt.Errorf("failed to decode heartbeat response: %w", err)
	}

	return &hbResp, nil
}

// PollJob retrieves pending forensic execution plans queued for the agent.
func (t *HTTPTransport) PollJob(ctx context.Context, agentID string) (*JobPollResponse, error) {
	url := fmt.Sprintf("%s/api/v1/agents/%s/jobs/poll", t.BaseURL, agentID)

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create http request: %w", err)
	}
	if t.AuthToken != "" {
		httpReq.Header.Set("Authorization", "Bearer "+t.AuthToken)
	}

	resp, err := t.HTTPClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("job poll request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNoContent {
		return &JobPollResponse{}, nil
	}

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("server returned error status %d during job poll: %s", resp.StatusCode, string(respBody))
	}

	var pollResp JobPollResponse
	if err := json.NewDecoder(resp.Body).Decode(&pollResp); err != nil {
		return nil, fmt.Errorf("failed to decode job poll response: %w", err)
	}

	return &pollResp, nil
}

// SubmitArtifacts uploads collected forensic evidence back to the server.
func (t *HTTPTransport) SubmitArtifacts(ctx context.Context, req ArtifactsSubmissionRequest) (*ArtifactsSubmissionResponse, error) {
	url := fmt.Sprintf("%s/api/v1/artifacts", t.BaseURL)
	bodyBytes, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal artifact submission: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(bodyBytes))
	if err != nil {
		return nil, fmt.Errorf("failed to create http request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")
	if t.AuthToken != "" {
		httpReq.Header.Set("Authorization", "Bearer "+t.AuthToken)
	}

	resp, err := t.HTTPClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("artifact submission request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("server returned error status %d during artifact submission: %s", resp.StatusCode, string(respBody))
	}

	var subResp ArtifactsSubmissionResponse
	if err := json.NewDecoder(resp.Body).Decode(&subResp); err != nil {
		return nil, fmt.Errorf("failed to decode artifact submission response: %w", err)
	}

	return &subResp, nil
}
