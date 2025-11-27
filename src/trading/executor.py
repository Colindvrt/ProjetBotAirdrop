"""
Unified trading executor for all platforms.

This module orchestrates trading operations across multiple platforms,
especially for delta-neutral strategies.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio

from src.platforms.base import BasePlatformAPI, PlatformFactory
from src.core.models import (
    Opportunity,
    DeltaNeutralStrategy,
    OrderResult,
    OrderSide,
    Position
)
from src.config.manager import ConfigManager


class TradingExecutor:
    """
    Unified executor for trading operations across all platforms.

    Handles:
    - Platform initialization
    - Delta-neutral strategy execution
    - Order placement with rollback on failure
    - Position tracking
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the trading executor.

        Args:
            config_manager: ConfigManager instance for platform credentials
        """
        self.config_manager = config_manager
        self.platforms: Dict[str, BasePlatformAPI] = {}
        self._initialize_platforms()

    def _initialize_platforms(self):
        """Initialize all configured platforms."""
        print("[Executor] Initializing platforms...")

        configured = self.config_manager.get_configured_platforms()

        for platform_name in configured:
            try:
                platform_config = self.config_manager.get_platform_config(platform_name)
                platform_instance = PlatformFactory.create(platform_name, platform_config)
                self.platforms[platform_name.lower()] = platform_instance
                print(f"[Executor] Initialized {platform_name}")
            except Exception as e:
                print(f"[Executor] Failed to initialize {platform_name}: {e}")

        print(f"[Executor] {len(self.platforms)} platforms ready")

    def get_platform(self, platform_name: str) -> Optional[BasePlatformAPI]:
        """
        Get a platform instance by name.

        Args:
            platform_name: Name of the platform (case-insensitive)

        Returns:
            Platform instance or None if not found
        """
        return self.platforms.get(platform_name.lower())

    def list_available_platforms(self) -> List[str]:
        """
        Get list of available platform names.

        Returns:
            List of platform names
        """
        return list(self.platforms.keys())

    # ========== DELTA NEUTRAL EXECUTION ==========

    async def execute_delta_neutral(
        self,
        opportunity: Opportunity,
        stake_size_usd: float,
        target_leverage: int,
        auto_close_on_reversal: bool = False,
        take_profit_usd: Optional[float] = None,
        stop_loss_usd: Optional[float] = None
    ) -> Tuple[bool, DeltaNeutralStrategy, str]:
        """
        Execute a delta-neutral arbitrage strategy.

        This opens a LONG position on the platform with the lowest funding rate
        and a SHORT position on the platform with the highest funding rate.

        Args:
            opportunity: Opportunity object with long/short platforms and rates
            stake_size_usd: Total stake size in USD
            target_leverage: Leverage to use on both sides
            auto_close_on_reversal: Auto-close if funding reverses
            take_profit_usd: Auto-close at this profit level
            stop_loss_usd: Auto-close at this loss level

        Returns:
            Tuple of (success, strategy, message)
        """
        print(f"\n[Executor] ========== DELTA NEUTRAL EXECUTION ==========")
        print(f"[Executor] Pair: {opportunity.pair}")
        print(f"[Executor] LONG on {opportunity.long_platform} @ {opportunity.long_rate_1h:.6f}%")
        print(f"[Executor] SHORT on {opportunity.short_platform} @ {opportunity.short_rate_1h:.6f}%")
        print(f"[Executor] Spread (1h): {opportunity.spread_1h:.6f}%")
        print(f"[Executor] Stake: ${stake_size_usd:.2f} @ {target_leverage}x leverage")
        print(f"[Executor] ===============================================\n")

        # Create strategy object
        strategy = DeltaNeutralStrategy(
            opportunity=opportunity,
            stake_size_usd=stake_size_usd,
            target_leverage=target_leverage,
            auto_close_on_reversal=auto_close_on_reversal,
            take_profit_usd=take_profit_usd,
            stop_loss_usd=stop_loss_usd
        )

        # Get platform instances
        long_platform = self.get_platform(opportunity.long_platform)
        short_platform = self.get_platform(opportunity.short_platform)

        if not long_platform:
            msg = f"Platform {opportunity.long_platform} not available"
            print(f"[Executor] ERROR: {msg}")
            return False, strategy, msg

        if not short_platform:
            msg = f"Platform {opportunity.short_platform} not available"
            print(f"[Executor] ERROR: {msg}")
            return False, strategy, msg

        # Execute LONG order
        print(f"[Executor] Step 1: Opening LONG on {opportunity.long_platform}...")
        long_result = await long_platform.place_market_order(
            pair=opportunity.pair,
            side=OrderSide.LONG,
            size_usd=stake_size_usd,
            leverage=target_leverage
        )

        if not long_result.success:
            msg = f"LONG order failed: {long_result.error_message}"
            print(f"[Executor] ERROR: {msg}")
            return False, strategy, msg

        print(f"[Executor] SUCCESS: LONG order filled @ ${long_result.filled_price:.2f}")

        # Execute SHORT order
        print(f"[Executor] Step 2: Opening SHORT on {opportunity.short_platform}...")
        short_result = await short_platform.place_market_order(
            pair=opportunity.pair,
            side=OrderSide.SHORT,
            size_usd=stake_size_usd,
            leverage=target_leverage
        )

        if not short_result.success:
            # SHORT failed - ROLLBACK LONG
            msg = f"SHORT order failed: {short_result.error_message}. Rolling back LONG..."
            print(f"[Executor] ERROR: {msg}")
            print(f"[Executor] Attempting rollback...")

            rollback_result = await long_platform.close_position(opportunity.pair)
            if rollback_result.success:
                print(f"[Executor] Rollback successful - LONG position closed")
                return False, strategy, f"{msg} (rolled back successfully)"
            else:
                print(f"[Executor] CRITICAL: Rollback failed - manual intervention required!")
                return False, strategy, f"{msg} (ROLLBACK FAILED - CHECK {opportunity.long_platform})"

        print(f"[Executor] SUCCESS: SHORT order filled @ ${short_result.filled_price:.2f}")

        # Create position records
        strategy.long_position = Position(
            platform=opportunity.long_platform,
            pair=opportunity.pair,
            side=OrderSide.LONG,
            size_usd=stake_size_usd,
            leverage=target_leverage,
            entry_price=long_result.filled_price,
            timestamp_opened=datetime.now()
        )

        strategy.short_position = Position(
            platform=opportunity.short_platform,
            pair=opportunity.pair,
            side=OrderSide.SHORT,
            size_usd=stake_size_usd,
            leverage=target_leverage,
            entry_price=short_result.filled_price,
            timestamp_opened=datetime.now()
        )

        msg = f"Delta-neutral strategy executed successfully!"
        print(f"\n[Executor] {msg}")
        print(f"[Executor] LONG: {long_result.order_id} on {opportunity.long_platform}")
        print(f"[Executor] SHORT: {short_result.order_id} on {opportunity.short_platform}")
        print(f"[Executor] Total PnL: ${strategy.get_total_pnl():.2f}")

        return True, strategy, msg

    def execute_delta_neutral_sync(
        self,
        opportunity: Opportunity,
        stake_size_usd: float,
        target_leverage: int,
        **kwargs
    ) -> Tuple[bool, DeltaNeutralStrategy, str]:
        """
        Synchronous wrapper for execute_delta_neutral().
        """
        return asyncio.run(
            self.execute_delta_neutral(
                opportunity, stake_size_usd, target_leverage, **kwargs
            )
        )

    # ========== POSITION MANAGEMENT ==========

    async def close_delta_neutral(
        self,
        strategy: DeltaNeutralStrategy
    ) -> Tuple[bool, str]:
        """
        Close both sides of a delta-neutral strategy.

        Args:
            strategy: DeltaNeutralStrategy to close

        Returns:
            Tuple of (success, message)
        """
        print(f"\n[Executor] ========== CLOSING DELTA NEUTRAL ==========")
        print(f"[Executor] Pair: {strategy.opportunity.pair}")

        if not strategy.long_position or not strategy.short_position:
            msg = "Strategy has no open positions"
            print(f"[Executor] ERROR: {msg}")
            return False, msg

        # Get platforms
        long_platform = self.get_platform(strategy.long_position.platform)
        short_platform = self.get_platform(strategy.short_position.platform)

        if not long_platform or not short_platform:
            msg = "One or both platforms not available"
            print(f"[Executor] ERROR: {msg}")
            return False, msg

        # Close LONG
        print(f"[Executor] Closing LONG on {strategy.long_position.platform}...")
        long_result = await long_platform.close_position(strategy.opportunity.pair)

        if not long_result.success:
            msg = f"Failed to close LONG: {long_result.error_message}"
            print(f"[Executor] ERROR: {msg}")
            return False, msg

        print(f"[Executor] SUCCESS: LONG closed")

        # Close SHORT
        print(f"[Executor] Closing SHORT on {strategy.short_position.platform}...")
        short_result = await short_platform.close_position(strategy.opportunity.pair)

        if not short_result.success:
            msg = f"Failed to close SHORT: {short_result.error_message}"
            print(f"[Executor] ERROR: {msg}")
            return False, msg

        print(f"[Executor] SUCCESS: SHORT closed")

        final_pnl = strategy.get_total_pnl()
        msg = f"Delta-neutral strategy closed. Final PnL: ${final_pnl:.2f}"
        print(f"[Executor] {msg}")

        return True, msg

    def close_delta_neutral_sync(
        self,
        strategy: DeltaNeutralStrategy
    ) -> Tuple[bool, str]:
        """
        Synchronous wrapper for close_delta_neutral().
        """
        return asyncio.run(self.close_delta_neutral(strategy))

    # ========== HEALTH CHECKS ==========

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all platforms.

        Returns:
            Dictionary mapping platform name to health status
        """
        print("[Executor] Running health checks...")
        results = {}

        for platform_name, platform in self.platforms.items():
            try:
                is_healthy = await platform.health_check()
                results[platform_name] = is_healthy
                status = "OK" if is_healthy else "FAILED"
                print(f"[Executor] {platform_name}: {status}")
            except Exception as e:
                results[platform_name] = False
                print(f"[Executor] {platform_name}: ERROR - {e}")

        return results

    def health_check_all_sync(self) -> Dict[str, bool]:
        """
        Synchronous wrapper for health_check_all().
        """
        return asyncio.run(self.health_check_all())

    # ========== BALANCE QUERIES ==========

    async def get_all_balances(self) -> Dict[str, float]:
        """
        Get account balances for all platforms.

        Returns:
            Dictionary mapping platform name to total equity (USD)
        """
        balances = {}

        for platform_name, platform in self.platforms.items():
            try:
                balance = await platform.get_account_balance()
                balances[platform_name] = balance.total_equity_usd
            except Exception as e:
                print(f"[Executor] Failed to fetch balance for {platform_name}: {e}")
                balances[platform_name] = 0.0

        return balances

    def get_all_balances_sync(self) -> Dict[str, float]:
        """
        Synchronous wrapper for get_all_balances().
        """
        return asyncio.run(self.get_all_balances())

    # ========== POSITION QUERIES ==========

    async def get_all_positions(self) -> Dict[str, List[Position]]:
        """
        Get all open positions across all platforms.

        Returns:
            Dictionary mapping platform name to list of positions
        """
        all_positions = {}

        for platform_name, platform in self.platforms.items():
            try:
                positions = await platform.get_positions()
                all_positions[platform_name] = positions
            except Exception as e:
                print(f"[Executor] Failed to fetch positions for {platform_name}: {e}")
                all_positions[platform_name] = []

        return all_positions

    def get_all_positions_sync(self) -> Dict[str, List[Position]]:
        """
        Synchronous wrapper for get_all_positions().
        """
        return asyncio.run(self.get_all_positions())
