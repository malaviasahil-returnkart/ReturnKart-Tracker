import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../lib/api'
import { formatINR, daysRemaining, urgencyLevel, urgencyColor, formatDate } from '../lib/formatters'
import { getRewardsSummary } from '../lib/goodShopper'
import { getDeliverySteps, getDeliveryProgress, getDeliveryLabel, getDeliveryIcon, getDeliveryColor, getOrderPhase } from '../lib/deliveryStatus'

export default function Dashboard({ userId, onDisconnect, onSettings }) {
  const [orders, setOrders]       = useState([])
  const [allOrders, setAllOrders] = useState([])
  const [loading, setLoading]     = useState(true)
  const [syncing, setSyncing]     = useState(false)
  const [selected, setSelected]   = useState(null)
  const [tab, setTab]             = useState('active')
  const [syncResult, setSyncResult] = useState(null)
  const [showRewards, setShowRewards] = useState(false)

  const loadOrders = useCallback(() => {
    setLoading(true)
    Promise.all([
      api.getOrders(userId, tab === 'all' ? null : tab),
      api.getOrders(userId)
    ])
      .then(([filtered, all]) => {
        setOrders(filtered.orders || [])
        setAllOrders(all.orders || [])
      })
      .catch(() => { setOrders([]); setAllOrders([]) })
      .finally(() => setLoading(false))
  }, [userId, tab])

  useEffect(() => { loadOrders() }, [loadOrders])

  async function handleSync() {
    setSyncing(true)
    setSyncResult(null)
    try {
      await api.syncGmail(userId)
      setTimeout(() => {
        loadOrders()
        setSyncResult('Sync complete')
        setTimeout(() => setSyncResult(null), 3000)
      }, 3000)
    } catch(e) {
      console.error(e)
      setSyncResult('Sync failed')
      setTimeout(() => setSyncResult(null), 3000)
    } finally {
      setTimeout(() => setSyncing(false), 3500)
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

  const activeOrders = allOrders.filter(o => o.status === 'active')
  const totalProtected = activeOrders.reduce((sum, o) => sum + (o.price || 0), 0)
  const urgentOrders = activeOrders.filter(o => {
    const d = daysRemaining(o.return_deadline)
    return d !== null && d >= 0 && d <= 3
  })
  const moneyAtRisk = urgentOrders.reduce((sum, o) => sum + (o.price || 0), 0)
  const savedOrders = allOrders.filter(o => o.status === 'returned')
  const moneySaved = savedOrders.reduce((sum, o) => sum + (o.price || 0), 0)
  const rewards = getRewardsSummary(allOrders)

  return (
    <div className="min-h-screen bg-vault-black flex flex-col">
      <header className="sticky top-0 z-10 bg-vault-black/95 backdrop-blur-sm border-b border-vault-border px-4 py-3 flex items-center justify-between">
        <h1 className="text-vault-gold font-bold text-lg tracking-tight">
          Return<span className="text-vault-text">Kart</span>
        </h1>
        <div className="flex items-center gap-2">
          <button onClick={handleSync} disabled={syncing}
            className="bg-vault-card card-border text-vault-muted px-3 py-1.5 rounded-xl text-xs font-medium flex items-center gap-1.5 active:scale-95 transition-transform">
            <span className={syncing ? 'animate-spin inline-block' : ''}>\u21bb</span>
            {syncing ? 'Syncing\u2026' : 'Sync'}
          </button>
          <button onClick={onSettings} className="text-vault-muted text-sm px-2 py-1.5 active:scale-95 transition-transform">\u2699</button>
        </div>
      </header>

      {syncResult && (
        <div className="mx-4 mt-2 rounded-xl bg-vault-card card-border px-3 py-2 text-center text-xs text-vault-muted animate-fade-in">{syncResult}</div>
      )}

      {/* Good Shopper Badge */}
      <button onClick={() => setShowRewards(!showRewards)}
        className="mx-4 mt-4 bg-vault-card card-border rounded-2xl px-4 py-3 flex items-center justify-between active:scale-[0.98] transition-transform">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{rewards.emoji}</span>
          <div className="text-left">
            <p className="text-vault-text font-semibold text-sm">{rewards.label} Shopper</p>
            <p className="text-vault-muted text-[10px]">Trust Score: {rewards.score}/100{rewards.streak > 0 ? ` \u00b7 ${rewards.streak} streak` : ''}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {rewards.keepRate > 0 && <span className="text-vault-safe text-xs font-medium">{rewards.keepRate}% kept</span>}
          <span className="text-vault-muted text-sm">{showRewards ? '\u25b2' : '\u25bc'}</span>
        </div>
      </button>
      {showRewards && <RewardsPanel rewards={rewards} />}

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-2 px-4 mt-3">
        <div className="bg-vault-card card-border rounded-2xl px-3 py-3 text-center">
          <p className="text-vault-muted text-[10px] uppercase tracking-wider">Protected</p>
          <p className="text-vault-gold font-bold text-base mt-0.5">{formatINR(totalProtected)}</p>
          <p className="text-vault-muted text-[10px] mt-0.5">{activeOrders.length} active</p>
        </div>
        <div className={`bg-vault-card rounded-2xl px-3 py-3 text-center ${moneyAtRisk > 0 ? 'urgent-border' : 'card-border'}`}>
          <p className="text-vault-muted text-[10px] uppercase tracking-wider">At Risk</p>
          <p className={`font-bold text-base mt-0.5 ${moneyAtRisk > 0 ? 'text-vault-urgent' : 'text-vault-muted'}`}>{formatINR(moneyAtRisk)}</p>
          <p className="text-vault-muted text-[10px] mt-0.5">{urgentOrders.length} expiring</p>
        </div>
        <div className="bg-vault-card card-border rounded-2xl px-3 py-3 text-center">
          <p className="text-vault-muted text-[10px] uppercase tracking-wider">Saved</p>
          <p className="text-vault-safe font-bold text-base mt-0.5">{formatINR(moneySaved)}</p>
          <p className="text-vault-muted text-[10px] mt-0.5">{savedOrders.length} returned</p>
        </div>
      </div>

      {/* Urgent Carousel */}
      {urgentOrders.length > 0 && (
        <div className="mt-4 px-4">
          <p className="text-vault-urgent text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span className="inline-block w-2 h-2 rounded-full bg-vault-urgent animate-pulse" />Expiring Soon
          </p>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
            {urgentOrders.map(order => {
              const days = daysRemaining(order.return_deadline)
              return (
                <button key={order.id} onClick={() => setSelected(order)}
                  className="flex-shrink-0 w-64 bg-vault-card urgent-border rounded-2xl px-4 py-3 text-left active:scale-95 transition-transform">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-vault-border text-vault-muted">{order.brand}</span>
                    <span className="text-vault-urgent font-bold text-lg">{days}d</span>
                  </div>
                  <p className="text-vault-text font-medium text-sm mt-2 truncate">{order.item_name}</p>
                  <p className="text-vault-gold font-semibold text-sm mt-1">{formatINR(order.price)}</p>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 px-4 mt-4">
        {[['active','Active'],['all','All'],['returned','Returned'],['expired','Expired']].map(([val, label]) => (
          <button key={val} onClick={() => setTab(val)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors ${
              tab === val ? 'bg-vault-gold text-vault-black' : 'bg-vault-card text-vault-muted card-border'
            }`}>
            {label}
            {val === 'active' && activeOrders.length > 0 && <span className="ml-1 text-[10px] opacity-70">{activeOrders.length}</span>}
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
            <span className="text-5xl">{tab === 'returned' ? '\ud83c\udf89' : tab === 'expired' ? '\u23f0' : '\ud83d\udcec'}</span>
            <p className="text-vault-muted text-center text-sm">
              {tab === 'active' ? 'No active orders tracked yet.\nTap Sync to import from Gmail.'
                : tab === 'returned' ? 'No returned orders yet.'
                : tab === 'expired' ? 'No expired orders \u2014 nice!' : 'No orders found.'}
            </p>
            {tab === 'active' && (
              <button onClick={handleSync} disabled={syncing} className="mt-2 bg-vault-gold text-vault-black px-6 py-2 rounded-xl font-semibold text-sm active:scale-95 transition-transform">
                {syncing ? 'Syncing\u2026' : '\ud83d\udce7 Sync Gmail Now'}
              </button>
            )}
          </div>
        ) : (
          orders.map(order => <OrderCard key={order.id} order={order} onTap={() => setSelected(order)} />)
        )}
      </div>

      {selected && (
        <OrderSheet
          order={selected}
          userId={userId}
          onClose={() => setSelected(null)}
          onKept={() => handleMarkKept(selected.id)}
          onReturned={() => handleMarkReturned(selected.id)}
        />
      )}
    </div>
  )
}


/* ============== REWARDS PANEL ============== */
function RewardsPanel({ rewards }) {
  const tiers = [
    { label: 'Bronze', min: 50, color: '#CD7F32' },
    { label: 'Silver', min: 65, color: '#C0C0C0' },
    { label: 'Gold', min: 80, color: '#D4AF37' },
    { label: 'Platinum', min: 90, color: '#E5E4E2' },
  ]
  return (
    <div className="mx-4 mt-2 bg-vault-card card-border rounded-2xl px-4 py-4 flex flex-col gap-4 animate-fade-in">
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-vault-muted text-xs">Trust Score</p>
          <p className="text-vault-text font-bold text-lg">{rewards.score}<span className="text-vault-muted text-xs font-normal">/100</span></p>
        </div>
        <div className="w-full h-2.5 bg-vault-border rounded-full overflow-hidden">
          <div className="h-full rounded-full transition-all duration-700" style={{ width: `${rewards.score}%`, background: rewards.color }} />
        </div>
        <div className="flex justify-between mt-1">
          {tiers.map(t => (<span key={t.label} className="text-[9px]" style={{ color: rewards.score >= t.min ? t.color : '#444' }}>{t.label}</span>))}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-vault-black rounded-xl px-3 py-2 text-center card-border">
          <p className="text-vault-safe font-bold text-lg">{rewards.keptCount}</p>
          <p className="text-vault-muted text-[10px]">Kept</p>
        </div>
        <div className="bg-vault-black rounded-xl px-3 py-2 text-center card-border">
          <p className="text-vault-urgent font-bold text-lg">{rewards.returnedCount}</p>
          <p className="text-vault-muted text-[10px]">Returned</p>
        </div>
        <div className="bg-vault-black rounded-xl px-3 py-2 text-center card-border">
          <p className="font-bold text-lg" style={{ color: rewards.color }}>{rewards.keepRate}%</p>
          <p className="text-vault-muted text-[10px]">Keep Rate</p>
        </div>
      </div>
      {rewards.streak > 0 && (
        <div className="flex items-center gap-2 bg-vault-black rounded-xl px-3 py-2 card-border">
          <span className="text-lg">{rewards.streakMsg.fire ? '\ud83d\udd25' : '\u2b50'}</span>
          <div>
            <p className="text-vault-text text-sm font-medium">{rewards.streak} order streak!</p>
            <p className="text-vault-muted text-xs">{rewards.streakMsg.text}</p>
          </div>
        </div>
      )}
      {rewards.score < 90 && (
        <p className="text-vault-muted text-[10px] text-center">
          {rewards.score < 50 ? 'Keep more items to build your trust score'
            : rewards.score < 65 ? `${65 - rewards.score} more points to Silver`
            : rewards.score < 80 ? `${80 - rewards.score} more points to Gold`
            : `${90 - rewards.score} more points to Platinum`}
        </p>
      )}
    </div>
  )
}


/* ============== DELIVERY TIMELINE ============== */
function DeliveryTimeline({ status, compact = false }) {
  const steps = getDeliverySteps()
  const { stepIndex } = getDeliveryProgress(status || 'ordered')

  if (compact) {
    // Mini inline version for order cards
    return (
      <div className="flex items-center gap-0.5 mt-1.5">
        {steps.map((step, i) => (
          <div key={step.key} className="flex items-center">
            <div className={`w-1.5 h-1.5 rounded-full transition-colors ${
              i <= stepIndex ? 'bg-vault-gold' : 'bg-vault-border'
            }`} />
            {i < steps.length - 1 && (
              <div className={`w-3 h-[1px] ${
                i < stepIndex ? 'bg-vault-gold' : 'bg-vault-border'
              }`} />
            )}
          </div>
        ))}
        <span className="text-[9px] ml-1" style={{ color: getDeliveryColor(status || 'ordered') }}>
          {getDeliveryLabel(status || 'ordered')}
        </span>
      </div>
    )
  }

  // Full version for order detail sheet
  return (
    <div className="bg-vault-black card-border rounded-2xl px-4 py-4">
      <p className="text-vault-muted text-[10px] uppercase tracking-wider mb-3">Delivery Journey</p>
      <div className="flex items-center justify-between relative">
        {/* Progress bar background */}
        <div className="absolute top-3 left-4 right-4 h-[2px] bg-vault-border" />
        {/* Progress bar filled */}
        <div className="absolute top-3 left-4 h-[2px] bg-vault-gold transition-all duration-700"
          style={{ width: `${stepIndex === 0 ? 0 : (stepIndex / (steps.length - 1)) * (100 - 8)}%` }} />

        {steps.map((step, i) => {
          const isActive = i <= stepIndex
          const isCurrent = i === stepIndex
          return (
            <div key={step.key} className="flex flex-col items-center z-10 relative" style={{ flex: 1 }}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs transition-all ${
                isCurrent ? 'bg-vault-gold ring-2 ring-vault-gold/30 scale-110'
                : isActive ? 'bg-vault-gold'
                : 'bg-vault-border'
              }`}>
                {isActive ? <span className="text-[10px]">{step.icon}</span> : <span className="text-[8px] text-vault-muted">{i + 1}</span>}
              </div>
              <span className={`text-[9px] mt-1.5 text-center leading-tight ${
                isCurrent ? 'text-vault-gold font-semibold' : isActive ? 'text-vault-text' : 'text-vault-muted'
              }`}>{step.short}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}


/* ============== ORDER CARD ============== */
function OrderCard({ order, onTap }) {
  const days = daysRemaining(order.return_deadline)
  const level = urgencyLevel(days)
  const color = urgencyColor(level)
  const phase = getOrderPhase(order)

  const statusBadge = order.status === 'returned'
    ? { text: 'Returned', bg: 'bg-green-900/30', textColor: 'text-green-400' }
    : order.status === 'kept'
    ? { text: '\u2713 Kept', bg: 'bg-blue-900/30', textColor: 'text-blue-400' }
    : order.status === 'expired'
    ? { text: 'Kept (expired)', bg: 'bg-vault-border', textColor: 'text-vault-muted' }
    : null

  const cardClass = order.status === 'expired' || order.status === 'returned' || order.status === 'kept'
    ? 'opacity-60 card-border'
    : level === 'critical' || level === 'urgent' ? 'urgent-border' : 'card-border'

  return (
    <button onClick={onTap}
      className={`w-full bg-vault-card rounded-2xl px-4 py-4 text-left ${cardClass} active:scale-[0.98] transition-transform animate-slide-up`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-vault-border text-vault-muted">{order.brand}</span>
            {order.is_replacement_only && <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-900/40 text-yellow-400">Replace only</span>}
            {statusBadge && <span className={`text-[10px] px-2 py-0.5 rounded-full ${statusBadge.bg} ${statusBadge.textColor}`}>{statusBadge.text}</span>}
          </div>
          <p className="text-vault-text font-medium text-sm truncate">{order.item_name}</p>
          <p className="text-vault-muted text-xs mt-0.5">{formatINR(order.price)} \u00b7 {formatDate(order.order_date)}</p>

          {/* Mini delivery timeline for pre-delivery orders */}
          {phase === 'pre_delivery' && order.delivery_status && order.delivery_status !== 'delivered' && (
            <DeliveryTimeline status={order.delivery_status} compact={true} />
          )}
        </div>
        <div className="flex flex-col items-center flex-shrink-0">
          {order.status === 'returned' ? <span className="text-green-400 text-xl">\u21a9</span>
            : order.status === 'kept' ? <span className="text-blue-400 text-xl">\u2713</span>
            : phase === 'pre_delivery' ? <span className="text-lg">{getDeliveryIcon(order.delivery_status)}</span>
            : days === null ? <span className="text-vault-muted text-xs">\u2014</span>
            : days < 0 ? <span className="text-vault-muted text-xs font-medium">Expired</span>
            : <><span className="text-2xl font-bold" style={{ color }}>{days}</span><span className="text-[10px]" style={{ color: '#A0A0A0' }}>day{days !== 1 ? 's' : ''}</span></>}
          {phase === 'return_window' && order.status === 'active' && <CountdownArc days={days} color={color} />}
        </div>
      </div>
    </button>
  )
}


function CountdownArc({ days, color }) {
  if (days === null || days < 0) return null
  const pct = Math.min(days / 30, 1), r = 12, circ = 2 * Math.PI * r, dash = pct * circ
  return (
    <svg width="32" height="32" className="mt-1" style={{ transform: 'rotate(-90deg)' }}>
      <circle cx="16" cy="16" r={r} fill="none" stroke="#2A2A2A" strokeWidth="2.5" />
      <circle cx="16" cy="16" r={r} fill="none" stroke={color} strokeWidth="2.5"
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" style={{ transition: 'stroke-dasharray 0.6s ease' }} />
    </svg>
  )
}


/* ============== ORDER DETAIL SHEET ============== */
function OrderSheet({ order, userId, onClose, onKept, onReturned }) {
  const days = daysRemaining(order.return_deadline)
  const level = urgencyLevel(days)
  const color = urgencyColor(level)
  const phase = getOrderPhase(order)
  const [showEvidence, setShowEvidence] = useState(false)

  return (
    <>
      <div onClick={onClose} className="fixed inset-0 bg-black/60 z-20 animate-fade-in" />
      <div className="fixed bottom-0 left-0 right-0 z-30 bg-vault-card rounded-t-3xl px-5 py-6 flex flex-col gap-5 animate-slide-up max-h-[85vh] overflow-y-auto">
        <div className="w-10 h-1 bg-vault-border rounded-full mx-auto -mt-1" />

        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-vault-muted px-2 py-0.5 rounded-full bg-vault-border">{order.brand}</span>
            {order.is_replacement_only && <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-900/40 text-yellow-400">Replace only</span>}
            {phase === 'pre_delivery' && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/30 text-blue-400">{getDeliveryLabel(order.delivery_status)}</span>
            )}
          </div>
          <h2 className="text-vault-text font-semibold text-base mt-2">{order.item_name}</h2>
          <p className="text-vault-muted text-sm mt-0.5">Order #{order.order_id}</p>
        </div>

        {/* Delivery Timeline */}
        <DeliveryTimeline status={order.delivery_status || 'delivered'} />

        {/* Dates and info */}
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Order Value', value: formatINR(order.price), highlight: true },
            phase === 'return_window' || phase === 'decided'
              ? { label: 'Days Remaining', value: days === null ? '\u2014' : days < 0 ? 'Expired' : `${days} days`, color }
              : { label: 'Delivery Status', value: getDeliveryLabel(order.delivery_status || 'ordered'), color: getDeliveryColor(order.delivery_status || 'ordered') },
            { label: 'Order Date', value: formatDate(order.order_date) },
            order.delivered_date
              ? { label: 'Delivered', value: formatDate(order.delivered_date) }
              : order.shipped_date
              ? { label: 'Shipped', value: formatDate(order.shipped_date) }
              : { label: 'Return Deadline', value: formatDate(order.return_deadline) },
            phase !== 'pre_delivery' && { label: 'Return Deadline', value: formatDate(order.return_deadline) },
            order.category && { label: 'Category', value: order.category },
            order.courier_partner && { label: 'Courier', value: order.courier_partner },
          ].filter(Boolean).map(item => (
            <div key={item.label} className="bg-vault-black rounded-xl px-3 py-3 card-border">
              <p className="text-vault-muted text-xs">{item.label}</p>
              <p className="font-semibold text-sm mt-0.5" style={{ color: item.color || (item.highlight ? '#D4AF37' : '#FFFFFF') }}>{item.value}</p>
            </div>
          ))}
        </div>

        {order.is_replacement_only && (
          <div className="bg-yellow-900/20 border border-yellow-700/30 rounded-xl px-4 py-3 text-sm text-yellow-400">
            \u26a0\ufe0f This item is <strong>replacement only</strong> \u2014 no cash refund available.
          </div>
        )}

        {/* Evidence Locker */}
        <button onClick={() => setShowEvidence(!showEvidence)}
          className="w-full bg-vault-black card-border rounded-2xl px-4 py-3 flex items-center justify-between active:scale-[0.98] transition-transform">
          <div className="flex items-center gap-3">
            <span className="text-lg">\ud83d\udd12</span>
            <div className="text-left">
              <p className="text-vault-text font-medium text-sm">Evidence Locker</p>
              <p className="text-vault-muted text-xs">Photos & videos for dispute proof</p>
            </div>
          </div>
          <span className="text-vault-muted text-sm">{showEvidence ? '\u25b2' : '\u25bc'}</span>
        </button>
        {showEvidence && <EvidenceLocker orderId={order.id} userId={userId} />}

        {/* Action buttons */}
        {order.status === 'active' && phase === 'return_window' && (
          <div className="flex flex-col gap-3">
            <button onClick={() => onReturned(order.id)}
              className="w-full bg-vault-gold text-vault-black py-4 rounded-2xl font-semibold text-base active:scale-95 transition-transform">
              \ud83d\udce6 I Returned This
            </button>
            <button onClick={() => onKept(order.id)}
              className="w-full bg-vault-card card-border text-vault-muted py-4 rounded-2xl font-semibold text-base active:scale-95 transition-transform">
              \u2713 I'm Keeping This
            </button>
          </div>
        )}

        {order.status === 'active' && phase === 'pre_delivery' && (
          <div className="bg-blue-900/15 border border-blue-800/30 rounded-2xl px-4 py-4 text-center">
            <span className="text-2xl">{getDeliveryIcon(order.delivery_status)}</span>
            <p className="text-blue-400 font-medium text-sm mt-1">{getDeliveryLabel(order.delivery_status)}</p>
            <p className="text-vault-muted text-xs mt-0.5">Return window starts after delivery</p>
          </div>
        )}

        {order.status !== 'active' && (
          <div className={`text-center py-3 rounded-2xl text-sm font-medium ${
            order.status === 'returned' ? 'bg-green-900/20 text-green-400'
            : order.status === 'kept' ? 'bg-blue-900/20 text-blue-400'
            : 'bg-vault-card text-vault-muted'
          }`}>
            {order.status === 'returned' ? '\u21a9 Returned successfully'
              : order.status === 'kept' ? '\u2713 You\'re keeping this item \u2014 Good Shopper!'
              : `Status: ${order.status}`}
          </div>
        )}
      </div>
    </>
  )
}


/* ============== EVIDENCE LOCKER ============== */
function EvidenceLocker({ orderId, userId }) {
  const [evidence, setEvidence] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const fileRef = useRef(null)

  useEffect(() => { loadEvidence() }, [orderId])

  async function loadEvidence() {
    setLoading(true)
    try { const data = await api.getEvidence(orderId, userId); setEvidence(data.evidence || []) }
    catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  async function handleFileSelect(e) {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 10 * 1024 * 1024) { setError('File too large (max 10MB)'); setTimeout(() => setError(null), 3000); return }
    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/quicktime']
    if (!allowed.includes(file.type)) { setError('Only JPEG, PNG, WebP, MP4 allowed'); setTimeout(() => setError(null), 3000); return }
    setUploading(true); setError(null)
    try {
      const base64 = await fileToBase64(file)
      await api.uploadEvidence(orderId, userId, base64, file.type, file.name)
      await loadEvidence()
    } catch(e) { console.error(e); setError('Upload failed'); setTimeout(() => setError(null), 3000) }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = '' }
  }

  async function handleDelete(evidenceId) {
    try { await api.deleteEvidence(evidenceId, userId); setEvidence(prev => prev.filter(e => e.id !== evidenceId)) }
    catch(e) { console.error(e) }
  }

  return (
    <div className="flex flex-col gap-3 animate-fade-in">
      <input ref={fileRef} type="file" accept="image/*,video/mp4" capture="environment" onChange={handleFileSelect} className="hidden" />
      <button onClick={() => fileRef.current?.click()} disabled={uploading}
        className="w-full bg-vault-black card-border rounded-xl px-4 py-3 flex items-center justify-center gap-2 active:scale-[0.98] transition-transform">
        {uploading
          ? <><div className="w-4 h-4 border-2 border-vault-gold border-t-transparent rounded-full animate-spin" /><span className="text-vault-muted text-sm">Uploading\u2026</span></>
          : <><span className="text-lg">\ud83d\udcf7</span><span className="text-vault-gold text-sm font-medium">Add Photo / Video</span></>}
      </button>
      {error && <p className="text-red-400 text-xs text-center">{error}</p>}
      {loading ? (
        <div className="flex justify-center py-4"><div className="w-5 h-5 border-2 border-vault-gold border-t-transparent rounded-full animate-spin" /></div>
      ) : evidence.length === 0 ? (
        <p className="text-vault-muted text-xs text-center py-2">No evidence uploaded yet.</p>
      ) : (
        <div className="grid grid-cols-3 gap-2">{evidence.map(item => (
          <div key={item.id} className="relative group">
            {item.file_type?.startsWith('video')
              ? <div className="w-full aspect-square bg-vault-black rounded-xl card-border flex items-center justify-center"><span className="text-2xl">\ud83c\udfac</span></div>
              : <img src={item.file_url} alt="Evidence" className="w-full aspect-square object-cover rounded-xl card-border" />}
            <button onClick={(e) => { e.stopPropagation(); handleDelete(item.id) }}
              className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-[10px] font-bold opacity-0 group-hover:opacity-100 transition-opacity">\u00d7</button>
            <p className="text-vault-muted text-[9px] mt-1 text-center">{new Date(item.uploaded_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</p>
          </div>
        ))}</div>
      )}
      <p className="text-vault-muted text-[10px] text-center">\ud83d\udd12 Evidence is encrypted and only visible to you. Max 10MB per file.</p>
    </div>
  )
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
