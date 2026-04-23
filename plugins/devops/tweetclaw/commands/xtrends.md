---
name: xtrends
description: Show trending topics on X and curated tech news from 7 sources
user-invocable: true
argument-hint: "[category]"
allowed-tools: "Bash(curl:*), WebFetch"
---

Fetch trending topics from X and curated news from the Xquik radar (7 sources).

1. Fetch X trending topics: `GET /trends`
2. Fetch curated radar: `GET /radar`
3. Display trending topics sorted by tweet volume
4. Display top radar stories grouped by source
