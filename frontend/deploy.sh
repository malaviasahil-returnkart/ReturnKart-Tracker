#!/bin/bash
set -e

echo "[1/3] Building frontend..."
cd /home/runner/workspace/frontend
npm install --silent
npm run build
echo "Frontend built successfully."

echo "[2/3] Verifying dist..."
ls /home/runner/workspace/frontend/dist/

echo "[3/3] Starting backend..."
cd /home/runner/workspace
exec .venv/bin/python backend/main.py
