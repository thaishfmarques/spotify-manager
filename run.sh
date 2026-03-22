#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtualenv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "[*] Creating virtual environment..."
  virtualenv venv
fi

source venv/bin/activate

# Install/update dependencies
echo "[*] Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo ""
    echo "[!] .env file created from .env.example"
    echo "    Edit .env with your Spotify credentials before running again."
    echo ""
    exit 1
  else
    echo "[!] No .env file found. Create one with SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, etc."
    exit 1
  fi
fi

# Validate required env vars
source .env
if [ -z "$SPOTIPY_CLIENT_ID" ] || [ "$SPOTIPY_CLIENT_ID" = "your_client_id_here" ]; then
  echo "[!] SPOTIPY_CLIENT_ID not set in .env"
  exit 1
fi
if [ -z "$SPOTIPY_CLIENT_SECRET" ] || [ "$SPOTIPY_CLIENT_SECRET" = "your_client_secret_here" ]; then
  echo "[!] SPOTIPY_CLIENT_SECRET not set in .env"
  exit 1
fi

mkdir -p flask_session

echo "[*] Starting Spotify Manager at http://localhost:5000"
python run.py
