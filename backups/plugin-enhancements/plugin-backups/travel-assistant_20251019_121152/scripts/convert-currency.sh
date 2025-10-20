#!/bin/bash
# Convert currency using ExchangeRate API
# Usage: ./convert-currency.sh "FROM" "TO" "AMOUNT"

FROM="${1:-USD}"
TO="${2:-EUR}"
AMOUNT="${3:-1}"

# Free tier ExchangeRate API (1500 calls/month)
RATE=$(curl -s "https://api.exchangerate-api.com/v4/latest/${FROM}" 2>/dev/null | grep -o "\"${TO}\":[0-9.]*" | cut -d: -f2)

if [ -n "$RATE" ]; then
    RESULT=$(echo "$AMOUNT * $RATE" | bc -l)
    echo "{\"from\":\"${FROM}\",\"to\":\"${TO}\",\"amount\":${AMOUNT},\"rate\":${RATE},\"result\":${RESULT}}"
else
    echo '{"error":"API unavailable"}'
fi
