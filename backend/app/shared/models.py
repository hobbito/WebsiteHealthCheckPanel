"""
Central import for all models to ensure proper SQLAlchemy relationship resolution.
Import this module instead of individual model modules to avoid circular import issues.
"""

# Import in dependency order: auth -> sites -> checks -> notifications
from app.domains.auth.models import User, Organization, UserRole
from app.domains.sites.models import Site
from app.domains.checks.models import (
    CheckConfiguration,
    CheckResult,
    Incident,
    CheckStatus,
    IncidentStatus
)
from app.domains.notifications.models import (
    NotificationChannel,
    NotificationRule,
    NotificationLog,
    NotificationChannelType,
    NotificationTrigger,
    NotificationStatus,
)

__all__ = [
    "User",
    "Organization",
    "UserRole",
    "Site",
    "CheckConfiguration",
    "CheckResult",
    "Incident",
    "CheckStatus",
    "IncidentStatus",
    "NotificationChannel",
    "NotificationRule",
    "NotificationLog",
    "NotificationChannelType",
    "NotificationTrigger",
    "NotificationStatus",
]
