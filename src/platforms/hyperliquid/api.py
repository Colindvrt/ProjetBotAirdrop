"""
Hyperliquid platform implementation.

This module implements the BasePlatformAPI for Hyperliquid exchange.
"""

import requests
from typing import List, Dict, Any
from datetime import datetime
from eth_account import Account

try:
    from hyperliquid.exchange import Exchange
    from hyperliquid.info import Info
    from hyperliquid.utils import constants
    HYPERLIQUID_SDK_AVAILABLE = True
except ImportError:
    print("ERROR: hyperliquid-python-sdk not installed. Run: pip install hyperliquid-python-sdk")
    HYPERLIQUID_SDK_AVAILABLE = False

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


class HyperliquidAPI(BasePlatformAPI):
    """
    Hyperliquid exchange implementation.

    Fully functional with:
    - Funding rate data
    - Account balance
    - Market orders (long/short)
    - Position management
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Hyperliquid API.

        Args:
            config: Dictionary with 'secret' (private key)
        """
        super().__init__(config)

        if not HYPERLIQUID_SDK_AVAILABLE:
            raise ImportError("Hyperliquid SDK not available")

        self.private_key = config.get("secret")
        if not self.private_key:
            raise ValueError("Hyperliquid: missing 'secret' (private key)")

        try:
            self.account = Account.from_key(self.private_key)
            self.address = self.account.address
            print(f"[Hyperliquid] Connected as: {self.address}")
        except Exception as e:
            raise ValueError(f"Hyperliquid: invalid private key: {e}")

        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self.exchange = Exchange(self.account, constants.MAINNET_API_URL)
        print("[Hyperliquid] Initialization complete")

    def _get_platform_name(self) -> str:
        """Return platform name."""
        return Platform.HYPERLIQUID.value

    # ========== FUNDING DATA ==========

    async def get_funding_rates(self) -> List[FundingData]:
        """
        Fetch funding rates for all Hyperliquid pairs.

        Returns:
            List of FundingData objects.
        """
        print("[Hyperliquid] Fetching funding rates...")
        url = "https://api.hyperliquid.xyz/info"
        payload = {"type": "metaAndAssetCtxs"}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            asset_metadata = data[0]['universe']
            asset_contexts = data[1]

            funding_data_list = []
            for i, asset_context in enumerate(asset_contexts):
                pair_name = asset_metadata[i].get('name')
                hourly_funding_rate = float(asset_context.get('funding', 0))
                max_leverage = int(asset_metadata[i].get('maxLeverage', 1))

                funding_data = FundingData(
                    pair=pair_name,
                    rate_1h=hourly_funding_rate,
                    platform=self.platform_name,
                    max_leverage=max_leverage,
                    timestamp=datetime.now()
                )
                funding_data_list.append(funding_data)

            print(f"[Hyperliquid] Found {len(funding_data_list)} pairs")
            return funding_data_list

        except Exception as e:
            print(f"[Hyperliquid] Error fetching funding rates: {e}")
            return []

    # ========== ACCOUNT INFORMATION ==========

    async def get_account_balance(self) -> AccountBalance:
        """
        Fetch account balance from Hyperliquid.

        Returns:
            AccountBalance object with current account state.
        """
        try:
            user_state = self.info.user_state(self.address)

            if "marginSummary" in user_state:
                margin_summary = user_state["marginSummary"]
                total_equity = float(margin_summary.get("accountValue", 0))
                total_margin_used = float(margin_summary.get("totalMarginUsed", 0))
                unrealized_pnl = float(margin_summary.get("totalNtlPos", 0))

                # Available = Total - Used
                available_balance = total_equity - total_margin_used

                return AccountBalance(
                    platform=self.platform_name,
                    total_equity_usd=total_equity,
                    available_balance_usd=max(0, available_balance),
                    margin_used_usd=total_margin_used,
                    unrealized_pnl_usd=unrealized_pnl,
                    timestamp=datetime.now()
                )
            else:
                # No positions, return zero balance
                return AccountBalance(
                    platform=self.platform_name,
                    total_equity_usd=0.0,
                    available_balance_usd=0.0,
                    timestamp=datetime.now()
                )

        except Exception as e:
            print(f"[Hyperliquid] Error fetching balance: {e}")
            return AccountBalance(
                platform=self.platform_name,
                total_equity_usd=0.0,
                available_balance_usd=0.0,
                timestamp=datetime.now()
            )

    async def get_positions(self) -> List[Position]:
        """
        Fetch all open positions on Hyperliquid.

        Returns:
            List of Position objects.
        """
        try:
            user_state = self.info.user_state(self.address)
            positions_list = []

            if "assetPositions" in user_state:
                for asset_pos in user_state["assetPositions"]:
                    position_data = asset_pos.get("position", {})
                    if not position_data:
                        continue

                    pair = position_data.get("coin")
                    size_str = position_data.get("szi")
                    entry_px = float(position_data.get("entryPx", 0))
                    leverage_str = position_data.get("leverage", {}).get("value", "1")
                    unrealized_pnl = float(position_data.get("unrealizedPnl", 0))
                    liquidation_px = position_data.get("liquidationPx")

                    if not size_str or float(size_str) == 0:
                        continue

                    size = float(size_str)
                    side = OrderSide.LONG if size > 0 else OrderSide.SHORT
                    size_abs = abs(size)

                    # Calculate notional size
                    size_usd = size_abs * entry_px

                    position = Position(
                        platform=self.platform_name,
                        pair=pair,
                        side=side,
                        size_usd=size_usd,
                        leverage=int(float(leverage_str)),
                        entry_price=entry_px,
                        unrealized_pnl_usd=unrealized_pnl,
                        liquidation_price=float(liquidation_px) if liquidation_px else None,
                        timestamp_opened=datetime.now(),
                        timestamp_updated=datetime.now()
                    )
                    positions_list.append(position)

            print(f"[Hyperliquid] Found {len(positions_list)} open positions")
            return positions_list

        except Exception as e:
            print(f"[Hyperliquid] Error fetching positions: {e}")
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
            # Get current price
            all_prices = self.info.all_mids()
            if pair not in all_prices:
                raise ValueError(f"Pair '{pair}' not found on Hyperliquid")

            mark_price = float(all_prices[pair])

            # Get metadata for this pair
            url = "https://api.hyperliquid.xyz/info"
            payload = {"type": "metaAndAssetCtxs"}
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            asset_metadata = data[0]['universe']
            asset_contexts = data[1]

            for i, meta in enumerate(asset_metadata):
                if meta.get('name') == pair:
                    max_leverage = int(meta.get('maxLeverage', 1))
                    funding_rate = float(asset_contexts[i].get('funding', 0))

                    return MarketInfo(
                        platform=self.platform_name,
                        pair=pair,
                        mark_price=mark_price,
                        funding_rate_1h=funding_rate,
                        max_leverage=max_leverage,
                        maker_fee_pct=0.02,
                        taker_fee_pct=0.03,
                        timestamp=datetime.now()
                    )

            raise ValueError(f"Metadata not found for pair '{pair}'")

        except Exception as e:
            print(f"[Hyperliquid] Error getting market info: {e}")
            raise

    # ========== TRADING OPERATIONS ==========

    async def set_leverage(self, pair: str, leverage: int) -> bool:
        """
        Set leverage for a trading pair.

        Args:
            pair: Trading pair
            leverage: Desired leverage (1-50)

        Returns:
            True if successful, False otherwise.
        """
        try:
            print(f"[Hyperliquid] Setting leverage to {leverage}x for {pair}...")
            response = self.exchange.update_leverage(int(leverage), pair)
            print(f"[Hyperliquid] Leverage response: {response}")
            return True
        except Exception as e:
            print(f"[Hyperliquid] Failed to set leverage: {e}")
            return False

    async def place_market_order(
        self,
        pair: str,
        side: OrderSide,
        size_usd: float,
        leverage: int
    ) -> OrderResult:
        """
        Place a market order on Hyperliquid.

        Args:
            pair: Trading pair (e.g., "BTC")
            side: OrderSide.LONG or OrderSide.SHORT
            size_usd: Position size in USD (notional)
            leverage: Leverage to use (1-50)

        Returns:
            OrderResult with execution details.
        """
        try:
            print(f"[Hyperliquid] Placing {side.value.upper()} order for {pair}...")

            # Get current price
            all_prices = self.info.all_mids()
            if pair not in all_prices:
                raise ValueError(f"Pair '{pair}' not found")

            current_price = float(all_prices[pair])
            print(f"[Hyperliquid] Current price: ${current_price:.2f}")

            # Calculate size in base asset
            size_in_asset = size_usd / current_price
            size_in_asset_rounded = round(size_in_asset, 6)

            if size_in_asset_rounded == 0.0:
                raise ValueError("Order size too small (rounds to 0)")

            # Set leverage
            await self.set_leverage(pair, leverage)

            # Place order
            is_buy = (side == OrderSide.LONG)
            print(f"[Hyperliquid] Sending order: {size_in_asset_rounded} {pair} @ market")

            order_response = self.exchange.market_open(
                pair, is_buy, size_in_asset_rounded, None
            )

            print(f"[Hyperliquid] Order response: {order_response}")

            # Parse response
            if order_response.get("status") == "ok":
                order_status = order_response["response"]["data"]["statuses"][0]
                if "filled" in order_status:
                    filled_data = order_status.get("filled", {})
                    return OrderResult(
                        success=True,
                        platform=self.platform_name,
                        pair=pair,
                        side=side,
                        order_id=str(filled_data.get("oid", "unknown")),
                        filled_size_usd=size_usd,
                        filled_price=current_price,
                        timestamp=datetime.now()
                    )
                else:
                    error_msg = f"Order accepted but not filled: {order_status}"
                    return OrderResult(
                        success=False,
                        platform=self.platform_name,
                        pair=pair,
                        side=side,
                        error_message=error_msg,
                        timestamp=datetime.now()
                    )
            else:
                error_msg = str(order_response.get("response", "Unknown error"))
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
            print(f"[Hyperliquid] {error_msg}")
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
            print(f"[Hyperliquid] Closing position for {pair}...")

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
                    side=OrderSide.LONG,  # Dummy
                    error_message=f"No open position found for {pair}",
                    timestamp=datetime.now()
                )

            # Close by opening opposite position
            opposite_side = OrderSide.SHORT if position_to_close.side == OrderSide.LONG else OrderSide.LONG
            is_buy = (opposite_side == OrderSide.LONG)

            # Get current price
            all_prices = self.info.all_mids()
            current_price = float(all_prices[pair])

            # Calculate size to close
            size_in_asset = position_to_close.size_usd / current_price
            size_in_asset_rounded = round(size_in_asset, 6)

            # Place closing order
            order_response = self.exchange.market_close(pair, size_in_asset_rounded)
            print(f"[Hyperliquid] Close response: {order_response}")

            if order_response.get("status") == "ok":
                return OrderResult(
                    success=True,
                    platform=self.platform_name,
                    pair=pair,
                    side=opposite_side,
                    filled_size_usd=position_to_close.size_usd,
                    filled_price=current_price,
                    timestamp=datetime.now()
                )
            else:
                return OrderResult(
                    success=False,
                    platform=self.platform_name,
                    pair=pair,
                    side=opposite_side,
                    error_message=str(order_response),
                    timestamp=datetime.now()
                )

        except Exception as e:
            error_msg = f"Error closing position: {str(e)}"
            print(f"[Hyperliquid] {error_msg}")
            return OrderResult(
                success=False,
                platform=self.platform_name,
                pair=pair,
                side=OrderSide.LONG,  # Dummy
                error_message=error_msg,
                timestamp=datetime.now()
            )


# Register this platform with the factory
PlatformFactory.register("hyperliquid", HyperliquidAPI)
