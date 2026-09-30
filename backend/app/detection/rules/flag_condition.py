import re
from typing import List, Dict, Any, Optional
from app.detection.rules.base import DetectionRule
from app.schemas.detection import DetectionCreate, EvidenceReference


SUPPORTED_OPERATORS = {
    "eq", "==", "equals",
    "neq", "!=", "not_equals",
    "contains", "in",
    "gt", ">",
    "gte", ">=",
    "lt", "<",
    "lte", "<=",
    "startswith",
    "endswith",
    "matches", "regex",
}

SUPPORTED_FIELDS = {
    "signed", "signature_status", "is_signed",
    "name", "process_name",
    "pid", "ppid",
    "path", "exe_path",
    "cmdline", "command_line",
    "dest_ip", "remote_ip", "dst_ip", "remote_address",
    "dest_port", "remote_port", "dst_port",
    "hash", "sha256", "md5",
    "username", "user",
    "state", "status",
    "type",
}


def evaluate_condition_predicate(
    field_value: Any,
    operator: str,
    target_value: Any,
) -> bool:
    """Safely evaluates a deterministic condition predicate without eval()."""
    op = operator.lower().strip()

    if op not in SUPPORTED_OPERATORS:
        raise ValueError(f"Unsupported condition operator: '{operator}'")

    # Equality
    if op in ["eq", "==", "equals"]:
        if isinstance(target_value, bool):
            if isinstance(field_value, str):
                return (field_value.lower() == "true") == target_value
            return bool(field_value) == target_value
        if isinstance(field_value, str) and isinstance(target_value, str):
            return field_value.lower() == target_value.lower()
        return field_value == target_value

    # Inequality
    if op in ["neq", "!=", "not_equals"]:
        if isinstance(target_value, bool):
            if isinstance(field_value, str):
                return (field_value.lower() == "true") != target_value
            return bool(field_value) != target_value
        if isinstance(field_value, str) and isinstance(target_value, str):
            return field_value.lower() != target_value.lower()
        return field_value != target_value

    # String containment / list membership
    if op in ["contains", "in"]:
        if field_value is None:
            return False
        if isinstance(field_value, (list, tuple, set)):
            return target_value in field_value
        return str(target_value).lower() in str(field_value).lower()

    # Prefix / Suffix
    if op == "startswith":
        if field_value is None:
            return False
        return str(field_value).lower().startswith(str(target_value).lower())

    if op == "endswith":
        if field_value is None:
            return False
        return str(field_value).lower().endswith(str(target_value).lower())

    # Regex
    if op in ["matches", "regex"]:
        if field_value is None:
            return False
        try:
            pattern = re.compile(str(target_value), re.IGNORECASE)
            return bool(pattern.search(str(field_value)))
        except re.error as e:
            raise ValueError(f"Invalid regular expression in condition: {e}")

    # Numeric comparisons
    try:
        num_field = float(field_value)
        num_target = float(target_value)
    except (ValueError, TypeError):
        return False

    if op in ["gt", ">"]:
        return num_field > num_target
    if op in ["gte", ">="]:
        return num_field >= num_target
    if op in ["lt", "<"]:
        return num_field < num_target
    if op in ["lte", "<="]:
        return num_field <= num_target

    return False


