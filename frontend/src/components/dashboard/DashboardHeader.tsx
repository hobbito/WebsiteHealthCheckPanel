import type { User } from '@/lib/types'

interface DashboardHeaderProps {
  user: User
  onLogout: () => void
}

export default function DashboardHeader({ user, onLogout }: DashboardHeaderProps) {
  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Health Check Panel</h1>
            <p className="text-sm text-gray-600 mt-1">
              Welcome, {user.full_name || user.email}
            </p>
          </div>
          <button
            onClick={onLogout}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}
