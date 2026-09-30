from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from app.schemas.detection import DetectionCreate


@runtime_checkable
class DetectionRule(Protocol):
    """Protocol interface for explainable deterministic DFIR detection rules."""

    rule_id: str
    name: str
    description: str
    severity: str

    def evaluate(
        self,
        artifacts: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DetectionCreate]:
        """
        Evaluate a batch of forensic artifacts and return structured detections.

        Args:
            artifacts: List of artifact records (dict or ArtifactRead/ArtifactModel).
            context: Optional contextual parameters (e.g., job plans, correlation window).

        Returns:
            List of structured DetectionCreate objects.
        """
        ...
