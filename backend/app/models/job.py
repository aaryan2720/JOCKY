from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from app.db.base import Base


class JobModel(Base):
    """Forensic query execution job dispatched to fleet agents."""
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True, index=True)
    script_id = Column(String(64), ForeignKey("scripts.id"), nullable=True)
    status = Column(String(32), default="pending", index=True)  # pending, running, completed, failed
    target_agents = Column(JSON, default=list)
    plan = Column(JSON, nullable=True)  # Compiled JOCKY execution plan
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
