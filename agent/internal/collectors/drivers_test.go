package collectors

import (
	"context"
	"testing"
)

func TestParseDriverQueryCSV(t *testing.T) {
	csvData := `"Module Name","Display Name","Description","Driver Type","Start Mode","State","Status","Accept Stop","Accept Pause","Paged Pool(bytes)","Code(bytes)","BSS(bytes)","Link Date","Path","Init(bytes)"
"ACPI","Microsoft ACPI Driver","Microsoft ACPI Driver","Kernel ","Boot","Running","OK","TRUE","FALSE","20,480","516,096","0","12/10/2024 10:20:00","C:\Windows\system32\drivers\ACPI.sys","8,192"
"tcpip","TCP/IP Protocol Driver","TCP/IP Protocol Driver","Kernel ","System","Running","OK","TRUE","FALSE","36,864","2,548,960","0","12/10/2024 10:25:00","C:\Windows\system32\drivers\tcpip.sys","16,384"
"Wof","Windows Overlay File System Filter Driver","Windows Overlay File System Filter Driver","File System ","System","Running","OK","TRUE","FALSE","4,096","110,592","0","12/10/2024 10:30:00","C:\Windows\system32\drivers\Wof.sys","4,096"
`

	entries := ParseDriverQueryCSV(csvData)
	if len(entries) != 3 {
		t.Fatalf("Expected 3 driver entries, got %d", len(entries))
	}

	// 1. ACPI
	d1 := entries[0]
	if d1.Name != "ACPI" {
		t.Errorf("Expected name 'ACPI', got '%s'", d1.Name)
	}
	if d1.DisplayName != "Microsoft ACPI Driver" {
		t.Errorf("Expected display name 'Microsoft ACPI Driver', got '%s'", d1.DisplayName)
	}
	if d1.Path != "C:\\Windows\\system32\\drivers\\ACPI.sys" {
		t.Errorf("Expected path 'C:\\Windows\\system32\\drivers\\ACPI.sys', got '%s'", d1.Path)
	}
	if d1.Type != "Kernel" {
		t.Errorf("Expected type 'Kernel', got '%s'", d1.Type)
	}
	if d1.State != "Running" {
		t.Errorf("Expected state 'Running', got '%s'", d1.State)
	}

	// 2. Wof
	d3 := entries[2]
	if d3.Name != "Wof" {
		t.Errorf("Expected name 'Wof', got '%s'", d3.Name)
	}
	if d3.Type != "File System" {
		t.Errorf("Expected type 'File System', got '%s'", d3.Type)
	}
}

func TestParseProcModules(t *testing.T) {
	procModulesContent := `ext4 1003520 1 - Live 0xffffffffc0800000
crc16 16384 1 ext4, Live 0xffffffffc00a0000
mbcache 16384 1 ext4, Live 0xffffffffc0090000
jbd2 163840 1 ext4, Live 0xffffffffc0750000
usbcore 315392 3 uas,usb_storage,xhci_hcd, Live 0xffffffffc0520000
`

	entries := ParseProcModules(procModulesContent)
	if len(entries) != 5 {
		t.Fatalf("Expected 5 driver/module entries, got %d", len(entries))
	}

	// ext4
	e0 := entries[0]
	if e0.Name != "ext4" {
		t.Errorf("Expected name 'ext4', got '%s'", e0.Name)
	}
	if e0.Size != 1003520 {
		t.Errorf("Expected size 1003520, got %d", e0.Size)
	}
	if e0.UsageCount != 1 {
		t.Errorf("Expected usage_count 1, got %d", e0.UsageCount)
	}
	if len(e0.DependsOn) != 0 {
		t.Errorf("Expected empty depends_on for ext4, got %v", e0.DependsOn)
	}
	if e0.State != "Live" {
		t.Errorf("Expected state 'Live', got '%s'", e0.State)
	}

	// usbcore with multiple dependencies
	e4 := entries[4]
	if e4.Name != "usbcore" {
		t.Errorf("Expected name 'usbcore', got '%s'", e4.Name)
	}
	if len(e4.DependsOn) != 3 {
		t.Fatalf("Expected 3 dependencies for usbcore, got %d: %v", len(e4.DependsOn), e4.DependsOn)
	}
	if e4.DependsOn[0] != "uas" || e4.DependsOn[1] != "usb_storage" || e4.DependsOn[2] != "xhci_hcd" {
		t.Errorf("Unexpected dependencies for usbcore: %v", e4.DependsOn)
	}
}

func TestDriverCollectorBasicsAndCancellation(t *testing.T) {
	col := NewDriverCollector()
	if col.Name() != "drivers" {
		t.Errorf("Expected name 'drivers', got '%s'", col.Name())
	}
	if !col.Supports("drivers") || !col.Supports("driver") || !col.Supports("kernel_modules") {
		t.Errorf("Expected Supports('drivers'), Supports('driver') to be true")
	}

	// Normal collection
	ctx := context.Background()
	artifacts, err := col.Collect(ctx, CollectionRequest{
		JobID:   "job-test-drivers-1",
		AgentID: "agent-test-1",
		Target:  "drivers",
	})
	if err != nil {
		t.Fatalf("Collect drivers failed: %v", err)
	}
	if len(artifacts) == 0 {
		t.Fatal("Expected at least 1 driver artifact, got 0")
	}

	art := artifacts[0]
	if art.Type != "driver" {
		t.Errorf("Expected artifact type 'driver', got '%s'", art.Type)
	}
	if _, ok := art.Data["name"]; !ok {
		t.Errorf("Expected 'name' field in driver artifact data")
	}
	if _, ok := art.Data["state"]; !ok {
		t.Errorf("Expected 'state' field in driver artifact data")
	}

	// Cancellation
	cancelCtx, cancel := context.WithCancel(context.Background())
	cancel()
	_, cErr := col.Collect(cancelCtx, CollectionRequest{Target: "drivers"})
	if cErr == nil {
		t.Error("Expected error on cancelled context, got nil")
	}
}
