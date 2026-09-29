#!/usr/bin/env bash
set -e

BACKEND_URL="${1:-http://localhost:8000}"

echo "=================================================="
echo " Checking JOCKY Backend Health (${BACKEND_URL}/health)"
echo "=================================================="

HTTP_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "${BACKEND_URL}/health" || true)
HTTP_BODY=$(echo "$HTTP_RESPONSE" | sed -e '$d')
HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tail -n 1 | sed -e 's/HTTP_STATUS://')

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo " Backend is healthy!"
    echo "Response: $HTTP_BODY"
    exit 0
else
    echo "❌ Health check failed with status: $HTTP_STATUS"
    echo "Response: $HTTP_BODY"
    exit 1
fi
