"""
Dashboard Page - Portfolio overview and performance metrics.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from src.ui.theme import GlassTheme, Typography, Spacing
from src.ui.components.kpi_card import NumericKPICard
from src.trading.executor import TradingExecutor


class DashboardPage(ctk.CTkScrollableFrame if CTK_AVAILABLE else object):
    """
    Dashboard page showing portfolio overview and key metrics.
    """

    def __init__(self, master, executor: TradingExecutor = None, **kwargs):
        """Initialize dashboard page."""
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required")

        super().__init__(
            master,
            fg_color=GlassTheme.BG_PRIMARY,
            **kwargs
        )

        self.executor = executor

        self._build_ui()
        self._update_data()

    def _build_ui(self):
        """Build the dashboard UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        row = 0

        # Title
        title = ctk.CTkLabel(
            self,
            text="Portfolio Dashboard",
            font=Typography.title(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        title.grid(row=row, column=0, columnspan=3, sticky="w", padx=Spacing.LARGE, pady=(Spacing.LARGE, Spacing.MEDIUM))
        row += 1

        # KPI Cards - Row 1
        self.kpi_total_equity = NumericKPICard(
            self,
            label="Total Equity",
            value=0.0,
            format_type="currency"
        )
        self.kpi_total_equity.grid(row=row, column=0, sticky="ew", padx=(Spacing.LARGE, Spacing.SMALL), pady=Spacing.MEDIUM)

        self.kpi_total_pnl = NumericKPICard(
            self,
            label="Total PnL",
            value=0.0,
            format_type="currency"
        )
        self.kpi_total_pnl.grid(row=row, column=1, sticky="ew", padx=Spacing.SMALL, pady=Spacing.MEDIUM)

        self.kpi_funding_earned = NumericKPICard(
            self,
            label="Funding Earned",
            value=0.0,
            format_type="currency"
        )
        self.kpi_funding_earned.grid(row=row, column=2, sticky="ew", padx=(Spacing.SMALL, Spacing.LARGE), pady=Spacing.MEDIUM)
        row += 1

        # Refresh button
        refresh_btn = ctk.CTkButton(
            self,
            text="Refresh Data",
            command=self._update_data,
            height=36,
            fg_color=GlassTheme.ACCENT_BLUE,
            hover_color=GlassTheme.ACCENT_CYAN
        )
        refresh_btn.grid(row=row, column=0, columnspan=3, sticky="w", padx=Spacing.LARGE, pady=Spacing.MEDIUM)
        row += 1

        # Platform balances title
        platform_title = ctk.CTkLabel(
            self,
            text="Platform Balances",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        platform_title.grid(row=row, column=0, columnspan=3, sticky="w", padx=Spacing.LARGE, pady=(Spacing.LARGE, Spacing.MEDIUM))
        row += 1

        # Platform balance cards
        self.platform_kpis = {}
        platforms = ["Hyperliquid", "Paradex", "Lighter", "Extended"]

        for i, platform in enumerate(platforms):
            col = i % 2
            if col == 0 and i > 0:
                row += 1

            kpi = NumericKPICard(
                self,
                label=platform,
                value=0.0,
                format_type="currency"
            )

            if col == 0:
                kpi.grid(row=row, column=0, columnspan=1, sticky="ew", padx=(Spacing.LARGE, Spacing.SMALL), pady=Spacing.SMALL)
            else:
                kpi.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(Spacing.SMALL, Spacing.LARGE), pady=Spacing.SMALL)

            self.platform_kpis[platform.lower()] = kpi

    def _update_data(self):
        """Update dashboard data from executor."""
        if not self.executor:
            print("[Dashboard] No executor available")
            return

        try:
            # Get all balances
            balances = self.executor.get_all_balances_sync()

            total_equity = sum(balances.values())
            self.kpi_total_equity.set_value(total_equity)

            # Update platform balances
            for platform, balance in balances.items():
                if platform in self.platform_kpis:
                    self.platform_kpis[platform].set_value(balance)

            print("[Dashboard] Data updated successfully")

        except Exception as e:
            print(f"[Dashboard] Error updating data: {e}")

    def refresh(self):
        """Public method to refresh data."""
        self._update_data()
