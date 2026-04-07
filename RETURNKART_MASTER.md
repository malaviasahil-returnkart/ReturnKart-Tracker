# 📦 RETURNKART.IN — MASTER PROJECT STATUS
Last Updated: 2026-04-07
Current Phase: Phase 2 — Product Build
Overall Progress: 15 / 45 tasks complete

---

## 🎯 VISION & POSITIONING

Returnkart.in is the "CIBIL of Commerce" — an automated audit layer that tracks e-commerce orders, calculates return deadlines using AI, and protects consumer funds with zero manual data entry.

**Exit Goal:** Strategic acquisition by Flipkart, PhonePe, or Shiprocket.
**Compliance Foundation:** Strict DPDP Act 2023 — consent-first, purpose limitation, data minimization.

---

## 🏗️ TECH STACK

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite) + Tailwind CSS |
| Backend | Python (FastAPI) — **LIVE** |
| Database | Supabase (PostgreSQL) — **LIVE** |
| AI Engine | Google Gemini 2.5 Flash (REST, no SDK) |
| Primary Data Pipe | Gmail API (OAuth) — universal query |
| HTML Sanitization | BeautifulSoup4 (pre-Gemini) |
| Orchestration | Replit + Claude Desktop |

---

## 📡 OMNI-CHANNEL INGESTION STRATEGY

| Phase | Channel | Target | Status |
|-------|---------|--------|--------|
| Phase 1 (Current) | Web Gmail OAuth | Amazon, Flipkart, Myntra, Ajio, Nykaa | ✅ Live |
| Phase 2 (Future) | Android Expo + BIND_NOTIFICATION_LISTENER_SERVICE | Meesho, Shopsy, Blinkit SMS/WhatsApp | Planned |

**Phase 1 Pipeline:** Gmail OAuth → category:purchases query → BeautifulSoup HTML strip → Gemini extract 5 fields → Python calculates deadline → Supabase upsert

**Phase 2 Pipeline:** Android notification listener → intercept SMS/WhatsApp → same Gemini extract → Python deadline → Supabase sync

---

## 🎨 DESIGN SYSTEM — "Premium Vault" (STRICT)

| Element | Spec | Rule |
|---------|------|------|
| Background | `#0A0A0A` deep black | Always |
| Cards | `#161616` elevated dark gray | Ultra-faded borders |
| Text Primary | `#EDEDED` off-white | Body + headings |
| Text Secondary | Muted gray | Labels + metadata |
| Premium Gold `#D4AF37` | **PRIMARY ACTION BUTTONS ONLY** | "Return Now", "Sync", "Connect Gmail" — NOTHING else |
| Countdown < 48hr | Pulsing highlight | Draw attention |
| Countdown < 12hr | Danger red accent | Urgency |
| Loading States | Progressive skeleton loaders | During parsing |

---

## 🔗 DEEP LINKING (NO API RETURNS)

ReturnKart does NOT process returns. It deep-links users to the platform's native app:

| Platform | Deep Link | Fallback |
|----------|-----------|----------|
| Amazon | `amazon://orders/{order_id}` | `https://www.amazon.in/gp/your-account/order-details?orderID={order_id}` |
| Flipkart | `flipkart://order/{order_id}` | `https://www.flipkart.com/account/orders` |
| Myntra | `myntra://order/{order_id}` | `https://www.myntra.com/my/orders` |

---

## 🔑 CRITICAL ARCHITECTURAL DECISIONS

