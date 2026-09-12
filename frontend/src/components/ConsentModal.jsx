import React, { useState } from 'react'
import { X, Clock, AlertCircle } from 'lucide-react'
import { consentAPI } from '../utils/api'
import './ConsentModal.css'

export default function ConsentModal({ request, onClose }) {
  const [loading, setLoading] = useState(false)
  const [duration, setDuration] = useState('once')
  const [customMinutes, setCustomMinutes] = useState(60)

  const handleRespond = async (allow) => {
    setLoading(true)
    try {
      await consentAPI.respondToConsent(request.id, allow, duration)
      onClose()
    } catch (error) {
      console.error('Error responding to consent:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="consent-overlay">
      <div className="consent-modal">
        <div className="consent-header">
          <h2>Permission Request</h2>
          <button
            className="consent-close"
            onClick={onClose}
            disabled={loading}
          >
            <X size={24} />
          </button>
        </div>

        <div className="consent-content">
          <div className="consent-section">
            <h3>🤖 Who is asking?</h3>
            <p className="consent-value">{request.requesting_agent}</p>
          </div>

          <div className="consent-section">
            <h3>📋 What data?</h3>
            <p className="consent-label">{request.data_category}</p>
            <div className="consent-fields">
              <div className="field-group">
                <p className="field-title">Will be shared:</p>
                <ul className="field-list shared">
                  {request.requested_fields?.map((field) => (
                    <li key={field}>
                      <span className="check">✓</span> {field}
                    </li>
                  ))}
                </ul>
              </div>
              {request.not_shared_fields?.length > 0 && (
                <div className="field-group">
                  <p className="field-title">Will NOT be shared:</p>
                  <ul className="field-list not-shared">
                    {request.not_shared_fields.map((field) => (
                      <li key={field}>
                        <span className="cross">✕</span> {field}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          <div className="consent-section">
            <h3>❓ Why?</h3>
            <p className="consent-value">{request.purpose}</p>
          </div>

          <div className="consent-section">
            <h3>⏱️ How long?</h3>
            <div className="duration-options">
              <label className="duration-option">
                <input
                  type="radio"
                  value="once"
                  checked={duration === 'once'}
                  onChange={(e) => setDuration(e.target.value)}
                  disabled={loading}
                />
                <span>One time only</span>
              </label>
              <label className="duration-option">
                <input
                  type="radio"
                  value="10min"
                  checked={duration === '10min'}
                  onChange={(e) => setDuration(e.target.value)}
                  disabled={loading}
                />
                <span>10 minutes</span>
              </label>
              <label className="duration-option">
                <input
                  type="radio"
                  value="1hour"
                  checked={duration === '1hour'}
                  onChange={(e) => setDuration(e.target.value)}
                  disabled={loading}
                />
                <span>1 hour</span>
              </label>
              <label className="duration-option">
                <input
                  type="radio"
                  value="custom"
                  checked={duration === 'custom'}
                  onChange={(e) => setDuration(e.target.value)}
                  disabled={loading}
                />
                <span>Custom</span>
              </label>
            </div>
            {duration === 'custom' && (
              <div className="custom-duration">
                <input
                  type="number"
                  min="1"
                  value={customMinutes}
                  onChange={(e) => setCustomMinutes(Number(e.target.value))}
                  disabled={loading}
                />
                <span>minutes</span>
              </div>
            )}
          </div>

          <div className="consent-warning">
            <AlertCircle size={20} />
            <p>
              Your data will be protected. Only the authorized information will
              be shared.
            </p>
          </div>
        </div>

        <div className="consent-actions">
          <button
            className="btn-deny"
            onClick={() => handleRespond(false)}
            disabled={loading}
          >
            {loading ? '...' : 'DENY'}
          </button>
          <button
            className="btn-allow"
            onClick={() => handleRespond(true)}
            disabled={loading}
          >
            {loading ? '...' : 'ALLOW'}
          </button>
        </div>
      </div>
    </div>
  )
}
