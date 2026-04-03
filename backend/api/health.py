"""
RETURNKART.IN — HEALTH + KEEP-ALIVE ENDPOINT

GET /api/health          — standard liveness check
GET /api/health/warmup   — called by UptimeRobot every 5 min to prevent
                           Replit cold starts. Free UptimeRobot monitors
                           at https://uptimerobot.com (no account needed
                           for a single monitor).

UptimeRobot setup (one-time, 2 min):
  1. uptimerobot.com → Add New Monitor
  2. Type: HTTP(s)
  3. URL: https://return-kart-tracker.replit.app/api/health
  4. Interval: every 5 minutes
  Done — Replit stays warm, cold starts disappear.
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter

router = APIRouter()
IST = timezone(timedelta(hours=5, minutes=30))


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "time_ist": datetime.now(IST).isoformat(),
    }


@router.get("/health/warmup")
async def warmup():
    """
    Lightweight endpoint pinged by UptimeRobot every 5 min.
    Keeps Replit deployment warm — eliminates cold start latency.
    """
    return {"status": "warm", "time_ist": datetime.now(IST).isoformat()}
