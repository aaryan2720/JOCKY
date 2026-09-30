from typing import List, Dict, Any, Optional
from app.detection.rules.base import DetectionRule
from app.schemas.detection import DetectionCreate, EvidenceReference


class UnsignedProcessRule:
    """
    Rule PROC-UNSIGNED-001: Detects processes reporting an unsigned binary executable.
    Does NOT trigger for signed binaries, nor unsupported platforms (e.g. Linux).
    """

    rule_id: str = "PROC-UNSIGNED-001"
    name: str = "Unsigned Process Executable"
    description: str = "A process reports an unsigned executable on the endpoint."
    severity: str = "high"

    def evaluate(
        self,
        artifacts: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DetectionCreate]:
        detections: List[DetectionCreate] = []

        for art in artifacts:
            # Handle both dict and object models
            art_id = getattr(art, "id", None) or (art.get("id") if isinstance(art, dict) else "")
            art_type = getattr(art, "type", None) or (art.get("type") if isinstance(art, dict) else "")
            agent_id = getattr(art, "agent_id", None) or (art.get("agent_id") if isinstance(art, dict) else "")
            job_id = getattr(art, "job_id", None) or (art.get("job_id") if isinstance(art, dict) else None)
            data = getattr(art, "data", None) or (art.get("data") if isinstance(art, dict) else {})

            if not isinstance(data, dict):
                continue

            # Process collector types: "process", "processes"
            if str(art_type).lower() not in ["process", "processes"]:
                continue

            signature_status = str(data.get("signature_status", "")).strip().lower()

            # Trigger only on explicitly unsigned status (not 'signed', not 'unsupported', not empty)
            if signature_status == "unsigned":
                pid = data.get("pid", "unknown")
                name = data.get("name") or data.get("process_name", "unknown")
                exe_path = data.get("path") or data.get("exe_path", "")

                obs_details = {
                    "pid": pid,
                    "name": name,
                    "path": exe_path,
                    "signature_status": "unsigned",
                }

                description = (
                    f"Process {name} (PID {pid}) reports an unsigned executable. "
                    "The process artifact reported an unsigned executable."
                )

                detection = DetectionCreate(
                    agent_id=agent_id,
                    job_id=job_id,
                    rule_id=self.rule_id,
                    severity=self.severity,
                    title=f"Unsigned process detected: {name}",
                    description=description,
                    status="open",
                    evidence=[
                        EvidenceReference(
                            artifact_id=str(art_id),
                            type="process",
                            details=obs_details,
                        )
                    ],
                )
                detections.append(detection)

        return detections
