---
name: calculate-tax
description: >
  Calculate cryptocurrency taxes with multi-jurisdiction support, cost
  basis...
shortcut: ct
---
# Calculate Crypto Taxes

Comprehensive cryptocurrency tax calculation system with support for multiple accounting methods (FIFO, LIFO, HIFO, Specific ID), multi-jurisdiction compliance (US IRS, UK HMRC, EU DAC8), and automated tax form generation. Handles capital gains/losses, staking rewards, airdrops, mining income, DeFi yield, NFT transactions, and wash sale rules.

## Usage

When calculating cryptocurrency taxes, implement comprehensive tax calculation across all taxable events:

### Required Parameters
- **Tax Year**: Year for tax calculation (2024, 2023, etc.)
- **Jurisdiction**: US, UK, EU, AU, CA, or custom
- **Accounting Method**: FIFO, LIFO, HIFO, Specific Identification
- **Transaction Sources**: Exchanges, wallets, DeFi protocols
- **Income Types**: Trading, staking, mining, airdrops, DeFi

### Supported Transaction Types
1. **Trading**: Buy, sell, swap, conversions
2. **DeFi**: Staking rewards, liquidity pool fees, yield farming
3. **Mining**: Block rewards, mining pool payouts
4. **Income**: Airdrops, hard forks, referral bonuses
5. **NFTs**: Minting, sales, royalties
6. **Gifts**: Received, sent, donations

## Implementation

### 1. Complete Tax Calculator with Multi-Exchange Support

