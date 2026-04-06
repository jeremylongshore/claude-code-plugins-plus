---
name: xstatus
description: Show X account status, credit balance, and active monitors
user-invocable: true
argument-hint: "[username]"
allowed-tools: "Bash(curl:*), WebFetch"
---

Check the current X account status, credit balance, active monitors, and webhook configurations.

1. Fetch account info: `GET /x/account`
2. Fetch credit balance: `GET /credits`
3. Fetch active monitors: `GET /monitors`
4. Display a summary table with account details, remaining credits, and monitor count
