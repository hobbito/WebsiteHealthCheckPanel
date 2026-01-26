"""Update notifications schema v2

Revision ID: add_notifications_v2
Revises: 3c84a22b641b
Create Date: 2026-01-25

This migration updates the notifications tables to the new organization-based schema.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_notifications_v2'
down_revision: Union[str, None] = '3c84a22b641b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old notification tables (they have different schema)
    op.drop_table('notification_logs')
    op.drop_table('notification_rules')
    op.drop_table('notification_channels')

    # Drop old enums
    op.execute("DROP TYPE IF EXISTS notificationchanneltype")
    op.execute("DROP TYPE IF EXISTS notificationseverity")

    # Create new enums using raw SQL (IF NOT EXISTS style)
    op.execute("DO $$ BEGIN CREATE TYPE notificationchanneltype AS ENUM ('EMAIL', 'WEBHOOK'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE notificationtrigger AS ENUM ('CHECK_FAILURE', 'CHECK_RECOVERY', 'INCIDENT_OPENED', 'INCIDENT_RESOLVED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE notificationstatus AS ENUM ('PENDING', 'SENT', 'FAILED'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create notification_channels table
    op.execute("""
        CREATE TABLE IF NOT EXISTS notification_channels (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            channel_type notificationchanneltype NOT NULL,
            configuration JSONB NOT NULL,
            is_enabled BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_channels_id ON notification_channels(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_channels_organization_id ON notification_channels(organization_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_channels_channel_type ON notification_channels(channel_type)")

    # Create notification_rules table
    op.execute("""
        CREATE TABLE IF NOT EXISTS notification_rules (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            channel_id INTEGER NOT NULL REFERENCES notification_channels(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            trigger notificationtrigger NOT NULL,
            site_ids JSONB,
            check_types JSONB,
            consecutive_failures INTEGER NOT NULL DEFAULT 1,
            is_enabled BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_rules_id ON notification_rules(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_rules_organization_id ON notification_rules(organization_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_rules_channel_id ON notification_rules(channel_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_rules_trigger ON notification_rules(trigger)")

    # Create notification_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id SERIAL PRIMARY KEY,
            rule_id INTEGER NOT NULL REFERENCES notification_rules(id) ON DELETE CASCADE,
            check_result_id INTEGER REFERENCES check_results(id) ON DELETE SET NULL,
            incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
            status notificationstatus NOT NULL DEFAULT 'PENDING',
            error_message TEXT,
            sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_id ON notification_logs(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_rule_id ON notification_logs(rule_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_check_result_id ON notification_logs(check_result_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_status ON notification_logs(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notification_logs_sent_at ON notification_logs(sent_at)")


def downgrade() -> None:
    # Drop new tables
    op.drop_table('notification_logs')
    op.drop_table('notification_rules')
    op.drop_table('notification_channels')

    # Drop new enums
    op.execute("DROP TYPE IF EXISTS notificationstatus")
    op.execute("DROP TYPE IF EXISTS notificationtrigger")
    op.execute("DROP TYPE IF EXISTS notificationchanneltype")

    # Recreate old enums
    notificationchanneltype_old = sa.Enum('EMAIL', 'SLACK', 'DISCORD', 'WEBHOOK', name='notificationchanneltype')
    notificationchanneltype_old.create(op.get_bind())

    notificationseverity = sa.Enum('INFO', 'WARNING', 'CRITICAL', name='notificationseverity')
    notificationseverity.create(op.get_bind())

    # Recreate old notification_channels table
    op.create_table('notification_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('channel_type', sa.Enum('EMAIL', 'SLACK', 'DISCORD', 'WEBHOOK', name='notificationchanneltype'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_channels_id'), 'notification_channels', ['id'], unique=False)
    op.create_index(op.f('ix_notification_channels_user_id'), 'notification_channels', ['user_id'], unique=False)

    # Recreate old notification_rules table
    op.create_table('notification_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=False),
        sa.Column('conditions', sa.JSON(), nullable=False),
        sa.Column('min_severity', sa.Enum('INFO', 'WARNING', 'CRITICAL', name='notificationseverity'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['notification_channels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_rules_channel_id'), 'notification_rules', ['channel_id'], unique=False)
    op.create_index(op.f('ix_notification_rules_id'), 'notification_rules', ['id'], unique=False)
    op.create_index(op.f('ix_notification_rules_user_id'), 'notification_rules', ['user_id'], unique=False)

    # Recreate old notification_logs table
    op.create_table('notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.Integer(), nullable=True),
        sa.Column('channel_id', sa.Integer(), nullable=True),
        sa.Column('channel_type', sa.Enum('EMAIL', 'SLACK', 'DISCORD', 'WEBHOOK', name='notificationchanneltype'), nullable=False),
        sa.Column('recipient', sa.String(length=500), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('sent_successfully', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['notification_channels.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_logs_id'), 'notification_logs', ['id'], unique=False)
    op.create_index(op.f('ix_notification_logs_incident_id'), 'notification_logs', ['incident_id'], unique=False)
    op.create_index(op.f('ix_notification_logs_sent_at'), 'notification_logs', ['sent_at'], unique=False)
