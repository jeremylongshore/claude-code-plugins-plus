# Apify Pricing Model — Reference

Apify charges across three dimensions: compute units (CU), proxy traffic (GB), and
storage. Understand all three before tuning — reducing memory helps CU but does
nothing for a residential-proxy bill.

## Compute Units (CU)

One CU = 1 GB of memory running for 1 hour.

```
CU = (Memory in GB) x (Duration in hours)

Example: 2048 MB (2 GB) running for 30 minutes = 2 x 0.5 = 1 CU
```

| Plan | CU Price | Included CUs |
|------|----------|-------------|
| Free | N/A | Limited trial |
| Starter | $0.30/CU | Varies by plan |
| Scale | $0.25/CU | Volume discounts |
| Enterprise | Custom | Negotiated |

CU cost scales with **both** memory allocation and wall-clock duration, which is why
the two biggest levers are Step 2 (reduce memory) and Step 3 (shorten crawls).

## Proxy Costs

| Proxy Type | Cost | Use Case |
|-----------|------|----------|
| Datacenter | Included in plan | Non-blocking sites |
| Residential | ~$12/GB | Sites that block datacenters |
| Google SERP | ~$3.50/1000 queries | Google search results |

Residential bandwidth is the most common source of surprise bills. Block images,
fonts, and CSS (Step 4) and only route through residential proxies when a site
actually blocks datacenter IPs.

## Storage

Named datasets and KV stores persist indefinitely but count against storage quota.
Unnamed (default run) storage expires after 7 days — prefer unnamed storage for
throwaway runs so it self-cleans.
