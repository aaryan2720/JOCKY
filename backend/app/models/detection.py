from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from app.db.base import Base


class DetectionModel(Base):
    """Correlated threat detection or policy violation alert."""
    __tablename__ = "detections"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), nullable=True, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    rule_id = Column(String(255), nullable=False, index=True)
    severity = Column(String(32), default="high", index=True)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="open", index=True)
    evidence = Column(JSON, nullable=False)
    dedup_key = Column(String(128), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
