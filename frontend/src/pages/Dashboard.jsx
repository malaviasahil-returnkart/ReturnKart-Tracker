import { useState, useEffect, useCallback } from 'react'
import { api } from '../lib/api'
import { formatINR, daysRemaining, urgencyLevel, urgencyColor, formatDate } from '../lib/formatters'

export default function Dashboard({ userId, onDisconnect }) {
  const [orders, setOrders]       = useState([])
  const [loading, setLoading]     = useState(true)
  const [syncing, setSyncing]     = useState(false)
  const [selected, setSelected]   = useState(null)
  const [tab, setTab]             = useState('active') // active | all | expired

  const loadOrders = useCallback(() => {
    setLoading(true)
    api.getOrders(userId, tab === 'all' ? null : tab)
      .then(data => setOrders(data.orders || []))
      .catch(() => setOrders([]))
      .finally(() => setLoading(false))
  }, [userId, tab])

  useEffect(() => { loadOrders() }, [loadOrders])

  async function handleSync() {
    setSyncing(true)
    try {
      await api.syncGmail(userId)
      setTimeout(loadOrders, 2000) // give backend time to process
    } catch(e) {
      console.error(e)
    } finally {
      setTimeout(() => setSyncing(false), 2500)
    }
  }

  async function handleMarkKept(orderId) {
    await api.patchOrder(orderId, userId, 'kept').catch(() => {})
    setSelected(null)
    loadOrders()
  }

  async function handleMarkReturned(orderId) {
    await api.patchOrder(orderId, userId, 'returned').catch(() => {})
    setSelected(null)
    loadOrders()
  }

  // Total money at risk (active orders expiring within 7 days)
  const moneyAtRisk = orders
    .filter(o => { const d = daysRemaining(o.return_deadline); return d !== null && d >= 0 && d <= 7 })
    .reduce((sum, o) => sum + (o.price || 0), 0)

  const urgentOrders = orders.filter(o => {
    const d = daysRemaining(o.return_deadline)
    return d !== null && d >= 0 && d <= 3
  })

  return (
    <div className="min-h-screen bg-vault-black flex flex-col">

      {/* Header */}
      <header className="sticky top-0 z-10 bg-vault-black border-b border-vault-border px-4 py-3 flex items-center justify-between">
        <h1 className="text-vault-gold font-bold text-lg tracking-tight">
          Return<span className="text-vault-text">Kart</span>
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="bg-vault-card card-border text-vault-muted px-3 py-1.5 rounded-xl text-xs font-medium flex items-center gap-1.5 active:scale-95 transition-transform"
          >
            <span className={syncing ? 'animate-spin inline-block' : ''}>↻</span>
            {syncing ? 'Syncing…' : 'Sync Gmail'}
          </button>
          <button onClick={onDisconnect} className="text-vault-muted text-xs px-2 py-1.5">
            ⚙
          </button>
        </div>
      </header>

      {/* Money at risk banner */}
      {moneyAtRisk > 0 && (
        <div className="mx-4 mt-4 rounded-2xl bg-vault-card urgent-border px-4 py-4 flex items-center justify-between animate-slide-up">
          <div>
            <p className="text-vault-muted text-xs uppercase tracking-wider">Money at Risk</p>
            <p className="text-2xl font-bold text-vault-urgent mt-0.5">{formatINR(moneyAtRisk)}</p>
            <p className="text-vault-muted text-xs mt-1">{urgentOrders.length} order{urgentOrders.length !== 1 ? 's' : ''} expiring in ≤3 days</p>
          </div>
          <div className="text-4xl">⚠️</div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 px-4 mt-4">
        {[['active','Active'],['all','All'],['expired','Expired']].map(([val, label]) => (
          <button
            key={val}
            onClick={() => setTab(val)}
            className={`px-4 py-1.5 rounded-xl text-sm font-medium transition-colors ${
              tab === val
                ? 'bg-vault-gold text-vault-black'
                : 'bg-vault-card text-vault-muted card-border'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Orders list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3 pb-24">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-7 h-7 border-2 border-vault-gold border-t-transparent rounded-full animate-spin" />
          </div>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center py-16 gap-4 animate-fade-in">
            <span className="text-5xl">📬</span>
            <p className="text-vault-muted text-center text-sm">
              {tab === 'active' ? 'No active orders tracked yet.\nTap Sync Gmail to import orders.' : 'No orders here.'}
            </p>
            {tab === 'active' && (
              <button onClick={handleSync} disabled={syncing} className="mt-2 bg-vault-gold text-vault-black px-6 py-2 rounded-xl font-semibold text-sm active:scale-95 transition-transform">
                {syncing ? 'Syncing…' : '📧 Sync Gmail Now'}
              </button>
            )}
          </div>
        ) : (
          orders.map(order => <OrderCard key={order.id} order={order} onTap={() => setSelected(order)} />)
        )}
      </div>

      {/* Order detail bottom sheet */}
      {selected && (
        <OrderSheet
          order={selected}
          onClose={() => setSelected(null)}
          onKept={() => handleMarkKept(selected.id)}
          onReturned={() => handleMarkReturned(selected.id)}
        />
      )}
    </div>
  )
}

function OrderCard({ order, onTap }) {
  const days = daysRemaining(order.return_deadline)
  const level = urgencyLevel(days)
  const color = urgencyColor(level)

  const cardClass = level === 'expired'
    ? 'opacity-50'
    : level === 'critical' || level === 'urgent'
    ? 'urgent-border'
    : 'card-border'

  return (
    <button
      onClick={onTap}
      className={`w-full bg-vault-card rounded-2xl px-4 py-4 text-left ${cardClass} active:scale-98 transition-transform animate-slide-up`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-vault-border text-vault-muted">
              {order.brand}
            </span>
            {order.is_replacement_only && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-900/40 text-yellow-400">Replace only</span>
            )}
          </div>
          <p className="text-vault-text font-medium text-sm truncate">{order.item_name}</p>
          <p className="text-vault-muted text-xs mt-0.5">{formatINR(order.price)} · {formatDate(order.order_date)}</p>
        </div>

        {/* Countdown */}
        <div className="flex flex-col items-center flex-shrink-0">
          {days === null ? (
            <span className="text-vault-muted text-xs">—</span>
          ) : days < 0 ? (
            <span className="text-vault-muted text-xs font-medium">Expired</span>
          ) : (
            <>
              <span className="text-2xl font-bold" style={{ color }}>{days}</span>
              <span className="text-xs" style={{ color: '#A0A0A0' }}>day{days !== 1 ? 's' : ''} left</span>
            </>
          )}
          {/* Progress arc */}
          <CountdownArc days={days} color={color} />
        </div>
      </div>
    </button>
  )
}

function CountdownArc({ days, color }) {
  if (days === null || days < 0) return null
  const max = 30
  const pct = Math.min(days / max, 1)
  const r = 12
  const circ = 2 * Math.PI * r
  const dash = pct * circ
  return (
    <svg width="32" height="32" className="mt-1" style={{ transform: 'rotate(-90deg)' }}>
      <circle cx="16" cy="16" r={r} fill="none" stroke="#2A2A2A" strokeWidth="2.5" />
      <circle
        cx="16" cy="16" r={r} fill="none"
        stroke={color} strokeWidth="2.5"
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 0.6s ease' }}
      />
    </svg>
  )
}

function OrderSheet({ order, onClose, onKept, onReturned }) {
  const days = daysRemaining(order.return_deadline)
  const level = urgencyLevel(days)
  const color = urgencyColor(level)

  return (
    <>
      {/* Backdrop */}
      <div onClick={onClose} className="fixed inset-0 bg-black/60 z-20 animate-fade-in" />

      {/* Sheet */}
      <div className="fixed bottom-0 left-0 right-0 z-30 bg-vault-card rounded-t-3xl px-5 py-6 flex flex-col gap-5 animate-slide-up max-h-[85vh] overflow-y-auto">
        {/* Handle */}
        <div className="w-10 h-1 bg-vault-border rounded-full mx-auto -mt-1" />

        {/* Header */}
        <div>
          <span className="text-xs font-semibold text-vault-muted px-2 py-0.5 rounded-full bg-vault-border">{order.brand}</span>
          <h2 className="text-vault-text font-semibold text-base mt-2">{order.item_name}</h2>
          <p className="text-vault-muted text-sm mt-0.5">Order #{order.order_id}</p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Order Value', value: formatINR(order.price), highlight: true },
            { label: 'Days Remaining', value: days === null ? '—' : days < 0 ? 'Expired' : `${days} days`, color },
            { label: 'Order Date', value: formatDate(order.order_date) },
            { label: 'Return Deadline', value: formatDate(order.return_deadline) },
            order.category && { label: 'Category', value: order.category },
            order.courier_partner && { label: 'Courier', value: order.courier_partner },
          ].filter(Boolean).map(item => (
            <div key={item.label} className="bg-vault-black rounded-xl px-3 py-3 card-border">
              <p className="text-vault-muted text-xs">{item.label}</p>
              <p className="font-semibold text-sm mt-0.5" style={{ color: item.color || (item.highlight ? '#D4AF37' : '#FFFFFF') }}>
                {item.value}
              </p>
            </div>
          ))}
        </div>

        {/* Return type badge */}
        {order.is_replacement_only && (
          <div className="bg-yellow-900/20 border border-yellow-700/30 rounded-xl px-4 py-3 text-sm text-yellow-400">
            ⚠️ This item is <strong>replacement only</strong> — no cash refund available.
          </div>
        )}

        {/* Action buttons */}
        {order.status === 'active' && (
          <div className="flex flex-col gap-3">
            <button
              onClick={() => onReturned(order.id)}
              className="w-full bg-vault-gold text-vault-black py-4 rounded-2xl font-semibold text-base active:scale-95 transition-transform"
            >
              📦 I Returned This
            </button>
            <button
              onClick={() => onKept(order.id)}
              className="w-full bg-vault-card card-border text-vault-muted py-4 rounded-2xl font-semibold text-base active:scale-95 transition-transform"
            >
              ✓ I'm Keeping This
            </button>
          </div>
        )}

        {order.status !== 'active' && (
          <div className="text-center text-vault-muted text-sm py-2">
            Status: <span className="text-vault-text capitalize font-medium">{order.status}</span>
          </div>
        )}
      </div>
    </>
  )
}
