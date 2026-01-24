"""
Central import for all models to ensure proper SQLAlchemy relationship resolution.
Import this module instead of individual model modules to avoid circular import issues.
"""

# Import in dependency order: auth -> sites -> checks
from app.domains.auth.models import User, Organization, UserRole
from app.domains.sites.models import Site
from app.domains.checks.models import (
    CheckConfiguration,
    CheckResult,
    Incident,
    CheckStatus,
    IncidentStatus
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
]
