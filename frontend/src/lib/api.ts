/**
 * Centralized API client for the Health Check Panel
 */
import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  User,
  LoginResponse,
  Site,
  SiteCreate,
  SiteUpdate,
  CheckConfiguration,
  CheckConfigurationCreate,
  CheckConfigurationUpdate,
  CheckResult,
  CheckTypeInfo,
  Incident,
  NotificationChannel,
  NotificationChannelCreate,
  NotificationChannelUpdate,
  NotificationRule,
  NotificationRuleCreate,
  NotificationRuleUpdate,
  NotificationLog,
  ChannelTypeInfo,
  TestConnectionResponse,
} from './types'

// Create axios instance with default configuration
const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear tokens and redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// ============ Auth API ============

export const authApi = {
  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<LoginResponse> {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await api.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  /**
   * Register a new user
   */
  async register(data: {
    email: string
    password: string
    full_name?: string
    organization_name: string
  }): Promise<User> {
    const response = await api.post<User>('/auth/register', data)
    return response.data
  },

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },
}

// ============ Sites API ============

export const sitesApi = {
  /**
   * List all sites for the organization
   */
  async list(): Promise<Site[]> {
    const response = await api.get<Site[]>('/sites/')
    return response.data
  },

  /**
   * Get a single site by ID
   */
  async get(id: number): Promise<Site> {
    const response = await api.get<Site>(`/sites/${id}`)
    return response.data
  },

  /**
   * Create a new site
   */
  async create(data: SiteCreate): Promise<Site> {
    const response = await api.post<Site>('/sites/', data)
    return response.data
  },

  /**
   * Update an existing site
   */
  async update(id: number, data: SiteUpdate): Promise<Site> {
    const response = await api.patch<Site>(`/sites/${id}`, data)
    return response.data
  },

  /**
   * Delete a site
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/sites/${id}`)
  },
}

// ============ Checks API ============

export const checksApi = {
  /**
   * List available check types
   */
  async listTypes(): Promise<CheckTypeInfo[]> {
    const response = await api.get<CheckTypeInfo[]>('/checks/types')
    return response.data
  },

  /**
   * List all check configurations, optionally filtered by site
   */
  async list(siteId?: number): Promise<CheckConfiguration[]> {
    const params = siteId ? { site_id: siteId } : {}
    const response = await api.get<CheckConfiguration[]>('/checks/', { params })
    return response.data
  },

  /**
   * Get a single check configuration by ID
   */
  async get(id: number): Promise<CheckConfiguration> {
    const response = await api.get<CheckConfiguration>(`/checks/${id}`)
    return response.data
  },

  /**
   * Create a new check configuration
   */
  async create(data: CheckConfigurationCreate): Promise<CheckConfiguration> {
    const response = await api.post<CheckConfiguration>('/checks/', data)
    return response.data
  },

  /**
   * Update an existing check configuration
   */
  async update(id: number, data: CheckConfigurationUpdate): Promise<CheckConfiguration> {
    const response = await api.patch<CheckConfiguration>(`/checks/${id}`, data)
    return response.data
  },

  /**
   * Delete a check configuration
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/checks/${id}`)
  },

  /**
   * Run a check immediately
   */
  async run(id: number): Promise<CheckResult> {
    const response = await api.post<CheckResult>(`/checks/${id}/run`)
    return response.data
  },

  /**
   * Get check results for a configuration
   */
  async getResults(checkId: number, limit?: number): Promise<CheckResult[]> {
    const params = limit ? { limit } : {}
    const response = await api.get<CheckResult[]>(`/checks/${checkId}/results`, { params })
    return response.data
  },

  /**
   * Get incidents for a check configuration
   */
  async getIncidents(checkId: number): Promise<Incident[]> {
    const response = await api.get<Incident[]>(`/checks/${checkId}/incidents`)
    return response.data
  },
}

// ============ Incidents API ============

export const incidentsApi = {
  /**
   * List all incidents
   */
  async list(status?: string): Promise<Incident[]> {
    const params = status ? { status } : {}
    const response = await api.get<Incident[]>('/incidents/', { params })
    return response.data
  },

  /**
   * Get a single incident
   */
  async get(id: number): Promise<Incident> {
    const response = await api.get<Incident>(`/incidents/${id}`)
    return response.data
  },

  /**
   * Acknowledge an incident
   */
  async acknowledge(id: number): Promise<Incident> {
    const response = await api.post<Incident>(`/incidents/${id}/acknowledge`)
    return response.data
  },

  /**
   * Resolve an incident
   */
  async resolve(id: number): Promise<Incident> {
    const response = await api.post<Incident>(`/incidents/${id}/resolve`)
    return response.data
  },
}

