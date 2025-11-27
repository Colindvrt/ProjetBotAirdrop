"""
Paradex platform implementation.

This module implements the BasePlatformAPI for Paradex exchange.
"""

import requests
import re
from typing import List, Dict, Any
from datetime import datetime

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


class ParadexAPI(BasePlatformAPI):
    """
    Paradex exchange implementation.

    Features:
    - Funding rate data
    - Account balance
    - Market orders (via JWT authentication)
    - Position management
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Paradex API.

        Args:
            config: Dictionary with 'key' (wallet address) and 'secret' (JWT token)
        """
        super().__init__(config)

        self.wallet_address = config.get("key")  # 0x...
        self.jwt_token = config.get("secret")  # JWT token

        if not self.wallet_address or not self.jwt_token:
            raise ValueError("Paradex: missing 'key' (wallet address) or 'secret' (JWT token)")

        self.base_url = "https://api.prod.paradex.trade/v1"
        print(f"[Paradex] Connected with wallet: {self.wallet_address[:10]}...")
        print("[Paradex] Initialization complete")

    def _get_platform_name(self) -> str:
        """Return platform name."""
        return Platform.PARADEX.value

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.jwt_token}"
        }

    # ========== FUNDING DATA ==========

    async def get_funding_rates(self) -> List[FundingData]:
        """
        Fetch funding rates for all Paradex pairs.

        Returns:
            List of FundingData objects.
        """
        print("[Paradex] Fetching funding rates...")

        try:
            # Step 1: Get market metadata (leverage, period)
            details_map = await self._get_market_details()
            if not details_map:
                print("[Paradex] Failed to fetch market details")
                return []

            # Step 2: Get funding rates
            url = f"{self.base_url}/markets/summary"
            params = {"market": "ALL"}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            markets_list = data.get('results', [])
            funding_data_list = []

            for market_data in markets_list:
                pair_name = market_data.get('symbol', '')
                details = details_map.get(pair_name)

                if details:
                    rate_for_period = float(market_data.get('funding_rate', 0))
                    funding_period = details.get('period', 1)
                    hourly_funding_rate = rate_for_period / funding_period

                    # Standardize pair name (remove -USD-PERP)
                    pair_std = self.standardize_pair_name(pair_name)

                    funding_data = FundingData(
                        pair=pair_std,
                        rate_1h=hourly_funding_rate,
                        platform=self.platform_name,
                        max_leverage=details.get('leverage'),
                        timestamp=datetime.now()
                    )
                    funding_data_list.append(funding_data)

            print(f"[Paradex] Found {len(funding_data_list)} pairs")
            return funding_data_list

        except Exception as e:
            print(f"[Paradex] Error fetching funding rates: {e}")
            return []

    async def _get_market_details(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch market metadata (leverage, funding period).

        Returns:
            Dictionary mapping symbol to {period, leverage}
        """
        url = f"{self.base_url}/markets"
        headers = {"accept": "application/json"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            markets_list = data.get('results', [])
            details_map = {}

            if not markets_list:
                print("[Paradex] No markets found in /markets")
                return {}

            for market_data in markets_list:
                pair_name = market_data.get('symbol')

                if market_data.get('asset_kind') == 'PERP':
                    period = int(market_data.get('funding_period_hours', 1))
                    if period == 0:
                        period = 1

                    # Calculate max leverage from IMF (Initial Margin Fraction)
                    imf_base_str = market_data.get('delta1_cross_margin_params', {}).get('imf_base', '1.0')
                    try:
                        max_leverage = int(1 / float(imf_base_str))
                    except (ValueError, ZeroDivisionError):
                        max_leverage = 1

                    details_map[pair_name] = {'period': period, 'leverage': max_leverage}

            return details_map

        except Exception as e:
            print(f"[Paradex] Error fetching market details: {e}")
            return {}

    # ========== ACCOUNT INFORMATION ==========

    async def get_account_balance(self) -> AccountBalance:
        """
        Fetch account balance from Paradex.

        Returns:
            AccountBalance object.
        """
        try:
            url = f"{self.base_url}/account"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse account data
            equity = float(data.get('equity', 0))
            available_balance = float(data.get('available_balance', 0))
            margin_used = float(data.get('margin_used', 0))
            unrealized_pnl = float(data.get('unrealized_pnl', 0))

            return AccountBalance(
                platform=self.platform_name,
                total_equity_usd=equity,
                available_balance_usd=available_balance,
                margin_used_usd=margin_used,
                unrealized_pnl_usd=unrealized_pnl,
                timestamp=datetime.now()
            )

        except Exception as e:
            print(f"[Paradex] Error fetching balance: {e}")
            return AccountBalance(
                platform=self.platform_name,
                total_equity_usd=0.0,
                available_balance_usd=0.0,
                timestamp=datetime.now()
            )

    async def get_positions(self) -> List[Position]:
        """
        Fetch all open positions on Paradex.

        Returns:
            List of Position objects.
        """
        try:
            url = f"{self.base_url}/positions"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            data = response.json()

            positions_list = []
            results = data.get('results', [])

            for pos_data in results:
                market = pos_data.get('market', '')
                size_str = pos_data.get('size', '0')
                size = float(size_str)

                if size == 0:
                    continue

                side = OrderSide.LONG if size > 0 else OrderSide.SHORT
                entry_price = float(pos_data.get('average_entry_price', 0))
                unrealized_pnl = float(pos_data.get('unrealized_pnl', 0))
                leverage_val = int(float(pos_data.get('leverage', 1)))

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

            print(f"[Paradex] Found {len(positions_list)} open positions")
            return positions_list

        except Exception as e:
            print(f"[Paradex] Error fetching positions: {e}")
            return []

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
            # Convert standardized name to Paradex format
            pair_paradex = f"{pair}-USD-PERP"

            # Get market summary
            url = f"{self.base_url}/markets/summary"
            params = {"market": pair_paradex}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get('results'):
                raise ValueError(f"Market {pair_paradex} not found on Paradex")

            market_data = data['results'][0]
            mark_price = float(market_data.get('mark_price', 0))
            funding_rate = float(market_data.get('funding_rate', 0))

            # Get market details for leverage
            details_map = await self._get_market_details()
            details = details_map.get(pair_paradex, {})
            max_leverage = details.get('leverage', 1)
            period = details.get('period', 1)

            # Convert to hourly funding
            hourly_funding = funding_rate / period

            return MarketInfo(
                platform=self.platform_name,
                pair=pair,
                mark_price=mark_price,
                funding_rate_1h=hourly_funding,
                max_leverage=max_leverage,
                maker_fee_pct=0.02,
                taker_fee_pct=0.05,
                timestamp=datetime.now()
            )

        except Exception as e:
            print(f"[Paradex] Error getting market info: {e}")
            raise

    # ========== TRADING OPERATIONS ==========

    async def set_leverage(self, pair: str, leverage: int) -> bool:
        """
        Set leverage for a trading pair on Paradex.

        Note: Paradex may handle leverage differently. This is a placeholder.

        Args:
            pair: Trading pair
            leverage: Desired leverage

        Returns:
            True if successful
        """
        try:
            print(f"[Paradex] Setting leverage to {leverage}x for {pair}...")
            # Paradex may not have explicit leverage setting endpoint
            # It may be set automatically based on order size
            # This is a placeholder
            return True
        except Exception as e:
            print(f"[Paradex] Failed to set leverage: {e}")
            return False

    async def place_market_order(
        self,
        pair: str,
        side: OrderSide,
        size_usd: float,
        leverage: int
    ) -> OrderResult:
        """
        Place a market order on Paradex.

        Args:
            pair: Trading pair (e.g., "BTC")
            side: OrderSide.LONG or OrderSide.SHORT
            size_usd: Position size in USD (notional)
            leverage: Leverage to use

        Returns:
            OrderResult with execution details.
        """
        try:
            print(f"[Paradex] Placing {side.value.upper()} order for {pair}...")

            # Convert to Paradex format
            pair_paradex = f"{pair}-USD-PERP"

            # Get current price
            market_info = await self.get_market_info(pair)
            current_price = market_info.mark_price
            print(f"[Paradex] Current price: ${current_price:.2f}")

            # Calculate size in base currency
            size_base = size_usd / current_price

            # Set leverage
            await self.set_leverage(pair, leverage)

            # Prepare order
            order_payload = {
                "market": pair_paradex,
                "side": "BUY" if side == OrderSide.LONG else "SELL",
                "type": "MARKET",
                "size": str(size_base),
                "client_id": f"bot_{int(datetime.now().timestamp())}"
            }

            print(f"[Paradex] Sending order: {order_payload}")

            # Submit order
            url = f"{self.base_url}/orders"
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=order_payload,
                timeout=15
            )

            print(f"[Paradex] Response status: {response.status_code}")
            print(f"[Paradex] Response: {response.text}")

            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                order_id = response_data.get('id', 'unknown')

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
            else:
                error_msg = f"Order failed: HTTP {response.status_code} - {response.text}"
                return OrderResult(
                    success=False,
                    platform=self.platform_name,
                    pair=pair,
                    side=side,
                    error_message=error_msg,
                    timestamp=datetime.now()
                )

        except Exception as e:
            error_msg = f"Critical error: {str(e)}"
            print(f"[Paradex] {error_msg}")
            return OrderResult(
                success=False,
                platform=self.platform_name,
                pair=pair,
                side=side,
                error_message=error_msg,
                timestamp=datetime.now()
            )

    async def close_position(self, pair: str) -> OrderResult:
        """
        Close an open position for a trading pair.

        Args:
            pair: Trading pair

        Returns:
            OrderResult with closing execution details.
        """
        try:
            print(f"[Paradex] Closing position for {pair}...")

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
            print(f"[Paradex] {error_msg}")
            return OrderResult(
                success=False,
                platform=self.platform_name,
                pair=pair,
                side=OrderSide.LONG,
                error_message=error_msg,
                timestamp=datetime.now()
            )


# Register this platform with the factory
PlatformFactory.register("paradex", ParadexAPI)
