export async function getAuthUrl(): Promise<string> {
  const res = await fetch("/api/email/auth-url");
  if (!res.ok) throw new Error("Failed to get auth URL");
  const data = await res.json();
  return data.url;
}

export async function syncEmails(tokens: { access_token: string; refresh_token?: string }) {
  const res = await fetch("/api/email/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tokens),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: "Sync failed" }));
    throw new Error(err.message);
  }
  return res.json();
}

export async function getOrders() {
  const res = await fetch("/api/orders");
  if (!res.ok) throw new Error("Failed to fetch orders");
  return res.json();
}

export async function getOrderStats() {
  const res = await fetch("/api/orders/summary/stats");
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}
