import type { Site } from '@/lib/types'

interface SitesListProps {
  sites: Site[]
}

export default function SitesList({ sites }: SitesListProps) {
  return (
    <div className="bg-white shadow-xl rounded-2xl border border-gray-100">
      <div className="px-6 py-6 sm:p-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900">Your Sites</h3>
            <p className="text-sm text-gray-600 mt-1">Monitor and manage your websites</p>
          </div>
          <button className="inline-flex items-center px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Site
          </button>
        </div>

        {sites.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-3">
            {sites.map((site) => (
              <SiteCard key={site.id} site={site} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-16 px-4 bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl">
      <div className="bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl p-4 w-16 h-16 mx-auto flex items-center justify-center">
        <svg
          className="h-8 w-8 text-blue-600"
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
        <button className="inline-flex items-center px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200">
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
}

function SiteCard({ site }: SiteCardProps) {
  return (
    <div className="group border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-lg transition-all duration-200 cursor-pointer bg-gradient-to-br from-white to-gray-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 flex-1">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-2.5 shadow-md group-hover:shadow-lg transition-shadow">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-base font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
              {site.name}
            </h4>
            <p className="text-sm text-gray-600 mt-0.5 truncate">{site.url}</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {site.is_active ? (
            <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md">
              <span className="w-1.5 h-1.5 bg-white rounded-full mr-2 animate-pulse"></span>
              Active
            </span>
          ) : (
            <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-semibold bg-gray-200 text-gray-700">
              <span className="w-1.5 h-1.5 bg-gray-500 rounded-full mr-2"></span>
              Inactive
            </span>
          )}
          <svg className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </div>
  )
}
