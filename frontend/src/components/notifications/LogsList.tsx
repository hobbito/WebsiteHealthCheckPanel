import React from 'react'
import type { NotificationLog, NotificationRule } from '../../lib/types'

interface Props {
  logs: NotificationLog[]
  rules: NotificationRule[]
}

export default function LogsList({ logs, rules }: Props) {
  const getRuleName = (ruleId: number) => {
    const rule = rules.find((r) => r.id === ruleId)
    return rule?.name || 'Unknown Rule'
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Sent
          </span>
        )
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Failed
          </span>
        )
      case 'pending':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            Pending
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {status}
          </span>
        )
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  if (logs.length === 0) {
    return (
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
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No notification logs</h3>
        <p className="mt-1 text-sm text-gray-500">
          Notification history will appear here once notifications are sent.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-gray-600">Recent notification history.</p>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {logs.map((log) => (
            <li key={log.id} className="px-4 py-4 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <p className="text-sm font-medium text-gray-900">{getRuleName(log.rule_id)}</p>
                  <span className="ml-3">{getStatusBadge(log.status)}</span>
                </div>
                <p className="text-sm text-gray-500">{formatDate(log.sent_at)}</p>
              </div>
              {log.error_message && (
                <div className="mt-2">
                  <p className="text-sm text-red-600">{log.error_message}</p>
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
