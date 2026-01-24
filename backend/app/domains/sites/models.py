"""Sites domain models"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.domains.auth.models import Organization
    from app.domains.checks.models import CheckConfiguration


class Site(Base):
    """Website/domain to monitor"""

    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="sites", lazy="select")
    check_configurations = relationship("CheckConfiguration", back_populates="site", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<Site(id={self.id}, name='{self.name}', url='{self.url}')>"
