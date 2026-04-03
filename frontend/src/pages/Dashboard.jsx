import { useState, useEffect, useCallback } from 'react'
import { api } from '../lib/api'
import { formatINR, daysRemaining, urgencyLevel, urgencyColor, formatDate } from '../lib/formatters'
import BrandLogo from '../lib/BrandLogo'
import {
  Package, Undo2, AlertTriangle, Settings, RefreshCw, Mail,
  Check, RotateCcw, ChevronDown, ShieldAlert, Clock, Calendar,
  Tag, Truck, X, ArrowDownUp, SortAsc, User
} from 'lucide-react'

// ─── Sort options ─────────────────────────────────────────────────────────────
const SORT_OPTIONS = [
  { key: 'expiry_asc',   label: 'Expiring Soon', icon: Clock        },
  { key: 'brand',        label: 'Brand',         icon: Tag          },
  { key: 'value_desc',   label: 'Value: High',   icon: ArrowDownUp  },
  { key: 'value_asc',    label: 'Value: Low',    icon: SortAsc      },
]

function sortOrders(orders, sortKey) {
  const arr = [...orders]
  switch (sortKey) {
    case 'expiry_asc':
      return arr.sort((a, b) => {
        const da = daysRemaining(a.return_deadline)
        const db = daysRemaining(b.return_deadline)
        if (da === null && db === null) return 0
        if (da === null) return 1
        if (db === null) return -1
        if (da < 0 && db >= 0) return 1
        if (db < 0 && da >= 0) return -1
        return da - db
      })
    case 'brand':
      return arr.sort((a, b) => (a.brand || '').localeCompare(b.brand || ''))
    case 'value_desc':
      return arr.sort((a, b) => (b.price || 0) - (a.price || 0))
    case 'value_asc':
      return arr.sort((a, b) => (a.price || 0) - (b.price || 0))
    default:
      return arr
  }
}

// ─── Skeleton loaders ─────────────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <div className="bg-vault-card rounded-2xl px-4 py-4 card-border animate-fade-in">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-xl skeleton flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-3 w-20 rounded skeleton" />
          <div className="h-4 w-40 rounded skeleton" />
          <div className="h-3 w-28 rounded skeleton" />
        </div>
        <div className="flex flex-col items-center gap-1">
          <div className="h-7 w-8 rounded skeleton" />
          <div className="h-3 w-12 rounded skeleton" />
        </div>
      </div>
    </div>
  )
}

function SkeletonTile() {
  return (
    <div className="rounded-2xl px-4 py-4 bg-vault-card card-border">
      <div className="h-3 w-24 rounded skeleton mb-3" />
      <div className="h-8 w-12 rounded skeleton mb-2" />
      <div className="h-4 w-20 rounded skeleton mb-1" />
      <div className="h-3 w-28 rounded skeleton" />
    </div>
  )
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getInitials(name, email) {
  if (name) {
    const parts = name.trim().split(/\s+/)
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    }
    return parts[0][0]?.toUpperCase() || ''
  }
  if (email) return email[0]?.toUpperCase() || ''
  return ''
}

// ─── User Avatar ──────────────────────────────────────────────────────────────
function UserAvatar({ profile, size = 32, onClick }) {
  if (profile?.picture) {
    return (
      <button
        onClick={onClick}
        aria-label={profile.name || 'User profile'}
        className="min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
      >
        <img
          src={profile.picture}
          alt={profile.name || 'User'}
          width={size}
          height={size}
          className="rounded-full ring-2 ring-vault-gold/40 ring-offset-1 ring-offset-vault-black"
          referrerPolicy="no-referrer"
        />
      </button>
    )
  }

  const initials = getInitials(profile?.name, profile?.email)
  return (
    <button
      onClick={onClick}
      aria-label="User profile"
      className="min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
    >
      <div
        className="rounded-full bg-vault-gold/15 ring-2 ring-vault-gold/30 ring-offset-1 ring-offset-vault-black flex items-center justify-center"
        style={{ width: size, height: size }}
      >
        {initials
          ? <span className="text-vault-gold text-[11px] font-bold leading-none">{initials}</span>
          : <User size={14} className="text-vault-gold" />
        }
      </div>
    </button>
  )
}

