/**
 * Zustand stores for state management
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  User,
  Site,
  CheckConfiguration,
  CheckResult,
  Incident,
  NotificationChannel,
  NotificationRule,
  NotificationLog,
} from './types'

// ============ Auth Store ============

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  setTokens: (accessToken: string, refreshToken: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setTokens: (accessToken, refreshToken) => {
        localStorage.setItem('access_token', accessToken)
        localStorage.setItem('refresh_token', refreshToken)
        set({ accessToken, refreshToken })
      },
      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user }),
    }
  )
)

// ============ Sites Store ============

interface SitesState {
  sites: Site[]
  selectedSite: Site | null
  isLoading: boolean
  error: string | null
  setSites: (sites: Site[]) => void
  addSite: (site: Site) => void
  updateSite: (site: Site) => void
  removeSite: (id: number) => void
  setSelectedSite: (site: Site | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useSitesStore = create<SitesState>((set) => ({
  sites: [],
  selectedSite: null,
  isLoading: false,
  error: null,
  setSites: (sites) => set({ sites }),
  addSite: (site) => set((state) => ({ sites: [...state.sites, site] })),
  updateSite: (site) =>
    set((state) => ({
      sites: state.sites.map((s) => (s.id === site.id ? site : s)),
      selectedSite: state.selectedSite?.id === site.id ? site : state.selectedSite,
    })),
  removeSite: (id) =>
    set((state) => ({
      sites: state.sites.filter((s) => s.id !== id),
      selectedSite: state.selectedSite?.id === id ? null : state.selectedSite,
    })),
  setSelectedSite: (site) => set({ selectedSite: site }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}))

// ============ Checks Store ============

interface ChecksState {
  checks: CheckConfiguration[]
  results: Map<number, CheckResult[]>
  isLoading: boolean
  error: string | null
  setChecks: (checks: CheckConfiguration[]) => void
  addCheck: (check: CheckConfiguration) => void
  updateCheck: (check: CheckConfiguration) => void
  removeCheck: (id: number) => void
  setResults: (checkId: number, results: CheckResult[]) => void
  addResult: (checkId: number, result: CheckResult) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useChecksStore = create<ChecksState>((set) => ({
  checks: [],
  results: new Map(),
  isLoading: false,
  error: null,
  setChecks: (checks) => set({ checks }),
  addCheck: (check) => set((state) => ({ checks: [...state.checks, check] })),
  updateCheck: (check) =>
    set((state) => ({
      checks: state.checks.map((c) => (c.id === check.id ? check : c)),
    })),
  removeCheck: (id) =>
    set((state) => ({
      checks: state.checks.filter((c) => c.id !== id),
    })),
  setResults: (checkId, results) =>
    set((state) => {
      const newResults = new Map(state.results)
      newResults.set(checkId, results)
      return { results: newResults }
    }),
  addResult: (checkId, result) =>
    set((state) => {
      const newResults = new Map(state.results)
      const existing = newResults.get(checkId) || []
      newResults.set(checkId, [result, ...existing].slice(0, 100)) // Keep last 100
      return { results: newResults }
    }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}))

// ============ Incidents Store ============

interface IncidentsState {
  incidents: Incident[]
  openIncidents: Incident[]
  isLoading: boolean
  error: string | null
  setIncidents: (incidents: Incident[]) => void
  addIncident: (incident: Incident) => void
  updateIncident: (incident: Incident) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useIncidentsStore = create<IncidentsState>((set) => ({
  incidents: [],
  openIncidents: [],
  isLoading: false,
  error: null,
  setIncidents: (incidents) =>
    set({
      incidents,
      openIncidents: incidents.filter((i) => i.status === 'open'),
    }),
  addIncident: (incident) =>
    set((state) => {
      const incidents = [...state.incidents, incident]
      return {
        incidents,
        openIncidents: incidents.filter((i) => i.status === 'open'),
      }
    }),
  updateIncident: (incident) =>
    set((state) => {
      const incidents = state.incidents.map((i) => (i.id === incident.id ? incident : i))
      return {
        incidents,
        openIncidents: incidents.filter((i) => i.status === 'open'),
      }
    }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}))

// ============ Notifications Store ============

interface NotificationsState {
  channels: NotificationChannel[]
  rules: NotificationRule[]
  logs: NotificationLog[]
  isLoading: boolean
  error: string | null
  setChannels: (channels: NotificationChannel[]) => void
  addChannel: (channel: NotificationChannel) => void
  updateChannel: (channel: NotificationChannel) => void
  removeChannel: (id: number) => void
  setRules: (rules: NotificationRule[]) => void
  addRule: (rule: NotificationRule) => void
  updateRule: (rule: NotificationRule) => void
  removeRule: (id: number) => void
  setLogs: (logs: NotificationLog[]) => void
  addLog: (log: NotificationLog) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useNotificationsStore = create<NotificationsState>((set) => ({
  channels: [],
  rules: [],
  logs: [],
  isLoading: false,
  error: null,
  setChannels: (channels) => set({ channels }),
  addChannel: (channel) => set((state) => ({ channels: [...state.channels, channel] })),
  updateChannel: (channel) =>
    set((state) => ({
      channels: state.channels.map((c) => (c.id === channel.id ? channel : c)),
    })),
  removeChannel: (id) =>
    set((state) => ({
      channels: state.channels.filter((c) => c.id !== id),
    })),
  setRules: (rules) => set({ rules }),
  addRule: (rule) => set((state) => ({ rules: [...state.rules, rule] })),
  updateRule: (rule) =>
    set((state) => ({
      rules: state.rules.map((r) => (r.id === rule.id ? rule : r)),
    })),
  removeRule: (id) =>
    set((state) => ({
      rules: state.rules.filter((r) => r.id !== id),
    })),
  setLogs: (logs) => set({ logs }),
  addLog: (log) => set((state) => ({ logs: [log, ...state.logs].slice(0, 100) })),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}))

// ============ UI Store ============

interface UIState {
  sidebarOpen: boolean
  currentView: string
  notifications: Array<{ id: string; type: 'success' | 'error' | 'info'; message: string }>
  toggleSidebar: () => void
  setCurrentView: (view: string) => void
  addNotification: (type: 'success' | 'error' | 'info', message: string) => void
  removeNotification: (id: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  currentView: 'dashboard',
  notifications: [],
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setCurrentView: (currentView) => set({ currentView }),
  addNotification: (type, message) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { id: Date.now().toString(), type, message },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}))
