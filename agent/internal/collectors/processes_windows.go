//go:build windows

package collectors

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"syscall"
	"unsafe"
)

var (
	modKernel32 = syscall.NewLazyDLL("kernel32.dll")
	modAdvapi32 = syscall.NewLazyDLL("advapi32.dll")
	modWintrust = syscall.NewLazyDLL("wintrust.dll")

	procCreateToolhelp32Snapshot = modKernel32.NewProc("CreateToolhelp32Snapshot")
	procProcess32FirstW          = modKernel32.NewProc("Process32FirstW")
	procProcess32NextW           = modKernel32.NewProc("Process32NextW")
	procOpenProcess              = modKernel32.NewProc("OpenProcess")
	procQueryFullProcessImageNameW = modKernel32.NewProc("QueryFullProcessImageNameW")
	procCloseHandle              = modKernel32.NewProc("CloseHandle")

	procOpenProcessToken         = modAdvapi32.NewProc("OpenProcessToken")
	procGetTokenInformation      = modAdvapi32.NewProc("GetTokenInformation")
	procLookupAccountSidW        = modAdvapi32.NewProc("LookupAccountSidW")

	procWinVerifyTrust           = modWintrust.NewProc("WinVerifyTrust")
)

const (
	TH32CS_SNAPPROCESS = 0x00000002

	PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
	PROCESS_QUERY_INFORMATION         = 0x0400
	PROCESS_VM_READ                   = 0x0010

	TOKEN_QUERY = 0x0008
	TokenUser   = 1

	INVALID_HANDLE_VALUE = ^uintptr(0)

	WTD_CHOICE_FILE               = 1
	WTD_UI_NONE                   = 2
	WTD_REVOKE_NONE               = 0
	WTD_STATEACTION_IGNORE        = 0
	WTD_REVOCATION_CHECK_NONE     = 0x00000010
	WTD_CACHE_ONLY_URL_RETRIEVAL  = 0x00001000
	WTD_SAFER_FLAG                = 0x00000100
)

// PROCESSENTRY32W represents process snapshot entry in Win32 API.
type PROCESSENTRY32W struct {
	dwSize              uint32
	cntUsage            uint32
	th32ProcessID       uint32
	th32DefaultHeapID   uintptr
	th32ModuleID        uint32
	cntThreads          uint32
	th32ParentProcessID uint32
	pcPriClassBase      int32
	dwFlags             uint32
	szExeFile           [260]uint16
}

type SID_AND_ATTRIBUTES struct {
	Sid        uintptr
	Attributes uint32
}

type TOKEN_USER struct {
	User SID_AND_ATTRIBUTES
}

// WINTRUST_FILE_INFO structure for Authenticode verification.
type WINTRUST_FILE_INFO struct {
	cbStruct      uint32
	pcwszFilePath *uint16
	hFile         uintptr
	pgKnownSubject uintptr
}

// WINTRUST_DATA structure for WinVerifyTrust API.
type WINTRUST_DATA struct {
	cbStruct            uint32
	pPolicyCallbackData uintptr
	pSIPClientData      uintptr
	dwUIChoice          uint32
	fdwRevocationChecks uint32
	dwUnionChoice       uint32
	pFile               uintptr
	dwStateAction       uint32
	hWVTStateData       uintptr
	pwszURLReference    *uint16
	dwProvFlags         uint32
	dwUIContext         uint32
	pSignatureSettings  uintptr
}

var (
	sigCache   = make(map[string]string)
	sigCacheMu sync.RWMutex
)

func collectPlatformProcesses(ctx context.Context) ([]ProcessInfo, error) {
	handle, _, err := procCreateToolhelp32Snapshot.Call(uintptr(TH32CS_SNAPPROCESS), 0)
	if handle == INVALID_HANDLE_VALUE || handle == 0 {
		return nil, fmt.Errorf("failed to create process snapshot: %w", err)
	}
	defer procCloseHandle.Call(handle)

	var entry PROCESSENTRY32W
	entry.dwSize = uint32(unsafe.Sizeof(entry))

	ret, _, err := procProcess32FirstW.Call(handle, uintptr(unsafe.Pointer(&entry)))
	if ret == 0 {
		return nil, fmt.Errorf("failed to read first process in snapshot: %w", err)
	}

	var results []ProcessInfo

	for {
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}

		pid := int(entry.th32ProcessID)
		parentPID := int(entry.th32ParentProcessID)
		name := syscall.UTF16ToString(entry.szExeFile[:])

		info := ProcessInfo{
			PID:             pid,
			Name:            name,
			ParentPID:       parentPID,
			SignatureStatus: "unknown",
		}

		// Attempt to query extended process information (Path, User, CommandLine)
		queryExtendedProcessInfo(pid, &info)

		results = append(results, info)

		entry.dwSize = uint32(unsafe.Sizeof(entry))
		ret, _, _ = procProcess32NextW.Call(handle, uintptr(unsafe.Pointer(&entry)))
		if ret == 0 {
			break
		}
	}

	return results, nil
}

