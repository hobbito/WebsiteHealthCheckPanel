import React, { useState, useEffect } from 'react'
import { notificationsApi } from '../../lib/api'
import type { NotificationChannel, ChannelTypeInfo } from '../../lib/types'
import Modal from '../common/Modal'

interface Props {
  channel: NotificationChannel | null
  channelTypes: ChannelTypeInfo[]
  onSave: (channel: NotificationChannel) => void
  onClose: () => void
}

export default function ChannelFormModal({ channel, channelTypes, onSave, onClose }: Props) {
  const [name, setName] = useState(channel?.name || '')
  const [channelType, setChannelType] = useState<string>(channel?.channel_type || 'email')
  const [isEnabled, setIsEnabled] = useState(channel?.is_enabled ?? true)
  const [configuration, setConfiguration] = useState<Record<string, any>>(
    channel?.configuration || {}
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isEditing = !!channel

  // Get the schema for the selected channel type
  const selectedType = channelTypes.find((t) => t.type === channelType)
  const configSchema = selectedType?.config_schema

  useEffect(() => {
    // Reset configuration when channel type changes (only for new channels)
    if (!isEditing) {
      setConfiguration({})
    }
  }, [channelType, isEditing])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)

    try {
      let result: NotificationChannel
      if (isEditing && channel) {
        result = await notificationsApi.updateChannel(channel.id, {
          name,
          configuration,
          is_enabled: isEnabled,
        })
      } else {
        result = await notificationsApi.createChannel({
          name,
          channel_type: channelType,
          configuration,
          is_enabled: isEnabled,
        })
      }
      onSave(result)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save channel')
    } finally {
      setSaving(false)
    }
  }

  const handleConfigChange = (key: string, value: any) => {
    setConfiguration((prev) => ({ ...prev, [key]: value }))
  }

  const renderConfigField = (key: string, schema: any) => {
    const value = configuration[key] ?? schema.default ?? ''
    const required = configSchema?.required?.includes(key) || false

    if (schema.enum) {
      return (
        <select
          id={key}
          value={value}
          onChange={(e) => handleConfigChange(key, e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          required={required}
        >
          {schema.enum.map((opt: string) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      )
    }

    if (schema.type === 'boolean') {
      return (
        <input
          type="checkbox"
          id={key}
          checked={!!value}
          onChange={(e) => handleConfigChange(key, e.target.checked)}
          className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
        />
      )
    }

    if (schema.type === 'integer' || schema.type === 'number') {
      return (
        <input
          type="number"
          id={key}
          value={value}
          onChange={(e) => handleConfigChange(key, parseInt(e.target.value) || 0)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          required={required}
        />
      )
    }

    // String input (handle password separately)
    const inputType = schema.format === 'password' ? 'password' : 'text'

    return (
      <input
        type={inputType}
        id={key}
        value={value}
        onChange={(e) => handleConfigChange(key, e.target.value)}
        placeholder={schema.description}
        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
        required={required}
      />
    )
  }

  return (
    <Modal isOpen={true} onClose={onClose} title={isEditing ? 'Edit Channel' : 'New Channel'}>
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
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            required
          />
        </div>

        {!isEditing && (
          <div>
            <label htmlFor="channel_type" className="block text-sm font-medium text-gray-700">
              Channel Type *
            </label>
            <select
              id="channel_type"
              value={channelType}
              onChange={(e) => setChannelType(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              required
            >
              {channelTypes.map((type) => (
                <option key={type.type} value={type.type}>
                  {type.display_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Dynamic configuration fields based on schema */}
        {configSchema?.properties && (
          <div className="border-t pt-4 mt-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Configuration</h4>
            <div className="space-y-3">
              {Object.entries(configSchema.properties).map(([key, schema]: [string, any]) => (
                <div key={key}>
                  <label htmlFor={key} className="block text-sm font-medium text-gray-700">
                    {schema.title || key}
                    {configSchema.required?.includes(key) && ' *'}
                  </label>
                  {schema.description && (
                    <p className="text-xs text-gray-500 mb-1">{schema.description}</p>
                  )}
                  {renderConfigField(key, schema)}
                </div>
              ))}
            </div>
          </div>
        )}

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
