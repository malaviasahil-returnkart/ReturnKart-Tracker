/**
 * ReturnKart — Delivery Status Engine
 * Maps delivery_status to UI elements (icons, colors, progress)
 * 
 * Journey: ordered → shipped → in_transit → out_for_delivery → delivered → [return window starts]
 */

const STEPS = [
  { key: 'ordered',          label: 'Ordered',          icon: '📝', short: 'Ordered' },
  { key: 'shipped',          label: 'Shipped',          icon: '📦', short: 'Shipped' },
  { key: 'in_transit',       label: 'In Transit',       icon: '🚚', short: 'Transit' },
  { key: 'out_for_delivery', label: 'Out for Delivery', icon: '🚴', short: 'Out' },
  { key: 'delivered',        label: 'Delivered',        icon: '✅', short: 'Delivered' },
]

export function getDeliverySteps() {
  return STEPS
}

export function getDeliveryProgress(status) {
  const idx = STEPS.findIndex(s => s.key === status)
  if (idx === -1) return { stepIndex: 0, percent: 0, currentStep: STEPS[0] }
  const percent = Math.round((idx / (STEPS.length - 1)) * 100)
  return { stepIndex: idx, percent, currentStep: STEPS[idx] }
}

export function getDeliveryLabel(status) {
  const step = STEPS.find(s => s.key === status)
  return step ? step.label : 'Ordered'
}

export function getDeliveryIcon(status) {
  const step = STEPS.find(s => s.key === status)
  return step ? step.icon : '📝'
}

export function getDeliveryColor(status) {
  switch(status) {
    case 'delivered':        return '#4ADE80' // green
    case 'out_for_delivery': return '#FBBF24' // yellow
    case 'in_transit':       return '#60A5FA' // blue
    case 'shipped':          return '#A78BFA' // purple
    default:                 return '#A0A0A0' // gray
  }
}

/**
 * Determine the overall "phase" of the order for the user
 * Phase 1: Pre-delivery (ordered → out_for_delivery)
 * Phase 2: Return window (delivered, deadline in future)
 * Phase 3: Decision made (kept/returned/expired)
 */
export function getOrderPhase(order) {
  if (['kept', 'returned', 'expired'].includes(order.status)) return 'decided'
  if (order.delivery_status === 'delivered') return 'return_window'
  return 'pre_delivery'
}
