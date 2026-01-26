/**
 * TypeScript type definitions for the Health Check Panel
 */

// ============ Auth Types ============

export type UserRole = 'admin' | 'user' | 'viewer'

export interface User {
  id: number
  email: string
  full_name: string | null
  role: UserRole
  is_active: boolean
  organization_id: number
  created_at: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Organization {
  id: number
  name: string
  slug: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// ============ Site Types ============

export interface Site {
  id: number
  name: string
  url: string
  description: string | null
  is_active: boolean
  organization_id: number
  created_at: string
  updated_at: string
}

export interface SiteCreate {
  name: string
  url: string
  description?: string
}

export interface SiteUpdate {
  name?: string
  url?: string
  description?: string
  is_active?: boolean
}

// ============ Check Types ============

export type CheckStatus = 'success' | 'failure' | 'warning'

export type IncidentStatus = 'open' | 'acknowledged' | 'resolved'

export interface CheckTypeInfo {
  type: string
  display_name: string
  description: string
  config_schema: Record<string, any>
}

export interface CheckConfiguration {
  id: number
  site_id: number
  check_type: string
  name: string
  configuration: Record<string, any>
  interval_seconds: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface CheckConfigurationCreate {
  site_id: number
  check_type: string
  name: string
  configuration?: Record<string, any>
  interval_seconds?: number
  is_enabled?: boolean
}

export interface CheckConfigurationUpdate {
  name?: string
  configuration?: Record<string, any>
  interval_seconds?: number
  is_enabled?: boolean
}

export interface CheckResult {
  id: number
  check_configuration_id: number
  status: CheckStatus
  response_time_ms: number | null
  error_message: string | null
  result_data: Record<string, any>
  checked_at: string
}

export interface Incident {
  id: number
  check_configuration_id: number
  status: IncidentStatus
  title: string
  description: string | null
  started_at: string
  acknowledged_at: string | null
  resolved_at: string | null
  failure_count: number
}

// ============ Notification Types ============

export type NotificationChannelType = 'email' | 'webhook' | 'slack' | 'discord'

export type NotificationTrigger =
  | 'check_failure'
  | 'check_recovery'
  | 'incident_opened'
  | 'incident_resolved'

export type NotificationStatus = 'pending' | 'sent' | 'failed'

export interface ChannelTypeInfo {
  type: string
  display_name: string
  config_schema: Record<string, any>
}

export interface NotificationChannel {
  id: number
  organization_id: number
  name: string
  channel_type: NotificationChannelType
  configuration: Record<string, any>
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface NotificationChannelCreate {
  name: string
  channel_type: NotificationChannelType
  configuration: Record<string, any>
  is_enabled?: boolean
}

export interface NotificationChannelUpdate {
  name?: string
  configuration?: Record<string, any>
  is_enabled?: boolean
}

export interface NotificationRule {
  id: number
  organization_id: number
  channel_id: number
  name: string
  trigger: NotificationTrigger
  site_ids: number[] | null
  check_types: string[] | null
  consecutive_failures: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface NotificationRuleCreate {
  name: string
  channel_id: number
  trigger: NotificationTrigger
  site_ids?: number[] | null
  check_types?: string[] | null
  consecutive_failures?: number
  is_enabled?: boolean
}

export interface NotificationRuleUpdate {
  name?: string
  channel_id?: number
  trigger?: NotificationTrigger
  site_ids?: number[] | null
  check_types?: string[] | null
  consecutive_failures?: number
  is_enabled?: boolean
}

export interface NotificationLog {
  id: number
  rule_id: number
  check_result_id: number | null
  incident_id: number | null
  status: NotificationStatus
  error_message: string | null
  sent_at: string
}

export interface TestConnectionResponse {
  success: boolean
  message: string
}

// ============ SSE Event Types ============

export type SSEEventType =
  | 'check_result'
  | 'incident_opened'
  | 'incident_resolved'
  | 'notification_sent'

export interface SSEEvent {
  type: SSEEventType
  data: Record<string, any>
  timestamp: string
}

// ============ API Response Types ============

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ApiError {
  detail: string
  status_code?: number
}
