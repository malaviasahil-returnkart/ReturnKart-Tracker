-- Run this in your Supabase SQL editor to create the orders table

CREATE TABLE IF NOT EXISTS orders (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  order_id TEXT UNIQUE NOT NULL,
  platform TEXT NOT NULL,
  product_name TEXT NOT NULL,
  product_image TEXT,
  order_date TIMESTAMPTZ NOT NULL,
  delivery_date TIMESTAMPTZ,
  return_window_days INTEGER DEFAULT 10,
  return_deadline TIMESTAMPTZ,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expiring_soon', 'expired', 'returned', 'return_initiated')),
  price NUMERIC,
  currency TEXT DEFAULT 'INR',
  email_id TEXT,
  user_email TEXT,
  raw_email_snippet TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast queries
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_platform ON orders(platform);
CREATE INDEX IF NOT EXISTS idx_orders_return_deadline ON orders(return_deadline);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_orders_updated_at
  BEFORE UPDATE ON orders
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
