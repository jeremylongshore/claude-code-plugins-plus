# Flash Loan Simulator - Error Handling Reference

## RPC Connection Errors

### ERR-001: RPC Connection Timeout
```
Error: Request timed out after 30000ms
```

**Cause:** Network latency or overloaded RPC endpoint.

**Solution:**
1. Switch to a different RPC endpoint:
   ```yaml
   rpc_endpoints:
     ethereum: "https://rpc.ankr.com/eth"      # Free, no signup
     backup: "https://eth.llamarpc.com"        # Alternative
   ```
2. Increase timeout in settings.yaml
3. Check network connectivity

### ERR-002: RPC Rate Limited
```
Error: 429 Too Many Requests
```

**Cause:** Free RPC tier limits exceeded.

**Solution:**
1. Add delay between requests:
   ```python
   import time
   time.sleep(0.5)  # 500ms between calls
   ```
2. Switch to a different free RPC (rotate between Ankr, Chainstack, Llamarpc)
3. Use a private RPC for production (Alchemy, Chainstack, Infura, or Quicknode)

---

## Simulation Errors

### ERR-010: Insufficient Liquidity
```
Error: Loan amount exceeds available liquidity
Provider: Aave V3
Available: 50,000 ETH
Requested: 100,000 ETH
```

**Cause:** Flash loan amount exceeds pool depth.

**Solution:**
1. Reduce loan amount
2. Split across multiple providers
3. Use a different asset with more liquidity

### ERR-011: Unsupported Asset
```
Error: Asset 'SHIB' not supported by provider 'dYdX'
```

**Cause:** Provider doesn't support the requested token.

**Solution:**
1. Check provider's supported assets:
   ```bash
   python flash_simulator.py compare SHIB 1000
   ```
2. Use a different provider (Aave V3 supports more assets)
3. Swap to a supported intermediary token

### ERR-012: Chain Mismatch
```
Error: Provider 'dYdX' not available on chain 'polygon'
```

**Cause:** Provider only operates on specific chains.

**Solution:**
1. Check provider chains:
   - dYdX: Ethereum only
   - Aave V3: Ethereum, Polygon, Arbitrum, Optimism, Avalanche
   - Balancer: Ethereum, Polygon, Arbitrum
2. Switch to a multi-chain provider

---

## Strategy Errors

### ERR-020: No Profitable Route
```
Error: All simulated routes result in loss
Best route: -0.05 ETH (-$125.00)
```

**Cause:** Current market conditions don't support the arbitrage.

**Solution:**
1. Wait for better price differences
2. Try different token pairs
3. Consider smaller trade sizes (less slippage)
4. Check for stale price data

### ERR-021: Negative Profit Margin
```
Warning: Strategy unprofitable after costs
Gross profit: +0.10 ETH
Total costs: -0.15 ETH
Net profit: -0.05 ETH
```

**Cause:** Costs (gas + fees) exceed the arbitrage opportunity.

**Solution:**
1. Use a zero-fee provider (dYdX)
2. Wait for lower gas prices
3. Increase trade size to improve margin ratio
4. Find larger price discrepancies

### ERR-022: High MEV Competition
```
Warning: MEV competition score 85/100
This pair has high bot activity
```

**Cause:** ETH/USDC and similar pairs are heavily competed.

**Solution:**
1. Use Flashbots Protect for private transactions
2. Try less-competitive pairs
3. Consider smaller, faster trades
4. Implement MEV protection in production

---

## Risk Assessment Errors

### ERR-030: Critical Risk Score
```
Warning: Risk score 78/100 (CRITICAL)
Viability: NO-GO
```

**Cause:** Multiple risk factors are elevated.

**Solution:**
1. Review individual risk factors:
   ```bash
   python flash_simulator.py arbitrage ETH USDC 100 --risk-analysis
   ```
2. Address the highest-scoring factors
3. Consider a different strategy or timing

### ERR-031: Protocol Risk Warning
```
Warning: Using unaudited protocol 'NewDEX'
Protocol risk score: 80/100
```

**Cause:** Less-established protocol increases smart contract risk.

**Solution:**
1. Verify protocol audits before using
2. Stick to well-audited protocols (Aave, Uniswap, Balancer)
3. Limit exposure to newer protocols

---

## Gas Estimation Errors

### ERR-040: Gas Price Spike
```
Warning: Current gas price 150 gwei (normal: 30 gwei)
Strategy breakeven gas: 45 gwei
```

**Cause:** Network congestion causing unprofitable gas costs.

**Solution:**
1. Wait for gas prices to normalize
2. Use gas oracles to estimate future prices:
   ```python
   # Check if current gas is above breakeven
   if current_gas > breakeven_gas:
       print("Wait for lower gas prices")
   ```
3. Set gas price limits in execution scripts

### ERR-041: Gas Estimation Failed
```
Error: Could not estimate gas for transaction
```

**Cause:** Transaction would revert on-chain.

**Solution:**
1. Check token approvals
2. Verify sufficient balances
3. Test on forked mainnet first
4. Review transaction parameters

---

## Input Validation Errors

### ERR-050: Invalid Amount
```
Error: Invalid amount 'abc' - must be numeric
```

**Solution:**
```bash
# Correct usage
python flash_simulator.py arbitrage ETH USDC 100    # Integer
python flash_simulator.py arbitrage ETH USDC 100.5  # Decimal
```

### ERR-051: Invalid Token Symbol
```
Error: Unknown token 'ETHEREUM' - did you mean 'ETH'?
```

**Solution:**
Use standard token symbols: ETH, WETH, USDC, USDT, DAI, WBTC

### ERR-052: Invalid Provider
```
Error: Unknown provider 'aavev3' - valid options: aave, dydx, balancer, uniswap
```

**Solution:**
```bash
# Use lowercase provider names
python flash_simulator.py arbitrage ETH USDC 100 --provider aave
```

---

## Output/Format Errors

### ERR-060: JSON Export Failed
```
Error: Cannot serialize Decimal to JSON
```

**Cause:** Custom Decimal types not handled.

**Solution:** The simulator handles this automatically. If using custom code:
```python
from formatters import DecimalEncoder
import json
json.dumps(data, cls=DecimalEncoder)
```

---

## Recovery Procedures

### Complete Reset
If simulator is in an inconsistent state:
```bash
# Clear any cached data
rm -rf ~/.cache/flash-simulator/

# Reinstall dependencies
pip install --upgrade web3 httpx
```

### Verify RPC Connectivity
```bash
# Test RPC endpoint
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  https://rpc.ankr.com/eth
```

### Test Simulation Engine
```bash
# Run built-in demo
python strategy_engine.py
python profit_calculator.py
python risk_assessor.py
```

---

## Getting Help

1. Check script help: `python flash_simulator.py --help`
2. Review examples: `references/examples.md`
3. Test on mainnet fork before real execution
4. Start with small amounts on testnet

**Remember:** Flash loans are complex DeFi operations. Always test thoroughly and understand the risks before any real execution.
