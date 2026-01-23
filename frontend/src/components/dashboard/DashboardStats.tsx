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
      <StatCard
        title="Total Sites"
        value={totalSites}
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
        }
        gradientFrom="from-blue-500"
        gradientTo="to-blue-600"
      />
      <StatCard
        title="Active Sites"
        value={activeSites}
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
        gradientFrom="from-green-500"
        gradientTo="to-green-600"
      />
      <StatCard
        title="User Role"
        value={user.role}
        capitalize
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        }
        gradientFrom="from-purple-500"
        gradientTo="to-purple-600"
      />
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string | number
  capitalize?: boolean
  icon: React.ReactNode
  gradientFrom: string
  gradientTo: string
}

function StatCard({ title, value, capitalize, icon, gradientFrom, gradientTo }: StatCardProps) {
  return (
    <div className="bg-white overflow-hidden shadow-lg rounded-2xl border border-gray-100 hover:shadow-xl transition-shadow duration-200">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <dt className="text-sm font-medium text-gray-600 truncate">
              {title}
            </dt>
            <dd className={`mt-2 text-3xl font-bold text-gray-900 ${capitalize ? 'capitalize' : ''}`}>
              {value}
            </dd>
          </div>
          <div className={`bg-gradient-to-br ${gradientFrom} ${gradientTo} rounded-xl p-3 shadow-lg`}>
            <div className="text-white">
              {icon}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
