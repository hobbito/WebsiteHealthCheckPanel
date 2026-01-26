import { useEffect, useState, useCallback } from 'react'
import { authApi, sitesApi, checksApi } from '@/lib/api'
import { useAuthStore, useSitesStore, useChecksStore } from '@/lib/store'
import { useRealtimeUpdates } from '@/lib/useSSE'
import type { User, Site, CheckResult, CheckConfiguration } from '@/lib/types'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import DashboardHeader from './DashboardHeader'
import DashboardStats from './DashboardStats'

export default function Dashboard() {
  const { user, setUser, logout } = useAuthStore()
  const { sites, setSites } = useSitesStore()
  const { checks, setChecks, results, setResults, addResult } = useChecksStore()
  const [loading, setLoading] = useState(true)
  const [recentResults, setRecentResults] = useState<(CheckResult & { check_name: string })[]>([])

  // Connect to SSE for real-time updates
  const { isConnected } = useRealtimeUpdates(!!user)

  // Handle real-time check result updates
  const handleNewResult = useCallback((result: CheckResult) => {
    const check = checks.find(c => c.id === result.check_configuration_id)
    if (check) {
      setRecentResults(prev => [{
        ...result,
        check_name: check.name
      }, ...prev].slice(0, 10))
    }
  }, [checks])

  useEffect(() => {
    checkAuth()
  }, [])

  // Update recent results when checks store is updated
  useEffect(() => {
    if (checks.length > 0) {
      updateRecentResults()
    }
  }, [results])

  const updateRecentResults = () => {
    const allResults: (CheckResult & { check_name: string })[] = []
    checks.forEach(check => {
      const checkResults = results.get(check.id) || []
      checkResults.forEach(result => {
        allResults.push({
          ...result,
          check_name: check.name
        })
      })
    })

    allResults.sort((a, b) =>
      new Date(b.checked_at).getTime() - new Date(a.checked_at).getTime()
    )

    setRecentResults(allResults.slice(0, 10))
  }

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      window.location.href = '/login'
      return
    }

    try {
      const userData = await authApi.getCurrentUser()
      setUser(userData)

      // Load all data in parallel
      await Promise.all([
        loadSites(),
        loadChecksAndResults()
      ])

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

  const loadChecksAndResults = async () => {
    try {
      const checksData = await checksApi.list()
      setChecks(checksData)

      // Load results for each check
      const resultsPromises = checksData.slice(0, 10).map(async (check) => {
        try {
          const checkResults = await checksApi.getResults(check.id, 10)
          setResults(check.id, checkResults)
        } catch (err) {
          console.error(`Error loading results for check ${check.id}:`, err)
        }
      })

      await Promise.all(resultsPromises)
    } catch (err) {
      console.error('Error loading checks:', err)
    }
  }

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  if (loading || !user) {
    return <LoadingSpinner />
  }

  const failedChecks = recentResults.filter(r => r.status === 'failure').length

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader user={user} onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">Overview of your monitoring system</p>
          </div>
          {/* Real-time connection indicator */}
          <div className="flex items-center gap-2">
            <span className={`inline-block w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></span>
            <span className="text-sm text-gray-500">
              {isConnected ? 'Live' : 'Connecting...'}
            </span>
          </div>
        </div>

        <DashboardStats
          sites={sites}
          user={user}
          totalChecks={checks.length}
          failedChecks={failedChecks}
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Sites */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Your Sites</h2>
              <a
                href="/dashboard/sites"
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                View all →
              </a>
            </div>
            {sites.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No sites yet</p>
                <a
                  href="/dashboard/sites"
                  className="inline-block mt-3 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  Add Your First Site
                </a>
              </div>
            ) : (
              <div className="space-y-3">
                {sites.slice(0, 5).map((site) => (
                  <a
                    key={site.id}
                    href={`/dashboard/sites/${site.id}`}
                    className="block border border-gray-200 rounded-lg p-4 hover:border-blue-400 hover:bg-gray-50"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{site.name}</h3>
                        <p className="text-sm text-gray-600 mt-0.5">{site.url}</p>
                      </div>
                      {site.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-700 border border-gray-300">
                          Inactive
                        </span>
                      )}
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>

          {/* Recent Results */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Check Results</h2>
            {recentResults.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No check results yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {recentResults.map((result) => (
                  <div
                    key={result.id}
                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {result.check_name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(result.checked_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 ml-4">
                      <span className="text-sm text-gray-600">
                        {result.response_time_ms ?? '-'}ms
                      </span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        result.status === 'success'
                          ? 'bg-green-50 text-green-700 border border-green-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        {result.status === 'success' ? '✓' : '✗'} {result.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
