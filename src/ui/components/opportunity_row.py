"""
Opportunity row component for displaying funding opportunities.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from src.ui.theme import GlassTheme, Typography, Spacing, ComponentSize
from src.ui.components.glass_frame import GlassFrame
from src.core.models import Opportunity


class OpportunityRow(GlassFrame if CTK_AVAILABLE else object):
    """
    A row component for displaying a single funding opportunity.

    Displays:
    - Pair name
    - Spread (1h and 8h)
    - Score
    - Long/Short platforms
    - Min leverage
    """

    def __init__(
        self,
        master,
        opportunity: Opportunity = None,
        on_click: callable = None,
        **kwargs
    ):
        """
        Initialize opportunity row.

        Args:
            master: Parent widget
            opportunity: Opportunity object to display
            on_click: Callback when row is clicked
            **kwargs: Additional arguments for GlassFrame
        """
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required for OpportunityRow")

        super().__init__(
            master,
            corner_radius=ComponentSize.CORNER_RADIUS_SMALL,
            border_width=ComponentSize.BORDER_WIDTH_THIN,
            hover_enabled=bool(on_click),
            **kwargs
        )

        self.opportunity = opportunity
        self.on_click_callback = on_click

        # Configure grid
        self.grid_columnconfigure(0, weight=0, minsize=80)   # Pair
        self.grid_columnconfigure(1, weight=1, minsize=100)  # Spread 1h
        self.grid_columnconfigure(2, weight=1, minsize=100)  # Spread 8h
        self.grid_columnconfigure(3, weight=1, minsize=80)   # Score
        self.grid_columnconfigure(4, weight=1, minsize=120)  # Long
        self.grid_columnconfigure(5, weight=1, minsize=120)  # Short
        self.grid_columnconfigure(6, weight=0, minsize=60)   # Leverage

        if opportunity:
            self._build_ui()

        # Bind click event
        if on_click:
            self.bind("<Button-1>", self._on_click)

    def _build_ui(self):
        """Build the UI elements for the opportunity."""
        opp = self.opportunity

        # Pair
        pair_label = ctk.CTkLabel(
            self,
            text=opp.pair,
            font=Typography.body(),
            text_color=GlassTheme.TEXT_PRIMARY,
            anchor="w"
        )
        pair_label.grid(row=0, column=0, sticky="w", padx=Spacing.SMALL, pady=Spacing.SMALL)

        # Spread 1h
        spread_1h_label = ctk.CTkLabel(
            self,
            text=f"{opp.spread_1h:.4f}%",
            font=Typography.body(),
            text_color=GlassTheme.ACCENT_SUCCESS if opp.spread_1h > 0 else GlassTheme.ACCENT_DANGER,
            anchor="w"
        )
        spread_1h_label.grid(row=0, column=1, sticky="w", padx=Spacing.SMALL, pady=Spacing.SMALL)

        # Spread 8h
        spread_8h_label = ctk.CTkLabel(
            self,
            text=f"{opp.spread_8h:.4f}%",
            font=Typography.body(),
            text_color=GlassTheme.ACCENT_SUCCESS if opp.spread_8h > 0 else GlassTheme.ACCENT_DANGER,
            anchor="w"
        )
        spread_8h_label.grid(row=0, column=2, sticky="w", padx=Spacing.SMALL, pady=Spacing.SMALL)

        # Score
        score_label = ctk.CTkLabel(
            self,
            text=f"{opp.score_1h:.2f}",
            font=Typography.body(),
            text_color=GlassTheme.ACCENT_BLUE,
            anchor="w"
        )
        score_label.grid(row=0, column=3, sticky="w", padx=Spacing.SMALL, pady=Spacing.SMALL)

        # Long platform
        long_label = ctk.CTkLabel(
            self,
            text=f"{opp.long_platform}",
            font=Typography.small(),
            text_color=GlassTheme.TEXT_SECONDARY,
            anchor="w"
        )
        long_label.grid(row=0, column=4, sticky="w", padx=Spacing.SMALL, pady=Spacing.SMALL)

        # Short platform
        short_label = ctk.CTkLabel(
            self,
            text=f"{opp.short_platform}",
            font=Typography.small(),
            text_color=GlassTheme.TEXT_SECONDARY,
            anchor="w"
        )
        short_label.grid(row=0, column=5, sticky="w", padx=Spacing.SMALL, pady=Spacing.SMALL)

        # Min leverage
        leverage_label = ctk.CTkLabel(
            self,
            text=f"{opp.min_leverage}x",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_MUTED,
            anchor="e"
        )
        leverage_label.grid(row=0, column=6, sticky="e", padx=Spacing.SMALL, pady=Spacing.SMALL)

    def _on_click(self, event):
        """Handle click event."""
        if self.on_click_callback and self.opportunity:
            self.on_click_callback(self.opportunity)

    def update_opportunity(self, opportunity: Opportunity):
        """
        Update the displayed opportunity.

        Args:
            opportunity: New Opportunity object
        """
        self.opportunity = opportunity

        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Rebuild UI
        self._build_ui()


class OpportunityHeader(GlassFrame if CTK_AVAILABLE else object):
    """
    Header row for opportunity list.
    """

    def __init__(self, master, **kwargs):
        """Initialize opportunity header."""
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required")

        super().__init__(
            master,
            corner_radius=ComponentSize.CORNER_RADIUS_SMALL,
            border_width=0,
            fg_color=GlassTheme.BG_SECONDARY,
            **kwargs
        )

        # Configure grid (same as OpportunityRow)
        self.grid_columnconfigure(0, weight=0, minsize=80)
        self.grid_columnconfigure(1, weight=1, minsize=100)
        self.grid_columnconfigure(2, weight=1, minsize=100)
        self.grid_columnconfigure(3, weight=1, minsize=80)
        self.grid_columnconfigure(4, weight=1, minsize=120)
        self.grid_columnconfigure(5, weight=1, minsize=120)
        self.grid_columnconfigure(6, weight=0, minsize=60)

        headers = [
            "Pair",
            "Spread 1h",
            "Spread 8h",
            "Score",
            "Long On",
            "Short On",
            "Leverage"
        ]

        for i, header_text in enumerate(headers):
            label = ctk.CTkLabel(
                self,
                text=header_text,
                font=(Typography.FONT_FAMILY_PRIMARY, Typography.SIZE_SMALL, Typography.WEIGHT_BOLD),
                text_color=GlassTheme.TEXT_SECONDARY,
                anchor="w" if i < 6 else "e"
            )
            label.grid(row=0, column=i, sticky="w" if i < 6 else "e", padx=Spacing.SMALL, pady=Spacing.SMALL)
