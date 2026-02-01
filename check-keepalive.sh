#!/bin/bash
# Check if keepAlive container survived
# Run this after 10+ minutes of inactivity

JOB_ID="r9c5fa1euxrt"
echo "Checking job $JOB_ID at $(date)"
echo "---"

# Check if marker file exists via debug endpoint
RESULT=$(curl -s "https://vmux.sh/jobs/$JOB_ID/debug" \
  -H "Authorization: Bearer $(cat ~/.vmux/token)")

echo "$RESULT" | jq .

# Also try direct exec
echo "---"
echo "Checking marker file..."
vmux logs $JOB_ID 2>&1 | tail -5
