#!/bin/bash
# Get timezone info from WorldTimeAPI (free, no key needed)
# Usage: ./get-timezone.sh "location"

LOCATION="${1:-Europe/London}"

# Free WorldTimeAPI
curl -s "https://worldtimeapi.org/api/timezone/${LOCATION}" 2>/dev/null || echo '{"error":"API unavailable"}'
