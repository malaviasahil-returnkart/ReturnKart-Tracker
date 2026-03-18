# 📦 RETURNKART.IN — MASTER PROJECT STATUS
**Last Updated:** 2026-03-18
**Current Phase:** Phase 2 IN PROGRESS
**Overall Progress:** 22 / 44 tasks complete

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
8. **user_id is TEXT, not UUID** — FK constraints to auth.users removed; RLS policies set to open (tighten when adding Supabase Auth).
9. **Evidence Locker uses base64 in DB** — no Supabase Storage bucket needed for MVP. Files stored as data URIs in `evidence_locker` table.

---

## 🗄️ SUPABASE DATABASE ✅ LIVE

**Project ID:** `xxfofdkttxrmbymopajo` | **Region:** AWS ap-southeast-2

| Table | Columns | RLS | Status |
|-------|---------|-----|--------|
| `orders` | 18 | ✅ Open policies (user_id TEXT) | Live |
| `user_consents` | 8 | ✅ Open policies | Live |
| `gmail_tokens` | 8 | ✅ Open policies | Live |
| `evidence_locker` | 7 | ✅ Open policies | Live |

**Note:** user_id migrated from UUID→TEXT on 2026-03-17. FK constraints to auth.users dropped. RLS policies set to permissive (USING true). Must tighten when implementing proper Supabase Auth.

---

## 🔗 GITHUB REPOS

| Repo | Purpose | Status |
|------|---------|--------|
| `malaviasahil-returnkart/ReturnKart-Tracker` | Main monorepo (matches Replit project) | ✅ Synced |
| `malaviasahil-returnkart/returnkart-backend` | Original backend (legacy reference) | ✅ |
| `malaviasahil-returnkart/returnkart-frontend` | Frontend placeholder | Unused |

---

## 📁 PROJECT STRUCTURE (Clean MVP)

```
~/workspace/
├── backend/           ← Python FastAPI (the real backend)
│   ├── api/           ← auth.py, orders.py, evidence.py, health.py
│   ├── services/      ← supabase_service.py, gmail_service.py, gemini_service.py, return_calculator.py
│   ├── models/        ← order.py (Pydantic)
│   ├── data/          ← knowledge_base.json (RAG return policies)
│   ├── config.py      ← Single env var gateway
│   ├── main.py        ← FastAPI entry point
│   └── requirements.txt
├── frontend/          ← React (Vite) + Tailwind
│   ├── src/
│   │   ├── pages/     ← Dashboard.jsx, Onboarding.jsx, Settings.jsx
│   │   ├── lib/       ← api.js, formatters.js, supabaseClient.js
│   │   ├── styles/    ← globals.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── scripts/           ← test_supabase.py
├── docs/              ← api_spec.md, supabase_schema.sql
│   └── future/        ← Archived non-MVP code (B2B analytics, encryption, TypeScript server, etc.)
├── MASTER_PROJECT_STATUS.md
├── .replit, replit.nix, start.sh
└── .env.example, .gitignore
```

---

## ✅ ACTIVE SPRINT TRACKER

Status Key: `[ ]` Not Started | `[~]` In Progress | `[x]` Done | `[!]` Blocked

### PHASE 1: FOUNDATION — ✅ COMPLETE (16/16)

| # | Task | Status |
|---|------|--------|
| 1 | Register returnkart.in domain | [x] GoDaddy → Cloudflare NS → Replit verified |
| 2 | Google Cloud + Gmail API + OAuth client | [x] |
| 3 | Supabase project + API keys | [x] |
| 4 | 6 secrets in Replit Secrets | [x] |
| 5 | GitHub repo + .gitignore | [x] ReturnKart-Tracker synced |
| 6 | Supabase schema (4 tables) | [x] |
| 7 | DPDP compliance fields | [x] |
| 8 | Row-Level Security policies | [x] Migrated to open (TEXT user_id) |
| 9 | IST timezone verified | [x] |
| 10 | Gmail OAuth flow | [x] |
| 11 | test_supabase.py — PASSES | [x] |
| 12 | CREATE TABLE executed | [x] |
| 13 | Email fetching (5 platforms) | [x] |
| 14 | Gemini + RAG extraction | [x] |
| 15 | Supabase upsert (no duplicates) | [x] |
| 16 | CHECKPOINT: Gmail sync e2e test | [x] Domain live, OAuth login works, dashboard loads |

### PHASE 2: PRODUCT BUILD (Weeks 5-12) — 6/9 Done

| # | Wk | Task | Owner | Priority | Status |
|---|----|----|-------|----------|--------|
| 17 | 5-6 | Screen 1: Zero-Touch Onboarding (Black/Gold UI, Google Sync, DPDP badge) | Dev | Critical | [x] |
| 18 | 5-6 | Screen 2: Main Dashboard (Protected amount, urgent carousel, countdown timers) | Dev | Critical | [x] |
| 19 | 7-8 | Screen 3: Order Detail Modal (Receipt, RAG policy, Mark as Kept/Returned) | Dev | Critical | [x] |
| 20 | 7-8 | Screen 4: Settings Vault (Revoke Gmail, consent timestamp, Delete All Data) | Dev | High | [x] |
| 21 | 8 | Return Countdown — Money at Risk dashboard | Dev | Critical | [x] |
| 22 | 9 | Evidence Locker — Secure photo/video storage (base64 in DB) | Dev | High | [x] |
| 23 | 11 | Good Shopper Rewards — auto-coupon issuance | Dev | Medium | [ ] |
| 24 | 11-12 | DPDP consent flow with timestamped logging | Dev | Critical | [ ] |
| 25 | 12 | CHECKPOINT: Feature-complete app ready for beta | Both | Critical | [ ] |

