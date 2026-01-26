import React, { useState } from 'react'
import { notificationsApi } from '../../lib/api'
import type {
  NotificationRule,
  NotificationChannel,
  Site,
  CheckTypeInfo,
  NotificationTrigger,
} from '../../lib/types'
import Modal from '../common/Modal'

interface Props {
  rule: NotificationRule | null
  channels: NotificationChannel[]
  sites: Site[]
  checkTypes: CheckTypeInfo[]
  onSave: (rule: NotificationRule) => void
  onClose: () => void
}

const TRIGGERS: { value: NotificationTrigger; label: string }[] = [
  { value: 'check_failure', label: 'Check Failure' },
  { value: 'check_recovery', label: 'Check Recovery' },
]

export default function RuleFormModal({
  rule,
  channels,
  sites,
  checkTypes,
  onSave,
  onClose,
}: Props) {
  const [name, setName] = useState(rule?.name || '')
  const [channelId, setChannelId] = useState(rule?.channel_id || channels[0]?.id || 0)
  const [trigger, setTrigger] = useState<NotificationTrigger>(rule?.trigger || 'check_failure')
  const [siteIds, setSiteIds] = useState<number[]>(rule?.site_ids || [])
  const [selectedCheckTypes, setSelectedCheckTypes] = useState<string[]>(rule?.check_types || [])
  const [consecutiveFailures, setConsecutiveFailures] = useState(rule?.consecutive_failures || 1)
  const [isEnabled, setIsEnabled] = useState(rule?.is_enabled ?? true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isEditing = !!rule

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)

    try {
      const data = {
        name,
        channel_id: channelId,
        trigger,
        site_ids: siteIds.length > 0 ? siteIds : null,
        check_types: selectedCheckTypes.length > 0 ? selectedCheckTypes : null,
        consecutive_failures: consecutiveFailures,
        is_enabled: isEnabled,
      }

      let result: NotificationRule
      if (isEditing && rule) {
        result = await notificationsApi.updateRule(rule.id, data)
      } else {
        result = await notificationsApi.createRule(data)
      }
      onSave(result)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save rule')
    } finally {
      setSaving(false)
    }
  }

  const handleSiteToggle = (siteId: number) => {
    setSiteIds((prev) =>
      prev.includes(siteId) ? prev.filter((id) => id !== siteId) : [...prev, siteId]
    )
  }

  const handleCheckTypeToggle = (checkType: string) => {
    setSelectedCheckTypes((prev) =>
      prev.includes(checkType) ? prev.filter((t) => t !== checkType) : [...prev, checkType]
    )
  }

  return (
    <Modal isOpen={true} onClose={onClose} title={isEditing ? 'Edit Rule' : 'New Rule'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Name *
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Alert on HTTP failures"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
          />
        </div>

        <div>
          <label htmlFor="channel" className="block text-sm font-medium text-gray-700">
            Notification Channel *
          </label>
          <select
            id="channel"
            value={channelId}
            onChange={(e) => setChannelId(parseInt(e.target.value))}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
          >
            {channels.map((channel) => (
              <option key={channel.id} value={channel.id}>
                {channel.name} ({channel.channel_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="trigger" className="block text-sm font-medium text-gray-700">
            Trigger *
          </label>
          <select
            id="trigger"
            value={trigger}
            onChange={(e) => setTrigger(e.target.value as NotificationTrigger)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
          >
            {TRIGGERS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        {trigger === 'check_failure' && (
          <div>
            <label htmlFor="consecutive" className="block text-sm font-medium text-gray-700">
              Consecutive Failures Required
            </label>
            <input
              type="number"
              id="consecutive"
              min={1}
              max={10}
              value={consecutiveFailures}
              onChange={(e) => setConsecutiveFailures(parseInt(e.target.value) || 1)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">
              Notification will only be sent after this many consecutive failures.
            </p>
          </div>
        )}

        {/* Sites Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Sites Filter
          </label>
          <p className="text-xs text-gray-500 mb-2">
            Leave empty to apply to all sites, or select specific sites.
          </p>
          <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
            {sites.length === 0 ? (
              <p className="text-sm text-gray-500">No sites available</p>
            ) : (
              sites.map((site) => (
                <label key={site.id} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={siteIds.includes(site.id)}
                    onChange={() => handleSiteToggle(site.id)}
                    className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">{site.name}</span>
                </label>
              ))
            )}
          </div>
        </div>

        {/* Check Types Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Check Types Filter
          </label>
          <p className="text-xs text-gray-500 mb-2">
            Leave empty to apply to all check types, or select specific types.
          </p>
          <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
            {checkTypes.map((checkType) => (
              <label key={checkType.type} className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedCheckTypes.includes(checkType.type)}
                  onChange={() => handleCheckTypeToggle(checkType.type)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="ml-2 text-sm text-gray-700">{checkType.display_name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_enabled"
            checked={isEnabled}
            onChange={(e) => setIsEnabled(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          <label htmlFor="is_enabled" className="ml-2 block text-sm text-gray-700">
            Enabled
          </label>
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {saving ? 'Saving...' : isEditing ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
