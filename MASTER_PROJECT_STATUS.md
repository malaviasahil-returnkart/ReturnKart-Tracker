# 📦 RETURNKART.IN — MASTER PROJECT STATUS
**Last Updated:** 2026-03-18
**Current Phase:** Phase 2 IN PROGRESS
**Overall Progress:** 24 / 44 tasks complete

---

## 🎯 VISION & POSITIONING

**Returnkart.in** is the **"CIBIL of Commerce"** — an automated audit layer that tracks e-commerce orders, calculates return deadlines using AI, and protects consumer funds with zero manual data entry.

- **For Consumers:** A "Set it and Forget it" financial guardian — no return window ever missed.
- **For Brands:** Verified "Good Shopper" data + accelerated inventory recovery.
- **For 3PLs:** High-integrity logistics benchmarking data.
- **Exit Goal:** Strategic acquisition by Flipkart, PhonePe, or Shiprocket.

**Compliance Foundation:** Strict DPDP Act 2023 — consent-first, purpose limitation, data minimization.

---

## 🏗️ TECH STACK

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite) + Tailwind CSS |
| Backend | Python (FastAPI) — **LIVE** |
| Database | Supabase (PostgreSQL) — **LIVE** |
| AI Engine | Google Gemini 1.5 Flash |
| Primary Data Pipe | Gmail API (OAuth) |
| Orchestration | Replit + Claude Desktop (via MCP) |

---

## 🎨 DESIGN SYSTEM — "Premium Vault"

| Element | Spec |
|---------|------|
| Background | Pitch Black `#0A0A0A` |
| Cards | Dark Charcoal `#1A1A1A` |
| Accent | Premium Gold `#D4AF37` |
| Typography | Inter/Roboto — White `#FFFFFF`, Gray `#A0A0A0` |

---

## 🌐 LIVE PRODUCTION URLs

| URL | Status |
|-----|--------|
| `https://returnkart.in` | ✅ Live — Onboarding + Dashboard |
| `https://returnkart.in/api/health` | ✅ `{"status":"ok"}` |
| `https://returnkart.in/api/docs` | ✅ Swagger UI live |
| `https://returnkart.in/api/auth/google` | ✅ OAuth flow working |
| `https://return-kart-tracker.replit.app` | ✅ Alias (same deployment) |

---

## 🔑 CRITICAL ARCHITECTURAL DECISIONS

1. **Vite proxy** — React calls `/api/*` for writes; Supabase ANON key for reads only.
2. **`config.py` only `os.getenv()` caller** — all modules import constants from here.
3. **PORT from environment** — never hardcode. DO NOT set PORT as Replit Secret.
4. **Python venv** — `.venv/bin/python` for deployment (bypasses Nix immutable store).
5. **`FRONTEND_URL`** — set to `https://returnkart.in` in Replit Secrets.
6. **`GOOGLE_REDIRECT_URI`** — set to `https://returnkart.in/api/auth/callback`.
7. **Cloudflare DNS-only** — gray cloud required; orange cloud breaks Replit SSL cert renewal.
8. **user_id is TEXT, not UUID** — FK constraints to auth.users removed; RLS policies set to open.
9. **Evidence Locker uses base64 in DB** — no Supabase Storage bucket. DPDP safe.
10. **AI Platform Onboarding** — Gemini auto-researches new platforms and generates email domains, return policies, and communication channels.

---

## 🗄️ SUPABASE DATABASE ✅ LIVE

**Project ID:** `xxfofdkttxrmbymopajo` | **Region:** AWS ap-southeast-2

| Table | Columns | RLS | Status |
|-------|---------|-----|--------|
| `orders` | 21 (added delivery_status, shipped_date, delivered_date) | ✅ Open | Live |
| `user_consents` | 8 | ✅ Open | Live |
| `gmail_tokens` | 8 | ✅ Open | Live |
| `evidence_locker` | 7 | ✅ Open | Live |
| `platforms` | 13 (AI-generated platform configs) | ✅ Open | Live |

---

## 🔗 GITHUB REPOS

| Repo | Purpose | Status |
|------|---------|--------|
| `malaviasahil-returnkart/ReturnKart-Tracker` | Main monorepo (matches Replit project) | ✅ Synced |

---

## 📁 PROJECT STRUCTURE (Clean MVP)

```
~/workspace/
├── backend/           ← Python FastAPI
│   ├── api/           ← auth.py, orders.py, evidence.py, platforms.py, health.py
│   ├── services/      ← supabase_service.py, gmail_service.py, gemini_service.py, return_calculator.py
│   ├── models/        ← order.py (Pydantic)
│   ├── data/          ← knowledge_base.json (RAG return policies)
│   ├── config.py      ← Single env var gateway
│   ├── main.py        ← FastAPI entry point
│   └── requirements.txt
├── frontend/          ← React (Vite) + Tailwind
│   ├── src/
│   │   ├── pages/     ← Dashboard.jsx, Onboarding.jsx, Settings.jsx
│   │   ├── lib/       ← api.js, formatters.js, goodShopper.js, deliveryStatus.js
│   │   ├── styles/    ← globals.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html, package.json, tailwind.config.js, vite.config.js
├── scripts/           ← test_supabase.py
├── docs/              ← api_spec.md, supabase_schema.sql
│   └── future/        ← Archived non-MVP code
├── MASTER_PROJECT_STATUS.md
└── .replit, replit.nix, start.sh, .env.example, .gitignore
```

---

## ✅ ACTIVE SPRINT TRACKER

### PHASE 1: FOUNDATION — ✅ COMPLETE (16/16)

