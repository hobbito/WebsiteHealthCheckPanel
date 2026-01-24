import { useState, useEffect } from 'react'
import axios from 'axios'
import type { Site } from '@/lib/types'
import SiteFormModal from './SiteFormModal'
import DeleteSiteModal from './DeleteSiteModal'

interface SitesListProps {
  sites: Site[]
  onRefresh: () => void
}

interface SiteHealth {
  siteId: number
  totalChecks: number
  activeChecks: number
  recentFailures: number
  lastCheckStatus?: 'success' | 'failure' | null
}

export default function SitesList({ sites, onRefresh }: SitesListProps) {
  const [isFormModalOpen, setIsFormModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [selectedSite, setSelectedSite] = useState<Site | undefined>()
  const [healthData, setHealthData] = useState<Map<number, SiteHealth>>(new Map())

  useEffect(() => {
    if (sites.length > 0) {
      loadHealthData()
    }
  }, [sites])

  const loadHealthData = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    const healthMap = new Map<number, SiteHealth>()

    for (const site of sites) {
      try {
        // Get checks for this site
        const checksRes = await axios.get(`/api/v1/checks/?site_id=${site.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        })

        const checks = checksRes.data
        const totalChecks = checks.length
        const activeChecks = checks.filter((c: any) => c.is_enabled).length

        // Get recent results for the first check
        let recentFailures = 0
        let lastCheckStatus = null

        if (checks.length > 0) {
          const resultsRes = await axios.get(`/api/v1/checks/${checks[0].id}/results?limit=10`, {
            headers: { Authorization: `Bearer ${token}` }
          }).catch(() => ({ data: [] }))

          const results = resultsRes.data
          recentFailures = results.filter((r: any) => r.status === 'failure').length
          if (results.length > 0) {
            lastCheckStatus = results[0].status
          }
        }

        healthMap.set(site.id, {
          siteId: site.id,
          totalChecks,
          activeChecks,
          recentFailures,
          lastCheckStatus
        })
      } catch (err) {
        console.error(`Error loading health for site ${site.id}:`, err)
      }
    }

    setHealthData(healthMap)
  }

  const handleAddClick = () => {
    setSelectedSite(undefined)
    setIsFormModalOpen(true)
  }

  const handleEditClick = (site: Site) => {
    setSelectedSite(site)
    setIsFormModalOpen(true)
  }

  const handleDeleteClick = (site: Site) => {
    setSelectedSite(site)
    setIsDeleteModalOpen(true)
  }

  const handleSuccess = () => {
    onRefresh()
  }

  return (
    <>
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-6 sm:p-8">
          <div className="flex justify-between items-center mb-6">
            <button
              onClick={handleAddClick}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Site
            </button>
          </div>

          {sites.length === 0 ? (
            <EmptyState onAddClick={handleAddClick} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sites.map((site) => (
                <SiteCard
                  key={site.id}
                  site={site}
                  health={healthData.get(site.id)}
                  onEdit={() => handleEditClick(site)}
                  onDelete={() => handleDeleteClick(site)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <SiteFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        onSuccess={handleSuccess}
        site={selectedSite}
      />

      {selectedSite && (
        <DeleteSiteModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onSuccess={handleSuccess}
          site={selectedSite}
        />
      )}
    </>
  )
}

interface EmptyStateProps {
  onAddClick: () => void
}

function EmptyState({ onAddClick }: EmptyStateProps) {
  return (
    <div className="text-center py-16 px-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
      <div className="bg-gray-100 rounded-full p-4 w-16 h-16 mx-auto flex items-center justify-center">
        <svg
          className="h-8 w-8 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
          />
        </svg>
      </div>
      <h3 className="mt-4 text-lg font-semibold text-gray-900">No sites yet</h3>
      <p className="mt-2 text-sm text-gray-600 max-w-sm mx-auto">
        Get started by adding your first website to monitor its health and performance.
      </p>
      <div className="mt-6">
        <button
          onClick={onAddClick}
          className="inline-flex items-center px-6 py-3 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Your First Site
        </button>
      </div>
    </div>
  )
}

interface SiteCardProps {
  site: Site
  health?: SiteHealth
  onEdit: () => void
  onDelete: () => void
}

function SiteCard({ site, health, onEdit, onDelete }: SiteCardProps) {
  const handleCardClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) {
      return
    }
    window.location.href = `/dashboard/sites/${site.id}`
  }

  const getHealthStatus = () => {
    if (!health || health.totalChecks === 0) {
      return { color: 'gray', label: 'No checks', icon: '○' }
    }
    if (health.recentFailures > 0) {
      return { color: 'red', label: `${health.recentFailures} failing`, icon: '✗' }
    }
    if (health.lastCheckStatus === 'success') {
      return { color: 'green', label: 'All passing', icon: '✓' }
    }
    return { color: 'yellow', label: 'Unknown', icon: '?' }
  }

  const status = getHealthStatus()

  return (
    <div
      onClick={handleCardClick}
      className="border border-gray-200 rounded-lg p-5 hover:border-blue-400 hover:shadow-sm cursor-pointer bg-white transition-all"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
            {site.name}
          </h3>
          <p className="text-sm text-gray-600 truncate">{site.url}</p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <div className={`inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium ${
          status.color === 'green'
            ? 'bg-green-50 text-green-700 border border-green-200'
            : status.color === 'red'
            ? 'bg-red-50 text-red-700 border border-red-200'
            : 'bg-gray-50 text-gray-700 border border-gray-200'
        }`}>
          <span className="mr-2">{status.icon}</span>
          {status.label}
        </div>
        <div className="text-sm text-gray-500">
          {health?.totalChecks || 0} checks
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={(e) => { e.stopPropagation(); onEdit(); }}
          className="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          Edit
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md border border-gray-200"
          title="Delete site"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  )
}
