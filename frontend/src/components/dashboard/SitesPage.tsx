import { useEffect, useState } from 'react'
import { authApi, sitesApi } from '@/lib/api'
import { useAuthStore, useSitesStore } from '@/lib/store'
import { useRealtimeUpdates } from '@/lib/useSSE'
import type { User, Site } from '@/lib/types'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import DashboardHeader from './DashboardHeader'
import SitesList from './SitesList'

export default function SitesPage() {
  const { user, setUser, logout } = useAuthStore()
  const { sites, setSites } = useSitesStore()
  const [loading, setLoading] = useState(true)

  // Connect to SSE for real-time updates
  const { isConnected } = useRealtimeUpdates(!!user)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      window.location.href = '/login'
      return
    }

    try {
      const userData = await authApi.getCurrentUser()
      setUser(userData)
      await loadSites()
      setLoading(false)
    } catch (err: any) {
      logout()
      window.location.href = '/login'
    }
  }

  const loadSites = async () => {
    try {
      const sitesData = await sitesApi.list()
      setSites(sitesData)
    } catch (err) {
      console.error('Error loading sites:', err)
    }
  }

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  if (loading || !user) {
    return <LoadingSpinner />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader user={user} onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Your Sites</h1>
            <p className="text-gray-600 mt-1">Monitor and manage all your websites</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`inline-block w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></span>
            <span className="text-sm text-gray-500">{isConnected ? 'Live' : 'Connecting...'}</span>
          </div>
        </div>

        <SitesList sites={sites} onRefresh={loadSites} />
      </main>
    </div>
  )
}
