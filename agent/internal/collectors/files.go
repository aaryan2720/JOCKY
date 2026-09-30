package collectors

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

const (
	DefaultMaxFiles          = 500
	DefaultMaxDepth          = 5
	DefaultMaxFileSizeForHash = 50 * 1024 * 1024 // 50 MB
)

// FileEntry holds normalized file metadata.
type FileEntry struct {
	Path        string    `json:"path"`
	Name        string    `json:"name"`
	Size        int64     `json:"size"`
	IsDir       bool      `json:"is_dir"`
	Extension   string    `json:"extension"`
	Permissions string    `json:"permissions"`
	ModifiedAt  time.Time `json:"modified_at"`
	CreatedAt   time.Time `json:"created_at"`
	AccessedAt  time.Time `json:"accessed_at"`
	SHA256      string    `json:"sha256,omitempty"`
}

// FileCollector safely enumerates filesystem metadata and calculates SHA-256 hashes without modifying files.
type FileCollector struct {
	MaxFiles          int
	MaxDepth          int
	MaxFileSizeForHash int64
}

// NewFileCollector creates an initialized FileCollector with safe defaults.
func NewFileCollector() *FileCollector {
	return &FileCollector{
		MaxFiles:          DefaultMaxFiles,
		MaxDepth:          DefaultMaxDepth,
		MaxFileSizeForHash: DefaultMaxFileSizeForHash,
	}
}

func (c *FileCollector) Name() string {
	return "files"
}

func (c *FileCollector) Supports(target string) bool {
	t := strings.ToLower(strings.TrimSpace(target))
	return t == "files" || t == "file" || t == "hash"
}

// Collect inspects the specified path, safely traverses directories within bounds, and optionally computes SHA-256 hashes.
func (c *FileCollector) Collect(ctx context.Context, request CollectionRequest) ([]Artifact, error) {
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	targetPath := ""
	hashRequested := false

	// 1. Extract path and options from request parameters or conditions
	if request.Parameters != nil {
		if p, ok := request.Parameters["path"].(string); ok && p != "" {
			targetPath = p
		}
		if h, ok := request.Parameters["hash"].(bool); ok {
			hashRequested = h
		}
	}

	if request.Target == "hash" {
		hashRequested = true
	}

	if targetPath == "" {
		for _, cond := range request.Conditions {
			if strings.ToLower(cond.Field) == "path" && cond.Operator == "eq" {
				if s, ok := cond.Value.(string); ok && s != "" {
					targetPath = s
					break
				}
			}
		}
	}

	// Default fallback path if none provided
	if targetPath == "" {
		targetPath = os.TempDir()
	}

	expandedPath := ExpandPath(targetPath)

	maxFiles := c.MaxFiles
	if request.Parameters != nil {
		if mf, ok := request.Parameters["max_files"].(int); ok && mf > 0 {
			maxFiles = mf
		}
		if md, ok := request.Parameters["max_depth"].(int); ok && md > 0 {
			c.MaxDepth = md
		}
	}

	fi, err := os.Lstat(expandedPath)
	if err != nil {
		return nil, fmt.Errorf("failed to access path %q: %w", expandedPath, err)
	}

	var entries []FileEntry

	if !fi.IsDir() {
		// Single file collection
		entry, fErr := c.collectSingleFile(ctx, expandedPath, fi, hashRequested)
		if fErr != nil {
			return nil, fErr
		}
		entries = append(entries, entry)
	} else {
		// Directory traversal
		dirEntries, dErr := c.traverseDirectory(ctx, expandedPath, maxFiles, c.MaxDepth, hashRequested)
		if dErr != nil {
			return nil, dErr
		}
		entries = dirEntries
	}

	now := time.Now().UTC()
	artifacts := make([]Artifact, 0, len(entries))
	for _, e := range entries {
		data := map[string]interface{}{
			"path":        e.Path,
			"name":        e.Name,
			"size":        e.Size,
			"is_dir":      e.IsDir,
			"extension":   e.Extension,
			"permissions": e.Permissions,
			"modified_at": e.ModifiedAt.Format(time.RFC3339),
			"created_at":  e.CreatedAt.Format(time.RFC3339),
			"accessed_at": e.AccessedAt.Format(time.RFC3339),
		}
		if e.SHA256 != "" {
			data["sha256"] = e.SHA256
		}

		artifacts = append(artifacts, Artifact{
			JobID:       request.JobID,
			AgentID:     request.AgentID,
			Type:        "file",
			CollectedAt: now,
			Data:        data,
		})
	}

	return artifacts, nil
}

