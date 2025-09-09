"""
Modern UI Components for Automaton Web Automation Framework

Advanced component implementations using the design system.
Provides drop-in replacements for standard Tkinter components with
modern styling, interaction states, and accessibility features.

Created by: Design System Architect  
Integration: Ready for GUI module replacement
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any, Union
from enum import Enum

from .design_system import (
    DesignTokens, ComponentLibrary, ThemeMode, ComponentSize, 
    ComponentState, ModernTkinterTheme
)

class ModernButton(tk.Button):
    """
    Modern button component with hover effects, multiple variants,
    and design system integration.
    
    Features:
    - Hover/focus states with smooth transitions
    - Multiple variants (primary, secondary, outline, ghost, danger)
    - Size variants (small, medium, large, extra_large)
    - Accessibility support with proper focus indicators
    - Loading state support
    """
    
    def __init__(self, parent: tk.Widget, 
                 text: str = "",
                 variant: str = 'primary',
                 size: ComponentSize = ComponentSize.MEDIUM,
                 command: Optional[Callable] = None,
                 theme_mode: ThemeMode = ThemeMode.DARK,
                 loading: bool = False,
                 disabled: bool = False,
                 **kwargs):
        
        self.variant = variant
        self.size = size
        self.theme_mode = theme_mode
        self.loading = loading
        self.component_lib = ComponentLibrary(theme_mode)
        self.original_text = text
        
        # Get initial styling
        style_config = self.component_lib.get_button_style(
            variant, size, ComponentState.DISABLED if disabled else ComponentState.DEFAULT
        )
        
        # Remove custom keys that aren't valid Button options
        button_config = {k: v for k, v in style_config.items() 
                        if k not in ['padx', 'pady']}
        
        # Merge with provided kwargs
        button_config.update(kwargs)
        
        super().__init__(parent, text=text, command=command, **button_config)
        
        # Apply padding separately
        if 'padx' in style_config:
            self.configure(padx=style_config['padx'])
        if 'pady' in style_config:
            self.configure(pady=style_config['pady'])
        
        # Set up interaction states
        self._setup_interaction_states()
        
        # Handle loading state
        if loading:
            self.set_loading(True)
        
        # Handle disabled state
        if disabled:
            self.configure(state='disabled')
    
    def _setup_interaction_states(self):
        """Set up hover and focus state handlers"""
        
        def on_enter(event):
            if self['state'] != 'disabled' and not self.loading:
                hover_style = self.component_lib.get_button_style(
                    self.variant, self.size, ComponentState.HOVER
                )
                self.configure(bg=hover_style.get('bg', self['bg']))
        
        def on_leave(event):
            if self['state'] != 'disabled' and not self.loading:
                normal_style = self.component_lib.get_button_style(
                    self.variant, self.size, ComponentState.DEFAULT
                )
                self.configure(bg=normal_style.get('bg', self['bg']))
        
        def on_focus(event):
            if self['state'] != 'disabled' and not self.loading:
                # Add visual focus indicator
                self.configure(relief=tk.SOLID, bd=2)
        
        def on_blur(event):
            if self['state'] != 'disabled' and not self.loading:
                # Remove focus indicator
                self.configure(relief=tk.FLAT, bd=1)
        
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave) 
        self.bind("<FocusIn>", on_focus)
        self.bind("<FocusOut>", on_blur)
    
    def set_loading(self, loading: bool):
        """Set button loading state"""
        self.loading = loading
        
        if loading:
            self.configure(text="Loading...", state='disabled')
            # Optionally add spinner animation here
        else:
            self.configure(text=self.original_text, state='normal')
    
    def set_variant(self, variant: str):
        """Change button variant dynamically"""
        self.variant = variant
        style_config = self.component_lib.get_button_style(
            variant, self.size, ComponentState.DEFAULT
        )
        
        # Update relevant style properties
        for key, value in style_config.items():
            if key in ['bg', 'fg', 'activebackground']:
                self.configure(**{key: value})

class ModernEntry(tk.Entry):
    """
    Modern input field with focus states, validation styling,
    and accessibility features.
    
    Features:
    - Focus ring indicators
    - Error/success state styling
    - Placeholder text support
    - Input validation with visual feedback
    - Clear button option
    """
    
    def __init__(self, parent: tk.Widget,
                 placeholder: str = "",
                 size: ComponentSize = ComponentSize.MEDIUM,
                 theme_mode: ThemeMode = ThemeMode.DARK,
                 validation_state: Optional[ComponentState] = None,
                 show_clear_button: bool = False,
                 **kwargs):
        
        self.placeholder = placeholder
        self.size = size
        self.theme_mode = theme_mode
        self.validation_state = validation_state
        self.show_clear_button = show_clear_button
        self.component_lib = ComponentLibrary(theme_mode)
        self.has_focus = False
        self.showing_placeholder = False
        
        # Get styling configuration
        style_config = self.component_lib.get_input_style(
            size, validation_state or ComponentState.DEFAULT
        )
        
        # Merge with provided kwargs
        style_config.update(kwargs)
        
        super().__init__(parent, **style_config)
        
        # Set up interaction states
        self._setup_interaction_states()
        
        # Set up placeholder if provided
        if placeholder:
            self._setup_placeholder()
        
        # Set up clear button if requested
        if show_clear_button:
            self._setup_clear_button()
    
    def _setup_interaction_states(self):
        """Set up focus and validation state handlers"""
        
        def on_focus_in(event):
            self.has_focus = True
            focus_style = self.component_lib.get_input_style(
                self.size, ComponentState.FOCUS
            )
            
            # Update border color for focus
            self.configure(
                highlightcolor=focus_style['highlightcolor'],
                highlightbackground=focus_style['highlightcolor']
            )
            
            # Handle placeholder
            if self.showing_placeholder:
                self.delete(0, tk.END)
                self.configure(fg=self.component_lib.get_color(
                    self.component_lib.tokens.TEXT_PRIMARY
                ))
                self.showing_placeholder = False
        
        def on_focus_out(event):
            self.has_focus = False
            
            # Restore normal border
            if self.validation_state:
                style = self.component_lib.get_input_style(self.size, self.validation_state)
            else:
                style = self.component_lib.get_input_style(self.size, ComponentState.DEFAULT)
            
            self.configure(
                highlightcolor=style['highlightcolor'],
                highlightbackground=style['highlightbackground']
            )
            
            # Handle placeholder
            if not self.get() and self.placeholder:
                self.insert(0, self.placeholder)
                self.configure(fg=self.component_lib.get_color(
                    self.component_lib.tokens.TEXT_TERTIARY
                ))
                self.showing_placeholder = True
        
        self.bind("<FocusIn>", on_focus_in)
        self.bind("<FocusOut>", on_focus_out)
    
    def _setup_placeholder(self):
        """Initialize placeholder text"""
        if not self.get():
            self.insert(0, self.placeholder)
            self.configure(fg=self.component_lib.get_color(
                self.component_lib.tokens.TEXT_TERTIARY
            ))
            self.showing_placeholder = True
    
    def _setup_clear_button(self):
        """Add clear button functionality"""
        # This would require a composite widget approach
        # For now, we'll add keyboard shortcut
        def clear_entry(event):
            if event.keysym == 'Escape':
                self.delete(0, tk.END)
        
        self.bind("<Key>", clear_entry)
    
    def set_validation_state(self, state: ComponentState):
        """Update validation state and styling"""
        self.validation_state = state
        
        style_config = self.component_lib.get_input_style(self.size, state)
        
        self.configure(
            highlightcolor=style_config['highlightcolor'],
            highlightbackground=style_config['highlightbackground']
        )
    
    def get_value(self) -> str:
        """Get entry value, handling placeholder text"""
        if self.showing_placeholder:
            return ""
        return self.get()

class ModernFrame(tk.Frame):
    """
    Modern container/panel component with elevation effects,
    semantic variants, and proper spacing.
    
    Features:
    - Multiple surface variants (primary, secondary, tertiary, elevated)
    - Elevation effects with visual depth
    - Consistent padding and margin system
    - Responsive design considerations
    """
    
    def __init__(self, parent: tk.Widget,
                 variant: str = 'primary',
                 elevation: str = 'none',
                 padding: Optional[Union[int, Dict[str, int]]] = None,
                 theme_mode: ThemeMode = ThemeMode.DARK,
                 **kwargs):
        
        self.variant = variant
        self.elevation = elevation
        self.theme_mode = theme_mode
        self.component_lib = ComponentLibrary(theme_mode)
        
        # Get styling configuration
        style_config = self.component_lib.get_panel_style(elevation, variant)
        
        # Merge with provided kwargs
        style_config.update(kwargs)
        
        super().__init__(parent, **style_config)
        
        # Apply padding if specified
        if padding:
            self._apply_padding(padding)
    
    def _apply_padding(self, padding: Union[int, Dict[str, int]]):
        """Apply padding using grid or pack configuration"""
        if isinstance(padding, int):
            self.configure(padx=padding, pady=padding)
        elif isinstance(padding, dict):
            padx = padding.get('x', padding.get('horizontal', 0))
            pady = padding.get('y', padding.get('vertical', 0))
            self.configure(padx=padx, pady=pady)

class ModernLabel(tk.Label):
    """
    Modern label component with typography variants,
    semantic text styling, and accessibility features.
    
    Features:
    - Typography scale support (hero, heading1-3, body, caption)
    - Semantic text colors (primary, secondary, tertiary, disabled)
    - Font weight variations
    - Proper line height and spacing
    """
    
    def __init__(self, parent: tk.Widget,
                 text: str = "",
                 variant: str = 'body',
                 weight: str = 'normal',
                 color: Optional[str] = None,
                 theme_mode: ThemeMode = ThemeMode.DARK,
                 **kwargs):
        
        self.variant = variant
        self.weight = weight
        self.theme_mode = theme_mode
        self.component_lib = ComponentLibrary(theme_mode)
        
        # Get styling configuration
        style_config = self.component_lib.get_text_style(variant, weight)
        
        # Override color if specified
        if color:
            if color in ['primary', 'secondary', 'tertiary', 'disabled']:
                color_token_map = {
                    'primary': self.component_lib.tokens.TEXT_PRIMARY,
                    'secondary': self.component_lib.tokens.TEXT_SECONDARY,
                    'tertiary': self.component_lib.tokens.TEXT_TERTIARY,
                    'disabled': self.component_lib.tokens.TEXT_DISABLED
                }
                style_config['fg'] = self.component_lib.get_color(color_token_map[color])
            else:
                style_config['fg'] = color
        
        # Merge with provided kwargs
        style_config.update(kwargs)
        
        super().__init__(parent, text=text, **style_config)
    
    def set_variant(self, variant: str, weight: str = None):
        """Change label variant and weight dynamically"""
        self.variant = variant
        if weight:
            self.weight = weight
        
        style_config = self.component_lib.get_text_style(variant, self.weight)
        
        # Update font configuration
        self.configure(font=style_config['font'])

class ModernNotebook(ttk.Notebook):
    """
    Modern tabbed interface with design system integration.
    
    Features:
    - Modern tab styling with hover effects
    - Consistent spacing and typography
    - Active/inactive state management
    - Keyboard navigation support
    """
    
    def __init__(self, parent: tk.Widget,
                 theme_mode: ThemeMode = ThemeMode.DARK,
                 **kwargs):
        
        self.theme_mode = theme_mode
        self.component_lib = ComponentLibrary(theme_mode)
        
        super().__init__(parent, **kwargs)
        
        # Apply modern styling
        self._apply_modern_styling()
    
    def _apply_modern_styling(self):
        """Apply modern styling to notebook"""
        style = ttk.Style()
        
        # Configure modern tab appearance
        bg_primary = self.component_lib.get_color(self.component_lib.tokens.SURFACE_PRIMARY)
        bg_secondary = self.component_lib.get_color(self.component_lib.tokens.SURFACE_SECONDARY)
        bg_tertiary = self.component_lib.get_color(self.component_lib.tokens.SURFACE_TERTIARY)
        text_primary = self.component_lib.get_color(self.component_lib.tokens.TEXT_PRIMARY)
        text_secondary = self.component_lib.get_color(self.component_lib.tokens.TEXT_SECONDARY)
        
        style.configure('Modern.TNotebook',
                       background=bg_primary,
                       borderwidth=0)
        
        style.configure('Modern.TNotebook.Tab',
                       background=bg_tertiary,
                       foreground=text_secondary,
                       padding=[20, 12],  # More generous padding
                       font=('Inter', 14, 'normal'))
        
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', bg_primary),
                           ('active', bg_secondary)],
                 foreground=[('selected', text_primary),
                           ('active', text_primary)])
        
        self.configure(style='Modern.TNotebook')

class ModernProgressBar(tk.Frame):
    """
    Modern progress bar component with smooth animations
    and semantic color coding.
    
    Features:
    - Smooth progress transitions
    - Multiple variants (primary, success, warning, error)
    - Percentage display option
    - Animated loading states
    """
    
    def __init__(self, parent: tk.Widget,
                 variant: str = 'primary',
                 show_percentage: bool = True,
                 height: int = 8,
                 theme_mode: ThemeMode = ThemeMode.DARK,
                 **kwargs):
        
        self.variant = variant
        self.show_percentage = show_percentage
        self.height = height
        self.theme_mode = theme_mode
        self.component_lib = ComponentLibrary(theme_mode)
        self.progress_value = 0
        
        super().__init__(parent, **kwargs)
        
        self._setup_progress_bar()
    
    def _setup_progress_bar(self):
        """Initialize progress bar components"""
        
        # Background track
        bg_color = self.component_lib.get_color(self.component_lib.tokens.SURFACE_TERTIARY)
        self.configure(bg=bg_color, height=self.height, relief=tk.FLAT)
        
        # Progress fill
        fill_color = self._get_variant_color()
        self.progress_fill = tk.Frame(self, bg=fill_color, height=self.height)
        self.progress_fill.place(x=0, y=0, relwidth=0, relheight=1)
        
        # Percentage label (if enabled)
        if self.show_percentage:
            self.percentage_label = ModernLabel(
                self, text="0%", variant='caption', 
                theme_mode=self.theme_mode
            )
            self.percentage_label.place(relx=0.5, rely=0.5, anchor='center')
    
    def _get_variant_color(self) -> str:
        """Get color for current variant"""
        variant_colors = {
            'primary': self.component_lib.tokens.BRAND_PRIMARY,
            'success': self.component_lib.tokens.STATE_SUCCESS,
            'warning': self.component_lib.tokens.STATE_WARNING,
            'error': self.component_lib.tokens.STATE_ERROR
        }
        
        color_token = variant_colors.get(self.variant, self.component_lib.tokens.BRAND_PRIMARY)
        return self.component_lib.get_color(color_token)
    
    def set_progress(self, percentage: float):
        """Set progress value (0-100)"""
        self.progress_value = max(0, min(100, percentage))
        
        # Update progress fill width
        rel_width = self.progress_value / 100
        self.progress_fill.place(relwidth=rel_width)
        
        # Update percentage label
        if self.show_percentage:
            self.percentage_label.configure(text=f"{int(self.progress_value)}%")

class ModernScrollableFrame(tk.Frame):
    """
    Modern scrollable container with custom scrollbars
    and smooth scrolling behavior.
    
    Features:
    - Custom styled scrollbars
    - Smooth scrolling with mouse wheel
    - Dynamic content sizing
    - Keyboard navigation support
    """
    
    def __init__(self, parent: tk.Widget,
                 theme_mode: ThemeMode = ThemeMode.DARK,
                 **kwargs):
        
        self.theme_mode = theme_mode
        self.component_lib = ComponentLibrary(theme_mode)
        
        super().__init__(parent, **kwargs)
        
        self._setup_scrollable_area()
    
    def _setup_scrollable_area(self):
        """Set up scrollable area with custom styling"""
        
        # Create canvas for scrolling
        self.canvas = tk.Canvas(
            self,
            bg=self.component_lib.get_color(self.component_lib.tokens.SURFACE_PRIMARY),
            highlightthickness=0
        )
        
        # Create scrollbar with modern styling
        scrollbar_bg = self.component_lib.get_color(self.component_lib.tokens.SURFACE_TERTIARY)
        scrollbar_fg = self.component_lib.get_color(self.component_lib.tokens.TEXT_TERTIARY)
        
        self.scrollbar = tk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg=scrollbar_bg,
            troughcolor=scrollbar_bg,
            activebackground=scrollbar_fg,
            width=12
        )
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create inner frame for content
        self.inner_frame = ModernFrame(
            self.canvas, 
            variant='primary',
            theme_mode=self.theme_mode
        )
        
        # Layout components
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner_frame, anchor='nw'
        )
        
        # Bind events
        self._bind_scroll_events()
    
    def _bind_scroll_events(self):
        """Set up scroll event handlers"""
        
        def on_frame_configure(event):
            """Update scroll region when inner frame changes"""
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        
        def on_canvas_configure(event):
            """Update inner frame width when canvas changes"""
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        def on_mousewheel(event):
            """Handle mouse wheel scrolling"""
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.inner_frame.bind('<Configure>', on_frame_configure)
        self.canvas.bind('<Configure>', on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def get_inner_frame(self) -> tk.Frame:
        """Get the inner frame for adding content"""
        return self.inner_frame

# =============================================================================
# COMPONENT SHOWCASE & EXAMPLES
# =============================================================================

class ComponentShowcase(tk.Toplevel):
    """
    Interactive showcase of all modern components.
    Useful for testing and demonstrating design system.
    """
    
    def __init__(self, parent: tk.Tk, theme_mode: ThemeMode = ThemeMode.DARK):
        super().__init__(parent)
        
        self.theme_mode = theme_mode
        self.component_lib = ComponentLibrary(theme_mode)
        
        self.title("Modern Component Showcase")
        self.geometry("800x600")
        
        # Apply theme
        theme = ModernTkinterTheme(theme_mode)
        theme.apply_to_root(self)
        
        self._create_showcase()
    
    def _create_showcase(self):
        """Create component showcase"""
        
        # Create scrollable area
        scrollable = ModernScrollableFrame(self, theme_mode=self.theme_mode)
        scrollable.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        content = scrollable.get_inner_frame()
        
        # Title
        ModernLabel(
            content, 
            text="Modern Component Showcase",
            variant='hero',
            weight='bold',
            theme_mode=self.theme_mode
        ).pack(pady=(0, 30))
        
        # Buttons section
        self._create_button_section(content)
        
        # Inputs section  
        self._create_input_section(content)
        
        # Typography section
        self._create_typography_section(content)
        
        # Progress section
        self._create_progress_section(content)
    
    def _create_button_section(self, parent):
        """Create button showcase section"""
        
        section = ModernFrame(parent, variant='secondary', theme_mode=self.theme_mode)
        section.pack(fill=tk.X, pady=(0, 20), padx=10, ipady=15)
        
        ModernLabel(
            section,
            text="Buttons",
            variant='heading2',
            weight='bold', 
            theme_mode=self.theme_mode
        ).pack(pady=(10, 15))
        
        button_frame = tk.Frame(section, bg=section['bg'])
        button_frame.pack(fill=tk.X, padx=10)
        
        # Button variants
        variants = [
            ('Primary', 'primary'),
            ('Secondary', 'secondary'), 
            ('Outline', 'outline'),
            ('Danger', 'danger')
        ]
        
        for i, (text, variant) in enumerate(variants):
            ModernButton(
                button_frame,
                text=text,
                variant=variant,
                theme_mode=self.theme_mode,
                command=lambda v=variant: print(f"{v} button clicked")
            ).grid(row=0, column=i, padx=5, pady=5)
    
    def _create_input_section(self, parent):
        """Create input showcase section"""
        
        section = ModernFrame(parent, variant='secondary', theme_mode=self.theme_mode) 
        section.pack(fill=tk.X, pady=(0, 20), padx=10, ipady=15)
        
        ModernLabel(
            section,
            text="Input Fields",
            variant='heading2',
            weight='bold',
            theme_mode=self.theme_mode
        ).pack(pady=(10, 15))
        
        input_frame = tk.Frame(section, bg=section['bg'])
        input_frame.pack(fill=tk.X, padx=10)
        
        # Regular input
        ModernLabel(input_frame, text="Regular Input:", theme_mode=self.theme_mode).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        ModernEntry(
            input_frame,
            placeholder="Enter text here...",
            theme_mode=self.theme_mode
        ).grid(row=0, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        
        # Error input
        ModernLabel(input_frame, text="Error State:", theme_mode=self.theme_mode).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        error_entry = ModernEntry(input_frame, theme_mode=self.theme_mode)
        error_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        error_entry.set_validation_state(ComponentState.ERROR)
    
    def _create_typography_section(self, parent):
        """Create typography showcase section"""
        
        section = ModernFrame(parent, variant='secondary', theme_mode=self.theme_mode)
        section.pack(fill=tk.X, pady=(0, 20), padx=10, ipady=15)
        
        ModernLabel(
            section,
            text="Typography Scale",
            variant='heading2',
            weight='bold',
            theme_mode=self.theme_mode
        ).pack(pady=(10, 15))
        
        typo_frame = tk.Frame(section, bg=section['bg'])
        typo_frame.pack(fill=tk.X, padx=10)
        
        # Typography examples
        variants = [
            ('Hero Text', 'hero'),
            ('Heading 1', 'heading1'),
            ('Heading 2', 'heading2'),
            ('Body Text', 'body'),
            ('Caption', 'caption')
        ]
        
        for text, variant in variants:
            ModernLabel(
                typo_frame,
                text=f"{text} - The quick brown fox jumps over the lazy dog",
                variant=variant,
                theme_mode=self.theme_mode
            ).pack(anchor=tk.W, pady=2)
    
    def _create_progress_section(self, parent):
        """Create progress showcase section"""
        
        section = ModernFrame(parent, variant='secondary', theme_mode=self.theme_mode)
        section.pack(fill=tk.X, pady=(0, 20), padx=10, ipady=15)
        
        ModernLabel(
            section,
            text="Progress Indicators",
            variant='heading2', 
            weight='bold',
            theme_mode=self.theme_mode
        ).pack(pady=(10, 15))
        
        progress_frame = tk.Frame(section, bg=section['bg'])
        progress_frame.pack(fill=tk.X, padx=10)
        
        # Progress examples
        variants = [
            ('Primary', 'primary', 75),
            ('Success', 'success', 100),
            ('Warning', 'warning', 45),
            ('Error', 'error', 30)
        ]
        
        for i, (label, variant, value) in enumerate(variants):
            ModernLabel(
                progress_frame,
                text=f"{label} Progress:",
                theme_mode=self.theme_mode
            ).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            progress = ModernProgressBar(
                progress_frame,
                variant=variant,
                theme_mode=self.theme_mode,
                width=200
            )
            progress.grid(row=i, column=1, padx=(10, 0), pady=5, sticky=tk.W)
            progress.set_progress(value)

# Export all modern components
__all__ = [
    'ModernButton',
    'ModernEntry', 
    'ModernFrame',
    'ModernLabel',
    'ModernNotebook',
    'ModernProgressBar',
    'ModernScrollableFrame',
    'ComponentShowcase'
]