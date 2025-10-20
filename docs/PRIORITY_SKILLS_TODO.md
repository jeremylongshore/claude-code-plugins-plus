# Priority Skills Generation TODO

**Date:** 2025-10-20
**Status:** 75 plugins remaining

---

## Immediate Priority (Before Release)

### Critical Fix
- [ ] **overnight-dev** - Fix YAML frontmatter (remove markdown code fence)

---

## High Priority (Post-Release Wave 1)

### Near-Complete Categories (1-2 plugins each)
- [ ] **devops/fairdb-operations-kit** (devops: 28/29)
- [ ] **performance/database-query-profiler** (performance: 24/25)
- [ ] **examples/hello-world** (example: 2/3)

### Productivity Category (4 plugins, 20% coverage)
- [ ] **ai-commit-gen**
- [ ] **domain-memory-agent**
- [ ] **formatter**
- [ ] **travel-assistant**

---

## Medium Priority (Post-Release Wave 2)

### API Development (25 plugins, 0% coverage)

#### Core API Tools (Priority 1)
- [ ] **rest-api-generator**
- [ ] **api-documentation-generator**
- [ ] **api-security-scanner**
- [ ] **api-test-automation**
- [ ] **api-schema-validator**

#### GraphQL & Advanced (Priority 2)
- [ ] **graphql-server-builder**
- [ ] **grpc-service-generator**
- [ ] **websocket-server-builder**
- [ ] **api-gateway-builder**
- [ ] **api-load-tester**

#### API Management (Priority 3)
- [ ] **api-rate-limiter**
- [ ] **api-throttling-manager**
- [ ] **api-versioning-manager**
- [ ] **api-monitoring-dashboard**
- [ ] **api-authentication-builder**

#### API Development Tools (Priority 4)
- [ ] **api-mock-server**
- [ ] **api-contract-generator**
- [ ] **api-migration-tool**
- [ ] **api-error-handler**
- [ ] **api-event-emitter**
- [ ] **api-batch-processor**
- [ ] **api-cache-manager**
- [ ] **api-request-logger**
- [ ] **api-response-validator**
- [ ] **api-sdk-generator**
- [ ] **webhook-handler-creator**

---

## Low Priority (Post-Release Wave 3+)

### Crypto Category (25 plugins, 0% coverage)

#### Trading & Market Analysis (Priority 1)
- [ ] **market-price-tracker**
- [ ] **trading-strategy-backtester**
- [ ] **crypto-signal-generator**
- [ ] **market-sentiment-analyzer**
- [ ] **arbitrage-opportunity-finder**

#### Portfolio & Analytics (Priority 2)
- [ ] **crypto-portfolio-tracker**
- [ ] **wallet-portfolio-tracker**
- [ ] **on-chain-analytics**
- [ ] **whale-alert-monitor**
- [ ] **crypto-tax-calculator**

#### DeFi Tools (Priority 3)
- [ ] **defi-yield-optimizer**
- [ ] **dex-aggregator-router**
- [ ] **liquidity-pool-analyzer**
- [ ] **staking-rewards-optimizer**
- [ ] **flash-loan-simulator**

#### Blockchain Infrastructure (Priority 4)
- [ ] **blockchain-explorer-cli**
- [ ] **cross-chain-bridge-monitor**
- [ ] **gas-fee-optimizer**
- [ ] **mempool-analyzer**

#### Advanced Trading (Priority 5)
- [ ] **crypto-derivatives-tracker**
- [ ] **options-flow-analyzer**
- [ ] **market-movers-scanner**
- [ ] **token-launch-tracker**
- [ ] **nft-rarity-analyzer**
- [ ] **crypto-news-aggregator**

### AI Agency Category (6 plugins, 0% coverage)
- [ ] **sow-generator**
- [ ] **roi-calculator**
- [ ] **discovery-questionnaire**
- [ ] **n8n-workflow-designer**
- [ ] **zapier-zap-builder**
- [ ] **make-scenario-builder**

### Single Plugin Categories
- [ ] **automation/workflow-orchestrator**
- [ ] **code-quality/project-health-auditor**
- [ ] **debugging/conversational-api-debugger**
- [ ] **design/design-to-code**
- [ ] **finance/openbb-terminal**
- [ ] **fullstack/fullstack-starter-pack**
- [ ] **packages/creator-studio-pack**

### Unknown Category (6 plugins)
- [ ] **ai-experiment-logger**
- [ ] **calendar-to-workflow**
- [ ] **fairdb-ops-manager**
- [ ] **file-to-code**
- [ ] **research-to-deploy**
- [ ] **search-to-slack**

---

## Execution Plan

### Release Preparation
1. Fix overnight-dev frontmatter
2. Validate all YAML with `python3 scripts/check-frontmatter.py`
3. Create release with 68.1% coverage

### Post-Release Roadmap

**Week 1-2:** High Priority (8 plugins)
- Complete near-finished categories
- Add productivity tools
- **Target:** 71% coverage (168/235)

**Week 3-4:** API Development Wave 1 (10 plugins)
- Core API tools and security
- **Target:** 75% coverage (178/235)

**Week 5-6:** API Development Wave 2 (15 plugins)
- Advanced API tools
- **Target:** 82% coverage (193/235)

**Week 7-8:** Crypto Wave 1 (15 plugins)
- Trading and DeFi essentials
- **Target:** 88% coverage (208/235)

**Week 9-10:** Final Cleanup (remaining plugins)
- AI Agency, single plugins, unknowns
- **Target:** 95%+ coverage (223+/235)

---

## Automation Commands

### Generate next plugin skill
```bash
cd /home/jeremy/000-projects/claude-code-plugins
./scripts/next-skill.sh
```

### Batch generate (with Vertex AI)
```bash
python3 scripts/vertex-skills-generator-safe.py
```

### Validate after generation
```bash
python3 scripts/check-frontmatter.py
./scripts/validate-all.sh
```

---

**Total:** 75 plugins to complete
**Current:** 160/235 (68.1%)
**Goal:** 223/235 (95%+)