**Note:** Ghost-Buster Flagging moved to Future Backlog — important but not MVP-critical.

### PHASE 3: LAUNCH & GROWTH (Weeks 13-24) — 0/9 Done

| # | Wk | Task | Owner | Priority | Status |
|---|----|----|-------|----------|--------|
| 26 | 13-14 | Brand identity (logo, colors, social templates) | Founder | High | [ ] |
| 27 | 13-14 | Content strategy around Consumer Protection angle | Founder | High | [ ] |
| 28 | 15-16 | Launch closed beta with 100-200 users | Founder | Critical | [ ] |
| 29 | 16-17 | Iterate UI/UX based on beta feedback | Dev | High | [ ] |
| 30 | 17-18 | SEO + App Store Optimization | Founder | Medium | [ ] |
| 31 | 18-20 | Contact pilot brands for audit fee partnerships | Founder | High | [ ] |
| 32 | 20-22 | Reach 10K-50K users via Consumer Protection marketing | Founder | Critical | [ ] |
| 33 | 22-24 | Launch Good Shopper brand reward program | Both | High | [ ] |
| 34 | 24 | CHECKPOINT: 10K-50K users acquired | Both | Critical | [ ] |

### PHASE 4: MONETIZATION (Weeks 25-48) — 0/10 Done

| # | Wk | Task | Owner | Priority | Status |
|---|----|----|-------|----------|--------|
| 35 | 25-28 | Launch B2B brand audit dashboard | Dev | High | [ ] |
| 36 | 28-30 | Sign first 20 pilot brand partnerships | Founder | Critical | [ ] |
| 37 | 30-32 | Build 3PL Benchmarking SaaS dashboard | Dev | High | [ ] |
| 38 | 32 | CHECKPOINT: 20 pilot brand partnerships secured | Both | Critical | [ ] |
| 39 | 33-36 | Launch Switching Matrix analytics | Dev | High | [ ] |
| 40 | 36-40 | Develop institutional data licensing packages | Founder | High | [ ] |
| 41 | 40-44 | Pitch CIBIL of Returns Trust API | Founder | Critical | [ ] |
| 42 | 41-44 | Build Trust API (usage-based pricing) | Dev | High | [ ] |
| 43 | 45-48 | Begin institutional data licensing conversations | Founder | High | [ ] |
| 44 | 48 | CHECKPOINT: 100K users, 20 brands, revenue validated | Both | Critical | [ ] |

---

## 🔑 KEY MILESTONES

| Target Week | Milestone | Status |
|-------------|-----------|--------|
| Week 4 | Gmail sync working, orders saving to Supabase | [x] ✅ |
| Week 12 | Feature-complete app ready for beta | [~] 6/9 Phase 2 tasks done |
| Week 16 | Closed beta launched (100+ users) | [ ] Not Started |
| Week 24 | 10K-50K users acquired | [ ] Not Started |
| Week 32 | 20 pilot brand partnerships secured | [ ] Not Started |
| Week 48 | SaaS + Trust API revenue validated | [ ] Not Started |

---

## 🔮 FUTURE BACKLOG

Code archived in `docs/future/`. Do not build until post-beta.

- Ghost-Buster Flagging — one-tap CNH reporting + courier reliability scoring (needs `ghost_flags` table)
- Anonymization Pipeline — B2B data anonymization engine (`docs/future/utils/anonymization.js`)
- Encryption Layer — client-side PII encryption (`docs/future/utils/encryption.js`)
- Analytics Schema — B2B reporting tables (`docs/future/utils/schema_analytics.sql`)
- AI Escalation Email Engine — auto-draft dispute emails (`docs/future/data/email_drafting_templates.json`)
- Android Notification Listener Service
- B2B Analytics Dashboard
- Cross-Platform Switching Matrix
- Tighten RLS policies when implementing Supabase Auth

---

## 📋 WEEKLY LOG

| Week # | Date Range | Tasks Completed | Blockers | Key Decisions | Next Focus |
|--------|-----------|----------------|----------|---------------|------------|
| 1 | 2026-03-14/16 | Phase 1 (15/16). Backend LIVE. Swagger UI. .venv fix. GitHub synced. | OAuth e2e needed FRONTEND_URL + test user. | Vite + FastAPI + venv on Nix locked. Cloudflare DNS-only for Replit. | Domain + OAuth login. |
| 2 | 2026-03-17 | Phase 1 COMPLETE (16/16). returnkart.in connected. OAuth e2e working. Dashboard upgraded (stats, carousel, order detail, settings). Tasks 17-21 done. | None. | Ghost-Buster moved to backlog. user_id UUID→TEXT migration. FRONTEND_URL + REDIRECT_URI → returnkart.in. | Evidence Locker, code cleanup. |
| 3 | 2026-03-18 | Evidence Locker built + deployed (Task 22). Codebase decluttered — all non-MVP code moved to docs/future/. Project structure cleaned. | None. | Evidence stored as base64 in DB (no public Storage bucket — DPDP safe). Ghost-Buster confirmed not MVP. | Good Shopper Rewards + DPDP consent logging. |

---

*This is the single source of truth for Returnkart.in.*
