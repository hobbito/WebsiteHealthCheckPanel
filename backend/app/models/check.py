from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class CheckStatus(str, enum.Enum):
    """Status of a check result"""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"


class IncidentStatus(str, enum.Enum):
    """Status of an incident"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class CheckConfiguration(Base):
    """Configuration for a specific check on a site"""

    __tablename__ = "check_configurations"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Check type (http, dns, email, custom_test, etc.)
    check_type = Column(String(50), nullable=False, index=True)

    # Check name/label
    name = Column(String(255), nullable=False)

    # Check-specific configuration stored as JSONB
    configuration = Column(JSON, nullable=False, default=dict)

    # Scheduling
    interval_seconds = Column(Integer, nullable=False, default=300)  # 5 minutes default

    # Status
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="check_configurations")
    check_results = relationship("CheckResult", back_populates="check_configuration", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="check_configuration", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CheckConfiguration(id={self.id}, type='{self.check_type}', name='{self.name}')>"


class CheckResult(Base):
    """Result of a check execution"""

    __tablename__ = "check_results"

    id = Column(Integer, primary_key=True, index=True)
    check_configuration_id = Column(Integer, ForeignKey("check_configurations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Result status
    status = Column(SQLEnum(CheckStatus), nullable=False, index=True)

    # Performance metrics
    response_time_ms = Column(Float, nullable=True)

    # Error details
    error_message = Column(Text, nullable=True)

    # Additional result data (JSON)
    result_data = Column(JSON, nullable=True)

    # Timestamp
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    check_configuration = relationship("CheckConfiguration", back_populates="check_results")

    def __repr__(self):
        return f"<CheckResult(id={self.id}, status='{self.status}', checked_at='{self.checked_at}')>"


class Incident(Base):
    """Tracking of continuous failures and their resolution"""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    check_configuration_id = Column(Integer, ForeignKey("check_configurations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Incident details
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Metrics
    failure_count = Column(Integer, default=1, nullable=False)

    # Relationships
    check_configuration = relationship("CheckConfiguration", back_populates="incidents")

    def __repr__(self):
        return f"<Incident(id={self.id}, status='{self.status}', started_at='{self.started_at}')>"
