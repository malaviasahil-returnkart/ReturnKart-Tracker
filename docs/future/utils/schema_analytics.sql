-- ═══════════════════════════════════════════════════════════════
-- ReturnKart — Analytics Schema (Anonymized Data)
-- Run AFTER schema.sql and schema_encryption_migration.sql
--
-- These tables store ONLY anonymized data.
-- They are the ONLY tables accessible to B2B API consumers.
-- No PII exists in any of these tables.
-- ═══════════════════════════════════════════════════════════════

-- ───────────────────────────
-- TABLE: anon_users
-- Anonymized user profiles for cohort analytics
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS anon_users (
    anon_user_id TEXT PRIMARY KEY,          -- Random: "RK_A7F3B2" (no link to real user)
    pincode_prefix TEXT,                     -- "560" (district level, not specific)
    region TEXT,                              -- "Bangalore Urban" (derived from prefix)
    trust_score_band INTEGER,                -- Perturbed ±2 and rounded to nearest 5
    signup_month TEXT,                        -- "2026-03" (month only, no exact date)
    total_orders INTEGER DEFAULT 0,
    total_returns INTEGER DEFAULT 0,
    return_rate DECIMAL(5,2) DEFAULT 0,      -- Calculated: returns / orders * 100
    avg_order_value DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_anon_users_region ON anon_users(region);
CREATE INDEX idx_anon_users_trust ON anon_users(trust_score_band);

-- ───────────────────────────
-- TABLE: anon_orders
-- Anonymized order data — the core monetizable dataset
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS anon_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anon_user_id TEXT NOT NULL,              -- Links to anon_users (not real users)
    anon_order_ref TEXT UNIQUE NOT NULL,      -- Random: "AORD_K9M2P4T7"

    -- Brand & Product (non-PII, passed through)
    brand TEXT NOT NULL,                      -- "flipkart", "amazon_in"
    brand_name TEXT,                          -- "Flipkart"
    category TEXT,                            -- "mobile", "fashion", "electronics"

    -- Value (exact for aggregation + bucketed for distribution)
    order_value DECIMAL(10,2),               -- Exact INR amount (not PII)
    value_bucket TEXT,                        -- "25K-50K"

    -- Geography (generalized to district, not specific address)
    delivery_pincode_prefix TEXT,             -- "560" (first 3 digits)
    delivery_region TEXT,                     -- "Bangalore Urban"

    -- Logistics (non-PII)
    courier TEXT,                             -- "Ekart Logistics"
    delivery_days INTEGER,                   -- Days from order to delivery
    return_window_days INTEGER,
    is_replacement_only BOOLEAN,
    refund_type TEXT,

    -- Status & Reason (non-PII)
    status TEXT,                              -- "active", "returned", "expired"
    return_reason TEXT,                       -- "Screen defect", "Wrong size"

    -- Blurred timestamps (month precision only)
    order_month TEXT,                         -- "2026-03"
    delivery_month TEXT,                      -- "2026-03"

    -- Derived flags
    days_until_expiry INTEGER,
    is_expired BOOLEAN DEFAULT false,

    -- Metadata
    anonymized_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_anon_orders_brand ON anon_orders(brand);
CREATE INDEX idx_anon_orders_category ON anon_orders(category);
CREATE INDEX idx_anon_orders_region ON anon_orders(delivery_region);
CREATE INDEX idx_anon_orders_status ON anon_orders(status);
CREATE INDEX idx_anon_orders_courier ON anon_orders(courier);
CREATE INDEX idx_anon_orders_month ON anon_orders(order_month);
CREATE INDEX idx_anon_orders_user ON anon_orders(anon_user_id);

-- ───────────────────────────
-- TABLE: anon_ghost_reports
-- Anonymized ghost delivery reports for courier benchmarking
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS anon_ghost_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anon_user_id TEXT NOT NULL,
    anon_order_ref TEXT,
    gps_grid_lat DECIMAL(5,2),               -- ~1.1km precision (2 decimals)
    gps_grid_lng DECIMAL(5,2),               -- ~1.1km precision
    status TEXT,
    report_month TEXT,                        -- "2026-03"
    anonymized_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_anon_ghost_region ON anon_ghost_reports(gps_grid_lat, gps_grid_lng);

-- ───────────────────────────
-- TABLE: anon_switching_matrix
-- Tracks cross-platform behavior (return on A, buy on B)
-- This is the "Switching Matrix" from your strategy doc
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS anon_switching_matrix (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anon_user_id TEXT NOT NULL,
    switch_from_brand TEXT NOT NULL,          -- "amazon_in"
    switch_to_brand TEXT NOT NULL,            -- "flipkart"
    category TEXT,                            -- "mobile"
    value_difference TEXT,                    -- "Saved 1K-2.5K"
    time_delta_days INTEGER,                 -- Days between return and re-purchase
    switch_month TEXT,                        -- "2026-03"
    anonymized_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_switch_from ON anon_switching_matrix(switch_from_brand);
CREATE INDEX idx_switch_to ON anon_switching_matrix(switch_to_brand);
CREATE INDEX idx_switch_category ON anon_switching_matrix(category);

-- ───────────────────────────
-- TABLE: anon_kpi_daily
-- Pre-aggregated daily KPIs for the B2B dashboard
-- No individual records, only aggregate counts
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS anon_kpi_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kpi_date DATE NOT NULL,
    brand TEXT,
    category TEXT,
    region TEXT,
    courier TEXT,

    -- Aggregate metrics (no individual data)
    total_orders INTEGER DEFAULT 0,
    total_returns INTEGER DEFAULT 0,
    total_value DECIMAL(12,2) DEFAULT 0,
    avg_delivery_days DECIMAL(5,1),
    avg_refund_delay_days DECIMAL(5,1),
    ghost_report_count INTEGER DEFAULT 0,
    return_rate DECIMAL(5,2),
    replacement_only_pct DECIMAL(5,2),

    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(kpi_date, brand, category, region, courier)
);

CREATE INDEX idx_kpi_date ON anon_kpi_daily(kpi_date);
CREATE INDEX idx_kpi_brand ON anon_kpi_daily(brand);

-- ═══════════════════════════════════════════════════
-- NO ROW LEVEL SECURITY on analytics tables
-- These are meant to be read by B2B API consumers
-- Access is controlled at the API layer, not database layer
-- ═══════════════════════════════════════════════════

-- B2B API uses a separate Supabase service role key
-- with read-only access to anon_* tables only

-- ═══════════════════════════════════════════════════
-- USEFUL ANALYTICS QUERIES (examples for B2B dashboard)
-- ═══════════════════════════════════════════════════

-- Return rate by brand
-- SELECT brand, COUNT(*) as total,
--        SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) as returns,
--        ROUND(SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END)::decimal / COUNT(*) * 100, 1) as return_rate
-- FROM anon_orders
-- GROUP BY brand ORDER BY return_rate DESC;

-- Courier performance by region
-- SELECT courier, delivery_region, COUNT(*) as deliveries,
--        ROUND(AVG(delivery_days), 1) as avg_days
-- FROM anon_orders
-- WHERE courier IS NOT NULL
-- GROUP BY courier, delivery_region ORDER BY avg_days;

-- Switching matrix (who's losing customers to whom)
-- SELECT switch_from_brand, switch_to_brand, category, COUNT(*) as switches
-- FROM anon_switching_matrix
-- GROUP BY switch_from_brand, switch_to_brand, category
-- ORDER BY switches DESC;

-- Ghost delivery hotspots
-- SELECT gps_grid_lat, gps_grid_lng, COUNT(*) as reports
-- FROM anon_ghost_reports
-- GROUP BY gps_grid_lat, gps_grid_lng
-- HAVING COUNT(*) >= 3
-- ORDER BY reports DESC;