| # | Task | Status |
|---|------|--------|
| 1 | Register returnkart.in domain | [x] GoDaddy → Cloudflare NS → Replit verified |
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
| 13 | Email fetching (5 platforms) | [x] |
| 14 | Gemini + RAG extraction | [x] |
| 15 | Supabase upsert (no duplicates) | [x] |
| 16 | CHECKPOINT: Gmail sync e2e test | [x] |

### PHASE 2: PRODUCT BUILD — 8/11 Done

| # | Task | Priority | Status |
|---|----|----------|--------|
| 17 | Zero-Touch Onboarding | Critical | [x] |
| 18 | Main Dashboard (stats, urgent carousel, countdown) | Critical | [x] |
| 19 | Order Detail Modal (mark Kept/Returned) | Critical | [x] |
| 20 | Settings Vault (revoke Gmail, DPDP rights, delete data) | High | [x] |
| 21 | Money at Risk dashboard | Critical | [x] |
| 22 | Evidence Locker (base64 photo/video in DB) | High | [x] |
| 23 | Good Shopper Rewards (trust score, badges, streaks) | Medium | [x] |
| 24 | Delivery Status Tracking (5-step timeline, order phases) | High | [x] |
| 25 | AI Platform Onboarding (Gemini auto-config new platforms) | High | [x] |
| 26 | DPDP consent flow with timestamped logging | Critical | [ ] |
| 27 | CHECKPOINT: Feature-complete for beta | Critical | [ ] |

**Moved to Future Backlog:** Ghost-Buster Flagging (CNH reporting)

### PHASE 3: LAUNCH & GROWTH (Weeks 13-24) — 0/9 Done

| # | Task | Priority | Status |
|---|----|----------|--------|
| 28 | Brand identity (logo, colors, social templates) | High | [ ] |
| 29 | Content strategy (Consumer Protection angle) | High | [ ] |
| 30 | Launch closed beta (100-200 users) | Critical | [ ] |
| 31 | Iterate UI/UX based on feedback | High | [ ] |
| 32 | SEO + App Store Optimization | Medium | [ ] |
| 33 | Contact pilot brands for audit partnerships | High | [ ] |
| 34 | Reach 10K-50K users | Critical | [ ] |
| 35 | Launch Good Shopper brand reward program | High | [ ] |
| 36 | CHECKPOINT: 10K-50K users acquired | Critical | [ ] |

### PHASE 4: MONETIZATION (Weeks 25-48) — 0/10 Done

| # | Task | Priority | Status |
|---|----|----------|--------|
| 37 | Launch B2B brand audit dashboard | High | [ ] |
| 38 | Sign first 20 pilot brand partnerships | Critical | [ ] |
| 39 | Build 3PL Benchmarking SaaS dashboard | High | [ ] |
| 40 | CHECKPOINT: 20 pilot partnerships | Critical | [ ] |
| 41 | Switching Matrix analytics | High | [ ] |
| 42 | Institutional data licensing packages | High | [ ] |
| 43 | CIBIL of Returns Trust API pitch | Critical | [ ] |
| 44 | Build Trust API (usage-based pricing) | High | [ ] |
| 45 | Begin institutional licensing conversations | High | [ ] |
| 46 | CHECKPOINT: 100K users, 20 brands, revenue | Critical | [ ] |

---

## 🔑 KEY MILESTONES

| Target Week | Milestone | Status |
|-------------|-----------|--------|
| Week 4 | Gmail sync working, orders in Supabase | [x] ✅ |
| Week 12 | Feature-complete for beta | [~] 8/11 Phase 2 done |
| Week 16 | Closed beta (100+ users) | [ ] |
| Week 24 | 10K-50K users | [ ] |
| Week 32 | 20 pilot brand partnerships | [ ] |
| Week 48 | SaaS + Trust API revenue | [ ] |

---

## 🔮 FUTURE BACKLOG

Code archived in `docs/future/`.

- Ghost-Buster Flagging — CNH reporting + courier reliability (needs `ghost_flags` table)
- Anonymization Pipeline — B2B data engine (`docs/future/utils/anonymization.js`)
- Encryption Layer — client-side PII encryption (`docs/future/utils/encryption.js`)
- Analytics Schema — B2B reporting tables (`docs/future/utils/schema_analytics.sql`)
- AI Escalation Email Engine — auto-draft dispute emails
- Android Notification Listener Service (Java/Kotlin native module)
- SMS Reader (needs Google Play policy justification)
- WhatsApp notification capture (via Android notification listener only)
- React Native + Expo mobile app (Phase 3)
- B2B Analytics Dashboard
- Cross-Platform Switching Matrix
- Tighten RLS policies with Supabase Auth

---

## 📋 WEEKLY LOG

| Week # | Date Range | Tasks Completed | Key Decisions | Next Focus |
|--------|-----------|----------------|---------------|------------|
| 1 | 2026-03-14/16 | Phase 1 (15/16). Backend LIVE. | Vite + FastAPI + venv on Nix. Cloudflare DNS-only. | Domain + OAuth. |
| 2 | 2026-03-17 | Phase 1 COMPLETE. Tasks 17-21 done. returnkart.in live. | Ghost-Buster → backlog. UUID→TEXT migration. | Evidence Locker, cleanup. |
| 3 | 2026-03-18 | Evidence Locker (T22). Good Shopper Rewards (T23). Delivery Tracking (T24). AI Platform Onboarding (T25). Codebase decluttered. `platforms` table added. | Evidence = base64 in DB. Ghost-Buster not MVP. Delivery status = 5-step journey. AI researches new platforms via Gemini. | DPDP consent logging → beta checkpoint. |

---

*This is the single source of truth for Returnkart.in.*
