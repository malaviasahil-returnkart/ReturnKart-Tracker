const BACKEND_URL = 'https://return-manager.replit.app';

export async function getAuthUrl(): Promise<string> {
  const res = await fetch(`${BACKEND_URL}/api/email/auth-url`);
  const data = await res.json();
  return data.url;
}

export async function syncEmails(tokens: { access_token: string; refresh_token?: string }) {
  const res = await fetch(`${BACKEND_URL}/api/email/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tokens),
  });
  return res.json();
}

export async function getOrders() {
  const res = await fetch(`${BACKEND_URL}/api/orders`);
  return res.json();
}

export async function getOrderStats() {
  const res = await fetch(`${BACKEND_URL}/api/orders/summary/stats`);
  return res.json();
}
