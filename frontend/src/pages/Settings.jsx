import { useState } from 'react'
import { api } from '../lib/api'
import {
  ArrowLeft, LogOut, Mail, Plus, Trash2, User, Shield, Clock
} from 'lucide-react'

export default function Settings({ userId, userProfile, accounts = [], onBack, onDisconnect, onDisconnectAccount, onAddAccount }) {
  const [confirming, setConfirming] = useState(null) // email or 'all'

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
                        onClick={() => { onDisconnectAccount(acct.email); setConfirming(null) }}
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
        </section>

        {/* ─── Danger Zone ────────────────────────────────────────── */}
        <section>
          <h2 className="text-vault-muted text-xs font-semibold uppercase tracking-wider mb-3">Account</h2>
          {confirming === 'all' ? (
            <div className="bg-red-500/10 border border-red-500/30 rounded-2xl px-4 py-4">
              <p className="text-red-400 text-sm font-medium mb-3">Disconnect all accounts and delete all data?</p>
              <div className="flex gap-3">
                <button
                  onClick={() => { onDisconnect(); setConfirming(null) }}
                  className="flex-1 min-h-[44px] bg-red-500/20 text-red-400 py-3 rounded-xl font-semibold text-sm cursor-pointer active:scale-95 transition-transform"
                >
                  Yes, Disconnect All
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
                <p className="text-red-400 text-sm font-semibold">Disconnect All & Logout</p>
                <p className="text-vault-muted text-xs">Remove all Gmail accounts and clear data</p>
              </div>
            </button>
          )}
        </section>

      </div>
    </div>
  )
}
