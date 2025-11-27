"""
Lighter platform implementation.

This module implements the BasePlatformAPI for Lighter exchange.
"""

import requests
from typing import List, Dict, Any
from datetime import datetime

try:
    import lighter
    LIGHTER_SDK_AVAILABLE = True
except ImportError:
    print("ERROR: lighter SDK not installed. Run: pip install lighter")
    LIGHTER_SDK_AVAILABLE = False

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


class LighterAPI(BasePlatformAPI):
    """
    Lighter exchange implementation.

    Features:
    - Funding rate data
    - Account balance (async SDK)
    - Market orders (async SDK)
    - Position management
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Lighter API.

        Args:
            config: Dictionary with 'key' (private key), 'account_index', 'api_key_index'
        """
        super().__init__(config)

        if not LIGHTER_SDK_AVAILABLE:
            raise ImportError("Lighter SDK not available")

        self.base_url = "https://mainnet.zklighter.elliot.ai"
        self.api_private_key = config.get("key")
        self.account_index_str = config.get("account_index")
        self.api_key_index_str = config.get("api_key_index")

        if not self.api_private_key or not self.account_index_str or not self.api_key_index_str:
            raise ValueError("Lighter: missing 'key', 'account_index', or 'api_key_index'")

        try:
            self.account_index = int(self.account_index_str)
            self.api_key_index = int(self.api_key_index_str)
        except ValueError:
            raise ValueError("Lighter: account_index or api_key_index must be integers")

        # Map from standardized pair to orderbook ID
        self.pair_to_orderbook = {}  # Will be populated on demand

        print(f"[Lighter] Initialized for Account {self.account_index} / Key {self.api_key_index}")

    def _get_platform_name(self) -> str:
        """Return platform name."""
        return Platform.LIGHTER.value

    async def _get_signer_client(self):
        """
        Create and return a SignerClient instance.

        Returns:
            lighter.SignerClient instance
        """
        client = lighter.SignerClient(
            url=self.base_url,
            private_key=self.api_private_key,
            account_index=self.account_index,
            api_key_index=self.api_key_index
        )
        return client

    # ========== FUNDING DATA ==========

    async def get_funding_rates(self) -> List[FundingData]:
        """
        Fetch funding rates for all Lighter pairs.

        Returns:
            List of FundingData objects.
        """
        print("[Lighter] Fetching funding rates...")

        try:
            # Step 1: Get leverage details
            details_map = await self._get_leverage_details()
            if not details_map:
                print("[Lighter] Failed to fetch leverage details")
                details_map = {}

            # Step 2: Get funding rates
            url = f"{self.base_url}/api/v1/funding-rates"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            all_rates_list = data.get('funding_rates', [])
            funding_data_list = []

            for item in all_rates_list:
                if item.get('exchange') == 'lighter':
                    pair_name = item.get('symbol')
                    max_leverage = details_map.get(pair_name, 1)

                    if max_leverage > 1:
                        eight_hour_rate = float(item.get('rate', 0))
                        hourly_funding_rate = eight_hour_rate / 8

                        # Standardize pair name
                        pair_std = self.standardize_pair_name(pair_name)

                        funding_data = FundingData(
                            pair=pair_std,
                            rate_1h=hourly_funding_rate,
                            platform=self.platform_name,
                            max_leverage=max_leverage,
                            timestamp=datetime.now()
                        )
                        funding_data_list.append(funding_data)

            print(f"[Lighter] Found {len(funding_data_list)} pairs")
            return funding_data_list

        except Exception as e:
            print(f"[Lighter] Error fetching funding rates: {e}")
            return []

    async def _get_leverage_details(self) -> Dict[str, int]:
        """
        Fetch leverage information for all markets.

        Returns:
            Dictionary mapping symbol to max_leverage
        """
        url = f"{self.base_url}/api/v1/orderBookDetails"
        headers = {"accept": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            markets_list = data.get('order_book_details', [])
            details_map = {}

            if not markets_list:
                print("[Lighter] No orderBookDetails found")
                return {}

            for market_data in markets_list:
                pair_name = market_data.get('symbol')
                margin_fraction_str = market_data.get('min_initial_margin_fraction')

                if margin_fraction_str:
                    try:
                        margin_fraction = float(margin_fraction_str)
                        if margin_fraction > 0:
                            max_leverage = int(10000 / margin_fraction)
                        else:
                            max_leverage = 1
                    except (ValueError, ZeroDivisionError, TypeError):
                        max_leverage = 1
                else:
                    max_leverage = 1

                details_map[pair_name] = max_leverage

                # Also populate pair_to_orderbook mapping
                order_book_id = market_data.get('order_book_id')
                if order_book_id:
                    pair_std = self.standardize_pair_name(pair_name)
                    self.pair_to_orderbook[pair_std] = order_book_id

            print(f"[Lighter] Fetched leverage for {len(details_map)} markets")
            return details_map

        except Exception as e:
            print(f"[Lighter] Error fetching leverage details: {e}")
            return {}

    # ========== ACCOUNT INFORMATION ==========

    async def get_account_balance(self) -> AccountBalance:
        """
        Fetch account balance from Lighter.

        Returns:
            AccountBalance object.
        """
        client = None
        try:
            client = await self._get_signer_client()
            response, err = await client.get_account()

            if err is not None:
                raise Exception(f"Lighter API error: {err}")

            target_sub_account_id = f"{self.account_index}-{self.api_key_index}"

            if response.sub_accounts and target_sub_account_id in response.sub_accounts:
                sub_account = response.sub_accounts[target_sub_account_id]
                balance_str = sub_account.portfolio_value
                equity = float(balance_str)

                # For available balance, we'd need margin used info
                # For now, assume all equity is available (conservative)
                return AccountBalance(
                    platform=self.platform_name,
                    total_equity_usd=equity,
                    available_balance_usd=equity,
                    margin_used_usd=0.0,
                    timestamp=datetime.now()
                )
            else:
                print(f"[Lighter] Sub-account {target_sub_account_id} not found")
                return AccountBalance(
                    platform=self.platform_name,
                    total_equity_usd=0.0,
                    available_balance_usd=0.0,
                    timestamp=datetime.now()
                )

        except Exception as e:
            print(f"[Lighter] Error fetching balance: {e}")
            return AccountBalance(
                platform=self.platform_name,
                total_equity_usd=0.0,
                available_balance_usd=0.0,
                timestamp=datetime.now()
            )
        finally:
            if client:
                await client.close()

    async def get_positions(self) -> List[Position]:
        """
        Fetch all open positions on Lighter.

        Returns:
            List of Position objects.
        """
        client = None
        try:
            client = await self._get_signer_client()
            response, err = await client.get_account()

            if err is not None:
                raise Exception(f"Lighter API error: {err}")

            positions_list = []
            target_sub_account_id = f"{self.account_index}-{self.api_key_index}"

            if response.sub_accounts and target_sub_account_id in response.sub_accounts:
                sub_account = response.sub_accounts[target_sub_account_id]

                if hasattr(sub_account, 'positions') and sub_account.positions:
                    for pos_data in sub_account.positions:
                        order_book_id = pos_data.order_book_id
                        size_str = pos_data.size
                        size = float(size_str)

                        if size == 0:
                            continue

                        side = OrderSide.LONG if size > 0 else OrderSide.SHORT
                        entry_price = float(pos_data.average_entry_price) if hasattr(pos_data, 'average_entry_price') else 0.0
                        unrealized_pnl = float(pos_data.unrealized_pnl) if hasattr(pos_data, 'unrealized_pnl') else 0.0

                        # Calculate notional size
                        size_usd = abs(size) * entry_price

                        # Try to get pair name from orderbook ID
                        # (This requires mapping, which we may not have)
                        pair = order_book_id  # Fallback to orderbook ID

                        position = Position(
                            platform=self.platform_name,
                            pair=pair,
                            side=side,
                            size_usd=size_usd,
                            leverage=1,  # Lighter doesn't expose leverage in position
                            entry_price=entry_price,
                            unrealized_pnl_usd=unrealized_pnl,
                            timestamp_opened=datetime.now(),
                            timestamp_updated=datetime.now()
                        )
                        positions_list.append(position)

            print(f"[Lighter] Found {len(positions_list)} open positions")
            return positions_list

        except Exception as e:
            print(f"[Lighter] Error fetching positions: {e}")
            return []
        finally:
            if client:
                await client.close()

    # ========== MARKET DATA ==========

    async def get_market_info(self, pair: str) -> MarketInfo:
        """
        Get market information for a specific pair.

        Args:
            pair: Trading pair (e.g., "BTC")

        Returns:
            MarketInfo object.
        """
        try:
            # Get leverage details to populate mapping
            if not self.pair_to_orderbook:
                await self._get_leverage_details()

            # Find orderbook ID for this pair
            order_book_id = self.pair_to_orderbook.get(pair)
            if not order_book_id:
                raise ValueError(f"Pair {pair} not found on Lighter")

            # Get market data (using REST API for simplicity)
            url = f"{self.base_url}/api/v1/orderBookDetails"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            for market_data in data.get('order_book_details', []):
                if market_data.get('order_book_id') == order_book_id:
                    # Extract info
                    margin_fraction = float(market_data.get('min_initial_margin_fraction', 1.0))
                    max_leverage = int(10000 / margin_fraction) if margin_fraction > 0 else 1

                    # For mark price, we'd need another API call
                    # Placeholder for now
                    mark_price = 0.0

                    return MarketInfo(
                        platform=self.platform_name,
                        pair=pair,
                        mark_price=mark_price,
                        funding_rate_1h=0.0,  # Would need funding-rates API
                        max_leverage=max_leverage,
                        maker_fee_pct=0.02,
                        taker_fee_pct=0.05,
                        timestamp=datetime.now()
                    )

            raise ValueError(f"Market info not found for {pair}")

        except Exception as e:
            print(f"[Lighter] Error getting market info: {e}")
            raise

    # ========== TRADING OPERATIONS ==========

    async def set_leverage(self, pair: str, leverage: int) -> bool:
        """
        Set leverage for a trading pair on Lighter.

        Note: Lighter may handle leverage differently via margin.

        Args:
            pair: Trading pair
            leverage: Desired leverage

        Returns:
            True if successful
        """
        try:
            print(f"[Lighter] Setting leverage to {leverage}x for {pair}...")
            # Lighter uses margin fractions, not explicit leverage setting
            # This is a placeholder
            return True
        except Exception as e:
            print(f"[Lighter] Failed to set leverage: {e}")
            return False

    async def place_market_order(
        self,
        pair: str,
        side: OrderSide,
        size_usd: float,
        leverage: int
    ) -> OrderResult:
        """
        Place a market order on Lighter.

        Args:
            pair: Trading pair (e.g., "BTC")
            side: OrderSide.LONG or OrderSide.SHORT
            size_usd: Position size in USD (notional)
            leverage: Leverage to use

        Returns:
            OrderResult with execution details.
        """
        client = None
        try:
            print(f"[Lighter] Placing {side.value.upper()} order for {pair}...")

            # Get orderbook ID
            if not self.pair_to_orderbook:
                await self._get_leverage_details()

            order_book_id = self.pair_to_orderbook.get(pair)
            if not order_book_id:
                raise ValueError(f"Pair {pair} not found on Lighter")

            # Set leverage (placeholder)
            await self.set_leverage(pair, leverage)

            # Create client
            client = await self._get_signer_client()

            # Place order
            lighter_side = "LONG" if side == OrderSide.LONG else "SHORT"
            size_str = str(int(size_usd))  # Lighter expects integer USD size

            print(f"[Lighter] Sending order: {size_str} USD {lighter_side} on {order_book_id}")

            response, err = await client.create_market_order(
                order_book_id=order_book_id,
                size=size_str,
                side=lighter_side
            )

            if err is not None:
                raise Exception(f"Order failed: {err}")

            order_id = response.order_id if response else "unknown"
            print(f"[Lighter] Order placed successfully: {order_id}")

            return OrderResult(
                success=True,
                platform=self.platform_name,
                pair=pair,
                side=side,
                order_id=order_id,
                filled_size_usd=size_usd,
                timestamp=datetime.now()
            )

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            print(f"[Lighter] {error_msg}")
            return OrderResult(
                success=False,
                platform=self.platform_name,
                pair=pair,
                side=side,
                error_message=error_msg,
                timestamp=datetime.now()
            )
        finally:
            if client:
                await client.close()

    async def close_position(self, pair: str) -> OrderResult:
        """
        Close an open position for a trading pair.

        Args:
            pair: Trading pair

        Returns:
            OrderResult with closing execution details.
        """
        try:
            print(f"[Lighter] Closing position for {pair}...")

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
            print(f"[Lighter] {error_msg}")
            return OrderResult(
                success=False,
                platform=self.platform_name,
                pair=pair,
                side=OrderSide.LONG,
                error_message=error_msg,
                timestamp=datetime.now()
            )


# Register this platform with the factory
PlatformFactory.register("lighter", LighterAPI)
