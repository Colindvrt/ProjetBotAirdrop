"""
Bot Page - Delta Neutral trading bot.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

import threading
from typing import Optional

from src.ui.theme import GlassTheme, Typography, Spacing, ComponentSize, format_currency
from src.ui.components.glass_frame import GlassCard
from src.ui.components.kpi_card import NumericKPICard
from src.core.models import Opportunity, DeltaNeutralStrategy
from src.trading.executor import TradingExecutor


class BotPage(ctk.CTkScrollableFrame if CTK_AVAILABLE else object):
    """
    Bot page for executing delta-neutral arbitrage strategies.
    """

    def __init__(self, master, executor: TradingExecutor = None, **kwargs):
        """
        Initialize bot page.

        Args:
            master: Parent widget
            executor: TradingExecutor instance
            **kwargs: Additional arguments
        """
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required")

        super().__init__(
            master,
            fg_color=GlassTheme.BG_PRIMARY,
            **kwargs
        )

        self.executor = executor

        # State
        self.selected_opportunity: Optional[Opportunity] = None
        self.current_strategy: Optional[DeltaNeutralStrategy] = None
        self.is_executing = False

        self._build_ui()

    def _build_ui(self):
        """Build the bot UI."""
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Title
        title = ctk.CTkLabel(
            self,
            text="Delta Neutral Bot",
            font=Typography.title(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        title.grid(row=row, column=0, sticky="w", padx=Spacing.LARGE, pady=(Spacing.LARGE, Spacing.MEDIUM))
        row += 1

        # Opportunity selection section
        opp_card = GlassCard(self)
        opp_card.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)
        opp_card.grid_columnconfigure(0, weight=1)

        opp_title = ctk.CTkLabel(
            opp_card,
            text="Selected Opportunity",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        opp_title.grid(row=0, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        self.opp_display = ctk.CTkLabel(
            opp_card,
            text="No opportunity selected. Use Scanner to find opportunities.",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_MUTED,
            anchor="w",
            wraplength=600
        )
        self.opp_display.grid(row=1, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(0, Spacing.MEDIUM))

        row += 1

        # Configuration section
        config_card = GlassCard(self)
        config_card.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)
        config_card.grid_columnconfigure(0, weight=1)
        config_card.grid_columnconfigure(1, weight=1)

        config_title = ctk.CTkLabel(
            config_card,
            text="Strategy Configuration",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        config_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        # Stake size
        stake_label = ctk.CTkLabel(
            config_card,
            text="Stake Size (USD):",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        stake_label.grid(row=1, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        self.stake_entry = ctk.CTkEntry(
            config_card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="100"
        )
        self.stake_entry.grid(row=2, column=0, sticky="ew", padx=(Spacing.MEDIUM, Spacing.SMALL), pady=(Spacing.TINY, Spacing.SMALL))
        self.stake_entry.insert(0, "100")

        # Leverage
        leverage_label = ctk.CTkLabel(
            config_card,
            text="Leverage:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        leverage_label.grid(row=1, column=1, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        self.leverage_entry = ctk.CTkEntry(
            config_card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="5"
        )
        self.leverage_entry.grid(row=2, column=1, sticky="ew", padx=(Spacing.SMALL, Spacing.MEDIUM), pady=(Spacing.TINY, Spacing.SMALL))
        self.leverage_entry.insert(0, "5")

        # Auto-management options
        auto_title = ctk.CTkLabel(
            config_card,
            text="Auto-Management (Optional)",
            font=Typography.subheading(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        auto_title.grid(row=3, column=0, columnspan=2, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        # Take profit
        tp_label = ctk.CTkLabel(
            config_card,
            text="Take Profit (USD):",
            font=Typography.small(),
            text_color=GlassTheme.TEXT_MUTED
        )
        tp_label.grid(row=4, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.TINY, 0))

        self.tp_entry = ctk.CTkEntry(
            config_card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="50 (optional)"
        )
        self.tp_entry.grid(row=5, column=0, sticky="ew", padx=(Spacing.MEDIUM, Spacing.SMALL), pady=(Spacing.TINY, Spacing.SMALL))

        # Stop loss
        sl_label = ctk.CTkLabel(
            config_card,
            text="Stop Loss (USD):",
            font=Typography.small(),
            text_color=GlassTheme.TEXT_MUTED
        )
        sl_label.grid(row=4, column=1, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.TINY, 0))

        self.sl_entry = ctk.CTkEntry(
            config_card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="-20 (optional)"
        )
        self.sl_entry.grid(row=5, column=1, sticky="ew", padx=(Spacing.SMALL, Spacing.MEDIUM), pady=(Spacing.TINY, Spacing.MEDIUM))

        row += 1

        # Execute button
        self.execute_button = ctk.CTkButton(
            self,
            text="Execute Strategy",
            command=self._execute_strategy,
            height=ComponentSize.BUTTON_HEIGHT_LARGE,
            font=Typography.body(),
            fg_color=GlassTheme.ACCENT_SUCCESS,
            hover_color=GlassTheme.gradient_success()[1]
        )
        self.execute_button.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)
        row += 1

        # Status section
        status_card = GlassCard(self)
        status_card.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)
        status_card.grid_columnconfigure(0, weight=1)

        status_title = ctk.CTkLabel(
            status_card,
            text="Status",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        status_title.grid(row=0, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        self.status_label = ctk.CTkLabel(
            status_card,
            text="Ready. Select an opportunity and configure your strategy.",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_MUTED,
            anchor="w",
            wraplength=600
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(0, Spacing.MEDIUM))

    def set_opportunity(self, opportunity: Opportunity):
        """
        Set the selected opportunity.

        Args:
            opportunity: Opportunity to execute
        """
        self.selected_opportunity = opportunity

        # Update display
        opp_text = (
            f"Pair: {opportunity.pair}\n"
            f"LONG on {opportunity.long_platform} @ {opportunity.long_rate_1h:.6f}%/h\n"
            f"SHORT on {opportunity.short_platform} @ {opportunity.short_rate_1h:.6f}%/h\n"
            f"Spread: {opportunity.spread_1h:.6f}%/h | Score: {opportunity.score_1h:.2f}"
        )

        self.opp_display.configure(
            text=opp_text,
            text_color=GlassTheme.TEXT_PRIMARY
        )

        # Enable execute button
        self.execute_button.configure(state="normal")

    def _execute_strategy(self):
        """Execute the delta-neutral strategy."""
        if not self.selected_opportunity:
            self._update_status("ERROR: No opportunity selected", GlassTheme.ACCENT_DANGER)
            return

        if not self.executor:
            self._update_status("ERROR: No executor available", GlassTheme.ACCENT_DANGER)
            return

        if self.is_executing:
            self._update_status("ERROR: Execution already in progress", GlassTheme.ACCENT_WARNING)
            return

        # Validate inputs
        try:
            stake_size = float(self.stake_entry.get())
            leverage = int(self.leverage_entry.get())

            if stake_size <= 0:
                raise ValueError("Stake size must be positive")
            if leverage < 1 or leverage > 50:
                raise ValueError("Leverage must be between 1 and 50")

            # Optional params
            take_profit = None
            stop_loss = None

            if self.tp_entry.get():
                take_profit = float(self.tp_entry.get())

            if self.sl_entry.get():
                stop_loss = float(self.sl_entry.get())

        except ValueError as e:
            self._update_status(f"ERROR: Invalid input - {e}", GlassTheme.ACCENT_DANGER)
            return

        # Disable button
        self.is_executing = True
        self.execute_button.configure(state="disabled")
        self._update_status("Executing strategy...", GlassTheme.ACCENT_BLUE)

        # Execute in background thread
        thread = threading.Thread(
            target=self._execute_thread,
            args=(stake_size, leverage, take_profit, stop_loss),
            daemon=True
        )
        thread.start()

    def _execute_thread(self, stake_size, leverage, take_profit, stop_loss):
        """Execute strategy in background thread."""
        try:
            success, strategy, message = self.executor.execute_delta_neutral_sync(
                self.selected_opportunity,
                stake_size,
                leverage,
                take_profit_usd=take_profit,
                stop_loss_usd=stop_loss
            )

            if success:
                self.current_strategy = strategy
                self._execution_callback(True, message)
            else:
                self._execution_callback(False, message)

        except Exception as e:
            self._execution_callback(False, f"Execution failed: {e}")

    def _execution_callback(self, success: bool, message: str):
        """Callback when execution completes."""
        self.is_executing = False

        # Update UI on main thread
        color = GlassTheme.ACCENT_SUCCESS if success else GlassTheme.ACCENT_DANGER
        self.after(0, lambda: self._update_status(message, color))
        self.after(0, lambda: self.execute_button.configure(state="normal"))

    def _update_status(self, message: str, color: str = None):
        """Update status message."""
        self.status_label.configure(
            text=message,
            text_color=color or GlassTheme.TEXT_MUTED
        )
        print(f"[Bot] {message}")
