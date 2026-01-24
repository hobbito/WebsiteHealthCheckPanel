import { useEffect, useState } from 'react'
import axios from 'axios'
import type { Site } from '@/lib/types'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import DashboardHeader from './DashboardHeader'
import CheckFormModal from './CheckFormModal'
import SiteFormModal from './SiteFormModal'
import DeleteSiteModal from './DeleteSiteModal'

interface SiteDetailProps {
  siteId: string
}

export default function SiteDetail({ siteId }: SiteDetailProps) {
  const [user, setUser] = useState<any>(null)
  const [site, setSite] = useState<Site | null>(null)
  const [checks, setChecks] = useState<any[]>([])
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [isCheckModalOpen, setIsCheckModalOpen] = useState(false)
  const [selectedCheck, setSelectedCheck] = useState<any>(undefined)
  const [isSiteModalOpen, setIsSiteModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)

  useEffect(() => {
    loadData()
  }, [siteId])

  const loadData = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      window.location.href = '/login'
      return
    }

    try {
      const [userRes, siteRes, checksRes] = await Promise.all([
        axios.get('/api/v1/auth/me', { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`/api/v1/sites/${siteId}`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`/api/v1/checks/?site_id=${siteId}`, { headers: { Authorization: `Bearer ${token}` } })
      ])

      setUser(userRes.data)
      setSite(siteRes.data)
      setChecks(checksRes.data)

      // Load recent results if there are checks
      if (checksRes.data.length > 0) {
        const resultsPromises = checksRes.data.slice(0, 3).map((check: any) =>
          axios.get(`/api/v1/checks/${check.id}/results?limit=5`, {
            headers: { Authorization: `Bearer ${token}` }
          })
        )
        const resultsResponses = await Promise.all(resultsPromises)
        const allResults = resultsResponses.flatMap((res, idx) =>
          res.data.map((r: any) => ({ ...r, check_name: checksRes.data[idx].name }))
        )
        setResults(allResults.sort((a, b) =>
          new Date(b.checked_at).getTime() - new Date(a.checked_at).getTime()
        ))
      }

      setLoading(false)
    } catch (err) {
      console.error('Error loading data:', err)
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.clear()
    window.location.href = '/login'
  }

  const handleAddCheck = () => {
    setSelectedCheck(undefined)
    setIsCheckModalOpen(true)
  }

  const handleEditCheck = (check: any) => {
    setSelectedCheck(check)
    setIsCheckModalOpen(true)
  }

  const handleRunCheck = async (checkId: number) => {
    const token = localStorage.getItem('access_token')
    try {
      await axios.post(`/api/v1/checks/${checkId}/run-now`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      // Reload data after a short delay to see results
      setTimeout(() => loadData(), 2000)
    } catch (err) {
      console.error('Error running check:', err)
    }
  }

  const handleCheckSuccess = () => {
    loadData()
  }

  const handleDeleteCheck = async (checkId: number) => {
    if (!confirm('Are you sure you want to delete this check? This action cannot be undone.')) {
      return
    }

    const token = localStorage.getItem('access_token')
    try {
      await axios.delete(`/api/v1/checks/${checkId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      loadData()
    } catch (err) {
      console.error('Error deleting check:', err)
      alert('Failed to delete check')
    }
  }

  const handleEditSite = () => {
    setIsSiteModalOpen(true)
  }

  const handleDeleteSite = () => {
    setIsDeleteModalOpen(true)
  }

  const handleSiteSuccess = () => {
    loadData()
  }

  const handleDeleteSuccess = () => {
    window.location.href = '/dashboard/sites'
  }

  if (loading || !site || !user) {
    return <LoadingSpinner />
  }

  const totalChecks = checks.length
  const activeChecks = checks.filter(c => c.is_enabled).length
  const failedResults = results.filter(r => r.status === 'FAILURE').length

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader user={user} onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-6">
          <a href="/dashboard" className="hover:text-gray-900">Dashboard</a>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <a href="/dashboard/sites" className="hover:text-gray-900">Sites</a>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-gray-900 font-medium">{site.name}</span>
        </nav>

        {/* Site Header */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-4">
              <div className="bg-blue-600 rounded-lg p-3">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{site.name}</h1>
                <a href={site.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-700 mt-1 inline-flex items-center">
                  {site.url}
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {site.is_active ? (
                <span className="inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium bg-green-50 text-green-700 border border-green-200">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Active
                </span>
              ) : (
                <span className="inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium bg-gray-100 text-gray-700 border border-gray-300">
                  <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                  Inactive
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={handleEditSite}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit Site
            </button>
            <button
              onClick={handleDeleteSite}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-300 rounded-md hover:bg-red-50"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete Site
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Uptime</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">-</p>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Response</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">-</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Checks</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{totalChecks}</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Recent Failures</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{failedResults}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-3">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Checks Section */}
        <div className="bg-white border border-gray-200 rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Health Checks</h2>
              <p className="text-sm text-gray-600 mt-0.5">{activeChecks} of {totalChecks} active</p>
            </div>
            <button
              onClick={handleAddCheck}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Check
            </button>
          </div>

          <div className="p-6">
            {checks.length === 0 ? (
              <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="bg-gray-100 rounded-full p-3 w-12 h-12 mx-auto flex items-center justify-center">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
                <h3 className="mt-4 text-sm font-medium text-gray-900">No checks configured</h3>
                <p className="mt-1 text-sm text-gray-500">Get started by creating your first health check.</p>
                <button
                  onClick={handleAddCheck}
                  className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add Your First Check
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {checks.map((check) => (
                  <div key={check.id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-sm">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <div className={`${check.is_enabled ? 'bg-blue-50' : 'bg-gray-100'} rounded-lg p-2.5`}>
                          <svg className={`w-5 h-5 ${check.is_enabled ? 'text-blue-600' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-gray-900">{check.name}</h3>
                            {!check.is_enabled && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 border border-gray-300">
                                Disabled
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-sm text-gray-600">
                            <span className="inline-flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                              </svg>
                              {check.check_type.toUpperCase()}
                            </span>
                            <span className="inline-flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              Every {Math.floor(check.interval_seconds / 60)} min
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => handleEditCheck(check)}
                          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
                          title="Edit check"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDeleteCheck(check.id)}
                          className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-md"
                          title="Delete check"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleRunCheck(check.id)}
                          className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50"
                          title="Run check now"
                        >
                          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Run Now
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Results */}
        {results.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Recent Results</h2>
              <p className="text-sm text-gray-600 mt-0.5">Latest check executions</p>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {results.map((result) => (
                  <div key={result.id} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`${result.status === 'success' ? 'bg-green-50' : 'bg-red-50'} rounded-lg p-2`}>
                        {result.status === 'success' ? (
                          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{result.check_name}</p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {new Date(result.checked_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-900">{result.response_time_ms}ms</span>
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium ${
                        result.status === 'success'
                          ? 'bg-green-50 text-green-700 border border-green-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        {result.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        <CheckFormModal
          isOpen={isCheckModalOpen}
          onClose={() => setIsCheckModalOpen(false)}
          onSuccess={handleCheckSuccess}
          siteId={parseInt(siteId)}
          check={selectedCheck}
        />

        <SiteFormModal
          isOpen={isSiteModalOpen}
          onClose={() => setIsSiteModalOpen(false)}
          onSuccess={handleSiteSuccess}
          site={site}
        />

        {site && (
          <DeleteSiteModal
            isOpen={isDeleteModalOpen}
            onClose={() => setIsDeleteModalOpen(false)}
            onSuccess={handleDeleteSuccess}
            site={site}
          />
        )}
      </main>
    </div>
  )
}
