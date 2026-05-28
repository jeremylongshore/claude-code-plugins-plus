---
name: agentpay
description: "AgentPay — agent registry for direct peer-to-peer USDC payments on Base. Zero fees, no custody."
---

# AgentPay — Agent Registry for Direct USDC Payments

AgentPay is a **registry** that maps agent IDs to their Base wallet addresses. It does NOT hold funds or charge fees. Every payment is a direct USDC transfer.

## Endpoints
- POST /register — register by Base address
- GET /resolve/{agent_id} — get wallet address
- GET /agents — list all agents

## Comparison
| Feature | AgentPay | Payment processor |
|---------|----------|-------------------|
| Custody | None | They hold your money |
| Fees | Zero | 0.5-3% |

## Deploy
```
git clone https://github.com/M1mino/agentpay
cd agentpay && pip install -r requirements.txt && python server.py
```

GitHub: https://github.com/M1mino/agentpay
