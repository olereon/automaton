#!/usr/bin/env python3.11
"""
Design System Demo for Automaton Web Automation Framework

Interactive demonstration of the modern design system and component library.
Shows all components, theming capabilities, and accessibility features.

Usage:
    python3.11 examples/design_system_demo.py

Features:
    - Component showcase with all variants and states
    - Theme switching (light/dark) demonstration  
    - Accessibility validation tools
    - Interactive component playground
    - Performance and contrast testing

Created by: Design System Architect
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from interfaces.design_system import (
    DesignTokens, ComponentLibrary, ModernTkinterTheme, ComponentFactory,
    AccessibilityValidator, ThemeMode, ComponentSize, ComponentState
)
from interfaces.modern_components import (
    ModernButton, ModernEntry, ModernFrame, ModernLabel, ModernNotebook,
    ModernProgressBar, ModernScrollableFrame, ComponentShowcase
)

class DesignSystemDemo:
    """
    Comprehensive design system demonstration application.
    
    Features:
    - Interactive component showcase
    - Theme switching capabilities  
    - Accessibility testing tools
    - Color contrast validation
    - Performance benchmarking
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Automaton Design System Demo")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize theme system
        self.current_theme = ThemeMode.DARK
        self.component_lib = ComponentLibrary(self.current_theme)
        self.theme = ModernTkinterTheme(self.current_theme)
        self.factory = ComponentFactory(self.root, self.current_theme)
        
        # Apply initial theme
        self._apply_theme()
        
        # Create demo interface
        self._create_interface()
        
        # Set up accessibility validator
        self.accessibility_validator = AccessibilityValidator()
    
    def _apply_theme(self):
        """Apply current theme to the application"""
        self.theme = ModernTkinterTheme(self.current_theme)
        self.theme.apply_to_root(self.root)
        
        # Configure ttk styles
        style = ttk.Style()
        self.theme.configure_ttk_styles(style)
    
    def _create_interface(self):
        """Create the main demo interface"""
        
        # Create main container
        main_container = ModernFrame(
            self.root, 
            variant='primary',
            theme_mode=self.current_theme
        )
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create header
        self._create_header(main_container)
        
        # Create main content area with notebook tabs
        self._create_content_area(main_container)
        
        # Create footer with controls
        self._create_footer(main_container)
    
    def _create_header(self, parent):
        """Create application header with title and theme controls"""
        
        header_frame = ModernFrame(
            parent,
            variant='secondary',
            theme_mode=self.current_theme
        )
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title section
        title_frame = tk.Frame(header_frame, bg=header_frame['bg'])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ModernLabel(
            title_frame,
            text="Automaton Design System",
            variant='hero',
            weight='bold',
            theme_mode=self.current_theme
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        ModernLabel(
            title_frame,
            text="Modern UI Components & Accessibility Framework",
            variant='body-large',
            color='secondary',
            theme_mode=self.current_theme
        ).pack(side=tk.LEFT, padx=(0, 20), pady=15)
        
        # Controls section
        controls_frame = tk.Frame(header_frame, bg=header_frame['bg'])
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Theme switcher
        ModernLabel(
            controls_frame,
            text="Theme:",
            variant='body',
            theme_mode=self.current_theme
        ).pack(side=tk.LEFT, padx=(20, 10), pady=15)
        
        ModernButton(
            controls_frame,
            text="🌙 Dark" if self.current_theme == ThemeMode.DARK else "☀️ Light",
            variant='outline',
            size=ComponentSize.MEDIUM,
            theme_mode=self.current_theme,
            command=self._toggle_theme
        ).pack(side=tk.LEFT, padx=(0, 20), pady=15)
    
    def _create_content_area(self, parent):
        """Create main content area with tabbed interface"""
        
        # Create notebook for different demo sections
        self.notebook = ModernNotebook(parent, theme_mode=self.current_theme)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self._create_components_tab()
        self._create_typography_tab()
        self._create_colors_tab()
        self._create_accessibility_tab()
        self._create_playground_tab()
    
    def _create_components_tab(self):
        """Create components showcase tab"""
        
        # Create scrollable content area
        scrollable = ModernScrollableFrame(self.root, theme_mode=self.current_theme)
        self.notebook.add(scrollable, text="Components")
        
        content = scrollable.get_inner_frame()
        
        # Buttons section
        self._create_button_showcase(content)
        
        # Inputs section
        self._create_input_showcase(content)
        
        # Progress indicators section
        self._create_progress_showcase(content)
        
        # Containers section
        self._create_container_showcase(content)
    
    def _create_button_showcase(self, parent):
        """Create button variants showcase"""
        
        section = self._create_section(parent, "Button Variants & States")
        
        # Button variants
        variants_frame = tk.Frame(section, bg=section['bg'])
        variants_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ModernLabel(
            variants_frame,
            text="Button Variants:",
            variant='heading3',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        
        variants = [
            ('Primary', 'primary'),
            ('Secondary', 'secondary'),
            ('Outline', 'outline'),
            ('Danger', 'danger')
        ]
        
        for i, (text, variant) in enumerate(variants):
            ModernButton(
                variants_frame,
                text=text,
                variant=variant,
                theme_mode=self.current_theme,
                command=lambda v=variant: self._show_message(f"{v.title()} button clicked!")
            ).grid(row=1, column=i, padx=5, pady=5, sticky=tk.W)
        
        # Button sizes
        sizes_frame = tk.Frame(section, bg=section['bg'])
        sizes_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ModernLabel(
            sizes_frame,
            text="Button Sizes:",
            variant='heading3',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        
        sizes = [
            ('Small', ComponentSize.SMALL),
            ('Medium', ComponentSize.MEDIUM),
            ('Large', ComponentSize.LARGE),
            ('Extra Large', ComponentSize.EXTRA_LARGE)
        ]
        
        for i, (text, size) in enumerate(sizes):
            ModernButton(
                sizes_frame,
                text=text,
                variant='primary',
                size=size,
                theme_mode=self.current_theme,
                command=lambda s=text: self._show_message(f"{s} button clicked!")
            ).grid(row=1, column=i, padx=5, pady=5, sticky=tk.W)
        
        # Button states
        states_frame = tk.Frame(section, bg=section['bg'])
        states_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ModernLabel(
            states_frame,
            text="Button States:",
            variant='heading3',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Normal button
        ModernButton(
            states_frame,
            text="Normal",
            variant='primary',
            theme_mode=self.current_theme,
            command=lambda: self._show_message("Normal button clicked!")
        ).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        # Loading button
        loading_btn = ModernButton(
            states_frame,
            text="Loading",
            variant='primary',
            theme_mode=self.current_theme,
            loading=True
        )
        loading_btn.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Disabled button
        ModernButton(
            states_frame,
            text="Disabled",
            variant='primary',
            theme_mode=self.current_theme,
            disabled=True
        ).grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
    
    def _create_input_showcase(self, parent):
        """Create input fields showcase"""
        
        section = self._create_section(parent, "Input Fields & States")
        
        inputs_frame = tk.Frame(section, bg=section['bg'])
        inputs_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Regular input
        ModernLabel(
            inputs_frame,
            text="Regular Input:",
            variant='body',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        regular_entry = ModernEntry(
            inputs_frame,
            placeholder="Enter your text here...",
            theme_mode=self.current_theme
        )
        regular_entry.grid(row=0, column=1, pady=5, sticky=tk.W)
        
        # Success state
        ModernLabel(
            inputs_frame,
            text="Success State:",
            variant='body',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        success_entry = ModernEntry(inputs_frame, theme_mode=self.current_theme)
        success_entry.insert(0, "Valid input")
        success_entry.set_validation_state(ComponentState.SUCCESS)
        success_entry.grid(row=1, column=1, pady=5, sticky=tk.W)
        
        # Error state
        ModernLabel(
            inputs_frame,
            text="Error State:",
            variant='body',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        error_entry = ModernEntry(inputs_frame, theme_mode=self.current_theme)
        error_entry.insert(0, "Invalid input")
        error_entry.set_validation_state(ComponentState.ERROR)
        error_entry.grid(row=2, column=1, pady=5, sticky=tk.W)
        
        # Disabled state
        ModernLabel(
            inputs_frame,
            text="Disabled State:",
            variant='body',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        disabled_entry = ModernEntry(inputs_frame, theme_mode=self.current_theme)
        disabled_entry.insert(0, "Disabled input")
        disabled_entry.configure(state='disabled')
        disabled_entry.grid(row=3, column=1, pady=5, sticky=tk.W)
    
    def _create_progress_showcase(self, parent):
        """Create progress indicators showcase"""
        
        section = self._create_section(parent, "Progress Indicators")
        
        progress_frame = tk.Frame(section, bg=section['bg'])
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        variants = [
            ('Primary Progress (75%)', 'primary', 75),
            ('Success Progress (100%)', 'success', 100),
            ('Warning Progress (45%)', 'warning', 45),
            ('Error Progress (30%)', 'error', 30)
        ]
        
        for i, (label, variant, value) in enumerate(variants):
            ModernLabel(
                progress_frame,
                text=label,
                variant='body',
                weight='bold',
                theme_mode=self.current_theme
            ).grid(row=i, column=0, sticky=tk.W, pady=5, padx=(0, 20))
            
            progress = ModernProgressBar(
                progress_frame,
                variant=variant,
                theme_mode=self.current_theme,
                width=300,
                show_percentage=True
            )
            progress.grid(row=i, column=1, pady=5, sticky=tk.W)
            progress.set_progress(value)
    
    def _create_container_showcase(self, parent):
        """Create container/panel showcase"""
        
        section = self._create_section(parent, "Containers & Panels")
        
        containers_frame = tk.Frame(section, bg=section['bg'])
        containers_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Panel variants
        variants = [
            ('Primary Surface', 'primary'),
            ('Secondary Surface', 'secondary'),
            ('Tertiary Surface', 'tertiary'),
            ('Elevated Surface', 'elevated')
        ]
        
        for i, (label, variant) in enumerate(variants):
            panel = ModernFrame(
                containers_frame,
                variant=variant,
                theme_mode=self.current_theme,
                width=200,
                height=80,
                relief=tk.RAISED if variant == 'elevated' else tk.FLAT,
                bd=1 if variant == 'elevated' else 0
            )
            panel.grid(row=i//2, column=i%2, padx=10, pady=10, sticky=tk.W)
            panel.pack_propagate(False)
            
            ModernLabel(
                panel,
                text=label,
                variant='body',
                weight='bold',
                theme_mode=self.current_theme
            ).pack(expand=True)
    
    def _create_typography_tab(self):
        """Create typography showcase tab"""
        
        scrollable = ModernScrollableFrame(self.root, theme_mode=self.current_theme)
        self.notebook.add(scrollable, text="Typography")
        
        content = scrollable.get_inner_frame()
        
        # Typography scale section
        section = self._create_section(content, "Typography Scale & Hierarchy")
        
        typo_frame = tk.Frame(section, bg=section['bg'])
        typo_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Typography examples
        examples = [
            ('Hero Text (35px)', 'hero', 'The quick brown fox jumps over the lazy dog'),
            ('Heading 1 (28px)', 'heading1', 'The quick brown fox jumps over the lazy dog'),
            ('Heading 2 (23px)', 'heading2', 'The quick brown fox jumps over the lazy dog'),
            ('Heading 3 (19px)', 'heading3', 'The quick brown fox jumps over the lazy dog'),
            ('Body Large (17px)', 'body-large', 'The quick brown fox jumps over the lazy dog'),
            ('Body Text (15px)', 'body', 'The quick brown fox jumps over the lazy dog'),
            ('Caption (13px)', 'caption', 'The quick brown fox jumps over the lazy dog'),
            ('Small Text (11px)', 'small', 'The quick brown fox jumps over the lazy dog'),
        ]
        
        for i, (label, variant, text) in enumerate(examples):
            # Label for size
            ModernLabel(
                typo_frame,
                text=label,
                variant='caption',
                color='secondary',
                theme_mode=self.current_theme
            ).grid(row=i*2, column=0, sticky=tk.W, pady=(10, 2))
            
            # Example text
            ModernLabel(
                typo_frame,
                text=text,
                variant=variant,
                theme_mode=self.current_theme
            ).grid(row=i*2+1, column=0, sticky=tk.W, pady=(0, 5))
        
        # Font weights section
        weights_section = self._create_section(content, "Font Weights")
        
        weights_frame = tk.Frame(weights_section, bg=weights_section['bg'])
        weights_frame.pack(fill=tk.X, padx=20, pady=10)
        
        weights = [
            ('Normal Weight', 'normal'),
            ('Bold Weight', 'bold')
        ]
        
        for i, (label, weight) in enumerate(weights):
            ModernLabel(
                weights_frame,
                text=f"{label}: The quick brown fox jumps over the lazy dog",
                variant='body-large',
                weight=weight,
                theme_mode=self.current_theme
            ).grid(row=i, column=0, sticky=tk.W, pady=5)
    
    def _create_colors_tab(self):
        """Create colors showcase tab"""
        
        scrollable = ModernScrollableFrame(self.root, theme_mode=self.current_theme)
        self.notebook.add(scrollable, text="Colors")
        
        content = scrollable.get_inner_frame()
        
        # Brand colors section
        self._create_color_section(content, "Brand Colors", [
            ('Primary', self.component_lib.get_color(self.component_lib.tokens.BRAND_PRIMARY)),
            ('Secondary', self.component_lib.get_color(self.component_lib.tokens.BRAND_SECONDARY))
        ])
        
        # Surface colors section
        self._create_color_section(content, "Surface Colors", [
            ('Primary Surface', self.component_lib.get_color(self.component_lib.tokens.SURFACE_PRIMARY)),
            ('Secondary Surface', self.component_lib.get_color(self.component_lib.tokens.SURFACE_SECONDARY)),
            ('Tertiary Surface', self.component_lib.get_color(self.component_lib.tokens.SURFACE_TERTIARY)),
            ('Elevated Surface', self.component_lib.get_color(self.component_lib.tokens.SURFACE_ELEVATED))
        ])
        
        # Text colors section
        self._create_color_section(content, "Text Colors", [
            ('Primary Text', self.component_lib.get_color(self.component_lib.tokens.TEXT_PRIMARY)),
            ('Secondary Text', self.component_lib.get_color(self.component_lib.tokens.TEXT_SECONDARY)),
            ('Tertiary Text', self.component_lib.get_color(self.component_lib.tokens.TEXT_TERTIARY)),
            ('Disabled Text', self.component_lib.get_color(self.component_lib.tokens.TEXT_DISABLED))
        ])
        
        # State colors section
        self._create_color_section(content, "State Colors", [
            ('Success', self.component_lib.get_color(self.component_lib.tokens.STATE_SUCCESS)),
            ('Warning', self.component_lib.get_color(self.component_lib.tokens.STATE_WARNING)),
            ('Error', self.component_lib.get_color(self.component_lib.tokens.STATE_ERROR)),
            ('Info', self.component_lib.get_color(self.component_lib.tokens.STATE_INFO))
        ])
    
    def _create_color_section(self, parent, title, colors):
        """Create a color showcase section"""
        
        section = self._create_section(parent, title)
        
        colors_frame = tk.Frame(section, bg=section['bg'])
        colors_frame.pack(fill=tk.X, padx=20, pady=10)
        
        for i, (name, color) in enumerate(colors):
            # Color swatch
            swatch = tk.Frame(
                colors_frame,
                bg=color,
                width=60,
                height=40,
                relief=tk.RAISED,
                bd=1
            )
            swatch.grid(row=i//4, column=(i%4)*2, padx=5, pady=5)
            swatch.pack_propagate(False)
            
            # Color info
            info_frame = tk.Frame(colors_frame, bg=section['bg'])
            info_frame.grid(row=i//4, column=(i%4)*2+1, padx=5, pady=5, sticky=tk.W)
            
            ModernLabel(
                info_frame,
                text=name,
                variant='body',
                weight='bold',
                theme_mode=self.current_theme
            ).pack(anchor=tk.W)
            
            ModernLabel(
                info_frame,
                text=color.upper(),
                variant='caption',
                color='secondary',
                theme_mode=self.current_theme
            ).pack(anchor=tk.W)
    
    def _create_accessibility_tab(self):
        """Create accessibility testing tab"""
        
        scrollable = ModernScrollableFrame(self.root, theme_mode=self.current_theme)
        self.notebook.add(scrollable, text="Accessibility")
        
        content = scrollable.get_inner_frame()
        
        # Contrast testing section
        section = self._create_section(content, "Color Contrast Testing")
        
        contrast_frame = tk.Frame(section, bg=section['bg'])
        contrast_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Contrast test inputs
        ModernLabel(
            contrast_frame,
            text="Test Color Combinations:",
            variant='heading3',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        
        ModernLabel(
            contrast_frame,
            text="Foreground Color:",
            variant='body',
            theme_mode=self.current_theme
        ).grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.fg_color_var = tk.StringVar(value="#F3F4F6")
        fg_entry = ModernEntry(
            contrast_frame,
            textvariable=self.fg_color_var,
            theme_mode=self.current_theme
        )
        fg_entry.grid(row=1, column=1, pady=5, padx=(0, 10))
        
        ModernLabel(
            contrast_frame,
            text="Background Color:",
            variant='body',
            theme_mode=self.current_theme
        ).grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.bg_color_var = tk.StringVar(value="#1E1E1E")
        bg_entry = ModernEntry(
            contrast_frame,
            textvariable=self.bg_color_var,
            theme_mode=self.current_theme
        )
        bg_entry.grid(row=2, column=1, pady=5, padx=(0, 10))
        
        # Test button
        ModernButton(
            contrast_frame,
            text="Test Contrast",
            variant='primary',
            theme_mode=self.current_theme,
            command=self._test_contrast
        ).grid(row=1, column=2, rowspan=2, padx=20, pady=5)
        
        # Results area
        self.contrast_results_frame = ModernFrame(
            section,
            variant='tertiary',
            theme_mode=self.current_theme
        )
        self.contrast_results_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Accessibility checklist section
        checklist_section = self._create_section(content, "Accessibility Features")
        
        checklist_frame = tk.Frame(checklist_section, bg=checklist_section['bg'])
        checklist_frame.pack(fill=tk.X, padx=20, pady=10)
        
        features = [
            "✅ WCAG 2.1 AA color contrast compliance (4.5:1 ratio)",
            "✅ Keyboard navigation support for all interactive elements",
            "✅ Focus indicators with visible focus rings",
            "✅ Semantic color coding for states (success, warning, error)",
            "✅ Scalable typography supporting accessibility preferences",
            "✅ High contrast mode compatibility",
            "✅ Screen reader friendly component structure",
            "✅ Alternative text and ARIA labels where appropriate"
        ]
        
        for i, feature in enumerate(features):
            ModernLabel(
                checklist_frame,
                text=feature,
                variant='body',
                theme_mode=self.current_theme
            ).grid(row=i, column=0, sticky=tk.W, pady=3)
    
    def _create_playground_tab(self):
        """Create interactive component playground tab"""
        
        scrollable = ModernScrollableFrame(self.root, theme_mode=self.current_theme)
        self.notebook.add(scrollable, text="Playground")
        
        content = scrollable.get_inner_frame()
        
        # Interactive demo section
        section = self._create_section(content, "Interactive Component Builder")
        
        playground_frame = tk.Frame(section, bg=section['bg'])
        playground_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Component type selector
        ModernLabel(
            playground_frame,
            text="Component Type:",
            variant='body',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.component_type_var = tk.StringVar(value="Button")
        component_combo = ttk.Combobox(
            playground_frame,
            textvariable=self.component_type_var,
            values=["Button", "Entry", "Label", "Progress Bar"],
            state="readonly"
        )
        component_combo.grid(row=0, column=1, pady=5, padx=(0, 20), sticky=tk.W)
        
        # Variant selector
        ModernLabel(
            playground_frame,
            text="Variant:",
            variant='body',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.variant_var = tk.StringVar(value="primary")
        variant_combo = ttk.Combobox(
            playground_frame,
            textvariable=self.variant_var,
            values=["primary", "secondary", "outline", "ghost", "danger"],
            state="readonly"
        )
        variant_combo.grid(row=0, column=3, pady=5, padx=(0, 20), sticky=tk.W)
        
        # Size selector
        ModernLabel(
            playground_frame,
            text="Size:",
            variant='body',
            weight='bold',
            theme_mode=self.current_theme
        ).grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.size_var = tk.StringVar(value="medium")
        size_combo = ttk.Combobox(
            playground_frame,
            textvariable=self.size_var,
            values=["small", "medium", "large", "extra_large"],
            state="readonly"
        )
        size_combo.grid(row=1, column=1, pady=5, padx=(0, 20), sticky=tk.W)
        
        # Generate button
        ModernButton(
            playground_frame,
            text="Generate Component",
            variant='primary',
            theme_mode=self.current_theme,
            command=self._generate_component
        ).grid(row=1, column=2, columnspan=2, pady=5, padx=20)
        
        # Preview area
        self.preview_section = self._create_section(content, "Component Preview")
        
        self.preview_frame = ModernFrame(
            self.preview_section,
            variant='elevated',
            theme_mode=self.current_theme,
            height=100
        )
        self.preview_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Code example section
        code_section = self._create_section(content, "Generated Code")
        
        self.code_text = tk.Text(
            code_section,
            height=8,
            bg=self.component_lib.get_color(self.component_lib.tokens.SURFACE_TERTIARY),
            fg=self.component_lib.get_color(self.component_lib.tokens.TEXT_PRIMARY),
            font=('Consolas', 11),
            wrap=tk.WORD
        )
        self.code_text.pack(fill=tk.X, padx=20, pady=10)
    
    def _create_section(self, parent, title):
        """Create a section with title"""
        
        section = ModernFrame(
            parent,
            variant='secondary',
            theme_mode=self.current_theme
        )
        section.pack(fill=tk.X, pady=(0, 20))
        
        ModernLabel(
            section,
            text=title,
            variant='heading2',
            weight='bold',
            theme_mode=self.current_theme
        ).pack(pady=(15, 10), padx=20, anchor=tk.W)
        
        return section
    
    def _create_footer(self, parent):
        """Create application footer"""
        
        footer_frame = ModernFrame(
            parent,
            variant='tertiary',
            theme_mode=self.current_theme
        )
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Info section
        info_frame = tk.Frame(footer_frame, bg=footer_frame['bg'])
        info_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ModernLabel(
            info_frame,
            text="Automaton Design System Demo",
            variant='caption',
            color='secondary',
            theme_mode=self.current_theme
        ).pack(side=tk.LEFT, padx=20, pady=10)
        
        # Action buttons
        actions_frame = tk.Frame(footer_frame, bg=footer_frame['bg'])
        actions_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ModernButton(
            actions_frame,
            text="Open Component Showcase",
            variant='outline',
            theme_mode=self.current_theme,
            command=self._open_component_showcase
        ).pack(side=tk.RIGHT, padx=10, pady=10)
        
        ModernButton(
            actions_frame,
            text="Export Theme Config",
            variant='secondary',
            theme_mode=self.current_theme,
            command=self._export_theme_config
        ).pack(side=tk.RIGHT, padx=10, pady=10)
    
    # Event handlers
    
    def _toggle_theme(self):
        """Toggle between light and dark themes"""
        
        # Switch theme
        self.current_theme = ThemeMode.LIGHT if self.current_theme == ThemeMode.DARK else ThemeMode.DARK
        
        # Update all components
        self.component_lib = ComponentLibrary(self.current_theme)
        self.factory = ComponentFactory(self.root, self.current_theme)
        
        # Apply new theme
        self._apply_theme()
        
        # Recreate interface with new theme
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self._create_interface()
        
        self._show_message(f"Switched to {self.current_theme.value} theme")
    
    def _test_contrast(self):
        """Test color contrast ratio"""
        
        fg_color = self.fg_color_var.get()
        bg_color = self.bg_color_var.get()
        
        try:
            # Validate colors
            self.root.winfo_rgb(fg_color)
            self.root.winfo_rgb(bg_color)
            
            # Test contrast
            results = self.accessibility_validator.validate_color_contrast(
                self.component_lib, fg_color, bg_color
            )
            
            # Clear previous results
            for widget in self.contrast_results_frame.winfo_children():
                widget.destroy()
            
            # Display results
            ModernLabel(
                self.contrast_results_frame,
                text=f"Contrast Ratio: {results['contrast_ratio']}:1",
                variant='heading3',
                weight='bold',
                theme_mode=self.current_theme
            ).pack(pady=10, padx=20, anchor=tk.W)
            
            # Compliance results
            compliance_frame = tk.Frame(
                self.contrast_results_frame,
                bg=self.contrast_results_frame['bg']
            )
            compliance_frame.pack(fill=tk.X, padx=20, pady=5)
            
            statuses = [
                ('WCAG AA Compliant', results['wcag_aa_compliant']),
                ('WCAG AAA Compliant', results['wcag_aaa_compliant']),
                ('Large Text AA Compliant', results['wcag_aa_large_compliant'])
            ]
            
            for i, (label, status) in enumerate(statuses):
                status_text = "✅ PASS" if status else "❌ FAIL"
                ModernLabel(
                    compliance_frame,
                    text=f"{label}: {status_text}",
                    variant='body',
                    theme_mode=self.current_theme
                ).grid(row=i, column=0, sticky=tk.W, pady=2)
            
            # Preview
            preview_frame = tk.Frame(
                self.contrast_results_frame,
                bg=bg_color,
                relief=tk.RAISED,
                bd=1,
                height=60
            )
            preview_frame.pack(fill=tk.X, padx=20, pady=10)
            preview_frame.pack_propagate(False)
            
            tk.Label(
                preview_frame,
                text="Sample text with these colors",
                bg=bg_color,
                fg=fg_color,
                font=('Inter', 14)
            ).pack(expand=True)
            
        except tk.TclError:
            self._show_message("Invalid color format. Use hex colors like #FF0000")
    
    def _generate_component(self):
        """Generate component based on playground settings"""
        
        # Clear preview
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        component_type = self.component_type_var.get()
        variant = self.variant_var.get()
        size_name = self.size_var.get()
        
        # Map size name to ComponentSize enum
        size_map = {
            'small': ComponentSize.SMALL,
            'medium': ComponentSize.MEDIUM,
            'large': ComponentSize.LARGE,
            'extra_large': ComponentSize.EXTRA_LARGE
        }
        size = size_map.get(size_name, ComponentSize.MEDIUM)
        
        # Generate component
        if component_type == "Button":
            component = ModernButton(
                self.preview_frame,
                text=f"{variant.title()} Button",
                variant=variant,
                size=size,
                theme_mode=self.current_theme,
                command=lambda: self._show_message(f"{variant} button clicked!")
            )
            code = f"""ModernButton(
    parent,
    text="{variant.title()} Button",
    variant='{variant}',
    size=ComponentSize.{size_name.upper()},
    theme_mode=ThemeMode.{self.current_theme.name},
    command=your_command_function
)"""
        
        elif component_type == "Entry":
            component = ModernEntry(
                self.preview_frame,
                placeholder=f"Sample {variant} input...",
                size=size,
                theme_mode=self.current_theme
            )
            code = f"""ModernEntry(
    parent,
    placeholder="Sample {variant} input...",
    size=ComponentSize.{size_name.upper()},
    theme_mode=ThemeMode.{self.current_theme.name}
)"""
        
        elif component_type == "Label":
            component = ModernLabel(
                self.preview_frame,
                text=f"Sample {variant} label text",
                variant='body' if variant == 'primary' else 'caption',
                weight='bold' if variant == 'primary' else 'normal',
                theme_mode=self.current_theme
            )
            code = f"""ModernLabel(
    parent,
    text="Sample {variant} label text",
    variant='{'body' if variant == 'primary' else 'caption'}',
    weight='{'bold' if variant == 'primary' else 'normal'}',
    theme_mode=ThemeMode.{self.current_theme.name}
)"""
        
        elif component_type == "Progress Bar":
            component = ModernProgressBar(
                self.preview_frame,
                variant=variant if variant in ['primary', 'success', 'warning', 'error'] else 'primary',
                theme_mode=self.current_theme,
                width=200
            )
            component.set_progress(75)
            code = f"""progress = ModernProgressBar(
    parent,
    variant='{variant if variant in ['primary', 'success', 'warning', 'error'] else 'primary'}',
    theme_mode=ThemeMode.{self.current_theme.name},
    width=200
)
progress.set_progress(75)"""
        
        # Position component
        component.pack(expand=True)
        
        # Update code display
        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(1.0, code)
    
    def _open_component_showcase(self):
        """Open the component showcase window"""
        ComponentShowcase(self.root, self.current_theme)
    
    def _export_theme_config(self):
        """Export current theme configuration"""
        config = {
            'theme_mode': self.current_theme.value,
            'brand_colors': {
                'primary': self.component_lib.get_color(self.component_lib.tokens.BRAND_PRIMARY),
                'secondary': self.component_lib.get_color(self.component_lib.tokens.BRAND_SECONDARY)
            },
            'surface_colors': {
                'primary': self.component_lib.get_color(self.component_lib.tokens.SURFACE_PRIMARY),
                'secondary': self.component_lib.get_color(self.component_lib.tokens.SURFACE_SECONDARY),
                'tertiary': self.component_lib.get_color(self.component_lib.tokens.SURFACE_TERTIARY)
            },
            'typography': self.component_lib.tokens.TYPOGRAPHY_SCALE,
            'spacing': self.component_lib.tokens.SPACING
        }
        
        import json
        config_json = json.dumps(config, indent=2)
        
        # Show in a dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Theme Configuration Export")
        dialog.geometry("600x400")
        
        text_widget = tk.Text(dialog, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, config_json)
        
        ModernButton(
            dialog,
            text="Close",
            variant='primary',
            theme_mode=self.current_theme,
            command=dialog.destroy
        ).pack(pady=10)
    
    def _show_message(self, message: str):
        """Show a message dialog"""
        messagebox.showinfo("Demo", message)
    
    def run(self):
        """Run the demo application"""
        self.root.mainloop()

if __name__ == "__main__":
    demo = DesignSystemDemo()
    demo.run()