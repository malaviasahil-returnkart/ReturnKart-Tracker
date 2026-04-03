import { useState } from 'react'

export default function Onboarding({ onConnect }) {
  const [agreed, setAgreed] = useState(false)
  const [loading, setLoading] = useState(false)

  // Generate a stable user ID for demo (real app uses Supabase Auth)
  function handleConnect() {
    if (!agreed || loading) return
    setLoading(true)
    const uid = localStorage.getItem('rk_user_id') ||
      'user_' + Math.random().toString(36).slice(2, 10)
    onConnect(uid)
  }

  return (
    <div className="min-h-screen bg-vault-black flex flex-col items-center justify-between px-6 py-12 animate-fade-in">

      {/* Top: Logo + tagline */}
      <div className="flex flex-col items-center gap-4 mt-8">
        <div className="w-20 h-20 rounded-2xl bg-vault-card card-border flex items-center justify-center">
          <span className="text-4xl">📦</span>
        </div>
        <h1 className="text-3xl font-bold text-vault-text tracking-tight">
          Return<span className="text-vault-gold">Kart</span>
        </h1>
        <p className="text-vault-muted text-center text-base max-w-xs leading-relaxed">
          Your personal AI guardian for e-commerce return windows.
          Never lose money to a missed deadline again.
        </p>
      </div>

      {/* Middle: Feature pills */}
      <div className="w-full max-w-sm flex flex-col gap-3 my-8">
        {[
          { icon: '⚡', title: 'Zero manual entry', desc: 'AI reads your invoice emails automatically' },
          { icon: '⏰', title: 'Live countdown timers', desc: 'Know exactly how many days you have left' },
          { icon: '🛡️', title: 'Money at risk alerts', desc: 'Urgent notifications before windows close' },
          { icon: '🔒', title: 'Read-only Gmail access', desc: 'We never send, delete or modify your emails' },
        ].map(f => (
          <div key={f.title} className="flex items-start gap-4 bg-vault-card card-border rounded-2xl px-4 py-4 animate-slide-up">
            <span className="text-2xl mt-0.5">{f.icon}</span>
            <div>
              <p className="text-vault-text font-medium text-sm">{f.title}</p>
              <p className="text-vault-muted text-xs mt-0.5">{f.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom: Consent + CTA */}
      <div className="w-full max-w-sm flex flex-col gap-4">
        {/* DPDP Consent */}
        <button
          onClick={() => setAgreed(a => !a)}
          className="flex items-start gap-3 text-left"
        >
          <div className={`mt-0.5 w-5 h-5 rounded flex-shrink-0 border-2 flex items-center justify-center transition-colors ${
            agreed ? 'bg-vault-gold border-vault-gold' : 'bg-transparent border-vault-border'
          }`}>
            {agreed && <span className="text-vault-black text-xs font-bold">✓</span>}
          </div>
          <span className="text-vault-muted text-xs leading-relaxed">
            I consent to ReturnKart scanning my order confirmation emails for return tracking purposes, in compliance with
            {' '}<span className="text-vault-gold">DPDP Act 2023</span>. My data will not be shared or sold.
          </span>
        </button>

        {/* Connect Gmail CTA */}
        <button
          onClick={handleConnect}
          disabled={!agreed || loading}
          className={`w-full py-4 rounded-2xl font-semibold text-base flex items-center justify-center gap-3 transition-all ${
            agreed && !loading
              ? 'bg-vault-gold text-vault-black animate-pulse-gold active:scale-95'
              : 'bg-vault-border text-vault-muted cursor-not-allowed'
          }`}
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-vault-black border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Connect Gmail
            </>
          )}
        </button>

        <p className="text-vault-muted text-xs text-center">
          Tracks Amazon, Flipkart, Myntra, Meesho & Ajio
        </p>
      </div>
    </div>
  )
}
