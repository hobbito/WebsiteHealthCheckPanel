"""Notifications domain models"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.domains.auth.models import Organization
    from app.domains.checks.models import CheckResult, Incident


class NotificationChannelType(str, enum.Enum):
    """Type of notification channel"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"


class NotificationTrigger(str, enum.Enum):
    """Events that can trigger a notification"""
    CHECK_FAILURE = "check_failure"
    CHECK_RECOVERY = "check_recovery"
    INCIDENT_OPENED = "incident_opened"
    INCIDENT_RESOLVED = "incident_resolved"


class NotificationStatus(str, enum.Enum):
    """Status of a notification delivery"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationChannel(Base):
    """Configuration for a notification channel (email, webhook, etc.)"""

    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Channel identification
    name = Column(String(255), nullable=False)
    channel_type = Column(SQLEnum(NotificationChannelType), nullable=False, index=True)

    # Channel-specific configuration stored as JSON
    # email: {smtp_host, smtp_port, smtp_user, smtp_password, from_address, to_addresses[], use_tls}
    # webhook: {url, method, headers, auth_type, auth_token, auth_username, auth_password}
    configuration = Column(JSON, nullable=False, default=dict)

    # Status
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", backref="notification_channels")
    notification_rules = relationship("NotificationRule", back_populates="channel", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<NotificationChannel(id={self.id}, name='{self.name}', type='{self.channel_type}')>"


class NotificationRule(Base):
    """Rules defining when and how to send notifications"""

    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("notification_channels.id", ondelete="CASCADE"), nullable=False, index=True)

    # Rule identification
    name = Column(String(255), nullable=False)

    # Trigger type
    trigger = Column(SQLEnum(NotificationTrigger), nullable=False, index=True)

    # Filtering (null means all)
    site_ids = Column(JSON, nullable=True)  # List of site IDs or null for all sites
    check_types = Column(JSON, nullable=True)  # List of check types or null for all types

    # Conditions
    consecutive_failures = Column(Integer, default=1, nullable=False)  # Trigger after N consecutive failures

    # Status
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", backref="notification_rules")
    channel = relationship("NotificationChannel", back_populates="notification_rules")
    logs = relationship("NotificationLog", back_populates="rule", cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<NotificationRule(id={self.id}, name='{self.name}', trigger='{self.trigger}')>"


class NotificationLog(Base):
    """Log of notification deliveries"""

    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("notification_rules.id", ondelete="CASCADE"), nullable=False, index=True)

    # Related entities (optional, for reference)
    check_result_id = Column(Integer, ForeignKey("check_results.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    # Delivery status
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    rule = relationship("NotificationRule", back_populates="logs")
    check_result = relationship("CheckResult", backref="notification_logs")
    incident = relationship("Incident", backref="notification_logs")

    def __repr__(self):
        return f"<NotificationLog(id={self.id}, rule_id={self.rule_id}, status='{self.status}')>"
