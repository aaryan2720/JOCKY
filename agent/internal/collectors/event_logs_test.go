package collectors

import (
	"context"
	"strings"
	"testing"
)

func TestParseWevtutilXML(t *testing.T) {
	xmlData := `<Events>
  <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
    <System>
      <Provider Name="Service Control Manager" Guid="{555908d1-a6d7-4695-8e1e-26931b2012f4}" EventSourceName="Service Control Manager"/>
      <EventID Qualifiers="16384">7036</EventID>
      <Version>0</Version>
      <Level>4</Level>
      <Task>0</Task>
      <Opcode>0</Opcode>
      <Keywords>0x8080000000000000</Keywords>
      <TimeCreated SystemTime="2026-09-30T09:45:12.1234567Z"/>
      <EventRecordID>104523</EventRecordID>
      <Correlation/>
      <Execution ProcessID="892" ThreadID="1204"/>
      <Channel>System</Channel>
      <Computer>FIN-SRV-01.corp.local</Computer>
      <Security/>
    </System>
    <RenderingInfo Culture="en-US">
      <Message>The Windows Update service entered the running state.</Message>
      <Level>Information</Level>
      <Task/>
      <Opcode>Info</Opcode>
      <ChannelDescription>System</ChannelDescription>
      <Provider>Service Control Manager</Provider>
      <Keywords/>
    </RenderingInfo>
  </Event>
  <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
    <System>
      <Provider Name="Microsoft-Windows-Security-Auditing"/>
      <EventID>4624</EventID>
      <Level>0</Level>
      <TimeCreated SystemTime="2026-09-30T09:46:00.0000000Z"/>
      <EventRecordID>104524</EventRecordID>
      <Channel>Security</Channel>
      <Computer>FIN-SRV-01.corp.local</Computer>
    </System>
    <EventData>
      <Data>S-1-5-18</Data>
      <Data>SYSTEM</Data>
      <Data>NT AUTHORITY</Data>
      <Data>0x3e7</Data>
    </EventData>
  </Event>
</Events>`

	entries := ParseWevtutilXML(xmlData, 10, 4096)
	if len(entries) != 2 {
		t.Fatalf("Expected 2 event log entries, got %d", len(entries))
	}

	// First event: System 7036
	e1 := entries[0]
	if e1.EventID != 7036 {
		t.Errorf("Expected EventID 7036, got %d", e1.EventID)
	}
	if e1.Provider != "Service Control Manager" {
		t.Errorf("Expected provider 'Service Control Manager', got '%s'", e1.Provider)
	}
	if e1.Channel != "System" {
		t.Errorf("Expected channel 'System', got '%s'", e1.Channel)
	}
	if e1.Level != "Information" {
		t.Errorf("Expected level 'Information', got '%s'", e1.Level)
	}
	if e1.RecordID != 104523 {
		t.Errorf("Expected RecordID 104523, got %d", e1.RecordID)
	}
	if e1.Computer != "FIN-SRV-01.corp.local" {
		t.Errorf("Expected computer 'FIN-SRV-01.corp.local', got '%s'", e1.Computer)
	}
	if !strings.Contains(e1.Message, "Windows Update") {
		t.Errorf("Expected message to contain 'Windows Update', got '%s'", e1.Message)
	}

	// Second event: Security 4624
	e2 := entries[1]
	if e2.EventID != 4624 {
		t.Errorf("Expected EventID 4624, got %d", e2.EventID)
	}
	if e2.Channel != "Security" {
		t.Errorf("Expected channel 'Security', got '%s'", e2.Channel)
	}
	if !strings.Contains(e2.Message, "SYSTEM") {
		t.Errorf("Expected EventData fallback message to contain 'SYSTEM', got '%s'", e2.Message)
	}
}

func TestParseWevtutilXML_BoundsAndMalformed(t *testing.T) {
	// Empty input
	empty := ParseWevtutilXML("", 10, 4096)
	if len(empty) != 0 {
		t.Errorf("Expected 0 entries for empty input, got %d", len(empty))
	}

	// Malformed XML
	malformed := ParseWevtutilXML("<invalid xml><unclosed>", 10, 4096)
	if len(malformed) != 0 {
		t.Errorf("Expected 0 entries for malformed input, got %d", len(malformed))
	}

	// Message size truncation
	singleEventXML := `<Event>
  <System>
    <EventID>100</EventID>
    <Channel>Application</Channel>
  </System>
  <RenderingInfo>
    <Message>This is a very long error message that exceeds the small maximum message size configured.</Message>
  </RenderingInfo>
</Event>`

	bounded := ParseWevtutilXML(singleEventXML, 10, 20)
	if len(bounded) != 1 {
		t.Fatalf("Expected 1 entry, got %d", len(bounded))
	}
	if !strings.HasSuffix(bounded[0].Message, "[truncated]") {
		t.Errorf("Expected truncated message, got '%s'", bounded[0].Message)
	}
}

