from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class DetectionModel(Base):
    """Correlated threat detection or policy violation alert."""
    __tablename__ = "detections"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_id = Column(String(255), nullable=False, index=True)
    severity = Column(String(32), default="high", index=True)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), default="open", index=True)
    evidence = Column(JSON, nullable=False, default=list)
    dedup_key = Column(String(128), index=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    agent = relationship("AgentModel", back_populates="detections", lazy="selectin")
    job = relationship("JobModel", back_populates="detections", lazy="selectin")
