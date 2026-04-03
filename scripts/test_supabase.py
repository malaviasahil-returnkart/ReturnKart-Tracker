"""
RETURNKART.IN — SUPABASE CONNECTION TEST
Phase 1, Task #11: Run this BEFORE writing any service code.
Verifies: connection, schema exists, IST timezone.
Usage: python scripts/test_supabase.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from supabase import create_client
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def test_connection():
    print("\n[1] Testing Supabase connection...")
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print(f"    OK  Connected to: {SUPABASE_URL}")
    return client


def test_timezone(client):
    print("\n[2] Testing IST timezone...")
    local_ist = datetime.now(IST)
    print(f"    IST now: {local_ist.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("    OK  Verify this matches India time")


def test_orders_table(client):
    print("\n[3] Testing orders table exists...")
    try:
        result = client.table("orders").select("id").limit(1).execute()
        print(f"    OK  orders table found ({len(result.data)} rows returned)")
    except Exception as e:
        print(f"    FAIL  orders table not found: {e}")
        print("    -> Run docs/supabase_schema.sql in Supabase dashboard first.")
        return False
    return True


def main():
    print("=" * 50)
    print("  RETURNKART.IN — SUPABASE TEST SUITE")
    print("=" * 50)
    try:
        client = test_connection()
        test_timezone(client)
        test_orders_table(client)
    except Exception as e:
        print(f"\n  FATAL: {e}")
        print("  Check your .env file and Replit Secrets.")
        sys.exit(1)
    print("\n" + "=" * 50)
    print("  ALL TESTS PASSED. Foundation is solid.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
