import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.detection.rules.base import DetectionRule
from app.schemas.detection import DetectionCreate, EvidenceReference


class SuspiciousParentChildRule:
    """
    Rule PROC-PARENT-001: Detects suspicious process parent/child lineage combinations
    defined in an external configuration file (e.g. rules/suspicious_parent_child.json).
    """

    rule_id: str = "PROC-PARENT-001"
    name: str = "Suspicious Process Lineage"
    description: str = "A process was spawned by an anomalous or known-suspicious parent process."
    severity: str = "high"

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._rules: List[Dict[str, Any]] = self._load_rules(config_path)

    def _load_rules(self, config_path: Optional[str]) -> List[Dict[str, Any]]:
        # Candidate search locations
        search_paths = []
        if config_path:
            search_paths.append(Path(config_path))
        
        # Look in workspace root 'rules/' and relative directories
        search_paths.extend([
            Path("rules/suspicious_parent_child.json"),
            Path("../rules/suspicious_parent_child.json"),
            Path(__file__).parent.parent.parent.parent.parent / "rules" / "suspicious_parent_child.json",
        ])

        for p in search_paths:
            try:
                if p.exists() and p.is_file():
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            return data
            except Exception:
                continue

        # Fallback default rules in memory if file cannot be loaded
        return [
            {
                "parent": "wmiprvse.exe",
                "child": "powershell.exe",
                "severity": "high",
                "title": "PowerShell spawned from WMI Provider Host",
                "description": "PowerShell spawned from WMI Provider Host (wmiprvse.exe)."
            },
            {
                "parent": "winword.exe",
                "child": "cmd.exe",
                "severity": "critical",
                "title": "Command shell spawned from Microsoft Word",
                "description": "Command prompt spawned directly from Microsoft Word."
            },
            {
                "parent": "excel.exe",
                "child": "powershell.exe",
                "severity": "critical",
                "title": "PowerShell spawned from Microsoft Excel",
                "description": "PowerShell spawned directly from Microsoft Excel."
            },
            {
                "parent": "nginx",
                "child": "bash",
                "severity": "high",
                "title": "Interactive shell spawned from web server",
                "description": "Nginx web server spawned a bash shell."
            }
        ]

    def _normalize_proc_name(self, name: Optional[str]) -> str:
        if not name:
            return ""
        # Strip path if full path is provided
        base = os.path.basename(str(name)).strip().lower()
        return base

    def evaluate(
        self,
        artifacts: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DetectionCreate]:
        detections: List[DetectionCreate] = []

        rules = self._rules
        if context and "parent_child_rules" in context and isinstance(context["parent_child_rules"], list):
            rules = context["parent_child_rules"]

        for art in artifacts:
            art_id = getattr(art, "id", None) or (art.get("id") if isinstance(art, dict) else "")
            art_type = str(getattr(art, "type", None) or (art.get("type") if isinstance(art, dict) else "")).lower()
            agent_id = getattr(art, "agent_id", None) or (art.get("agent_id") if isinstance(art, dict) else "")
            job_id = getattr(art, "job_id", None) or (art.get("job_id") if isinstance(art, dict) else None)
            data = getattr(art, "data", None) or (art.get("data") if isinstance(art, dict) else {})

            if not isinstance(data, dict):
                continue

            if art_type not in ["process", "processes"]:
                continue

            child_name = self._normalize_proc_name(data.get("name") or data.get("process_name"))
            parent_name = self._normalize_proc_name(
                data.get("parent_name") or data.get("parent_process_name") or data.get("ppid_name")
            )

            if not child_name or not parent_name:
                continue

            pid = data.get("pid", "unknown")
            ppid = data.get("ppid", "unknown")

            for r in rules:
                target_parent = self._normalize_proc_name(r.get("parent"))
                target_child = self._normalize_proc_name(r.get("child"))

                if target_parent == parent_name and target_child == child_name:
                    severity = r.get("severity", self.severity)
                    title = r.get("title", f"Suspicious parent/child: {parent_name} -> {child_name}")
                    base_desc = r.get("description", "Suspicious parent/child relationship observed.")
                    
                    explanation = (
                        f"{base_desc} Observed child process '{child_name}' (PID {pid}) "
                        f"spawned by parent process '{parent_name}' (PPID {ppid})."
                    )

                    detection = DetectionCreate(
                        agent_id=agent_id,
                        job_id=job_id,
                        rule_id=self.rule_id,
                        severity=severity,
                        title=title,
                        description=explanation,
                        status="open",
                        evidence=[
                            EvidenceReference(
                                artifact_id=str(art_id),
                                type="process",
                                details={
                                    "pid": pid,
                                    "ppid": ppid,
                                    "name": data.get("name") or child_name,
                                    "parent_name": data.get("parent_name") or parent_name,
                                    "cmdline": data.get("cmdline") or data.get("command_line", ""),
                                },
                            )
                        ],
                    )
                    detections.append(detection)
                    break

        return detections
