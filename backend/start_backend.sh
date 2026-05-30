#!/bin/bash
# Start Blend Search Backend with proper environment
set -e

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔵 Starting Blend Search Backend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f "../../blend/venv/bin/activate" ]; then
  source ../../blend/venv/bin/activate
else
  echo "❌ No Python virtual environment found."
  exit 1
fi

# Run Blend in embedded/offline-friendly mode so local startup does not fail
# on external engine network probes.
export BLEND_EMBEDDED_BACKEND=1
BLEND_HOST="${BLEND_HOST:-127.0.0.1}"
BLEND_PORT="${BLEND_PORT:-8081}"
export PORT="${PORT:-$BLEND_PORT}"
if [ -n "${BLEND_SECRET_KEY:-}" ] && [ -z "${MARKANM_SECRET:-}" ]; then
  export MARKANM_SECRET="$BLEND_SECRET_KEY"
fi

# Start the backend
echo "📡 Backend starting on http://${BLEND_HOST}:${PORT}"
python app.py
