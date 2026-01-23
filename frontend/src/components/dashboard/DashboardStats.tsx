import type { Site, User } from '@/lib/types'

interface DashboardStatsProps {
  sites: Site[]
  user: User
}

export default function DashboardStats({ sites, user }: DashboardStatsProps) {
  const totalSites = sites.length
  const activeSites = sites.filter(s => s.is_active).length

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-8">
      <StatCard title="Total Sites" value={totalSites} />
      <StatCard title="Active Sites" value={activeSites} />
      <StatCard title="User Role" value={user.role} capitalize />
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string | number
  capitalize?: boolean
}

function StatCard({ title, value, capitalize }: StatCardProps) {
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-1">
            <dt className="text-sm font-medium text-gray-500 truncate">
              {title}
            </dt>
            <dd className={`mt-1 text-3xl font-semibold text-gray-900 ${capitalize ? 'capitalize' : ''}`}>
              {value}
            </dd>
          </div>
        </div>
      </div>
    </div>
  )
}
