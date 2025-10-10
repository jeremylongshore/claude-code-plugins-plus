#!/bin/bash
# Example hook script

# Read hook data from stdin
data=$(cat)

# Process the data
echo "Hook triggered!"
echo "$data" | jq '.'
