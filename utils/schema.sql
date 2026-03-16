-- ═══════════════════════════════════════════════════
-- ReturnKart RAG System — Supabase Database Schema
-- Timezone: Asia/Kolkata (IST)
-- ═══════════════════════════════════════════════════

-- Set default timezone to IST
ALTER DATABASE postgres SET timezone TO 'Asia/Kolkata';

-- ───────────────────────────
-- TABLE: users
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    display_name TEXT,
    avatar_url TEXT,
    pincode TEXT CHECK (length(pincode) = 6),
    trust_score INTEGER DEFAULT 50 CHECK (trust_score >= 0 AND trust_score <= 100),
    -- DPDP Compliance Fields
    consent_timestamp TIMESTAMPTZ,
    consent_purposes TEXT[] DEFAULT '{}',
    data_expiry_date TIMESTAMPTZ DEFAULT (now() + INTERVAL '24 months'),
    anonymization_status BOOLEAN DEFAULT false,
    -- Notification Preferences
    notify_expiry_reminders BOOLEAN DEFAULT true,
    notify_refund_confirmations BOOLEAN DEFAULT true,
    notify_rewards BOOLEAN DEFAULT true,
    notify_weekly_summary BOOLEAN DEFAULT false,
    -- Google OAuth
    google_access_token TEXT,
    google_refresh_token TEXT,
    last_gmail_sync TIMESTAMPTZ,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ───────────────────────────
-- TABLE: orders
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- Order Context
    order_id_external TEXT NOT NULL,
    brand_slug TEXT NOT NULL,
    brand_display_name TEXT,
    item_name TEXT NOT NULL,
    item_category TEXT,
    order_value DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'INR',
    quantity INTEGER DEFAULT 1,
    -- Dates
    order_date DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    -- Return Logic
    return_window_days INTEGER,
    return_expiry_date DATE,
    is_replacement_only BOOLEAN DEFAULT false,
    refund_type TEXT CHECK (refund_type IN ('bank_refund', 'store_credit', 'replacement', NULL)),
    -- Logistics
    delivery_pincode TEXT,
    courier_partner TEXT,
    tracking_id TEXT,
    -- Status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expiring_soon', 'expired', 'return_initiated', 'returned', 'refunded', 'kept')),
    return_reason TEXT,
    -- Source Tracking
    email_id TEXT,
    notification_source TEXT,
    parsed_at TIMESTAMPTZ DEFAULT now(),
    ai_confidence_score DECIMAL(3,2),
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    -- Constraints
    UNIQUE(user_id, order_id_external, brand_slug)
);

-- ───────────────────────────
-- TABLE: evidence
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('photo', 'video')),
    file_size_bytes INTEGER,
    sha256_hash TEXT NOT NULL,
    duration_seconds INTEGER,
    thumbnail_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ───────────────────────────
-- TABLE: ghost_reports
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS ghost_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    gps_latitude DECIMAL(10,8),
    gps_longitude DECIMAL(11,8),
    address_text TEXT,
    description TEXT,
    evidence_ids UUID[] DEFAULT '{}',
    status TEXT DEFAULT 'submitted' CHECK (status IN ('submitted', 'under_review', 'resolved', 'rejected')),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ───────────────────────────
-- TABLE: rewards
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    brand_slug TEXT NOT NULL,
    brand_display_name TEXT,
    coupon_code TEXT,
    description TEXT NOT NULL,
    discount_value DECIMAL(10,2),
    discount_type TEXT CHECK (discount_type IN ('percentage', 'flat', 'freebie')),
    expiry_date DATE,
    is_claimed BOOLEAN DEFAULT false,
    claimed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ───────────────────────────
-- TABLE: notifications
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('expiry_alert', 'expiry_final', 'refund_received', 'reward_earned', 'ghost_update', 'sync_complete', 'system')),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    reference_type TEXT,
    reference_id UUID,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ───────────────────────────
-- TABLE: escalation_emails
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS escalation_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    escalation_level INTEGER NOT NULL CHECK (escalation_level BETWEEN 1 AND 4),
    issue_type TEXT NOT NULL,
    subject_line TEXT NOT NULL,
    email_body TEXT NOT NULL,
    recipient_email TEXT,
    is_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,
    platform_response TEXT,
    response_received_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ───────────────────────────
-- TABLE: complaint_timeline
-- ───────────────────────────
CREATE TABLE IF NOT EXISTS complaint_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    channel TEXT CHECK (channel IN ('email', 'phone', 'chat', 'app', 'social_media', 'consumer_forum')),
    details TEXT,
    platform_response TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ═══════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_expiry ON orders(return_expiry_date);
CREATE INDEX idx_orders_brand ON orders(brand_slug);
CREATE INDEX idx_evidence_order ON evidence(order_id);
CREATE INDEX idx_ghost_reports_order ON ghost_reports(order_id);
CREATE INDEX idx_rewards_user ON rewards(user_id);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_escalation_order ON escalation_emails(order_id);
CREATE INDEX idx_complaint_order ON complaint_timeline(order_id);

-- ═══════════════════════════════════════════════════
-- ROW LEVEL SECURITY (RLS)
-- ═══════════════════════════════════════════════════

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE ghost_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE rewards ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalation_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaint_timeline ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users read own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users update own data" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users read own orders" ON orders FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own orders" ON orders FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update own orders" ON orders FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users read own evidence" ON evidence FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own evidence" ON evidence FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users delete own evidence" ON evidence FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users read own ghost_reports" ON ghost_reports FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own ghost_reports" ON ghost_reports FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users read own rewards" ON rewards FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users update own rewards" ON rewards FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users read own notifications" ON notifications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users update own notifications" ON notifications FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users read own escalation_emails" ON escalation_emails FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own escalation_emails" ON escalation_emails FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users read own complaint_timeline" ON complaint_timeline FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own complaint_timeline" ON complaint_timeline FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════
-- FUNCTIONS
-- ═══════════════════════════════════════════════════

-- Auto-update return status based on expiry date
CREATE OR REPLACE FUNCTION update_order_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.return_expiry_date IS NOT NULL THEN
        IF NEW.return_expiry_date < CURRENT_DATE AND NEW.status = 'active' THEN
            NEW.status := 'expired';
        ELSIF NEW.return_expiry_date <= CURRENT_DATE + INTERVAL '3 days' AND NEW.status = 'active' THEN
            NEW.status := 'expiring_soon';
        END IF;
    END IF;
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_order_status
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_order_status();

-- Auto-calculate return_expiry_date when delivery date is set
CREATE OR REPLACE FUNCTION calculate_expiry_date()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.actual_delivery_date IS NOT NULL AND NEW.return_window_days IS NOT NULL THEN
        NEW.return_expiry_date := NEW.actual_delivery_date + (NEW.return_window_days || ' days')::INTERVAL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_expiry
    BEFORE INSERT OR UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION calculate_expiry_date();
