import { useEffect, useState } from 'react'
import axios from 'axios'
import type { User, Site } from '@/lib/types'
import LoadingSpinner from '@/components/common/LoadingSpinner'
import DashboardHeader from './DashboardHeader'
import DashboardStats from './DashboardStats'
import SitesList from './SitesList'

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null)
  const [sites, setSites] = useState<Site[]>([])
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

      // Load sites
      const sitesResponse = await axios.get('/api/v1/sites/', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      setSites(sitesResponse.data)
      setLoading(false)

    } catch (err: any) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
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

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader user={user} onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DashboardStats sites={sites} user={user} />
        <SitesList sites={sites} />
      </main>
    </div>
  )
}
