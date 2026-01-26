"""Notification service for handling check results and sending notifications"""
import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    NotificationChannel,
    NotificationRule,
    NotificationLog,
    NotificationStatus,
    NotificationTrigger,
)
from .channels.registry import ChannelRegistry
from .channels.base import NotificationPayload
from app.domains.checks.models import CheckConfiguration, CheckResult, CheckStatus
from app.domains.sites.models import Site

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for processing check results and sending notifications"""

    @staticmethod
    async def handle_check_result(
        db: AsyncSession,
        check_config: CheckConfiguration,
        check_result: CheckResult,
        site: Site
    ) -> None:
        """
        Process a check result and send notifications if rules match.

        Args:
            db: Database session
            check_config: The check configuration
            check_result: The check result to process
            site: The site being checked
        """
        # Determine trigger type based on result status
        trigger: Optional[NotificationTrigger] = None

        if check_result.status == CheckStatus.FAILURE:
            trigger = NotificationTrigger.CHECK_FAILURE
        elif check_result.status == CheckStatus.SUCCESS:
            # Check if this is a recovery (previous was failure)
            is_recovery = await NotificationService._is_recovery(
                db, check_config.id, check_result.id
            )
            if is_recovery:
                trigger = NotificationTrigger.CHECK_RECOVERY

        if not trigger:
            return  # No notification needed

        # Find matching rules
        rules = await NotificationService._find_matching_rules(
            db,
            site.organization_id,
            trigger,
            site.id,
            check_config.check_type,
            check_config.id
        )

        if not rules:
            return  # No matching rules

        # Build notification payload
        payload = NotificationPayload(
            trigger=trigger.value,
            site_name=site.name,
            site_url=site.url,
            check_name=check_config.name,
            check_type=check_config.check_type,
            status=check_result.status.value if isinstance(check_result.status, CheckStatus) else check_result.status,
            error_message=check_result.error_message,
            response_time_ms=int(check_result.response_time_ms) if check_result.response_time_ms else None,
            checked_at=check_result.checked_at or datetime.utcnow(),
        )

        # Send notifications for each matching rule
        for rule in rules:
            await NotificationService._send_notification(
                db, rule, payload, check_result.id
            )

    @staticmethod
    async def _is_recovery(
        db: AsyncSession,
        check_config_id: int,
        current_result_id: int
    ) -> bool:
        """Check if current success is a recovery from previous failure"""
        # Get the previous result (before the current one)
        query = (
            select(CheckResult)
            .where(
                CheckResult.check_configuration_id == check_config_id,
                CheckResult.id < current_result_id
            )
            .order_by(CheckResult.id.desc())
            .limit(1)
        )
        result = await db.execute(query)
        previous_result = result.scalar_one_or_none()

        if previous_result and previous_result.status == CheckStatus.FAILURE:
            return True

        return False

    @staticmethod
    async def _find_matching_rules(
        db: AsyncSession,
        organization_id: int,
        trigger: NotificationTrigger,
        site_id: int,
        check_type: str,
        check_config_id: int
    ) -> List[NotificationRule]:
        """Find enabled rules matching the criteria"""
        # Get all enabled rules for this org and trigger
        query = (
            select(NotificationRule)
            .options(selectinload(NotificationRule.channel))
            .where(
                NotificationRule.organization_id == organization_id,
                NotificationRule.trigger == trigger,
                NotificationRule.is_enabled == True,
            )
        )

        result = await db.execute(query)
        rules = result.scalars().all()

        # Filter rules
        matching = []
        for rule in rules:
            # Skip if channel is disabled
            if not rule.channel or not rule.channel.is_enabled:
                continue

            # Check site filter
            if rule.site_ids and site_id not in rule.site_ids:
                continue

            # Check check_type filter
            if rule.check_types and check_type not in rule.check_types:
                continue

            # Check consecutive failures requirement (only for failure trigger)
            if trigger == NotificationTrigger.CHECK_FAILURE and rule.consecutive_failures > 1:
                consecutive = await NotificationService._count_consecutive_failures(
                    db, check_config_id
                )
                if consecutive < rule.consecutive_failures:
                    continue

            matching.append(rule)

        return matching

    @staticmethod
    async def _count_consecutive_failures(
        db: AsyncSession,
        check_config_id: int
    ) -> int:
        """Count consecutive failures for a check configuration"""
        query = (
            select(CheckResult)
            .where(CheckResult.check_configuration_id == check_config_id)
            .order_by(CheckResult.checked_at.desc())
            .limit(100)  # Reasonable limit
        )

        result = await db.execute(query)
        results = result.scalars().all()

        count = 0
        for r in results:
            if r.status == CheckStatus.FAILURE:
                count += 1
            else:
                break

        return count

    @staticmethod
    async def _send_notification(
        db: AsyncSession,
        rule: NotificationRule,
        payload: NotificationPayload,
        check_result_id: int
    ) -> None:
        """Send notification via the rule's channel"""
        # Create log entry
        log = NotificationLog(
            rule_id=rule.id,
            check_result_id=check_result_id,
            status=NotificationStatus.PENDING,
            sent_at=datetime.utcnow()
        )
        db.add(log)
        await db.flush()

        try:
            # Get channel implementation
            channel_class = ChannelRegistry.get_channel(rule.channel.channel_type.value)
            channel_instance = channel_class()

            # Send notification
            await channel_instance.send(rule.channel.configuration, payload)

            log.status = NotificationStatus.SENT
            logger.info(
                f"Notification sent via {rule.channel.channel_type} for rule '{rule.name}'"
            )

        except Exception as e:
            log.status = NotificationStatus.FAILED
            log.error_message = str(e)
            logger.error(f"Failed to send notification for rule '{rule.name}': {e}")

        await db.commit()

    @staticmethod
    async def send_test_notification(
        db: AsyncSession,
        channel: NotificationChannel
    ) -> bool:
        """Send a test notification through a channel"""
        # Get channel implementation
        channel_class = ChannelRegistry.get_channel(channel.channel_type.value)
        channel_instance = channel_class()

        # Test connection
        return await channel_instance.test_connection(channel.configuration)
