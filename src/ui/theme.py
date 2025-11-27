"""
Glassmorphism theme for CustomTkinter.

Defines colors, styles, and constants for a modern, translucent UI design.
"""

from typing import Dict, Tuple

# ========== COLOR PALETTE ==========

class GlassTheme:
    """
    Glassmorphism color scheme and styling constants.

    This theme uses a dark blue/purple base with translucent panels,
    subtle borders, and clean typography.
    """

    # Background colors
    BG_PRIMARY = "#0A0E27"          # Deep dark blue (main window background)
    BG_SECONDARY = "#121829"        # Slightly lighter (secondary panels)
    BG_GLASS = "#1A1F3A"            # Semi-transparent glass panels
    BG_GLASS_HOVER = "#252B4A"      # Glass panels on hover
    BG_INPUT = "#1E2442"            # Input fields background
    BG_SIDEBAR = "#0F1428"          # Sidebar background

    # Accent colors
    ACCENT_BLUE = "#3B82F6"         # Primary actions (buttons, highlights)
    ACCENT_CYAN = "#06B6D4"         # Secondary highlights
    ACCENT_PURPLE = "#8B5CF6"       # Tertiary accents
    ACCENT_SUCCESS = "#10B981"      # Positive values, success states
    ACCENT_WARNING = "#F59E0B"      # Warning states
    ACCENT_DANGER = "#EF4444"       # Negative values, danger states

    # Text colors
    TEXT_PRIMARY = "#F9FAFB"        # Main text (pure white)
    TEXT_SECONDARY = "#D1D5DB"      # Secondary text (light gray)
    TEXT_MUTED = "#9CA3AF"          # Muted text (medium gray)
    TEXT_DISABLED = "#6B7280"       # Disabled text (dark gray)

    # Border colors
    BORDER_GLASS = "#374151"        # Glass panel borders
    BORDER_SUBTLE = "#1F2937"       # Subtle borders
    BORDER_FOCUS = "#3B82F6"        # Focused elements

    # Shadow colors
    SHADOW_DARK = "#000000"         # Shadows and overlays

    # Special effects
    GLASS_OPACITY = 0.1             # Opacity for glass effect
    BLUR_RADIUS = 10                # Blur radius (visual reference)

    # ========== GRADIENTS ==========

    @staticmethod
    def gradient_blue() -> Tuple[str, str]:
        """Blue gradient (for buttons, highlights)."""
        return ("#3B82F6", "#2563EB")

    @staticmethod
    def gradient_purple() -> Tuple[str, str]:
        """Purple gradient (for premium features)."""
        return ("#8B5CF6", "#7C3AED")

    @staticmethod
    def gradient_success() -> Tuple[str, str]:
        """Success gradient (for positive actions)."""
        return ("#10B981", "#059669")

    @staticmethod
    def gradient_danger() -> Tuple[str, str]:
        """Danger gradient (for critical actions)."""
        return ("#EF4444", "#DC2626")


# ========== CUSTOMTKINTER THEME DICT ==========

def get_ctk_theme() -> Dict:
    """
    Get CustomTkinter theme dictionary.

    Returns:
        Dictionary compatible with customtkinter.set_default_color_theme()
    """
    return {
        "CTk": {
            "fg_color": [GlassTheme.BG_PRIMARY, GlassTheme.BG_PRIMARY]
        },
        "CTkToplevel": {
            "fg_color": [GlassTheme.BG_PRIMARY, GlassTheme.BG_PRIMARY]
        },
        "CTkFrame": {
            "fg_color": [GlassTheme.BG_GLASS, GlassTheme.BG_GLASS],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS]
        },
        "CTkButton": {
            "fg_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN],
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS]
        },
        "CTkLabel": {
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY]
        },
        "CTkEntry": {
            "fg_color": [GlassTheme.BG_INPUT, GlassTheme.BG_INPUT],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS],
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY],
            "placeholder_text_color": [GlassTheme.TEXT_MUTED, GlassTheme.TEXT_MUTED]
        },
        "CTkTextbox": {
            "fg_color": [GlassTheme.BG_INPUT, GlassTheme.BG_INPUT],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS],
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY]
        },
        "CTkScrollbar": {
            "fg_color": [GlassTheme.BG_SECONDARY, GlassTheme.BG_SECONDARY],
            "button_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "button_hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN]
        },
        "CTkCheckBox": {
            "fg_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN],
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS]
        },
        "CTkSwitch": {
            "fg_color": [GlassTheme.BG_SECONDARY, GlassTheme.BG_SECONDARY],
            "progress_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "button_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY],
            "button_hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN],
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY]
        },
        "CTkProgressBar": {
            "fg_color": [GlassTheme.BG_SECONDARY, GlassTheme.BG_SECONDARY],
            "progress_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS]
        },
        "CTkSlider": {
            "fg_color": [GlassTheme.BG_SECONDARY, GlassTheme.BG_SECONDARY],
            "progress_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "button_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY],
            "button_hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN]
        },
        "CTkOptionMenu": {
            "fg_color": [GlassTheme.BG_INPUT, GlassTheme.BG_INPUT],
            "button_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "button_hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN],
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY]
        },
        "CTkComboBox": {
            "fg_color": [GlassTheme.BG_INPUT, GlassTheme.BG_INPUT],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS],
            "button_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "button_hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN],
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY]
        },
        "CTkSegmentedButton": {
            "fg_color": [GlassTheme.BG_SECONDARY, GlassTheme.BG_SECONDARY],
            "selected_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "selected_hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN],
            "text_color": [GlassTheme.TEXT_SECONDARY, GlassTheme.TEXT_SECONDARY],
            "text_color_disabled": [GlassTheme.TEXT_DISABLED, GlassTheme.TEXT_DISABLED]
        },
        "CTkTabview": {
            "fg_color": [GlassTheme.BG_GLASS, GlassTheme.BG_GLASS],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS],
            "segmented_button_fg_color": [GlassTheme.BG_SECONDARY, GlassTheme.BG_SECONDARY],
            "segmented_button_selected_color": [GlassTheme.ACCENT_BLUE, GlassTheme.ACCENT_BLUE],
            "segmented_button_selected_hover_color": [GlassTheme.ACCENT_CYAN, GlassTheme.ACCENT_CYAN],
            "text_color": [GlassTheme.TEXT_PRIMARY, GlassTheme.TEXT_PRIMARY],
            "text_color_disabled": [GlassTheme.TEXT_DISABLED, GlassTheme.TEXT_DISABLED]
        },
        "CTkScrollableFrame": {
            "fg_color": [GlassTheme.BG_GLASS, GlassTheme.BG_GLASS],
            "border_color": [GlassTheme.BORDER_GLASS, GlassTheme.BORDER_GLASS]
        }
    }


