import re
from typing import List, Dict, Any, Optional
from app.detection.rules.base import DetectionRule
from app.schemas.detection import DetectionCreate, EvidenceReference


class SuspiciousAutorunRule:
    """
    Rule AUTORUN-SUSP-001: Detects autoruns configured to launch binaries
    from temporary, volatile, or suspicious user-writable directories.
    """

    rule_id: str = "AUTORUN-SUSP-001"
    name: str = "Suspicious Autorun Binary Location"
    description: str = "An autorun persistence entry executes a payload from a temporary or volatile directory."
    severity: str = "high"

    # Suspicious execution path indicators
    SUSPICIOUS_PATHS = [
        "\\temp\\",
        "\\appdata\\local\\temp\\",
        "/tmp/",
        "/var/tmp/",
        "\\users\\public\\",
    ]

    def evaluate(
        self,
        artifacts: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DetectionCreate]:
        detections: List[DetectionCreate] = []

        for art in artifacts:
            art_id = getattr(art, "id", None) or (art.get("id") if isinstance(art, dict) else "")
            art_type = str(getattr(art, "type", None) or (art.get("type") if isinstance(art, dict) else "")).lower()
            agent_id = getattr(art, "agent_id", None) or (art.get("agent_id") if isinstance(art, dict) else "")
            job_id = getattr(art, "job_id", None) or (art.get("job_id") if isinstance(art, dict) else None)
            data = getattr(art, "data", None) or (art.get("data") if isinstance(art, dict) else {})

            if not isinstance(data, dict):
                continue

            if art_type not in ["autorun", "autoruns"]:
                continue

            command = str(data.get("command", "")).strip()
            name = str(data.get("name", "unknown")).strip()
            location = str(data.get("location", "")).strip()
            user = str(data.get("user", "")).strip()

            if not command:
                continue

            lower_cmd = command.lower()
            matched_indicator = None

            for indicator in self.SUSPICIOUS_PATHS:
                if indicator in lower_cmd:
                    matched_indicator = indicator
                    break

            if matched_indicator:
                explanation = (
                    f"Autorun entry '{name}' at '{location}' is configured to execute "
                    f"from a volatile/suspicious directory '{matched_indicator}'. "
                    f"Observed command: {command}"
                )

                detection = DetectionCreate(
                    agent_id=agent_id,
                    job_id=job_id,
                    rule_id=self.rule_id,
                    severity=self.severity,
                    title=f"Suspicious autorun location: {name}",
                    description=explanation,
                    status="open",
                    evidence=[
                        EvidenceReference(
                            artifact_id=str(art_id),
                            type="autorun",
                            details={
                                "name": name,
                                "command": command,
                                "location": location,
                                "user": user,
                                "matched_indicator": matched_indicator,
                            },
                        )
                    ],
                )
                detections.append(detection)

        return detections
