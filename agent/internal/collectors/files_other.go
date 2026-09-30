//go:build !windows && !linux
// +build !windows,!linux

package collectors

import (
	"os"
	"time"
)

// getFileTimes extracts modification timestamp as fallback for other OS platforms.
func getFileTimes(fi os.FileInfo) (created, accessed, modified time.Time) {
	modified = fi.ModTime().UTC()
	created = modified
	accessed = modified
	return created, accessed, modified
}
