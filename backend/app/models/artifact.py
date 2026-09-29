from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from app.db.base import Base


class ArtifactModel(Base):
    """Forensic artifact evidence collected from endpoints."""
    __tablename__ = "artifacts"

    id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=False, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id"), nullable=False, index=True)
    type = Column(String(64), nullable=False, index=True)  # process, network, persistence, etc.
    data = Column(JSON, nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
