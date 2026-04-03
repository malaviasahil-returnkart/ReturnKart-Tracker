# ReturnKart.in — API Specification

## Base URL
- Dev: `http://localhost:8000`
- Production: `https://return-kart-tracker.replit.app`

## Auth
All endpoints except `/api/health` and `/api/auth/*` require `Authorization: Bearer <supabase-jwt>`.

---

## Endpoints

### Health
`GET /api/health` → `{"status": "ok", "env": "production"}`

### Auth
`GET /api/auth/google` — Initiates Gmail OAuth flow
`GET /api/auth/callback` — OAuth callback, saves token to Supabase
`DELETE /api/auth/revoke` — Revokes Gmail + deletes token (DPDP: Right to Withdraw)

### Orders
`GET /api/orders` — All orders for authenticated user
`POST /api/orders/sync` — Triggers Gmail sync → Gemini parse → Supabase save
`PATCH /api/orders/:id` — Update order status (kept / returned)

---

## Vite Proxy (dev)
`/api/*` requests from frontend → proxied to `http://localhost:8000`
