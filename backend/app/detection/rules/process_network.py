from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.detection.rules.base import DetectionRule
from app.schemas.detection import DetectionCreate, EvidenceReference


class UnsignedProcessNetworkRule:
    """
    Rule PROC-NET-001: Correlates unsigned process executables with active network connections
    originating from the same PID on the same host within a configurable time window.
    """

    rule_id: str = "PROC-NET-001"
    name: str = "Unsigned Process with Network Connection"
    description: str = "A process without a valid digital signature has an associated active network connection."
    severity: str = "high"
    default_window_seconds: int = 300  # 5 minutes

    def __init__(self, correlation_window_seconds: Optional[int] = None):
        self.correlation_window_seconds = correlation_window_seconds or self.default_window_seconds

    def _parse_timestamp(self, ts: Any) -> Optional[datetime]:
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc)
            return ts
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                return None
        return None

    def evaluate(
        self,
        artifacts: List[Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DetectionCreate]:
        detections: List[DetectionCreate] = []

        window_sec = self.correlation_window_seconds
        if context and "correlation_window_seconds" in context:
            try:
                window_sec = int(context["correlation_window_seconds"])
            except Exception:
                pass

        process_artifacts: List[Dict[str, Any]] = []
        network_artifacts: List[Dict[str, Any]] = []

        for art in artifacts:
            art_id = getattr(art, "id", None) or (art.get("id") if isinstance(art, dict) else "")
            art_type = str(getattr(art, "type", None) or (art.get("type") if isinstance(art, dict) else "")).lower()
            agent_id = getattr(art, "agent_id", None) or (art.get("agent_id") if isinstance(art, dict) else "")
            job_id = getattr(art, "job_id", None) or (art.get("job_id") if isinstance(art, dict) else None)
            data = getattr(art, "data", None) or (art.get("data") if isinstance(art, dict) else {})
            collected_at = getattr(art, "collected_at", None) or (art.get("collected_at") if isinstance(art, dict) else None)

            if not isinstance(data, dict):
                continue

            parsed_ts = self._parse_timestamp(collected_at) or datetime.now(timezone.utc)

            item = {
                "id": str(art_id),
                "type": art_type,
                "agent_id": agent_id,
                "job_id": job_id,
                "data": data,
                "timestamp": parsed_ts,
            }

            if art_type in ["process", "processes"]:
                process_artifacts.append(item)
            elif art_type in ["network", "connections", "network_connection", "connection"]:
                network_artifacts.append(item)

        # Correlate unsigned processes with network connections
        for proc in process_artifacts:
            proc_data = proc["data"]
            signature_status = str(proc_data.get("signature_status", "")).strip().lower()

            # Must be explicitly unsigned
            if signature_status != "unsigned":
                continue

            proc_pid = proc_data.get("pid")
            if proc_pid is None:
                continue

            try:
                proc_pid_int = int(proc_pid)
            except (ValueError, TypeError):
                continue

            proc_name = proc_data.get("name") or proc_data.get("process_name", "unknown")
            exe_path = proc_data.get("path") or proc_data.get("exe_path", "")

            for net in network_artifacts:
                # Must belong to the exact same agent
                if proc["agent_id"] != net["agent_id"]:
                    continue

                net_data = net["data"]
                net_pid = net_data.get("pid") or net_data.get("process_id") or net_data.get("owner_pid")
                if net_pid is None:
                    continue

                try:
                    net_pid_int = int(net_pid)
                except (ValueError, TypeError):
                    continue

                if proc_pid_int != net_pid_int:
                    continue

                # Check timestamp correlation window
                time_diff = abs((proc["timestamp"] - net["timestamp"]).total_seconds())
                if time_diff > window_sec:
                    continue

                # Connection details
                dest_ip = net_data.get("dest_ip") or net_data.get("remote_ip") or net_data.get("dst_ip") or net_data.get("remote_address", "unknown")
                dest_port = net_data.get("dest_port") or net_data.get("remote_port") or net_data.get("dst_port", "unknown")
                protocol = net_data.get("protocol") or net_data.get("proto", "TCP")

                explanation = (
                    f"Process PID {proc_pid_int} ({proc_name}) reported unsigned and was associated "
                    f"with {protocol} connection {dest_ip}:{dest_port}."
                )

                detection = DetectionCreate(
                    agent_id=proc["agent_id"],
                    job_id=proc["job_id"] or net["job_id"],
                    rule_id=self.rule_id,
                    severity=self.severity,
                    title="Unsigned process with active network connection",
                    description=explanation,
                    status="open",
                    evidence=[
                        EvidenceReference(
                            artifact_id=proc["id"],
                            type="process",
                            details={
                                "pid": proc_pid_int,
                                "name": proc_name,
                                "path": exe_path,
                                "signature_status": "unsigned",
                            },
                        ),
                        EvidenceReference(
                            artifact_id=net["id"],
                            type="network_connection",
                            details={
                                "pid": net_pid_int,
                                "dest_ip": dest_ip,
                                "dest_port": dest_port,
                                "protocol": protocol,
                                "state": net_data.get("state", ""),
                            },
                        ),
                    ],
                )
                detections.append(detection)

        return detections
