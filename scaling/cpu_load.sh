#!/bin/bash

URL="${1:-http://localhost:8000}/compute"
CONCURRENCY="${2:-200}"
DURATION="${3:-60s}"

# Check for hey or wrk
if command -v hey &> /dev/null; then
  echo "Using hey — hammering $URL"
  echo "Concurrency: $CONCURRENCY, Duration: $DURATION"
  echo ""
  hey -c "$CONCURRENCY" -z "$DURATION" "$URL"
elif command -v wrk &> /dev/null; then
  echo "Using wrk — hammering $URL"
  echo "Concurrency: $CONCURRENCY, Duration: $DURATION"
  echo ""
  wrk -t8 -c "$CONCURRENCY" -d "$DURATION" "$URL"
else
  echo "Neither 'hey' nor 'wrk' found. Install one:"
  echo "  brew install hey      # macOS"
  echo "  brew install wrk      # macOS"
  echo "  go install github.com/rakyll/hey@latest  # Go"
  exit 1
fi
