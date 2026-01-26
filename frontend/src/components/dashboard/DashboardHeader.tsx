import type { User } from '@/lib/types'

interface DashboardHeaderProps {
  user: User
  onLogout: () => void
}

export default function DashboardHeader({ user, onLogout }: DashboardHeaderProps) {
  const currentPath = typeof window !== 'undefined' ? window.location.pathname : ''

  const isActive = (path: string) => {
    if (path === '/dashboard' && currentPath === '/dashboard') return true
    if (path !== '/dashboard' && currentPath.startsWith(path)) return true
    return false
  }

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <a href="/dashboard" className="flex items-center space-x-3">
              <div className="bg-blue-600 rounded-lg p-2">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="text-xl font-bold text-gray-900">Health Check Panel</span>
            </a>

            <nav className="hidden md:flex space-x-1">
              <a
                href="/dashboard"
                className={`px-3 py-2 text-sm font-medium rounded-md ${
                  isActive('/dashboard')
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                Dashboard
              </a>
              <a
                href="/dashboard/sites"
                className={`px-3 py-2 text-sm font-medium rounded-md ${
                  isActive('/dashboard/sites')
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                Sites
              </a>
              <a
                href="/dashboard/notifications"
                className={`px-3 py-2 text-sm font-medium rounded-md ${
                  isActive('/dashboard/notifications')
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                Notifications
              </a>
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900">{user.full_name || 'User'}</div>
              <div className="text-xs text-gray-500">{user.email}</div>
            </div>
            <button
              onClick={onLogout}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
