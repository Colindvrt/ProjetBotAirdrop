"""
Position manager for real-time monitoring and management.

This module handles position tracking, PnL monitoring, and automated risk management.
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

from src.core.models import (
    DeltaNeutralStrategy,
    Position,
    AlertConfig,
    OrderSide
)
from src.platforms.base import BasePlatformAPI


@dataclass
class PositionUpdate:
    """Real-time position update event."""
    strategy_id: str
    timestamp: datetime
    total_pnl: float
    funding_accumulated: float
    unrealized_pnl: float
    long_position: Optional[Position]
    short_position: Optional[Position]
    is_at_risk: bool = False
    risk_message: Optional[str] = None


class PositionManager:
    """
    Manages open positions and monitors them in real-time.

    Features:
    - Real-time PnL tracking
    - Funding accumulation monitoring
    - Automated risk management (TP/SL/reversal)
    - Alert notifications
    - Position health monitoring
    """

    def __init__(
        self,
        long_platform: BasePlatformAPI,
        short_platform: BasePlatformAPI,
        strategy: DeltaNeutralStrategy,
        alert_config: Optional[AlertConfig] = None
    ):
        """
        Initialize position manager.

        Args:
            long_platform: Platform API for long position
            short_platform: Platform API for short position
            strategy: DeltaNeutralStrategy being managed
            alert_config: Alert configuration
        """
        self.long_platform = long_platform
        self.short_platform = short_platform
        self.strategy = strategy
        self.alert_config = alert_config or AlertConfig()

        self.is_monitoring = False
        self.monitoring_interval_seconds = 5  # Update every 5 seconds

        # Callbacks
        self.on_update_callback: Optional[Callable[[PositionUpdate], None]] = None
        self.on_alert_callback: Optional[Callable[[str, str], None]] = None

        # Tracking
        self.last_update: Optional[PositionUpdate] = None
        self.funding_history: List[float] = []

    def set_on_update_callback(self, callback: Callable[[PositionUpdate], None]):
        """
        Set callback for position updates.

        Args:
            callback: Function to call with PositionUpdate on each update
        """
        self.on_update_callback = callback

    def set_on_alert_callback(self, callback: Callable[[str, str], None]):
        """
        Set callback for alerts.

        Args:
            callback: Function to call with (alert_type, message)
        """
        self.on_alert_callback = callback

    async def _fetch_current_positions(self) -> tuple[Optional[Position], Optional[Position]]:
        """
        Fetch current positions from both platforms.

        Returns:
            Tuple of (long_position, short_position)
        """
        try:
            # Fetch positions from both platforms
            long_positions = await self.long_platform.get_positions()
            short_positions = await self.short_platform.get_positions()

            # Find our specific positions
            long_pos = None
            short_pos = None

            pair = self.strategy.opportunity.pair

            for pos in long_positions:
                if pos.pair == pair and pos.side == OrderSide.LONG:
                    long_pos = pos
                    break

            for pos in short_positions:
                if pos.pair == pair and pos.side == OrderSide.SHORT:
                    short_pos = pos
                    break

            return long_pos, short_pos

        except Exception as e:
            print(f"[PositionManager] Error fetching positions: {e}")
            return None, None

    async def _check_auto_close_conditions(
        self,
        total_pnl: float,
        current_spread: float
    ) -> tuple[bool, Optional[str]]:
        """
        Check if auto-close conditions are met.

        Args:
            total_pnl: Current total PnL
            current_spread: Current funding spread

        Returns:
            Tuple of (should_close, reason)
        """
        # Take profit
        if self.strategy.take_profit_usd and total_pnl >= self.strategy.take_profit_usd:
            return True, f"Take profit reached: ${total_pnl:.2f} >= ${self.strategy.take_profit_usd:.2f}"

        # Stop loss
        if self.strategy.stop_loss_usd and total_pnl <= self.strategy.stop_loss_usd:
            return True, f"Stop loss triggered: ${total_pnl:.2f} <= ${self.strategy.stop_loss_usd:.2f}"

        # Funding reversal
        if self.strategy.auto_close_on_reversal and current_spread < 0:
            return True, f"Funding reversed: spread now {current_spread:.6f}% (negative)"

        # Max hold time
        if self.strategy.max_hold_hours:
            time_held = datetime.now() - self.strategy.timestamp_created
            max_hold = timedelta(hours=self.strategy.max_hold_hours)
            if time_held >= max_hold:
                return True, f"Max hold time reached: {time_held.total_seconds()/3600:.1f}h"

        return False, None

    async def _send_alert(self, alert_type: str, message: str):
        """
        Send an alert notification.

        Args:
            alert_type: Type of alert (e.g., "profit", "loss", "reversal")
            message: Alert message
        """
        if not self.alert_config.enabled:
            return

        print(f"[ALERT] [{alert_type.upper()}] {message}")

        if self.on_alert_callback:
            try:
                self.on_alert_callback(alert_type, message)
            except Exception as e:
                print(f"[PositionManager] Alert callback error: {e}")

    async def _monitor_loop(self):
        """
        Main monitoring loop.

        Runs continuously while is_monitoring is True.
        """
        print(f"[PositionManager] Monitoring started for {self.strategy.opportunity.pair}")

        while self.is_monitoring:
            try:
                # Fetch current positions
                long_pos, short_pos = await self._fetch_current_positions()

                if not long_pos or not short_pos:
                    print("[PositionManager] Warning: One or both positions not found")
                    await asyncio.sleep(self.monitoring_interval_seconds)
                    continue

                # Update strategy positions
                self.strategy.long_position = long_pos
                self.strategy.short_position = short_pos

                # Calculate total PnL
                total_pnl = self.strategy.get_total_pnl()
                unrealized_pnl = long_pos.unrealized_pnl_usd + short_pos.unrealized_pnl_usd
                funding_accumulated = long_pos.funding_accumulated_usd + short_pos.funding_accumulated_usd

                # Track funding history
                self.funding_history.append(funding_accumulated)
                if len(self.funding_history) > 1000:  # Keep last 1000 samples
                    self.funding_history = self.funding_history[-1000:]

                # Calculate current spread
                current_spread = short_pos.unrealized_pnl_usd - long_pos.unrealized_pnl_usd

                # Check risk conditions
                is_at_risk = False
                risk_message = None

                # Check liquidation risk
                if self.alert_config.alert_on_liquidation_risk:
                    if long_pos.liquidation_price:
                        distance_to_liq_long = abs(
                            (long_pos.current_price - long_pos.liquidation_price) / long_pos.current_price
                        ) * 100
                        if distance_to_liq_long < self.alert_config.liquidation_risk_threshold_pct:
                            is_at_risk = True
                            risk_message = f"LONG position near liquidation: {distance_to_liq_long:.1f}% away"
                            await self._send_alert("liquidation_risk", risk_message)

                    if short_pos.liquidation_price:
                        distance_to_liq_short = abs(
                            (short_pos.current_price - short_pos.liquidation_price) / short_pos.current_price
                        ) * 100
                        if distance_to_liq_short < self.alert_config.liquidation_risk_threshold_pct:
                            is_at_risk = True
                            risk_message = f"SHORT position near liquidation: {distance_to_liq_short:.1f}% away"
                            await self._send_alert("liquidation_risk", risk_message)

                # Check PnL alerts
                if self.alert_config.alert_on_profit_threshold:
                    if total_pnl >= self.alert_config.profit_threshold_usd:
                        await self._send_alert(
                            "profit",
                            f"Profit threshold reached: ${total_pnl:.2f}"
                        )

                if self.alert_config.alert_on_loss_threshold:
                    if total_pnl <= self.alert_config.loss_threshold_usd:
                        await self._send_alert(
                            "loss",
                            f"Loss threshold reached: ${total_pnl:.2f}"
                        )

                # Check funding reversal
                if self.alert_config.alert_on_funding_reversal:
                    if current_spread < 0:
                        await self._send_alert(
                            "reversal",
                            f"Funding spread reversed: {current_spread:.6f}%"
                        )

                # Check auto-close conditions
                should_close, close_reason = await self._check_auto_close_conditions(
                    total_pnl, current_spread
                )

                if should_close:
                    await self._send_alert("auto_close", f"Auto-close triggered: {close_reason}")
                    self.is_monitoring = False
                    # Note: Actual closing should be handled by the executor

                # Create update object
                update = PositionUpdate(
                    strategy_id=str(id(self.strategy)),
                    timestamp=datetime.now(),
                    total_pnl=total_pnl,
                    funding_accumulated=funding_accumulated,
                    unrealized_pnl=unrealized_pnl,
                    long_position=long_pos,
                    short_position=short_pos,
                    is_at_risk=is_at_risk,
                    risk_message=risk_message
                )

                self.last_update = update

                # Call update callback
                if self.on_update_callback:
                    try:
                        self.on_update_callback(update)
                    except Exception as e:
                        print(f"[PositionManager] Update callback error: {e}")

                # Wait for next iteration
                await asyncio.sleep(self.monitoring_interval_seconds)

            except Exception as e:
                print(f"[PositionManager] Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval_seconds)

        print(f"[PositionManager] Monitoring stopped for {self.strategy.opportunity.pair}")

    def start_monitoring(self):
        """
        Start real-time monitoring.

        This spawns an async task that runs in the background.
        """
        if self.is_monitoring:
            print("[PositionManager] Already monitoring")
            return

        self.is_monitoring = True
        asyncio.create_task(self._monitor_loop())

    def stop_monitoring(self):
        """
        Stop real-time monitoring.
        """
        self.is_monitoring = False

    def get_current_state(self) -> Optional[PositionUpdate]:
        """
        Get the most recent position update.

        Returns:
            Latest PositionUpdate or None if no updates yet
        """
        return self.last_update

    def get_funding_history(self) -> List[float]:
        """
        Get funding accumulation history.

        Returns:
            List of funding accumulated values over time
        """
        return self.funding_history.copy()

    def calculate_roi(self) -> float:
        """
        Calculate return on investment.

        Returns:
            ROI as a percentage
        """
        if not self.last_update:
            return 0.0

        initial_investment = self.strategy.stake_size_usd
        total_pnl = self.last_update.total_pnl

        roi = (total_pnl / initial_investment) * 100
        return roi

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get comprehensive performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        if not self.last_update:
            return {}

        time_held = datetime.now() - self.strategy.timestamp_created
        hours_held = time_held.total_seconds() / 3600

        return {
            'total_pnl_usd': self.last_update.total_pnl,
            'unrealized_pnl_usd': self.last_update.unrealized_pnl,
            'funding_accumulated_usd': self.last_update.funding_accumulated,
            'roi_pct': self.calculate_roi(),
            'hours_held': hours_held,
            'pnl_per_hour': self.last_update.total_pnl / max(hours_held, 0.01),
            'is_at_risk': self.last_update.is_at_risk
        }


class PortfolioManager:
    """
    Manages multiple position managers for a portfolio of strategies.
    """

    def __init__(self):
        """Initialize portfolio manager."""
        self.position_managers: Dict[str, PositionManager] = {}

    def add_strategy(
        self,
        strategy_id: str,
        position_manager: PositionManager
    ):
        """
        Add a strategy to the portfolio.

        Args:
            strategy_id: Unique identifier for the strategy
            position_manager: PositionManager for this strategy
        """
        self.position_managers[strategy_id] = position_manager

    def remove_strategy(self, strategy_id: str):
        """
        Remove a strategy from the portfolio.

        Args:
            strategy_id: Strategy identifier
        """
        if strategy_id in self.position_managers:
            self.position_managers[strategy_id].stop_monitoring()
            del self.position_managers[strategy_id]

    def get_total_pnl(self) -> float:
        """
        Get total PnL across all strategies.

        Returns:
            Total PnL in USD
        """
        total = 0.0
        for manager in self.position_managers.values():
            state = manager.get_current_state()
            if state:
                total += state.total_pnl
        return total

    def get_portfolio_summary(self) -> Dict[str, any]:
        """
        Get summary of entire portfolio.

        Returns:
            Dictionary with portfolio metrics
        """
        total_pnl = 0.0
        total_funding = 0.0
        num_strategies = len(self.position_managers)
        num_at_risk = 0

        for manager in self.position_managers.values():
            state = manager.get_current_state()
            if state:
                total_pnl += state.total_pnl
                total_funding += state.funding_accumulated
                if state.is_at_risk:
                    num_at_risk += 1

        return {
            'total_pnl_usd': total_pnl,
            'total_funding_usd': total_funding,
            'num_strategies': num_strategies,
            'num_at_risk': num_at_risk,
            'active_managers': list(self.position_managers.keys())
        }

    def start_all_monitoring(self):
        """Start monitoring for all strategies."""
        for manager in self.position_managers.values():
            manager.start_monitoring()

    def stop_all_monitoring(self):
        """Stop monitoring for all strategies."""
        for manager in self.position_managers.values():
            manager.stop_monitoring()
