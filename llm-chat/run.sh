#!/bin/bash
# Run the full LLM chat stack: backend on vmux + frontend locally
set -e

cd "$(dirname "$0")"

# Install frontend deps if needed
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

# Start backend on vmux (detached)
echo "Starting backend on vmux..."
BACKEND_OUTPUT=$(vmux run --provider modal --gpu A10G -dp 8000 -d python backend.py 2>&1)
echo "$BACKEND_OUTPUT"

# Extract preview URL from output
PREVIEW_URL=$(echo "$BACKEND_OUTPUT" | grep -oE 'https://[^ ]+\.vmux\.(dev|io)[^ ]*' | head -1)

if [ -z "$PREVIEW_URL" ]; then
  echo "Could not extract preview URL. Check vmux output above."
  echo "You can manually set: export NEXT_PUBLIC_BACKEND_URL=<your-url>"
else
  echo ""
  echo "Backend URL: $PREVIEW_URL"
  export NEXT_PUBLIC_BACKEND_URL="$PREVIEW_URL"
fi

echo ""
echo "Starting frontend..."
echo "Open http://localhost:3000"
echo ""

# Start frontend
npm run dev