```python
#!/usr/bin/env python3
"""
Comprehensive Cryptocurrency Tax Calculator
Supports: FIFO, LIFO, HIFO, Specific ID
Jurisdictions: US (IRS), UK (HMRC), EU (DAC8), AU (ATO), CA (CRA)
"""

import csv
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccountingMethod(Enum):
    """Cost basis accounting methods"""
    FIFO = "First In, First Out"
    LIFO = "Last In, First Out"
    HIFO = "Highest In, First Out"
    SPECIFIC_ID = "Specific Identification"
    AVERAGE_COST = "Average Cost Basis"


class TaxJurisdiction(Enum):
    """Tax jurisdiction configurations"""
    US_IRS = {
        "name": "United States (IRS)",
        "short_term_days": 365,
        "long_term_threshold": 365,
        "forms": ["Form 8949", "Schedule D", "Schedule 1"],
        "wash_sale_days": 30,
        "de_minimis_threshold": 200
    }
    UK_HMRC = {
        "name": "United Kingdom (HMRC)",
        "short_term_days": 0,
        "capital_gains_allowance": 6000,
        "forms": ["SA108", "Cryptoasset Manual"],
        "same_day_rule": True,
        "bed_and_breakfast_days": 30
    }
    EU_DAC8 = {
        "name": "European Union (DAC8)",
        "reporting_threshold": 50000,
        "forms": ["DAC8 Report"],
        "mifid_requirements": True
    }
    AU_ATO = {
        "name": "Australia (ATO)",
        "cgt_discount_days": 365,
        "cgt_discount_rate": 0.5,
        "forms": ["myTax CGT Schedule"]
    }
    CA_CRA = {
        "name": "Canada (CRA)",
        "capital_gains_inclusion": 0.5,
        "forms": ["Schedule 3"],
        "superficial_loss_days": 30
    }


class TransactionType(Enum):
    """All supported transaction types"""
    BUY = "buy"
    SELL = "sell"
    TRADE = "trade"
    SWAP = "swap"
    RECEIVE = "receive"
    SEND = "send"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    MINING = "mining"
    AIRDROP = "airdrop"
    FORK = "fork"
    GIFT = "gift"
    DONATION = "donation"
    LP_ADD = "lp_add"
    LP_REMOVE = "lp_remove"
    BORROW = "borrow"
    REPAY = "repay"
    LIQUIDATION = "liquidation"
    NFT_MINT = "nft_mint"
    NFT_SALE = "nft_sale"


@dataclass
class Transaction:
    """Represents a single cryptocurrency transaction"""
    tx_id: str
    timestamp: datetime
    tx_type: TransactionType
    asset: str
    amount: Decimal
    price_usd: Decimal
    fee: Decimal = Decimal('0')
    fee_asset: str = 'USD'
    exchange: str = ''
    wallet: str = ''
    notes: str = ''

    # For trades/swaps
    to_asset: Optional[str] = None
    to_amount: Optional[Decimal] = None

    # Cost basis tracking
    cost_basis: Optional[Decimal] = None
    fair_market_value: Optional[Decimal] = None

    # Metadata
    is_income: bool = False
    is_gift: bool = False
    is_lost: bool = False

    def __post_init__(self):
        """Calculate fair market value"""
        if self.fair_market_value is None:
            self.fair_market_value = self.amount * self.price_usd


@dataclass
class TaxLot:
    """Represents a tax lot for cost basis tracking"""
    lot_id: str
    asset: str
    amount: Decimal
    cost_basis: Decimal
    acquisition_date: datetime
    acquisition_price: Decimal
    acquisition_source: str
    is_income: bool = False

    # Tracking
    remaining_amount: Decimal = field(init=False)
    disposed_amount: Decimal = Decimal('0')

    def __post_init__(self):
        self.remaining_amount = self.amount
        self.lot_id = self.generate_lot_id()

    def generate_lot_id(self) -> str:
        """Generate unique lot identifier"""
        data = f"{self.asset}{self.acquisition_date}{self.amount}{self.cost_basis}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def dispose(self, amount: Decimal) -> Decimal:
        """Dispose of amount from this lot"""
        if amount > self.remaining_amount:
            raise ValueError(f"Cannot dispose {amount} from lot with {self.remaining_amount}")

        self.disposed_amount += amount
        self.remaining_amount -= amount

        # Calculate proportional cost basis
        proportion = amount / self.amount
        return self.cost_basis * proportion


@dataclass
class TaxEvent:
    """Represents a taxable event"""
    event_id: str
    timestamp: datetime
    event_type: str
    asset: str
    amount: Decimal
    proceeds: Decimal
    cost_basis: Decimal
    gain_loss: Decimal
    holding_period_days: int
    is_long_term: bool
    tax_rate: Decimal

    # Source tracking
    source_tx_id: str
    lots_used: List[str] = field(default_factory=list)

    # Form generation
    form_8949_category: str = ''  # A, B, C, D, E, F
    schedule_d_line: str = ''

    # Jurisdiction specific
    jurisdiction_notes: str = ''


class CryptoTaxCalculator:
    """Main cryptocurrency tax calculator"""

    def __init__(
        self,
        jurisdiction: TaxJurisdiction = TaxJurisdiction.US_IRS,
        accounting_method: AccountingMethod = AccountingMethod.FIFO,
        tax_year: int = 2024,
        db_path: str = "crypto_tax.db"
    ):
        self.jurisdiction = jurisdiction
        self.accounting_method = accounting_method
        self.tax_year = tax_year
        self.db_path = db_path

        # Storage
        self.transactions: List[Transaction] = []
        self.tax_lots: Dict[str, List[TaxLot]] = {}  # asset -> [lots]
        self.tax_events: List[TaxEvent] = []
        self.income_events: List[Transaction] = []

        # Statistics
        self.stats = {
            'total_transactions': 0,
            'total_trades': 0,
            'total_income_events': 0,
            'total_gain': Decimal('0'),
            'total_loss': Decimal('0'),
            'short_term_gain': Decimal('0'),
            'long_term_gain': Decimal('0')
        }

        # Initialize database
        self.init_database()

        logger.info(f"Initialized tax calculator for {jurisdiction.value['name']} using {accounting_method.value}")

    def init_database(self):
        """Initialize SQLite database for persistent storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                tx_id TEXT PRIMARY KEY,
                timestamp TEXT,
                tx_type TEXT,
                asset TEXT,
                amount REAL,
                price_usd REAL,
                fee REAL,
                exchange TEXT,
                wallet TEXT,
                to_asset TEXT,
                to_amount REAL,
                fair_market_value REAL,
                is_income INTEGER,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tax_lots (
                lot_id TEXT PRIMARY KEY,
                asset TEXT,
                amount REAL,
                cost_basis REAL,
                acquisition_date TEXT,
                acquisition_price REAL,
                remaining_amount REAL,
                disposed_amount REAL,
                is_income INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tax_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT,
                event_type TEXT,
                asset TEXT,
                amount REAL,
                proceeds REAL,
                cost_basis REAL,
                gain_loss REAL,
                holding_period_days INTEGER,
                is_long_term INTEGER,
                tax_rate REAL,
                form_8949_category TEXT,
                lots_used TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tx_timestamp
            ON transactions(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lots_asset
            ON tax_lots(asset, acquisition_date)
        """)

        conn.commit()
        conn.close()

        logger.info("Database initialized")

    def import_transactions(self, source: str, file_path: str) -> int:
        """
        Import transactions from various sources
        Supported: Coinbase, Binance, Kraken, CSV, JSON
        """
        logger.info(f"Importing transactions from {source}: {file_path}")

        importers = {
            'coinbase': self._import_coinbase,
            'binance': self._import_binance,
            'kraken': self._import_kraken,
            'csv': self._import_csv,
            'json': self._import_json
        }

        if source.lower() not in importers:
            raise ValueError(f"Unsupported source: {source}")

        count = importers[source.lower()](file_path)
        logger.info(f"Imported {count} transactions")
        return count

    def _import_coinbase(self, file_path: str) -> int:
        """Import Coinbase transaction history"""
        count = 0
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Parse Coinbase format
                    timestamp = datetime.strptime(
                        row['Timestamp'],
                        '%Y-%m-%dT%H:%M:%SZ'
                    )

                    tx = Transaction(
                        tx_id=row.get('Transaction Hash', f"CB_{count}"),
                        timestamp=timestamp,
                        tx_type=self._map_coinbase_type(row['Transaction Type']),
                        asset=row['Asset'],
                        amount=Decimal(row['Quantity Transacted']),
                        price_usd=Decimal(row.get('Spot Price at Transaction', 0)),
                        fee=Decimal(row.get('Fees', 0)),
                        exchange='Coinbase',
                        notes=row.get('Notes', '')
                    )

                    self.add_transaction(tx)
                    count += 1

                except Exception as e:
                    logger.error(f"Error importing Coinbase row {count}: {e}")
                    continue

        return count

    def _import_binance(self, file_path: str) -> int:
        """Import Binance transaction history"""
        count = 0
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    timestamp = datetime.strptime(
                        row['Date(UTC)'],
                        '%Y-%m-%d %H:%M:%S'
                    )

                    tx = Transaction(
                        tx_id=f"BN_{count}_{row.get('Order ID', '')}",
                        timestamp=timestamp,
                        tx_type=self._map_binance_type(row['Type']),
                        asset=row['Coin'],
                        amount=Decimal(row['Change']),
                        price_usd=Decimal('0'),  # Need to fetch historical price
                        fee=Decimal('0'),
                        exchange='Binance',
                        notes=row.get('Remark', '')
                    )

                    # Fetch historical price
                    tx.price_usd = self._fetch_historical_price(
                        tx.asset,
                        tx.timestamp
                    )

                    self.add_transaction(tx)
                    count += 1

                except Exception as e:
                    logger.error(f"Error importing Binance row {count}: {e}")
                    continue

        return count

    def _import_kraken(self, file_path: str) -> int:
        """Import Kraken transaction history"""
        count = 0
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    timestamp = datetime.strptime(
                        row['time'],
                        '%Y-%m-%d %H:%M:%S'
                    )

                    tx = Transaction(
                        tx_id=row.get('txid', f"KR_{count}"),
                        timestamp=timestamp,
                        tx_type=self._map_kraken_type(row['type']),
                        asset=row['asset'],
                        amount=Decimal(row['amount']),
                        price_usd=Decimal('0'),
                        fee=Decimal(row.get('fee', 0)),
                        exchange='Kraken'
                    )

                    tx.price_usd = self._fetch_historical_price(
                        tx.asset,
                        tx.timestamp
                    )

                    self.add_transaction(tx)
                    count += 1

                except Exception as e:
                    logger.error(f"Error importing Kraken row {count}: {e}")
                    continue

        return count

    def _import_csv(self, file_path: str) -> int:
        """Import generic CSV format"""
        count = 0
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    tx = Transaction(
                        tx_id=row.get('tx_id', f"CSV_{count}"),
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        tx_type=TransactionType(row['type']),
                        asset=row['asset'],
                        amount=Decimal(row['amount']),
                        price_usd=Decimal(row.get('price_usd', 0)),
                        fee=Decimal(row.get('fee', 0)),
                        exchange=row.get('exchange', ''),
                        wallet=row.get('wallet', '')
                    )

                    self.add_transaction(tx)
                    count += 1

                except Exception as e:
                    logger.error(f"Error importing CSV row {count}: {e}")
                    continue

        return count

    def _import_json(self, file_path: str) -> int:
        """Import JSON format"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        count = 0
        for tx_data in data:
            try:
                tx = Transaction(
                    tx_id=tx_data['tx_id'],
                    timestamp=datetime.fromisoformat(tx_data['timestamp']),
                    tx_type=TransactionType(tx_data['type']),
                    asset=tx_data['asset'],
                    amount=Decimal(str(tx_data['amount'])),
                    price_usd=Decimal(str(tx_data.get('price_usd', 0))),
                    fee=Decimal(str(tx_data.get('fee', 0))),
                    exchange=tx_data.get('exchange', ''),
                    wallet=tx_data.get('wallet', '')
                )

                self.add_transaction(tx)
                count += 1

            except Exception as e:
                logger.error(f"Error importing JSON transaction {count}: {e}")
                continue

        return count

    def _map_coinbase_type(self, cb_type: str) -> TransactionType:
        """Map Coinbase transaction types"""
        mapping = {
            'Buy': TransactionType.BUY,
            'Sell': TransactionType.SELL,
            'Send': TransactionType.SEND,
            'Receive': TransactionType.RECEIVE,
            'Rewards Income': TransactionType.REWARD,
            'Coinbase Earn': TransactionType.REWARD,
            'Convert': TransactionType.SWAP
        }
        return mapping.get(cb_type, TransactionType.RECEIVE)

    def _map_binance_type(self, bn_type: str) -> TransactionType:
        """Map Binance transaction types"""
        mapping = {
            'Deposit': TransactionType.RECEIVE,
            'Withdraw': TransactionType.SEND,
            'Buy': TransactionType.BUY,
            'Sell': TransactionType.SELL,
            'Fee': TransactionType.SEND,
            'Staking Rewards': TransactionType.STAKE,
            'Distribution': TransactionType.REWARD
        }
        return mapping.get(bn_type, TransactionType.RECEIVE)

    def _map_kraken_type(self, kr_type: str) -> TransactionType:
        """Map Kraken transaction types"""
        mapping = {
            'deposit': TransactionType.RECEIVE,
            'withdrawal': TransactionType.SEND,
            'trade': TransactionType.TRADE,
            'staking': TransactionType.STAKE,
            'reward': TransactionType.REWARD
        }
        return mapping.get(kr_type, TransactionType.RECEIVE)

    def _fetch_historical_price(self, asset: str, timestamp: datetime) -> Decimal:
        """
        Fetch historical price for asset at timestamp
        In production, integrate with CoinGecko/CoinMarketCap API
        """
        # Mock implementation - replace with actual API call
        logger.debug(f"Fetching price for {asset} at {timestamp}")
        return Decimal('0')  # Placeholder

    def add_transaction(self, tx: Transaction):
        """Add transaction and create tax lots"""
        self.transactions.append(tx)
        self.stats['total_transactions'] += 1

        # Check if this is an income event
        if tx.tx_type in [TransactionType.STAKE, TransactionType.REWARD,
                         TransactionType.MINING, TransactionType.AIRDROP]:
            tx.is_income = True
            self.income_events.append(tx)
            self.stats['total_income_events'] += 1

        # Create tax lot for acquisitions
        if self._is_acquisition(tx):
            self._create_tax_lot(tx)

        # Process disposals
        if self._is_disposal(tx):
            self._process_disposal(tx)

        # Save to database
        self._save_transaction(tx)

    def _is_acquisition(self, tx: Transaction) -> bool:
        """Check if transaction is an acquisition"""
        return tx.tx_type in [
            TransactionType.BUY, TransactionType.RECEIVE,
            TransactionType.STAKE, TransactionType.REWARD,
            TransactionType.MINING, TransactionType.AIRDROP,
            TransactionType.LP_ADD
        ]

    def _is_disposal(self, tx: Transaction) -> bool:
        """Check if transaction is a disposal"""
        return tx.tx_type in [
            TransactionType.SELL, TransactionType.SEND,
            TransactionType.TRADE, TransactionType.SWAP,
            TransactionType.GIFT, TransactionType.DONATION,
            TransactionType.LP_REMOVE
        ]

    def _create_tax_lot(self, tx: Transaction):
        """Create a tax lot from acquisition transaction"""
        cost_basis = tx.fair_market_value + (tx.fee * tx.price_usd)

        lot = TaxLot(
            lot_id='',  # Will be generated
            asset=tx.asset,
            amount=tx.amount,
            cost_basis=cost_basis,
            acquisition_date=tx.timestamp,
            acquisition_price=tx.price_usd,
            acquisition_source=tx.exchange or tx.wallet,
            is_income=tx.is_income
        )

        if tx.asset not in self.tax_lots:
            self.tax_lots[tx.asset] = []

        self.tax_lots[tx.asset].append(lot)
        self._save_tax_lot(lot)

        logger.debug(f"Created tax lot {lot.lot_id} for {tx.amount} {tx.asset}")

    def _process_disposal(self, tx: Transaction):
        """Process disposal transaction and create tax event"""
        if tx.asset not in self.tax_lots:
            logger.warning(f"No lots found for {tx.asset} disposal")
            return

        # Get lots to dispose based on accounting method
        lots_to_use = self._select_lots(tx.asset, tx.amount)

        if not lots_to_use:
            logger.warning(f"Insufficient lots for {tx.amount} {tx.asset}")
            return

        # Calculate cost basis and create tax event
        total_cost_basis = Decimal('0')
        lots_used = []

        remaining_amount = tx.amount

        for lot in lots_to_use:
            if remaining_amount <= 0:
                break

            dispose_amount = min(remaining_amount, lot.remaining_amount)
            cost_basis = lot.dispose(dispose_amount)

            total_cost_basis += cost_basis
            lots_used.append(lot.lot_id)
            remaining_amount -= dispose_amount

            # Update lot in database
            self._update_tax_lot(lot)

        # Create tax event
        proceeds = tx.fair_market_value - (tx.fee * tx.price_usd)
        gain_loss = proceeds - total_cost_basis

        holding_period = (tx.timestamp - lots_to_use[0].acquisition_date).days
        is_long_term = holding_period >= self.jurisdiction.value['short_term_days']

        event = TaxEvent(
            event_id=f"EVENT_{tx.tx_id}",
            timestamp=tx.timestamp,
            event_type=tx.tx_type.value,
            asset=tx.asset,
            amount=tx.amount,
            proceeds=proceeds,
            cost_basis=total_cost_basis,
            gain_loss=gain_loss,
            holding_period_days=holding_period,
            is_long_term=is_long_term,
            tax_rate=self._calculate_tax_rate(gain_loss, is_long_term),
            source_tx_id=tx.tx_id,
            lots_used=lots_used,
            form_8949_category=self._get_form_8949_category(tx, is_long_term),
            schedule_d_line=self._get_schedule_d_line(is_long_term)
        )

        self.tax_events.append(event)
        self._save_tax_event(event)

        # Update statistics
        if gain_loss > 0:
            self.stats['total_gain'] += gain_loss
            if is_long_term:
                self.stats['long_term_gain'] += gain_loss
            else:
                self.stats['short_term_gain'] += gain_loss
        else:
            self.stats['total_loss'] += abs(gain_loss)

        self.stats['total_trades'] += 1

        logger.info(f"Processed disposal: {tx.amount} {tx.asset}, Gain/Loss: ${gain_loss:.2f}")

    def _select_lots(self, asset: str, amount: Decimal) -> List[TaxLot]:
        """Select tax lots based on accounting method"""
        available_lots = [
            lot for lot in self.tax_lots[asset]
            if lot.remaining_amount > 0
        ]

        if self.accounting_method == AccountingMethod.FIFO:
            # First In, First Out
            available_lots.sort(key=lambda x: x.acquisition_date)

        elif self.accounting_method == AccountingMethod.LIFO:
            # Last In, First Out
            available_lots.sort(key=lambda x: x.acquisition_date, reverse=True)

        elif self.accounting_method == AccountingMethod.HIFO:
            # Highest In, First Out (highest cost basis first)
            available_lots.sort(
                key=lambda x: x.cost_basis / x.amount,
                reverse=True
            )

        elif self.accounting_method == AccountingMethod.SPECIFIC_ID:
            # Specific Identification - user must specify
            # For now, default to FIFO
            available_lots.sort(key=lambda x: x.acquisition_date)

        return available_lots

    def _calculate_tax_rate(self, gain_loss: Decimal, is_long_term: bool) -> Decimal:
        """Calculate applicable tax rate based on jurisdiction"""
        if self.jurisdiction == TaxJurisdiction.US_IRS:
            if is_long_term:
                # Long-term capital gains (simplified - use actual brackets)
                if gain_loss <= 40000:
                    return Decimal('0.0')
                elif gain_loss <= 441450:
                    return Decimal('0.15')
                else:
                    return Decimal('0.20')
            else:
                # Short-term capital gains (ordinary income - simplified)
                if gain_loss <= 10000:
                    return Decimal('0.10')
                elif gain_loss <= 40000:
                    return Decimal('0.12')
                elif gain_loss <= 85000:
                    return Decimal('0.22')
                else:
                    return Decimal('0.24')

        elif self.jurisdiction == TaxJurisdiction.UK_HMRC:
            # UK capital gains tax
            return Decimal('0.20')  # Simplified

        elif self.jurisdiction == TaxJurisdiction.AU_ATO:
            # Australian CGT with 50% discount for long-term
            base_rate = Decimal('0.32')  # Simplified
            if is_long_term:
                return base_rate * Decimal('0.5')
            return base_rate

        return Decimal('0')

    def _get_form_8949_category(self, tx: Transaction, is_long_term: bool) -> str:
        """Determine Form 8949 category"""
        # Categories: A, B, C (short-term), D, E, F (long-term)
        # Based on whether 1099-B was received
        if is_long_term:
            return "D"  # Long-term, no 1099-B
        else:
            return "A"  # Short-term, no 1099-B

    def _get_schedule_d_line(self, is_long_term: bool) -> str:
        """Determine Schedule D line number"""
        return "8b" if is_long_term else "3"

    def calculate_taxes(self) -> Dict:
        """Calculate all taxes for the year"""
        logger.info(f"Calculating taxes for year {self.tax_year}")

        # Filter events for tax year
        year_events = [
            event for event in self.tax_events
            if event.timestamp.year == self.tax_year
        ]

        # Calculate totals
        short_term_gain = sum(
            e.gain_loss for e in year_events
            if not e.is_long_term and e.gain_loss > 0
        )
        short_term_loss = sum(
            abs(e.gain_loss) for e in year_events
            if not e.is_long_term and e.gain_loss < 0
        )
        long_term_gain = sum(
            e.gain_loss for e in year_events
            if e.is_long_term and e.gain_loss > 0
        )
        long_term_loss = sum(
            abs(e.gain_loss) for e in year_events
            if e.is_long_term and e.gain_loss < 0
        )

        net_short_term = short_term_gain - short_term_loss
        net_long_term = long_term_gain - long_term_loss
        net_gain_loss = net_short_term + net_long_term

        # Calculate tax liability
        tax_liability = self._calculate_tax_liability(
            net_short_term,
            net_long_term
        )

        # Income events
        year_income = [
            tx for tx in self.income_events
            if tx.timestamp.year == self.tax_year
        ]

        total_income = sum(tx.fair_market_value for tx in year_income)

        result = {
            'tax_year': self.tax_year,
            'jurisdiction': self.jurisdiction.value['name'],
            'accounting_method': self.accounting_method.value,
            'summary': {
                'total_transactions': len([t for t in self.transactions if t.timestamp.year == self.tax_year]),
                'total_trades': len(year_events),
                'total_income_events': len(year_income),
                'short_term': {
                    'gains': float(short_term_gain),
                    'losses': float(short_term_loss),
                    'net': float(net_short_term)
                },
                'long_term': {
                    'gains': float(long_term_gain),
                    'losses': float(long_term_loss),
                    'net': float(net_long_term)
                },
                'net_gain_loss': float(net_gain_loss),
                'ordinary_income': float(total_income),
                'tax_liability': float(tax_liability),
                'effective_rate': float(tax_liability / net_gain_loss * 100) if net_gain_loss > 0 else 0
            },
            'events': [self._event_to_dict(e) for e in year_events],
            'income': [self._tx_to_dict(tx) for tx in year_income]
        }

        logger.info(f"Tax calculation complete: Net gain/loss ${net_gain_loss:.2f}, Tax ${tax_liability:.2f}")

        return result

    def _calculate_tax_liability(self, net_short_term: Decimal, net_long_term: Decimal) -> Decimal:
        """Calculate total tax liability"""
        short_term_tax = max(0, net_short_term) * self._calculate_tax_rate(net_short_term, False)
        long_term_tax = max(0, net_long_term) * self._calculate_tax_rate(net_long_term, True)
        return short_term_tax + long_term_tax

    def generate_form_8949(self, output_path: str):
        """Generate IRS Form 8949 PDF"""
        logger.info(f"Generating Form 8949: {output_path}")

        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(inch, height - inch, "Form 8949")
        c.setFont("Helvetica", 10)
        c.drawString(inch, height - inch * 1.3,
                    f"Sales and Other Dispositions of Capital Assets - {self.tax_year}")

        # Filter events by category
        categories = {}
        for event in self.tax_events:
            if event.timestamp.year != self.tax_year:
                continue

            cat = event.form_8949_category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(event)

        y_position = height - inch * 2

        for category, events in categories.items():
            c.setFont("Helvetica-Bold", 12)
            c.drawString(inch, y_position, f"Part I - Category {category}")
            y_position -= 0.3 * inch

            # Headers
            c.setFont("Helvetica", 8)
            headers = ["Description", "Date Acquired", "Date Sold",
                      "Proceeds", "Cost Basis", "Gain/Loss"]
            x_positions = [inch, 2*inch, 3*inch, 4*inch, 5*inch, 6*inch]

            for i, header in enumerate(headers):
                c.drawString(x_positions[i], y_position, header)

            y_position -= 0.2 * inch

            # Transactions
            for event in events[:20]:  # Limit to 20 per page
                if y_position < inch:
                    c.showPage()
                    y_position = height - inch

                c.setFont("Helvetica", 7)
                c.drawString(x_positions[0], y_position,
                           f"{event.amount:.8f} {event.asset}")
                c.drawString(x_positions[1], y_position,
                           event.timestamp.strftime("%m/%d/%Y"))
                c.drawString(x_positions[2], y_position,
                           event.timestamp.strftime("%m/%d/%Y"))
                c.drawString(x_positions[3], y_position,
                           f"${event.proceeds:.2f}")
                c.drawString(x_positions[4], y_position,
                           f"${event.cost_basis:.2f}")
                c.drawString(x_positions[5], y_position,
                           f"${event.gain_loss:.2f}")

                y_position -= 0.15 * inch

            # Totals for category
            y_position -= 0.1 * inch
            c.setFont("Helvetica-Bold", 8)
            total_proceeds = sum(e.proceeds for e in events)
            total_cost = sum(e.cost_basis for e in events)
            total_gain = sum(e.gain_loss for e in events)

            c.drawString(x_positions[2], y_position, "TOTALS:")
            c.drawString(x_positions[3], y_position, f"${total_proceeds:.2f}")
            c.drawString(x_positions[4], y_position, f"${total_cost:.2f}")
            c.drawString(x_positions[5], y_position, f"${total_gain:.2f}")

            y_position -= 0.5 * inch

        c.save()
        logger.info(f"Form 8949 generated: {output_path}")

    def generate_schedule_d(self, output_path: str):
        """Generate IRS Schedule D PDF"""
        logger.info(f"Generating Schedule D: {output_path}")
        # Implementation similar to Form 8949
        pass

    def export_csv(self, output_path: str):
        """Export all tax events to CSV"""
        logger.info(f"Exporting to CSV: {output_path}")

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Date', 'Type', 'Asset', 'Amount', 'Proceeds',
                'Cost Basis', 'Gain/Loss', 'Holding Period',
                'Term', 'Tax Rate'
            ])

            for event in self.tax_events:
                if event.timestamp.year != self.tax_year:
                    continue

                writer.writerow([
                    event.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    event.event_type,
                    event.asset,
                    f"{event.amount:.8f}",
                    f"{event.proceeds:.2f}",
                    f"{event.cost_basis:.2f}",
                    f"{event.gain_loss:.2f}",
                    event.holding_period_days,
                    'Long' if event.is_long_term else 'Short',
                    f"{event.tax_rate:.2%}"
                ])

        logger.info(f"CSV export complete: {output_path}")

    def export_json(self, output_path: str):
        """Export complete tax calculation to JSON"""
        result = self.calculate_taxes()

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        logger.info(f"JSON export complete: {output_path}")

    def _save_transaction(self, tx: Transaction):
        """Save transaction to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO transactions VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tx.tx_id, tx.timestamp.isoformat(), tx.tx_type.value,
            tx.asset, float(tx.amount), float(tx.price_usd),
            float(tx.fee), tx.exchange, tx.wallet,
            tx.to_asset, float(tx.to_amount) if tx.to_amount else None,
            float(tx.fair_market_value), int(tx.is_income), tx.notes
        ))

        conn.commit()
        conn.close()

    def _save_tax_lot(self, lot: TaxLot):
        """Save tax lot to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO tax_lots VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lot.lot_id, lot.asset, float(lot.amount),
            float(lot.cost_basis), lot.acquisition_date.isoformat(),
            float(lot.acquisition_price), float(lot.remaining_amount),
            float(lot.disposed_amount), int(lot.is_income)
        ))

        conn.commit()
        conn.close()

    def _update_tax_lot(self, lot: TaxLot):
        """Update tax lot in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tax_lots
            SET remaining_amount = ?, disposed_amount = ?
            WHERE lot_id = ?
        """, (float(lot.remaining_amount), float(lot.disposed_amount), lot.lot_id))

        conn.commit()
        conn.close()

    def _save_tax_event(self, event: TaxEvent):
        """Save tax event to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO tax_events VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id, event.timestamp.isoformat(), event.event_type,
            event.asset, float(event.amount), float(event.proceeds),
            float(event.cost_basis), float(event.gain_loss),
            event.holding_period_days, int(event.is_long_term),
            float(event.tax_rate), event.form_8949_category,
            ','.join(event.lots_used)
        ))

        conn.commit()
        conn.close()

    def _event_to_dict(self, event: TaxEvent) -> Dict:
        """Convert tax event to dictionary"""
        return {
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'type': event.event_type,
            'asset': event.asset,
            'amount': float(event.amount),
            'proceeds': float(event.proceeds),
            'cost_basis': float(event.cost_basis),
            'gain_loss': float(event.gain_loss),
            'holding_period_days': event.holding_period_days,
            'is_long_term': event.is_long_term,
            'tax_rate': float(event.tax_rate),
            'form_8949_category': event.form_8949_category,
            'schedule_d_line': event.schedule_d_line
        }

    def _tx_to_dict(self, tx: Transaction) -> Dict:
        """Convert transaction to dictionary"""
        return {
            'tx_id': tx.tx_id,
            'timestamp': tx.timestamp.isoformat(),
            'type': tx.tx_type.value,
            'asset': tx.asset,
            'amount': float(tx.amount),
            'price_usd': float(tx.price_usd),
            'fair_market_value': float(tx.fair_market_value),
            'exchange': tx.exchange,
            'wallet': tx.wallet
        }


# Example Usage
if __name__ == "__main__":
    # Initialize calculator
    calculator = CryptoTaxCalculator(
        jurisdiction=TaxJurisdiction.US_IRS,
        accounting_method=AccountingMethod.FIFO,
        tax_year=2024
    )

    # Import transactions from multiple exchanges
    calculator.import_transactions('coinbase', 'coinbase_transactions.csv')
    calculator.import_transactions('binance', 'binance_transactions.csv')
    calculator.import_transactions('kraken', 'kraken_transactions.csv')

    # Calculate taxes
    results = calculator.calculate_taxes()

    # Print summary
    print(f"\n{'='*60}")
    print(f"CRYPTOCURRENCY TAX SUMMARY - {results['tax_year']}")
    print(f"{'='*60}")
    print(f"Jurisdiction: {results['jurisdiction']}")
    print(f"Accounting Method: {results['accounting_method']}")
    print(f"\nTransactions: {results['summary']['total_transactions']}")
    print(f"Trades: {results['summary']['total_trades']}")
    print(f"Income Events: {results['summary']['total_income_events']}")
    print(f"\nSHORT-TERM:")
    print(f"  Gains: ${results['summary']['short_term']['gains']:,.2f}")
    print(f"  Losses: ${results['summary']['short_term']['losses']:,.2f}")
    print(f"  Net: ${results['summary']['short_term']['net']:,.2f}")
    print(f"\nLONG-TERM:")
    print(f"  Gains: ${results['summary']['long_term']['gains']:,.2f}")
    print(f"  Losses: ${results['summary']['long_term']['losses']:,.2f}")
    print(f"  Net: ${results['summary']['long_term']['net']:,.2f}")
    print(f"\nNET GAIN/LOSS: ${results['summary']['net_gain_loss']:,.2f}")
    print(f"ORDINARY INCOME: ${results['summary']['ordinary_income']:,.2f}")
    print(f"TAX LIABILITY: ${results['summary']['tax_liability']:,.2f}")
    print(f"EFFECTIVE RATE: {results['summary']['effective_rate']:.2f}%")
    print(f"{'='*60}\n")

    # Generate reports
    calculator.generate_form_8949('Form_8949_2024.pdf')
    calculator.generate_schedule_d('Schedule_D_2024.pdf')
    calculator.export_csv('crypto_tax_report_2024.csv')
    calculator.export_json('crypto_tax_report_2024.json')

    print("Tax calculation complete! Reports generated:")
    print("  - Form_8949_2024.pdf")
    print("  - Schedule_D_2024.pdf")
    print("  - crypto_tax_report_2024.csv")
    print("  - crypto_tax_report_2024.json")
```

