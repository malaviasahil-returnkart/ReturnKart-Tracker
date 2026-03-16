-- RETURNKART.IN — SUPABASE SCHEMA
-- Instructions: Supabase dashboard → SQL Editor → paste this → Run
-- Then run: python scripts/test_supabase.py to verify.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- TABLE: orders (core entity)
CREATE TABLE IF NOT EXISTS orders (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id              UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    order_id             TEXT NOT NULL,
    brand                TEXT NOT NULL,
    item_name            TEXT NOT NULL,
    price                DECIMAL(10,2) NOT NULL,
    order_date           DATE NOT NULL,
    return_deadline      DATE,
    category             TEXT,
    courier_partner      TEXT,
    delivery_pincode     TEXT,
    is_replacement_only  BOOLEAN DEFAULT FALSE,
    status               TEXT DEFAULT 'active'
                         CHECK (status IN ('active','kept','returned','expired')),
    -- DPDP Act 2023 compliance
    consent_timestamp    TIMESTAMPTZ,
    purpose_id           TEXT DEFAULT 'return_tracking',
    data_expiry_date     DATE,
    anonymization_status BOOLEAN DEFAULT FALSE,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, order_id)
);

-- TABLE: user_consents (immutable DPDP audit log)
CREATE TABLE IF NOT EXISTS user_consents (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    purpose_id   TEXT NOT NULL,
    consented    BOOLEAN NOT NULL,
    consent_text TEXT,
    ip_address   TEXT,
    user_agent   TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- TABLE: gmail_tokens
CREATE TABLE IF NOT EXISTS gmail_tokens (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    access_token  TEXT NOT NULL,
    refresh_token TEXT,
    token_expiry  TIMESTAMPTZ,
    scope         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- TABLE: evidence_locker
CREATE TABLE IF NOT EXISTS evidence_locker (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id        UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    file_url        TEXT NOT NULL,
    file_type       TEXT NOT NULL,
    file_size_bytes INTEGER,
    uploaded_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ROW LEVEL SECURITY
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE gmail_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_locker ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own orders"    ON orders FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own orders"  ON orders FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update own orders"  ON orders FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users view own consents"  ON user_consents FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own consents" ON user_consents FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users manage own gmail token" ON gmail_tokens FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users manage own evidence"    ON evidence_locker FOR ALL USING (auth.uid() = user_id);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_orders_user_id        ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_return_deadline ON orders(return_deadline);
CREATE INDEX IF NOT EXISTS idx_orders_status          ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_brand           ON orders(brand);

-- Verify IST: SELECT NOW() AT TIME ZONE 'Asia/Kolkata' AS ist_time;
