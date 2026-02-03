-- Health Check Panel - Supabase Schema
-- Run this SQL in your Supabase SQL Editor to create all necessary tables

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE user_role AS ENUM ('admin', 'user', 'viewer');
CREATE TYPE check_status AS ENUM ('success', 'failure', 'warning');
CREATE TYPE incident_status AS ENUM ('open', 'acknowledged', 'resolved');
CREATE TYPE notification_channel_type AS ENUM ('email', 'webhook');
CREATE TYPE notification_trigger AS ENUM ('check_failure', 'check_recovery', 'incident_opened', 'incident_resolved');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed');

-- Organizations table
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_organizations_slug ON organizations(slug);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role DEFAULT 'user' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_login TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_organization ON users(organization_id);

-- Sites table
CREATE TABLE sites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_sites_organization ON sites(organization_id);

-- Check configurations table
CREATE TABLE check_configurations (
    id SERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    check_type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    configuration JSONB DEFAULT '{}' NOT NULL,
    interval_seconds INTEGER DEFAULT 300 NOT NULL,
    is_enabled BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_check_configurations_site ON check_configurations(site_id);
CREATE INDEX idx_check_configurations_type ON check_configurations(check_type);

-- Check results table
CREATE TABLE check_results (
    id SERIAL PRIMARY KEY,
    check_configuration_id INTEGER NOT NULL REFERENCES check_configurations(id) ON DELETE CASCADE,
    status check_status NOT NULL,
    response_time_ms FLOAT,
    error_message TEXT,
    result_data JSONB,
    checked_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_check_results_config ON check_results(check_configuration_id);
CREATE INDEX idx_check_results_status ON check_results(status);
CREATE INDEX idx_check_results_checked_at ON check_results(checked_at);

-- Incidents table
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    check_configuration_id INTEGER NOT NULL REFERENCES check_configurations(id) ON DELETE CASCADE,
    status incident_status DEFAULT 'open' NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    failure_count INTEGER DEFAULT 1 NOT NULL
);

CREATE INDEX idx_incidents_config ON incidents(check_configuration_id);
CREATE INDEX idx_incidents_status ON incidents(status);

-- Notification channels table
CREATE TABLE notification_channels (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    channel_type notification_channel_type NOT NULL,
    configuration JSONB DEFAULT '{}' NOT NULL,
    is_enabled BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_notification_channels_org ON notification_channels(organization_id);
CREATE INDEX idx_notification_channels_type ON notification_channels(channel_type);

-- Notification rules table
CREATE TABLE notification_rules (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    channel_id INTEGER NOT NULL REFERENCES notification_channels(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    trigger notification_trigger NOT NULL,
    site_ids JSONB,
    check_types JSONB,
    consecutive_failures INTEGER DEFAULT 1 NOT NULL,
    is_enabled BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_notification_rules_org ON notification_rules(organization_id);
CREATE INDEX idx_notification_rules_channel ON notification_rules(channel_id);
CREATE INDEX idx_notification_rules_trigger ON notification_rules(trigger);

-- Notification logs table
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES notification_rules(id) ON DELETE CASCADE,
    check_result_id INTEGER REFERENCES check_results(id) ON DELETE SET NULL,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
    status notification_status DEFAULT 'pending' NOT NULL,
    error_message TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_notification_logs_rule ON notification_logs(rule_id);
CREATE INDEX idx_notification_logs_status ON notification_logs(status);
CREATE INDEX idx_notification_logs_sent_at ON notification_logs(sent_at);

-- Updated at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sites_updated_at BEFORE UPDATE ON sites FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_check_configurations_updated_at BEFORE UPDATE ON check_configurations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_channels_updated_at BEFORE UPDATE ON notification_channels FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_rules_updated_at BEFORE UPDATE ON notification_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default organization and admin user
-- Password: adminadmin (hashed with bcrypt)
INSERT INTO organizations (name, slug, is_active) VALUES ('Default Organization', 'default', true);

INSERT INTO users (email, hashed_password, full_name, role, is_active, is_verified, organization_id)
VALUES (
    'admin@admin.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.mSyt6i5mvXkDXS',
    'Admin User',
    'admin',
    true,
    true,
    1
);

-- Grant permissions (for Supabase RLS - optional, enable if using Row Level Security)
-- ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sites ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE check_configurations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE check_results ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE notification_channels ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE notification_rules ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;