func (c *FileCollector) collectSingleFile(ctx context.Context, path string, fi os.FileInfo, hash bool) (FileEntry, error) {
	created, accessed, modified := getFileTimes(fi)
	ext := filepath.Ext(fi.Name())

	entry := FileEntry{
		Path:        path,
		Name:        fi.Name(),
		Size:        fi.Size(),
		IsDir:       fi.IsDir(),
		Extension:   ext,
		Permissions: fi.Mode().String(),
		ModifiedAt:  modified,
		CreatedAt:   created,
		AccessedAt:  accessed,
	}

	if hash && !fi.IsDir() {
		if c.MaxFileSizeForHash <= 0 || fi.Size() <= c.MaxFileSizeForHash {
			shaVal, err := ComputeFileSHA256(ctx, path)
			if err == nil {
				entry.SHA256 = shaVal
			}
		}
	}

	return entry, nil
}

func (c *FileCollector) traverseDirectory(ctx context.Context, rootDir string, maxFiles int, maxDepth int, hash bool) ([]FileEntry, error) {
	var results []FileEntry
	cleanRoot := filepath.Clean(rootDir)
	rootDepth := strings.Count(cleanRoot, string(filepath.Separator))

	err := filepath.WalkDir(cleanRoot, func(path string, d os.DirEntry, walkErr error) error {
		if ctx.Err() != nil {
			return ctx.Err()
		}

		if walkErr != nil {
			// Gracefully skip inaccessible files or directories without aborting full collection
			return nil
		}

		currentDepth := strings.Count(filepath.Clean(path), string(filepath.Separator)) - rootDepth
		if currentDepth > maxDepth {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		if path == cleanRoot {
			return nil
		}

		// Don't follow symlinks into directories to avoid recursion loops
		if d.Type()&os.ModeSymlink != 0 {
			if info, err := os.Stat(path); err == nil && info.IsDir() {
				return nil
			}
		}

		info, err := d.Info()
		if err != nil {
			return nil
		}

		entry, err := c.collectSingleFile(ctx, path, info, hash)
		if err != nil {
			return nil
		}

		results = append(results, entry)
		if len(results) >= maxFiles {
			return io.EOF // Sentinel to stop walking
		}

		return nil
	})

	if err != nil && err != io.EOF {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
		return nil, err
	}

	return results, nil
}

// ComputeFileSHA256 computes the SHA-256 hash using streaming reads without buffering whole file in memory.
func ComputeFileSHA256(ctx context.Context, filePath string) (string, error) {
	f, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer f.Close()

	hasher := sha256.New()
	buf := make([]byte, 64*1024)

	for {
		if ctx.Err() != nil {
			return "", ctx.Err()
		}
		n, rErr := f.Read(buf)
		if n > 0 {
			hasher.Write(buf[:n])
		}
		if rErr != nil {
			if rErr == io.EOF {
				break
			}
			return "", rErr
		}
	}

	return hex.EncodeToString(hasher.Sum(nil)), nil
}

var winEnvRegex = regexp.MustCompile(`%([a-zA-Z0-9_]+)%`)

// ExpandPath resolves Windows `%VAR%` and Unix `$VAR` environment variables.
func ExpandPath(path string) string {
	if path == "" {
		return ""
	}

	// Replace %VAR% style (Windows / JOCKY DSL standard)
	res := winEnvRegex.ReplaceAllStringFunc(path, func(match string) string {
		varName := strings.Trim(match, "%")
		val := os.Getenv(varName)
		if val != "" {
			return val
		}
		// Fallbacks for common special variables
		if strings.EqualFold(varName, "TEMP") || strings.EqualFold(varName, "TMP") {
			return os.TempDir()
		}
		return match
	})

	// Replace $VAR or ${VAR} style (POSIX)
	res = os.ExpandEnv(res)

	return filepath.Clean(res)
}
