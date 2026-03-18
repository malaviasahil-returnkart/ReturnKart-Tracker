/**
 * ReturnKart — Good Shopper Rewards Engine
 * Calculates trust score, badges, streaks, and keep rate from order data.
 * Pure frontend calculation — no backend or DB needed.
 */

export function getRewardsSummary(allOrders) {
  // Resolved = orders where user made a decision
  const resolved = allOrders.filter(o => ['kept', 'returned', 'expired'].includes(o.status))
  const kept = resolved.filter(o => o.status === 'kept' || o.status === 'expired')
  const returned = resolved.filter(o => o.status === 'returned')
  const resolvedCount = resolved.length

  // Keep rate (expired counts as kept)
  const keepRate = resolvedCount > 0 ? Math.round((kept.length / resolvedCount) * 100) : 0

  // Calculate streak (consecutive kept/expired, most recent first)
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
  const volumeBonus = Math.min(Math.floor(allOrders.length / 5), 10)
  const score = Math.min(baseScore + streakBonus + volumeBonus, 100)

  // Badge tier
  let emoji, label, color
  if (score >= 90) {
    emoji = '💎'; label = 'Platinum'; color = '#E5E4E2'
  } else if (score >= 80) {
    emoji = '🏆'; label = 'Gold'; color = '#D4AF37'
  } else if (score >= 65) {
    emoji = '🥈'; label = 'Silver'; color = '#C0C0C0'
  } else if (score >= 50) {
    emoji = '🥉'; label = 'Bronze'; color = '#CD7F32'
  } else if (allOrders.length > 0) {
    emoji = '⭐'; label = 'Rising'; color = '#FBBF24'
  } else {
    emoji = '🌱'; label = 'New'; color = '#A0A0A0'
  }

  // Streak message
  let streakMsg = { fire: false, text: '' }
  if (streak >= 10) {
    streakMsg = { fire: true, text: 'Incredible! Brands love shoppers like you.' }
  } else if (streak >= 5) {
    streakMsg = { fire: true, text: 'Amazing streak! Keep it going.' }
  } else if (streak >= 3) {
    streakMsg = { fire: false, text: 'Nice streak! Building trust.' }
  } else if (streak >= 1) {
    streakMsg = { fire: false, text: 'Good start! Every kept order counts.' }
  }

  return {
    score,
    emoji,
    label,
    color,
    keepRate,
    streak,
    streakMsg,
    keptCount: kept.length,
    returnedCount: returned.length,
    totalValueKept: kept.reduce((sum, o) => sum + (o.price || 0), 0),
  }
}
