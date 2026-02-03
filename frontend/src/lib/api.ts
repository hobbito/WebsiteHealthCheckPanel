import axios from 'axios'
import type {
  User,
  Site,
  NotificationChannel,
  NotificationRule,
  NotificationLog,
  ChannelTypeInfo,
  CheckTypeInfo,
} from './types'

// Get API base URL from environment or use relative path
const getApiBaseUrl = () => {
  // In browser, check for runtime config or use relative path
  if (typeof window !== 'undefined') {
    return (window as any).__API_URL__ || import.meta.env.PUBLIC_API_URL || '/api/v1'
  }
  return import.meta.env.PUBLIC_API_URL || '/api/v1'
}

// Helper to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token')
  return {
    Authorization: `Bearer ${token}`,
  }
}

// Axios instance with default config
const api = axios.create({
  baseURL: getApiBaseUrl(),
})

// Add auth header interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth API
export const authApi = {
  login: async (email: string, password: string): Promise<{ access_token: string; refresh_token: string }> => {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me')
    return response.data
  },

  register: async (data: { email: string; username: string; password: string }): Promise<User> => {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  refreshToken: async (refreshToken: string): Promise<{ access_token: string }> => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },
}

// Sites API
export const sitesApi = {
  list: async (): Promise<Site[]> => {
    const response = await api.get('/sites/')
    return response.data
  },

  get: async (id: number): Promise<Site> => {
    const response = await api.get(`/sites/${id}`)
    return response.data
  },

  create: async (data: Partial<Site>): Promise<Site> => {
    const response = await api.post('/sites/', data)
    return response.data
  },

  update: async (id: number, data: Partial<Site>): Promise<Site> => {
    const response = await api.put(`/sites/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/sites/${id}`)
  },
}

// Checks API
export const checksApi = {
  listTypes: async (): Promise<CheckTypeInfo[]> => {
    const response = await api.get('/checks/types')
    return response.data
  },

  list: async (siteId?: number): Promise<any[]> => {
    const url = siteId ? `/checks/?site_id=${siteId}` : '/checks/'
    const response = await api.get(url)
    return response.data
  },

  get: async (id: number): Promise<any> => {
    const response = await api.get(`/checks/${id}`)
    return response.data
  },

  create: async (data: any): Promise<any> => {
    const response = await api.post('/checks/', data)
    return response.data
  },

  update: async (id: number, data: any): Promise<any> => {
    const response = await api.put(`/checks/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/checks/${id}`)
  },

  runNow: async (id: number): Promise<any> => {
    const response = await api.post(`/checks/${id}/run-now`)
    return response.data
  },

  getResults: async (id: number, limit = 10): Promise<any[]> => {
    const response = await api.get(`/checks/${id}/results?limit=${limit}`)
    return response.data
  },
}

// Notifications API
export const notificationsApi = {
  // Channels
  listChannels: async (): Promise<NotificationChannel[]> => {
    const response = await api.get('/notifications/channels/')
    return response.data
  },

  getChannel: async (id: number): Promise<NotificationChannel> => {
    const response = await api.get(`/notifications/channels/${id}`)
    return response.data
  },

  createChannel: async (data: {
    name: string
    channel_type: string
    configuration: Record<string, any>
    is_enabled?: boolean
  }): Promise<NotificationChannel> => {
    const response = await api.post('/notifications/channels/', data)
    return response.data
  },

  updateChannel: async (
    id: number,
    data: {
      name?: string
      configuration?: Record<string, any>
      is_enabled?: boolean
    }
  ): Promise<NotificationChannel> => {
    const response = await api.put(`/notifications/channels/${id}`, data)
    return response.data
  },

  deleteChannel: async (id: number): Promise<void> => {
    await api.delete(`/notifications/channels/${id}`)
  },

  testChannel: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/notifications/channels/${id}/test`)
    return response.data
  },

  listChannelTypes: async (): Promise<ChannelTypeInfo[]> => {
    const response = await api.get('/notifications/channels/types')
    return response.data
  },

  // Rules
  listRules: async (): Promise<NotificationRule[]> => {
    const response = await api.get('/notifications/rules/')
    return response.data
  },

  getRule: async (id: number): Promise<NotificationRule> => {
    const response = await api.get(`/notifications/rules/${id}`)
    return response.data
  },

  createRule: async (data: {
    name: string
    channel_id: number
    trigger: string
    site_ids?: number[] | null
    check_types?: string[] | null
    consecutive_failures?: number
    is_enabled?: boolean
  }): Promise<NotificationRule> => {
    const response = await api.post('/notifications/rules/', data)
    return response.data
  },

  updateRule: async (
    id: number,
    data: {
      name?: string
      channel_id?: number
      trigger?: string
      site_ids?: number[] | null
      check_types?: string[] | null
      consecutive_failures?: number
      is_enabled?: boolean
    }
  ): Promise<NotificationRule> => {
    const response = await api.put(`/notifications/rules/${id}`, data)
    return response.data
  },

  deleteRule: async (id: number): Promise<void> => {
    await api.delete(`/notifications/rules/${id}`)
  },

  // Logs
  listLogs: async (params?: { limit?: number; offset?: number }): Promise<NotificationLog[]> => {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    const response = await api.get(`/notifications/logs/?${queryParams.toString()}`)
    return response.data
  },
}
