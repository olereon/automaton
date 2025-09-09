"""
Design System for Automaton Web Automation Framework

This module provides comprehensive design tokens, component specifications,
and styling utilities for a modern, accessible user interface.

Created by: Design System Architect
Architecture: Semantic design tokens with dark/light theme support
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
import tkinter as tk
from tkinter import ttk

class ThemeMode(Enum):
    """Theme mode enumeration"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class ComponentSize(Enum):
    """Component size enumeration"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"

class ComponentState(Enum):
    """Component state enumeration"""
    DEFAULT = "default"
    HOVER = "hover"
    FOCUS = "focus"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    SUCCESS = "success"

class DesignTokens:
    """
    Comprehensive design token system following modern design principles.
    Provides semantic color tokens, typography scales, spacing system,
    and accessibility-compliant color combinations.
    """
    
    # =============================================================================
    # COLOR SYSTEM - Semantic Tokens
    # =============================================================================
    
    # Core Brand Colors
    BRAND_PRIMARY = {
        ThemeMode.LIGHT: "#0066CC",      # Professional blue
        ThemeMode.DARK: "#3399FF"        # Lighter blue for dark theme
    }
    
    BRAND_SECONDARY = {
        ThemeMode.LIGHT: "#6B46C1",      # Purple accent  
        ThemeMode.DARK: "#8B5CF6"        # Lighter purple for dark theme
    }
    
    # Surface Colors (Backgrounds & Panels)
    SURFACE_PRIMARY = {
        ThemeMode.LIGHT: "#FFFFFF",      # Pure white
        ThemeMode.DARK: "#1E1E1E"        # VS Code dark
    }
    
    SURFACE_SECONDARY = {
        ThemeMode.LIGHT: "#F8F9FA",      # Light gray surface
        ThemeMode.DARK: "#252526"        # Medium dark surface
    }
    
    SURFACE_TERTIARY = {
        ThemeMode.LIGHT: "#F0F2F5",      # Subtle gray surface
        ThemeMode.DARK: "#2D2D30"        # Darker surface for depth
    }
    
    SURFACE_ELEVATED = {
        ThemeMode.LIGHT: "#FFFFFF",      # White with elevation
        ThemeMode.DARK: "#333333"        # Elevated dark surface
    }
    
    # Input & Interactive Elements
    INPUT_BACKGROUND = {
        ThemeMode.LIGHT: "#FFFFFF",      # Clean white inputs
        ThemeMode.DARK: "#3C3C3C"        # Dark input background
    }
    
    INPUT_BORDER = {
        ThemeMode.LIGHT: "#D1D5DB",      # Light border
        ThemeMode.DARK: "#555555"        # Subtle dark border
    }
    
    INPUT_BORDER_FOCUS = {
        ThemeMode.LIGHT: "#3399FF",      # Blue focus ring
        ThemeMode.DARK: "#66B3FF"        # Brighter blue for dark theme
    }
    
    # Text Colors (Hierarchy)
    TEXT_PRIMARY = {
        ThemeMode.LIGHT: "#1F2937",      # Near black
        ThemeMode.DARK: "#F3F4F6"        # Near white
    }
    
    TEXT_SECONDARY = {
        ThemeMode.LIGHT: "#6B7280",      # Medium gray
        ThemeMode.DARK: "#D1D5DB"        # Light gray
    }
    
    TEXT_TERTIARY = {
        ThemeMode.LIGHT: "#9CA3AF",      # Light gray
        ThemeMode.DARK: "#9CA3AF"        # Consistent across themes
    }
    
    TEXT_DISABLED = {
        ThemeMode.LIGHT: "#D1D5DB",      # Very light gray
        ThemeMode.DARK: "#6B7280"        # Medium gray
    }
    
    # State Colors
    STATE_SUCCESS = {
        ThemeMode.LIGHT: "#059669",      # Green
        ThemeMode.DARK: "#10B981"        # Brighter green
    }
    
    STATE_WARNING = {
        ThemeMode.LIGHT: "#D97706",      # Orange
        ThemeMode.DARK: "#F59E0B"        # Brighter orange
    }
    
    STATE_ERROR = {
        ThemeMode.LIGHT: "#DC2626",      # Red
        ThemeMode.DARK: "#F87171"        # Softer red
    }
    
    STATE_INFO = {
        ThemeMode.LIGHT: "#2563EB",      # Blue
        ThemeMode.DARK: "#60A5FA"        # Lighter blue
    }
    
    # =============================================================================
    # TYPOGRAPHY SYSTEM
    # =============================================================================
    
    # Font Families
    FONT_FAMILY_PRIMARY = "Inter, 'Segoe UI', system-ui, sans-serif"
    FONT_FAMILY_MONO = "'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace"
    
    # Typography Scale (rem values converted to pixel approximations)
    TYPOGRAPHY_SCALE = {
        'xs': {'size': 11, 'line_height': 16},      # Small text
        'sm': {'size': 13, 'line_height': 20},      # Body small
        'base': {'size': 15, 'line_height': 24},    # Body text
        'lg': {'size': 17, 'line_height': 28},      # Large text
        'xl': {'size': 19, 'line_height': 32},      # Headings
        '2xl': {'size': 23, 'line_height': 32},     # Large headings
        '3xl': {'size': 28, 'line_height': 36},     # Display text
        '4xl': {'size': 35, 'line_height': 40}      # Hero text
    }
    
    # Font Weights
    FONT_WEIGHT_NORMAL = 'normal'
    FONT_WEIGHT_MEDIUM = 'normal'  # Tkinter limitation
    FONT_WEIGHT_BOLD = 'bold'
    
    # =============================================================================
    # SPACING SYSTEM
    # =============================================================================
    
    # Spacing tokens based on 4px grid
    SPACING = {
        'xs': 4,      # 0.25rem
        'sm': 8,      # 0.5rem  
        'base': 12,   # 0.75rem
        'md': 16,     # 1rem
        'lg': 24,     # 1.5rem
        'xl': 32,     # 2rem
        '2xl': 48,    # 3rem
        '3xl': 64,    # 4rem
        '4xl': 96     # 6rem
    }
    
    # Component-specific spacing
    PADDING = {
        ComponentSize.SMALL: {'x': 12, 'y': 6},
        ComponentSize.MEDIUM: {'x': 16, 'y': 8},
        ComponentSize.LARGE: {'x': 20, 'y': 10},
        ComponentSize.EXTRA_LARGE: {'x': 24, 'y': 12}
    }
    
    # =============================================================================
    # COMPONENT SPECIFICATIONS
    # =============================================================================
    
    # Border Radius
    BORDER_RADIUS = {
        'none': 0,
        'sm': 4,
        'base': 6,
        'md': 8,
        'lg': 12,
        'full': 999
    }
    
    # Border Widths
    BORDER_WIDTH = {
        'none': 0,
        'thin': 1,
        'base': 2,
        'thick': 4
    }
    
    # Elevation/Shadow System
    ELEVATION = {
        'none': {'offset': (0, 0), 'blur': 0, 'color': 'transparent'},
        'sm': {'offset': (0, 1), 'blur': 3, 'color': 'rgba(0, 0, 0, 0.1)'},
        'base': {'offset': (0, 4), 'blur': 6, 'color': 'rgba(0, 0, 0, 0.1)'},
        'md': {'offset': (0, 10), 'blur': 15, 'color': 'rgba(0, 0, 0, 0.1)'},
        'lg': {'offset': (0, 20), 'blur': 25, 'color': 'rgba(0, 0, 0, 0.1)'}
    }

class ComponentLibrary:
    """
    Component specifications and styling utilities for UI elements.
    Provides consistent styling patterns and interaction states.
    """
    
    def __init__(self, theme_mode: ThemeMode = ThemeMode.DARK):
        self.theme_mode = theme_mode
        self.tokens = DesignTokens()
    
    def get_color(self, color_token: Dict[ThemeMode, str]) -> str:
        """Get color value for current theme"""
        return color_token.get(self.theme_mode, color_token[ThemeMode.DARK])
    
    # =============================================================================
    # BUTTON SPECIFICATIONS
    # =============================================================================
    
    def get_button_style(self, 
                        variant: str = 'primary',
                        size: ComponentSize = ComponentSize.MEDIUM,
                        state: ComponentState = ComponentState.DEFAULT) -> Dict[str, Any]:
        """
        Get comprehensive button styling configuration
        
        Variants: 'primary', 'secondary', 'outline', 'ghost', 'danger'
        """
        
        # Base button styles
        base_styles = {
            'font': ('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size'], self.tokens.FONT_WEIGHT_MEDIUM),
            'relief': tk.FLAT,
            'bd': self.tokens.BORDER_WIDTH['thin'],
            'cursor': 'hand2'
        }
        
        # Size-specific styles
        size_styles = {
            ComponentSize.SMALL: {
                'font': ('Inter', self.tokens.TYPOGRAPHY_SCALE['sm']['size'], self.tokens.FONT_WEIGHT_MEDIUM),
                'padx': self.tokens.PADDING[ComponentSize.SMALL]['x'],
                'pady': self.tokens.PADDING[ComponentSize.SMALL]['y']
            },
            ComponentSize.MEDIUM: {
                'font': ('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size'], self.tokens.FONT_WEIGHT_MEDIUM),
                'padx': self.tokens.PADDING[ComponentSize.MEDIUM]['x'],
                'pady': self.tokens.PADDING[ComponentSize.MEDIUM]['y']
            },
            ComponentSize.LARGE: {
                'font': ('Inter', self.tokens.TYPOGRAPHY_SCALE['lg']['size'], self.tokens.FONT_WEIGHT_MEDIUM),
                'padx': self.tokens.PADDING[ComponentSize.LARGE]['x'],
                'pady': self.tokens.PADDING[ComponentSize.LARGE]['y']
            },
            ComponentSize.EXTRA_LARGE: {
                'font': ('Inter', self.tokens.TYPOGRAPHY_SCALE['xl']['size'], self.tokens.FONT_WEIGHT_MEDIUM),
                'padx': self.tokens.PADDING[ComponentSize.EXTRA_LARGE]['x'],
                'pady': self.tokens.PADDING[ComponentSize.EXTRA_LARGE]['y']
            }
        }
        
        # Variant-specific styles
        variant_styles = self._get_button_variant_styles(variant, state)
        
        # Merge all styles
        return {**base_styles, **size_styles[size], **variant_styles}
    
    def _get_button_variant_styles(self, variant: str, state: ComponentState) -> Dict[str, Any]:
        """Get variant and state-specific button styles"""
        
        styles = {}
        
        if variant == 'primary':
            if state == ComponentState.DEFAULT:
                styles.update({
                    'bg': self.get_color(self.tokens.BRAND_PRIMARY),
                    'fg': self.get_color(self.tokens.SURFACE_PRIMARY),
                    'activebackground': self._darken_color(self.get_color(self.tokens.BRAND_PRIMARY), 0.1)
                })
            elif state == ComponentState.HOVER:
                styles.update({
                    'bg': self._darken_color(self.get_color(self.tokens.BRAND_PRIMARY), 0.05),
                    'fg': self.get_color(self.tokens.SURFACE_PRIMARY)
                })
            elif state == ComponentState.DISABLED:
                styles.update({
                    'bg': self.get_color(self.tokens.TEXT_DISABLED),
                    'fg': self.get_color(self.tokens.TEXT_TERTIARY),
                    'cursor': 'arrow'
                })
                
        elif variant == 'secondary':
            if state == ComponentState.DEFAULT:
                styles.update({
                    'bg': self.get_color(self.tokens.SURFACE_TERTIARY),
                    'fg': self.get_color(self.tokens.TEXT_PRIMARY),
                    'bd': self.tokens.BORDER_WIDTH['thin']
                })
            elif state == ComponentState.HOVER:
                styles.update({
                    'bg': self.get_color(self.tokens.SURFACE_SECONDARY),
                    'fg': self.get_color(self.tokens.TEXT_PRIMARY)
                })
                
        elif variant == 'outline':
            if state == ComponentState.DEFAULT:
                styles.update({
                    'bg': self.get_color(self.tokens.SURFACE_PRIMARY),  # Use surface color instead of transparent
                    'fg': self.get_color(self.tokens.BRAND_PRIMARY),
                    'relief': tk.SOLID,
                    'bd': self.tokens.BORDER_WIDTH['thin']
                })
            elif state == ComponentState.HOVER:
                styles.update({
                    'bg': self.get_color(self.tokens.BRAND_PRIMARY),
                    'fg': self.get_color(self.tokens.SURFACE_PRIMARY)
                })
                
        elif variant == 'danger':
            if state == ComponentState.DEFAULT:
                styles.update({
                    'bg': self.get_color(self.tokens.STATE_ERROR),
                    'fg': self.get_color(self.tokens.SURFACE_PRIMARY),
                    'activebackground': self._darken_color(self.get_color(self.tokens.STATE_ERROR), 0.1)
                })
            elif state == ComponentState.HOVER:
                styles.update({
                    'bg': self._darken_color(self.get_color(self.tokens.STATE_ERROR), 0.05),
                    'fg': self.get_color(self.tokens.SURFACE_PRIMARY)
                })
        
        return styles
    
    # =============================================================================
    # INPUT FIELD SPECIFICATIONS
    # =============================================================================
    
    def get_input_style(self, 
                       size: ComponentSize = ComponentSize.MEDIUM,
                       state: ComponentState = ComponentState.DEFAULT) -> Dict[str, Any]:
        """Get input field styling configuration"""
        
        base_styles = {
            'bg': self.get_color(self.tokens.INPUT_BACKGROUND),
            'fg': self.get_color(self.tokens.TEXT_PRIMARY),
            'insertbackground': self.get_color(self.tokens.TEXT_PRIMARY),  # Cursor color
            'relief': tk.SOLID,
            'bd': self.tokens.BORDER_WIDTH['thin'],
            'highlightthickness': 2,
            'font': ('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size'], self.tokens.FONT_WEIGHT_NORMAL)
        }
        
        # State-specific styling
        if state == ComponentState.DEFAULT:
            base_styles.update({
                'highlightcolor': self.get_color(self.tokens.INPUT_BORDER),
                'highlightbackground': self.get_color(self.tokens.INPUT_BORDER)
            })
        elif state == ComponentState.FOCUS:
            base_styles.update({
                'highlightcolor': self.get_color(self.tokens.INPUT_BORDER_FOCUS),
                'highlightbackground': self.get_color(self.tokens.INPUT_BORDER_FOCUS)
            })
        elif state == ComponentState.ERROR:
            base_styles.update({
                'highlightcolor': self.get_color(self.tokens.STATE_ERROR),
                'highlightbackground': self.get_color(self.tokens.STATE_ERROR)
            })
        elif state == ComponentState.SUCCESS:
            base_styles.update({
                'highlightcolor': self.get_color(self.tokens.STATE_SUCCESS),
                'highlightbackground': self.get_color(self.tokens.STATE_SUCCESS)
            })
        elif state == ComponentState.DISABLED:
            base_styles.update({
                'bg': self.get_color(self.tokens.SURFACE_TERTIARY),
                'fg': self.get_color(self.tokens.TEXT_DISABLED),
                'state': 'disabled'
            })
        
        return base_styles
    
    # =============================================================================
    # PANEL & CONTAINER SPECIFICATIONS
    # =============================================================================
    
    def get_panel_style(self, 
                       elevation: str = 'base',
                       variant: str = 'primary') -> Dict[str, Any]:
        """Get panel/container styling configuration"""
        
        base_styles = {
            'relief': tk.FLAT,
            'bd': 0
        }
        
        # Variant-specific backgrounds
        if variant == 'primary':
            base_styles['bg'] = self.get_color(self.tokens.SURFACE_PRIMARY)
        elif variant == 'secondary':
            base_styles['bg'] = self.get_color(self.tokens.SURFACE_SECONDARY)
        elif variant == 'tertiary':
            base_styles['bg'] = self.get_color(self.tokens.SURFACE_TERTIARY)
        elif variant == 'elevated':
            base_styles['bg'] = self.get_color(self.tokens.SURFACE_ELEVATED)
            base_styles['relief'] = tk.RAISED
            base_styles['bd'] = 1
        
        return base_styles
    
    # =============================================================================
    # TYPOGRAPHY SPECIFICATIONS
    # =============================================================================
    
    def get_text_style(self, 
                      variant: str = 'body',
                      weight: str = 'normal') -> Dict[str, Any]:
        """
        Get text styling configuration
        
        Variants: 'hero', 'heading1', 'heading2', 'heading3', 'body', 'caption', 'mono'
        """
        
        variant_mapping = {
            'hero': '4xl',
            'heading1': '3xl',
            'heading2': '2xl', 
            'heading3': 'xl',
            'body': 'base',
            'body-large': 'lg',
            'caption': 'sm',
            'small': 'xs'
        }
        
        scale_key = variant_mapping.get(variant, 'base')
        scale_info = self.tokens.TYPOGRAPHY_SCALE[scale_key]
        
        base_styles = {
            'fg': self.get_color(self.tokens.TEXT_PRIMARY),
            'font': ('Inter', scale_info['size'], weight),
            'bg': self.get_color(self.tokens.SURFACE_PRIMARY)  # Use surface color instead of transparent
        }
        
        # Variant-specific adjustments
        if variant in ['heading1', 'heading2', 'heading3']:
            base_styles['font'] = ('Inter', scale_info['size'], 'bold')
            
        elif variant == 'mono':
            base_styles['font'] = (self.tokens.FONT_FAMILY_MONO.split(',')[0].strip("'"), 
                                 scale_info['size'], weight)
        
        return base_styles
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a hex color by a factor (0.0 to 1.0)"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * (1 - factor))) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
    
    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Lighten a hex color by a factor (0.0 to 1.0)"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        lightened = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
        return f"#{lightened[0]:02x}{lightened[1]:02x}{lightened[2]:02x}"
    
    def get_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors (WCAG compliance check)"""
        def get_luminance(hex_color: str) -> float:
            hex_color = hex_color.lstrip('#')
            rgb = [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
            rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
            return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        
        lum1 = get_luminance(color1)
        lum2 = get_luminance(color2)
        
        if lum1 > lum2:
            return (lum1 + 0.05) / (lum2 + 0.05)
        else:
            return (lum2 + 0.05) / (lum1 + 0.05)
    
    def is_wcag_compliant(self, fg_color: str, bg_color: str, level: str = 'AA') -> bool:
        """Check if color combination meets WCAG contrast requirements"""
        ratio = self.get_contrast_ratio(fg_color, bg_color)
        
        if level == 'AA':
            return ratio >= 4.5  # Normal text
        elif level == 'AAA':
            return ratio >= 7.0  # Enhanced
        elif level == 'AA_LARGE':
            return ratio >= 3.0  # Large text (18pt+ or 14pt+ bold)
        
        return False

class ModernTkinterTheme:
    """
    Modern theme implementation for Tkinter applications.
    Applies design system tokens to create consistent, professional UI.
    """
    
    def __init__(self, theme_mode: ThemeMode = ThemeMode.DARK):
        self.theme_mode = theme_mode
        self.component_lib = ComponentLibrary(theme_mode)
        self.tokens = DesignTokens()
    
    def apply_to_root(self, root: tk.Tk) -> None:
        """Apply theme to root window"""
        root.configure(bg=self.component_lib.get_color(self.tokens.SURFACE_PRIMARY))
        
        # Configure default font
        root.option_add('*Font', f'Inter {self.tokens.TYPOGRAPHY_SCALE["base"]["size"]}')
    
    def configure_ttk_styles(self, style: ttk.Style) -> None:
        """Configure ttk.Style with modern design tokens"""
        
        # Configure theme
        style.theme_use('clam')
        
        # Color palette
        bg_primary = self.component_lib.get_color(self.tokens.SURFACE_PRIMARY)
        bg_secondary = self.component_lib.get_color(self.tokens.SURFACE_SECONDARY)
        bg_tertiary = self.component_lib.get_color(self.tokens.SURFACE_TERTIARY)
        text_primary = self.component_lib.get_color(self.tokens.TEXT_PRIMARY)
        text_secondary = self.component_lib.get_color(self.tokens.TEXT_SECONDARY)
        accent = self.component_lib.get_color(self.tokens.BRAND_PRIMARY)
        
        # Base styles
        style.configure('TFrame', background=bg_primary)
        style.configure('TLabel', 
                       background=bg_primary, 
                       foreground=text_primary,
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size']))
        
        # LabelFrame (panels with titles)
        style.configure('TLabelFrame', 
                       background=bg_primary,
                       foreground=text_primary,
                       borderwidth=1,
                       relief='solid')
        style.configure('TLabelFrame.Label',
                       background=bg_primary,
                       foreground=text_primary,
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['lg']['size'], 'bold'))
        
        # Buttons
        style.configure('TButton',
                       background=accent,
                       foreground=bg_primary,
                       borderwidth=0,
                       focuscolor='none',
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size']))
        style.map('TButton',
                 background=[('active', self.component_lib._darken_color(accent, 0.1)),
                           ('pressed', self.component_lib._darken_color(accent, 0.2))])
        
        # Entry fields
        style.configure('TEntry',
                       fieldbackground=self.component_lib.get_color(self.tokens.INPUT_BACKGROUND),
                       foreground=text_primary,
                       borderwidth=1,
                       insertcolor=text_primary,
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size']))
        
        # Combobox
        style.configure('TCombobox',
                       fieldbackground=self.component_lib.get_color(self.tokens.INPUT_BACKGROUND),
                       foreground=text_primary,
                       borderwidth=1,
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size']))
        
        # Checkbutton
        style.configure('TCheckbutton',
                       background=bg_primary,
                       foreground=text_primary,
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size']))
        
        # Notebook (tabs)
        style.configure('TNotebook',
                       background=bg_primary,
                       borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=bg_tertiary,
                       foreground=text_secondary,
                       padding=[16, 8],
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['base']['size']))
        style.map('TNotebook.Tab',
                 background=[('selected', bg_primary),
                           ('active', bg_secondary)],
                 foreground=[('selected', text_primary),
                           ('active', text_primary)])
        
        # Typography variants
        style.configure('Title.TLabel',
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['3xl']['size'], 'bold'),
                       foreground=text_primary,
                       background=bg_primary)
        style.configure('Heading.TLabel',
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['xl']['size'], 'bold'),
                       foreground=text_primary,
                       background=bg_primary)
        style.configure('Caption.TLabel',
                       font=('Inter', self.tokens.TYPOGRAPHY_SCALE['sm']['size']),
                       foreground=text_secondary,
                       background=bg_primary)

# =============================================================================
# ACCESSIBILITY UTILITIES
# =============================================================================

class AccessibilityValidator:
    """Validate design choices against WCAG 2.1 AA standards"""
    
    @staticmethod
    def validate_color_contrast(component_lib: ComponentLibrary, 
                              fg_color: str, 
                              bg_color: str,
                              text_size: str = 'base') -> Dict[str, Any]:
        """Validate color contrast and return compliance results"""
        
        ratio = component_lib.get_contrast_ratio(fg_color, bg_color)
        
        # Determine if text is considered "large" (18pt+ or 14pt+ bold)
        size_info = component_lib.tokens.TYPOGRAPHY_SCALE[text_size]
        is_large_text = size_info['size'] >= 18
        
        return {
            'contrast_ratio': round(ratio, 2),
            'wcag_aa_compliant': component_lib.is_wcag_compliant(fg_color, bg_color, 'AA'),
            'wcag_aaa_compliant': component_lib.is_wcag_compliant(fg_color, bg_color, 'AAA'),
            'wcag_aa_large_compliant': component_lib.is_wcag_compliant(fg_color, bg_color, 'AA_LARGE'),
            'is_large_text': is_large_text,
            'recommendation': 'PASS' if ratio >= 4.5 else 'FAIL - Increase contrast'
        }

# =============================================================================
# USAGE EXAMPLES & COMPONENT FACTORY
# =============================================================================

class ComponentFactory:
    """Factory class for creating pre-styled components"""
    
    def __init__(self, parent: tk.Widget, theme_mode: ThemeMode = ThemeMode.DARK):
        self.parent = parent
        self.component_lib = ComponentLibrary(theme_mode)
    
    def create_button(self, text: str, 
                     variant: str = 'primary',
                     size: ComponentSize = ComponentSize.MEDIUM,
                     command=None, **kwargs) -> tk.Button:
        """Create a styled button with design system tokens"""
        
        style_config = self.component_lib.get_button_style(variant, size)
        style_config.update(kwargs)
        
        button = tk.Button(self.parent, text=text, command=command, **style_config)
        
        # Add hover effects
        def on_enter(event):
            hover_style = self.component_lib.get_button_style(variant, size, ComponentState.HOVER)
            for key, value in hover_style.items():
                if key in ['bg', 'fg']:
                    button.configure(**{key: value})
        
        def on_leave(event):
            normal_style = self.component_lib.get_button_style(variant, size, ComponentState.DEFAULT)
            for key, value in normal_style.items():
                if key in ['bg', 'fg']:
                    button.configure(**{key: value})
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    def create_input(self, textvariable=None, 
                    size: ComponentSize = ComponentSize.MEDIUM,
                    **kwargs) -> tk.Entry:
        """Create a styled input field with design system tokens"""
        
        style_config = self.component_lib.get_input_style(size)
        style_config.update(kwargs)
        
        if textvariable:
            style_config['textvariable'] = textvariable
        
        return tk.Entry(self.parent, **style_config)
    
    def create_panel(self, 
                    elevation: str = 'base',
                    variant: str = 'primary',
                    padding: Optional[int] = None,
                    **kwargs) -> tk.Frame:
        """Create a styled panel/container with design system tokens"""
        
        style_config = self.component_lib.get_panel_style(elevation, variant)
        style_config.update(kwargs)
        
        frame = tk.Frame(self.parent, **style_config)
        
        if padding:
            frame.configure(padx=padding, pady=padding)
        
        return frame
    
    def create_label(self, text: str,
                    variant: str = 'body',
                    weight: str = 'normal',
                    **kwargs) -> tk.Label:
        """Create a styled label with design system tokens"""
        
        style_config = self.component_lib.get_text_style(variant, weight)
        style_config.update(kwargs)
        
        return tk.Label(self.parent, text=text, **style_config)

# Export primary classes for external use
__all__ = [
    'DesignTokens',
    'ComponentLibrary', 
    'ModernTkinterTheme',
    'ComponentFactory',
    'AccessibilityValidator',
    'ThemeMode',
    'ComponentSize', 
    'ComponentState'
]