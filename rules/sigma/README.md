# Sigma Detection Rules Directory

Place Sigma rules (`.yml` / `.yaml`) for log and event correlation in this directory.

### Example rule structure:
```yaml
title: Suspicious Process Spawning Cmd
id: 5b4e3c2a-1234-4567-890a-bcdef1234567
status: experimental
description: Detects command prompt spawned from Office applications or unusual parents
logsource:
  category: process_creation
  product: windows
detection:
  selection:
    ParentImage|endswith:
      - '\winword.exe'
      - '\excel.exe'
    Image|endswith: '\cmd.exe'
  condition: selection
level: high
```
