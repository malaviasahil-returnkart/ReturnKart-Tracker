import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export default function Settings({ userId, onDisconnect, onBack }) {
  const [revoking, setRevoking] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  // Platform management
  const [platforms, setPlatforms] = useState([])
  const [loadingPlatforms, setLoadingPlatforms] = useState(true)
  const [showAddPlatform, setShowAddPlatform] = useState(false)
  const [newPlatformName, setNewPlatformName] = useState('')
  const [newPlatformUrl, setNewPlatformUrl] = useState('')
  const [addingPlatform, setAddingPlatform] = useState(false)
  const [platformResult, setPlatformResult] = useState(null)

  // Consent history
  const [consentHistory, setConsentHistory] = useState([])
  const [showConsent, setShowConsent] = useState(false)
  const [loadingConsent, setLoadingConsent] = useState(false)

  useEffect(() => { loadPlatforms() }, [])

  async function loadPlatforms() {
    setLoadingPlatforms(true)
    try {
      const data = await api.getPlatforms(userId)
      setPlatforms(data.platforms || [])
    } catch(e) { console.error(e) }
    finally { setLoadingPlatforms(false) }
  }

  async function loadConsentHistory() {
    setLoadingConsent(true)
    try {
      const data = await api.getConsentHistory(userId)
      setConsentHistory(data.history || [])
    } catch(e) { console.error(e) }
    finally { setLoadingConsent(false) }
  }

  async function handleAddPlatform() {
    if (!newPlatformName.trim()) return
    setAddingPlatform(true)
    setPlatformResult(null)
    try {
      const res = await api.addPlatform(userId, newPlatformName.trim(), newPlatformUrl.trim())
      setPlatformResult(res.message)
      setNewPlatformName('')
      setNewPlatformUrl('')
      setShowAddPlatform(false)
      await loadPlatforms()
      setTimeout(() => setPlatformResult(null), 5000)
    } catch(e) {
      console.error(e)
      setPlatformResult('Failed to add platform. Try again.')
      setTimeout(() => setPlatformResult(null), 3000)
    } finally { setAddingPlatform(false) }
  }

  async function handleDeletePlatform(id) {
    try {
      await api.deletePlatform(id, userId)
      setPlatforms(prev => prev.filter(p => p.id !== id))
    } catch(e) { console.error(e) }
  }

  async function handleRevokeGmail() {
    if (!confirm('This will disconnect your Gmail. ReturnKart will stop tracking new orders.')) return
    setRevoking(true)
    try {
      // Log consent revocation event BEFORE revoking
      await api.logConsent(userId, 'gmail_revoke', false,
        'User revoked Gmail read access. ReturnKart will stop scanning emails.')
      await api.authRevoke(userId)
      onDisconnect()
    } catch(e) { console.error(e) }
    finally { setRevoking(false) }
  }

  async function handleDeleteAll() {
    if (!confirmDelete) { setConfirmDelete(true); return }
    setDeleting(true)
    try {
      // Log data deletion request BEFORE deleting
      await api.logConsent(userId, 'data_delete_request', false,
        'User requested deletion of all personal data under DPDP Act 2023 Right to Erasure.')
      onDisconnect()
    } catch(e) { console.error(e) }
    finally { setDeleting(false) }
  }

  function toggleConsentHistory() {
    if (!showConsent) loadConsentHistory()
    setShowConsent(!showConsent)
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
      <header className="sticky top-0 z-10 bg-vault-black/95 backdrop-blur-sm border-b border-vault-border px-4 py-3 flex items-center gap-3">
        <button onClick={onBack} className="text-vault-muted text-sm px-2 py-1.5 active:scale-95 transition-transform">← Back</button>
        <h1 className="text-vault-text font-bold text-lg">Settings</h1>
      </header>

      <div className="flex-1 px-4 py-6 flex flex-col gap-6 overflow-y-auto pb-24">

        {/* Account */}
        <section className="flex flex-col gap-3">
          <p className="text-vault-muted text-xs uppercase tracking-wider font-semibold">Account</p>
          <div className="bg-vault-card card-border rounded-2xl px-4 py-3">
            <p className="text-vault-muted text-xs">User ID</p>
            <p className="text-vault-text text-sm font-mono mt-0.5 truncate">{userId}</p>
          </div>
          <div className="bg-vault-card card-border rounded-2xl px-4 py-3">
            <p className="text-vault-muted text-xs">Gmail Status</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="w-2 h-2 rounded-full bg-vault-safe" />
              <p className="text-vault-safe text-sm font-medium">Connected</p>
            </div>
          </div>
        </section>

        {/* Tracked Platforms */}
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <p className="text-vault-muted text-xs uppercase tracking-wider font-semibold">Tracked Platforms</p>
            <button onClick={() => setShowAddPlatform(!showAddPlatform)}
              className="text-vault-gold text-xs font-medium active:scale-95 transition-transform">
              {showAddPlatform ? 'Cancel' : '+ Add Platform'}
            </button>
          </div>

          {platformResult && (
            <div className="bg-vault-card card-border rounded-xl px-3 py-2 text-center text-xs text-vault-safe animate-fade-in">{platformResult}</div>
          )}

          {showAddPlatform && (
            <div className="bg-vault-card card-border rounded-2xl px-4 py-4 flex flex-col gap-3 animate-fade-in">
              <p className="text-vault-text text-sm font-medium">🤖 AI Platform Setup</p>
              <p className="text-vault-muted text-xs">Enter the platform name and optional website. Our AI will auto-detect email domains, return policies, and communication channels.</p>
              <input type="text" value={newPlatformName} onChange={e => setNewPlatformName(e.target.value)}
                placeholder="Platform name (e.g. Nykaa, Tata CLiQ)"
                className="w-full bg-vault-black card-border rounded-xl px-3 py-2.5 text-sm text-vault-text placeholder-vault-muted outline-none focus:border-vault-gold transition-colors" />
              <input type="text" value={newPlatformUrl} onChange={e => setNewPlatformUrl(e.target.value)}
                placeholder="Website URL (optional, e.g. nykaa.com)"
                className="w-full bg-vault-black card-border rounded-xl px-3 py-2.5 text-sm text-vault-text placeholder-vault-muted outline-none focus:border-vault-gold transition-colors" />
              <button onClick={handleAddPlatform} disabled={addingPlatform || !newPlatformName.trim()}
                className="w-full bg-vault-gold text-vault-black py-3 rounded-xl font-semibold text-sm active:scale-95 transition-transform disabled:opacity-50">
                {addingPlatform ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-vault-black border-t-transparent rounded-full animate-spin" />
                    AI is researching...
                  </span>
                ) : '🤖 Add with AI'}
              </button>
            </div>
          )}

          {loadingPlatforms ? (
            <div className="flex justify-center py-4"><div className="w-5 h-5 border-2 border-vault-gold border-t-transparent rounded-full animate-spin" /></div>
          ) : platforms.length === 0 ? (
            <div className="bg-vault-card card-border rounded-2xl px-4 py-4 text-center">
              <p className="text-vault-muted text-xs">Default platforms (Amazon, Flipkart, Myntra, Meesho, Ajio) are tracked automatically via Gmail. Add more platforms above.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {platforms.map(p => (
                <div key={p.id} className="bg-vault-card card-border rounded-2xl px-4 py-3 flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-vault-text text-sm font-medium">{p.platform_name}</p>
                      {p.ai_generated && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-blue-900/30 text-blue-400">🤖 AI</span>}
                      {p.is_global && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-vault-border text-vault-muted">Global</span>}
                    </div>
                    <p className="text-vault-muted text-[10px] mt-0.5 truncate">
                      {p.email_domains?.length > 0 ? p.email_domains.join(', ') : 'No email domains'}
                      {p.return_policy?.general ? ` · ${p.return_policy.general.window_days}d return` : ''}
                    </p>
                  </div>
                  {!p.is_global && (
                    <button onClick={() => handleDeletePlatform(p.id)}
                      className="text-red-400 text-xs px-2 py-1 active:scale-95 transition-transform flex-shrink-0 ml-2">×</button>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Data Controls */}
        <section className="flex flex-col gap-3">
          <p className="text-vault-muted text-xs uppercase tracking-wider font-semibold">Data Controls</p>
          <button onClick={handleRevokeGmail} disabled={revoking}
            className="w-full bg-vault-card card-border rounded-2xl px-4 py-4 text-left active:scale-[0.98] transition-transform">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-vault-text font-medium text-sm">Disconnect Gmail</p>
                <p className="text-vault-muted text-xs mt-0.5">Stop reading your emails. Existing data stays.</p>
              </div>
              <span className="text-vault-muted text-lg">📧</span>
            </div>
          </button>
          <button onClick={handleDeleteAll} disabled={deleting}
            className={`w-full bg-vault-card rounded-2xl px-4 py-4 text-left active:scale-[0.98] transition-transform ${
              confirmDelete ? 'border-2 border-red-500' : 'border border-red-900/50'
            }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-400 font-medium text-sm">{confirmDelete ? 'Tap again to confirm deletion' : 'Delete All My Data'}</p>
                <p className="text-vault-muted text-xs mt-0.5">{confirmDelete ? 'This action cannot be undone.' : 'Permanently erases everything.'}</p>
              </div>
              <span className="text-lg">{confirmDelete ? '⚠️' : '🗑️'}</span>
            </div>
          </button>
        </section>

        {/* DPDP Rights + Consent Audit */}
        <section className="flex flex-col gap-3">
          <p className="text-vault-muted text-xs uppercase tracking-wider font-semibold">Your DPDP Rights</p>
          <div className="bg-vault-card card-border rounded-2xl px-4 py-4">
            <div className="flex flex-col gap-3">
              {[
                { icon: '🔍', right: 'Right to Access', desc: 'View all data ReturnKart holds about you' },
                { icon: '✏️', right: 'Right to Correction', desc: 'Request corrections to your data' },
                { icon: '🗑️', right: 'Right to Erasure', desc: 'Delete all your data permanently' },
                { icon: '🚫', right: 'Right to Withdraw', desc: 'Revoke Gmail access at any time' },
              ].map(item => (
                <div key={item.right} className="flex items-start gap-3">
                  <span className="text-base mt-0.5">{item.icon}</span>
                  <div>
                    <p className="text-vault-text text-sm font-medium">{item.right}</p>
                    <p className="text-vault-muted text-xs mt-0.5">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Consent Audit Trail */}
          <button onClick={toggleConsentHistory}
            className="w-full bg-vault-card card-border rounded-2xl px-4 py-3 flex items-center justify-between active:scale-[0.98] transition-transform">
            <div className="flex items-center gap-3">
              <span className="text-lg">📜</span>
              <div className="text-left">
                <p className="text-vault-text font-medium text-sm">Consent Audit Trail</p>
                <p className="text-vault-muted text-xs">Timestamped log of all your consent decisions</p>
              </div>
            </div>
            <span className="text-vault-muted text-sm">{showConsent ? '▲' : '▼'}</span>
          </button>

          {showConsent && (
            <div className="bg-vault-card card-border rounded-2xl px-4 py-4 animate-fade-in">
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

        {/* Legal */}
        <section className="flex flex-col gap-2">
          <p className="text-vault-muted text-xs uppercase tracking-wider font-semibold">Legal</p>
          <p className="text-vault-muted text-xs leading-relaxed">
            ReturnKart operates under India's Digital Personal Data Protection Act 2023.
            We collect only the minimum data required for return tracking.
            Your data is never sold or shared with third parties.
            Gmail access is read-only — we never send, delete, or modify your emails.
          </p>
        </section>

        <p className="text-vault-border text-xs text-center mt-auto pt-4">ReturnKart v1.0 · returnkart.in</p>
      </div>
    </div>
  )
}
