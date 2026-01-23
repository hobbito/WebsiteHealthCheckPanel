from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class NotificationChannelType(str, enum.Enum):
    """Types of notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"


class NotificationSeverity(str, enum.Enum):
    """Severity levels for notifications"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationChannel(Base):
    """Configuration for a notification channel"""

    __tablename__ = "notification_channels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Channel details
    channel_type = Column(SQLEnum(NotificationChannelType), nullable=False)
    name = Column(String(255), nullable=False)

    # Channel-specific configuration (SMTP details, webhook URL, etc.)
    configuration = Column(JSON, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notification_channels")
    notification_rules = relationship("NotificationRule", back_populates="channel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<NotificationChannel(id={self.id}, type='{self.channel_type}', name='{self.name}')>"


class NotificationRule(Base):
    """Rules for when and how to send notifications"""

    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("notification_channels.id", ondelete="CASCADE"), nullable=False, index=True)

    # Rule details
    name = Column(String(255), nullable=False)

    # Filters (which sites/checks to monitor)
    # Can filter by site_ids, check_types, severity, etc.
    filters = Column(JSON, nullable=False, default=dict)

    # Conditions (when to trigger)
    # e.g., "notify after 3 consecutive failures"
    conditions = Column(JSON, nullable=False, default=dict)

    # Severity filter
    min_severity = Column(SQLEnum(NotificationSeverity), default=NotificationSeverity.WARNING, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notification_rules")
    channel = relationship("NotificationChannel", back_populates="notification_rules")

    def __repr__(self):
        return f"<NotificationRule(id={self.id}, name='{self.name}')>"


class NotificationLog(Base):
    """Log of sent notifications"""

    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Reference to what triggered the notification
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    channel_id = Column(Integer, ForeignKey("notification_channels.id", ondelete="SET NULL"), nullable=True)

    # Notification details
    channel_type = Column(SQLEnum(NotificationChannelType), nullable=False)
    recipient = Column(String(500), nullable=False)
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)

    # Status
    sent_successfully = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamp
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<NotificationLog(id={self.id}, type='{self.channel_type}', sent_at='{self.sent_at}')>"
