from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from app.db.base import Base


class DetectionModel(Base):
    """Correlated threat detection or policy violation alert."""
    __tablename__ = "detections"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=True, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id"), nullable=False, index=True)
    rule = Column(String(255), nullable=False, index=True)
    severity = Column(String(32), default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    evidence = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
