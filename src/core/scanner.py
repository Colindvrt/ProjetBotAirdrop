"""
Enhanced funding opportunity scanner with fee and slippage calculations.

This module finds delta-neutral arbitrage opportunities across platforms,
accounting for transaction costs and slippage.
"""

from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

from src.core.models import (
    FundingData,
    Opportunity,
    Platform,
    PLATFORM_FEES,
    PLATFORM_SLIPPAGE
)


def standardize_pair_name(pair: str) -> str:
    """
    Standardize pair name across platforms.

    Args:
        pair: Platform-specific pair name

    Returns:
        Standardized pair name (e.g., "BTC", "ETH")
    """
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


def calculate_entry_cost(
    long_platform: str,
    short_platform: str,
    leverage: int = 1
) -> float:
    """
    Calculate total entry/exit cost as percentage.

    Includes:
    - Entry fees on both platforms
    - Exit fees on both platforms
    - Estimated slippage on both platforms

    Args:
        long_platform: Platform for long position
        short_platform: Platform for short position
        leverage: Leverage used (affects fee impact)

    Returns:
        Total cost as decimal (e.g., 0.001 = 0.1%)
    """
    # Get platform enums
    try:
        long_plat_enum = Platform[long_platform.upper().replace(" ", "")]
        short_plat_enum = Platform[short_platform.upper().replace(" ", "")]
    except KeyError:
        # Fallback if platform not in enum
        return 0.002  # Conservative 0.2% estimate

    # Get fees
    long_fee = PLATFORM_FEES.get(long_plat_enum, {}).get('taker', 0.0005)
    short_fee = PLATFORM_FEES.get(short_plat_enum, {}).get('taker', 0.0005)

    # Get slippage
    long_slippage = PLATFORM_SLIPPAGE.get(long_plat_enum, 0.001)
    short_slippage = PLATFORM_SLIPPAGE.get(short_plat_enum, 0.001)

    # Total cost = (entry_fee + exit_fee + slippage) for both sides
    # Entry + exit = 2x fees
    total_cost = (
        (long_fee * 2 + long_slippage) +
        (short_fee * 2 + short_slippage)
    )

    return total_cost


def calculate_net_spread(
    gross_spread_1h: float,
    long_platform: str,
    short_platform: str,
    leverage: int = 1,
    hold_hours: int = 24
) -> float:
    """
    Calculate net spread after fees and slippage.

    Args:
        gross_spread_1h: Gross hourly spread (decimal)
        long_platform: Platform for long position
        short_platform: Platform for short position
        leverage: Leverage used
        hold_hours: Expected hold time in hours

    Returns:
        Net hourly spread (decimal)
    """
    # Get entry/exit cost
    entry_cost = calculate_entry_cost(long_platform, short_platform, leverage)

    # Amortize entry/exit cost over hold period
    hourly_cost = entry_cost / hold_hours

    # Multiply by leverage (higher leverage amplifies costs)
    hourly_cost_with_leverage = hourly_cost * leverage

    # Net spread = gross spread - hourly cost
    net_spread = gross_spread_1h - hourly_cost_with_leverage

    return net_spread


