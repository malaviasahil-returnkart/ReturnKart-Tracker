/**
 * ReturnKart API client
 * All calls go through /api/* — proxied to FastAPI backend in dev,
 * served directly on production domain.
 */

const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => request('/api/health'),

  // Auth
  authStatus:  (userId) => request(`/api/auth/status?user_id=${userId}`),
  authRevoke:  (userId, email) => {
    const url = email
      ? `/api/auth/revoke?user_id=${userId}&email=${encodeURIComponent(email)}`
      : `/api/auth/revoke?user_id=${userId}`
    return request(url, { method: 'DELETE' })
  },
  getAccounts: (userId) => request(`/api/auth/accounts?user_id=${userId}`),
  gmailOAuthUrl: (userId) => `${BASE}/api/auth/google?user_id=${userId}`,

  // Orders
  getOrders:   (userId, status) => request(`/api/orders?user_id=${userId}${status ? `&status=${status}` : ''}`),
  getUrgent:   (userId, days = 3) => request(`/api/orders/urgent?user_id=${userId}&days=${days}`),
  patchOrder:  (orderId, userId, status) => request(`/api/orders/${orderId}`, {
    method: 'PATCH',
    body: JSON.stringify({ user_id: userId, status }),
  }),
  syncGmail:   (userId) => request('/api/orders/sync', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  }),
}
