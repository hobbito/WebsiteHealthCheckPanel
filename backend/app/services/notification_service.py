import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.check import CheckConfiguration, CheckResult, Incident, IncidentStatus
from app.models.notification import NotificationChannel, NotificationRule, NotificationLog, NotificationSeverity
from app.models.site import Site
from app.notifications.registry import NotificationRegistry
from app.notifications.base import NotificationMessage

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notifications based on check failures"""

    @staticmethod
    async def handle_check_failure(
        db: AsyncSession,
        check_config: CheckConfiguration,
        check_result: CheckResult
    ):
        """
        Handle a check failure by creating/updating incidents and sending notifications.

        Args:
            db: Database session
            check_config: The check configuration that failed
            check_result: The failed check result
        """
        try:
            # Get site information
            site_result = await db.execute(
                select(Site).where(Site.id == check_config.site_id)
            )
            site = site_result.scalar_one_or_none()

            if not site:
                logger.error(f"Site {check_config.site_id} not found")
                return

            # Find or create incident
            incident = await NotificationService._get_or_create_incident(
                db, check_config, check_result
            )

            # Find applicable notification rules
            rules = await NotificationService._get_applicable_rules(
                db, site, check_config, incident
            )

            # Send notifications for each rule
            for rule in rules:
                await NotificationService._send_notification(
                    db, rule, site, check_config, check_result, incident
                )

        except Exception as e:
            logger.error(f"Error handling check failure: {e}", exc_info=True)

    @staticmethod
    async def _get_or_create_incident(
        db: AsyncSession,
        check_config: CheckConfiguration,
        check_result: CheckResult
    ) -> Incident:
        """Get existing open incident or create new one"""

        # Look for open incident for this check
        result = await db.execute(
            select(Incident).where(
                Incident.check_configuration_id == check_config.id,
                Incident.status == IncidentStatus.OPEN
            ).order_by(Incident.started_at.desc()).limit(1)
        )
        incident = result.scalar_one_or_none()

        if incident:
            # Update existing incident
            incident.failure_count += 1
            logger.info(f"Updated incident {incident.id}, failure count: {incident.failure_count}")
        else:
            # Create new incident
            incident = Incident(
                check_configuration_id=check_config.id,
                status=IncidentStatus.OPEN,
                title=f"{check_config.name} failing",
                description=check_result.error_message,
                failure_count=1
            )
            db.add(incident)
            logger.info(f"Created new incident for check {check_config.id}")

        await db.commit()
        await db.refresh(incident)
        return incident

    @staticmethod
    async def _get_applicable_rules(
        db: AsyncSession,
        site: Site,
        check_config: CheckConfiguration,
        incident: Incident
    ) -> List[NotificationRule]:
        """Get notification rules that apply to this failure"""

        # Get all active rules for the organization
        result = await db.execute(
            select(NotificationRule)
            .join(NotificationRule.user)
            .where(
                NotificationRule.is_active == True,
                NotificationRule.user.has(organization_id=site.organization_id)
            )
        )
        all_rules = result.scalars().all()

        # Filter rules based on conditions
        applicable_rules = []
        for rule in all_rules:
            # Check filters
            filters = rule.filters or {}
            site_ids = filters.get("site_ids", [])
            check_types = filters.get("check_types", [])

            # If filters are empty, rule applies to all
            if site_ids and site.id not in site_ids:
                continue

            if check_types and check_config.check_type not in check_types:
                continue

            # Check conditions
            conditions = rule.conditions or {}
            min_failures = conditions.get("min_consecutive_failures", 1)

            if incident.failure_count < min_failures:
                continue

            applicable_rules.append(rule)

        return applicable_rules

    @staticmethod
    async def _send_notification(
        db: AsyncSession,
        rule: NotificationRule,
        site: Site,
        check_config: CheckConfiguration,
        check_result: CheckResult,
        incident: Incident
    ):
        """Send notification via the rule's channel"""

        try:
            # Get notification channel
            channel_result = await db.execute(
                select(NotificationChannel).where(
                    NotificationChannel.id == rule.channel_id
                )
            )
            channel = channel_result.scalar_one_or_none()

            if not channel or not channel.is_active:
                logger.warning(f"Channel {rule.channel_id} not found or inactive")
                return

            # Get channel implementation
            if not NotificationRegistry.is_registered(channel.channel_type.value):
                logger.error(f"Channel type {channel.channel_type} not registered")
                return

            channel_class = NotificationRegistry.get_channel(channel.channel_type.value)
            channel_instance = channel_class()

            # Prepare message
            recipient = channel.configuration.get("recipient") or channel.configuration.get("smtp_user")
            subject = f"🚨 Health Check Alert: {site.name} - {check_config.name}"
            message_body = f"""
Health Check Failure Detected

Site: {site.name} ({site.url})
Check: {check_config.name}
Type: {check_config.check_type}

Status: FAILURE
Error: {check_result.error_message or 'Unknown error'}
Response Time: {check_result.response_time_ms:.0f}ms

Incident #{incident.id}
Consecutive Failures: {incident.failure_count}
Started At: {incident.started_at}

---
Health Check Panel
            """.strip()

            notification_message = NotificationMessage(
                recipient=recipient,
                subject=subject,
                message=message_body,
                data={
                    "site_id": site.id,
                    "check_id": check_config.id,
                    "incident_id": incident.id
                }
            )

            # Send notification
            success, error = await channel_instance.send(
                channel.configuration,
                notification_message
            )

            # Log notification
            log_entry = NotificationLog(
                incident_id=incident.id,
                channel_id=channel.id,
                channel_type=channel.channel_type,
                recipient=recipient,
                subject=subject,
                message=message_body,
                sent_successfully=success,
                error_message=error
            )
            db.add(log_entry)
            await db.commit()

            if success:
                logger.info(f"Sent notification via {channel.channel_type} to {recipient}")
            else:
                logger.error(f"Failed to send notification: {error}")

        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
