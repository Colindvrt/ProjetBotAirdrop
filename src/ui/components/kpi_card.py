"""
KPI Card component for displaying key metrics.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

from src.ui.theme import GlassTheme, Typography, Spacing, format_currency, get_color_for_value
from src.ui.components.glass_frame import GlassCard


class KPICard(GlassCard if CTK_AVAILABLE else object):
    """
    A card component for displaying a key performance indicator.

    Features:
    - Large value display
    - Label and subtitle
    - Optional icon/emoji
    - Color-coded for positive/negative values
    """

    def __init__(
        self,
        master,
        label: str,
        value: str = "0",
        subtitle: str = "",
        icon: str = "",
        value_color: str = None,
        **kwargs
    ):
        """
        Initialize KPI card.

        Args:
            master: Parent widget
            label: KPI label (e.g., "Total PnL")
            value: KPI value (e.g., "$1,234.56")
            subtitle: Optional subtitle (e.g., "+5.2%")
            icon: Optional icon/emoji
            value_color: Color for the value (auto if None)
            **kwargs: Additional arguments for GlassCard
        """
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required for KPICard")

        super().__init__(master, padding=Spacing.MEDIUM, **kwargs)

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Icon (if provided)
        if icon:
            icon_label = ctk.CTkLabel(
                self,
                text=icon,
                font=Typography.heading(),
                text_color=GlassTheme.TEXT_SECONDARY
            )
            icon_label.grid(row=row, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, 0))
            row += 1

        # Label
        self.label_widget = ctk.CTkLabel(
            self,
            text=label,
            font=Typography.small(),
            text_color=GlassTheme.TEXT_SECONDARY,
            anchor="w"
        )
        self.label_widget.grid(row=row, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.MEDIUM, Spacing.TINY))
        row += 1

        # Value
        self.value_widget = ctk.CTkLabel(
            self,
            text=value,
            font=Typography.title(),
            text_color=value_color or GlassTheme.TEXT_PRIMARY,
            anchor="w"
        )
        self.value_widget.grid(row=row, column=0, sticky="w", padx=Spacing.MEDIUM, pady=0)
        row += 1

        # Subtitle (if provided)
        if subtitle:
            self.subtitle_widget = ctk.CTkLabel(
                self,
                text=subtitle,
                font=Typography.small(),
                text_color=GlassTheme.TEXT_MUTED,
                anchor="w"
            )
            self.subtitle_widget.grid(row=row, column=0, sticky="w", padx=Spacing.MEDIUM, pady=(Spacing.TINY, Spacing.MEDIUM))
        else:
            # Add bottom padding
            self.grid_rowconfigure(row, minsize=Spacing.MEDIUM)

    def update_value(self, value: str, value_color: str = None):
        """
        Update the displayed value.

        Args:
            value: New value string
            value_color: New color (optional)
        """
        self.value_widget.configure(text=value)
        if value_color:
            self.value_widget.configure(text_color=value_color)

    def update_subtitle(self, subtitle: str):
        """
        Update the subtitle.

        Args:
            subtitle: New subtitle string
        """
        if hasattr(self, 'subtitle_widget'):
            self.subtitle_widget.configure(text=subtitle)


class NumericKPICard(KPICard):
    """
    KPI Card specialized for numeric values with auto-formatting.
    """

    def __init__(
        self,
        master,
        label: str,
        value: float = 0.0,
        format_type: str = "currency",  # "currency", "percentage", "number"
        **kwargs
    ):
        """
        Initialize numeric KPI card.

        Args:
            master: Parent widget
            label: KPI label
            value: Numeric value
            format_type: How to format the value ("currency", "percentage", "number")
            **kwargs: Additional arguments for KPICard
        """
        self.format_type = format_type
        self.numeric_value = value

        # Format initial value
        formatted_value = self._format_value(value)
        value_color = get_color_for_value(value)

        super().__init__(
            master,
            label=label,
            value=formatted_value,
            value_color=value_color,
            **kwargs
        )

    def _format_value(self, value: float) -> str:
        """Format numeric value based on format_type."""
        if self.format_type == "currency":
            return format_currency(value)
        elif self.format_type == "percentage":
            return f"{value:.2f}%"
        elif self.format_type == "number":
            return f"{value:,.2f}"
        else:
            return str(value)

    def set_value(self, value: float):
        """
        Set new numeric value with auto-formatting.

        Args:
            value: New numeric value
        """
        self.numeric_value = value
        formatted = self._format_value(value)
        color = get_color_for_value(value)
        self.update_value(formatted, color)
