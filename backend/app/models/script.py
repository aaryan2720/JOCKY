from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base


class ScriptModel(Base):
    """JOCKY forensic query script definition."""
    __tablename__ = "scripts"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(512), nullable=True)
    body = Column(Text, nullable=False)
    created_by = Column(String(128), default="analyst")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    jobs = relationship("JobModel", back_populates="script", lazy="selectin")
