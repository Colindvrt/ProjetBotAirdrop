"""
Settings Page - API key configuration.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from src.ui.theme import GlassTheme, Typography, Spacing, ComponentSize
from src.ui.components.glass_frame import GlassCard
from src.config.manager import ConfigManager


class SettingsPage(ctk.CTkScrollableFrame if CTK_AVAILABLE else object):
    """
    Settings page for configuring API keys for all platforms.
    """

    def __init__(self, master, config_manager: ConfigManager, **kwargs):
        """
        Initialize settings page.

        Args:
            master: Parent widget
            config_manager: ConfigManager instance
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

        # Store entry widgets
        self.entries = {}

        self._build_ui()
        self._load_current_config()

    def _build_ui(self):
        """Build the settings UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Title
        title = ctk.CTkLabel(
            self,
            text="API Configuration",
            font=Typography.title(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        title.grid(row=row, column=0, sticky="w", padx=Spacing.LARGE, pady=(Spacing.LARGE, Spacing.MEDIUM))
        row += 1

        # Subtitle
        subtitle = ctk.CTkLabel(
            self,
            text="Configure your API keys for each trading platform",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        subtitle.grid(row=row, column=0, sticky="w", padx=Spacing.LARGE, pady=(0, Spacing.XLARGE))
        row += 1

        # Platform sections
        self._create_hyperliquid_section(row)
        row += 1

        self._create_paradex_section(row)
        row += 1

        self._create_lighter_section(row)
        row += 1

        self._create_extended_section(row)
        row += 1

        # Save button
        save_button = ctk.CTkButton(
            self,
            text="Save Configuration",
            command=self._save_config,
            height=ComponentSize.BUTTON_HEIGHT_LARGE,
            font=Typography.body(),
            fg_color=GlassTheme.ACCENT_BLUE,
            hover_color=GlassTheme.ACCENT_CYAN
        )
        save_button.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.LARGE)

    def _create_hyperliquid_section(self, row):
        """Create Hyperliquid configuration section."""
        card = GlassCard(self)
        card.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)

        card.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            card,
            text="Hyperliquid",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        header.grid(row=0, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        # Private Key
        label = ctk.CTkLabel(
            card,
            text="Private Key:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label.grid(row=1, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="0x...",
            show="*"
        )
        entry.grid(row=2, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.MEDIUM))

        self.entries['hyperliquid_secret'] = entry

    def _create_paradex_section(self, row):
        """Create Paradex configuration section."""
        card = GlassCard(self)
        card.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)

        card.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            card,
            text="Paradex",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        header.grid(row=0, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        # Wallet Address
        label1 = ctk.CTkLabel(
            card,
            text="Wallet Address:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label1.grid(row=1, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry1 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="0x..."
        )
        entry1.grid(row=2, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.SMALL))

        # JWT Token
        label2 = ctk.CTkLabel(
            card,
            text="JWT Token:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label2.grid(row=3, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry2 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="eyJ...",
            show="*"
        )
        entry2.grid(row=4, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.MEDIUM))

        self.entries['paradex_key'] = entry1
        self.entries['paradex_secret'] = entry2

    def _create_lighter_section(self, row):
        """Create Lighter configuration section."""
        card = GlassCard(self)
        card.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)

        card.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            card,
            text="Lighter",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        header.grid(row=0, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        # API Private Key
        label1 = ctk.CTkLabel(
            card,
            text="API Private Key:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label1.grid(row=1, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry1 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="Private key",
            show="*"
        )
        entry1.grid(row=2, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.SMALL))

        # Account Index
        label2 = ctk.CTkLabel(
            card,
            text="Account Index:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label2.grid(row=3, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry2 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="0"
        )
        entry2.grid(row=4, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.SMALL))

        # API Key Index
        label3 = ctk.CTkLabel(
            card,
            text="API Key Index:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label3.grid(row=5, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry3 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="2"
        )
        entry3.grid(row=6, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.MEDIUM))

        self.entries['lighter_key'] = entry1
        self.entries['lighter_account_index'] = entry2
        self.entries['lighter_api_key_index'] = entry3

    def _create_extended_section(self, row):
        """Create Extended (X10) configuration section."""
        card = GlassCard(self)
        card.grid(row=row, column=0, sticky="ew", padx=Spacing.LARGE, pady=Spacing.MEDIUM)

        card.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            card,
            text="Extended (X10)",
            font=Typography.heading(),
            text_color=GlassTheme.TEXT_PRIMARY
        )
        header.grid(row=0, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.SMALL))

        # API Key
        label1 = ctk.CTkLabel(
            card,
            text="API Key:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label1.grid(row=1, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry1 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="API key"
        )
        entry1.grid(row=2, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.SMALL))

        # Public Key
        label2 = ctk.CTkLabel(
            card,
            text="Public Key:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label2.grid(row=3, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry2 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="Public key"
        )
        entry2.grid(row=4, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.SMALL))

        # Private Key
        label3 = ctk.CTkLabel(
            card,
            text="Private Key:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label3.grid(row=5, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry3 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="Private key",
            show="*"
        )
        entry3.grid(row=6, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.SMALL))

        # Vault ID
        label4 = ctk.CTkLabel(
            card,
            text="Vault ID:",
            font=Typography.body(),
            text_color=GlassTheme.TEXT_SECONDARY
        )
        label4.grid(row=7, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.SMALL, 0))

        entry4 = ctk.CTkEntry(
            card,
            height=ComponentSize.INPUT_HEIGHT,
            placeholder_text="Vault ID"
        )
        entry4.grid(row=8, column=0, sticky="ew", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.MEDIUM))

        self.entries['extended_api_key'] = entry1
        self.entries['extended_public_key'] = entry2
        self.entries['extended_private_key'] = entry3
        self.entries['extended_vault_id'] = entry4

    def _load_current_config(self):
        """Load current configuration into entries."""
        # Hyperliquid
        hl_config = self.config_manager.get_platform_config('hyperliquid')
        if hl_config.get('secret'):
            self.entries['hyperliquid_secret'].insert(0, hl_config['secret'])

        # Paradex
        pdx_config = self.config_manager.get_platform_config('paradex')
        if pdx_config.get('key'):
            self.entries['paradex_key'].insert(0, pdx_config['key'])
        if pdx_config.get('secret'):
            self.entries['paradex_secret'].insert(0, pdx_config['secret'])

        # Lighter
        lt_config = self.config_manager.get_platform_config('lighter')
        if lt_config.get('key'):
            self.entries['lighter_key'].insert(0, lt_config['key'])
        if lt_config.get('account_index'):
            self.entries['lighter_account_index'].insert(0, lt_config['account_index'])
        if lt_config.get('api_key_index'):
            self.entries['lighter_api_key_index'].insert(0, lt_config['api_key_index'])

        # Extended
        ext_config = self.config_manager.get_platform_config('extended')
        if ext_config.get('api_key'):
            self.entries['extended_api_key'].insert(0, ext_config['api_key'])
        if ext_config.get('public_key'):
            self.entries['extended_public_key'].insert(0, ext_config['public_key'])
        if ext_config.get('private_key'):
            self.entries['extended_private_key'].insert(0, ext_config['private_key'])
        if ext_config.get('vault_id'):
            self.entries['extended_vault_id'].insert(0, ext_config['vault_id'])

    def _save_config(self):
        """Save configuration from entries."""
        # Hyperliquid
        self.config_manager.update_platform_field(
            'hyperliquid', 'secret', self.entries['hyperliquid_secret'].get()
        )

        # Paradex
        self.config_manager.update_platform_field(
            'paradex', 'key', self.entries['paradex_key'].get()
        )
        self.config_manager.update_platform_field(
            'paradex', 'secret', self.entries['paradex_secret'].get()
        )

        # Lighter
        self.config_manager.update_platform_field(
            'lighter', 'key', self.entries['lighter_key'].get()
        )
        self.config_manager.update_platform_field(
            'lighter', 'account_index', self.entries['lighter_account_index'].get()
        )
        self.config_manager.update_platform_field(
            'lighter', 'api_key_index', self.entries['lighter_api_key_index'].get()
        )

        # Extended
        self.config_manager.update_platform_field(
            'extended', 'api_key', self.entries['extended_api_key'].get()
        )
        self.config_manager.update_platform_field(
            'extended', 'public_key', self.entries['extended_public_key'].get()
        )
        self.config_manager.update_platform_field(
            'extended', 'private_key', self.entries['extended_private_key'].get()
        )
        self.config_manager.update_platform_field(
            'extended', 'vault_id', self.entries['extended_vault_id'].get()
        )

        # Save to file
        self.config_manager.save_config()

        print("[Settings] Configuration saved successfully")
