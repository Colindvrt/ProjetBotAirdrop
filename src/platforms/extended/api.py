"""
Extended (X10) platform implementation on Starknet.

This module implements the BasePlatformAPI for Extended/X10 exchange.
"""

import re
from typing import List, Dict, Any
from datetime import datetime

try:
    from x10_starknet.models.config import MAINNET_CONFIG
    from x10_starknet.public_client import PublicClient
    from x10_starknet.trading_client import TradingClient
    from x10_starknet.models.account import StarkPerpetualAccount
    from x10_starknet.models.order import OrderSide as X10OrderSide
    X10_SDK_AVAILABLE = True
except ImportError:
    print("ERROR: x10-python-trading-starknet not installed. Run: pip install x10-python-trading-starknet")
    X10_SDK_AVAILABLE = False

from src.platforms.base import BasePlatformAPI, PlatformFactory
from src.core.models import (
    FundingData,
    AccountBalance,
    OrderResult,
    Position,
    MarketInfo,
    OrderSide,
    OrderStatus,
    Platform
)


class ExtendedAPI(BasePlatformAPI):
    """
    Extended (X10) exchange implementation on Starknet.

    Features:
    - Funding rate data
    - Account balance (async SDK)
    - Market orders (async SDK with Starknet signatures)
    - Position management
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Extended API.

        Args:
            config: Dictionary with 'api_key', 'public_key', 'private_key', 'vault_id'
        """
        super().__init__(config)

        if not X10_SDK_AVAILABLE:
            raise ImportError("X10 Starknet SDK not available")

        self.api_key = config.get("api_key")
        self.public_key = config.get("public_key")
        self.private_key = config.get("private_key")
        self.vault_id_str = config.get("vault_id")

        if not all([self.api_key, self.public_key, self.private_key, self.vault_id_str]):
            raise ValueError("Extended: missing api_key, public_key, private_key, or vault_id")

        try:
            self.vault_id = int(self.vault_id_str)
        except ValueError:
            raise ValueError("Extended: vault_id must be an integer")

        # Initialize Starknet account
        self.stark_account = StarkPerpetualAccount(
            api_key=self.api_key,
            public_key=self.public_key,
            private_key=self.private_key,
            vault=self.vault_id,
        )

        # Initialize trading client
        self.trading_client = TradingClient(MAINNET_CONFIG, self.stark_account)

        print(f"[Extended] Initialized for vault {self.vault_id}")

    def _get_platform_name(self) -> str:
        """Return platform name."""
        return Platform.EXTENDED.value

    # ========== FUNDING DATA ==========

    async def get_funding_rates(self) -> List[FundingData]:
        """
        Fetch funding rates for all Extended pairs.

        Returns:
            List of FundingData objects.
        """
        print("[Extended] Fetching funding rates...")
        client = None

        try:
            # Use public client (no authentication needed)
            client = PublicClient(MAINNET_CONFIG)

            # Get markets dictionary
            markets_dict = await client.get_markets()

            if not markets_dict:
                print("[Extended] No markets found")
                return []

            funding_data_list = []

            for pair_name_api, market_data in markets_dict.items():
                # Skip inactive markets
                if market_data.status != 'ACTIVE':
                    continue

                stats = market_data.market_stats
                config = market_data.trading_config

                hourly_funding_rate = stats.funding_rate
                max_leverage = config.max_leverage

                if hourly_funding_rate is not None and max_leverage is not None:
                    try:
                        # Extract base pair name (e.g., "BTC" from "BTC-USD-PERP")
                        match = re.match(r"^[A-Z0-9]+", pair_name_api)
                        pair_std = match.group(0) if match else pair_name_api

                        funding_data = FundingData(
                            pair=pair_std,
                            rate_1h=float(hourly_funding_rate),
                            platform=self.platform_name,
                            max_leverage=int(max_leverage),
                            timestamp=datetime.now()
                        )
                        funding_data_list.append(funding_data)
                    except Exception as e:
                        print(f"[Extended] Skipping pair {pair_name_api}: {e}")

            print(f"[Extended] Found {len(funding_data_list)} pairs")
            return funding_data_list

        except Exception as e:
            print(f"[Extended] Error fetching funding rates: {e}")
            return []
        finally:
            if client:
                await client.close_session()

    # ========== ACCOUNT INFORMATION ==========

    async def get_account_balance(self) -> AccountBalance:
        """
        Fetch account balance from Extended.

        Returns:
            AccountBalance object.
        """
        try:
            # Get account overview
            account_overview = await self.trading_client.get_account_overview()

            if account_overview and account_overview.balance is not None:
                # equity includes unrealized PnL
                total_equity = float(account_overview.equity)
                wallet_balance = float(account_overview.balance)
                unrealized_pnl = total_equity - wallet_balance

                # Available balance (simplified)
                available_balance = wallet_balance

                return AccountBalance(
                    platform=self.platform_name,
                    total_equity_usd=total_equity,
                    available_balance_usd=available_balance,
                    margin_used_usd=0.0,  # Not provided in current API
                    unrealized_pnl_usd=unrealized_pnl,
                    timestamp=datetime.now()
                )
            else:
                print("[Extended] Invalid account overview structure")
                return AccountBalance(
                    platform=self.platform_name,
                    total_equity_usd=0.0,
                    available_balance_usd=0.0,
                    timestamp=datetime.now()
                )

        except Exception as e:
            print(f"[Extended] Error fetching balance: {e}")
            return AccountBalance(
                platform=self.platform_name,
                total_equity_usd=0.0,
                available_balance_usd=0.0,
                timestamp=datetime.now()
            )
        finally:
            if self.trading_client:
                await self.trading_client.close_session()

    async def get_positions(self) -> List[Position]:
        """
        Fetch all open positions on Extended.

        Returns:
            List of Position objects.
        """
        try:
            # Get positions from trading client
            positions_response = await self.trading_client.get_positions()
            positions_list = []

            if positions_response and hasattr(positions_response, 'positions'):
                for pos_data in positions_response.positions:
                    market = pos_data.market
                    size = float(pos_data.size)

                    if size == 0:
                        continue

                    side = OrderSide.LONG if size > 0 else OrderSide.SHORT
                    entry_price = float(pos_data.average_entry_price) if hasattr(pos_data, 'average_entry_price') else 0.0
                    unrealized_pnl = float(pos_data.unrealized_pnl) if hasattr(pos_data, 'unrealized_pnl') else 0.0
                    leverage_val = int(float(pos_data.leverage)) if hasattr(pos_data, 'leverage') else 1

                    # Calculate notional size
                    size_usd = abs(size) * entry_price

                    # Standardize pair name
                    pair_std = self.standardize_pair_name(market)

                    position = Position(
                        platform=self.platform_name,
                        pair=pair_std,
                        side=side,
                        size_usd=size_usd,
                        leverage=leverage_val,
                        entry_price=entry_price,
                        unrealized_pnl_usd=unrealized_pnl,
                        timestamp_opened=datetime.now(),
                        timestamp_updated=datetime.now()
                    )
                    positions_list.append(position)

            print(f"[Extended] Found {len(positions_list)} open positions")
            return positions_list

        except Exception as e:
            print(f"[Extended] Error fetching positions: {e}")
            return []
        finally:
            if self.trading_client:
                await self.trading_client.close_session()

    # ========== MARKET DATA ==========

    async def get_market_info(self, pair: str) -> MarketInfo:
        """
        Get market information for a specific pair.

        Args:
            pair: Trading pair (e.g., "BTC")

        Returns:
            MarketInfo object.
        """
        client = None
        try:
            # Use public client
            client = PublicClient(MAINNET_CONFIG)
            markets_dict = await client.get_markets()

            # Find market (try different formats)
            market_key = f"{pair}-USD-PERP"
            market_data = markets_dict.get(market_key)

            if not market_data:
                raise ValueError(f"Market {pair} not found on Extended")

            stats = market_data.market_stats
            config = market_data.trading_config

            mark_price = float(stats.mark_price)
            funding_rate = float(stats.funding_rate)
            max_leverage = int(config.max_leverage)

            return MarketInfo(
                platform=self.platform_name,
                pair=pair,
                mark_price=mark_price,
                funding_rate_1h=funding_rate,
                max_leverage=max_leverage,
                maker_fee_pct=0.02,
                taker_fee_pct=0.05,
                timestamp=datetime.now()
            )

        except Exception as e:
            print(f"[Extended] Error getting market info: {e}")
            raise
        finally:
            if client:
                await client.close_session()

    # ========== TRADING OPERATIONS ==========

    async def set_leverage(self, pair: str, leverage: int) -> bool:
        """
        Set leverage for a trading pair on Extended.

        Args:
            pair: Trading pair
            leverage: Desired leverage

        Returns:
            True if successful
        """
        try:
            print(f"[Extended] Setting leverage to {leverage}x for {pair}...")

            # Get market ID
            market_key = f"{pair}-USD-PERP"
            client = PublicClient(MAINNET_CONFIG)
            markets_dict = await client.get_markets()
            await client.close_session()

            market_data = markets_dict.get(market_key)
            if not market_data:
                raise ValueError(f"Market {pair} not found")

            market_id = market_data.market_id

            # Set leverage via trading client
            result = await self.trading_client.set_leverage(
                market_id=market_id,
                leverage=leverage
            )

            print(f"[Extended] Leverage set successfully")
            return True

        except Exception as e:
            print(f"[Extended] Failed to set leverage: {e}")
            return False
        finally:
            if self.trading_client:
                await self.trading_client.close_session()

    async def place_market_order(
        self,
        pair: str,
        side: OrderSide,
        size_usd: float,
        leverage: int
    ) -> OrderResult:
        """
        Place a market order on Extended.

        Args:
            pair: Trading pair (e.g., "BTC")
            side: OrderSide.LONG or OrderSide.SHORT
            size_usd: Position size in USD (notional)
            leverage: Leverage to use

        Returns:
            OrderResult with execution details.
        """
        try:
            print(f"[Extended] Placing {side.value.upper()} order for {pair}...")

            # Get market info
            market_info = await self.get_market_info(pair)
            current_price = market_info.mark_price
            print(f"[Extended] Current price: ${current_price:.2f}")

            # Calculate size in base currency
            size_base = size_usd / current_price

            # Get market ID
            market_key = f"{pair}-USD-PERP"
            client = PublicClient(MAINNET_CONFIG)
            markets_dict = await client.get_markets()
            await client.close_session()

            market_data = markets_dict.get(market_key)
            if not market_data:
                raise ValueError(f"Market {pair} not found")

            market_id = market_data.market_id

            # Set leverage
            await self.set_leverage(pair, leverage)

            # Convert OrderSide to X10OrderSide
            x10_side = X10OrderSide.BUY if side == OrderSide.LONG else X10OrderSide.SELL

            # Place market order
            print(f"[Extended] Sending order: {size_base} {pair} {side.value}")
            result = await self.trading_client.create_market_order(
                market_id=market_id,
                side=x10_side,
                size=size_base
            )

            order_id = result.order_id if result and hasattr(result, 'order_id') else "unknown"
            print(f"[Extended] Order placed successfully: {order_id}")

            return OrderResult(
                success=True,
                platform=self.platform_name,
                pair=pair,
                side=side,
                order_id=order_id,
                filled_size_usd=size_usd,
                filled_price=current_price,
                timestamp=datetime.now()
            )

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            print(f"[Extended] {error_msg}")
            return OrderResult(
                success=False,
                platform=self.platform_name,
                pair=pair,
                side=side,
                error_message=error_msg,
                timestamp=datetime.now()
            )
        finally:
            if self.trading_client:
                await self.trading_client.close_session()

    async def close_position(self, pair: str) -> OrderResult:
        """
        Close an open position for a trading pair.

        Args:
            pair: Trading pair

        Returns:
            OrderResult with closing execution details.
        """
        try:
            print(f"[Extended] Closing position for {pair}...")

            # Get current position
            positions = await self.get_positions()
            position_to_close = None

            for pos in positions:
                if pos.pair == pair:
                    position_to_close = pos
                    break

            if not position_to_close:
                return OrderResult(
                    success=False,
                    platform=self.platform_name,
                    pair=pair,
                    side=OrderSide.LONG,
                    error_message=f"No open position found for {pair}",
                    timestamp=datetime.now()
                )

            # Close by placing opposite order
            opposite_side = OrderSide.SHORT if position_to_close.side == OrderSide.LONG else OrderSide.LONG

            return await self.place_market_order(
                pair=pair,
                side=opposite_side,
                size_usd=position_to_close.size_usd,
                leverage=position_to_close.leverage
            )

        except Exception as e:
            error_msg = f"Error closing position: {str(e)}"
            print(f"[Extended] {error_msg}")
            return OrderResult(
                success=False,
                platform=self.platform_name,
                pair=pair,
                side=OrderSide.LONG,
                error_message=error_msg,
                timestamp=datetime.now()
            )


# Register this platform with the factory
PlatformFactory.register("extended", ExtendedAPI)
