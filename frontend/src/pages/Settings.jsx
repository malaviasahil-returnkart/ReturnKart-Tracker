import { api } from '../lib/api'

export default function Settings({ userId, onDisconnect }) {
  async function handleRevokeGmail() {
    if (!confirm('This will disconnect your Gmail. ReturnKart will stop tracking new orders.')) return
    try {
      await api.authRevoke(userId)
      onDisconnect()
    } catch(e) {
      console.error(e)
    }
  }

  async function handleDeleteAll() {
    if (!confirm('Delete ALL your data permanently? This cannot be undone.')) return
    // DPDP right to erasure — to be implemented in backend
    onDisconnect()
  }

  return (
    <div className="min-h-screen bg-vault-black px-5 py-8 flex flex-col gap-6">
      <h2 className="text-vault-text font-bold text-xl">Settings Vault</h2>

      {/* Account */}
      <section className="flex flex-col gap-3">
        <p className="text-vault-muted text-xs uppercase tracking-wider">Account</p>
        <div className="bg-vault-card card-border rounded-2xl px-4 py-3">
          <p className="text-vault-muted text-xs">User ID</p>
          <p className="text-vault-text text-sm font-mono mt-0.5 truncate">{userId}</p>
        </div>
      </section>

      {/* DPDP rights */}
      <section className="flex flex-col gap-3">
        <p className="text-vault-muted text-xs uppercase tracking-wider">Your DPDP Rights</p>
        <button
          onClick={handleRevokeGmail}
          className="w-full bg-vault-card card-border rounded-2xl px-4 py-4 text-left active:scale-95 transition-transform"
        >
          <p className="text-vault-text font-medium text-sm">Revoke Gmail Access</p>
          <p className="text-vault-muted text-xs mt-0.5">Disconnect Gmail. We will stop reading your emails immediately.</p>
        </button>
        <button
          onClick={handleDeleteAll}
          className="w-full bg-vault-card border border-red-900/50 rounded-2xl px-4 py-4 text-left active:scale-95 transition-transform"
        >
          <p className="text-red-400 font-medium text-sm">Delete All My Data</p>
          <p className="text-vault-muted text-xs mt-0.5">Permanently erases all orders, tokens and your account. Cannot be undone.</p>
        </button>
      </section>

      {/* Legal */}
      <section className="flex flex-col gap-2 mt-4">
        <p className="text-vault-muted text-xs uppercase tracking-wider">Legal</p>
        <p className="text-vault-muted text-xs leading-relaxed">
          ReturnKart operates under India's Digital Personal Data Protection Act 2023.
          We collect only the minimum data required for return tracking.
          Your data is never sold or shared with third parties.
        </p>
      </section>

      <p className="text-vault-border text-xs text-center mt-auto">ReturnKart v1.0 · returnkart.in</p>
    </div>
  )
}