def find_funding_opportunities(
    all_funding_data: List[FundingData],
    min_spread: float = 0.0,
    min_leverage: int = 1,
    top_n: int = 25,
    include_net_spread: bool = True
) -> List[Opportunity]:
    """
    Find delta-neutral funding arbitrage opportunities.

    Args:
        all_funding_data: List of FundingData from all platforms
        min_spread: Minimum gross spread to consider (decimal)
        min_leverage: Minimum leverage required
        top_n: Number of top opportunities to return
        include_net_spread: Calculate net spread with fees/slippage

    Returns:
        List of Opportunity objects, sorted by score descending
    """
    if not all_funding_data:
        return []

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame([
        {
            'pair': standardize_pair_name(fd.pair),
            'rate_1h': fd.rate_1h,
            'platform': fd.platform,
            'max_leverage': fd.max_leverage,
            'volume_24h': fd.volume_24h
        }
        for fd in all_funding_data
    ])

    if df.empty:
        return []

    # Pivot to compare rates across platforms
    pivot = df.pivot_table(
        index='pair',
        columns='platform',
        values='rate_1h',
        aggfunc='first'
    )

    # Get leverage info
    leverage_pivot = df.pivot_table(
        index='pair',
        columns='platform',
        values='max_leverage',
        aggfunc='first'
    )

    opportunities = []

    for pair in pivot.index:
        rates = pivot.loc[pair].dropna()

        if len(rates) < 2:
            # Need at least 2 platforms for arbitrage
            continue

        # Find min and max rates
        min_rate = rates.min()
        max_rate = rates.max()

        # Get platforms
        long_platform = rates.idxmin()  # Platform with lowest rate (go LONG here)
        short_platform = rates.idxmax()  # Platform with highest rate (go SHORT here)

        # Must be different platforms
        if long_platform == short_platform:
            continue

        # Calculate spread
        spread_1h = max_rate - min_rate
        spread_8h = spread_1h * 8

        # Filter by minimum spread
        if spread_1h < min_spread:
            continue

        # Get leverage info
        try:
            long_leverage = int(leverage_pivot.loc[pair, long_platform])
            short_leverage = int(leverage_pivot.loc[pair, short_platform])
        except (KeyError, ValueError):
            long_leverage = 1
            short_leverage = 1

        min_lev = min(long_leverage, short_leverage)

        # Filter by minimum leverage
        if min_lev < min_leverage:
            continue

        # Calculate scores
        score_1h = spread_1h * min_lev * 100  # Convert to percentage points
        score_8h = spread_8h * min_lev * 100

        # Calculate net spread if requested
        net_spread_1h = None
        entry_cost_pct = None

        if include_net_spread:
            net_spread_1h = calculate_net_spread(
                spread_1h,
                long_platform,
                short_platform,
                leverage=min_lev,
                hold_hours=24
            )
            entry_cost_pct = calculate_entry_cost(long_platform, short_platform, min_lev)

        # Create opportunity
        opp = Opportunity(
            pair=pair,
            long_platform=long_platform,
            long_rate_1h=min_rate,
            long_leverage=long_leverage,
            short_platform=short_platform,
            short_rate_1h=max_rate,
            short_leverage=short_leverage,
            spread_1h=spread_1h,
            spread_8h=spread_8h,
            min_leverage=min_lev,
            score_1h=score_1h,
            score_8h=score_8h,
            net_spread_1h=net_spread_1h,
            entry_cost_pct=entry_cost_pct,
            timestamp=datetime.now()
        )

        opportunities.append(opp)

    # Sort by score (descending)
    opportunities.sort(key=lambda x: x.score_1h, reverse=True)

    # Return top N
    return opportunities[:top_n]


def filter_opportunities(
    opportunities: List[Opportunity],
    min_net_spread: float = None,
    max_entry_cost: float = None,
    platforms: List[str] = None,
    pairs: List[str] = None
) -> List[Opportunity]:
    """
    Filter opportunities based on criteria.

    Args:
        opportunities: List of opportunities to filter
        min_net_spread: Minimum net spread (after fees)
        max_entry_cost: Maximum entry cost percentage
        platforms: List of allowed platforms (None = all)
        pairs: List of allowed pairs (None = all)

    Returns:
        Filtered list of opportunities
    """
    filtered = opportunities.copy()

    # Filter by net spread
    if min_net_spread is not None:
        filtered = [
            opp for opp in filtered
            if opp.net_spread_1h is not None and opp.net_spread_1h >= min_net_spread
        ]

    # Filter by entry cost
    if max_entry_cost is not None:
        filtered = [
            opp for opp in filtered
            if opp.entry_cost_pct is not None and opp.entry_cost_pct <= max_entry_cost
        ]

    # Filter by platforms
    if platforms:
        platforms_lower = [p.lower() for p in platforms]
        filtered = [
            opp for opp in filtered
            if opp.long_platform.lower() in platforms_lower
            and opp.short_platform.lower() in platforms_lower
        ]

    # Filter by pairs
    if pairs:
        pairs_upper = [p.upper() for p in pairs]
        filtered = [
            opp for opp in filtered
            if opp.pair.upper() in pairs_upper
        ]

    return filtered


def get_opportunity_summary(opportunities: List[Opportunity]) -> Dict[str, Any]:
    """
    Get summary statistics for a list of opportunities.

    Args:
        opportunities: List of opportunities

    Returns:
        Dictionary with summary statistics
    """
    if not opportunities:
        return {
            'count': 0,
            'avg_spread_1h': 0.0,
            'max_spread_1h': 0.0,
            'avg_score': 0.0,
            'max_score': 0.0,
            'platforms': []
        }

    spreads = [opp.spread_1h for opp in opportunities]
    scores = [opp.score_1h for opp in opportunities]

    platforms = set()
    for opp in opportunities:
        platforms.add(opp.long_platform)
        platforms.add(opp.short_platform)

    return {
        'count': len(opportunities),
        'avg_spread_1h': sum(spreads) / len(spreads),
        'max_spread_1h': max(spreads),
        'avg_score': sum(scores) / len(scores),
        'max_score': max(scores),
        'platforms': list(platforms)
    }
