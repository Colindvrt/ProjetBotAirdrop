"""
Abstract base class for all trading platform implementations.

All platform-specific implementations (Hyperliquid, Paradex, Lighter, Extended)
must inherit from BasePlatformAPI and implement all abstract methods.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncio
from src.core.models import (
    FundingData,
    AccountBalance,
    OrderResult,
    Position,
    MarketInfo,
    OrderSide,
    Platform
)


class BasePlatformAPI(ABC):
    """
    Abstract base class for trading platform APIs.

    This class defines the interface that all platform implementations must follow.
    It ensures consistency across different platforms and makes it easy to add new ones.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the platform API with configuration.

        Args:
            config: Platform-specific configuration (API keys, secrets, etc.)
        """
        self.config = config
        self.platform_name = self._get_platform_name()

    @abstractmethod
    def _get_platform_name(self) -> str:
        """Return the platform name (e.g., 'Hyperliquid')."""
        pass

    # ========== FUNDING DATA ==========

    @abstractmethod
    async def get_funding_rates(self) -> List[FundingData]:
        """
        Fetch current funding rates for all available trading pairs.

        Returns:
            List of FundingData objects containing funding rate information.
        """
        pass

    def get_funding_rates_sync(self) -> List[FundingData]:
        """
        Synchronous wrapper for get_funding_rates().

        This is useful for calling from non-async contexts.
        """
        return asyncio.run(self.get_funding_rates())

    # ========== ACCOUNT INFORMATION ==========

    @abstractmethod
    async def get_account_balance(self) -> AccountBalance:
        """
        Fetch account balance and equity information.

        Returns:
            AccountBalance object with current account state.
        """
        pass

    def get_account_balance_sync(self) -> AccountBalance:
        """
        Synchronous wrapper for get_account_balance().
        """
        return asyncio.run(self.get_account_balance())

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """
        Fetch all open positions.

        Returns:
            List of Position objects representing current open positions.
        """
        pass

    def get_positions_sync(self) -> List[Position]:
        """
        Synchronous wrapper for get_positions().
        """
        return asyncio.run(self.get_positions())

    # ========== MARKET DATA ==========

    @abstractmethod
    async def get_market_info(self, pair: str) -> MarketInfo:
        """
        Fetch market information for a specific trading pair.

        Args:
            pair: Trading pair (e.g., "BTC", "ETH")

        Returns:
            MarketInfo object with current market state.
        """
        pass

    def get_market_info_sync(self, pair: str) -> MarketInfo:
        """
        Synchronous wrapper for get_market_info().
        """
        return asyncio.run(self.get_market_info(pair))

    # ========== TRADING OPERATIONS ==========

    @abstractmethod
    async def place_market_order(
        self,
        pair: str,
        side: OrderSide,
        size_usd: float,
        leverage: int
    ) -> OrderResult:
        """
        Place a market order on the platform.

        Args:
            pair: Trading pair (e.g., "BTC", "ETH")
            side: OrderSide.LONG or OrderSide.SHORT
            size_usd: Position size in USD (notional value)
            leverage: Leverage to use (1-50x depending on platform)

        Returns:
            OrderResult object with execution details.
        """
        pass

    def place_market_order_sync(
        self,
        pair: str,
        side: OrderSide,
        size_usd: float,
        leverage: int
    ) -> OrderResult:
        """
        Synchronous wrapper for place_market_order().
        """
        return asyncio.run(self.place_market_order(pair, side, size_usd, leverage))

    @abstractmethod
    async def close_position(self, pair: str) -> OrderResult:
        """
        Close an open position for a specific trading pair.

        Args:
            pair: Trading pair (e.g., "BTC", "ETH")

        Returns:
            OrderResult object with closing execution details.
        """
        pass

    def close_position_sync(self, pair: str) -> OrderResult:
        """
        Synchronous wrapper for close_position().
        """
        return asyncio.run(self.close_position(pair))

    @abstractmethod
    async def set_leverage(self, pair: str, leverage: int) -> bool:
        """
        Set leverage for a specific trading pair.

        Args:
            pair: Trading pair (e.g., "BTC", "ETH")
            leverage: Desired leverage (1-50x)

        Returns:
            True if successful, False otherwise.
        """
        pass

    def set_leverage_sync(self, pair: str, leverage: int) -> bool:
        """
        Synchronous wrapper for set_leverage().
        """
        return asyncio.run(self.set_leverage(pair, leverage))

    # ========== HELPER METHODS ==========

    def standardize_pair_name(self, pair: str) -> str:
        """
        Standardize pair name across platforms.

        Different platforms use different naming conventions:
        - Hyperliquid: "BTC"
        - Paradex: "BTC-USD-PERP"
        - Lighter: "BTC_USDC_PER_9"
        - Extended: "BTC-USD-PERP"

        This method converts platform-specific names to a standard format ("BTC").

        Args:
            pair: Platform-specific pair name

        Returns:
            Standardized pair name (e.g., "BTC", "ETH", "SOL")
        """
        # Remove common suffixes
        pair = pair.upper()
        pair = pair.replace("-USD-PERP", "")
        pair = pair.replace("-PERP", "")
        pair = pair.replace("_USDC_PER_9", "")
        pair = pair.replace("_USDC", "")
        pair = pair.replace("USDC", "")
        pair = pair.replace("USD", "")
        pair = pair.replace("-", "")
        pair = pair.replace("_", "")
        return pair.strip()

    def validate_config(self) -> bool:
        """
        Validate that the configuration has all required fields.

        Returns:
            True if configuration is valid, False otherwise.
        """
        # Subclasses can override this to add platform-specific validation
        return self.config is not None and len(self.config) > 0

    async def health_check(self) -> bool:
        """
        Perform a health check to verify the API is accessible.

        Returns:
            True if API is healthy, False otherwise.
        """
        try:
            # Try to fetch account balance as a health check
            await self.get_account_balance()
            return True
        except Exception:
            return False

    def health_check_sync(self) -> bool:
        """
        Synchronous wrapper for health_check().
        """
        return asyncio.run(self.health_check())


class PlatformFactory:
    """
    Factory class for creating platform instances.

    This makes it easy to instantiate the correct platform implementation
    based on a platform name.
    """

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, platform_name: str, platform_class: type):
        """
        Register a platform implementation.

        Args:
            platform_name: Name of the platform (e.g., "Hyperliquid")
            platform_class: The platform class to register
        """
        cls._registry[platform_name.lower()] = platform_class

    @classmethod
    def create(cls, platform_name: str, config: Dict[str, Any]) -> BasePlatformAPI:
        """
        Create a platform instance.

        Args:
            platform_name: Name of the platform (e.g., "Hyperliquid")
            config: Platform-specific configuration

        Returns:
            Instance of the platform implementation

        Raises:
            ValueError: If platform is not registered
        """
        platform_class = cls._registry.get(platform_name.lower())
        if platform_class is None:
            raise ValueError(f"Unknown platform: {platform_name}")
        return platform_class(config)

    @classmethod
    def list_platforms(cls) -> List[str]:
        """
        List all registered platforms.

        Returns:
            List of platform names
        """
        return list(cls._registry.keys())
