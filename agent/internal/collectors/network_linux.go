//go:build linux

package collectors

import (
	"bufio"
	"context"
	"encoding/hex"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

func collectPlatformConnections(ctx context.Context) ([]NetworkConnectionInfo, error) {
	inodeToPID := buildLinuxSocketInodeMap()

	var results []NetworkConnectionInfo

	// 1. TCP IPv4
	if tcp, err := parseLinuxProcNetFile("/proc/net/tcp", "tcp", inodeToPID); err == nil {
		results = append(results, tcp...)
	}

	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	// 2. TCP IPv6
	if tcp6, err := parseLinuxProcNetFile("/proc/net/tcp6", "tcp6", inodeToPID); err == nil {
		results = append(results, tcp6...)
	}

	// 3. UDP IPv4
	if udp, err := parseLinuxProcNetFile("/proc/net/udp", "udp", inodeToPID); err == nil {
		results = append(results, udp...)
	}

	// 4. UDP IPv6
	if udp6, err := parseLinuxProcNetFile("/proc/net/udp6", "udp6", inodeToPID); err == nil {
		results = append(results, udp6...)
	}

	return results, nil
}

func parseLinuxProcNetFile(filePath string, protocol string, inodeMap map[string]int) ([]NetworkConnectionInfo, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var conns []NetworkConnectionInfo
	scanner := bufio.NewScanner(file)

	// Skip header line
	if scanner.Scan() {
		_ = scanner.Text()
	}

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		fields := strings.Fields(line)
		if len(fields) < 10 {
			continue
		}

		localAddr, localPort := parseLinuxHexIPPort(fields[1])
		remoteAddr, remotePort := parseLinuxHexIPPort(fields[2])
		stateHex := fields[3]
		inode := fields[9]

		stateStr := "NONE"
		if strings.HasPrefix(protocol, "tcp") {
			stateStr = mapLinuxTCPState(stateHex)
		}

		pid := inodeMap[inode]

		conns = append(conns, NetworkConnectionInfo{
			Protocol:      protocol,
			LocalAddress:  localAddr,
			LocalPort:     localPort,
			RemoteAddress: remoteAddr,
			RemotePort:    remotePort,
			State:         stateStr,
			PID:           pid,
		})
	}

	return conns, nil
}

func parseLinuxHexIPPort(hexStr string) (string, int) {
	parts := strings.Split(hexStr, ":")
	if len(parts) != 2 {
		return "0.0.0.0", 0
	}

	// Port hex to int
	portVal, _ := strconv.ParseInt(parts[1], 16, 32)

	// IPv4 hex parsing (8 hex chars)
	if len(parts[0]) == 8 {
		bytes, err := hex.DecodeString(parts[0])
		if err == nil && len(bytes) == 4 {
			// /proc/net/tcp stores in little-endian order
			ip := net.IPv4(bytes[3], bytes[2], bytes[1], bytes[0])
			return ip.String(), int(portVal)
		}
	} else if len(parts[0]) == 32 {
		// IPv6 (32 hex chars)
		bytes, err := hex.DecodeString(parts[0])
		if err == nil && len(bytes) == 16 {
			ip := net.IP(bytes)
			return ip.String(), int(portVal)
		}
	}

	return parts[0], int(portVal)
}

func mapLinuxTCPState(stateHex string) string {
	switch strings.ToUpper(stateHex) {
	case "01":
		return "ESTABLISHED"
	case "02":
		return "SYN_SENT"
	case "03":
		return "SYN_RECV"
	case "04":
		return "FIN_WAIT1"
	case "05":
		return "FIN_WAIT2"
	case "06":
		return "TIME_WAIT"
	case "07":
		return "CLOSE"
	case "08":
		return "CLOSE_WAIT"
	case "09":
		return "LAST_ACK"
	case "0A":
		return "LISTEN"
	case "0B":
		return "CLOSING"
	default:
		return fmt.Sprintf("STATE_%s", stateHex)
	}
}

// buildLinuxSocketInodeMap scans /proc/[pid]/fd/* symlinks to map socket inodes to PIDs.
func buildLinuxSocketInodeMap() map[string]int {
	inodeMap := make(map[string]int)

	procEntries, err := os.ReadDir("/proc")
	if err != nil {
		return inodeMap
	}

	for _, pEntry := range procEntries {
		if !pEntry.IsDir() {
			continue
		}
		pid, err := strconv.Atoi(pEntry.Name())
		if err != nil {
			continue
		}

		fdDir := fmt.Sprintf("/proc/%d/fd", pid)
		fdEntries, err := os.ReadDir(fdDir)
		if err != nil {
			continue
		}

		for _, fdEntry := range fdEntries {
			fdPath := filepath.Join(fdDir, fdEntry.Name())
			linkTarget, err := os.Readlink(fdPath)
			if err == nil && strings.HasPrefix(linkTarget, "socket:[") {
				inode := strings.TrimPrefix(linkTarget, "socket:[")
				inode = strings.TrimSuffix(inode, "]")
				if inode != "" {
					inodeMap[inode] = pid
				}
			}
		}
	}

	return inodeMap
}
