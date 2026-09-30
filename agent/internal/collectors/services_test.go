package collectors

import (
	"context"
	"strings"
	"testing"
)

func TestParseScQueryOutput(t *testing.T) {
	rawOutput := `
SERVICE_NAME: wuauserv
DISPLAY_NAME: Windows Update
        TYPE               : 20  WIN32_SHARE_PROCESS
        STATE              : 4  RUNNING
                                (STOPPABLE, NOT_PAUSABLE, ACCEPTS_SHUTDOWN)
        WIN32_EXIT_CODE    : 0  (0x0)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0

SERVICE_NAME: XboxGipSvc
DISPLAY_NAME: Xbox Accessory Management Service
        TYPE               : 30  WIN32
        STATE              : 1  STOPPED
        WIN32_EXIT_CODE    : 1077  (0x435)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0
`

	entries := ParseScQueryOutput(rawOutput)
	if len(entries) != 2 {
		t.Fatalf("Expected 2 service entries, got %d", len(entries))
	}

	// First service
	s1 := entries[0]
	if s1.Name != "wuauserv" {
		t.Errorf("Expected name 'wuauserv', got '%s'", s1.Name)
	}
	if s1.DisplayName != "Windows Update" {
		t.Errorf("Expected display name 'Windows Update', got '%s'", s1.DisplayName)
	}
	if s1.Status != "running" {
		t.Errorf("Expected status 'running', got '%s'", s1.Status)
	}
	if s1.Source != "windows_service" {
		t.Errorf("Expected source 'windows_service', got '%s'", s1.Source)
	}

	// Second service
	s2 := entries[1]
	if s2.Name != "XboxGipSvc" {
		t.Errorf("Expected name 'XboxGipSvc', got '%s'", s2.Name)
	}
	if s2.Status != "stopped" {
		t.Errorf("Expected status 'stopped', got '%s'", s2.Status)
	}
}

func TestParseSystemctlListUnits(t *testing.T) {
	rawOutput := `
  UNIT                                  LOAD   ACTIVE SUB     DESCRIPTION
● bad.service                           loaded failed failed  Faulty Service
  cron.service                          loaded active running Regular background program processing daemon
  dbus.service                          loaded active running D-Bus System Message Bus
  ssh.service                           loaded active running OpenBSD Secure Shell server
  systemd-journald.socket               loaded active running Journal Socket
`

	entries := ParseSystemctlListUnits(rawOutput)
	if len(entries) != 4 {
		t.Fatalf("Expected 4 service entries (.service units only), got %d", len(entries))
	}

	// First entry
	e0 := entries[0]
	if e0.Name != "bad" {
		t.Errorf("Expected name 'bad', got '%s'", e0.Name)
	}
	if e0.DisplayName != "bad.service" {
		t.Errorf("Expected display name 'bad.service', got '%s'", e0.DisplayName)
	}
	if e0.Status != "failed" {
		t.Errorf("Expected status 'failed', got '%s'", e0.Status)
	}

	// Cron entry
	e1 := entries[1]
	if e1.Name != "cron" {
		t.Errorf("Expected name 'cron', got '%s'", e1.Name)
	}
	if e1.Status != "active/running" {
		t.Errorf("Expected status 'active/running', got '%s'", e1.Status)
	}
	if !strings.Contains(e1.Description, "background program") {
		t.Errorf("Expected description to contain 'background program', got '%s'", e1.Description)
	}
}

func TestParseSystemdUnitFile(t *testing.T) {
	unitContent := `
[Unit]
Description=OpenBSD Secure Shell server
Documentation=man:sshd(8) man:sshd_config(5)
After=network.target auditd.service
ConditionPathExists=!/etc/ssh/sshd_not_to_be_run

[Service]
EnvironmentFile=-/etc/default/ssh
ExecStartPre=/usr/sbin/sshd -t
ExecStart=/usr/sbin/sshd -D $SSHD_OPTS
ExecReload=/usr/sbin/sshd -t
KillMode=process
Restart=on-failure
RestartPreventExitStatus=255
Type=notify
RuntimeDirectory=sshd
RuntimeDirectoryMode=0755
User=root

[Install]
WantedBy=multi-user.target
Alias=sshd.service
`

	entry := ParseSystemdUnitFile(unitContent, "ssh.service")
	if entry == nil {
		t.Fatal("Expected parsed service entry, got nil")
	}

	if entry.Name != "ssh" {
		t.Errorf("Expected name 'ssh', got '%s'", entry.Name)
	}
	if entry.Path != "/usr/sbin/sshd -D $SSHD_OPTS" {
		t.Errorf("Expected ExecStart path, got '%s'", entry.Path)
	}
	if entry.User != "root" {
		t.Errorf("Expected user 'root', got '%s'", entry.User)
	}
	if entry.Description != "OpenBSD Secure Shell server" {
		t.Errorf("Expected description 'OpenBSD Secure Shell server', got '%s'", entry.Description)
	}
}

func TestServiceCollectorBasicsAndCancellation(t *testing.T) {
	col := NewServiceCollector()
	if col.Name() != "services" {
		t.Errorf("Expected name 'services', got '%s'", col.Name())
	}
	if !col.Supports("services") || !col.Supports("service") {
		t.Errorf("Expected Supports('services') and Supports('service') to be true")
	}

	// Normal collection
	ctx := context.Background()
	artifacts, err := col.Collect(ctx, CollectionRequest{
		JobID:   "job-test-services-1",
		AgentID: "agent-test-1",
		Target:  "services",
	})
	if err != nil {
		t.Fatalf("Collect services failed: %v", err)
	}
	if len(artifacts) == 0 {
		t.Fatal("Expected at least 1 service artifact, got 0")
	}

	art := artifacts[0]
	if art.Type != "service" {
		t.Errorf("Expected artifact type 'service', got '%s'", art.Type)
	}
	if _, ok := art.Data["name"]; !ok {
		t.Errorf("Expected 'name' field in service artifact data")
	}
	if _, ok := art.Data["status"]; !ok {
		t.Errorf("Expected 'status' field in service artifact data")
	}

	// Cancellation
	cancelCtx, cancel := context.WithCancel(context.Background())
	cancel()
	_, cErr := col.Collect(cancelCtx, CollectionRequest{Target: "services"})
	if cErr == nil {
		t.Error("Expected error on cancelled context, got nil")
	}
}
