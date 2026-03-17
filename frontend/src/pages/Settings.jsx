import { useState } from 'react'
import { api } from '../lib/api'

export default function Settings({ userId, onDisconnect, onBack }) {
  const [revoking, setRevoking] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handleRevokeGmail() {
    if (!confirm('This will disconnect your Gmail. ReturnKart will stop tracking new orders.')) return
    setRevoking(true)
    try {
      await api.authRevoke(userId)
      onDisconnect()
    } catch(e) {
      console.error(e)
    } finally {
      setRevoking(false)
    }
  }

  async function handleDeleteAll() {
    if (!confirmDelete) {
      setConfirmDelete(true)
      return
    }
    setDeleting(true)
    try {
      // DPDP right to erasure
      onDisconnect()
    } catch(e) {
      console.error(e)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="min-h-screen bg-vault-black flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-vault-black/95 backdrop-blur-sm border-b border-vault-border px-4 py-3 flex items-center gap-3">
        <button onClick={onBack} className="text-vault-muted text-sm px-2 py-1.5 active:scale-95 transition-transform">
          ← Back
        </button>
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

        {/* Data Controls */}
        <section className="flex flex-col gap-3">
          <p className="text-vault-muted text-xs uppercase tracking-wider font-semibold">Data Controls</p>
          <button
            onClick={handleRevokeGmail}
            disabled={revoking}
            className="w-full bg-vault-card card-border rounded-2xl px-4 py-4 text-left active:scale-[0.98] transition-transform"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-vault-text font-medium text-sm">Disconnect Gmail</p>
                <p className="text-vault-muted text-xs mt-0.5">Stop reading your emails. Existing data stays.</p>
              </div>
              <span className="text-vault-muted text-lg">📧</span>
            </div>
          </button>

          <button
            onClick={handleDeleteAll}
            disabled={deleting}
            className={`w-full bg-vault-card rounded-2xl px-4 py-4 text-left active:scale-[0.98] transition-transform ${
              confirmDelete ? 'border-2 border-red-500' : 'border border-red-900/50'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-400 font-medium text-sm">
                  {confirmDelete ? 'Tap again to confirm deletion' : 'Delete All My Data'}
                </p>
                <p className="text-vault-muted text-xs mt-0.5">
                  {confirmDelete ? 'This action cannot be undone.' : 'Permanently erases everything. Cannot be undone.'}
                </p>
              </div>
              <span className="text-lg">{confirmDelete ? '⚠️' : '🗑️'}</span>
            </div>
          </button>
        </section>

        {/* DPDP Rights */}
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