# ========== TYPOGRAPHY ==========

class Typography:
    """Font configurations for different text elements."""

    # Font families
    FONT_FAMILY_PRIMARY = "Segoe UI"
    FONT_FAMILY_MONO = "Consolas"

    # Font sizes
    SIZE_TITLE = 24
    SIZE_HEADING = 18
    SIZE_SUBHEADING = 16
    SIZE_BODY = 14
    SIZE_SMALL = 12
    SIZE_TINY = 10

    # Font weights
    WEIGHT_BOLD = "bold"
    WEIGHT_NORMAL = "normal"

    @staticmethod
    def title() -> Tuple[str, int, str]:
        """Title font configuration."""
        return (Typography.FONT_FAMILY_PRIMARY, Typography.SIZE_TITLE, Typography.WEIGHT_BOLD)

    @staticmethod
    def heading() -> Tuple[str, int, str]:
        """Heading font configuration."""
        return (Typography.FONT_FAMILY_PRIMARY, Typography.SIZE_HEADING, Typography.WEIGHT_BOLD)

    @staticmethod
    def subheading() -> Tuple[str, int, str]:
        """Subheading font configuration."""
        return (Typography.FONT_FAMILY_PRIMARY, Typography.SIZE_SUBHEADING, Typography.WEIGHT_BOLD)

    @staticmethod
    def body() -> Tuple[str, int]:
        """Body text font configuration."""
        return (Typography.FONT_FAMILY_PRIMARY, Typography.SIZE_BODY)

    @staticmethod
    def small() -> Tuple[str, int]:
        """Small text font configuration."""
        return (Typography.FONT_FAMILY_PRIMARY, Typography.SIZE_SMALL)

    @staticmethod
    def mono() -> Tuple[str, int]:
        """Monospace font configuration."""
        return (Typography.FONT_FAMILY_MONO, Typography.SIZE_BODY)


# ========== SPACING ==========

class Spacing:
    """Spacing constants for consistent layout."""

    TINY = 4
    SMALL = 8
    MEDIUM = 16
    LARGE = 24
    XLARGE = 32
    XXLARGE = 48


# ========== COMPONENT SIZES ==========

class ComponentSize:
    """Standard sizes for UI components."""

    # Button heights
    BUTTON_HEIGHT_SMALL = 28
    BUTTON_HEIGHT_MEDIUM = 36
    BUTTON_HEIGHT_LARGE = 44

    # Input heights
    INPUT_HEIGHT = 36

    # Border widths
    BORDER_WIDTH_THIN = 1
    BORDER_WIDTH_MEDIUM = 2
    BORDER_WIDTH_THICK = 3

    # Corner radius
    CORNER_RADIUS_SMALL = 6
    CORNER_RADIUS_MEDIUM = 8
    CORNER_RADIUS_LARGE = 12
    CORNER_RADIUS_XLARGE = 16


# ========== UTILITY FUNCTIONS ==========

def format_currency(value: float) -> str:
    """
    Format a value as USD currency.

    Args:
        value: Numeric value

    Returns:
        Formatted string (e.g., "$1,234.56")
    """
    if value >= 0:
        return f"${value:,.2f}"
    else:
        return f"-${abs(value):,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a value as percentage.

    Args:
        value: Numeric value (e.g., 0.05 for 5%)
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "5.00%")
    """
    return f"{value * 100:.{decimals}f}%"


def get_color_for_value(value: float, positive_color: str = None, negative_color: str = None) -> str:
    """
    Get color based on value (positive/negative).

    Args:
        value: Numeric value
        positive_color: Color for positive values (default: success green)
        negative_color: Color for negative values (default: danger red)

    Returns:
        Color hex string
    """
    if positive_color is None:
        positive_color = GlassTheme.ACCENT_SUCCESS
    if negative_color is None:
        negative_color = GlassTheme.ACCENT_DANGER

    return positive_color if value >= 0 else negative_color
