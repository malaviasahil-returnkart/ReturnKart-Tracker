-- RETURNKART.IN — email_tokens table migration
-- Run this in Supabase SQL Editor: supabase.com → Your Project → SQL Editor
--
-- This table stores credentials for all non-Gmail email providers:
-- Yahoo, Outlook, Rediffmail, iCloud, Zoho, AOL, etc.
-- For IMAP providers, access_token stores the app password (encrypted at rest by Supabase).
-- For OAuth providers (Outlook), access_token + refresh_token store OAuth tokens.

CREATE TABLE IF NOT EXISTS email_tokens (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider         TEXT NOT NULL,          -- 'yahoo', 'outlook', 'rediff', 'icloud', etc.
    provider_label   TEXT,                   -- Display name e.g. 'Yahoo Mail'
    email_address    TEXT,                   -- The user's email address for this provider
    access_token     TEXT NOT NULL,          -- OAuth access token OR IMAP app password
    refresh_token    TEXT,                   -- OAuth refresh token (null for IMAP)
    token_expiry     TIMESTAMPTZ,            -- OAuth token expiry (null for IMAP)
    imap_host        TEXT,                   -- IMAP server host (IMAP providers only)
    last_synced_at   TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, provider)               -- One account per provider per user
);

-- Row-Level Security: users can only see their own tokens
ALTER TABLE email_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own email tokens"
    ON email_tokens
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Index for fast lookup by user
CREATE INDEX IF NOT EXISTS idx_email_tokens_user_id ON email_tokens(user_id);

COMMENT ON TABLE email_tokens IS
    'Stores email credentials for non-Gmail providers. '
    'access_token holds OAuth token OR IMAP app password. '
    'Encrypted at rest by Supabase.';
