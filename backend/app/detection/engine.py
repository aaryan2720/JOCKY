import hashlib
import logging
from typing import List, Dict, Any, Optional
from app.detection.rules.base import DetectionRule
from app.detection.rules.unsigned_process import UnsignedProcessRule
from app.detection.rules.process_network import UnsignedProcessNetworkRule
from app.detection.rules.parent_child import SuspiciousParentChildRule
from app.detection.rules.flag_condition import FlagConditionRule
from app.schemas.detection import DetectionCreate

logger = logging.getLogger(__name__)


def compute_dedup_key(
    rule_id: str,
    agent_id: str,
    job_id: Optional[str],
    evidence_artifact_ids: List[str],
) -> str:
    """Calculates a deterministic deduplication key for a detection."""
    sorted_ids = sorted(str(aid) for aid in evidence_artifact_ids if aid)
    raw_key = f"{rule_id}:{agent_id}:{job_id or 'none'}:{':'.join(sorted_ids)}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:32]


class DetectionEngine:
    """
    Explainable threat detection and correlation engine.
    Applies deterministic heuristic rules and JOCKY flag conditions to forensic artifacts.
    """

    def __init__(
        self,
        rules: Optional[List[DetectionRule]] = None,
        correlation_window_seconds: int = 300,
    ):
        self.correlation_window_seconds = correlation_window_seconds
        if rules is not None:
            self.rules = list(rules)
        else:
            self.rules = [
                UnsignedProcessRule(),
                UnsignedProcessNetworkRule(correlation_window_seconds=self.correlation_window_seconds),
                SuspiciousParentChildRule(),
            ]

    def register_rule(self, rule: DetectionRule) -> None:
        """Register an additional detection rule."""
        self.rules.append(rule)

    def evaluate_artifacts(
        self,
        artifacts: List[Any],
        plan: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[DetectionCreate, str]]:
        """
        Evaluates a batch of artifacts against all registered heuristic rules
        and any JOCKY flag operations present in the execution plan.

        Returns:
            List of tuples: (DetectionCreate, dedup_key)
        """
        all_detections: List[tuple[DetectionCreate, str]] = []
        seen_keys: set[str] = set()

        ctx = context.copy() if context else {}
        ctx.setdefault("correlation_window_seconds", self.correlation_window_seconds)

        # 1. Evaluate Static/Heuristic Rules
        for rule in self.rules:
            try:
                results = rule.evaluate(artifacts, context=ctx)
                for det in results:
                    evidence_ids = [ev.artifact_id for ev in det.evidence]
                    dedup_key = compute_dedup_key(det.rule_id, det.agent_id, det.job_id, evidence_ids)
                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        all_detections.append((det, dedup_key))
            except Exception as e:
                logger.error(f"Error evaluating rule {getattr(rule, 'rule_id', 'unknown')}: {e}", exc_info=True)

        # 2. Evaluate Dynamic JOCKY Flag Conditions from Plan
        if plan and isinstance(plan, dict):
            flag_ops = []
            # Check top-level or checks/operations in plan
            if "flags" in plan and isinstance(plan["flags"], list):
                flag_ops.extend(plan["flags"])
            if "checks" in plan and isinstance(plan["checks"], list):
                for chk in plan["checks"]:
                    if isinstance(chk, dict) and chk.get("operation") == "flag":
                        flag_ops.append(chk)
            if "operations" in plan and isinstance(plan["operations"], list):
                for op in plan["operations"]:
                    if isinstance(op, dict) and op.get("operation") == "flag":
                        flag_ops.append(op)
            if plan.get("operation") == "flag":
                flag_ops.append(plan)

            for flag_op in flag_ops:
                try:
                    cond = flag_op.get("condition")
                    if cond:
                        severity = flag_op.get("severity", "high")
                        message = flag_op.get("message")
                        flag_rule = FlagConditionRule(condition=cond, severity=severity, message=message)
                        results = flag_rule.evaluate(artifacts, context=ctx)
                        for det in results:
                            evidence_ids = [ev.artifact_id for ev in det.evidence]
                            dedup_key = compute_dedup_key(det.rule_id, det.agent_id, det.job_id, evidence_ids)
                            if dedup_key not in seen_keys:
                                seen_keys.add(dedup_key)
                                all_detections.append((det, dedup_key))
                except Exception as e:
                    logger.error(f"Error evaluating flag condition in plan: {e}", exc_info=True)

        return all_detections
