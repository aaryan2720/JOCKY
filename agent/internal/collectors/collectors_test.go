package collectors

import (
	"context"
	"strings"
	"testing"
)

// --- Registry Tests ---

func TestRegistryDefaults(t *testing.T) {
	reg := NewDefaultRegistry()
	names := reg.List()
	expected := []string{
		"autoruns",
		"connections",
		"drivers",
		"event_logs",
		"files",
		"processes",
		"scheduled_tasks",
		"services",
		"sessions",
		"users",
	}

	if len(names) != len(expected) {
		t.Fatalf("Expected %d registered collectors, got %d: %v", len(expected), len(names), names)
	}

	for _, exp := range expected {
		if _, ok := reg.Get(exp); !ok {
			t.Errorf("Expected collector '%s' to be registered", exp)
		}
	}
}

func TestRegistryIsPlaceholder(t *testing.T) {
	reg := NewDefaultRegistry()

	// Real collectors in Phase 6
	reals := []string{"autoruns", "scheduled_tasks", "users", "sessions", "processes", "connections"}
	for _, name := range reals {
		if reg.IsPlaceholder(name) {
			t.Errorf("Expected collector '%s' to be REAL, but reported as placeholder", name)
		}
	}

	// Placeholder collectors in Phase 6
	placeholders := []string{"files", "drivers", "services", "event_logs"}
	for _, name := range placeholders {
		if !reg.IsPlaceholder(name) {
			t.Errorf("Expected collector '%s' to be PLACEHOLDER, but reported as real", name)
		}
	}
}

func TestPlaceholderCollection(t *testing.T) {
	ctx := context.Background()
	p := NewPlaceholderCollector("files")
	artifacts, err := p.Collect(ctx, CollectionRequest{Target: "files"})
	if err != nil {
		t.Fatalf("Placeholder collection should never error, got: %v", err)
	}
	if len(artifacts) == 0 {
		t.Fatalf("Expected placeholder artifact metadata")
	}
	if artifacts[0].Data["status"] != "placeholder" {
		t.Errorf("Expected status 'placeholder', got: %v", artifacts[0].Data["status"])
	}
}

// --- Autoruns Tests ---

func TestAutorunParseRegQuery(t *testing.T) {
	fixture := `
HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run
    SecurityHealth    REG_EXPAND_SZ    %windir%\system32\SecurityHealthSystray.exe
    RealtekAudio      REG_SZ           "C:\Program Files\Realtek\Audio\RtkAud.exe" -s
`
	entries := ParseRegQueryOutput(fixture, "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", "SYSTEM")
	if len(entries) != 2 {
		t.Fatalf("Expected 2 autorun entries, got %d", len(entries))
	}

	if entries[0].Name != "SecurityHealth" || entries[0].Source != "registry" {
		t.Errorf("Unexpected entry 0: %+v", entries[0])
	}
	if !strings.Contains(entries[0].Command, "SecurityHealthSystray.exe") {
		t.Errorf("Expected command path in entry 0, got: %s", entries[0].Command)
	}

	if entries[1].Name != "RealtekAudio" || !entries[1].Enabled {
		t.Errorf("Unexpected entry 1: %+v", entries[1])
	}
}

func TestAutorunParseDesktopFile(t *testing.T) {
	fixture := `[Desktop Entry]
Type=Application
Name=Signal
Exec=/opt/Signal/signal-desktop --no-sandbox %U
Icon=signal-desktop
Comment=Private messaging
Terminal=false
`
	entry := ParseDesktopFile(fixture, "/etc/xdg/autostart/signal.desktop", "root")
	if entry == nil {
		t.Fatalf("Expected valid desktop entry parsed, got nil")
	}
	if entry.Name != "Signal" {
		t.Errorf("Expected name 'Signal', got '%s'", entry.Name)
	}
	if !strings.Contains(entry.Command, "signal-desktop") {
		t.Errorf("Expected command to contain 'signal-desktop', got '%s'", entry.Command)
	}
	if entry.Source != "xdg_autostart" || !entry.Enabled {
		t.Errorf("Unexpected entry fields: %+v", entry)
	}
}

func TestAutorunParseDesktopFile_Invalid(t *testing.T) {
	fixture := `[OtherSection]
Foo=Bar
`
	entry := ParseDesktopFile(fixture, "/etc/xdg/autostart/invalid.desktop", "root")
	if entry != nil {
		t.Errorf("Expected nil for invalid desktop entry without [Desktop Entry], got %+v", entry)
	}
}

