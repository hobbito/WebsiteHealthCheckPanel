import type { Site, User } from '@/lib/types'

interface DashboardStatsProps {
  sites: Site[]
  user: User
  totalChecks?: number
  failedChecks?: number
}

export default function DashboardStats({ sites, user, totalChecks = 0, failedChecks = 0 }: DashboardStatsProps) {
  const totalSites = sites.length
  const activeSites = sites.filter(s => s.is_active).length

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
      <StatCard
        title="Total Sites"
        value={totalSites}
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
        }
        iconColor="text-blue-600"
        iconBg="bg-blue-50"
      />
      <StatCard
        title="Active Sites"
        value={activeSites}
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
        iconColor="text-green-600"
        iconBg="bg-green-50"
      />
      <StatCard
        title="Total Checks"
        value={totalChecks}
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        }
        iconColor="text-purple-600"
        iconBg="bg-purple-50"
      />
      <StatCard
        title="Failed Checks"
        value={failedChecks}
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
        iconColor="text-red-600"
        iconBg="bg-red-50"
      />
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string | number
  capitalize?: boolean
  icon: React.ReactNode
  iconColor: string
  iconBg: string
}

function StatCard({ title, value, capitalize, icon, iconColor, iconBg }: StatCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <dt className="text-sm font-medium text-gray-600">
            {title}
          </dt>
          <dd className={`mt-2 text-3xl font-bold text-gray-900 ${capitalize ? 'capitalize' : ''}`}>
            {value}
          </dd>
        </div>
        <div className={`${iconBg} rounded-lg p-3`}>
          <div className={iconColor}>
            {icon}
          </div>
        </div>
      </div>
    </div>
  )
}
