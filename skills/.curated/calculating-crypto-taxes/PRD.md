# PRD: Crypto Tax Calculator

## Summary

**One-liner**: Calculate cryptocurrency tax obligations with cost basis tracking, capital gains computation, and jurisdiction-aware reporting.

**Domain**: Cryptocurrency / Tax Compliance
**Users**: Individual Traders, Tax Professionals, Accountants

## Problem Statement

Cryptocurrency tax compliance is complex due to:

- Multiple taxable event types (trades, staking, airdrops, DeFi yields)
- Various cost basis methods (FIFO, LIFO, HIFO, specific ID)
- Short-term vs long-term capital gains distinctions
- Transaction data scattered across multiple exchanges/wallets
- Jurisdiction-specific rules varying by country

Users need a tool that parses transaction history, calculates cost basis accurately, identifies taxable events, and generates tax-ready reports.

## User Personas

### Persona 1: Individual Trader (Alex)

- **Profile**: Active crypto trader with 100+ transactions/year across 3-5 exchanges
- **Pain Points**: Manual tracking is error-prone, multiple exchange exports, uncertain about DeFi taxation
- **Goals**: Accurate tax calculations, minimize tax liability legally, generate Form 8949

### Persona 2: Tax Professional (Morgan)

- **Profile**: CPA with multiple crypto clients
- **Pain Points**: Each client uses different exchanges/wallets, needs audit-ready documentation
- **Goals**: Batch processing, clear audit trail, jurisdiction flexibility

### Persona 3: DeFi User (Jordan)

- **Profile**: Yield farmer with staking, liquidity provision, token swaps
- **Pain Points**: Complex DeFi transactions, unclear tax treatment, multiple protocols
- **Goals**: Accurate categorization of DeFi events, cost basis for LP tokens

## User Stories

### US-1: Import Transaction History (Critical)

**As a** trader
**I want to** import my transaction history from exchange CSV exports
**So that** I can calculate taxes without manual entry

**Acceptance Criteria**:

- Supports Coinbase, Binance, Kraken CSV formats
- Handles generic CSV with configurable column mapping
- Validates required fields (date, type, asset, quantity, price)
- Reports import errors with line numbers

### US-2: Calculate Cost Basis (Critical)

**As a** trader
**I want to** calculate cost basis using my preferred method
**So that** I can optimize my tax liability legally

**Acceptance Criteria**:

- Supports FIFO, LIFO, HIFO, specific identification
- Tracks lot-level cost basis
- Handles partial disposals correctly
- Shows comparison across methods

### US-3: Generate Tax Report (Critical)

**As a** trader
**I want to** generate a tax report in Form 8949 format
**So that** I can file my taxes or give to my accountant

**Acceptance Criteria**:

- Separates short-term and long-term gains
- Calculates total gains/losses per category
- Outputs CSV compatible with tax software
- Includes summary totals

### US-4: Identify Taxable Events (High)

**As a** DeFi user
**I want to** identify all taxable events including staking rewards
**So that** I don't miss reportable income

**Acceptance Criteria**:

- Flags trades, swaps, sells as disposals
- Identifies staking/yield as income at fair market value
- Detects airdrops as income
- Marks transfers (non-taxable) separately

### US-5: Multi-Year Analysis (Medium)

**As a** tax professional
**I want to** analyze multiple tax years
**So that** I can handle amended returns or multi-year audits

**Acceptance Criteria**:

- Filter transactions by tax year
- Carry forward cost basis across years
- Generate year-over-year comparison
- Track wash sale implications

## Functional Requirements

### REQ-1: Transaction Import

- Parse CSV exports from major exchanges (Coinbase, Binance, Kraken, Gemini)
- Support generic CSV with column mapping configuration
- Handle transaction types: buy, sell, trade, transfer, deposit, withdrawal, staking, airdrop
- Validate and normalize data (timestamps, symbols, quantities)

### REQ-2: Cost Basis Calculation

- Implement FIFO (First In First Out) - IRS default
- Implement LIFO (Last In First Out)
- Implement HIFO (Highest In First Out) - minimize gains
- Implement Specific Identification (manual lot selection)
- Track acquisition date and cost per lot
- Handle fees (add to cost basis on buy, reduce proceeds on sell)

### REQ-3: Gains/Losses Calculation

- Calculate realized gains/losses per disposal
- Determine holding period (< 1 year = short-term, >= 1 year = long-term)
- Apply wash sale rules where applicable
- Sum by category (short-term gains, short-term losses, long-term gains, long-term losses)

### REQ-4: Income Recognition

- Fair market value lookup for staking rewards at receipt time
- Airdrop valuation at receipt time
- Mining/yield income categorization
- DeFi reward tracking

### REQ-5: Report Generation

- Form 8949 format (Date Acquired, Date Sold, Proceeds, Cost Basis, Gain/Loss)
- Summary by category
- Export to CSV for tax software import
- JSON output for programmatic use

## API Integrations

- **CoinGecko Historical API**: Historical prices for cost basis and FMV
- **Local CSV Import**: Exchange export files (no API needed)

## Non-Goals

- Real-time portfolio tracking (see crypto-portfolio-tracker)
- Exchange API integration for automatic import (privacy/security)
- Tax filing submission (generates reports for manual/software filing)
- Legal tax advice (informational tool only)

## Success Metrics

- Skill activates on tax-related trigger phrases
- Imports common exchange CSV formats without errors
- Calculates gains/losses matching manual verification
- Generates valid Form 8949 format output

## Technical Constraints

- Python 3.8+ with standard library (csv, json, datetime)
- Optional: requests for historical price lookups
- No exchange API credentials stored
- Works offline for basic calculations

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Incorrect tax calculations | Medium | High | Extensive validation, disclaimers |
| Missing taxable events | Medium | High | Clear documentation of supported events |
| Historical price API unavailable | Low | Medium | Fallback to manual price entry |
| Jurisdiction mismatch | Medium | Medium | US-focused with clear documentation |

## Examples

### Example 1: Basic Tax Report

```bash
python tax_calculator.py --transactions trades.csv --method fifo --year 2025 --output tax_report.csv
```

### Example 2: Cost Basis Comparison

```bash
python tax_calculator.py --transactions trades.csv --compare-methods
```

### Example 3: DeFi Income Report

```bash
python tax_calculator.py --transactions all_transactions.csv --income-report
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-14 | Jeremy Longshore | Initial PRD |