class FlagConditionRule:
    """
    Evaluates JOCKY DSL `flag` statement conditions from compiled execution plans.
    Validates supported fields and operators safely without arbitrary code execution.
    """

    rule_id: str = "FLAG-DYNAMIC-001"
    name: str = "JOCKY Flag Condition Match"
    description: str = "Matches user-defined JOCKY flag conditions from compiled execution plans."
    severity: str = "high"

    def __init__(
        self,
        condition: Optional[Dict[str, Any]] = None,
        severity: str = "high",
        message: Optional[str] = None,
        rule_id: Optional[str] = None,
    ):
        self.condition = condition or {}
        self.severity = severity
        self.message = message
        if rule_id:
            self.rule_id = rule_id

    def validate_condition(self, condition: Dict[str, Any]) -> None:
        """Validates that a flag condition contains supported fields and operators."""
        if not isinstance(condition, dict):
            raise ValueError("Flag condition must be a dictionary")

        if "field" not in condition:
            raise ValueError("Malformed flag condition: missing 'field'")
        if "operator" not in condition:
            raise ValueError("Malformed flag condition: missing 'operator'")
        if "value" not in condition:
            raise ValueError("Malformed flag condition: missing 'value'")

        field_name = str(condition["field"]).lower().strip()
        if field_name not in SUPPORTED_FIELDS:
            raise ValueError(f"Unsupported flag condition field: '{condition['field']}'")

        operator = str(condition["operator"]).lower().strip()
        if operator not in SUPPORTED_OPERATORS:
            raise ValueError(f"Unsupported condition operator: '{condition['operator']}'")

    def _extract_field_value(self, data: Dict[str, Any], field_name: str) -> Any:
        field_lower = field_name.lower().strip()

        # Handle boolean 'signed' alias
        if field_lower in ["signed", "is_signed"]:
            sig_status = str(data.get("signature_status", "")).strip().lower()
            if sig_status == "signed":
                return True
            if sig_status == "unsigned":
                return False
            # Check direct bool field if present
            if "signed" in data:
                return bool(data["signed"])
            if "is_signed" in data:
                return bool(data["is_signed"])
            return None

        # Field alias map
        alias_map = {
            "process_name": ["process_name", "name"],
            "name": ["name", "process_name"],
            "exe_path": ["exe_path", "path"],
            "path": ["path", "exe_path"],
            "command_line": ["command_line", "cmdline"],
            "cmdline": ["cmdline", "command_line"],
            "remote_ip": ["remote_ip", "dest_ip", "dst_ip", "remote_address"],
            "dest_ip": ["dest_ip", "remote_ip", "dst_ip", "remote_address"],
            "remote_port": ["remote_port", "dest_port", "dst_port"],
            "dest_port": ["dest_port", "remote_port", "dst_port"],
        }

        candidates = alias_map.get(field_lower, [field_lower])
        for c in candidates:
            if c in data:
                return data[c]

        return None

    def evaluate(
        self,
        artifacts: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DetectionCreate]:
        detections: List[DetectionCreate] = []

        condition = self.condition
        if context and "condition" in context and isinstance(context["condition"], dict):
            condition = context["condition"]

        if not condition:
            return []

        # Validate condition format
        self.validate_condition(condition)

        field_name = condition["field"]
        operator = condition["operator"]
        target_value = condition["value"]

        severity = (context.get("severity") if context else None) or self.severity
        custom_message = (context.get("message") if context else None) or self.message

        for art in artifacts:
            art_id = getattr(art, "id", None) or (art.get("id") if isinstance(art, dict) else "")
            art_type = getattr(art, "type", None) or (art.get("type") if isinstance(art, dict) else "")
            agent_id = getattr(art, "agent_id", None) or (art.get("agent_id") if isinstance(art, dict) else "")
            job_id = getattr(art, "job_id", None) or (art.get("job_id") if isinstance(art, dict) else None)
            data = getattr(art, "data", None) or (art.get("data") if isinstance(art, dict) else {})

            if not isinstance(data, dict):
                continue

            field_val = self._extract_field_value(data, field_name)
            if field_val is None:
                # Field not found on this artifact
                continue

            matched = evaluate_condition_predicate(field_val, operator, target_value)
            if matched:
                explanation = custom_message or (
                    f"JOCKY flag condition matched: field '{field_name}' "
                    f"(observed: {field_val}) {operator} {target_value}."
                )

                detection = DetectionCreate(
                    agent_id=agent_id,
                    job_id=job_id,
                    rule_id=self.rule_id,
                    severity=severity,
                    title=f"Flagged artifact ({art_type}): {field_name}={field_val}",
                    description=explanation,
                    status="open",
                    evidence=[
                        EvidenceReference(
                            artifact_id=str(art_id),
                            type=str(art_type),
                            details={
                                "field": field_name,
                                "observed_value": field_val,
                                "condition_operator": operator,
                                "condition_value": target_value,
                            },
                        )
                    ],
                )
                detections.append(detection)

        return detections
