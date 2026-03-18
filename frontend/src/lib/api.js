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
  authRevoke:  (userId) => request(`/api/auth/revoke?user_id=${userId}`, { method: 'DELETE' }),
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

  // Evidence Locker
  getEvidence: (orderId, userId) => request(`/api/evidence/${orderId}?user_id=${userId}`),
  uploadEvidence: (orderId, userId, fileData, fileType, fileName) => request('/api/evidence/upload', {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      order_id: orderId,
      file_data: fileData,
      file_type: fileType,
      file_name: fileName,
    }),
  }),
  deleteEvidence: (evidenceId, userId) => request(`/api/evidence/${evidenceId}?user_id=${userId}`, {
    method: 'DELETE',
  }),
}
