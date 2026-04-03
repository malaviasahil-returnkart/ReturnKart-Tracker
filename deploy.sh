#!/bin/bash
# RETURNKART.IN — DEPLOYMENT SCRIPT
# Runs every time Replit deploys.
# Safe to run even if frontend isn't built or npm isn't available.

set -e  # Exit on error

echo "=== ReturnKart Deploy ==="

# ── Step 1: Install/update Python dependencies ─────────────────────────────
echo "[1/3] Installing Python dependencies..."
.venv/bin/pip install -q -r backend/requirements.txt
echo "Dependencies OK."

# ── Step 2: Build frontend (only if npm is available) ──────────────────────
echo "[2/3] Checking frontend..."
if command -v npm &> /dev/null; then
    echo "npm found — building frontend..."
    cd /home/runner/workspace/frontend
    npm install --silent
    npm run build
    cd /home/runner/workspace
    echo "Frontend built."
elif [ -d "/home/runner/workspace/frontend/dist" ]; then
    echo "npm not available but frontend/dist exists — using existing build."
else
    echo "npm not available and no dist found — backend-only mode."
    echo "Frontend will show API-only message. Build frontend locally and redeploy."
fi

# ── Step 3: Start backend ───────────────────────────────────────────────────
echo "[3/3] Starting backend..."
cd /home/runner/workspace
exec .venv/bin/python backend/main.py
