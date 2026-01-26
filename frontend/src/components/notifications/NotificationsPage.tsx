import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { notificationsApi, sitesApi, checksApi } from '../../lib/api'
import type {
  NotificationChannel,
  NotificationRule,
  NotificationLog,
  ChannelTypeInfo,
  Site,
  CheckTypeInfo,
  User,
} from '../../lib/types'
import DashboardHeader from '../dashboard/DashboardHeader'
import LoadingSpinner from '../common/LoadingSpinner'
import ChannelsList from './ChannelsList'
import ChannelFormModal from './ChannelFormModal'
import RulesList from './RulesList'
import RuleFormModal from './RuleFormModal'
import LogsList from './LogsList'

type Tab = 'channels' | 'rules' | 'logs'

export default function NotificationsPage() {
  const [user, setUser] = useState<User | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('channels')
  const [channels, setChannels] = useState<NotificationChannel[]>([])
  const [rules, setRules] = useState<NotificationRule[]>([])
  const [logs, setLogs] = useState<NotificationLog[]>([])
  const [channelTypes, setChannelTypes] = useState<ChannelTypeInfo[]>([])
  const [sites, setSites] = useState<Site[]>([])
  const [checkTypes, setCheckTypes] = useState<CheckTypeInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal state
  const [showChannelModal, setShowChannelModal] = useState(false)
  const [showRuleModal, setShowRuleModal] = useState(false)
  const [editingChannel, setEditingChannel] = useState<NotificationChannel | null>(null)
  const [editingRule, setEditingRule] = useState<NotificationRule | null>(null)

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
      await loadData()
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

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [channelsData, rulesData, logsData, channelTypesData, sitesData, checkTypesData] =
        await Promise.all([
          notificationsApi.listChannels(),
          notificationsApi.listRules(),
          notificationsApi.listLogs({ limit: 50 }),
          notificationsApi.listChannelTypes(),
          sitesApi.list(),
          checksApi.listTypes(),
        ])

      setChannels(channelsData)
      setRules(rulesData)
      setLogs(logsData)
      setChannelTypes(channelTypesData)
      setSites(sitesData)
      setCheckTypes(checkTypesData)
    } catch (err: any) {
      // Check if it's an auth error
      if (err.response?.status === 401) {
        window.location.href = '/login'
        return
      }
      setError(err.response?.data?.detail || 'Failed to load notifications data')
      console.error('Error loading notifications:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateChannel = () => {
    setEditingChannel(null)
    setShowChannelModal(true)
  }

  const handleEditChannel = (channel: NotificationChannel) => {
    setEditingChannel(channel)
    setShowChannelModal(true)
  }

  const handleDeleteChannel = async (id: number) => {
    if (!confirm('Are you sure you want to delete this channel?')) return

    try {
      await notificationsApi.deleteChannel(id)
      setChannels(channels.filter((c) => c.id !== id))
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete channel')
    }
  }

  const handleTestChannel = async (id: number) => {
    try {
      const result = await notificationsApi.testChannel(id)
      alert(result.message || 'Test notification sent successfully!')
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Test failed')
    }
  }

  const handleChannelSaved = (channel: NotificationChannel) => {
    if (editingChannel) {
      setChannels(channels.map((c) => (c.id === channel.id ? channel : c)))
    } else {
      setChannels([...channels, channel])
    }
    setShowChannelModal(false)
    setEditingChannel(null)
  }

  const handleCreateRule = () => {
    setEditingRule(null)
    setShowRuleModal(true)
  }

  const handleEditRule = (rule: NotificationRule) => {
    setEditingRule(rule)
    setShowRuleModal(true)
  }

  const handleDeleteRule = async (id: number) => {
    if (!confirm('Are you sure you want to delete this rule?')) return

    try {
      await notificationsApi.deleteRule(id)
      setRules(rules.filter((r) => r.id !== id))
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete rule')
    }
  }

  const handleRuleSaved = (rule: NotificationRule) => {
    if (editingRule) {
      setRules(rules.map((r) => (r.id === rule.id ? rule : r)))
    } else {
      setRules([...rules, rule])
    }
    setShowRuleModal(false)
    setEditingRule(null)
  }

  if (loading || !user) {
    return <LoadingSpinner />
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <DashboardHeader user={user} onLogout={handleLogout} />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
            <button onClick={loadData} className="ml-4 underline">
              Retry
            </button>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader user={user} onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
              <p className="text-gray-600 mt-1">Configure how you receive alerts</p>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('channels')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'channels'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Channels ({channels.length})
              </button>
              <button
                onClick={() => setActiveTab('rules')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'rules'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Rules ({rules.length})
              </button>
              <button
                onClick={() => setActiveTab('logs')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'logs'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Logs
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'channels' && (
            <ChannelsList
              channels={channels}
              onCreateChannel={handleCreateChannel}
              onEditChannel={handleEditChannel}
              onDeleteChannel={handleDeleteChannel}
              onTestChannel={handleTestChannel}
            />
          )}

          {activeTab === 'rules' && (
            <RulesList
              rules={rules}
              channels={channels}
              sites={sites}
              onCreateRule={handleCreateRule}
              onEditRule={handleEditRule}
              onDeleteRule={handleDeleteRule}
            />
          )}

          {activeTab === 'logs' && <LogsList logs={logs} rules={rules} />}

          {/* Modals */}
          {showChannelModal && (
            <ChannelFormModal
              channel={editingChannel}
              channelTypes={channelTypes}
              onSave={handleChannelSaved}
              onClose={() => {
                setShowChannelModal(false)
                setEditingChannel(null)
              }}
            />
          )}

          {showRuleModal && (
            <RuleFormModal
              rule={editingRule}
              channels={channels}
              sites={sites}
              checkTypes={checkTypes}
              onSave={handleRuleSaved}
              onClose={() => {
                setShowRuleModal(false)
                setEditingRule(null)
              }}
            />
          )}
        </div>
      </main>
    </div>
  )
}
