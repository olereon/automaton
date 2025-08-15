# GUI Interface for Web Automation App
# Modern GUI using tkinter with custom styling

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
import asyncio
import json
import threading
from pathlib import Path
from datetime import datetime
import queue
import os

from core.engine import (
    WebAutomationEngine,
    AutomationSequenceBuilder,
    AutomationConfig,
    ActionType,
    Action
)

class ModernButton(tk.Button):
    """Custom styled button that respects theme settings"""
    
    # Class variable to store GUI reference
    _gui_instance = None
    
    @classmethod
    def set_gui_instance(cls, gui_instance):
        """Set the GUI instance for all ModernButton instances"""
        cls._gui_instance = gui_instance
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.default_config = {
            'relief': tk.FLAT,
            'padx': 20,
            'pady': 10,
            'cursor': 'hand2'
        }
        self.configure(**self.default_config)
        
        # Store reference to find GUI later if not set
        self.parent_widget = parent
        
        # Apply initial theme
        self._apply_theme()
        
        # Bind hover events
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
    def _get_gui_instance(self):
        """Get the GUI instance through class variable or widget traversal"""
        if ModernButton._gui_instance:
            return ModernButton._gui_instance
            
        # Fallback: traverse widget hierarchy
        widget = self.parent_widget
        while widget and not hasattr(widget, 'settings'):
            widget = getattr(widget, 'master', None)
        return widget if widget and hasattr(widget, 'settings') else None
        
    def _apply_theme(self):
        """Apply current theme to button"""
        gui = self._get_gui_instance()
        if not gui:
            # Fallback to default colors
            self.configure(bg='#007acc', fg='white', font=('Arial', 12))
            self.normal_color = '#007acc'
            self.hover_color = '#005a9e'
            return
            
        settings = gui.settings
        font_size = max(10, settings.get('font_size', 20) - 6)  # Button font smaller than main
        
        if settings.get('dark_mode', False):
            bg_color = settings.get('custom_primary') or settings.get('dark_accent', '#007acc')
            fg_color = settings.get('custom_font') or settings.get('dark_text_bright', '#ffffff')
            self.hover_color = settings.get('dark_surface', '#2d2d30')
        else:
            bg_color = settings.get('custom_primary') or settings.get('light_accent', '#0078d4')
            fg_color = settings.get('custom_font') or settings.get('light_text_bright', '#000000')
            self.hover_color = '#005a9e'
            
        # Check if this is a stop button (contains "Stop" text)
        if "Stop" in str(self.cget('text')):
            if settings.get('dark_mode', False):
                bg_color = settings.get('dark_error', '#f44747')
                self.hover_color = '#e53e3e'
            else:
                bg_color = settings.get('light_error', '#d13438')
                self.hover_color = '#b02a2a'
        
        self.normal_color = bg_color
        self.configure(bg=bg_color, fg=fg_color, font=('Arial', font_size, 'bold'))
        
    def _on_enter(self, event):
        """Handle mouse enter"""
        if hasattr(self, 'hover_color'):
            self.configure(bg=self.hover_color)
            
    def _on_leave(self, event):
        """Handle mouse leave"""
        if hasattr(self, 'normal_color'):
            self.configure(bg=self.normal_color)
            
    def update_theme(self):
        """Public method to update theme"""
        self._apply_theme()

