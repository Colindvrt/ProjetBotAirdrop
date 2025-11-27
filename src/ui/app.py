"""
Main application window with tabbed navigation.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    print("ERROR: CustomTkinter not installed. Run: pip install customtkinter")
    CTK_AVAILABLE = False

from src.ui.theme import GlassTheme, Typography, Spacing
from src.ui.pages.scanner_page import ScannerPage
from src.ui.pages.bot_page import BotPage
from src.ui.pages.dashboard_page import DashboardPage
from src.ui.pages.stats_page import StatsPage
from src.ui.pages.settings_page import SettingsPage

from src.config.manager import ConfigManager
from src.trading.executor import TradingExecutor


class FundingFarmingApp(ctk.CTk if CTK_AVAILABLE else object):
    """
    Main application window for Funding Farming Bot.

    Features:
    - Tabbed navigation (Scanner, Bot, Dashboard, Stats, Settings)
    - Glassmorphism theme
    - Integrated trading executor
    - Configuration management
    """

    def __init__(self):
        """Initialize the application."""
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required")

        super().__init__()

        # Window configuration
        self.title("Funding Farming Bot v2.0")
        self.geometry("1200x800")
        self.minsize(1000, 600)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configure colors
        self.configure(fg_color=GlassTheme.BG_PRIMARY)

        # Initialize managers
        self.config_manager = ConfigManager()
        self.executor = TradingExecutor(self.config_manager)

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the main UI."""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create tabview
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=GlassTheme.BG_PRIMARY,
            segmented_button_fg_color=GlassTheme.BG_SECONDARY,
            segmented_button_selected_color=GlassTheme.ACCENT_BLUE,
            segmented_button_selected_hover_color=GlassTheme.ACCENT_CYAN
        )
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Create tabs
        scanner_tab = self.tabview.add("Scanner")
        bot_tab = self.tabview.add("Bot")
        dashboard_tab = self.tabview.add("Dashboard")
        stats_tab = self.tabview.add("Stats")
        settings_tab = self.tabview.add("Settings")

        # Configure tab grids
        scanner_tab.grid_rowconfigure(0, weight=1)
        scanner_tab.grid_columnconfigure(0, weight=1)

        bot_tab.grid_rowconfigure(0, weight=1)
        bot_tab.grid_columnconfigure(0, weight=1)

        dashboard_tab.grid_rowconfigure(0, weight=1)
        dashboard_tab.grid_columnconfigure(0, weight=1)

        stats_tab.grid_rowconfigure(0, weight=1)
        stats_tab.grid_columnconfigure(0, weight=1)

        settings_tab.grid_rowconfigure(0, weight=1)
        settings_tab.grid_columnconfigure(0, weight=1)

        # Create pages
        self.scanner_page = ScannerPage(
            scanner_tab,
            config_manager=self.config_manager,
            on_opportunity_select=self._on_opportunity_selected
        )
        self.scanner_page.grid(row=0, column=0, sticky="nsew")

        self.bot_page = BotPage(
            bot_tab,
            executor=self.executor
        )
        self.bot_page.grid(row=0, column=0, sticky="nsew")

        self.dashboard_page = DashboardPage(
            dashboard_tab,
            executor=self.executor
        )
        self.dashboard_page.grid(row=0, column=0, sticky="nsew")

        self.stats_page = StatsPage(stats_tab)
        self.stats_page.grid(row=0, column=0, sticky="nsew")

        self.settings_page = SettingsPage(
            settings_tab,
            config_manager=self.config_manager
        )
        self.settings_page.grid(row=0, column=0, sticky="nsew")

    def _on_opportunity_selected(self, opportunity):
        """
        Handle opportunity selection from scanner.

        Args:
            opportunity: Selected Opportunity object
        """
        # Switch to Bot tab
        self.tabview.set("Bot")

        # Set opportunity in bot page
        self.bot_page.set_opportunity(opportunity)

    def run(self):
        """Run the application."""
        print("[App] Starting Funding Farming Bot v2.0...")
        print("[App] Glassmorphism theme loaded")
        print(f"[App] Configured platforms: {self.config_manager.get_configured_platforms()}")

        # Start main loop
        self.mainloop()
