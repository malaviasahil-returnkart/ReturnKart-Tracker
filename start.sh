#!/bin/bash
# RETURNKART.IN — PROCESS STARTER
# Nix note: pip cannot write to /nix/store. All deps go into .venv instead.
# The direct Python path bypasses the Nix shim selector.
PYTHON=/nix/store/hg8z7jqs9pwg114dh6s34iqrv5aswmrw-python3-3.10.14/bin/python3.10

echo "🐍 Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
  $PYTHON -m venv .venv
  echo "   venv created."
fi
source .venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt -q

echo "🎨 Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..

echo "⚡ Launching backend + frontend..."
python backend/main.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

cd frontend && npm run dev