1. **Universal Gmail query** — single `category:purchases OR category:updates` query replaces 10 platform-specific queries.
2. **HTML sanitization** — BeautifulSoup strips all tags before Gemini sees the text. Never feed raw HTML to AI.
3. **AI extracts only 5 fields** — order_id, brand, item_name, purchase_price, delivery_date. That's it.
4. **Python calculates deadlines** — `return_calculator.py` uses `knowledge_base.json`. AI never calculates dates.
5. **Sequential Gmail fetch** — Gmail API client is NOT thread-safe. Emails fetched one at a time.
6. **Gemini 2.5 Flash REST** — no SDK, httpx async, maxOutputTokens=2048.
7. **Vite proxy** — React calls `/api/*` for writes; Supabase ANON key for reads only.
8. **`config.py` only `os.getenv()` caller** — all modules import constants from here.
9. **PORT from environment** — never hardcode. DO NOT set PORT as Replit Secret.
10. **`FRONTEND_URL`** — must be set as Replit Secret.

---

## 🗄️ SUPABASE DATABASE ✅ LIVE

**Project ID:** `xxfofdkttxrmbymopajo` | **Region:** AWS ap-southeast-2

| Table | Columns | RLS | Status |
|-------|---------|-----|--------|
| `orders` | 18 | ✅ 3 policies + 4 indexes | Live |
| `user_consents` | 8 | ✅ 2 policies | Live |
| `gmail_tokens` | 8 | ✅ 1 policy | Live |
| `evidence_locker` | 7 | ✅ 1 policy | Live |

---

## 🌐 LIVE PRODUCTION URLs

| URL | Status |
|-----|--------|
| `https://returnkart.in/api/health` | ✅ Live |
| `https://returnkart.in/api/docs` | ✅ Swagger UI |
| `https://returnkart.in/api/auth/google` | ✅ OAuth flow |

---

## ✅ ACTIVE SPRINT TRACKER

### PHASE 1: FOUNDATION — ✅ COMPLETE (15/16)

| # | Task | Status |
|---|------|--------|
| 1 | Register returnkart.in domain | [x] |
| 2 | Google Cloud + Gmail API + OAuth client | [x] |
| 3 | Supabase project + API keys | [x] |
| 4 | 6 secrets in Replit Secrets | [x] |
| 5 | GitHub repo + .gitignore | [x] |
| 6 | Supabase schema (4 tables) | [x] |
| 7 | DPDP compliance fields | [x] |
| 8 | Row-Level Security policies | [x] |
| 9 | IST timezone verified | [x] |
| 10 | Gmail OAuth flow | [x] |
| 11 | test_supabase.py — PASSES | [x] |
| 12 | CREATE TABLE executed | [x] |
| 13 | Email fetching (universal query) | [x] |
| 14 | Gemini extraction (5-field, HTML-stripped) | [x] |
| 15 | Supabase upsert (no duplicates) | [x] |
| 16 | Python return deadline calculator | [x] |

### PHASE 2: PRODUCT BUILD (Weeks 5-12) — 0/10 Done

| # | Task | Priority | Status |
|---|------|----------|--------|
| 17 | Screen 1: Zero-Touch Onboarding | Critical | [ ] |
| 18 | Screen 2: Main Dashboard | Critical | [ ] |
| 19 | Screen 3: Order Detail + Deep Link | Critical | [ ] |
| 20 | Screen 4: Settings Vault | High | [ ] |
| 21 | Return Countdown — Money at Risk | Critical | [ ] |
| 22 | Evidence Locker | High | [ ] |
| 23 | Ghost-Buster Flagging | High | [ ] |
| 24 | Good Shopper Rewards | Medium | [ ] |
| 25 | DPDP consent flow | Critical | [ ] |
| 26 | CHECKPOINT: Feature-complete beta | Critical | [ ] |

### PHASE 3 & 4: Unchanged from previous doc.

---

## 📋 WEEKLY LOG

| Week | Date | Completed | Key Decisions |
|------|------|-----------|---------------|
| 1 | 2026-03-14/16 | Phase 1 infra (15/16) | Vite + FastAPI + venv on Nix |
| 4 | 2026-04-07 | Pipeline v2 rewrite | Universal Gmail query, BeautifulSoup HTML strip, 5-field Gemini prompt, Python deadline calc, sequential fetch fix, maxOutputTokens=2048 |

---

*This is the single source of truth for Returnkart.in.*
