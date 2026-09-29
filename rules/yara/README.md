# YARA Detection Rules Directory

Place YARA rules (`.yar` / `.yara`) for file and memory scanning in this directory.

### Example rule structure:
```yara
rule Suspicious_Encoded_PowerShell {
    meta:
        description = "Detects base64 encoded PowerShell invocations"
        author = "JOCKY DFIR Team"
        severity = "HIGH"
    strings:
        $enc1 = "-enc" nocase
        $enc2 = "-encodedcommand" nocase
    condition:
        any of them
}
```