func TestAutorunNormalization(t *testing.T) {
	c := NewAutorunCollector()
	if c.Name() != "autoruns" {
		t.Errorf("Expected name 'autoruns', got '%s'", c.Name())
	}
	artifacts, err := c.Collect(context.Background(), CollectionRequest{Target: "autoruns"})
	if err != nil {
		t.Fatalf("Autorun collection failed: %v", err)
	}
	for _, art := range artifacts {
		if art.Type != "autorun" {
			t.Errorf("Expected artifact type 'autorun', got '%s'", art.Type)
		}
		if _, ok := art.Data["location"]; !ok {
			t.Errorf("Missing 'location' field in autorun artifact")
		}
	}
}

// --- Scheduled Tasks Tests ---

func TestScheduledTasksParseCSV(t *testing.T) {
	fixture := `"HostName","TaskName","Next Run Time","Status","Logon Mode","Last Run Time","Last Result","Author","Task To Run","Start In","Comment","Scheduled Task State","Idle Time","Power Management","Run As User","Delete Task If Not Rescheduled","Stop Task If Runs X Hours/Mins","Schedule","Schedule Type","Start Time","Start Date","End Date","Days","Months","Repeat: Every","Repeat: Until: Time","Repeat: Until: Duration","Repeat: Stop If Still Running"
"DESKTOP-1","\GoogleUpdateTaskMachineUA","10/1/2026 12:00:00 AM","Ready","Interactive/Background","9/30/2026 12:00:00 AM","0","Google LLC","C:\Program Files (x86)\Google\Update\GoogleUpdate.exe /ua /installsource scheduler","N/A","N/A","Enabled","Disabled","Stop On Battery Mode, No Start On Batteries","SYSTEM","Disabled","72:00:00","Every 1 day(s)","Daily","12:00:00 AM","1/1/2020","N/A","N/A","N/A","Disabled","Disabled","Disabled","Disabled"
`
	entries := ParseSchtasksCSV(fixture)
	if len(entries) != 1 {
		t.Fatalf("Expected 1 scheduled task entry, got %d", len(entries))
	}

	task := entries[0]
	if task.Name != "\\GoogleUpdateTaskMachineUA" {
		t.Errorf("Expected task name '\\GoogleUpdateTaskMachineUA', got '%s'", task.Name)
	}
	if task.Author != "Google LLC" {
		t.Errorf("Expected author 'Google LLC', got '%s'", task.Author)
	}
	if !strings.Contains(task.Action, "GoogleUpdate.exe") {
		t.Errorf("Expected action containing 'GoogleUpdate.exe', got '%s'", task.Action)
	}
	if !task.Enabled {
		t.Errorf("Expected task to be enabled")
	}
}

func TestScheduledTasksParseCSV_Disabled(t *testing.T) {
	fixture := `"HostName","TaskName","Status","Task To Run"
"DESKTOP-1","\DisabledTask","Disabled","C:\Temp\tool.exe"
`
	entries := ParseSchtasksCSV(fixture)
	if len(entries) != 1 {
		t.Fatalf("Expected 1 entry, got %d", len(entries))
	}
	if entries[0].Enabled {
		t.Errorf("Expected task with Status 'Disabled' to have Enabled=false")
	}
}

func TestScheduledTasksParseCrontab(t *testing.T) {
	fixture := `# System crontab
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

17 * * * * root cd / && run-parts --report /etc/cron.hourly
25 6 * * * root test -x /usr/sbin/anacron || { cd / && run-parts --report /etc/cron.daily; }
0 2 * * 0 backup /usr/local/bin/backup.sh --full
`
	entries := ParseCrontab(fixture, "/etc/crontab")
	if len(entries) != 3 {
		t.Fatalf("Expected 3 cron entries parsed, got %d", len(entries))
	}

	if entries[0].User != "root" || entries[0].Trigger != "17 * * * *" {
		t.Errorf("Unexpected entry 0: %+v", entries[0])
	}
	if entries[2].User != "backup" || !strings.Contains(entries[2].Action, "backup.sh") {
		t.Errorf("Unexpected entry 2: %+v", entries[2])
	}
}

func TestScheduledTasksParseCronLine(t *testing.T) {
	line := "0 12 * * * root /usr/bin/certbot renew --quiet"
	entry, err := ParseCronLine(line, "/etc/cron.d/certbot")
	if err != nil || entry == nil {
		t.Fatalf("Failed to parse cron line: %v", err)
	}

	if entry.User != "root" {
		t.Errorf("Expected user 'root', got '%s'", entry.User)
	}
	if entry.Trigger != "0 12 * * *" {
		t.Errorf("Expected trigger '0 12 * * *', got '%s'", entry.Trigger)
	}
	if entry.Arguments != "renew --quiet" {
		t.Errorf("Expected arguments 'renew --quiet', got '%s'", entry.Arguments)
	}
}

