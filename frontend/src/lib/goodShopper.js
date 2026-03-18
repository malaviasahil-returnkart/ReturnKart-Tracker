/**
 * ReturnKart — Good Shopper Rewards Engine
 * Calculates trust score, streak, and badge from order history.
 * Pure client-side — no new API calls or DB tables needed.
 *
 * Trust Score (0-100):
 *   Base: 50 (new user)
 *   +5 per order kept (expired without return)
 *   +3 per order manually marked as "kept"
 *   -10 per returned order
 *
 * Streak: consecutive non-returned orders from most recent
 *
 * Badges: New → Bronze → Silver → Gold → Platinum
 */

export function calculateTrustScore(orders) {
  if (!orders || orders.length === 0) return { score: 50, label: 'New', emoji: '🆕' }

  let score = 50

  orders.forEach(order => {
    if (order.status === 'kept') score += 3
    else if (order.status === 'expired') score += 5
    else if (order.status === 'returned') score -= 10
    // 'active' orders don't affect score yet
  })

  // Clamp 0-100
  score = Math.max(0, Math.min(100, score))

  return { score, ...getBadge(score) }
}

export function getBadge(score) {
  if (score >= 90) return { label: 'Platinum', emoji: '💎', color: '#E5E4E2', tier: 4 }
  if (score >= 80) return { label: 'Gold', emoji: '🥇', color: '#D4AF37', tier: 3 }
  if (score >= 65) return { label: 'Silver', emoji: '🥈', color: '#C0C0C0', tier: 2 }
  if (score >= 50) return { label: 'Bronze', emoji: '🥉', color: '#CD7F32', tier: 1 }
  return { label: 'New', emoji: '🆕', color: '#A0A0A0', tier: 0 }
}

export function calculateStreak(orders) {
  if (!orders || orders.length === 0) return 0

  // Sort by order_date descending (most recent first)
  const sorted = [...orders]
    .filter(o => o.status !== 'active') // only resolved orders count
    .sort((a, b) => new Date(b.order_date) - new Date(a.order_date))

  let streak = 0
  for (const order of sorted) {
    if (order.status === 'kept' || order.status === 'expired') {
      streak++
    } else {
      break // streak broken by a return
    }
  }
  return streak
}

export function getStreakMessage(streak) {
  if (streak >= 10) return { text: 'Legendary keeper! 🏆', fire: true }
  if (streak >= 7) return { text: 'On fire! 🔥🔥🔥', fire: true }
  if (streak >= 5) return { text: 'Great streak! 🔥🔥', fire: true }
  if (streak >= 3) return { text: 'Building momentum! 🔥', fire: false }
  if (streak >= 1) return { text: 'Good start!', fire: false }
  return { text: '', fire: false }
}

export function getRewardsSummary(orders) {
  const trustData = calculateTrustScore(orders)
  const streak = calculateStreak(orders)
  const streakMsg = getStreakMessage(streak)

  const keptCount = orders.filter(o => o.status === 'kept' || o.status === 'expired').length
  const returnedCount = orders.filter(o => o.status === 'returned').length
  const totalResolved = keptCount + returnedCount
  const keepRate = totalResolved > 0 ? Math.round((keptCount / totalResolved) * 100) : 100

  return {
    ...trustData,
    streak,
    streakMsg,
    keptCount,
    returnedCount,
    keepRate,
  }
}
