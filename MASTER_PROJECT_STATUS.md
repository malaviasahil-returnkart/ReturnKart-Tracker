# 📦 RETURNKART.IN — MASTER PROJECT STATUS
Last Updated: 2026-03-16
Current Phase: Phase 1 COMPLETE → Starting Phase 2
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
| `https://return-kart-tracker.replit.app/api/health` | ✅ `{"status":"ok"}` |
| `https://return-kart-tracker.replit.app/api/docs` | ✅ Swagger UI live |
| `https://return-kart-tracker.replit.app/api/auth/google` | ✅ OAuth flow ready |

---

## 🔑 CRITICAL ARCHITECTURAL DECISIONS

1. **Vite proxy** — React calls `/api/*` for writes; Supabase ANON key for reads only.
2. **`config.py` only `os.getenv()` caller** — all modules import constants from here.
3. **PORT from environment** — never hardcode. DO NOT set PORT as Replit Secret.
4. **Python venv** — `.venv/bin/python` for deployment (bypasses Nix immutable store).
5. **`FRONTEND_URL`** — must be set as Replit Secret to `https://return-kart-tracker.replit.app`.

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

## ✅ ACTIVE SPRINT TRACKER

Status Key: `[ ]` Not Started | `[~]` In Progress | `[x]` Done | `[!]` Blocked

### PHASE 1: FOUNDATION — ✅ COMPLETE (15/16)

| # | Task | Status |
|---|------|--------|
| 1 | Register returnkart.in domain | [ ] |
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
| 16 | CHECKPOINT: Gmail sync e2e test | [~] |

### PHASE 2: PRODUCT BUILD (Weeks 5-12) — 0/10 Done

| # | Wk | Task | Owner | Priority | Status |
|---|----|----|-------|----------|--------|
| 17 | 5-6 | Screen 1: Zero-Touch Onboarding (Black/Gold UI, Google Sync, DPDP badge) | Dev | Critical | [ ] |
| 18 | 5-6 | Screen 2: Main Dashboard (Protected amount, urgent carousel, countdown timers) | Dev | Critical | [ ] |
| 19 | 7-8 | Screen 3: Order Detail Modal (Receipt, RAG policy, Mark as Kept/Returned) | Dev | Critical | [ ] |
| 20 | 7-8 | Screen 4: Settings Vault (Revoke Gmail, consent timestamp, Delete All Data) | Dev | High | [ ] |
| 21 | 8 | Return Countdown — Money at Risk dashboard | Dev | Critical | [ ] |
| 22 | 9 | Evidence Locker — Secure photo/video storage | Dev | High | [ ] |
| 23 | 10 | Ghost-Buster Flagging — one-tap CNH reporting | Dev | High | [ ] |
| 24 | 11 | Good Shopper Rewards — auto-coupon issuance | Dev | Medium | [ ] |
| 25 | 11-12 | DPDP consent flow with timestamped logging | Dev | Critical | [ ] |
| 26 | 12 | CHECKPOINT: Feature-complete app ready for beta | Both | Critical | [ ] |

### PHASE 3: LAUNCH & GROWTH (Weeks 13-24) — 0/9 Done

| # | Wk | Task | Owner | Priority | Status |
|---|----|----|-------|----------|--------|
| 27 | 13-14 | Brand identity (logo, colors, social templates) | Founder | High | [ ] |
| 28 | 13-14 | Content strategy around Consumer Protection angle | Founder | High | [ ] |
| 29 | 15-16 | Launch closed beta with 100-200 users | Founder | Critical | [ ] |
| 30 | 16-17 | Iterate UI/UX based on beta feedback | Dev | High | [ ] |
| 31 | 17-18 | SEO + App Store Optimization | Founder | Medium | [ ] |
| 32 | 18-20 | Contact pilot brands for audit fee partnerships | Founder | High | [ ] |
| 33 | 20-22 | Reach 10K-50K users via Consumer Protection marketing | Founder | Critical | [ ] |
| 34 | 22-24 | Launch Good Shopper brand reward program | Both | High | [ ] |
| 35 | 24 | CHECKPOINT: 10K-50K users acquired | Both | Critical | [ ] |

### PHASE 4: MONETIZATION (Weeks 25-48) — 0/10 Done

| # | Wk | Task | Owner | Priority | Status |
|---|----|----|-------|----------|--------|
| 36 | 25-28 | Launch B2B brand audit dashboard | Dev | High | [ ] |
| 37 | 28-30 | Sign first 20 pilot brand partnerships | Founder | Critical | [ ] |
| 38 | 30-32 | Build 3PL Benchmarking SaaS dashboard | Dev | High | [ ] |
| 39 | 32 | CHECKPOINT: 20 pilot brand partnerships secured | Both | Critical | [ ] |
| 40 | 33-36 | Launch Switching Matrix analytics | Dev | High | [ ] |
| 41 | 36-40 | Develop institutional data licensing packages | Founder | High | [ ] |
| 42 | 40-44 | Pitch CIBIL of Returns Trust API | Founder | Critical | [ ] |
| 43 | 41-44 | Build Trust API (usage-based pricing) | Dev | High | [ ] |
| 44 | 45-48 | Begin institutional data licensing conversations | Founder | High | [ ] |
| 45 | 48 | CHECKPOINT: 100K users, 20 brands, revenue validated | Both | Critical | [ ] |

---

## 🔑 KEY MILESTONES

| Target Week | Milestone | Status |
|-------------|-----------|--------|
| Week 4 | Gmail sync working, orders saving to Supabase | [~] Backend live. e2e test pending. |
| Week 12 | Feature-complete app ready for beta | [ ] Not Started |
| Week 16 | Closed beta launched (100+ users) | [ ] Not Started |
| Week 24 | 10K-50K users acquired | [ ] Not Started |
| Week 32 | 20 pilot brand partnerships secured | [ ] Not Started |
| Week 48 | SaaS + Trust API revenue validated | [ ] Not Started |

---

## 🔮 FUTURE BACKLOG

- Android Notification Listener Service
- AI Escalation Email Engine
- B2B Analytics Dashboard
- Cross-Platform Switching Matrix

---

## 📋 WEEKLY LOG

| Week # | Date Range | Tasks Completed | Blockers | Key Decisions | Next Focus |
|--------|-----------|----------------|----------|---------------|------------|
| 1 | 2026-03-14/16 | Phase 1 complete (15/16). Backend LIVE at return-kart-tracker.replit.app. Swagger UI live. .venv deployment fix. | Task #1 (domain) pending. OAuth e2e test needs FRONTEND_URL secret + test user in Google Cloud. | Vite + FastAPI + venv on Nix locked. | Phase 2: React frontend (Vite, black/gold, mobile-first) |

---

*This is the single source of truth for Returnkart.in.*
