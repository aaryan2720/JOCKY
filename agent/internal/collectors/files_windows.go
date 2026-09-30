//go:build windows
// +build windows

package collectors

import (
	"os"
	"syscall"
	"time"
)

// getFileTimes extracts created, accessed, and modified timestamps from Windows FileInfo.
func getFileTimes(fi os.FileInfo) (created, accessed, modified time.Time) {
	modified = fi.ModTime().UTC()
	created = modified
	accessed = modified

	if sys := fi.Sys(); sys != nil {
		if winData, ok := sys.(*syscall.Win32FileAttributeData); ok {
			created = time.Unix(0, winData.CreationTime.Nanoseconds()).UTC()
			accessed = time.Unix(0, winData.LastAccessTime.Nanoseconds()).UTC()
			modified = time.Unix(0, winData.LastWriteTime.Nanoseconds()).UTC()
		}
	}
	return created, accessed, modified
}