func TestScheduledTasksNormalization(t *testing.T) {
	c := NewScheduledTaskCollector()
	if c.Name() != "scheduled_tasks" {
		t.Errorf("Expected name 'scheduled_tasks', got '%s'", c.Name())
	}
	artifacts, err := c.Collect(context.Background(), CollectionRequest{Target: "scheduled_tasks"})
	if err != nil {
		t.Fatalf("Scheduled tasks collection failed: %v", err)
	}
	for _, art := range artifacts {
		if art.Type != "scheduled_task" {
			t.Errorf("Expected artifact type 'scheduled_task', got '%s'", art.Type)
		}
		if _, ok := art.Data["action"]; !ok {
			t.Errorf("Missing 'action' field in scheduled task artifact")
		}
	}
}

// --- Users Tests ---

func TestUserParsePasswd(t *testing.T) {
	fixture := `root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
sysadmin:x:1001:1001:System Administrator,,,:/home/sysadmin:/bin/zsh
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
`
	entries := ParsePasswd(fixture)
	if len(entries) != 4 {
		t.Fatalf("Expected 4 user entries, got %d", len(entries))
	}

	// root
	if entries[0].Username != "root" || entries[0].UID != 0 || !entries[0].Enabled || entries[0].AccountType != "root" {
		t.Errorf("Unexpected root entry: %+v", entries[0])
	}

	// daemon (nologin => disabled)
	if entries[1].Username != "daemon" || entries[1].Enabled {
		t.Errorf("Expected daemon account to be disabled, got: %+v", entries[1])
	}

	// sysadmin
	if entries[2].Username != "sysadmin" || entries[2].UID != 1001 || !entries[2].Enabled || entries[2].AccountType != "local" {
		t.Errorf("Unexpected sysadmin entry: %+v", entries[2])
	}
}

func TestUserParsePasswd_DisabledShell(t *testing.T) {
	fixture := `svc_app:x:999:999:Service Account:/var/lib/app:/bin/false
`
	entries := ParsePasswd(fixture)
	if len(entries) != 1 {
		t.Fatalf("Expected 1 entry, got %d", len(entries))
	}
	if entries[0].Enabled {
		t.Errorf("Account with /bin/false shell should be marked Enabled=false")
	}
}

func TestUserParseNetUserList(t *testing.T) {
	fixture := `User accounts for \\DESKTOP-1

-------------------------------------------------------------------------------
Administrator            DefaultAccount           Guest                    
WDAGUtilityAccount       uzair                    
The command completed successfully.
`
	entries := ParseNetUserList(fixture)
	if len(entries) < 4 {
		t.Fatalf("Expected at least 4 users parsed from net user, got %d", len(entries))
	}

	usernames := make(map[string]bool)
	for _, u := range entries {
		usernames[u.Username] = true
	}

	if !usernames["Administrator"] || !usernames["Guest"] || !usernames["uzair"] {
		t.Errorf("Missing expected users in parsed list: %+v", entries)
	}
}

func TestUserNormalization(t *testing.T) {
	c := NewUserCollector()
	if c.Name() != "users" {
		t.Errorf("Expected name 'users', got '%s'", c.Name())
	}
	artifacts, err := c.Collect(context.Background(), CollectionRequest{Target: "users"})
	if err != nil {
		t.Fatalf("User collection failed: %v", err)
	}
	for _, art := range artifacts {
		if art.Type != "user" {
			t.Errorf("Expected artifact type 'user', got '%s'", art.Type)
		}
		if _, ok := art.Data["username"]; !ok {
			t.Errorf("Missing 'username' field in user artifact")
		}
	}
}

// --- Sessions Tests ---

func TestSessionParseQwinsta(t *testing.T) {
	fixture := ` SESSIONNAME       USERNAME                 ID  STATE    TYPE        DEVICE 
 services                                    0  Disc
>console           Alice                     1  Active
 rdp-tcp#0         Bob                       2  Active
`
	entries := ParseQwinstaOutput(fixture)
	if len(entries) != 3 {
		t.Fatalf("Expected 3 session entries, got %d", len(entries))
	}

	if entries[1].Username != "Alice" || entries[1].SessionID != "1" || entries[1].State != "Active" || entries[1].LogonType != "Console" {
		t.Errorf("Unexpected console session entry: %+v", entries[1])
	}
	if entries[2].Username != "Bob" || entries[2].SessionID != "2" || entries[2].LogonType != "RDP" {
		t.Errorf("Unexpected RDP session entry: %+v", entries[2])
	}
}

