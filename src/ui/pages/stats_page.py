"""
Stats Page - Airdrop ROI tracking.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from src.ui.theme import GlassTheme, Typography, Spacing
from src.ui.components.glass_frame import GlassCard
from src.ui.components.kpi_card import KPICard


class StatsPage(ctk.CTkScrollableFrame if CTK_AVAILABLE else object):
    """
    Stats page for tracking airdrop ROI and performance.
    """

    def __init__(self, master, **kwargs):
        """Initialize stats page."""
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required")

        super().__init__(
            master,
            fg_color=GlassTheme.BG_PRIMARY,
            **kwargs
        )

        self._build_ui()

    def _build_ui(self):
        """Build the stats UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        row = 0

        # Title
        title = ctk.CTkLabel(
            self,
            text="Airdrop Statistics",
            font=Typography.title(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        title.grid(row=row, column=0, columnspan=2, sticky="w", padx=Spacing.LARGE, pady=(Spacing.LARGE, Spacing.MEDIUM))
        row += 1

        # KPI Cards
        self.kpi_total_farmed = KPICard(
            self,
            label="Total Farmed",
            value="$0.00",
            subtitle="Across all platforms",
            icon=""
        )
        self.kpi_total_farmed.grid(row=row, column=0, sticky="ew", padx=(Spacing.LARGE, Spacing.SMALL), pady=Spacing.MEDIUM)

        self.kpi_avg_roi = KPICard(
            self,
            label="Avg ROI",
            value="0.00%",
            subtitle="Average return",
            icon=""
        )
        self.kpi_avg_roi.grid(row=row, column=1, sticky="ew", padx=(Spacing.SMALL, Spacing.LARGE), pady=Spacing.MEDIUM)
        row += 1

        # Platform breakdown
        breakdown_card = GlassCard(self)
        breakdown_card.grid(row=row, column=0, columnspan=2, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)
        breakdown_card.grid_columnconfigure(0, weight=1)

        breakdown_title = ctk.CTkLabel(
            breakdown_card,
            text="Platform Breakdown",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        breakdown_title.grid(row=0, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        platforms = [
            ("Hyperliquid", "$0.00"),
            ("Paradex", "$0.00"),
            ("Lighter", "$0.00"),
            ("Extended", "$0.00")
        ]

        for i, (platform, amount) in enumerate(platforms):
            platform_label = ctk.CTkLabel(
                breakdown_card,
                text=platform,
                font=Typography.body(),
                text_color=GlassTheme.TEXT_SECONDARY,
                anchor="w"
            )
            platform_label.grid(row=i+1, column=0, sticky="w", padx=Spacing.MEDIUM, pady=Spacing.TINY)

            amount_label = ctk.CTkLabel(
                breakdown_card,
                text=amount,
                font=Typography.body(),
                text_color=GlassTheme.TEXT_PRIMARY,
                anchor="e"
            )
            amount_label.grid(row=i+1, column=1, sticky="e", padx=Spacing.MEDIUM, pady=Spacing.TINY)

        # Bottom padding
        breakdown_card.grid_rowconfigure(len(platforms)+1, minsize=Spacing.MEDIUM)