func TestParseJournaldJSON(t *testing.T) {
	rawJSON := `{"__REALTIME_TIMESTAMP":"1727689200000000","_HOSTNAME":"ub-server-01","_SYSTEMD_UNIT":"sshd.service","PRIORITY":"3","MESSAGE":"Failed password for root from 192.168.1.100 port 44122","_PID":"4812"}
{"__REALTIME_TIMESTAMP":"1727689205000000","_HOSTNAME":"ub-server-01","SYSLOG_IDENTIFIER":"cron","PRIORITY":"6","MESSAGE":"(root) CMD (run-parts /etc/cron.hourly)","_PID":"4900"}
{"invalid json line"
`

	entries := ParseJournaldJSON(rawJSON, 10, 4096)
	if len(entries) != 2 {
		t.Fatalf("Expected 2 parsed journald entries, got %d", len(entries))
	}

	// Entry 1: sshd priority 3 (Error)
	e1 := entries[0]
	if e1.Provider != "sshd.service" {
		t.Errorf("Expected provider 'sshd.service', got '%s'", e1.Provider)
	}
	if e1.Level != "Error" {
		t.Errorf("Expected level 'Error' for priority 3, got '%s'", e1.Level)
	}
	if e1.Computer != "ub-server-01" {
		t.Errorf("Expected computer 'ub-server-01', got '%s'", e1.Computer)
	}
	if e1.RecordID != 4812 {
		t.Errorf("Expected RecordID/PID 4812, got %d", e1.RecordID)
	}
	if !strings.Contains(e1.Message, "Failed password") {
		t.Errorf("Expected message to contain 'Failed password', got '%s'", e1.Message)
	}

	// Entry 2: cron priority 6 (Information)
	e2 := entries[1]
	if e2.Provider != "cron" {
		t.Errorf("Expected provider 'cron', got '%s'", e2.Provider)
	}
	if e2.Level != "Information" {
		t.Errorf("Expected level 'Information' for priority 6, got '%s'", e2.Level)
	}
}

func TestParseSyslogContent(t *testing.T) {
	content := `# Syslog test file
Sep 30 10:15:32 linux-host systemd[1]: Started Daily apt upgrade.
Sep 30 10:16:01 linux-host CRON[5123]: (root) CMD (test -x /usr/sbin/anacron || { cd / && run-parts --report /etc/cron.daily; })
2026-09-30T10:17:00.000000+00:00 linux-host dockerd[999]: Container started container_id=a1b2c3d4
`

	entries := ParseSyslogContent(content, "syslog", 10, 4096)
	if len(entries) != 3 {
		t.Fatalf("Expected 3 parsed syslog entries, got %d", len(entries))
	}

	// Entry 1
	e1 := entries[0]
	if e1.Computer != "linux-host" {
		t.Errorf("Expected computer 'linux-host', got '%s'", e1.Computer)
	}
	if e1.Provider != "systemd[1]" {
		t.Errorf("Expected provider 'systemd[1]', got '%s'", e1.Provider)
	}
	if !strings.Contains(e1.Message, "Started Daily apt upgrade") {
		t.Errorf("Expected message to contain 'Started Daily apt upgrade', got '%s'", e1.Message)
	}

	// Entry 3 (ISO format)
	e3 := entries[2]
	if e3.Computer != "linux-host" {
		t.Errorf("Expected computer 'linux-host', got '%s'", e3.Computer)
	}
	if e3.Provider != "dockerd[999]" {
		t.Errorf("Expected provider 'dockerd[999]', got '%s'", e3.Provider)
	}
}

func TestEventLogCollectorBasicsAndCancellation(t *testing.T) {
	col := NewEventLogCollector()
	if col.Name() != "event_logs" {
		t.Errorf("Expected name 'event_logs', got '%s'", col.Name())
	}
	if !col.Supports("event_logs") || !col.Supports("event") || !col.Supports("logs") || !col.Supports("syslog") {
		t.Errorf("Expected Supports('event_logs'), Supports('syslog') to be true")
	}

	// Normal collection
	ctx := context.Background()
	artifacts, err := col.Collect(ctx, CollectionRequest{
		JobID:   "job-test-events-1",
		AgentID: "agent-test-1",
		Target:  "event_logs",
		Parameters: map[string]interface{}{
			"max_events": 5,
			"channel":    "System",
		},
	})
	if err != nil {
		t.Fatalf("Collect event_logs failed: %v", err)
	}
	if len(artifacts) == 0 {
		t.Fatal("Expected at least 1 event artifact, got 0")
	}

	art := artifacts[0]
	if art.Type != "event" {
		t.Errorf("Expected artifact type 'event', got '%s'", art.Type)
	}
	if _, ok := art.Data["channel"]; !ok {
		t.Errorf("Expected 'channel' field in event artifact data")
	}
	if _, ok := art.Data["message"]; !ok {
		t.Errorf("Expected 'message' field in event artifact data")
	}

	// Cancellation
	cancelCtx, cancel := context.WithCancel(context.Background())
	cancel()
	_, cErr := col.Collect(cancelCtx, CollectionRequest{Target: "event_logs"})
	if cErr == nil {
		t.Error("Expected error on cancelled context, got nil")
	}
}