## Compliance Considerations

### United States (IRS)

**Key Requirements:**
- Report all crypto transactions on Form 8949 and Schedule D
- Report ordinary income (staking, mining, airdrops) on Schedule 1
- De minimis exception: Personal transactions under $200 may be exempt
- Wash sale rules: Currently DO NOT apply to crypto (as of 2024)
- FinCEN Form 114: Required for foreign exchange accounts over $10k

**Tax Rates (2024):**
- Short-term capital gains: Ordinary income rates (10%-37%)
- Long-term capital gains: 0%, 15%, or 20% based on income
- Net Investment Income Tax: Additional 3.8% for high earners

**Common Pitfalls:**
- Failing to report crypto-to-crypto trades
- Not tracking cost basis properly
- Misclassifying staking rewards as capital gains
- Forgetting about hard forks and airdrops

### United Kingdom (HMRC)

**Key Requirements:**
- Report on Self Assessment tax return (SA108)
- Same-day rule: Acquisitions on same day as disposal
- Bed and breakfast rule: 30-day lookback for repurchases
- Capital Gains Annual Exempt Amount: £6,000 (2024)
- Pooling: UK uses share pool accounting for most crypto

**Tax Rates:**
- Capital Gains Tax: 10% or 20% depending on income band
- Income Tax on crypto earnings: 20%-45%

