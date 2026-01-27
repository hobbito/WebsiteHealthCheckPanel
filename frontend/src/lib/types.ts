// User types
export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  is_active: boolean
  created_at: string
}

// Site types
export interface Site {
  id: number
  name: string
  url: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// Notification types
export type NotificationTrigger = 'check_failure' | 'check_recovery'

export interface NotificationChannel {
  id: number
  name: string
  channel_type: string
  configuration: Record<string, any>
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface NotificationRule {
  id: number
  name: string
  channel_id: number
  trigger: NotificationTrigger
  site_ids: number[] | null
  check_types: string[] | null
  consecutive_failures: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface NotificationLog {
  id: number
  rule_id: number
  channel_id: number
  trigger: NotificationTrigger
  site_name: string
  check_name: string
  status: 'success' | 'failure'
  error_message: string | null
  sent_at: string
}

export interface ChannelTypeInfo {
  type: string
  display_name: string
  description: string
  config_schema: {
    type: string
    properties: Record<string, any>
    required?: string[]
  }
}

// Check types
export interface CheckTypeInfo {
  type: string
  display_name: string
  description: string
  config_schema: {
    type: string
    properties: Record<string, any>
    required?: string[]
  }
}

export interface CheckConfiguration {
  id: number
  site_id: number
  name: string
  check_type: string
  configuration: Record<string, any>
  interval_seconds: number
  timeout_seconds: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface CheckResult {
  id: number
  check_id: number
  status: 'success' | 'failure'
  response_time_ms: number
  error_message: string | null
  details: Record<string, any>
  checked_at: string
}
