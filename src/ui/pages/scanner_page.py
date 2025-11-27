"""
Scanner Page - Funding opportunity scanner.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

import threading
from typing import List, Callable
from datetime import datetime, timedelta

from src.ui.theme import GlassTheme, Typography, Spacing, ComponentSize
from src.ui.components.glass_frame import GlassCard
from src.ui.components.opportunity_row import OpportunityRow, OpportunityHeader
from src.core.models import FundingData, Opportunity
from src.core.scanner import find_funding_opportunities
from src.platforms.base import PlatformFactory


class ScannerPage(ctk.CTkScrollableFrame if CTK_AVAILABLE else object):
    """
    Scanner page for finding and displaying funding opportunities.
    """

    def __init__(self, master, config_manager, on_opportunity_select: Callable = None, **kwargs):
        """
        Initialize scanner page.

        Args:
            master: Parent widget
            config_manager: ConfigManager instance
            on_opportunity_select: Callback when opportunity is selected
            **kwargs: Additional arguments
        """
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required")

        super().__init__(
            master,
            fg_color=GlassTheme.BG_PRIMARY,
            **kwargs
        )

        self.config_manager = config_manager
        self.on_opportunity_select = on_opportunity_select

        # State
        self.opportunities: List[Opportunity] = []
        self.is_scanning = False
        self.last_scan_time: datetime = None
        self.scan_thread = None

        # Platform filters
        self.platform_vars = {}

        self._build_ui()

    def _build_ui(self):
        """Build the scanner UI."""
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=(Spacing.LARGE, Spacing.MEDIUM))
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="Funding Scanner",
            font=Typography.title(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        title.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(
            header_frame,
            text="Ready to scan",
            font=Typography.small(),
            text_color=GlassTheme.TEXT_MUTED
        )
        self.status_label.grid(row=1, column=0, sticky="w", pady=(Spacing.TINY, 0))

        row += 1

        # Controls
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)

        scan_btn = ctk.CTkButton(
            controls_frame,
            text="Scan Opportunities",
            command=self._start_scan,
            height=ComponentSize.BUTTON_HEIGHT_LARGE,
            fg_color=GlassTheme.ACCENT_BLUE,
            hover_color=GlassTheme.ACCENT_CYAN,
            font=Typography.body()
        )
        scan_btn.grid(row=0, column=0, padx=(0, Spacing.SMALL))

        # Platform filters
        platforms = ["Hyperliquid", "Paradex", "Lighter", "Extended"]
        for i, platform in enumerate(platforms):
            var = ctk.BooleanVar(value=True)
            self.platform_vars[platform.lower()] = var

            checkbox = ctk.CTkCheckBox(
                controls_frame,
                text=platform,
                variable=var,
                font=Typography.small()
            )
            checkbox.grid(row=0, column=i+1, padx=Spacing.SMALL)

        row += 1

        # Opportunities list
        list_frame = GlassCard(self)
        list_frame.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)
        list_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = OpportunityHeader(list_frame)
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.SMALL, pady=(Spacing.SMALL, 0))

        # Scrollable area for opportunities
        self.opportunities_container = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent",
            height=400
        )
        self.opportunities_container.grid(row=1, column=0, sticky="nsew", padx=Spacing.SMALL, pady=Spacing.SMALL)
        self.opportunities_container.grid_columnconfigure(0, weight=1)

        list_frame.grid_rowconfigure(1, weight=1)

    def _start_scan(self):
        """Start scanning for opportunities."""
        if self.is_scanning:
            print("[Scanner] Scan already in progress")
            return

        self.is_scanning = True
        self.status_label.configure(text="Scanning...")

        # Clear previous results
        for widget in self.opportunities_container.winfo_children():
            widget.destroy()

        # Start scan in background thread
        self.scan_thread = threading.Thread(target=self._scan_thread, daemon=True)
        self.scan_thread.start()

    def _scan_thread(self):
        """Background thread for scanning."""
        try:
            all_funding_data: List[FundingData] = []

            # Get enabled platforms
            enabled_platforms = [
                name for name, var in self.platform_vars.items()
                if var.get()
            ]

            if not enabled_platforms:
                self._scan_callback([], "No platforms selected")
                return

            # Fetch funding data from each platform
            for platform_name in enabled_platforms:
                try:
                    platform_config = self.config_manager.get_platform_config(platform_name)
                    if not platform_config:
                        continue

                    # Create platform instance
                    platform = PlatformFactory.create(platform_name, platform_config)

                    # Fetch funding rates
                    funding_data = platform.get_funding_rates_sync()
                    all_funding_data.extend(funding_data)

                    print(f"[Scanner] Fetched {len(funding_data)} pairs from {platform_name}")

                except Exception as e:
                    print(f"[Scanner] Error fetching from {platform_name}: {e}")

            # Find opportunities
            opportunities = find_funding_opportunities(
                all_funding_data,
                min_spread=0.0,
                top_n=25,
                include_net_spread=True
            )

            self.last_scan_time = datetime.now()
            self._scan_callback(opportunities, f"Found {len(opportunities)} opportunities")

        except Exception as e:
            print(f"[Scanner] Scan error: {e}")
            self._scan_callback([], f"Scan failed: {e}")

    def _scan_callback(self, opportunities: List[Opportunity], message: str):
        """
        Callback when scan completes.

        Args:
            opportunities: List of found opportunities
            message: Status message
        """
        self.is_scanning = False
        self.opportunities = opportunities

        # Update UI (must be on main thread)
        self.after(0, lambda: self._update_opportunities_ui(message))

    def _update_opportunities_ui(self, message: str):
        """Update opportunities display (on main thread)."""
        # Update status
        time_str = self.last_scan_time.strftime("%H:%M:%S") if self.last_scan_time else "Never"
        self.status_label.configure(text=f"{message} | Last scan: {time_str}")

        # Clear container
        for widget in self.opportunities_container.winfo_children():
            widget.destroy()

        # Add opportunity rows
        for i, opp in enumerate(self.opportunities):
            row = OpportunityRow(
                self.opportunities_container,
                opportunity=opp,
                on_click=self._on_opportunity_click
            )
            row.grid(row=i, column=0, sticky="ew", padx=0, pady=1)

        # Empty state
        if not self.opportunities:
            empty_label = ctk.CTkLabel(
                self.opportunities_container,
                text="No opportunities found. Try scanning again.",
                font=Typography.body(),
                text_color=GlassTheme.TEXT_MUTED
            )
            empty_label.grid(row=0, column=0, pady=Spacing.LARGE)

    def _on_opportunity_click(self, opportunity: Opportunity):
        """Handle opportunity selection."""
        print(f"[Scanner] Selected opportunity: {opportunity.pair}")
        if self.on_opportunity_select:
            self.on_opportunity_select(opportunity)

    def get_opportunities(self) -> List[Opportunity]:
        """Get current list of opportunities."""
        return self.opportunities.copy()