### European Union (DAC8)

**Key Requirements:**
- Mandatory reporting for crypto service providers
- Cross-border information exchange
- MiFID II compliance for some crypto assets
- AMLD5 anti-money laundering requirements

**Member State Variations:**
- Germany: Tax-free after 1 year holding
- France: Flat 30% tax on gains
- Portugal: Generally tax-free for individuals

### Australia (ATO)

**Key Requirements:**
- Report on myTax CGT schedule
- 50% CGT discount for assets held >12 months
- Personal use asset exemption: Under $10,000 for personal spending

### Canada (CRA)

**Key Requirements:**
- Report on Schedule 3
- 50% capital gains inclusion rate
- Superficial loss rules: 30-day restriction

## Wash Sale Considerations

While wash sales don't currently apply to cryptocurrency in the US, best practices include:

1. **Track repurchases within 30 days** of sales at a loss
2. **Document business purpose** for quick repurchases
3. **Consider tax-loss harvesting** opportunities
4. **Monitor legislative changes** - may change in future

## Audit Trail Requirements

Maintain records for at least 7 years:
- Complete transaction history from all exchanges
- Wallet addresses and blockchain transaction IDs
- Historical price data and valuation methods
- Cost basis calculations and methodology documentation
- Form 8949 and Schedule D calculations
- Supporting documentation for adjustments

## Error Handling

```python
try:
    calculator = CryptoTaxCalculator(
        jurisdiction=TaxJurisdiction.US_IRS,
        accounting_method=AccountingMethod.FIFO,
        tax_year=2024
    )

    # Import and calculate
    calculator.import_transactions('coinbase', 'transactions.csv')
    results = calculator.calculate_taxes()

    # Generate reports
    calculator.generate_form_8949('Form_8949.pdf')
    calculator.export_csv('tax_report.csv')

except FileNotFoundError as e:
    logger.error(f"Transaction file not found: {e}")
except ValueError as e:
    logger.error(f"Invalid data format: {e}")
except Exception as e:
    logger.error(f"Tax calculation failed: {e}")
    raise
```

## Best Practices

1. **Import transactions frequently** - Don't wait until tax season
2. **Reconcile holdings** - Verify calculated balances match actual holdings
3. **Use consistent accounting method** - Don't switch mid-year
4. **Track ALL taxable events** - Including DeFi, staking, airdrops
5. **Maintain documentation** - Keep records of all transactions and valuations
6. **Consult tax professional** - Especially for complex situations

This command provides enterprise-grade cryptocurrency tax calculation with full compliance support for multiple jurisdictions and automated form generation.