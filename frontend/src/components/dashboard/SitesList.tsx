import type { Site } from '@/lib/types'

interface SitesListProps {
  sites: Site[]
}

export default function SitesList({ sites }: SitesListProps) {
  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Your Sites</h3>
          <button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition">
            Add Site
          </button>
        </div>

        {sites.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-4">
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
    <div className="text-center py-12">
      <svg
        className="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 className="mt-2 text-sm font-medium text-gray-900">No sites yet</h3>
      <p className="mt-1 text-sm text-gray-500">
        Get started by adding your first site to monitor.
      </p>
      <div className="mt-6">
        <button className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition">
          Add Site
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
    <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition cursor-pointer">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-lg font-medium text-gray-900">
            {site.name}
          </h4>
          <p className="text-sm text-gray-500 mt-1">{site.url}</p>
        </div>
        <div>
          {site.is_active ? (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              Active
            </span>
          ) : (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
              Inactive
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
