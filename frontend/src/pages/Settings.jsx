import { useState } from 'react'
import { api } from '../lib/api'
import {
  ArrowLeft, LogOut, Mail, Plus, Trash2, User, Shield, Clock, FileText
} from 'lucide-react'

export default function Settings({ userId, userProfile, accounts = [], onBack, onDisconnect, onDisconnectAccount, onAddAccount }) {
  const [confirming, setConfirming] = useState(null) // email or 'all'
  const [deleting, setDeleting] = useState(false)
  const [deleteResult, setDeleteResult] = useState(null)

  // Consent audit trail
  const [consentHistory, setConsentHistory] = useState([])
  const [showConsent, setShowConsent] = useState(false)
  const [loadingConsent, setLoadingConsent] = useState(false)

  async function loadConsentHistory() {
    setLoadingConsent(true)
    try {
      const data = await api.getConsentHistory(userId)
      setConsentHistory(data.history || [])
    } catch(e) { console.error(e) }
    finally { setLoadingConsent(false) }
  }

  function toggleConsentHistory() {
    if (!showConsent) loadConsentHistory()
    setShowConsent(!showConsent)
  }

  async function handleDeleteAll() {
    setDeleting(true)
    try {
      // Step 1: Log deletion consent BEFORE deleting
      await api.logConsent(userId, 'data_delete_request', false,
        'User requested deletion of all personal data under DPDP Act 2023 Right to Erasure.')

      // Step 2: Actually delete all data from backend
      const result = await api.deleteAllData(userId)
      setDeleteResult(result.message || 'All data deleted successfully.')

      // Step 3: Clear local state after delay so user sees confirmation
      setTimeout(() => {
        onDisconnect()
      }, 2000)
    } catch(e) {
      console.error('Data deletion failed:', e)
      setDeleteResult('Deletion failed. Please try again.')
      setConfirming(null)
      setTimeout(() => setDeleteResult(null), 5000)
    } finally { setDeleting(false) }
  }

  async function handleDisconnectAccount(email) {
    try {
      // Log Gmail revocation consent
      await api.logConsent(userId, 'gmail_revoke', false,
        `User revoked Gmail access for ${email}.`)
    } catch(e) { console.error('Consent log failed:', e) }
    onDisconnectAccount(email)
  }

  const purposeLabels = {
    gmail_read_access: { icon: '📧', label: 'Gmail Read Access' },
    return_tracking: { icon: '⏰', label: 'Return Tracking' },
    data_storage: { icon: '🗄️', label: 'Data Storage' },
    gmail_revoke: { icon: '🚫', label: 'Gmail Revoked' },
    data_delete_request: { icon: '🗑️', label: 'Data Deletion Request' },
    platform_add: { icon: '🤖', label: 'Platform Added' },
  }

  return (
    <div className="min-h-screen bg-vault-black flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-vault-black/95 backdrop-blur-sm border-b border-vault-border px-4 py-3 flex items-center gap-3" style={{ paddingTop: 'max(12px, env(safe-area-inset-top))' }}>
        <button
          onClick={onBack}
          aria-label="Back"
          className="min-h-[44px] min-w-[44px] flex items-center justify-center text-vault-muted hover:text-vault-text transition-colors cursor-pointer"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-vault-text font-bold text-lg">Settings</h1>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-6" style={{ paddingBottom: 'max(32px, calc(32px + env(safe-area-inset-bottom)))' }}>

        {/* ─── Connected Gmail Accounts ──────────────────────────────── */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-vault-muted text-xs font-semibold uppercase tracking-wider">Connected Gmail Accounts</h2>
            <span className="text-vault-gold text-xs font-bold">{accounts.length}</span>
          </div>

          <div className="flex flex-col gap-3">
            {accounts.map((acct) => (
              <div key={acct.email} className="bg-vault-card card-border rounded-2xl px-4 py-4">
                <div className="flex items-center gap-3">
                  {/* Avatar */}
                  {acct.picture ? (
                    <img
                      src={acct.picture}
                      alt={acct.name}
                      className="w-10 h-10 rounded-full ring-2 ring-vault-gold/30 ring-offset-1 ring-offset-vault-black flex-shrink-0"
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-vault-gold/15 ring-2 ring-vault-gold/30 ring-offset-1 ring-offset-vault-black flex items-center justify-center flex-shrink-0">
                      <User size={18} className="text-vault-gold" />
                    </div>
                  )}

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-vault-text text-sm font-semibold truncate">{acct.name || 'Gmail Account'}</p>
                    <p className="text-vault-muted text-xs truncate">{acct.email}</p>
                  </div>

                  {/* Remove button */}
                  {confirming === acct.email ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => { handleDisconnectAccount(acct.email); setConfirming(null) }}
                        className="min-h-[36px] px-3 py-1.5 bg-red-500/20 text-red-400 rounded-lg text-xs font-semibold cursor-pointer active:scale-95 transition-transform"
                      >
                        Remove
                      </button>
                      <button
                        onClick={() => setConfirming(null)}
                        className="min-h-[36px] px-3 py-1.5 bg-vault-border text-vault-muted rounded-lg text-xs font-medium cursor-pointer"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setConfirming(acct.email)}
                      aria-label={`Remove ${acct.email}`}
                      className="min-h-[44px] min-w-[44px] flex items-center justify-center text-vault-muted hover:text-red-400 transition-colors cursor-pointer"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              </div>
            ))}

            {/* Add another Gmail */}
            <button
              onClick={onAddAccount}
              className="bg-vault-card card-border rounded-2xl px-4 py-4 flex items-center gap-3 active:scale-[0.98] transition-transform cursor-pointer"
            >
              <div className="w-10 h-10 rounded-full bg-vault-gold/10 flex items-center justify-center flex-shrink-0">
                <Plus size={18} className="text-vault-gold" />
              </div>
              <div>
                <p className="text-vault-gold text-sm font-semibold">Add another Gmail</p>
                <p className="text-vault-muted text-xs">Connect a second account to track more orders</p>
              </div>
            </button>
          </div>
        </section>

        {/* ─── Privacy & DPDP ─────────────────────────────────────── */}
        <section>
          <h2 className="text-vault-muted text-xs font-semibold uppercase tracking-wider mb-3">Privacy</h2>
          <div className="bg-vault-card card-border rounded-2xl px-4 py-4 flex items-start gap-3">
            <Shield size={18} className="text-vault-gold flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-vault-text text-sm font-medium">DPDP Act 2023 Compliant</p>
              <p className="text-vault-muted text-xs mt-1 leading-relaxed">
                ReturnKart only reads your order emails. We never send emails, delete data, or share your information. You can disconnect any account at any time.
              </p>
            </div>
          </div>

          {/* Consent Audit Trail */}
          <button onClick={toggleConsentHistory}
            className="w-full bg-vault-card card-border rounded-2xl px-4 py-3 mt-3 flex items-center justify-between active:scale-[0.98] transition-transform cursor-pointer">
            <div className="flex items-center gap-3">
              <FileText size={18} className="text-vault-gold" />
              <div className="text-left">
                <p className="text-vault-text font-medium text-sm">Consent Audit Trail</p>
                <p className="text-vault-muted text-xs">Timestamped log of all your consent decisions</p>
              </div>
            </div>
            <span className="text-vault-muted text-sm">{showConsent ? '▲' : '▼'}</span>
          </button>

          {showConsent && (
            <div className="bg-vault-card card-border rounded-2xl px-4 py-4 mt-2">
              {loadingConsent ? (
                <div className="flex justify-center py-4"><div className="w-5 h-5 border-2 border-vault-gold border-t-transparent rounded-full animate-spin" /></div>
              ) : consentHistory.length === 0 ? (
                <p className="text-vault-muted text-xs text-center py-2">No consent events logged yet.</p>
              ) : (
                <div className="flex flex-col gap-3">
                  {consentHistory.map((event, i) => {
                    const purpose = purposeLabels[event.purpose_id] || { icon: '•', label: event.purpose_id }
                    return (
                      <div key={event.id || i} className="flex items-start gap-3 bg-vault-black rounded-xl px-3 py-2.5 card-border">
                        <span className="text-base mt-0.5">{purpose.icon}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-vault-text text-xs font-medium">{purpose.label}</p>
                            <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                              event.consented ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                            }`}>{event.consented ? 'Granted' : 'Revoked'}</span>
                          </div>
                          <p className="text-vault-muted text-[10px] mt-0.5 truncate">{event.consent_text}</p>
                          <p className="text-vault-muted text-[9px] mt-0.5">
                            {new Date(event.created_at).toLocaleString('en-IN', {
                              day: 'numeric', month: 'short', year: 'numeric',
                              hour: '2-digit', minute: '2-digit', hour12: true
                            })}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </section>

        {/* ─── Danger Zone ────────────────────────────────────────── */}
        <section>
          <h2 className="text-vault-muted text-xs font-semibold uppercase tracking-wider mb-3">Account</h2>

          {deleteResult && (
            <div className="bg-vault-card card-border rounded-xl px-4 py-3 mb-3 text-center">
              <p className="text-vault-safe text-xs">{deleteResult}</p>
            </div>
          )}

          {confirming === 'all' ? (
            <div className="bg-red-500/10 border border-red-500/30 rounded-2xl px-4 py-4">
              <p className="text-red-400 text-sm font-medium mb-1">Delete all data and disconnect?</p>
              <p className="text-vault-muted text-xs mb-3">This will permanently erase all orders, evidence, and tokens. Consent audit trail is preserved as legally required.</p>
              <div className="flex gap-3">
                <button
                  onClick={handleDeleteAll}
                  disabled={deleting}
                  className="flex-1 min-h-[44px] bg-red-500/20 text-red-400 py-3 rounded-xl font-semibold text-sm cursor-pointer active:scale-95 transition-transform disabled:opacity-50"
                >
                  {deleting ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                      Deleting...
                    </span>
                  ) : 'Yes, Delete Everything'}
                </button>
                <button
                  onClick={() => setConfirming(null)}
                  className="flex-1 min-h-[44px] bg-vault-card card-border text-vault-muted py-3 rounded-xl font-medium text-sm cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setConfirming('all')}
              className="w-full bg-vault-card card-border rounded-2xl px-4 py-4 flex items-center gap-3 active:scale-[0.98] transition-transform cursor-pointer"
            >
              <LogOut size={18} className="text-red-400" />
              <div className="text-left">
                <p className="text-red-400 text-sm font-semibold">Delete All Data & Disconnect</p>
                <p className="text-vault-muted text-xs">DPDP Right to Erasure — permanently erase everything</p>
              </div>
            </button>
          )}
        </section>

      </div>
    </div>
  )
}
