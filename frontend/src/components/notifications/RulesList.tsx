import React from 'react'
import type { NotificationRule, NotificationChannel, Site } from '../../lib/types'

interface Props {
  rules: NotificationRule[]
  channels: NotificationChannel[]
  sites: Site[]
  onCreateRule: () => void
  onEditRule: (rule: NotificationRule) => void
  onDeleteRule: (id: number) => void
}

export default function RulesList({
  rules,
  channels,
  sites,
  onCreateRule,
  onEditRule,
  onDeleteRule,
}: Props) {
  const getTriggerLabel = (trigger: string) => {
    switch (trigger) {
      case 'check_failure':
        return 'Check Failure'
      case 'check_recovery':
        return 'Check Recovery'
      case 'incident_opened':
        return 'Incident Opened'
      case 'incident_resolved':
        return 'Incident Resolved'
      default:
        return trigger
    }
  }

  const getTriggerColor = (trigger: string) => {
    switch (trigger) {
      case 'check_failure':
      case 'incident_opened':
        return 'bg-red-100 text-red-800'
      case 'check_recovery':
      case 'incident_resolved':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getChannelName = (channelId: number) => {
    const channel = channels.find((c) => c.id === channelId)
    return channel?.name || 'Unknown'
  }

  const getSiteNames = (siteIds: number[] | null) => {
    if (!siteIds || siteIds.length === 0) return 'All sites'
    return siteIds
      .map((id) => sites.find((s) => s.id === id)?.name || 'Unknown')
      .join(', ')
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-gray-600">
          Create rules to define when notifications should be sent.
        </p>
        <button
          onClick={onCreateRule}
          disabled={channels.length === 0}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          title={channels.length === 0 ? 'Create a channel first' : ''}
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Rule
        </button>
      </div>

      {channels.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded text-sm">
          You need to create at least one notification channel before creating rules.
        </div>
      )}

      {rules.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No notification rules</h3>
          <p className="mt-1 text-sm text-gray-500">
            Create rules to specify when notifications should be sent.
          </p>
          {channels.length > 0 && (
            <div className="mt-6">
              <button
                onClick={onCreateRule}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Add Rule
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {rules.map((rule) => (
              <li key={rule.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-gray-900">{rule.name}</p>
                      {!rule.is_enabled && (
                        <span className="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                          Disabled
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => onEditRule(rule)}
                        className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => onDeleteRule(rule.id)}
                        className="inline-flex items-center px-3 py-1.5 border border-red-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex sm:space-x-4">
                      <p className="flex items-center text-sm text-gray-500">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTriggerColor(rule.trigger)}`}
                        >
                          {getTriggerLabel(rule.trigger)}
                        </span>
                      </p>
                      <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                        <svg
                          className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                          />
                        </svg>
                        {getChannelName(rule.channel_id)}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                      <span className="text-xs">Sites: {getSiteNames(rule.site_ids)}</span>
                      {rule.consecutive_failures > 1 && (
                        <span className="ml-3 text-xs">
                          After {rule.consecutive_failures} consecutive failures
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
