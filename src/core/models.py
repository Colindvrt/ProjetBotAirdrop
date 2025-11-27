"""
Data models for the Funding Farming Bot application.

This module contains all data structures used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class Platform(Enum):
    """Supported trading platforms."""
    HYPERLIQUID = "Hyperliquid"
    PARADEX = "Paradex"
    LIGHTER = "Lighter"
    EXTENDED = "Extended"


class OrderSide(Enum):
    """Order side (long/short)."""
    LONG = "long"
    SHORT = "short"


class OrderStatus(Enum):
    """Order execution status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FundingData:
    """Funding rate data for a trading pair on a specific platform."""
    pair: str  # Asset name (e.g., "BTC", "ETH")
    rate_1h: float  # Hourly funding rate (decimal, e.g., 0.00025 = 0.025%)
    platform: str  # Platform name
    max_leverage: int  # Maximum leverage available
    timestamp: datetime = field(default_factory=datetime.now)
    volume_24h: Optional[float] = None  # 24h trading volume in USD

    def __post_init__(self):
        """Validate data after initialization."""
        if self.rate_1h is None:
            self.rate_1h = 0.0
        if self.max_leverage is None:
            self.max_leverage = 1


@dataclass
class Opportunity:
    """Delta-neutral funding arbitrage opportunity."""
    pair: str  # Trading pair

    # Long side
    long_platform: str
    long_rate_1h: float
    long_leverage: int

    # Short side
    short_platform: str
    short_rate_1h: float
    short_leverage: int

    # Metrics
    spread_1h: float  # Hourly spread (short_rate - long_rate)
    spread_8h: float  # 8-hour spread
    min_leverage: int  # Minimum of long and short leverage
    score_1h: float  # spread_1h * min_leverage
    score_8h: float  # spread_8h * min_leverage

    # Enhanced metrics (optional)
    net_spread_1h: Optional[float] = None  # Spread after fees and slippage
    entry_cost_pct: Optional[float] = None  # Entry + exit fees + slippage
    confidence_score: Optional[int] = None  # 0-100 confidence score
    volume_24h: Optional[float] = None  # Minimum volume across platforms

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AccountBalance:
    """Account balance information."""
    platform: str
    total_equity_usd: float  # Total account value in USD
    available_balance_usd: float  # Available balance for trading
    margin_used_usd: float = 0.0  # Margin currently used
    unrealized_pnl_usd: float = 0.0  # Unrealized PnL
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OrderResult:
    """Result of an order placement attempt."""
    success: bool
    platform: str
    pair: str
    side: OrderSide
    order_id: Optional[str] = None
    filled_size_usd: Optional[float] = None
    filled_price: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    """Open trading position."""
    platform: str
    pair: str
    side: OrderSide  # LONG or SHORT
    size_usd: float  # Position size in USD (notional)
    leverage: int
    entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl_usd: float = 0.0
    funding_accumulated_usd: float = 0.0
    liquidation_price: Optional[float] = None
    timestamp_opened: datetime = field(default_factory=datetime.now)
    timestamp_updated: datetime = field(default_factory=datetime.now)

    def update_pnl(self, current_price: float):
        """Update unrealized PnL based on current price."""
        self.current_price = current_price
        price_diff = current_price - self.entry_price

        if self.side == OrderSide.SHORT:
            price_diff = -price_diff

        # PnL = price_diff / entry_price * size * leverage
        self.unrealized_pnl_usd = (price_diff / self.entry_price) * self.size_usd * self.leverage
        self.timestamp_updated = datetime.now()


@dataclass
class MarketInfo:
    """Market information for a trading pair."""
    platform: str
    pair: str
    mark_price: float
    index_price: Optional[float] = None
    funding_rate_1h: float = 0.0
    next_funding_time: Optional[datetime] = None
    max_leverage: int = 1
    min_order_size_usd: float = 10.0
    maker_fee_pct: float = 0.02  # Default 0.02%
    taker_fee_pct: float = 0.05  # Default 0.05%
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DeltaNeutralStrategy:
    """Configuration for a delta-neutral arbitrage strategy."""
    opportunity: Opportunity
    stake_size_usd: float  # Total stake size
    target_leverage: int  # Target leverage to use

    # Auto-management settings
    auto_close_on_reversal: bool = False  # Close if funding reverses
    take_profit_usd: Optional[float] = None  # Close at profit target
    stop_loss_usd: Optional[float] = None  # Close at loss threshold
    max_hold_hours: Optional[int] = None  # Max time to hold position

    # Positions (filled after execution)
    long_position: Optional[Position] = None
    short_position: Optional[Position] = None

    timestamp_created: datetime = field(default_factory=datetime.now)

    def get_total_pnl(self) -> float:
        """Calculate total PnL across both positions."""
        pnl = 0.0
        if self.long_position:
            pnl += self.long_position.unrealized_pnl_usd
            pnl += self.long_position.funding_accumulated_usd
        if self.short_position:
            pnl += self.short_position.unrealized_pnl_usd
            pnl += self.short_position.funding_accumulated_usd
        return pnl


@dataclass
class AlertConfig:
    """Configuration for alerts and notifications."""
    enabled: bool = True

    # Spread alerts
    alert_on_new_opportunity: bool = True
    min_spread_threshold_pct: float = 0.05  # Alert if spread > 0.05%

    # PnL alerts
    alert_on_profit_threshold: bool = True
    profit_threshold_usd: float = 50.0
    alert_on_loss_threshold: bool = True
    loss_threshold_usd: float = -20.0

    # Risk alerts
    alert_on_liquidation_risk: bool = True
    liquidation_risk_threshold_pct: float = 20.0  # Alert if within 20% of liquidation

    # Funding reversal
    alert_on_funding_reversal: bool = True


# Platform fee structure (used for net spread calculations)
PLATFORM_FEES = {
    Platform.HYPERLIQUID: {
        'maker': 0.00020,  # 0.02%
        'taker': 0.00030,  # 0.03%
    },
    Platform.PARADEX: {
        'maker': 0.00020,  # 0.02%
        'taker': 0.00050,  # 0.05%
    },
    Platform.LIGHTER: {
        'maker': 0.00020,  # 0.02%
        'taker': 0.00050,  # 0.05%
    },
    Platform.EXTENDED: {
        'maker': 0.00020,  # 0.02%
        'taker': 0.00050,  # 0.05%
    },
}


# Default slippage estimates by platform (conservative)
PLATFORM_SLIPPAGE = {
    Platform.HYPERLIQUID: 0.0010,  # 0.1%
    Platform.PARADEX: 0.0015,  # 0.15%
    Platform.LIGHTER: 0.0015,  # 0.15%
    Platform.EXTENDED: 0.0020,  # 0.2%
}
