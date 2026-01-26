import { useState, useEffect } from 'react'
import { checksApi } from '@/lib/api'
import Modal from '@/components/common/Modal'
import type { CheckConfiguration, CheckTypeInfo } from '@/lib/types'

interface CheckFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  siteId: number
  check?: CheckConfiguration
}

export default function CheckFormModal({ isOpen, onClose, onSuccess, siteId, check }: CheckFormModalProps) {
  const [checkTypes, setCheckTypes] = useState<CheckTypeInfo[]>([])
  const [selectedType, setSelectedType] = useState('')
  const [name, setName] = useState('')
  const [configuration, setConfiguration] = useState<Record<string, any>>({})
  const [intervalSeconds, setIntervalSeconds] = useState(300)
  const [isEnabled, setIsEnabled] = useState(true)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const isEdit = !!check

  useEffect(() => {
    if (isOpen) {
      loadCheckTypes()
      if (check) {
        setSelectedType(check.check_type)
        setName(check.name)
        setConfiguration(check.configuration)
        setIntervalSeconds(check.interval_seconds)
        setIsEnabled(check.is_enabled)
      } else {
        resetForm()
      }
    }
  }, [isOpen, check])

  const loadCheckTypes = async () => {
    try {
      const types = await checksApi.listTypes()
      setCheckTypes(types)
      if (!isEdit && types.length > 0) {
        setSelectedType(types[0].type)
        setConfiguration(getDefaultConfig(types[0]))
      }
    } catch (err) {
      console.error('Error loading check types:', err)
    }
  }

  const getDefaultConfig = (checkType: CheckTypeInfo): Record<string, any> => {
    const defaults: Record<string, any> = {}
    if (checkType.config_schema?.properties) {
      Object.entries(checkType.config_schema.properties).forEach(([key, schema]: [string, any]) => {
        if (schema.default !== undefined) {
          defaults[key] = schema.default
        }
      })
    }
    return defaults
  }

  const resetForm = () => {
    setName('')
    setConfiguration({})
    setIntervalSeconds(300)
    setIsEnabled(true)
    setError('')
  }

  const handleTypeChange = (type: string) => {
    setSelectedType(type)
    const checkType = checkTypes.find(ct => ct.type === type)
    if (checkType) {
      setConfiguration(getDefaultConfig(checkType))
    }
  }

  const handleConfigChange = (key: string, value: any) => {
    setConfiguration({ ...configuration, [key]: value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      if (isEdit && check) {
        await checksApi.update(check.id, {
          name,
          configuration,
          interval_seconds: intervalSeconds,
          is_enabled: isEnabled
        })
      } else {
        await checksApi.create({
          site_id: siteId,
          check_type: selectedType,
          name,
          configuration,
          interval_seconds: intervalSeconds,
          is_enabled: isEnabled
        })
      }

      onSuccess()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save check')
    } finally {
      setIsLoading(false)
    }
  }

  const renderConfigField = (key: string, schema: any) => {
    const value = configuration[key] ?? schema.default ?? ''

    if (schema.type === 'integer' || schema.type === 'number') {
      return (
        <div key={key} className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {schema.title || key}
          </label>
          <input
            type="number"
            value={value}
            onChange={(e) => handleConfigChange(key, parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            min={schema.minimum}
            max={schema.maximum}
          />
          {schema.description && (
            <p className="text-xs text-gray-500 mt-1">{schema.description}</p>
          )}
        </div>
      )
    }

    if (schema.type === 'boolean') {
      return (
        <div key={key} className="mb-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleConfigChange(key, e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm font-medium text-gray-700">
              {schema.title || key}
            </span>
          </label>
          {schema.description && (
            <p className="text-xs text-gray-500 mt-1 ml-6">{schema.description}</p>
          )}
        </div>
      )
    }

    // Default to text input
    return (
      <div key={key} className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {schema.title || key}
        </label>
        <input
          type="text"
          value={value}
          onChange={(e) => handleConfigChange(key, e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {schema.description && (
          <p className="text-xs text-gray-500 mt-1">{schema.description}</p>
        )}
      </div>
    )
  }

  const selectedCheckType = checkTypes.find(ct => ct.type === selectedType)

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? 'Edit Check' : 'Add Check'}
      icon={
        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      }
    >
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Check Type
            </label>
            <select
              value={selectedType}
              onChange={(e) => handleTypeChange(e.target.value)}
              disabled={isEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            >
              {checkTypes.map((ct) => (
                <option key={ct.type} value={ct.type}>
                  {ct.type.toUpperCase()} - {ct.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Check Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Main page availability"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Check Interval
            </label>
            <select
              value={intervalSeconds}
              onChange={(e) => setIntervalSeconds(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={60}>Every 1 minute</option>
              <option value={300}>Every 5 minutes</option>
              <option value={600}>Every 10 minutes</option>
              <option value={1800}>Every 30 minutes</option>
              <option value={3600}>Every 1 hour</option>
            </select>
          </div>

          {selectedCheckType?.config_schema?.properties && (
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">Configuration</h4>
              {Object.entries(selectedCheckType.config_schema.properties).map(([key, schema]: [string, any]) =>
                renderConfigField(key, schema)
              )}
            </div>
          )}

          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={isEnabled}
                onChange={(e) => setIsEnabled(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">
                Enable this check
              </span>
            </label>
          </div>
        </div>

        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50"
          >
            {isLoading ? 'Saving...' : (isEdit ? 'Update Check' : 'Create Check')}
          </button>
        </div>
      </form>
    </Modal>
  )
}
