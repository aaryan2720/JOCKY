package collectors

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestFileCollectorMetadataAndSingleFile(t *testing.T) {
	tempDir := t.TempDir()
	testFile := filepath.Join(tempDir, "sample.txt")
	content := []byte("Hello JOCKY Forensics File System Collector!")
	if err := os.WriteFile(testFile, content, 0644); err != nil {
		t.Fatalf("Failed to write test file: %v", err)
	}

	expectedHashBytes := sha256.Sum256(content)
	expectedHash := hex.EncodeToString(expectedHashBytes[:])

	col := NewFileCollector()
	ctx := context.Background()

	// 1. Collect single file without hash
	reqNoHash := CollectionRequest{
		JobID:      "job-test-file-1",
		AgentID:    "agent-test-1",
		Target:     "files",
		Parameters: map[string]any{"path": testFile, "hash": false},
	}

	artifacts, err := col.Collect(ctx, reqNoHash)
	if err != nil {
		t.Fatalf("Collect failed: %v", err)
	}
	if len(artifacts) != 1 {
		t.Fatalf("Expected 1 artifact, got %d", len(artifacts))
	}

	art := artifacts[0]
	if art.Type != "file" {
		t.Errorf("Expected artifact type 'file', got '%s'", art.Type)
	}
	if art.JobID != "job-test-file-1" {
		t.Errorf("Expected job_id 'job-test-file-1', got '%s'", art.JobID)
	}

	data := art.Data
	if data["name"] != "sample.txt" {
		t.Errorf("Expected name 'sample.txt', got '%v'", data["name"])
	}
	if data["path"] != testFile {
		t.Errorf("Expected path '%s', got '%v'", testFile, data["path"])
	}
	if data["size"] != int64(len(content)) {
		t.Errorf("Expected size %d, got %v", len(content), data["size"])
	}
	if data["is_dir"] != false {
		t.Errorf("Expected is_dir false, got %v", data["is_dir"])
	}
	if data["extension"] != ".txt" {
		t.Errorf("Expected extension '.txt', got %v", data["extension"])
	}
	if _, ok := data["modified_at"]; !ok {
		t.Errorf("Expected modified_at timestamp")
	}
	if _, ok := data["created_at"]; !ok {
		t.Errorf("Expected created_at timestamp")
	}
	if _, ok := data["accessed_at"]; !ok {
		t.Errorf("Expected accessed_at timestamp")
	}
	if _, ok := data["sha256"]; ok {
		t.Errorf("sha256 should not be computed when hash=false")
	}

	// 2. Collect single file with SHA-256 hash
	reqWithHash := CollectionRequest{
		JobID:      "job-test-file-2",
		AgentID:    "agent-test-1",
		Target:     "files",
		Parameters: map[string]any{"path": testFile, "hash": true},
	}

	artifactsWithHash, err := col.Collect(ctx, reqWithHash)
	if err != nil {
		t.Fatalf("Collect with hash failed: %v", err)
	}
	if len(artifactsWithHash) != 1 {
		t.Fatalf("Expected 1 artifact, got %d", len(artifactsWithHash))
	}

	hashVal, ok := artifactsWithHash[0].Data["sha256"].(string)
	if !ok || hashVal == "" {
		t.Fatalf("Expected sha256 to be present in data, got %v", artifactsWithHash[0].Data["sha256"])
	}
	if hashVal != expectedHash {
		t.Errorf("Expected SHA-256 '%s', got '%s'", expectedHash, hashVal)
	}
}

func TestFileCollectorEmptyFileAndBinaryFileHashing(t *testing.T) {
	tempDir := t.TempDir()

	// Empty file
	emptyFile := filepath.Join(tempDir, "empty.bin")
	if err := os.WriteFile(emptyFile, []byte{}, 0644); err != nil {
		t.Fatalf("Failed to create empty file: %v", err)
	}
	expectedEmptySHA256 := "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

	// Binary file with bytes 0x00 through 0xFF
	binaryFile := filepath.Join(tempDir, "binary.bin")
	binData := make([]byte, 256)
	for i := 0; i < 256; i++ {
		binData[i] = byte(i)
	}
	if err := os.WriteFile(binaryFile, binData, 0644); err != nil {
		t.Fatalf("Failed to create binary file: %v", err)
	}
	expectedBinHashBytes := sha256.Sum256(binData)
	expectedBinSHA256 := hex.EncodeToString(expectedBinHashBytes[:])

	ctx := context.Background()
	col := NewFileCollector()

	// Verify empty file hash
	artsEmpty, err := col.Collect(ctx, CollectionRequest{
		Target:     "files",
		Parameters: map[string]any{"path": emptyFile, "hash": true},
	})
	if err != nil {
		t.Fatalf("Collect empty file failed: %v", err)
	}
	if artsEmpty[0].Data["sha256"] != expectedEmptySHA256 {
		t.Errorf("Expected empty file SHA-256 '%s', got '%v'", expectedEmptySHA256, artsEmpty[0].Data["sha256"])
	}

	// Verify binary file hash
	artsBin, err := col.Collect(ctx, CollectionRequest{
		Target:     "files",
		Parameters: map[string]any{"path": binaryFile, "hash": true},
	})
	if err != nil {
		t.Fatalf("Collect binary file failed: %v", err)
	}
	if artsBin[0].Data["sha256"] != expectedBinSHA256 {
		t.Errorf("Expected binary file SHA-256 '%s', got '%v'", expectedBinSHA256, artsBin[0].Data["sha256"])
	}
}

