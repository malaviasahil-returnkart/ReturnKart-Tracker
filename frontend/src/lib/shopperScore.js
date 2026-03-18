/**
 * ReturnKart — Good Shopper Score Engine
 * Calculates trust score, badges, and streaks from order data.
 * Pure frontend calculation — no backend or DB needed.
 */

// Badge definitions (ordered by tier)
const BADGES = [
  { id: 'diamond', name: 'Diamond Shopper', icon: '💎', minOrders: 50, minKeepRate: 90, color: '#B9F2FF' },
  { id: 'gold',    name: 'Gold Shopper',    icon: '🏆', minOrders: 20, minKeepRate: 85, color: '#D4AF37' },
  { id: 'trusted', name: 'Trusted Buyer',   icon: '🛡️', minOrders: 10, minKeepRate: 75, color: '#4ADE80' },
  { id: 'rising',  name: 'Rising Star',     icon: '⭐', minOrders: 5,  minKeepRate: 60, color: '#FBBF24' },
  { id: 'new',     name: 'New Shopper',     icon: '🌱', minOrders: 0,  minKeepRate: 0,  color: '#A0A0A0' },
]

export function computeShopperStats(allOrders) {
  // Resolved = orders where user made a decision (kept, returned, expired)
  const resolved = allOrders.filter(o => ['kept', 'returned', 'expired'].includes(o.status))
  const kept = resolved.filter(o => o.status === 'kept' || o.status === 'expired')
  const returned = resolved.filter(o => o.status === 'returned')
  const totalOrders = allOrders.length
  const resolvedCount = resolved.length

  // Keep rate (expired counts as kept — they didn't return it)
  const keepRate = resolvedCount > 0 ? Math.round((kept.length / resolvedCount) * 100) : 0

  // Calculate streak (consecutive kept/expired orders, sorted by date)
  const sortedResolved = [...resolved].sort((a, b) =>
    new Date(b.order_date) - new Date(a.order_date)
  )
  let streak = 0
  for (const order of sortedResolved) {
    if (order.status === 'kept' || order.status === 'expired') {
      streak++
    } else {
      break
    }
  }

  // Trust score formula
  // Base: keep rate (0-70 points)
  // Streak bonus: +2 per streak (max +20)
  // Volume bonus: +1 per 5 orders (max +10)
  const baseScore = Math.round(keepRate * 0.7)
  const streakBonus = Math.min(streak * 2, 20)
  const volumeBonus = Math.min(Math.floor(totalOrders / 5), 10)
  const trustScore = Math.min(baseScore + streakBonus + volumeBonus, 100)

  // Determine badge
  let badge = BADGES[BADGES.length - 1] // default: New Shopper
  for (const b of BADGES) {
    if (resolvedCount >= b.minOrders && keepRate >= b.minKeepRate) {
      badge = b
      break
    }
  }

  // Total value kept
  const totalValueKept = kept.reduce((sum, o) => sum + (o.price || 0), 0)

  return {
    trustScore,
    keepRate,
    streak,
    totalOrders,
    resolvedCount,
    keptCount: kept.length,
    returnedCount: returned.length,
    totalValueKept,
    badge,
    // Score breakdown (for Settings or detail view)
    scoreBreakdown: {
      baseScore,
      streakBonus,
      volumeBonus,
    }
  }
}

export function getTrustScoreColor(score) {
  if (score >= 80) return '#4ADE80'  // green
  if (score >= 60) return '#D4AF37'  // gold
  if (score >= 40) return '#FBBF24'  // yellow
  if (score >= 20) return '#FB923C'  // orange
  return '#A0A0A0'                   // gray
}

export function getTrustScoreLabel(score) {
  if (score >= 80) return 'Excellent'
  if (score >= 60) return 'Good'
  if (score >= 40) return 'Average'
  if (score >= 20) return 'Building'
  return 'New'
}
