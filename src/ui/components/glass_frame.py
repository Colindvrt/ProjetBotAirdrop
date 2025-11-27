"""
Glassmorphism frame component.

A translucent frame with subtle borders and hover effects.
"""

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    print("CustomTkinter not installed. Run: pip install customtkinter")
    CTK_AVAILABLE = False

from src.ui.theme import GlassTheme, ComponentSize, Spacing


class GlassFrame(ctk.CTkFrame if CTK_AVAILABLE else object):
    """
    A frame with glassmorphism styling.

    Features:
    - Translucent background
    - Subtle border
    - Rounded corners
    - Optional hover effect
    """

    def __init__(
        self,
        master,
        corner_radius: int = ComponentSize.CORNER_RADIUS_MEDIUM,
        border_width: int = ComponentSize.BORDER_WIDTH_THIN,
        hover_enabled: bool = False,
        **kwargs
    ):
        """
        Initialize glass frame.

        Args:
            master: Parent widget
            corner_radius: Corner radius in pixels
            border_width: Border width in pixels
            hover_enabled: Enable hover effect
            **kwargs: Additional arguments for CTkFrame
        """
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required for GlassFrame")

        # Set default glass styling
        default_kwargs = {
            "fg_color": GlassTheme.BG_GLASS,
            "border_color": GlassTheme.BORDER_GLASS,
            "corner_radius": corner_radius,
            "border_width": border_width,
        }

        # Merge with provided kwargs
        default_kwargs.update(kwargs)

        super().__init__(master, **default_kwargs)

        self.hover_enabled = hover_enabled
        self.original_fg_color = GlassTheme.BG_GLASS

        if hover_enabled:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """Handle mouse enter (hover)."""
        if self.hover_enabled:
            self.configure(fg_color=GlassTheme.BG_GLASS_HOVER)

    def _on_leave(self, event):
        """Handle mouse leave."""
        if self.hover_enabled:
            self.configure(fg_color=self.original_fg_color)


class GlassCard(GlassFrame):
    """
    A glass frame with padding and elevation effect.

    This is a convenience wrapper around GlassFrame with sensible defaults
    for card-like components.
    """

    def __init__(
        self,
        master,
        padding: int = Spacing.MEDIUM,
        **kwargs
    ):
        """
        Initialize glass card.

        Args:
            master: Parent widget
            padding: Internal padding
            **kwargs: Additional arguments for GlassFrame
        """
        super().__init__(
            master,
            corner_radius=ComponentSize.CORNER_RADIUS_LARGE,
            **kwargs
        )

        # Add internal padding
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Store padding for potential use
        self._padding = padding


class GlassSidebar(ctk.CTkFrame if CTK_AVAILABLE else object):
    """
    A glass-styled sidebar for navigation.
    """

    def __init__(self, master, width: int = 200, **kwargs):
        """
        Initialize glass sidebar.

        Args:
            master: Parent widget
            width: Sidebar width
            **kwargs: Additional arguments
        """
        if not CTK_AVAILABLE:
            raise ImportError("CustomTkinter is required for GlassSidebar")

        default_kwargs = {
            "fg_color": GlassTheme.BG_SIDEBAR,
            "border_color": GlassTheme.BORDER_GLASS,
            "corner_radius": 0,
            "border_width": 0,
            "width": width
        }

        default_kwargs.update(kwargs)

        super().__init__(master, **default_kwargs)