func TestSessionParseWho(t *testing.T) {
	fixture := `alice    tty1         2026-09-30 08:30 (:0)
bob      pts/0        2026-09-30 09:15 (192.168.1.50)
`
	entries := ParseWhoOutput(fixture)
	if len(entries) != 2 {
		t.Fatalf("Expected 2 session entries, got %d", len(entries))
	}

	if entries[0].Username != "alice" || entries[0].Terminal != "tty1" || entries[0].LogonType != "Console" {
		t.Errorf("Unexpected tty1 session: %+v", entries[0])
	}
	if entries[1].Username != "bob" || entries[1].Terminal != "pts/0" || entries[1].LogonType != "PTS" || entries[1].Source != "192.168.1.50" {
		t.Errorf("Unexpected pts/0 session: %+v", entries[1])
	}
}

func TestSessionNormalization(t *testing.T) {
	c := NewSessionCollector()
	if c.Name() != "sessions" {
		t.Errorf("Expected name 'sessions', got '%s'", c.Name())
	}
	artifacts, err := c.Collect(context.Background(), CollectionRequest{Target: "sessions"})
	if err != nil {
		t.Fatalf("Session collection failed: %v", err)
	}
	for _, art := range artifacts {
		if art.Type != "session" {
			t.Errorf("Expected artifact type 'session', got '%s'", art.Type)
		}
		if _, ok := art.Data["username"]; !ok {
			t.Errorf("Missing 'username' field in session artifact")
		}
	}
}

// --- Process and Connection Parser Tests ---

func TestProcessParseTasklist(t *testing.T) {
	fixture := `"Image Name","PID","Session Name","Session#","Mem Usage","Status","User Name","CPU Time","Window Title"
"System Idle Process","0","Services","0","8 K","Unknown","NT AUTHORITY\SYSTEM","0:00:00","N/A"
"System","4","Services","0","156 K","Unknown","NT AUTHORITY\SYSTEM","0:00:00","N/A"
"explorer.exe","3100","Console","1","50,000 K","Running","DESKTOP-1\uzair","0:00:15","N/A"
`
	entries := ParseTasklistCSV(fixture)
	if len(entries) != 3 {
		t.Fatalf("Expected 3 process entries, got %d", len(entries))
	}
	if entries[2].Name != "explorer.exe" || entries[2].PID != 3100 || entries[2].User != "DESKTOP-1\\uzair" {
		t.Errorf("Unexpected process entry: %+v", entries[2])
	}
}

func TestProcessParseLinuxPs(t *testing.T) {
	fixture := `  PID  PPID USER     COMMAND
    1     0 root     /sbin/init splash
  500     1 root     /usr/lib/systemd/systemd-journald
 1200   500 syslog   /usr/sbin/rsyslogd -n -iNONE
`
	entries := ParseLinuxPsOutput(fixture)
	if len(entries) != 3 {
		t.Fatalf("Expected 3 entries, got %d", len(entries))
	}
	if entries[0].PID != 1 || entries[0].PPID != 0 || entries[0].User != "root" || entries[0].Name != "init" {
		t.Errorf("Unexpected entry 0: %+v", entries[0])
	}
}

func TestConnectionParseNetstat(t *testing.T) {
	fixture := `
Active Connections

  Proto  Local Address          Foreign Address        State           PID
  TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       904
  TCP    192.168.1.100:54321    142.250.190.46:443     ESTABLISHED     4812
  UDP    0.0.0.0:5353           *:*                                    1200
`
	entries := ParseNetstatOutput(fixture)
	if len(entries) != 3 {
		t.Fatalf("Expected 3 connections, got %d", len(entries))
	}
	if entries[1].Protocol != "TCP" || entries[1].LocalPort != 54321 || entries[1].RemotePort != 443 || entries[1].PID != 4812 {
		t.Errorf("Unexpected connection entry: %+v", entries[1])
	}
}

func TestConnectionParseLinuxNetstat(t *testing.T) {
	fixture := `Proto Recv-Q Send-Q Local Address           Foreign Address         State      
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN     
tcp        0      0 10.0.0.5:45678          198.51.100.1:4444       ESTABLISHED
`
	entries := ParseLinuxNetstatOutput(fixture)
	if len(entries) != 2 {
		t.Fatalf("Expected 2 connections, got %d", len(entries))
	}
	if entries[1].LocalPort != 45678 || entries[1].RemotePort != 4444 || entries[1].State != "ESTABLISHED" {
		t.Errorf("Unexpected connection entry: %+v", entries[1])
	}
}
