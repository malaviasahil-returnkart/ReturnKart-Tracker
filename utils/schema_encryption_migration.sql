-- ═══════════════════════════════════════════════════════════════
-- ReturnKart — Encryption Support Migration
-- Run AFTER the base schema.sql
--
-- This adds _hash columns alongside encrypted fields so the app
-- can search/match records without decrypting everything.
-- ═══════════════════════════════════════════════════════════════

-- ───────────────────────────
-- Add hash columns to orders table
-- ───────────────────────────
-- The original columns (order_id_external, tracking_id, email_id)
-- now store ENCRYPTED values. These _hash columns store SHA-256
-- hashes for lookups and deduplication.

ALTER TABLE orders
  ADD COLUMN IF NOT EXISTS order_id_external_hash TEXT,
  ADD COLUMN IF NOT EXISTS tracking_id_hash TEXT,
  ADD COLUMN IF NOT EXISTS email_id_hash TEXT;

-- Index the hash columns for fast lookups
CREATE INDEX IF NOT EXISTS idx_orders_order_hash ON orders(order_id_external_hash);
CREATE INDEX IF NOT EXISTS idx_orders_tracking_hash ON orders(tracking_id_hash);
CREATE INDEX IF NOT EXISTS idx_orders_email_hash ON orders(email_id_hash);

-- Update unique constraint to use hash instead of raw value
-- (Drop old constraint first if it exists)
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_user_id_order_id_external_brand_slug_key;
ALTER TABLE orders ADD CONSTRAINT orders_user_hash_brand_unique
  UNIQUE(user_id, order_id_external_hash, brand_slug);

-- ───────────────────────────
-- Add encryption_salt to users table
-- ───────────────────────────
-- Each user gets a unique salt for key derivation.
-- This is NOT secret — it just ensures two users with the
-- same password get different encryption keys.

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS encryption_salt TEXT DEFAULT gen_random_uuid()::TEXT;

-- ───────────────────────────
-- Add key_verification_hash to users table
-- ───────────────────────────
-- On first encryption setup, we encrypt a known string and store it.
-- On subsequent logins, we try to decrypt it to verify the key is correct
-- BEFORE attempting to decrypt actual data (prevents corruption).

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS key_verification_token TEXT;

-- ───────────────────────────
-- DPDP Compliance: Data Retention Automation
-- ───────────────────────────
-- Automatically flag expired data for deletion.
-- DPDP requires data to be deleted when purpose is fulfilled
-- or when the data_expiry_date is reached.

CREATE OR REPLACE FUNCTION check_data_expiry()
RETURNS void AS $$
BEGIN
  -- Flag users whose data has expired
  UPDATE users
  SET anonymization_status = true
  WHERE data_expiry_date < now()
    AND anonymization_status = false;

  -- Log the action for DPDP audit trail
  INSERT INTO dpdp_audit_log (action, details, executed_at)
  VALUES (
    'auto_anonymization',
    'Flagged ' || (
      SELECT count(*) FROM users
      WHERE data_expiry_date < now() AND anonymization_status = true
    ) || ' users for anonymization due to data expiry',
    now()
  );
END;
$$ LANGUAGE plpgsql;

-- ───────────────────────────
-- DPDP Audit Log table
-- ───────────────────────────
-- Every data operation that affects compliance is logged here.
-- This table is NEVER encrypted — it must be readable by
-- the Data Protection Board of India during audits.

CREATE TABLE IF NOT EXISTS dpdp_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  action TEXT NOT NULL,
  user_id UUID,
  details TEXT,
  ip_address TEXT,
  executed_at TIMESTAMPTZ DEFAULT now()
);

-- No RLS on audit log — must be accessible for compliance audits
-- Only service_role key can write to it (not anon/user keys)

CREATE INDEX IF NOT EXISTS idx_audit_action ON dpdp_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_date ON dpdp_audit_log(executed_at);

-- ───────────────────────────
-- DPDP Consent Changes Log
-- ───────────────────────────
-- Every time a user changes their consent preferences, log it.
-- Required for demonstrating lawful basis of processing.

CREATE TABLE IF NOT EXISTS consent_changes_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  previous_purposes TEXT[],
  new_purposes TEXT[],
  action TEXT NOT NULL CHECK (action IN ('grant', 'revoke', 'modify')),
  notice_version TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_consent_user ON consent_changes_log(user_id);

-- ───────────────────────────
-- Data Deletion Requests
-- ───────────────────────────
-- DPDP Right to Erasure: track all deletion requests and their status.

CREATE TABLE IF NOT EXISTS data_deletion_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  requested_at TIMESTAMPTZ DEFAULT now(),
  reason TEXT,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  completed_at TIMESTAMPTZ,
  crypto_shredded BOOLEAN DEFAULT false,
  rows_deleted JSONB
);

-- ───────────────────────────
-- Scheduled job: Run expiry check daily
-- ───────────────────────────
-- In Supabase, you'd use pg_cron or a Supabase Edge Function
-- scheduled via cron to call check_data_expiry() daily.
--
-- Example pg_cron (if available):
-- SELECT cron.schedule('check-data-expiry', '0 2 * * *', 'SELECT check_data_expiry()');
--
-- Or create a Supabase Edge Function that runs on a schedule.
