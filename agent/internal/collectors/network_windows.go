//go:build windows

package collectors

import (
	"context"
	"fmt"
	"net"
	"syscall"
	"unsafe"
)

var (
	modIphlpapi = syscall.NewLazyDLL("iphlpapi.dll")

	procGetExtendedTcpTable = modIphlpapi.NewProc("GetExtendedTcpTable")
	procGetExtendedUdpTable = modIphlpapi.NewProc("GetExtendedUdpTable")
)

const (
	AF_INET  = 2
	AF_INET6 = 23

	TCP_TABLE_OWNER_PID_ALL = 5
	UDP_TABLE_OWNER_PID     = 1

	ERROR_INSUFFICIENT_BUFFER = 122
)

type MIB_TCPROW_OWNER_PID struct {
	dwState      uint32
	dwLocalAddr  uint32
	dwLocalPort  uint32
	dwRemoteAddr uint32
	dwRemotePort uint32
	dwOwningPid  uint32
}

type MIB_UDPROW_OWNER_PID struct {
	dwLocalAddr uint32
	dwLocalPort uint32
	dwOwningPid uint32
}

func collectPlatformConnections(ctx context.Context) ([]NetworkConnectionInfo, error) {
	var results []NetworkConnectionInfo

	// 1. Collect IPv4 TCP Connections
	tcpConns, err := getWindowsTCPConnections(ctx)
	if err == nil {
		results = append(results, tcpConns...)
	}

	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	// 2. Collect IPv4 UDP Sockets
	udpConns, err := getWindowsUDPSockets(ctx)
	if err == nil {
		results = append(results, udpConns...)
	}

	return results, nil
}

func getWindowsTCPConnections(ctx context.Context) ([]NetworkConnectionInfo, error) {
	var size uint32
	// First call to determine required buffer size
	procGetExtendedTcpTable.Call(
		0,
		uintptr(unsafe.Pointer(&size)),
		0, // false: do not sort
		uintptr(AF_INET),
		uintptr(TCP_TABLE_OWNER_PID_ALL),
		0,
	)
	if size == 0 {
		return nil, nil
	}

	buf := make([]byte, size)
	ret, _, err := procGetExtendedTcpTable.Call(
		uintptr(unsafe.Pointer(&buf[0])),
		uintptr(unsafe.Pointer(&size)),
		0,
		uintptr(AF_INET),
		uintptr(TCP_TABLE_OWNER_PID_ALL),
		0,
	)
	if ret != 0 {
		return nil, fmt.Errorf("GetExtendedTcpTable failed with code %d: %w", ret, err)
	}

	numEntries := *(*uint32)(unsafe.Pointer(&buf[0]))
	if numEntries == 0 {
		return nil, nil
	}

	rowSize := unsafe.Sizeof(MIB_TCPROW_OWNER_PID{})
	results := make([]NetworkConnectionInfo, 0, numEntries)
	offset := unsafe.Sizeof(numEntries)

	for i := uint32(0); i < numEntries; i++ {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}

		rowPtr := unsafe.Pointer(uintptr(unsafe.Pointer(&buf[0])) + offset + uintptr(i)*rowSize)
		row := (*MIB_TCPROW_OWNER_PID)(rowPtr)

		localIP := intToIPv4(row.dwLocalAddr)
		remoteIP := intToIPv4(row.dwRemoteAddr)
		localPort := decodePort(row.dwLocalPort)
		remotePort := decodePort(row.dwRemotePort)
		stateStr := mapWindowsTCPState(row.dwState)

		results = append(results, NetworkConnectionInfo{
			Protocol:      "tcp",
			LocalAddress:  localIP.String(),
			LocalPort:     localPort,
			RemoteAddress: remoteIP.String(),
			RemotePort:    remotePort,
			State:         stateStr,
			PID:           int(row.dwOwningPid),
		})
	}

	return results, nil
}

func getWindowsUDPSockets(ctx context.Context) ([]NetworkConnectionInfo, error) {
	var size uint32
	procGetExtendedUdpTable.Call(
		0,
		uintptr(unsafe.Pointer(&size)),
		0,
		uintptr(AF_INET),
		uintptr(UDP_TABLE_OWNER_PID),
		0,
	)
	if size == 0 {
		return nil, nil
	}

	buf := make([]byte, size)
	ret, _, err := procGetExtendedUdpTable.Call(
		uintptr(unsafe.Pointer(&buf[0])),
		uintptr(unsafe.Pointer(&size)),
		0,
		uintptr(AF_INET),
		uintptr(UDP_TABLE_OWNER_PID),
		0,
	)
	if ret != 0 {
		return nil, fmt.Errorf("GetExtendedUdpTable failed with code %d: %w", ret, err)
	}

	numEntries := *(*uint32)(unsafe.Pointer(&buf[0]))
	if numEntries == 0 {
		return nil, nil
	}

	rowSize := unsafe.Sizeof(MIB_UDPROW_OWNER_PID{})
	results := make([]NetworkConnectionInfo, 0, numEntries)
	offset := unsafe.Sizeof(numEntries)

	for i := uint32(0); i < numEntries; i++ {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}

		rowPtr := unsafe.Pointer(uintptr(unsafe.Pointer(&buf[0])) + offset + uintptr(i)*rowSize)
		row := (*MIB_UDPROW_OWNER_PID)(rowPtr)

		localIP := intToIPv4(row.dwLocalAddr)
		localPort := decodePort(row.dwLocalPort)

		results = append(results, NetworkConnectionInfo{
			Protocol:      "udp",
			LocalAddress:  localIP.String(),
			LocalPort:     localPort,
			RemoteAddress: "0.0.0.0",
			RemotePort:    0,
			State:         "NONE",
			PID:           int(row.dwOwningPid),
		})
	}

	return results, nil
}

func decodePort(rawPort uint32) int {
	return int(((rawPort & 0xFF00) >> 8) | ((rawPort & 0x00FF) << 8))
}

func intToIPv4(addr uint32) net.IP {
	return net.IPv4(
		byte(addr&0xFF),
		byte((addr>>8)&0xFF),
		byte((addr>>16)&0xFF),
		byte((addr>>24)&0xFF),
	)
}

func mapWindowsTCPState(state uint32) string {
	switch state {
	case 1:
		return "CLOSED"
	case 2:
		return "LISTEN"
	case 3:
		return "SYN_SENT"
	case 4:
		return "SYN_RCVD"
	case 5:
		return "ESTABLISHED"
	case 6:
		return "FIN_WAIT1"
	case 7:
		return "FIN_WAIT2"
	case 8:
		return "CLOSE_WAIT"
	case 9:
		return "CLOSING"
	case 10:
		return "LAST_ACK"
	case 11:
		return "TIME_WAIT"
	case 12:
		return "DELETE_TCB"
	default:
		return fmt.Sprintf("STATE_%d", state)
	}
}
