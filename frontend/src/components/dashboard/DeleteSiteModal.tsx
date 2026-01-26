import { useState } from 'react'
import { sitesApi } from '@/lib/api'
import Modal from '@/components/common/Modal'
import type { Site } from '@/lib/types'

interface DeleteSiteModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  site: Site
}

export default function DeleteSiteModal({ isOpen, onClose, onSuccess, site }: DeleteSiteModalProps) {
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleDelete = async () => {
    setError('')
    setIsLoading(true)

    try {
      await sitesApi.delete(site.id)
      onSuccess()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete site')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Site"
      icon={
        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      }
      iconColor="bg-red-600"
    >
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <p className="text-sm text-gray-600 mb-3">
        Are you sure you want to delete <span className="font-semibold text-gray-900">{site.name}</span>?
      </p>
      <p className="text-sm text-red-600 mb-6">
        This will also delete all checks and results associated with this site. This action cannot be undone.
      </p>

      <div className="flex gap-3 justify-end">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={handleDelete}
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md disabled:opacity-50"
        >
          {isLoading ? 'Deleting...' : 'Delete Site'}
        </button>
      </div>
    </Modal>
  )
}