class AutomationGUI:
    """Modern GUI for Web Automation"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Web Automation Tool")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)  # Set minimum size to prevent shrinking too small
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Variables
        self.current_config = None
        self.automation_thread = None
        self.log_queue = queue.Queue()
        self.current_engine = None  # Keep reference to the automation engine
        self.stop_requested = False  # Flag for stopping automation
        self.is_running = False  # Track automation state
        
        # Settings
        self.settings_file = Path.home() / ".automaton_settings.json"
        self.settings = self._load_settings()
        
        # Set GUI instance for ModernButton class
        ModernButton.set_gui_instance(self)
        
        # Setup UI
        self._setup_ui()
        self._setup_styles()
        
        # Apply initial settings
        self._apply_settings()
        
        # Start log processor
        self.root.after(100, self._process_log_queue)
        
    def _setup_styles(self):
        """Configure custom styles"""
        # Configure colors
        bg_color = '#f5f5f5'
        self.root.configure(bg=bg_color)
        
        # Get base font size
        base_font_size = self.settings.get('font_size', 20)
        
        # Configure ttk styles with scalable fonts
        self.style.configure('Title.TLabel', font=('Arial', base_font_size + 4, 'bold'))
        self.style.configure('Heading.TLabel', font=('Arial', base_font_size, 'bold'))
        self.style.configure('TLabel', font=('Arial', max(10, base_font_size - 4)))
        self.style.configure('TButton', font=('Arial', max(10, base_font_size - 6)))
        self.style.configure('TEntry', font=('Arial', max(10, base_font_size - 4)))
        self.style.configure('TCombobox', font=('Arial', max(10, base_font_size - 4)))
        self.style.configure('TCheckbutton', font=('Arial', max(10, base_font_size - 4)))
        self.style.configure('Action.TFrame', relief=tk.RIDGE, borderwidth=1)
        
    def _setup_ui(self):
        """Setup the main UI layout"""
        # Create main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_container, text="Web Automation Tool", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Main automation tab
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Automation")
        
        # Settings tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        
        # Setup main automation interface
        self._setup_main_tab()
        
        # Setup settings interface
        self._setup_settings_tab()
        
    def _setup_main_tab(self):
        """Setup the main automation tab"""
        # Configure grid weights for main frame
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        # Left panel - Configuration
        self._create_config_panel(self.main_frame)
        
        # Middle panel - Actions
        self._create_actions_panel(self.main_frame)
        
        # Right panel - Controls
        self._create_controls_panel(self.main_frame)
        
        # Bottom panel - Log output
        self._create_log_panel(self.main_frame)
        
    def _setup_settings_tab(self):
        """Setup the settings tab"""
        # Configure grid weights
        self.settings_frame.columnconfigure(0, weight=1)
        self.settings_frame.rowconfigure(0, weight=1)
        
        # Create main settings container
        settings_container = ttk.Frame(self.settings_frame, padding="20")
        settings_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Settings title
        title_label = ttk.Label(settings_container, text="Application Settings", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Appearance section
        appearance_frame = ttk.LabelFrame(settings_container, text="Appearance", padding="15")
        appearance_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Dark mode toggle
        ttk.Label(appearance_frame, text="Dark Mode:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=5)
        
        self.dark_mode_var = tk.BooleanVar(value=self.settings.get('dark_mode', False))
        dark_mode_toggle = ttk.Checkbutton(appearance_frame, text="Enable dark theme", 
                                          variable=self.dark_mode_var,
                                          command=self._on_dark_mode_changed)
        dark_mode_toggle.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Font size setting
        ttk.Label(appearance_frame, text="Font Size:", style='Heading.TLabel').grid(
            row=1, column=0, sticky=tk.W, pady=(15, 5))
        
        font_frame = ttk.Frame(appearance_frame)
        font_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(15, 5), padx=(10, 0))
        
        # Font size slider (16-48px with 4px intervals)
        self.font_size_var = tk.IntVar(value=self.settings.get('font_size', 20))
        # Use tk.Scale instead of ttk.Scale for resolution support
        self.font_slider = tk.Scale(font_frame, from_=16, to=48, 
                              variable=self.font_size_var,
                              orient=tk.HORIZONTAL, length=300,
                              resolution=4,  # 4px intervals
                              command=self._on_font_size_changed,
                              bg='#f0f0f0', highlightthickness=0)
        self.font_slider.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Font size label
        self.font_size_label = ttk.Label(font_frame, text=f"{self.font_size_var.get()}px")
        self.font_size_label.grid(row=0, column=1, padx=(10, 0))
        
        # Font size preview
        self.font_preview_label = ttk.Label(font_frame, text="Sample Text", 
                                           font=('Arial', self.font_size_var.get()))
        self.font_preview_label.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        # Window Resolution section
        resolution_frame = ttk.LabelFrame(settings_container, text="Window Resolution", padding="15")
        resolution_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Resolution dropdown
        ttk.Label(resolution_frame, text="Default Window Size:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=5)
        
        resolution_option_frame = ttk.Frame(resolution_frame)
        resolution_option_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Resolution options for different monitor types
        self.resolution_options = [
            ("1200x800", "1200x800 (HD Ready)"),
            ("1440x900", "1440x900 (HD+)"),
            ("1600x1000", "1600x1000 (UXGA)"),
            ("1920x1200", "1920x1200 (Full HD)"),
            ("2560x1600", "2560x1600 (2K)"),
            ("3200x2000", "3200x2000 (3K)"),
            ("3840x2400", "3840x2400 (4K)")
        ]
        
        current_resolution = self.settings.get('window_resolution', '1200x800')
        self.resolution_var = tk.StringVar(value=current_resolution)
        
        self.resolution_combo = ttk.Combobox(resolution_option_frame, textvariable=self.resolution_var,
                                           values=[desc for _, desc in self.resolution_options],
                                           state='readonly', width=25)
        self.resolution_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.resolution_combo.bind('<<ComboboxSelected>>', self._on_resolution_changed)
        
        # Set current selection
        for i, (res, desc) in enumerate(self.resolution_options):
            if res == current_resolution:
                self.resolution_combo.current(i)
                break
        
        # Apply resolution button
        ModernButton(resolution_option_frame, text="Apply Resolution", 
                    command=self._apply_resolution).grid(row=0, column=1, padx=(10, 0))
        
        # Current resolution info
        current_size = f"{self.root.winfo_width()}x{self.root.winfo_height()}"
        self.current_res_label = ttk.Label(resolution_frame, 
                                          text=f"Current: {current_size}")
        self.current_res_label.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        # Color Customization section
        color_frame = ttk.LabelFrame(settings_container, text="Color Customization", padding="15")
        color_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Color picker variables
        self.custom_bg_var = tk.StringVar(value=self.settings.get('custom_background', ''))
        self.custom_primary_var = tk.StringVar(value=self.settings.get('custom_primary', ''))
        self.custom_font_var = tk.StringVar(value=self.settings.get('custom_font', ''))
        
        # Background color picker
        ttk.Label(color_frame, text="Window Background:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=5)
        
        bg_frame = ttk.Frame(color_frame)
        bg_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        self.bg_color_preview = tk.Label(bg_frame, width=4, height=2, relief=tk.RAISED,
                                        bg=self.custom_bg_var.get() or '#1e1e1e')
        self.bg_color_preview.grid(row=0, column=0, padx=(0, 10))
        
        ModernButton(bg_frame, text="Choose Color", 
                    command=lambda: self._choose_color('background')).grid(row=0, column=1)
        ModernButton(bg_frame, text="Reset", 
                    command=lambda: self._reset_color('background')).grid(row=0, column=2, padx=(5, 0))
        
        # Primary/Accent color picker
        ttk.Label(color_frame, text="Primary Color:", style='Heading.TLabel').grid(
            row=1, column=0, sticky=tk.W, pady=(15, 5))
        
        primary_frame = ttk.Frame(color_frame)
        primary_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(15, 5), padx=(10, 0))
        
        self.primary_color_preview = tk.Label(primary_frame, width=4, height=2, relief=tk.RAISED,
                                             bg=self.custom_primary_var.get() or '#007acc')
        self.primary_color_preview.grid(row=0, column=0, padx=(0, 10))
        
        ModernButton(primary_frame, text="Choose Color", 
                    command=lambda: self._choose_color('primary')).grid(row=0, column=1)
        ModernButton(primary_frame, text="Reset", 
                    command=lambda: self._reset_color('primary')).grid(row=0, column=2, padx=(5, 0))
        
        # Font color picker
        ttk.Label(color_frame, text="Font Color:", style='Heading.TLabel').grid(
            row=2, column=0, sticky=tk.W, pady=(15, 5))
        
        font_color_frame = ttk.Frame(color_frame)
        font_color_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(15, 5), padx=(10, 0))
        
        self.font_color_preview = tk.Label(font_color_frame, width=4, height=2, relief=tk.RAISED,
                                          bg=self.custom_font_var.get() or '#cccccc')
        self.font_color_preview.grid(row=0, column=0, padx=(0, 10))
        
        ModernButton(font_color_frame, text="Choose Color", 
                    command=lambda: self._choose_color('font')).grid(row=0, column=1)
        ModernButton(font_color_frame, text="Reset", 
                    command=lambda: self._reset_color('font')).grid(row=0, column=2, padx=(5, 0))
        
        # Preview section
        preview_frame = ttk.LabelFrame(settings_container, text="Theme Preview", padding="15")
        preview_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        self.theme_preview_frame = tk.Frame(preview_frame, relief=tk.RAISED, bd=2, height=100)
        self.theme_preview_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.theme_preview_frame.grid_propagate(False)
        
        self.preview_title = tk.Label(self.theme_preview_frame, text="Sample Window", 
                                     font=('Arial', 14, 'bold'))
        self.preview_title.pack(pady=10)
        
        self.preview_text = tk.Label(self.theme_preview_frame, 
                                    text="This is how your text will look with the current settings")
        self.preview_text.pack(pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(settings_container)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=(30, 0))
        
        # Reset to defaults button
        ModernButton(buttons_frame, text="Reset to Defaults", 
                    command=self._reset_settings).pack(side=tk.LEFT, padx=5)
        
        # Save settings button  
        ModernButton(buttons_frame, text="Save Settings", 
                    command=self._save_settings).pack(side=tk.LEFT, padx=5)
        
    def _create_config_panel(self, parent):
        """Create configuration panel"""
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Configure grid weights for proper expansion
        config_frame.columnconfigure(1, weight=1)
        
        # Name label and entry
        ttk.Label(config_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=(5, 2))
        self.name_var = tk.StringVar()
        name_entry = tk.Text(config_frame, width=25, height=3, wrap=tk.WORD, font=('Arial', 10))
        name_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Bind the Text widget to the StringVar for compatibility
        def update_name_var(*args):
            content = name_entry.get("1.0", tk.END).strip()
            self.name_var.set(content)
        
        def update_name_text(*args):
            current_pos = name_entry.index(tk.INSERT)
            name_entry.delete("1.0", tk.END)
            name_entry.insert("1.0", self.name_var.get())
            try:
                name_entry.mark_set(tk.INSERT, current_pos)
            except:
                pass
        
        name_entry.bind('<KeyRelease>', update_name_var)
        name_entry.bind('<FocusOut>', update_name_var)
        self.name_var.trace('w', update_name_text)
        self.name_entry = name_entry  # Store reference for theme updates
        
        # URL label and entry
        ttk.Label(config_frame, text="URL:").grid(row=2, column=0, sticky=tk.W, pady=(5, 2))
        self.url_var = tk.StringVar()
        url_entry = tk.Text(config_frame, width=25, height=3, wrap=tk.WORD, font=('Arial', 10))
        url_entry.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Bind the Text widget to the StringVar for compatibility
        def update_url_var(*args):
            content = url_entry.get("1.0", tk.END).strip()
            self.url_var.set(content)
        
        def update_url_text(*args):
            current_pos = url_entry.index(tk.INSERT)
            url_entry.delete("1.0", tk.END)
            url_entry.insert("1.0", self.url_var.get())
            try:
                url_entry.mark_set(tk.INSERT, current_pos)
            except:
                pass
        
        url_entry.bind('<KeyRelease>', update_url_var)
        url_entry.bind('<FocusOut>', update_url_var)
        self.url_var.trace('w', update_url_text)
        self.url_entry = url_entry  # Store reference for theme updates
        
        # Options
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(config_frame, text="Run headless", 
                                        variable=self.headless_var)
        headless_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=15)
        
        # File operations - moved to bottom
        file_frame = ttk.Frame(config_frame)
        file_frame.grid(row=5, column=0, columnspan=2, pady=(20, 10), sticky=(tk.W, tk.E))
        
        ModernButton(file_frame, text="Load Config", 
                    command=self._load_config).pack(side=tk.LEFT, padx=2)
        ModernButton(file_frame, text="Save Config", 
                    command=self._save_config).pack(side=tk.LEFT, padx=2)
        ModernButton(file_frame, text="New Config", 
                    command=self._new_config).pack(side=tk.LEFT, padx=2)
        
    def _create_actions_panel(self, parent):
        """Create actions panel"""
        actions_frame = ttk.LabelFrame(parent, text="Actions", padding="10")
        actions_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), 
                          padx=5, pady=(0, 5))
        
        # Actions listbox with scrollbar
        list_frame = ttk.Frame(actions_frame)
        list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.actions_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                         height=15, font=('Arial', 10))
        self.actions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.actions_listbox.yview)
        
        # Action buttons
        action_buttons = ttk.Frame(actions_frame)
        action_buttons.grid(row=1, column=0, columnspan=2, pady=10)
        
        ModernButton(action_buttons, text="Add Action", 
                    command=self._show_add_action_dialog).pack(side=tk.LEFT, padx=2)
        ModernButton(action_buttons, text="Edit Action", 
                    command=self._edit_action).pack(side=tk.LEFT, padx=2)
        ModernButton(action_buttons, text="Delete Action", 
                    command=self._delete_action).pack(side=tk.LEFT, padx=2)
        ModernButton(action_buttons, text="Move Up", 
                    command=lambda: self._move_action(-1)).pack(side=tk.LEFT, padx=2)
        ModernButton(action_buttons, text="Move Down", 
                    command=lambda: self._move_action(1)).pack(side=tk.LEFT, padx=2)
        
        # Configure grid weights
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.rowconfigure(0, weight=1)
        
    def _create_controls_panel(self, parent):
        """Create controls panel"""
        controls_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        controls_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Run button
        self.run_button = ModernButton(controls_frame, text="▶ Run Automation",
                                      command=self._run_automation,
                                      font=('Arial', 12, 'bold'))
        self.run_button.pack(fill=tk.X, pady=5)
        
        # Stop button
        self.stop_button = ModernButton(controls_frame, text="■ Stop",
                                       command=self._stop_automation,
                                       state=tk.DISABLED)
        # Stop button will use error color from theme
        self.stop_button.pack(fill=tk.X, pady=5)
        
        # Close Browser button
        self.close_browser_button = ModernButton(controls_frame, text="🌐 Close Browser",
                                                command=self._close_browser,
                                                state=tk.DISABLED)
        self.close_browser_button.pack(fill=tk.X, pady=5)
        
        # Progress
        ttk.Label(controls_frame, text="Progress:").pack(anchor=tk.W, pady=(10, 5))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(controls_frame, variable=self.progress_var,
                                          maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status
        self.status_label = ttk.Label(controls_frame, text="Ready", 
                                    font=('Arial', 10))
        self.status_label.pack(pady=10)
        
        # Statistics
        stats_frame = ttk.LabelFrame(controls_frame, text="Statistics", padding="5")
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=8, width=25, 
                                 font=('Courier', 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.stats_text.config(state=tk.DISABLED)
        
    def _create_log_panel(self, parent):
        """Create log output panel"""
        log_frame = ttk.LabelFrame(parent, text="Log Output", padding="10")
        log_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S),
                      pady=(5, 0))
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                 font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.log_text.tag_config('info', foreground='black')
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')
        
        # Clear log button
        ModernButton(log_frame, text="Clear Log", 
                    command=lambda: self.log_text.delete(1.0, tk.END)).pack(pady=5)
        
    def _show_add_action_dialog(self):
        """Show dialog to add new action"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Action")
        
        # Set minimum and initial size - increased from 600x500 to 900x700
        dialog.minsize(900, 700)
        dialog.geometry("900x700")  # Much larger dialog size
        
        # Apply theme to dialog
        self._apply_dialog_theme(dialog)
        
        # Make dialog resizable
        dialog.resizable(True, True)
        
        # Center dialog on parent window (after setting size)
        self._center_dialog(dialog, force_size=(900, 700))
        
        # Configure grid weights for proper scaling
        dialog.columnconfigure(1, weight=1)
        dialog.rowconfigure(1, weight=1)  # Allow fields frame to expand to push buttons down
        
        # Action type selection - increased height and font size
        ttk.Label(dialog, text="Action Type:", font=('Arial', 14, 'bold')).grid(row=0, column=0, sticky=tk.W, 
                                                   padx=20, pady=20)
        
        action_type_var = tk.StringVar()
        # Configure style for larger combobox
        combo_style = ttk.Style()
        combo_style.configure('Large.TCombobox', 
                            padding=(10, 15, 10, 15),  # Increased padding for height
                            font=('Arial', 22))  # Doubled font size from 11 to 22
        
        action_combo = ttk.Combobox(dialog, textvariable=action_type_var, 
                                   state='readonly', width=60, 
                                   style='Large.TCombobox',
                                   font=('Arial', 22))  # Doubled font size
        action_combo['values'] = [action.value for action in ActionType]
        action_combo.grid(row=0, column=1, padx=20, pady=20, sticky=(tk.W, tk.E))
        action_combo.current(0)
        
        # Dynamic fields frame - adjusted padding and sticky to not expand vertically
        fields_frame = ttk.Frame(dialog)
        fields_frame.grid(row=1, column=0, columnspan=2, padx=25, pady=(10, 15), 
                         sticky=(tk.W, tk.E, tk.N))  # Removed tk.S to prevent vertical expansion
        fields_frame.columnconfigure(1, weight=1)
        
        # Field variables
        field_vars = {}
        
        def update_fields(*args):
            """Update fields based on selected action type"""
            # Clear existing fields
            for widget in fields_frame.winfo_children():
                widget.destroy()
            field_vars.clear()
            
            action_type = ActionType(action_type_var.get())
            row = 0
            
            # Add fields based on action type
            if action_type == ActionType.LOGIN:
                # Username field
                ttk.Label(fields_frame, text="Username:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                              sticky=tk.W, pady=10, padx=(0, 15))
                field_vars['username'] = tk.StringVar()
                username_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                username_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                
                def update_username(*args):
                    username_text.delete("1.0", tk.END)
                    username_text.insert("1.0", field_vars['username'].get())
                field_vars['username'].trace('w', update_username)
                username_text.bind('<KeyRelease>', lambda e: field_vars['username'].set(username_text.get("1.0", tk.END).strip()))
                row += 1
                
                # Password field
                ttk.Label(fields_frame, text="Password:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                              sticky=tk.W, pady=10, padx=(0, 15))
                field_vars['password'] = tk.StringVar()
                password_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                password_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                # Note: Text widget doesn't support show="*" like Entry, so password won't be masked
                
                def update_password(*args):
                    password_text.delete("1.0", tk.END)
                    password_text.insert("1.0", field_vars['password'].get())
                field_vars['password'].trace('w', update_password)
                password_text.bind('<KeyRelease>', lambda e: field_vars['password'].set(password_text.get("1.0", tk.END).strip()))
                row += 1
                
                # Username selector field
                ttk.Label(fields_frame, text="Username Selector:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                                       sticky=tk.W, pady=10, padx=(0, 15))
                field_vars['username_selector'] = tk.StringVar()
                username_sel_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                username_sel_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                
                def update_username_sel(*args):
                    username_sel_text.delete("1.0", tk.END)
                    username_sel_text.insert("1.0", field_vars['username_selector'].get())
                field_vars['username_selector'].trace('w', update_username_sel)
                username_sel_text.bind('<KeyRelease>', lambda e: field_vars['username_selector'].set(username_sel_text.get("1.0", tk.END).strip()))
                row += 1
                
                # Password selector field
                ttk.Label(fields_frame, text="Password Selector:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                                       sticky=tk.W, pady=10, padx=(0, 15))
                field_vars['password_selector'] = tk.StringVar()
                password_sel_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                password_sel_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                
                def update_password_sel(*args):
                    password_sel_text.delete("1.0", tk.END)
                    password_sel_text.insert("1.0", field_vars['password_selector'].get())
                field_vars['password_selector'].trace('w', update_password_sel)
                password_sel_text.bind('<KeyRelease>', lambda e: field_vars['password_selector'].set(password_sel_text.get("1.0", tk.END).strip()))
                row += 1
                
                # Submit button selector field
                ttk.Label(fields_frame, text="Submit Button Selector:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                                            sticky=tk.W, pady=10, padx=(0, 15))
                field_vars['submit_selector'] = tk.StringVar()
                submit_sel_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                submit_sel_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                
                def update_submit_sel(*args):
                    submit_sel_text.delete("1.0", tk.END)
                    submit_sel_text.insert("1.0", field_vars['submit_selector'].get())
                field_vars['submit_selector'].trace('w', update_submit_sel)
                submit_sel_text.bind('<KeyRelease>', lambda e: field_vars['submit_selector'].set(submit_sel_text.get("1.0", tk.END).strip()))
                row += 1
                
            elif action_type not in [ActionType.REFRESH_PAGE]:
                if action_type not in [ActionType.WAIT, ActionType.LOGIN]:
                    ttk.Label(fields_frame, text="Selector:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                                  sticky=tk.W, pady=10, padx=(0, 15))
                    field_vars['selector'] = tk.StringVar()
                    selector_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                    selector_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                    
                    def update_selector(*args):
                        selector_text.delete("1.0", tk.END)
                        selector_text.insert("1.0", field_vars['selector'].get())
                    field_vars['selector'].trace('w', update_selector)
                    selector_text.bind('<KeyRelease>', lambda e: field_vars['selector'].set(selector_text.get("1.0", tk.END).strip()))
                    row += 1
                
                if action_type in [ActionType.INPUT_TEXT, ActionType.UPLOAD_IMAGE]:
                    label = "Text:" if action_type == ActionType.INPUT_TEXT else "File Path:"
                    ttk.Label(fields_frame, text=label, font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                            sticky=tk.W, pady=10, padx=(0, 15))
                    field_vars['value'] = tk.StringVar()
                    value_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                    value_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                    
                    def update_value(*args):
                        value_text.delete("1.0", tk.END)
                        value_text.insert("1.0", field_vars['value'].get())
                    field_vars['value'].trace('w', update_value)
                    value_text.bind('<KeyRelease>', lambda e: field_vars['value'].set(value_text.get("1.0", tk.END).strip()))
                    
                    if action_type == ActionType.UPLOAD_IMAGE:
                        ttk.Button(fields_frame, text="Browse", font=('Arial', 11),
                                  command=lambda: field_vars['value'].set(
                                      filedialog.askopenfilename()
                                  )).grid(row=row, column=2, padx=10, pady=10)
                    row += 1
                    
                elif action_type == ActionType.TOGGLE_SETTING:
                    ttk.Label(fields_frame, text="Enable:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                                sticky=tk.W, pady=10, padx=(0, 15))
                    field_vars['value'] = tk.BooleanVar()
                    check_frame = ttk.Frame(fields_frame)
                    check_frame.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                    ttk.Checkbutton(check_frame, variable=field_vars['value'], 
                                   style='Large.TCheckbutton').pack(pady=10)
                    row += 1
                    
                elif action_type == ActionType.CHECK_ELEMENT:
                    # Check type dropdown
                    ttk.Label(fields_frame, text="Check Type:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                                sticky=tk.W, pady=10, padx=(0, 15))
                    field_vars['check_type'] = tk.StringVar(value="equals")
                    check_types = ["equals", "not_equals", "greater", "less", "contains", "not_zero"]
                    check_combo = ttk.Combobox(fields_frame, textvariable=field_vars['check_type'],
                                              values=check_types, state='readonly', width=58,
                                              font=('Arial', 22))
                    check_combo.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                    row += 1
                    
                    # Expected value
                    ttk.Label(fields_frame, text="Expected Value:", font=('Arial', 20, 'bold')).grid(row=row, column=0,
                                                                sticky=tk.W, pady=10, padx=(0, 15))
                    field_vars['expected_value'] = tk.StringVar()
                    expected_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                    expected_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                    
                    def update_expected(*args):
                        expected_text.delete("1.0", tk.END)
                        expected_text.insert("1.0", field_vars['expected_value'].get())
                    field_vars['expected_value'].trace('w', update_expected)
                    expected_text.bind('<KeyRelease>', lambda e: field_vars['expected_value'].set(expected_text.get("1.0", tk.END).strip()))
                    row += 1
                    
                    # Attribute to check
                    ttk.Label(fields_frame, text="Attribute:", font=('Arial', 20, 'bold')).grid(row=row, column=0,
                                                                sticky=tk.W, pady=10, padx=(0, 15))
                    field_vars['attribute'] = tk.StringVar(value="text")
                    attr_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                    attr_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                    attr_text.insert("1.0", "text")
                    
                    def update_attr(*args):
                        attr_text.delete("1.0", tk.END)
                        attr_text.insert("1.0", field_vars['attribute'].get())
                    field_vars['attribute'].trace('w', update_attr)
                    attr_text.bind('<KeyRelease>', lambda e: field_vars['attribute'].set(attr_text.get("1.0", tk.END).strip()))
                    
                    # Attribute help text
                    ttk.Label(fields_frame, text="(e.g., text, value, data-count, aria-label)", 
                             font=('Arial', 12), foreground='gray').grid(row=row+1, column=1, sticky=tk.W, pady=(0, 10))
                    row += 2
                    
                elif action_type == ActionType.WAIT:
                    ttk.Label(fields_frame, text="Wait (ms):", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                                   sticky=tk.W, pady=10, padx=(0, 15))
                    field_vars['value'] = tk.StringVar(value="1000")
                    wait_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
                    wait_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
                    wait_text.insert("1.0", "1000")
                    
                    def update_wait(*args):
                        wait_text.delete("1.0", tk.END)
                        wait_text.insert("1.0", field_vars['value'].get())
                    field_vars['value'].trace('w', update_wait)
                    wait_text.bind('<KeyRelease>', lambda e: field_vars['value'].set(wait_text.get("1.0", tk.END).strip()))
                    row += 1
            
            # Description field (always present)
            ttk.Label(fields_frame, text="Description:", font=('Arial', 20, 'bold')).grid(row=row, column=0, 
                                                             sticky=tk.W, pady=10, padx=(0, 15))
            field_vars['description'] = tk.StringVar()
            desc_text = tk.Text(fields_frame, width=60, height=1, font=('Arial', 24), wrap=tk.WORD)
            desc_text.grid(row=row, column=1, pady=10, sticky=(tk.W, tk.E))
            
            def update_desc(*args):
                desc_text.delete("1.0", tk.END)
                desc_text.insert("1.0", field_vars['description'].get())
            field_vars['description'].trace('w', update_desc)
            desc_text.bind('<KeyRelease>', lambda e: field_vars['description'].set(desc_text.get("1.0", tk.END).strip()))
            
        action_type_var.trace('w', update_fields)
        update_fields()  # Initial field setup
        
        # Buttons - positioned at bottom right corner
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 15), padx=(0, 25), sticky=(tk.E, tk.S))
        
        def add_action():
            """Add the action to the list"""
            action_type = ActionType(action_type_var.get())
            
            # Create action based on type and fields
            action_data = {
                'type': action_type,
                'description': field_vars.get('description', tk.StringVar()).get()
            }
            
            if action_type == ActionType.LOGIN:
                # Handle login action with special value structure
                login_data = {
                    'username': field_vars['username'].get(),
                    'password': field_vars['password'].get(),
                    'username_selector': field_vars['username_selector'].get(),
                    'password_selector': field_vars['password_selector'].get(),
                    'submit_selector': field_vars['submit_selector'].get()
                }
                action_data['value'] = login_data
            elif action_type == ActionType.CHECK_ELEMENT:
                # Handle check element action with special value structure
                check_data = {
                    'check': field_vars['check_type'].get(),
                    'value': field_vars['expected_value'].get(),
                    'attribute': field_vars['attribute'].get()
                }
                action_data['selector'] = field_vars.get('selector', tk.StringVar()).get()
                action_data['value'] = check_data
            else:
                if 'selector' in field_vars:
                    action_data['selector'] = field_vars['selector'].get()
                if 'value' in field_vars:
                    value = field_vars['value'].get()
                    if isinstance(field_vars['value'], tk.BooleanVar):
                        value = field_vars['value'].get()
                    elif action_type == ActionType.WAIT:
                        value = int(value)
                    action_data['value'] = value
                
            # Add to listbox
            display_text = f"{action_type.value}"
            if action_type == ActionType.LOGIN:
                # Show username for login actions
                username = login_data.get('username', '')
                if username:
                    display_text += f" ({username})"
            if action_data.get('description'):
                display_text += f" - {action_data['description']}"
            self.actions_listbox.insert(tk.END, display_text)
            
            # Store action data
            if not hasattr(self, 'actions_data'):
                self.actions_data = []
            self.actions_data.append(action_data)
            
            dialog.destroy()
            
        ModernButton(button_frame, text="Add", command=add_action).pack(side=tk.LEFT, padx=10)
        ModernButton(button_frame, text="Cancel", 
                    command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
    def _edit_action(self):
        """Edit selected action"""
        selection = self.actions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an action to edit")
            return
        
        if not hasattr(self, 'actions_data') or not self.actions_data:
            messagebox.showwarning("No Data", "No action data available to edit")
            return
            
        index = selection[0]
        if index >= len(self.actions_data):
            messagebox.showwarning("Invalid Selection", "Selected action index is invalid")
            return
            
        action_data = self.actions_data[index]
        
        # Show edit dialog with current data
        self._show_edit_action_dialog(action_data, index)
    
    def _show_edit_action_dialog(self, action_data, index):
        """Show dialog to edit an existing action"""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Edit Action")
            dialog.geometry("600x700")
            dialog.transient(self.root)
            
            # Add protocol handler to prevent dialog from closing unexpectedly
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            
            # Main frame
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Action type (read-only) - with error handling
            try:
                if isinstance(action_data['type'], str):
                    action_type = ActionType(action_data['type'])
                else:
                    action_type = action_data['type']
            except (ValueError, KeyError) as e:
                messagebox.showerror("Error", f"Invalid action type: {action_data.get('type', 'unknown')}")
                dialog.destroy()
                return
            
            ttk.Label(main_frame, text="Action Type:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            type_label = ttk.Label(main_frame, text=action_type.value, 
                                  foreground="gray", font=("Segoe UI", 10))
            type_label.pack(anchor=tk.W, pady=(0, 10))
            
            # Scrollable frame for fields
            canvas = tk.Canvas(main_frame, height=400)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            # Dictionary to store field variables
            field_vars = {}
            
            try:
                # Create fields based on action type
                self._create_action_fields(scrollable_frame, action_type, field_vars, action_data)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create fields: {str(e)}")
                dialog.destroy()
                return
            
            # Configure scrollable area
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True, pady=(0, 10))
            scrollbar.pack(side="right", fill="y", pady=(0, 10))
            
            # Update canvas scroll region after widget creation
            scrollable_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(20, 0))
            
            def save_action():
                """Save the edited action"""
                try:
                    # Create updated action data
                    updated_data = {
                        'type': action_type,
                        'description': field_vars.get('description', tk.StringVar()).get()
                    }
                    
                    # Handle different action types
                    if action_type == ActionType.LOGIN:
                        login_data = {
                            'username': field_vars['username'].get(),
                            'password': field_vars['password'].get(),
                            'username_selector': field_vars['username_selector'].get(),
                            'password_selector': field_vars['password_selector'].get(),
                            'submit_selector': field_vars['submit_selector'].get()
                        }
                        updated_data['value'] = login_data
                    elif action_type == ActionType.CHECK_ELEMENT:
                        check_data = {
                            'check': field_vars['check_type'].get(),
                            'value': field_vars['expected_value'].get(),
                            'attribute': field_vars['attribute'].get()
                        }
                        updated_data['selector'] = field_vars.get('selector', tk.StringVar()).get()
                        updated_data['value'] = check_data
                    elif action_type in [ActionType.IF_BEGIN, ActionType.ELIF, ActionType.WHILE_BEGIN]:
                        # Handle conditional block actions
                        condition_data = {
                            'condition': field_vars['condition'].get()
                        }
                        updated_data['value'] = condition_data
                    elif action_type in [ActionType.CONDITIONAL_WAIT]:
                        # Handle conditional wait
                        conditional_data = {
                            'condition': field_vars['condition'].get(),
                            'wait_time': int(field_vars['wait_time'].get() or 5000),
                            'max_retries': int(field_vars['max_retries'].get() or 3),
                            'retry_from_action': int(field_vars['retry_from_action'].get() or 0)
                        }
                        updated_data['value'] = conditional_data
                    elif action_type in [ActionType.SKIP_IF]:
                        # Handle skip if
                        skip_data = {
                            'condition': field_vars['condition'].get(),
                            'skip_count': int(field_vars['skip_count'].get() or 1)
                        }
                        updated_data['value'] = skip_data
                    else:
                        # Handle standard actions
                        if 'selector' in field_vars:
                            updated_data['selector'] = field_vars['selector'].get()
                        if 'value' in field_vars:
                            value = field_vars['value'].get()
                            if isinstance(field_vars['value'], tk.BooleanVar):
                                value = field_vars['value'].get()
                            elif action_type == ActionType.WAIT:
                                value = int(value) if value else 1000
                            updated_data['value'] = value
                    
                    # Update the action data
                    self.actions_data[index] = updated_data
                    
                    # Update the display
                    self._update_action_display(index, updated_data)
                    
                    dialog.destroy()
                    messagebox.showinfo("Success", "Action updated successfully!")
                    
                except ValueError as e:
                    messagebox.showerror("Invalid Input", f"Please check your input values: {str(e)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update action: {str(e)}")
            
            ModernButton(button_frame, text="Save", command=save_action).pack(side=tk.LEFT, padx=10)
            ModernButton(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
            
            # Center dialog on parent window
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
            y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
            
            # Don't grab_set to prevent freezing
            dialog.focus_set()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create edit dialog: {str(e)}")
            if 'dialog' in locals():
                dialog.destroy()
    
    def _update_action_display(self, index, action_data):
        """Update the display text for an action in the listbox"""
        action_type = ActionType(action_data['type']) if isinstance(action_data['type'], str) else action_data['type']
        
        # Create display text
        display_text = f"{action_type.value}"
        
        if action_type == ActionType.LOGIN:
            # Show username for login actions
            login_data = action_data.get('value', {})
            username = login_data.get('username', '')
            if username:
                display_text += f" ({username})"
        elif action_type == ActionType.CHECK_ELEMENT:
            # Show selector and check type
            selector = action_data.get('selector', '')
            check_data = action_data.get('value', {})
            check_type = check_data.get('check', '')
            if selector:
                display_text += f" ({selector[:20]}...)" if len(selector) > 20 else f" ({selector})"
        elif action_type in [ActionType.IF_BEGIN, ActionType.ELIF, ActionType.WHILE_BEGIN]:
            # Show condition for conditional blocks
            condition_data = action_data.get('value', {})
            condition = condition_data.get('condition', 'check_passed')
            display_text += f" ({condition})"
        elif action_type in [ActionType.CONDITIONAL_WAIT, ActionType.SKIP_IF]:
            # Show condition for conditional actions
            conditional_data = action_data.get('value', {})
            condition = conditional_data.get('condition', 'check_failed')
            display_text += f" ({condition})"
        elif action_data.get('selector'):
            # Show selector for other actions
            selector = action_data['selector']
            display_text += f" ({selector[:20]}...)" if len(selector) > 20 else f" ({selector})"
        
        if action_data.get('description'):
            display_text += f" - {action_data['description']}"
        
        # Update the listbox
        self.actions_listbox.delete(index)
        self.actions_listbox.insert(index, display_text)
        self.actions_listbox.selection_set(index)
    
    def _create_action_fields(self, parent, action_type, field_vars, action_data=None):
        """Create form fields based on action type for add/edit dialogs"""
        
        # Common description field
        ttk.Label(parent, text="Description:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        field_vars['description'] = tk.StringVar()
        if action_data and action_data.get('description'):
            field_vars['description'].set(action_data['description'])
        ttk.Entry(parent, textvariable=field_vars['description'], width=50).pack(anchor=tk.W, pady=(0, 15))
        
        # Block control actions (IF/WHILE/ELSE)
        if action_type in [ActionType.IF_BEGIN, ActionType.ELIF, ActionType.WHILE_BEGIN]:
            ttk.Label(parent, text="Condition:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['condition'] = tk.StringVar()
            condition_combo = ttk.Combobox(parent, textvariable=field_vars['condition'], 
                                         values=['check_passed', 'check_failed', 'value_equals', 'value_not_equals'],
                                         state='readonly', width=47)
            condition_combo.pack(anchor=tk.W, pady=(0, 5))
            
            # Set default/current value
            if action_data and action_data.get('value', {}).get('condition'):
                field_vars['condition'].set(action_data['value']['condition'])
            else:
                field_vars['condition'].set('check_passed')
            
            # Help text
            help_text = "Condition to evaluate based on the last CHECK_ELEMENT result:\n" \
                       "• check_passed: Execute if last check returned true\n" \
                       "• check_failed: Execute if last check returned false\n" \
                       "• value_equals: Execute if actual equals expected\n" \
                       "• value_not_equals: Execute if actual differs from expected"
            ttk.Label(parent, text=help_text, font=("Segoe UI", 8), foreground="gray").pack(anchor=tk.W, pady=(0, 15))
        
        elif action_type in [ActionType.ELSE, ActionType.IF_END, ActionType.WHILE_END, ActionType.BREAK, ActionType.CONTINUE]:
            # These actions don't need additional configuration
            ttk.Label(parent, text="No additional configuration needed for this action type.", 
                     font=("Segoe UI", 10), foreground="gray").pack(anchor=tk.W, pady=(0, 15))
        
        elif action_type == ActionType.CONDITIONAL_WAIT:
            # Condition dropdown
            ttk.Label(parent, text="Condition:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['condition'] = tk.StringVar()
            condition_combo = ttk.Combobox(parent, textvariable=field_vars['condition'],
                                         values=['check_failed', 'check_passed', 'value_equals', 'value_not_equals'],
                                         state='readonly', width=47)
            condition_combo.pack(anchor=tk.W, pady=(0, 10))
            
            # Wait time
            ttk.Label(parent, text="Wait Time (ms):", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['wait_time'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['wait_time'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Max retries
            ttk.Label(parent, text="Max Retries:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['max_retries'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['max_retries'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Retry from action
            ttk.Label(parent, text="Retry From Action Index:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['retry_from_action'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['retry_from_action'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Set defaults/current values
            if action_data and action_data.get('value'):
                value_data = action_data['value']
                field_vars['condition'].set(value_data.get('condition', 'check_failed'))
                field_vars['wait_time'].set(str(value_data.get('wait_time', 5000)))
                field_vars['max_retries'].set(str(value_data.get('max_retries', 3)))
                field_vars['retry_from_action'].set(str(value_data.get('retry_from_action', 0)))
            else:
                field_vars['condition'].set('check_failed')
                field_vars['wait_time'].set('5000')
                field_vars['max_retries'].set('3')
                field_vars['retry_from_action'].set('0')
        
        elif action_type == ActionType.SKIP_IF:
            # Condition dropdown
            ttk.Label(parent, text="Condition:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['condition'] = tk.StringVar()
            condition_combo = ttk.Combobox(parent, textvariable=field_vars['condition'],
                                         values=['check_passed', 'check_failed', 'value_equals', 'value_not_equals'],
                                         state='readonly', width=47)
            condition_combo.pack(anchor=tk.W, pady=(0, 10))
            
            # Skip count
            ttk.Label(parent, text="Skip Count:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['skip_count'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['skip_count'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Set defaults/current values
            if action_data and action_data.get('value'):
                value_data = action_data['value']
                field_vars['condition'].set(value_data.get('condition', 'check_passed'))
                field_vars['skip_count'].set(str(value_data.get('skip_count', 1)))
            else:
                field_vars['condition'].set('check_passed')
                field_vars['skip_count'].set('1')
        
        elif action_type == ActionType.LOGIN:
            # Username
            ttk.Label(parent, text="Username:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['username'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['username'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Password
            ttk.Label(parent, text="Password:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['password'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['password'], show="*", width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Username selector
            ttk.Label(parent, text="Username Selector:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['username_selector'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['username_selector'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Password selector
            ttk.Label(parent, text="Password Selector:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['password_selector'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['password_selector'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Submit selector
            ttk.Label(parent, text="Submit Selector:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['submit_selector'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['submit_selector'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Set current values if editing
            if action_data and action_data.get('value'):
                login_data = action_data['value']
                field_vars['username'].set(login_data.get('username', ''))
                field_vars['password'].set(login_data.get('password', ''))
                field_vars['username_selector'].set(login_data.get('username_selector', ''))
                field_vars['password_selector'].set(login_data.get('password_selector', ''))
                field_vars['submit_selector'].set(login_data.get('submit_selector', ''))
        
        elif action_type == ActionType.CHECK_ELEMENT:
            # Selector
            ttk.Label(parent, text="Selector:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['selector'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['selector'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Check type
            ttk.Label(parent, text="Check Type:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['check_type'] = tk.StringVar()
            check_combo = ttk.Combobox(parent, textvariable=field_vars['check_type'],
                                     values=['equals', 'not_equals', 'greater', 'less', 'contains', 'not_zero'],
                                     state='readonly', width=47)
            check_combo.pack(anchor=tk.W, pady=(0, 10))
            
            # Expected value
            ttk.Label(parent, text="Expected Value:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['expected_value'] = tk.StringVar()
            ttk.Entry(parent, textvariable=field_vars['expected_value'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            # Attribute
            ttk.Label(parent, text="Attribute:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
            field_vars['attribute'] = tk.StringVar()
            attribute_combo = ttk.Combobox(parent, textvariable=field_vars['attribute'],
                                         values=['text', 'value', 'data-count', 'data-status', 'aria-valuenow', 'href', 'title'],
                                         width=47)
            attribute_combo.pack(anchor=tk.W, pady=(0, 10))
            
            # Set current values if editing
            if action_data:
                if action_data.get('selector'):
                    field_vars['selector'].set(action_data['selector'])
                if action_data.get('value'):
                    check_data = action_data['value']
                    field_vars['check_type'].set(check_data.get('check', 'equals'))
                    field_vars['expected_value'].set(check_data.get('value', ''))
                    field_vars['attribute'].set(check_data.get('attribute', 'text'))
            else:
                field_vars['check_type'].set('equals')
                field_vars['attribute'].set('text')
        
        else:
            # Standard actions (wait, click, input, etc.)
            if action_type in [ActionType.CLICK_BUTTON, ActionType.INPUT_TEXT, ActionType.WAIT_FOR_ELEMENT]:
                ttk.Label(parent, text="Selector:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
                field_vars['selector'] = tk.StringVar()
                if action_data and action_data.get('selector'):
                    field_vars['selector'].set(action_data['selector'])
                ttk.Entry(parent, textvariable=field_vars['selector'], width=50).pack(anchor=tk.W, pady=(0, 10))
            
            if action_type in [ActionType.INPUT_TEXT, ActionType.WAIT]:
                value_label = "Text:" if action_type == ActionType.INPUT_TEXT else "Duration (ms):"
                ttk.Label(parent, text=value_label, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
                field_vars['value'] = tk.StringVar()
                if action_data and action_data.get('value'):
                    field_vars['value'].set(str(action_data['value']))
                ttk.Entry(parent, textvariable=field_vars['value'], width=50).pack(anchor=tk.W, pady=(0, 10))
        
    def _delete_action(self):
        """Delete selected action"""
        selection = self.actions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an action to delete")
            return
            
        if messagebox.askyesno("Confirm Delete", "Delete selected action?"):
            index = selection[0]
            self.actions_listbox.delete(index)
            if hasattr(self, 'actions_data'):
                self.actions_data.pop(index)
                
    def _move_action(self, direction):
        """Move selected action up or down"""
        selection = self.actions_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        new_index = index + direction
        
        if 0 <= new_index < self.actions_listbox.size():
            # Get items
            item = self.actions_listbox.get(index)
            self.actions_listbox.delete(index)
            self.actions_listbox.insert(new_index, item)
            self.actions_listbox.selection_set(new_index)
            
            # Update data
            if hasattr(self, 'actions_data'):
                self.actions_data[index], self.actions_data[new_index] = \
                    self.actions_data[new_index], self.actions_data[index]
                    
    def _load_config(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.current_config = AutomationSequenceBuilder.load_from_file(filename)
                self._update_ui_from_config()
                self._log("Loaded configuration from: " + filename, "success")
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load config: {str(e)}")
                
    def _save_config(self):
        """Save current configuration to file"""
        if not self.name_var.get() or not self.url_var.get():
            messagebox.showwarning("Missing Info", 
                                 "Please enter name and URL before saving")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                config = self._build_config_from_ui()
                builder = AutomationSequenceBuilder(config.name, config.url)
                builder.config = config
                builder.save_to_file(filename)
                self._log("Saved configuration to: " + filename, "success")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save config: {str(e)}")
                
    def _new_config(self):
        """Create new configuration"""
        if messagebox.askyesno("New Configuration", 
                             "Clear current configuration and start new?"):
            self.name_var.set("")
            self.url_var.set("")
            self.headless_var.set(True)
            self.actions_listbox.delete(0, tk.END)
            if hasattr(self, 'actions_data'):
                self.actions_data.clear()
            self._log("Created new configuration", "info")
            
    def _update_ui_from_config(self):
        """Update UI elements from loaded config"""
        if not self.current_config:
            return
            
        self.name_var.set(self.current_config.name)
        self.url_var.set(self.current_config.url)
        self.headless_var.set(self.current_config.headless)
        
        # Clear and repopulate actions
        self.actions_listbox.delete(0, tk.END)
        self.actions_data = []
        
        for action in self.current_config.actions:
            display_text = f"{action.type.value}"
            if action.type == ActionType.LOGIN and action.value:
                # Show username for login actions
                username = action.value.get('username', '') if isinstance(action.value, dict) else ''
                if username:
                    display_text += f" ({username})"
            if action.description:
                display_text += f" - {action.description}"
            self.actions_listbox.insert(tk.END, display_text)
            
            action_data = {
                'type': action.type,
                'selector': action.selector,
                'value': action.value,
                'description': action.description,
                'timeout': action.timeout
            }
            self.actions_data.append(action_data)
            
    def _build_config_from_ui(self) -> AutomationConfig:
        """Build AutomationConfig from UI state"""
        config = AutomationConfig(
            name=self.name_var.get(),
            url=self.url_var.get(),
            headless=self.headless_var.get(),
            actions=[]
        )
        
        if hasattr(self, 'actions_data'):
            for action_data in self.actions_data:
                action = Action(
                    type=action_data['type'],
                    selector=action_data.get('selector'),
                    value=action_data.get('value'),
                    timeout=action_data.get('timeout', 30000),
                    description=action_data.get('description')
                )
                config.actions.append(action)
                
        return config
        
    def _run_automation(self):
        """Run the automation in a separate thread"""
        if not self.name_var.get() or not self.url_var.get():
            messagebox.showwarning("Missing Info", 
                                 "Please enter name and URL before running")
            return
            
        if not hasattr(self, 'actions_data') or not self.actions_data:
            messagebox.showwarning("No Actions", 
                                 "Please add at least one action before running")
            return
            
        # Set automation state
        self.is_running = True
        self.stop_requested = False
        
        # Disable run button, enable stop
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Reset progress
        self.progress_var.set(0)
        self.status_label.config(text="Running...")
        
        # Build config and run in thread
        config = self._build_config_from_ui()
        self.automation_thread = threading.Thread(
            target=self._run_automation_thread,
            args=(config,),
            daemon=True
        )
        self.automation_thread.start()
        
    def _run_automation_thread(self, config):
        """Run automation in separate thread"""
        try:
            # Create custom log handler
            import logging
            
            class QueueHandler(logging.Handler):
                def __init__(self, log_queue):
                    super().__init__()
                    self.log_queue = log_queue
                    
                def emit(self, record):
                    self.log_queue.put(('info', self.format(record)))
                    
            # Setup logging
            logger = logging.getLogger('web_automation')
            handler = QueueHandler(self.log_queue)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            # Reuse existing engine if available, otherwise create new one
            if self.current_engine:
                # Update config for existing engine
                self.current_engine.config = config
                engine = self.current_engine
                self.log_queue.put(('info', 'Reusing existing browser window'))
            else:
                # Create new engine
                engine = WebAutomationEngine(config)
                # Store engine reference for browser control
                self.current_engine = engine
                self.log_queue.put(('info', 'Creating new browser window'))
            
            # Create event loop for thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run automation
            self.log_queue.put(('info', 'Starting automation execution...'))
            try:
                results = loop.run_until_complete(engine.run_automation())
                self.log_queue.put(('info', f'Automation completed with results: {results}'))
            except Exception as automation_error:
                self.log_queue.put(('error', f"Automation execution failed: {str(automation_error)}"))
                self.log_queue.put(('error', f"Error type: {type(automation_error).__name__}"))
                # Log the full traceback
                import traceback
                self.log_queue.put(('error', f"Traceback: {traceback.format_exc()}"))
                raise
            
            # Update UI with results (pass engine to enable browser close button)
            self.root.after(0, self._automation_complete, results, engine)
            
        except Exception as e:
            self.log_queue.put(('error', f"Thread error: {str(e)}"))
            self.log_queue.put(('error', f"Error type: {type(e).__name__}"))
            # Log the full traceback
            import traceback
            self.log_queue.put(('error', f"Traceback: {traceback.format_exc()}"))
            self.root.after(0, self._automation_complete, {'success': False})
            
    def _automation_complete(self, results, engine=None):
        """Handle automation completion"""
        # Reset automation state
        self.is_running = False
        self.stop_requested = False
        
        # Re-enable buttons
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        # Enable browser close button if engine is available
        if engine and getattr(engine, 'browser', None):
            self.close_browser_button.config(state=tk.NORMAL)
            self._log("Browser kept open - use 'Close Browser' button when done", "info")
        else:
            self.close_browser_button.config(state=tk.DISABLED)
        
        # Update progress
        self.progress_var.set(100 if results['success'] else 
                            (results['actions_completed'] / results['total_actions'] * 100))
        
        # Update status
        status = "Completed successfully!" if results['success'] else "Completed with errors"
        self.status_label.config(text=status)
        
        # Update statistics
        stats = f"""Automation: {self.name_var.get()}
Status: {'Success' if results['success'] else 'Failed'}
Actions: {results['actions_completed']}/{results['total_actions']}
Time: {datetime.now().strftime('%H:%M:%S')}

Errors: {len(results.get('errors', []))}
"""
        
        if results.get('outputs'):
            stats += "\nOutputs:\n"
            for key, value in results['outputs'].items():
                stats += f"  {key}: {value}\n"
                
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
        self.stats_text.config(state=tk.DISABLED)
        
        # Log completion
        if results['success']:
            self._log("Automation completed successfully!", "success")
        else:
            self._log("Automation completed with errors", "error")
            for error in results.get('errors', []):
                self._log(f"  Error: {error}", "error")
                
    def _stop_automation(self):
        """Stop running automation"""
        if not self.is_running:
            messagebox.showinfo("Not Running", "No automation is currently running")
            return
        
        # Confirm stop action
        result = messagebox.askyesno(
            "Stop Automation", 
            "Are you sure you want to stop the running automation?\n\n"
            "This will interrupt the current workflow and may leave\n"
            "the browser in an incomplete state."
        )
        
        if not result:
            return
        
        try:
            # Set stop flag
            self.stop_requested = True
            
            # Update UI immediately
            self.run_button.config(text="Stopping...", state="disabled")
            self.stop_button.config(state="disabled")
            
            # Log stop request
            self._log_message("🛑 Stop requested by user", "warning")
            
            # If we have an engine with a page, try to stop gracefully
            if hasattr(self, 'current_engine') and self.current_engine:
                if hasattr(self.current_engine, 'page') and self.current_engine.page:
                    # Try to stop any ongoing page operations
                    try:
                        # This will interrupt any ongoing page operations
                        asyncio.create_task(self._graceful_stop())
                    except Exception as e:
                        self._log_message(f"⚠️ Error during graceful stop: {e}", "error")
            
            # Update status
            self._log_message("⏹️ Automation stopped by user", "info")
            
            # Reset UI state
            self._reset_ui_after_completion()
            
        except Exception as e:
            self._log_message(f"❌ Error stopping automation: {e}", "error")
            messagebox.showerror("Stop Error", f"Failed to stop automation: {str(e)}")
            
            # Force UI reset even if stop failed
            self._reset_ui_after_completion()
    
    async def _graceful_stop(self):
        """Perform graceful stop of automation"""
        try:
            if hasattr(self, 'current_engine') and self.current_engine:
                # Try to stop any ongoing operations
                if hasattr(self.current_engine, 'page') and self.current_engine.page:
                    # Cancel any pending operations
                    await self.current_engine.page.evaluate("window.stop()")
                    
                # Close browser if needed
                if hasattr(self.current_engine, 'cleanup'):
                    await self.current_engine.cleanup(close_browser=True)
                    
        except Exception as e:
            print(f"Warning: Error during graceful stop: {e}")
    
    def _reset_ui_after_completion(self):
        """Reset UI state after automation completion or stop"""
        self.is_running = False
        self.stop_requested = False
        
        # Reset buttons
        self.run_button.config(state=tk.NORMAL, text="Run Automation")
        self.stop_button.config(state=tk.DISABLED)
        
        # Update status
        self.status_label.config(text="Ready")
        
        # Enable browser close if browser is still open
        if self.current_engine and hasattr(self.current_engine, 'browser') and self.current_engine.browser:
            self.close_browser_button.config(state=tk.NORMAL)
        else:
            self.close_browser_button.config(state=tk.DISABLED)
    
    def _close_browser(self):
        """Close the browser manually"""
        if self.current_engine:
            try:
                # Run the close browser coroutine in a thread
                def close_browser_sync():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.current_engine.close_browser())
                    loop.close()
                
                # Run in a separate thread to avoid blocking GUI
                thread = threading.Thread(target=close_browser_sync)
                thread.start()
                
                self._log("Browser closed", "success")
                self.close_browser_button.config(state=tk.DISABLED)
                self.current_engine = None
            except Exception as e:
                self._log(f"Failed to close browser: {e}", "error")
        else:
            self._log("No browser to close", "warning")
        
    def _log(self, message, tag="info"):
        """Add message to log queue"""
        self.log_queue.put((tag, f"[{datetime.now().strftime('%H:%M:%S')}] {message}"))
        
    def _process_log_queue(self):
        """Process messages from log queue"""
        try:
            while True:
                tag, message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n", tag)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_log_queue)
            
    def _load_settings(self):
        """Load settings from file"""
        default_settings = {
            'font_size': 20,
            'dark_mode': False,
            'theme': 'clam',
            # Professional dark theme colors
            'dark_background': '#1e1e1e',      # VS Code dark background
            'dark_surface': '#2d2d30',         # Slightly lighter surface
            'dark_input': '#3c3c3c',           # Input field background
            'dark_accent': '#007acc',          # VS Code blue accent
            'dark_text': '#cccccc',            # Light grey text
            'dark_text_bright': '#ffffff',     # White for important text
            'dark_success': '#4ec9b0',         # Teal green for success
            'dark_warning': '#dcdcaa',         # Light yellow for warnings
            'dark_error': '#f44747',           # Red for errors
            # Light theme colors
            'light_background': '#ffffff',
            'light_surface': '#f8f8f8',
            'light_input': '#ffffff',
            'light_accent': '#0078d4',
            'light_text': '#323130',
            'light_text_bright': '#000000',
            'light_success': '#107c10',
            'light_warning': '#f7630c',
            'light_error': '#d13438',
            # Custom color overrides
            'custom_background': None,
            'custom_primary': None,
            'custom_font': None
        }
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                default_settings.update(settings)
                return default_settings
            else:
                return default_settings
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings: {e}")
            return default_settings
            
    def _save_settings(self):
        """Save current settings to file"""
        try:
            # Update settings with current values
            self.settings['font_size'] = self.font_size_var.get()
            self.settings['dark_mode'] = self.dark_mode_var.get()
            
            # Update color settings if they exist
            if hasattr(self, 'custom_bg_var'):
                self.settings['custom_background'] = self.custom_bg_var.get() or None
            if hasattr(self, 'custom_primary_var'):
                self.settings['custom_primary'] = self.custom_primary_var.get() or None
            if hasattr(self, 'custom_font_var'):
                self.settings['custom_font'] = self.custom_font_var.get() or None
            
            # Create directory if it doesn't exist
            self.settings_file.parent.mkdir(exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
                
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")
            
        except IOError as e:
            messagebox.showerror("Save Error", f"Failed to save settings: {e}")
            
    def _apply_settings(self):
        """Apply current settings to the UI"""
        # Apply font size settings
        font_size = self.settings.get('font_size', 20)
        
        # Update ALL ttk styles with new font size
        self.style.configure('Title.TLabel', font=('Arial', font_size + 4, 'bold'))
        self.style.configure('Heading.TLabel', font=('Arial', font_size, 'bold'))
        self.style.configure('TLabel', font=('Arial', max(10, font_size - 4)))
        self.style.configure('TButton', font=('Arial', max(10, font_size - 6)))
        self.style.configure('TEntry', font=('Arial', max(10, font_size - 4)))
        self.style.configure('TCombobox', font=('Arial', max(10, font_size - 4)))
        self.style.configure('TCheckbutton', font=('Arial', max(10, font_size - 4)))
        
        # Apply dark mode if enabled
        if self.settings.get('dark_mode', False):
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
            
        # Apply saved resolution
        self._apply_saved_resolution()
            
    def _apply_dark_theme(self):
        """Apply professional dark theme colors"""
        # Get colors with custom overrides
        bg_main = self.settings.get('custom_background') or self.settings.get('dark_background', '#1e1e1e')
        bg_surface = self.settings.get('dark_surface', '#2d2d30')
        bg_input = self.settings.get('dark_input', '#3c3c3c')
        accent_color = self.settings.get('custom_primary') or self.settings.get('dark_accent', '#007acc')
        text_color = self.settings.get('custom_font') or self.settings.get('dark_text', '#cccccc')
        text_bright = self.settings.get('dark_text_bright', '#ffffff')
        success_color = self.settings.get('dark_success', '#4ec9b0')
        
        self.root.configure(bg=bg_main)
        
        # Configure ttk styles for professional dark theme - preserving fonts
        font_size = self.settings.get('font_size', 20)
        
        self.style.configure('TFrame', background=bg_main)
        self.style.configure('TLabel', background=bg_main, foreground=text_color,
                           font=('Arial', max(10, font_size - 4)))
        self.style.configure('TLabelFrame', background=bg_main, foreground=text_bright, 
                            borderwidth=1, relief='solid')
        self.style.configure('TLabelFrame.Label', background=bg_main, foreground=text_bright)
        
        # Improved button styling
        self.style.configure('TButton', background=bg_surface, foreground=text_color,
                           borderwidth=1, relief='solid', font=('Arial', max(10, font_size - 6)))
        self.style.map('TButton', 
                      background=[('active', accent_color), ('pressed', bg_input)])
        
        # Better input field contrast with grey-teal color like highlighted selection
        input_bg = '#4a5c5a'  # Grey-teal color similar to highlighted combobox
        input_fg = '#ffffff'  # White text for maximum contrast
        
        self.style.configure('TEntry', 
                           background=input_bg, foreground=input_fg,
                           borderwidth=1, relief='solid', insertcolor=input_fg,
                           font=('Arial', max(10, font_size - 4)),
                           fieldbackground=input_bg, selectbackground='#6b7d7b',
                           selectforeground='#ffffff')
        
        self.style.configure('TCombobox', 
                           background=input_bg, foreground=input_fg,
                           borderwidth=1, relief='solid', font=('Arial', max(10, font_size - 4)),
                           fieldbackground=input_bg, selectbackground='#6b7d7b',
                           selectforeground='#ffffff', arrowcolor=input_fg)
        
        # Configure combobox dropdown appearance
        self.style.map('TCombobox',
                      background=[('readonly', input_bg), ('active', '#5a6c6a')],
                      foreground=[('readonly', input_fg)],
                      fieldbackground=[('readonly', input_bg), ('active', '#5a6c6a')],
                      selectbackground=[('readonly', '#6b7d7b')],
                      selectforeground=[('readonly', '#ffffff')])
        
        self.style.configure('TCheckbutton', background=bg_main, foreground=text_color,
                           font=('Arial', max(10, font_size - 4)))
        self.style.configure('TScale', background=bg_main, troughcolor=bg_input)
        
        # Notebook styling
        self.style.configure('TNotebook', background=bg_main, borderwidth=0)
        self.style.configure('TNotebook.Tab', background=bg_surface, foreground=text_color,
                           padding=[12, 8], borderwidth=1, relief='solid')
        self.style.map('TNotebook.Tab',
                      background=[('selected', accent_color), ('active', bg_input)])
        
        # Update tk.Scale widget if it exists
        if hasattr(self, 'font_slider'):
            self.font_slider.config(bg=bg_surface, fg=text_color, troughcolor=input_bg,
                                   activebackground=accent_color)
            
        # Update all tkinter widgets that don't use ttk styles
        self._update_tkinter_widgets_theme(bg_main, bg_surface, input_bg, text_color, input_fg)
        
        # Update preview colors
        self._update_theme_preview()
        
    def _apply_light_theme(self):
        """Apply professional light theme colors"""
        # Get colors with custom overrides
        bg_main = self.settings.get('custom_background') or self.settings.get('light_background', '#ffffff')
        bg_surface = self.settings.get('light_surface', '#f8f8f8')
        bg_input = self.settings.get('light_input', '#ffffff')
        accent_color = self.settings.get('custom_primary') or self.settings.get('light_accent', '#0078d4')
        text_color = self.settings.get('custom_font') or self.settings.get('light_text', '#323130')
        text_bright = self.settings.get('light_text_bright', '#000000')
        
        self.root.configure(bg=bg_main)
        
        # Configure ttk styles for professional light theme - preserving fonts
        font_size = self.settings.get('font_size', 20)
        
        self.style.configure('TFrame', background=bg_main)
        self.style.configure('TLabel', background=bg_main, foreground=text_color,
                           font=('Arial', max(10, font_size - 4)))
        self.style.configure('TLabelFrame', background=bg_main, foreground=text_bright,
                           borderwidth=1, relief='solid')
        self.style.configure('TLabelFrame.Label', background=bg_main, foreground=text_bright)
        
        # Improved button styling
        self.style.configure('TButton', background=bg_surface, foreground=text_color,
                           borderwidth=1, relief='solid', font=('Arial', max(10, font_size - 6)))
        self.style.map('TButton',
                      background=[('active', accent_color), ('pressed', '#e1e1e1')])
        
        # Better input field contrast for light theme
        light_input_bg = '#f0f0f0'  # Light grey for better contrast
        light_input_fg = '#000000'  # Black text for maximum contrast
        
        self.style.configure('TEntry', 
                           background=light_input_bg, foreground=light_input_fg,
                           borderwidth=1, relief='solid', insertcolor=light_input_fg,
                           font=('Arial', max(10, font_size - 4)),
                           fieldbackground=light_input_bg, selectbackground='#0078d4',
                           selectforeground='#ffffff')
                           
        self.style.configure('TCombobox', 
                           background=light_input_bg, foreground=light_input_fg,
                           borderwidth=1, relief='solid', font=('Arial', max(10, font_size - 4)),
                           fieldbackground=light_input_bg, selectbackground='#0078d4',
                           selectforeground='#ffffff', arrowcolor=light_input_fg)
        
        # Configure combobox dropdown appearance for light theme
        self.style.map('TCombobox',
                      background=[('readonly', light_input_bg), ('active', '#e8e8e8')],
                      foreground=[('readonly', light_input_fg)],
                      fieldbackground=[('readonly', light_input_bg), ('active', '#e8e8e8')],
                      selectbackground=[('readonly', '#0078d4')],
                      selectforeground=[('readonly', '#ffffff')])
        
        self.style.configure('TCheckbutton', background=bg_main, foreground=text_color,
                           font=('Arial', max(10, font_size - 4)))
        self.style.configure('TScale', background=bg_main, troughcolor=bg_surface)
        
        # Notebook styling
        self.style.configure('TNotebook', background=bg_main, borderwidth=0)
        self.style.configure('TNotebook.Tab', background=bg_surface, foreground=text_color,
                           padding=[12, 8], borderwidth=1, relief='solid')
        self.style.map('TNotebook.Tab',
                      background=[('selected', accent_color), ('active', '#e1e1e1')])
        
        # Update tk.Scale widget if it exists
        if hasattr(self, 'font_slider'):
            self.font_slider.config(bg=bg_surface, fg=text_color, troughcolor=light_input_bg,
                                   activebackground=accent_color)
            
        # Update all tkinter widgets that don't use ttk styles
        self._update_tkinter_widgets_theme(bg_main, bg_surface, light_input_bg, text_color, light_input_fg)
        
        # Update preview colors
        self._update_theme_preview()
        
    def _update_tkinter_widgets_theme(self, bg_main, bg_surface, bg_input, text_color, text_bright):
        """Update all tkinter widgets that don't use ttk styles"""
        # Update actions listbox
        if hasattr(self, 'actions_listbox'):
            self.actions_listbox.config(
                bg=bg_input,
                fg=text_bright,
                selectbackground=bg_surface,
                selectforeground=text_bright,
                font=('Arial', max(10, self.settings.get('font_size', 20) - 4))
            )
            
        # Update log text area
        if hasattr(self, 'log_text'):
            self.log_text.config(
                bg=bg_input,
                fg=text_color,
                insertbackground=text_bright,
                font=('Courier', max(9, self.settings.get('font_size', 20) - 6))
            )
            # Update log text tags for colored output
            self.log_text.tag_config('info', foreground=text_color)
            self.log_text.tag_config('success', foreground=self.settings.get('dark_success' if self.dark_mode_var.get() else 'light_success', '#4ec9b0'))
            self.log_text.tag_config('error', foreground=self.settings.get('dark_error' if self.dark_mode_var.get() else 'light_error', '#f44747'))
            self.log_text.tag_config('warning', foreground=self.settings.get('dark_warning' if self.dark_mode_var.get() else 'light_warning', '#dcdcaa'))
            
        # Update stats text area  
        if hasattr(self, 'stats_text'):
            self.stats_text.config(
                bg=bg_input,
                fg=text_color,
                insertbackground=text_bright,
                font=('Courier', max(9, self.settings.get('font_size', 20) - 6))
            )
            
        # Update Name and URL text entries
        if hasattr(self, 'name_entry'):
            self.name_entry.config(
                bg=bg_input,
                fg=text_bright,
                insertbackground=text_bright,
                selectbackground=bg_surface,
                selectforeground=text_bright,
                font=('Arial', max(10, self.settings.get('font_size', 20) - 4))
            )
            
        if hasattr(self, 'url_entry'):
            self.url_entry.config(
                bg=bg_input,
                fg=text_bright,
                insertbackground=text_bright,
                selectbackground=bg_surface,
                selectforeground=text_bright,
                font=('Arial', max(10, self.settings.get('font_size', 20) - 4))
            )
            
        # Update all ModernButton instances
        self._update_modern_buttons()
        
    def _update_modern_buttons(self):
        """Update all ModernButton instances to use current theme"""
        # Find all ModernButton widgets recursively
        def find_buttons(widget):
            buttons = []
            if isinstance(widget, ModernButton):
                buttons.append(widget)
            for child in widget.winfo_children():
                buttons.extend(find_buttons(child))
            return buttons
            
        buttons = find_buttons(self.root)
        for button in buttons:
            if hasattr(button, 'update_theme'):
                button.update_theme()
        
    def _on_font_size_changed(self, value):
        """Handle font size slider change"""
        font_size = int(float(value))
        self.font_size_label.config(text=f"{font_size}px")
        self.font_preview_label.config(font=('Arial', font_size))
        
        # Update settings
        self.settings['font_size'] = font_size
        
        # Update ALL ttk styles comprehensively
        self.style.configure('Title.TLabel', font=('Arial', font_size + 4, 'bold'))
        self.style.configure('Heading.TLabel', font=('Arial', font_size, 'bold'))
        self.style.configure('TLabel', font=('Arial', max(10, font_size - 4)))
        self.style.configure('TButton', font=('Arial', max(10, font_size - 6)))
        self.style.configure('TEntry', font=('Arial', max(10, font_size - 4)))
        self.style.configure('TCombobox', font=('Arial', max(10, font_size - 4)))
        self.style.configure('TCheckbutton', font=('Arial', max(10, font_size - 4)))
        
        # Force update of all ttk widgets
        self._force_ttk_update()
        
        # Update all tkinter widgets that don't use ttk styles
        try:
            if hasattr(self, 'actions_listbox'):
                self.actions_listbox.config(font=('Arial', max(10, font_size - 4)))
            if hasattr(self, 'log_text'):
                self.log_text.config(font=('Courier', max(9, font_size - 6)))
            if hasattr(self, 'stats_text'):
                self.stats_text.config(font=('Courier', max(9, font_size - 6)))
            if hasattr(self, 'name_entry'):
                self.name_entry.config(font=('Arial', max(10, font_size - 4)))
            if hasattr(self, 'url_entry'):
                self.url_entry.config(font=('Arial', max(10, font_size - 4)))
        except:
            pass  # Ignore errors if widgets don't exist yet
            
        # Update all ModernButton instances
        self._update_modern_buttons()
        
    def _on_resolution_changed(self, event=None):
        """Handle resolution dropdown change"""
        # Get the selected resolution value
        selected_desc = self.resolution_var.get()
        for res, desc in self.resolution_options:
            if desc == selected_desc:
                self.settings['window_resolution'] = res
                break
                
    def _apply_resolution(self):
        """Apply the selected resolution to the window"""
        resolution = self.settings.get('window_resolution', '1200x800')
        try:
            width, height = map(int, resolution.split('x'))
            
            # Get current window position
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            
            # Set new geometry while preserving position
            self.root.geometry(f"{width}x{height}+{current_x}+{current_y}")
            
            # Update current resolution label
            if hasattr(self, 'current_res_label'):
                self.current_res_label.config(text=f"Current: {width}x{height}")
                
            # Save settings
            self._save_settings()
            
            self._log(f"Window resolution changed to {width}x{height}", "success")
            
        except Exception as e:
            messagebox.showerror("Resolution Error", f"Failed to apply resolution: {str(e)}")
            
    def _apply_saved_resolution(self):
        """Apply the saved resolution on startup"""
        resolution = self.settings.get('window_resolution', '1200x800')
        if resolution != '1200x800':  # Only apply if different from default
            try:
                width, height = map(int, resolution.split('x'))
                # Get screen dimensions to ensure window fits
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Limit to 90% of screen size
                max_width = int(screen_width * 0.9)
                max_height = int(screen_height * 0.9)
                
                width = min(width, max_width)
                height = min(height, max_height)
                
                self.root.geometry(f"{width}x{height}")
                
            except Exception as e:
                # Fall back to default if there's an error
                self.root.geometry("1200x800")
                self.settings['window_resolution'] = '1200x800'
            
    def _force_ttk_update(self):
        """Force update of all ttk widgets by refreshing their styles"""
        # This forces all ttk widgets to re-read their style configurations
        def update_widget_styles(widget):
            if isinstance(widget, (ttk.Label, ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                # Force widget to update by temporarily changing and restoring style
                current_style = str(widget.cget('style'))
                widget.configure(style='temp_style_update')
                widget.configure(style=current_style)
            
            # Recursively update children
            for child in widget.winfo_children():
                update_widget_styles(child)
        
        try:
            update_widget_styles(self.root)
        except:
            pass  # Ignore any errors during update
            
    def _on_dark_mode_changed(self):
        """Handle dark mode toggle change"""
        # Update color preview defaults when theme changes
        if hasattr(self, 'bg_color_preview'):
            default_bg = '#1e1e1e' if self.dark_mode_var.get() else '#ffffff'
            if not self.custom_bg_var.get():
                self.bg_color_preview.config(bg=default_bg)
                
        if hasattr(self, 'primary_color_preview'):
            default_primary = '#007acc' if self.dark_mode_var.get() else '#0078d4'
            if not self.custom_primary_var.get():
                self.primary_color_preview.config(bg=default_primary)
                
        if hasattr(self, 'font_color_preview'):
            default_font = '#cccccc' if self.dark_mode_var.get() else '#323130'
            if not self.custom_font_var.get():
                self.font_color_preview.config(bg=default_font)
        
        # Apply the appropriate theme
        if self.dark_mode_var.get():
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
            
    def _reset_settings(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Reset Settings", 
                             "Are you sure you want to reset all settings to defaults?"):
            # Reset to defaults
            self.font_size_var.set(20)
            self.dark_mode_var.set(False)
            
            # Reset color variables
            if hasattr(self, 'custom_bg_var'):
                self.custom_bg_var.set('')
            if hasattr(self, 'custom_primary_var'):
                self.custom_primary_var.set('')
            if hasattr(self, 'custom_font_var'):
                self.custom_font_var.set('')
            
            # Reset color preview widgets
            if hasattr(self, 'bg_color_preview'):
                self.bg_color_preview.config(bg='#ffffff')
            if hasattr(self, 'primary_color_preview'):
                self.primary_color_preview.config(bg='#0078d4')
            if hasattr(self, 'font_color_preview'):
                self.font_color_preview.config(bg='#323130')
            
            # Update settings dict
            self.settings = {
                'font_size': 20,
                'dark_mode': False,
                'theme': 'clam',
                'custom_background': None,
                'custom_primary': None,
                'custom_font': None
            }
            
            # Apply changes
            self._on_font_size_changed(20)
            self._on_dark_mode_changed()
            
    def _choose_color(self, color_type):
        """Open color chooser dialog"""
        current_color = None
        title = ""
        
        if color_type == 'background':
            current_color = self.custom_bg_var.get() or (
                '#1e1e1e' if self.dark_mode_var.get() else '#ffffff')
            title = "Choose Background Color"
        elif color_type == 'primary':
            current_color = self.custom_primary_var.get() or (
                '#007acc' if self.dark_mode_var.get() else '#0078d4')
            title = "Choose Primary Color"
        elif color_type == 'font':
            current_color = self.custom_font_var.get() or (
                '#cccccc' if self.dark_mode_var.get() else '#323130')
            title = "Choose Font Color"
            
        color = colorchooser.askcolor(
            initialcolor=current_color,
            title=title
        )
        
        if color[1]:  # If a color was selected
            hex_color = color[1]
            
            if color_type == 'background':
                self.custom_bg_var.set(hex_color)
                self.bg_color_preview.config(bg=hex_color)
                self.settings['custom_background'] = hex_color
            elif color_type == 'primary':
                self.custom_primary_var.set(hex_color)
                self.primary_color_preview.config(bg=hex_color)
                self.settings['custom_primary'] = hex_color
            elif color_type == 'font':
                self.custom_font_var.set(hex_color)
                self.font_color_preview.config(bg=hex_color)
                self.settings['custom_font'] = hex_color
                
            # Apply the theme with new colors
            if self.dark_mode_var.get():
                self._apply_dark_theme()
            else:
                self._apply_light_theme()
                
    def _reset_color(self, color_type):
        """Reset color to default"""
        if color_type == 'background':
            self.custom_bg_var.set('')
            self.settings['custom_background'] = None
            default_color = '#1e1e1e' if self.dark_mode_var.get() else '#ffffff'
            self.bg_color_preview.config(bg=default_color)
        elif color_type == 'primary':
            self.custom_primary_var.set('')
            self.settings['custom_primary'] = None
            default_color = '#007acc' if self.dark_mode_var.get() else '#0078d4'
            self.primary_color_preview.config(bg=default_color)
        elif color_type == 'font':
            self.custom_font_var.set('')
            self.settings['custom_font'] = None
            default_color = '#cccccc' if self.dark_mode_var.get() else '#323130'
            self.font_color_preview.config(bg=default_color)
            
        # Apply the theme with reset colors
        if self.dark_mode_var.get():
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
            
    def _update_theme_preview(self):
        """Update the theme preview section"""
        if not hasattr(self, 'theme_preview_frame'):
            return
            
        if self.dark_mode_var.get():
            bg_color = self.settings.get('custom_background') or self.settings.get('dark_background', '#1e1e1e')
            text_color = self.settings.get('custom_font') or self.settings.get('dark_text', '#cccccc')
            title_color = self.settings.get('dark_text_bright', '#ffffff')
        else:
            bg_color = self.settings.get('custom_background') or self.settings.get('light_background', '#ffffff')
            text_color = self.settings.get('custom_font') or self.settings.get('light_text', '#323130')
            title_color = self.settings.get('light_text_bright', '#000000')
            
        self.theme_preview_frame.config(bg=bg_color)
        self.preview_title.config(bg=bg_color, fg=title_color)
        self.preview_text.config(bg=bg_color, fg=text_color)
        
    def _apply_dialog_theme(self, dialog):
        """Apply current theme to a dialog window"""
        if self.settings.get('dark_mode', False):
            bg_main = self.settings.get('custom_background') or self.settings.get('dark_background', '#1e1e1e')
            text_color = self.settings.get('custom_font') or self.settings.get('dark_text', '#cccccc')
        else:
            bg_main = self.settings.get('custom_background') or self.settings.get('light_background', '#ffffff')
            text_color = self.settings.get('custom_font') or self.settings.get('light_text', '#323130')
            
        dialog.configure(bg=bg_main)
        
        # Apply theme to all ttk widgets in dialog
        def apply_to_children(widget):
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Label, ttk.Button, ttk.Entry, ttk.Combobox, ttk.Frame)):
                    # TTK widgets will use the global style
                    pass
                elif isinstance(child, tk.Label):
                    child.configure(bg=bg_main, fg=text_color)
                elif isinstance(child, tk.Frame):
                    child.configure(bg=bg_main)
                apply_to_children(child)
        
        # Apply to all children after a short delay to ensure they exist
        dialog.after(10, lambda: apply_to_children(dialog))
        
    def _center_dialog(self, dialog, force_size=None):
        """Center dialog on the parent window"""
        dialog.update_idletasks()  # Ensure geometry is calculated
        
        # Get dialog dimensions
        if force_size:
            dialog_width, dialog_height = force_size
        else:
            dialog_width = max(dialog.winfo_reqwidth(), 400)  # Minimum 400px width
            dialog_height = max(dialog.winfo_reqheight(), 300)  # Minimum 300px height
        
        # Get parent window position and size
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        
        # Calculate centered position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Ensure dialog is not off-screen
        x = max(0, x)
        y = max(0, y)
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

def main():
    """Main entry point for GUI"""
    root = tk.Tk()
    app = AutomationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
