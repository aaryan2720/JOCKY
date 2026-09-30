from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class ArtifactModel(Base):
    """Forensic artifact evidence collected from endpoints."""
    __tablename__ = "artifacts"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(64), nullable=False, index=True)  # processes, connections, files, autoruns, etc.
    target = Column(String(128), nullable=True, index=True)
    host_id = Column(String(128), nullable=True)
    data = Column(JSON, nullable=False, default=dict)
    extra_metadata = Column("metadata", JSON, nullable=False, default=dict)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("AgentModel", back_populates="artifacts", lazy="selectin")
    job = relationship("JobModel", back_populates="artifacts", lazy="selectin")
