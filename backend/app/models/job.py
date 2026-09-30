from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class JobModel(Base):
    """Forensic query execution job dispatched to fleet agents."""
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True, index=True)
    script_id = Column(String(64), ForeignKey("scripts.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(32), default="pending", index=True)  # pending, queued, in_progress, completed, failed, cancelled
    target_agents = Column(JSON, default=list)
    plan = Column(JSON, nullable=True)  # Compiled JOCKY execution plan
    error_message = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    script = relationship("ScriptModel", back_populates="jobs", lazy="selectin")
    agent = relationship("AgentModel", lazy="selectin")
    artifacts = relationship("ArtifactModel", back_populates="job", lazy="selectin", cascade="save-update, merge")
    detections = relationship("DetectionModel", back_populates="job", lazy="selectin", cascade="save-update, merge")
