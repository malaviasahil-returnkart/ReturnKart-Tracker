"""
RETURNKART.IN — CENTRAL CONFIGURATION
The ONLY file that calls os.getenv(). All other modules import from here.
Rule: one import path for secrets = one place to fix if a key rotates.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Get a required env variable. Warns but doesn't crash if missing — lets server start."""
    value = os.getenv(key)
    if not value:
        print(f"WARNING: Missing env variable: {key}. Add it to Replit Secrets.")
        return ""
    return value


# Supabase
SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_SERVICE_KEY: str = _require("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY: str = _require("SUPABASE_ANON_KEY")

# Google OAuth (Gmail)
GOOGLE_CLIENT_ID: str = _require("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str = _require("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI: str = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "https://return-kart-tracker.replit.app/api/auth/callback"
)

# Microsoft OAuth (Outlook / Hotmail)
# Setup: portal.azure.com → App Registrations → New registration
# Redirect URI: https://return-kart-tracker.replit.app/api/email/outlook/callback
MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_REDIRECT_URI: str = os.getenv(
    "MICROSOFT_REDIRECT_URI",
    "https://return-kart-tracker.replit.app/api/email/outlook/callback"
)

# Gemini AI
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")

# WhatsApp Business API (Meta Cloud API)
WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_APP_SECRET: str = os.getenv("WHATSAPP_APP_SECRET", "")

# App — PORT is injected by Replit. NEVER hardcode.
PORT: int = int(os.getenv("PORT", "8000"))
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://return-kart-tracker.replit.app")
ENV: str = os.getenv("ENV", "development")
IS_PRODUCTION: bool = ENV == "production"