func queryExtendedProcessInfo(pid int, info *ProcessInfo) {
	if pid == 0 || pid == 4 {
		// System / Idle process
		info.User = "NT AUTHORITY\\SYSTEM"
		info.SignatureStatus = "signed"
		return
	}

	// Try with limited query information first (available for standard processes)
	hProc, _, _ := procOpenProcess.Call(uintptr(PROCESS_QUERY_LIMITED_INFORMATION), 0, uintptr(pid))
	if hProc == 0 {
		// Fallback to basic query
		hProc, _, _ = procOpenProcess.Call(uintptr(PROCESS_QUERY_INFORMATION), 0, uintptr(pid))
	}
	if hProc == 0 {
		return
	}
	defer procCloseHandle.Call(hProc)

	// 1. Query Executable Path
	var pathBuf [1024]uint16
	pathSize := uint32(len(pathBuf))
	rPath, _, _ := procQueryFullProcessImageNameW.Call(hProc, 0, uintptr(unsafe.Pointer(&pathBuf[0])), uintptr(unsafe.Pointer(&pathSize)))
	if rPath != 0 {
		fullPath := syscall.UTF16ToString(pathBuf[:pathSize])
		info.Path = fullPath
		if info.Name == "" {
			info.Name = filepath.Base(fullPath)
		}

		// Verify signature if executable exists
		info.SignatureStatus = verifyWindowsSignatureCached(fullPath)
	}

	// 2. Query User from Process Token
	var hToken uintptr
	rToken, _, _ := procOpenProcessToken.Call(hProc, uintptr(TOKEN_QUERY), uintptr(unsafe.Pointer(&hToken)))
	if rToken != 0 && hToken != 0 {
		defer procCloseHandle.Call(hToken)

		var tokenBuf [512]byte
		var returnLength uint32
		rInfo, _, _ := procGetTokenInformation.Call(
			hToken,
			uintptr(TokenUser),
			uintptr(unsafe.Pointer(&tokenBuf[0])),
			uintptr(len(tokenBuf)),
			uintptr(unsafe.Pointer(&returnLength)),
		)
		if rInfo != 0 {
			tokenUser := (*TOKEN_USER)(unsafe.Pointer(&tokenBuf[0]))
			user, domain := lookupAccountName(tokenUser.User.Sid)
			if user != "" {
				if domain != "" {
					info.User = fmt.Sprintf("%s\\%s", domain, user)
				} else {
					info.User = user
				}
			}
		}
	}
}

func lookupAccountName(sid uintptr) (string, string) {
	var nameLen, domainLen uint32
	var sidType uint32

	procLookupAccountSidW.Call(
		0,
		sid,
		0,
		uintptr(unsafe.Pointer(&nameLen)),
		0,
		uintptr(unsafe.Pointer(&domainLen)),
		uintptr(unsafe.Pointer(&sidType)),
	)
	if nameLen == 0 {
		return "", ""
	}

	nameBuf := make([]uint16, nameLen)
	domainBuf := make([]uint16, domainLen)

	r, _, _ := procLookupAccountSidW.Call(
		0,
		sid,
		uintptr(unsafe.Pointer(&nameBuf[0])),
		uintptr(unsafe.Pointer(&nameLen)),
		uintptr(unsafe.Pointer(&domainBuf[0])),
		uintptr(unsafe.Pointer(&domainLen)),
		uintptr(unsafe.Pointer(&sidType)),
	)
	if r == 0 {
		return "", ""
	}

	return syscall.UTF16ToString(nameBuf), syscall.UTF16ToString(domainBuf)
}

func verifyWindowsSignatureCached(filePath string) string {
	sigCacheMu.RLock()
	if val, ok := sigCache[filePath]; ok {
		sigCacheMu.RUnlock()
		return val
	}
	sigCacheMu.RUnlock()

	status := verifyWindowsSignature(filePath)

	sigCacheMu.Lock()
	sigCache[filePath] = status
	sigCacheMu.Unlock()

	return status
}

func verifyWindowsSignature(filePath string) string {
	if _, err := os.Stat(filePath); err != nil {
		return "unknown"
	}

	pathUTF16, err := syscall.UTF16PtrFromString(filePath)
	if err != nil {
		return "unknown"
	}

	var fileInfo WINTRUST_FILE_INFO
	fileInfo.cbStruct = uint32(unsafe.Sizeof(fileInfo))
	fileInfo.pcwszFilePath = pathUTF16

	var trustData WINTRUST_DATA
	trustData.cbStruct = uint32(unsafe.Sizeof(trustData))
	trustData.dwUIChoice = WTD_UI_NONE
	trustData.fdwRevocationChecks = WTD_REVOKE_NONE
	trustData.dwUnionChoice = WTD_CHOICE_FILE
	trustData.pFile = uintptr(unsafe.Pointer(&fileInfo))
	trustData.dwStateAction = WTD_STATEACTION_IGNORE
	trustData.dwProvFlags = WTD_REVOCATION_CHECK_NONE | WTD_CACHE_ONLY_URL_RETRIEVAL | WTD_SAFER_FLAG

	type GUID struct {
		Data1 uint32
		Data2 uint16
		Data3 uint16
		Data4 [8]byte
	}
	guid := GUID{
		Data1: 0x00AAC56B,
		Data2: 0xCD44,
		Data3: 0x11d0,
		Data4: [8]byte{0x8C, 0xC2, 0x00, 0xC0, 0x4F, 0xC2, 0x95, 0xEE},
	}

	ret, _, _ := procWinVerifyTrust.Call(
		0,
		uintptr(unsafe.Pointer(&guid)),
		uintptr(unsafe.Pointer(&trustData)),
	)

	if ret == 0 {
		return "signed"
	}
	return "unsigned"
}
