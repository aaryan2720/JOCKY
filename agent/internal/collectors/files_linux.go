//go:build linux
// +build linux

package collectors

import (
	"os"
	"syscall"
	"time"
)

// getFileTimes extracts access, change/status, and modification timestamps on Linux.
func getFileTimes(fi os.FileInfo) (created, accessed, modified time.Time) {
	modified = fi.ModTime().UTC()
	created = modified
	accessed = modified

	if sys := fi.Sys(); sys != nil {
		if stat, ok := sys.(*syscall.Stat_t); ok {
			accessed = time.Unix(stat.Atim.Sec, stat.Atim.Nsec).UTC()
			modified = time.Unix(stat.Mtim.Sec, stat.Mtim.Nsec).UTC()
			created = time.Unix(stat.Ctim.Sec, stat.Ctim.Nsec).UTC()
		}
	}
	return created, accessed, modified
}
