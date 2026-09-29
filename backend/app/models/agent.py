from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base


class AgentModel(Base):
    """Registered forensic fleet agent."""
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True, index=True)
    hostname = Column(String(255), nullable=False, index=True)
    os = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    status = Column(String(32), default="offline", index=True)
    version = Column(String(32), nullable=True)
    cert_fingerprint = Column(String(128), nullable=True)
    tags = Column(JSON, default=list)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
