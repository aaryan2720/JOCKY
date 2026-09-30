from typing import List, Dict, Any, Optional
from app.detection.rules.base import DetectionRule
from app.schemas.detection import DetectionCreate, EvidenceReference


class SuspiciousUserRule:
    """
    Rule USER-SUSP-001: Detects dormant, guest, or explicitly abnormal user accounts
    observed in an active / enabled state on the endpoint.
    """

    rule_id: str = "USER-SUSP-001"
    name: str = "Anomalous Active Account Configuration"
    description: str = "A dormant, guest, or suspicious account was observed in an enabled state."
    severity: str = "medium"

    SUSPICIOUS_ACTIVE_ACCOUNTS = {"guest", "defaultaccount"}

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

            if art_type not in ["user", "users"]:
                continue

            enabled = data.get("enabled", False)
            if enabled is not True and str(enabled).lower() != "true":
                continue

            username = str(data.get("username", "")).strip()
            desc = str(data.get("description", "")).strip().lower()
            lower_user = username.lower()

            is_suspicious = False
            reason = ""

            if lower_user in self.SUSPICIOUS_ACTIVE_ACCOUNTS:
                is_suspicious = True
                reason = f"Built-in dormant account '{username}' is enabled."
            elif "backdoor" in lower_user or "temp_admin" in lower_user or "backdoor" in desc:
                is_suspicious = True
                reason = f"Account '{username}' exhibits suspicious naming or description."

            if is_suspicious:
                explanation = (
                    f"Local account '{username}' was detected in an active enabled state. {reason}"
                )

                detection = DetectionCreate(
                    agent_id=agent_id,
                    job_id=job_id,
                    rule_id=self.rule_id,
                    severity=self.severity,
                    title=f"Anomalous active account: {username}",
                    description=explanation,
                    status="open",
                    evidence=[
                        EvidenceReference(
                            artifact_id=str(art_id),
                            type="user",
                            details={
                                "username": username,
                                "enabled": True,
                                "account_type": data.get("account_type", ""),
                                "description": data.get("description", ""),
                                "sid": data.get("sid", ""),
                            },
                        )
                    ],
                )
                detections.append(detection)

        return detections