export default function Dashboard({ userId, userProfile, onDisconnect, onOpenSettings }) {
  const [orders, setOrders]     = useState([])
  const [loading, setLoading]   = useState(true)
  const [syncing, setSyncing]   = useState(false)
  const [selected, setSelected] = useState(null)
  const [tab, setTab]           = useState('active')
  const [sort, setSort]         = useState('expiry_asc')
  const [summary, setSummary]   = useState({ activeCount: 0, activeValue: 0, returnCount: 0, returnValue: 0 })
  const [summaryLoading, setSummaryLoading] = useState(true)

  // ─── Fetch summary counts (all orders, unfiltered) ──────────────────────────
  const loadSummary = useCallback(() => {
    setSummaryLoading(true)
    api.getOrders(userId, null)
      .then(data => {
        const all = data.orders || []
        const active = all.filter(o => {
          if (o.status !== 'active') return false
          const d = daysRemaining(o.return_deadline)
          return d !== null && d >= 0
        })
        const wtr = all.filter(o => o.status === 'want_to_return')
        setSummary({
          activeCount: active.length,
          activeValue: active.reduce((s, o) => s + (o.price || 0), 0),
          returnCount: wtr.length,
          returnValue: wtr.reduce((s, o) => s + (o.price || 0), 0),
        })
      })
      .catch(() => {})
      .finally(() => setSummaryLoading(false))
  }, [userId])

  const loadOrders = useCallback(() => {
    setLoading(true)
    const statusFilter = tab === 'all' ? null : tab === 'return' ? 'want_to_return' : tab
    api.getOrders(userId, statusFilter)
      .then(data => setOrders(data.orders || []))
      .catch(() => setOrders([]))
      .finally(() => setLoading(false))
  }, [userId, tab])

  useEffect(() => { loadOrders() }, [loadOrders])
  useEffect(() => { loadSummary() }, [loadSummary])

  function refreshAll() {
    loadOrders()
    loadSummary()
  }

  async function handleSync() {
    setSyncing(true)
    try {
      await api.syncGmail(userId)
      setTimeout(refreshAll, 2000)
    } catch(e) {
      console.error(e)
    } finally {
      setTimeout(() => setSyncing(false), 2500)
    }
  }

  async function handleMarkKept(orderId) {
    await api.patchOrder(orderId, userId, 'kept').catch(() => {})
    setSelected(null)
    refreshAll()
  }

  async function handleMarkReturned(orderId) {
    await api.patchOrder(orderId, userId, 'returned').catch(() => {})
    setSelected(null)
    refreshAll()
  }

  async function handleMarkWantToReturn(orderId) {
    await api.patchOrder(orderId, userId, 'want_to_return').catch(() => {})
    setSelected(null)
    refreshAll()
  }

  async function handleUndoWantToReturn(orderId) {
    await api.patchOrder(orderId, userId, 'active').catch(() => {})
    setSelected(null)
    refreshAll()
  }

  const moneyAtRisk = orders
    .filter(o => { const d = daysRemaining(o.return_deadline); return d !== null && d >= 0 && d <= 7 })
    .reduce((sum, o) => sum + (o.price || 0), 0)

  const urgentOrders = orders.filter(o => {
    const d = daysRemaining(o.return_deadline)
    return d !== null && d >= 0 && d <= 3
  })

  const sortedOrders = sortOrders(orders, sort)
  const showBrandHeader = sort === 'brand'

  return (
    <div className="min-h-screen bg-vault-black flex flex-col">

      {/* ─── Header ──────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-10 bg-vault-black/95 backdrop-blur-sm border-b border-vault-border px-4 py-3 flex items-center justify-between" style={{ paddingTop: 'max(12px, env(safe-area-inset-top))' }}>
        <h1 className="text-vault-gold font-bold text-lg tracking-tight select-none">
          Return<span className="text-vault-text">Kart</span>
        </h1>
        <div className="flex items-center gap-1">
          <button
            onClick={handleSync}
            disabled={syncing}
            aria-label="Sync Gmail"
            className="min-h-[44px] min-w-[44px] bg-vault-card card-border text-vault-muted px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-1.5 active:scale-95 transition-transform cursor-pointer disabled:opacity-50"
          >
            <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Syncing…' : 'Sync'}
          </button>
          <button
            onClick={onOpenSettings}
            aria-label="Settings"
            className="min-h-[44px] min-w-[44px] flex items-center justify-center text-vault-muted hover:text-vault-gold transition-colors cursor-pointer"
          >
            <Settings size={20} />
          </button>
          <UserAvatar profile={userProfile} size={32} onClick={onOpenSettings} />
        </div>
      </header>

      {/* ─── Summary Tiles ───────────────────────────────────────────────── */}
      {summaryLoading ? (
        <div className="grid grid-cols-2 gap-3 px-4 mt-4">
          <SkeletonTile />
          <SkeletonTile />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 px-4 mt-4 animate-fade-in">
          <button
            onClick={() => setTab('active')}
            aria-label={`Active tracking: ${summary.activeCount} orders`}
            className={`rounded-2xl px-4 py-4 text-left transition-all active:scale-[0.97] cursor-pointer ${
              tab === 'active'
                ? 'bg-vault-card border border-vault-gold/30 gold-glow'
                : 'bg-vault-card card-border'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-lg bg-vault-gold/10 flex items-center justify-center">
                <Package size={14} className="text-vault-gold" />
              </div>
              <span className="text-vault-muted text-[11px] font-semibold uppercase tracking-wider">Tracking</span>
            </div>
            <p className="text-3xl font-bold text-vault-text tabular-nums">{summary.activeCount}</p>
            <p className="text-vault-gold text-sm font-semibold mt-1">{formatINR(summary.activeValue)}</p>
            <p className="text-vault-muted text-[11px] mt-0.5">open return windows</p>
          </button>

          <button
            onClick={() => setTab('return')}
            aria-label={`Want to return: ${summary.returnCount} orders`}
            className={`rounded-2xl px-4 py-4 text-left transition-all active:scale-[0.97] cursor-pointer ${
              tab === 'return'
                ? 'bg-vault-card return-border'
                : 'bg-vault-card card-border'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Undo2 size={14} className="text-vault-blue" />
              </div>
              <span className="text-vault-muted text-[11px] font-semibold uppercase tracking-wider">Return</span>
            </div>
            <p className="text-3xl font-bold text-vault-text tabular-nums">{summary.returnCount}</p>
            <p className="text-sm font-semibold mt-1" style={{ color: summary.returnCount > 0 ? '#60A5FA' : '#A0A0A0' }}>
              {formatINR(summary.returnValue)}
            </p>
            <p className="text-vault-muted text-[11px] mt-0.5">marked for return</p>
          </button>
        </div>
      )}

      {/* ─── Money at Risk Banner ────────────────────────────────────────── */}
      {moneyAtRisk > 0 && tab === 'active' && (
        <div className="mx-4 mt-3 rounded-2xl bg-vault-card urgent-border px-4 py-4 flex items-center justify-between animate-slide-up">
          <div>
            <p className="text-vault-muted text-[11px] uppercase tracking-wider font-semibold">Money at Risk</p>
            <p className="text-2xl font-bold text-vault-urgent mt-0.5 tabular-nums">{formatINR(moneyAtRisk)}</p>
            <p className="text-vault-muted text-xs mt-1">{urgentOrders.length} order{urgentOrders.length !== 1 ? 's' : ''} expiring in 3 days or less</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center flex-shrink-0">
            <AlertTriangle size={20} className="text-vault-urgent" />
          </div>
        </div>
      )}

      {/* ─── Tabs ────────────────────────────────────────────────────────── */}
      <div className="flex gap-2 px-4 mt-4">
        {[['active','Active'],['return','Return'],['all','All'],['expired','Expired']].map(([val, label]) => (
          <button
            key={val}
            onClick={() => setTab(val)}
            className={`min-h-[36px] px-4 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer ${
              tab === val
                ? 'bg-vault-gold text-vault-black'
                : 'bg-vault-card text-vault-muted card-border'
            }`}
          >
            {label}
            {val === 'return' && summary.returnCount > 0 && (
              <span className="ml-1.5 inline-flex items-center justify-center min-w-[18px] h-[18px] bg-blue-500/20 text-blue-400 text-[10px] font-bold px-1 rounded-full">
                {summary.returnCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ─── Sort Bar ────────────────────────────────────────────────────── */}
      <div className="flex gap-2 px-4 mt-3 overflow-x-auto pb-1 scrollbar-hide">
        {SORT_OPTIONS.map(opt => {
          const Icon = opt.icon
          return (
            <button
              key={opt.key}
              onClick={() => setSort(opt.key)}
              className={`flex-shrink-0 min-h-[32px] px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer flex items-center gap-1.5 ${
                sort === opt.key
                  ? 'bg-vault-gold text-vault-black'
                  : 'bg-vault-border text-vault-muted'
              }`}
            >
              <Icon size={12} />
              {opt.label}
            </button>
          )
        })}
      </div>

      {/* ─── Orders List ─────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3" style={{ paddingBottom: 'max(96px, calc(96px + env(safe-area-inset-bottom)))' }}>
        {loading ? (
          <div className="flex flex-col gap-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : sortedOrders.length === 0 ? (
          <div className="flex flex-col items-center py-16 gap-4 animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-vault-card card-border flex items-center justify-center">
              {tab === 'return' ? <Undo2 size={28} className="text-vault-muted" /> : <Mail size={28} className="text-vault-muted" />}
            </div>
            <p className="text-vault-muted text-center text-sm leading-relaxed max-w-[260px]">
              {tab === 'active' ? 'No active orders tracked yet. Tap Sync to import orders from Gmail.'
                : tab === 'return' ? 'No orders marked for return yet. Tap an order and hit Want to Return.'
                : 'No orders here.'}
            </p>
            {tab === 'active' && (
              <button
                onClick={handleSync}
                disabled={syncing}
                className="mt-2 min-h-[44px] bg-vault-gold text-vault-black px-6 py-3 rounded-xl font-semibold text-sm active:scale-95 transition-transform cursor-pointer flex items-center gap-2"
              >
                <Mail size={16} />
                {syncing ? 'Syncing…' : 'Sync Gmail Now'}
              </button>
            )}
          </div>
        ) : (
          sortedOrders.map((order, idx) => {
            const prevOrder = sortedOrders[idx - 1]
            const showLabel = showBrandHeader && (idx === 0 || prevOrder.brand !== order.brand)
            return (
              <div key={order.id}>
                {showLabel && (
                  <div className="flex items-center gap-2 mt-2 mb-1">
                    <BrandLogo brand={order.brand} size={18} className="rounded" />
                    <p className="text-vault-muted text-xs font-semibold uppercase tracking-wider">{order.brand}</p>
                  </div>
                )}
                <OrderCard order={order} onTap={() => setSelected(order)} />
              </div>
            )
          })
        )}
      </div>

      {selected && (
        <OrderSheet
          order={selected}
          onClose={() => setSelected(null)}
          onKept={() => handleMarkKept(selected.id)}
          onReturned={() => handleMarkReturned(selected.id)}
          onWantToReturn={() => handleMarkWantToReturn(selected.id)}
          onUndoWantToReturn={() => handleUndoWantToReturn(selected.id)}
        />
      )}
    </div>
  )
}

// ─── Order Card ───────────────────────────────────────────────────────────────
function OrderCard({ order, onTap }) {
  const days = daysRemaining(order.return_deadline)
  const level = urgencyLevel(days)
  const color = urgencyColor(level)
  const isWantToReturn = order.status === 'want_to_return'

  const cardClass = level === 'expired'
    ? 'opacity-50'
    : isWantToReturn
    ? 'return-border'
    : level === 'critical' || level === 'urgent'
    ? 'urgent-border'
    : 'card-border'

  return (
    <button
      onClick={onTap}
      className={`w-full bg-vault-card rounded-2xl px-4 py-4 text-left ${cardClass} active:scale-[0.98] transition-transform animate-slide-up cursor-pointer`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <BrandLogo brand={order.brand} size={36} className="rounded-xl mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-xs font-semibold text-vault-gold truncate">{order.brand}</span>
              {order.is_replacement_only && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-yellow-900/40 text-yellow-400 flex-shrink-0 font-medium">Replace</span>
              )}
              {isWantToReturn && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-900/30 text-blue-400 flex-shrink-0 font-medium flex items-center gap-0.5">
                  <Undo2 size={9} /> Return
                </span>
              )}
            </div>
            <p className="text-vault-text font-medium text-sm truncate">{order.item_name}</p>
            <p className="text-vault-muted text-xs mt-0.5">{formatINR(order.price)} · {formatDate(order.order_date)}</p>
          </div>
        </div>
        <div className="flex flex-col items-center flex-shrink-0">
          {days === null ? (
            <span className="text-vault-muted text-xs">—</span>
          ) : days < 0 ? (
            <span className="text-vault-muted text-xs font-medium">Expired</span>
          ) : (
            <>
              <span className="text-2xl font-bold tabular-nums" style={{ color }}>{days}</span>
              <span className="text-[11px] text-vault-muted">day{days !== 1 ? 's' : ''}</span>
            </>
          )}
          <CountdownArc days={days} color={color} />
        </div>
      </div>
    </button>
  )
}

// ─── Countdown Arc ────────────────────────────────────────────────────────────
function CountdownArc({ days, color }) {
  if (days === null || days < 0) return null
  const max = 30
  const pct = Math.min(days / max, 1)
  const r = 12
  const circ = 2 * Math.PI * r
  const dash = pct * circ
  return (
    <svg width="32" height="32" className="mt-1" style={{ transform: 'rotate(-90deg)' }} aria-hidden="true">
      <circle cx="16" cy="16" r={r} fill="none" stroke="#2A2A2A" strokeWidth="2.5" />
      <circle
        cx="16" cy="16" r={r} fill="none"
        stroke={color} strokeWidth="2.5"
        strokeDasharray={`${dash} ${circ}`}
        strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 0.4s ease' }}
      />
    </svg>
  )
}

// ─── Order Detail Sheet ───────────────────────────────────────────────────────
function OrderSheet({ order, onClose, onKept, onReturned, onWantToReturn, onUndoWantToReturn }) {
  const days = daysRemaining(order.return_deadline)
  const level = urgencyLevel(days)
  const color = urgencyColor(level)
  const isWantToReturn = order.status === 'want_to_return'

  return (
    <>
      <div onClick={onClose} className="fixed inset-0 bg-black/60 z-20 animate-fade-in" />
      <div
        className="fixed bottom-0 left-0 right-0 z-30 bg-vault-card rounded-t-3xl px-5 py-6 flex flex-col gap-5 animate-slide-up max-h-[85vh] overflow-y-auto elevation-3"
        style={{ paddingBottom: 'max(24px, calc(24px + env(safe-area-inset-bottom)))' }}
        role="dialog"
        aria-label={`Order details for ${order.item_name}`}
      >
        <div className="w-10 h-1 bg-vault-border rounded-full mx-auto -mt-1" />

        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute top-4 right-4 min-w-[44px] min-h-[44px] flex items-center justify-center text-vault-muted hover:text-vault-text transition-colors cursor-pointer"
        >
          <X size={20} />
        </button>

        <div className="flex items-center gap-3 pr-10">
          <BrandLogo brand={order.brand} size={48} className="rounded-2xl flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-vault-gold">{order.brand}</span>
              {isWantToReturn && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-900/30 text-blue-400 font-medium flex items-center gap-0.5">
                  <Undo2 size={9} /> Returning
                </span>
              )}
            </div>
            <h2 className="text-vault-text font-semibold text-base mt-0.5 truncate">{order.item_name}</h2>
            <p className="text-vault-muted text-xs">Order #{order.order_id}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Order Value', value: formatINR(order.price), highlight: true, icon: Package },
            { label: 'Days Left', value: days === null ? '—' : days < 0 ? 'Expired' : `${days} days`, color, icon: Clock },
            { label: 'Order Date', value: formatDate(order.order_date), icon: Calendar },
            { label: 'Deadline', value: formatDate(order.return_deadline), icon: ShieldAlert },
            order.category && { label: 'Category', value: order.category, icon: Tag },
            order.courier_partner && { label: 'Courier', value: order.courier_partner, icon: Truck },
          ].filter(Boolean).map(item => {
            const Icon = item.icon
            return (
              <div key={item.label} className="bg-vault-black rounded-xl px-3 py-3 card-border">
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon size={11} className="text-vault-muted" />
                  <p className="text-vault-muted text-[11px] font-medium">{item.label}</p>
                </div>
                <p className="font-semibold text-sm" style={{ color: item.color || (item.highlight ? '#D4AF37' : '#FFFFFF') }}>
                  {item.value}
                </p>
              </div>
            )
          })}
        </div>

        {order.is_replacement_only && (
          <div className="bg-yellow-900/15 border border-yellow-700/25 rounded-xl px-4 py-3 text-sm text-yellow-400 flex items-start gap-2">
            <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
            <span>This item is <strong>replacement only</strong> — no cash refund available.</span>
          </div>
        )}

        {order.status === 'active' && (
          <div className="flex flex-col gap-3">
            <button
              onClick={onWantToReturn}
              className="w-full min-h-[52px] bg-vault-gold text-vault-black py-4 rounded-2xl font-semibold text-base active:scale-[0.97] transition-transform cursor-pointer flex items-center justify-center gap-2"
            >
              <Undo2 size={18} /> Want to Return
            </button>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={onReturned}
                className="min-h-[48px] bg-vault-card card-border text-vault-muted py-3 rounded-2xl font-medium text-sm active:scale-95 transition-transform cursor-pointer flex items-center justify-center gap-1.5"
              >
                <Package size={15} /> Returned
              </button>
              <button
                onClick={onKept}
                className="min-h-[48px] bg-vault-card card-border text-vault-muted py-3 rounded-2xl font-medium text-sm active:scale-95 transition-transform cursor-pointer flex items-center justify-center gap-1.5"
              >
                <Check size={15} /> Keeping
              </button>
            </div>
          </div>
        )}

        {isWantToReturn && (
          <div className="flex flex-col gap-3">
            <button
              onClick={onReturned}
              className="w-full min-h-[52px] bg-vault-gold text-vault-black py-4 rounded-2xl font-semibold text-base active:scale-[0.97] transition-transform cursor-pointer flex items-center justify-center gap-2"
            >
              <Package size={18} /> I Returned This
            </button>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={onUndoWantToReturn}
                className="min-h-[48px] bg-vault-card card-border text-vault-muted py-3 rounded-2xl font-medium text-sm active:scale-95 transition-transform cursor-pointer flex items-center justify-center gap-1.5"
              >
                <RotateCcw size={15} /> Undo
              </button>
              <button
                onClick={onKept}
                className="min-h-[48px] bg-vault-card card-border text-vault-muted py-3 rounded-2xl font-medium text-sm active:scale-95 transition-transform cursor-pointer flex items-center justify-center gap-1.5"
              >
                <Check size={15} /> Keeping
              </button>
            </div>
          </div>
        )}

        {order.status !== 'active' && !isWantToReturn && (
          <div className="text-center text-vault-muted text-sm py-2">
            Status: <span className="text-vault-text capitalize font-medium">{order.status}</span>
          </div>
        )}
      </div>
    </>
  )
}