// ============ Notifications API ============

export const notificationsApi = {
  // --- Channel Types ---

  /**
   * List available channel types
   */
  async listChannelTypes(): Promise<ChannelTypeInfo[]> {
    const response = await api.get<ChannelTypeInfo[]>('/notifications/channel-types')
    return response.data
  },

  // --- Channels ---

  /**
   * List all notification channels
   */
  async listChannels(): Promise<NotificationChannel[]> {
    const response = await api.get<NotificationChannel[]>('/notifications/channels')
    return response.data
  },

  /**
   * Get a single channel
   */
  async getChannel(id: number): Promise<NotificationChannel> {
    const response = await api.get<NotificationChannel>(`/notifications/channels/${id}`)
    return response.data
  },

  /**
   * Create a new channel
   */
  async createChannel(data: NotificationChannelCreate): Promise<NotificationChannel> {
    const response = await api.post<NotificationChannel>('/notifications/channels', data)
    return response.data
  },

  /**
   * Update an existing channel
   */
  async updateChannel(id: number, data: NotificationChannelUpdate): Promise<NotificationChannel> {
    const response = await api.patch<NotificationChannel>(`/notifications/channels/${id}`, data)
    return response.data
  },

  /**
   * Delete a channel
   */
  async deleteChannel(id: number): Promise<void> {
    await api.delete(`/notifications/channels/${id}`)
  },

  /**
   * Test a channel connection
   */
  async testChannel(id: number): Promise<TestConnectionResponse> {
    const response = await api.post<TestConnectionResponse>(`/notifications/channels/${id}/test`)
    return response.data
  },

  // --- Rules ---

  /**
   * List all notification rules
   */
  async listRules(): Promise<NotificationRule[]> {
    const response = await api.get<NotificationRule[]>('/notifications/rules')
    return response.data
  },

  /**
   * Get a single rule
   */
  async getRule(id: number): Promise<NotificationRule> {
    const response = await api.get<NotificationRule>(`/notifications/rules/${id}`)
    return response.data
  },

  /**
   * Create a new rule
   */
  async createRule(data: NotificationRuleCreate): Promise<NotificationRule> {
    const response = await api.post<NotificationRule>('/notifications/rules', data)
    return response.data
  },

  /**
   * Update an existing rule
   */
  async updateRule(id: number, data: NotificationRuleUpdate): Promise<NotificationRule> {
    const response = await api.patch<NotificationRule>(`/notifications/rules/${id}`, data)
    return response.data
  },

  /**
   * Delete a rule
   */
  async deleteRule(id: number): Promise<void> {
    await api.delete(`/notifications/rules/${id}`)
  },

  // --- Logs ---

  /**
   * List notification logs
   */
  async listLogs(params?: { limit?: number; offset?: number; rule_id?: number }): Promise<NotificationLog[]> {
    const response = await api.get<NotificationLog[]>('/notifications/logs', { params })
    return response.data
  },
}

// ============ SSE Stream ============

export interface SSECallbacks {
  onCheckResult?: (result: CheckResult) => void
  onIncidentOpened?: (incident: Incident) => void
  onIncidentResolved?: (incident: Incident) => void
  onNotificationSent?: (log: NotificationLog) => void
  onError?: (error: Event) => void
  onOpen?: () => void
}

/**
 * Connect to the SSE event stream for real-time updates
 */
export function connectToEventStream(callbacks: SSECallbacks): EventSource {
  const token = localStorage.getItem('access_token')
  const eventSource = new EventSource(`/api/v1/stream/updates?token=${token}`)

  eventSource.onopen = () => {
    callbacks.onOpen?.()
  }

  eventSource.onerror = (error) => {
    callbacks.onError?.(error)
  }

  eventSource.addEventListener('check_result', (event) => {
    const data = JSON.parse(event.data)
    callbacks.onCheckResult?.(data)
  })

  eventSource.addEventListener('incident_opened', (event) => {
    const data = JSON.parse(event.data)
    callbacks.onIncidentOpened?.(data)
  })

  eventSource.addEventListener('incident_resolved', (event) => {
    const data = JSON.parse(event.data)
    callbacks.onIncidentResolved?.(data)
  })

  eventSource.addEventListener('notification_sent', (event) => {
    const data = JSON.parse(event.data)
    callbacks.onNotificationSent?.(data)
  })

  return eventSource
}

// Export the axios instance for custom requests
export { api }
export default api
