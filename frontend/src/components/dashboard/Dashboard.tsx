import { useEffect, useState } from 'react'
import axios from 'axios'
import type { User, Site } from '@/lib/types'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import DashboardHeader from './DashboardHeader'
import DashboardStats from './DashboardStats'

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null)
  const [sites, setSites] = useState<Site[]>([])
  const [totalChecks, setTotalChecks] = useState(0)
  const [recentResults, setRecentResults] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

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
      // Verify token and get user data
      const userResponse = await axios.get('/api/v1/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setUser(userResponse.data)

      // Load all data in parallel
      await Promise.all([
        loadSites(),
        loadChecks(),
        loadRecentResults()
      ])

      setLoading(false)

    } catch (err: any) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
  }

  const loadSites = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    try {
      const sitesResponse = await axios.get('/api/v1/sites/', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setSites(sitesResponse.data)
    } catch (err) {
      console.error('Error loading sites:', err)
    }
  }

  const loadChecks = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    try {
      const checksResponse = await axios.get('/api/v1/checks/', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setTotalChecks(checksResponse.data.length)
    } catch (err) {
      console.error('Error loading checks:', err)
    }
  }

  const loadRecentResults = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    try {
      const checksResponse = await axios.get('/api/v1/checks/', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (checksResponse.data.length > 0) {
        // Load results for the first few checks
        const resultsPromises = checksResponse.data.slice(0, 5).map((check: any) =>
          axios.get(`/api/v1/checks/${check.id}/results?limit=10`, {
            headers: { Authorization: `Bearer ${token}` }
          }).catch(() => ({ data: [] }))
        )

        const resultsResponses = await Promise.all(resultsPromises)
        const allResults = resultsResponses.flatMap((res, idx) =>
          res.data.map((r: any) => ({
            ...r,
            check_name: checksResponse.data[idx]?.name || 'Unknown',
            site_id: checksResponse.data[idx]?.site_id
          }))
        )

        setRecentResults(allResults.sort((a, b) =>
          new Date(b.checked_at).getTime() - new Date(a.checked_at).getTime()
        ).slice(0, 10))
      }
    } catch (err) {
      console.error('Error loading recent results:', err)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
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
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Overview of your monitoring system</p>
        </div>

        <DashboardStats
          sites={sites}
          user={user}
          totalChecks={totalChecks}
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
                        {result.response_time_ms}ms
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