func TestFileCollectorDirectoryTraversalAndBounds(t *testing.T) {
	tempDir := t.TempDir()

	// Structure:
	// tempDir/
	//   file1.txt
	//   file2.log
	//   sub1/
	//     nested.txt
	//     sub2/
	//       deep.txt
	_ = os.WriteFile(filepath.Join(tempDir, "file1.txt"), []byte("file1"), 0644)
	_ = os.WriteFile(filepath.Join(tempDir, "file2.log"), []byte("file2"), 0644)
	sub1 := filepath.Join(tempDir, "sub1")
	_ = os.MkdirAll(sub1, 0755)
	_ = os.WriteFile(filepath.Join(sub1, "nested.txt"), []byte("nested"), 0644)
	sub2 := filepath.Join(sub1, "sub2")
	_ = os.MkdirAll(sub2, 0755)
	_ = os.WriteFile(filepath.Join(sub2, "deep.txt"), []byte("deep"), 0644)

	col := NewFileCollector()
	ctx := context.Background()

	// 1. Full traversal with hash
	artifacts, err := col.Collect(ctx, CollectionRequest{
		Target:     "files",
		Parameters: map[string]any{"path": tempDir, "hash": true},
	})
	if err != nil {
		t.Fatalf("Directory traversal failed: %v", err)
	}

	// Should contain sub1, sub1/sub2, and the files
	if len(artifacts) < 4 {
		t.Errorf("Expected at least 4 collected entries, got %d", len(artifacts))
	}

	foundNested := false
	for _, a := range artifacts {
		if a.Data["name"] == "nested.txt" {
			foundNested = true
			if a.Data["sha256"] == "" {
				t.Errorf("nested.txt missing expected sha256 hash")
			}
		}
	}
	if !foundNested {
		t.Errorf("Expected to find nested.txt in directory traversal")
	}

	// 2. MaxFiles limit test
	colBounded := NewFileCollector()
	boundedArts, err := colBounded.Collect(ctx, CollectionRequest{
		Target:     "files",
		Parameters: map[string]any{"path": tempDir, "max_files": 2},
	})
	if err != nil {
		t.Fatalf("Bounded collection failed: %v", err)
	}
	if len(boundedArts) > 2 {
		t.Errorf("Expected at most 2 artifacts due to max_files limit, got %d", len(boundedArts))
	}
}

func TestFileCollectorErrorsAndNonexistentPath(t *testing.T) {
	col := NewFileCollector()
	ctx := context.Background()

	nonExistent := filepath.Join(t.TempDir(), "does_not_exist_12345.bin")
	_, err := col.Collect(ctx, CollectionRequest{
		Target:     "files",
		Parameters: map[string]any{"path": nonExistent},
	})
	if err == nil {
		t.Errorf("Expected error when collecting nonexistent path, got nil")
	}
}

func TestFileCollectorContextCancellation(t *testing.T) {
	tempDir := t.TempDir()
	for i := 0; i < 20; i++ {
		_ = os.WriteFile(filepath.Join(tempDir, filepath.Base(t.Name())+"_file.txt"), []byte("data"), 0644)
	}

	col := NewFileCollector()
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Cancel immediately

	_, err := col.Collect(ctx, CollectionRequest{
		Target:     "files",
		Parameters: map[string]any{"path": tempDir},
	})

	if err == nil {
		t.Errorf("Expected context cancellation error, got nil")
	}
	if !strings.Contains(err.Error(), "context canceled") {
		t.Errorf("Expected context canceled error, got: %v", err)
	}
}

func TestExpandPath(t *testing.T) {
	// %TEMP% should expand to a non-empty path
	expandedTemp := ExpandPath("%TEMP%")
	if expandedTemp == "" || expandedTemp == "%TEMP%" {
		t.Errorf("Failed to expand %%TEMP%%: got %q", expandedTemp)
	}

	// Normal path should remain cleaned
	cleanPath := ExpandPath("/var/log")
	if cleanPath == "" {
		t.Errorf("ExpandPath returned empty for /var/log")
	}
}
