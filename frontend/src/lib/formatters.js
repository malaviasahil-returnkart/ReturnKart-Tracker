// ReturnKart — shared formatting utilities

export function formatINR(amount) {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d)) return '—'
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function daysRemaining(deadlineStr) {
  if (!deadlineStr) return null
  const deadline = new Date(deadlineStr)
  if (isNaN(deadline)) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  deadline.setHours(0, 0, 0, 0)
  return Math.round((deadline - today) / (1000 * 60 * 60 * 24))
}

export function urgencyLevel(days) {
  if (days === null) return 'unknown'
  if (days < 0) return 'expired'
  if (days <= 2) return 'critical'
  if (days <= 5) return 'urgent'
  return 'safe'
}

export function urgencyColor(level) {
  switch (level) {
    case 'critical': return '#FF6B6B'
    case 'urgent':   return '#D4AF37'
    case 'safe':     return '#4ADE80'
    case 'expired':  return '#666666'
    default:         return '#A0A0A0'
  }
}
