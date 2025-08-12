# GUI Interface for Web Automation App
# Modern GUI using tkinter with custom styling

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import asyncio
import json
import threading
from pathlib import Path
from datetime import datetime
import queue

from core.engine import (
    WebAutomationEngine,
    AutomationSequenceBuilder,
    AutomationConfig,
    ActionType,
    Action
)

class ModernButton(tk.Button):
    """Custom styled button"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(
            relief=tk.FLAT,
            bg='#2196F3',
            fg='white',
            font=('Arial', 10),
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.bind('<Enter>', lambda e: self.configure(bg='#1976D2'))
        self.bind('<Leave>', lambda e: self.configure(bg='#2196F3'))

class AutomationGUI:
    """Modern GUI for Web Automation"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Web Automation Tool")
        self.root.geometry("1000x700")
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Variables
        self.current_config = None
        self.automation_thread = None
        self.log_queue = queue.Queue()
        
        # Setup UI
        self._setup_ui()
        self._setup_styles()
        
        # Start log processor
        self.root.after(100, self._process_log_queue)
        
    def _setup_styles(self):
        """Configure custom styles"""
        # Configure colors
        bg_color = '#f5f5f5'
        self.root.configure(bg=bg_color)
        
        # Configure ttk styles
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Action.TFrame', relief=tk.RIDGE, borderwidth=1)
        
    def _setup_ui(self):
        """Setup the main UI layout"""
        # Create main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_container, text="Web Automation Tool", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Left panel - Configuration
        self._create_config_panel(main_container)
        
        # Middle panel - Actions
        self._create_actions_panel(main_container)
        
        # Right panel - Controls
        self._create_controls_panel(main_container)
        
        # Bottom panel - Log output
        self._create_log_panel(main_container)
        
    def _create_config_panel(self, parent):
        """Create configuration panel"""
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # Name entry
        ttk.Label(config_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(config_frame, textvariable=self.name_var, width=25)
        name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # URL entry
        ttk.Label(config_frame, text="URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(config_frame, textvariable=self.url_var, width=25)
        url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Options
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(config_frame, text="Run headless", 
                                        variable=self.headless_var)
        headless_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # File operations
        file_frame = ttk.Frame(config_frame)
        file_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
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
        self.stop_button.configure(bg='#f44336')
        self.stop_button.pack(fill=tk.X, pady=5)
        
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
        dialog.geometry("400x300")
        
        # Action type selection
        ttk.Label(dialog, text="Action Type:").grid(row=0, column=0, sticky=tk.W, 
                                                   padx=10, pady=5)
        
        action_type_var = tk.StringVar()
        action_combo = ttk.Combobox(dialog, textvariable=action_type_var, 
                                   state='readonly', width=30)
        action_combo['values'] = [action.value for action in ActionType]
        action_combo.grid(row=0, column=1, padx=10, pady=5)
        action_combo.current(0)
        
        # Dynamic fields frame
        fields_frame = ttk.Frame(dialog)
        fields_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, 
                         sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
            if action_type not in [ActionType.REFRESH_PAGE]:
                if action_type != ActionType.WAIT:
                    ttk.Label(fields_frame, text="Selector:").grid(row=row, column=0, 
                                                                  sticky=tk.W, pady=5)
                    field_vars['selector'] = tk.StringVar()
                    ttk.Entry(fields_frame, textvariable=field_vars['selector'], 
                             width=30).grid(row=row, column=1, pady=5)
                    row += 1
                
                if action_type in [ActionType.INPUT_TEXT, ActionType.UPLOAD_IMAGE]:
                    label = "Text:" if action_type == ActionType.INPUT_TEXT else "File Path:"
                    ttk.Label(fields_frame, text=label).grid(row=row, column=0, 
                                                            sticky=tk.W, pady=5)
                    field_vars['value'] = tk.StringVar()
                    entry = ttk.Entry(fields_frame, textvariable=field_vars['value'], 
                                    width=30)
                    entry.grid(row=row, column=1, pady=5)
                    
                    if action_type == ActionType.UPLOAD_IMAGE:
                        ttk.Button(fields_frame, text="Browse",
                                  command=lambda: field_vars['value'].set(
                                      filedialog.askopenfilename()
                                  )).grid(row=row, column=2, padx=5)
                    row += 1
                    
                elif action_type == ActionType.TOGGLE_SETTING:
                    ttk.Label(fields_frame, text="Enable:").grid(row=row, column=0, 
                                                                sticky=tk.W, pady=5)
                    field_vars['value'] = tk.BooleanVar()
                    ttk.Checkbutton(fields_frame, 
                                   variable=field_vars['value']).grid(row=row, column=1, 
                                                                     sticky=tk.W, pady=5)
                    row += 1
                    
                elif action_type == ActionType.WAIT:
                    ttk.Label(fields_frame, text="Wait (ms):").grid(row=row, column=0, 
                                                                   sticky=tk.W, pady=5)
                    field_vars['value'] = tk.StringVar(value="1000")
                    ttk.Entry(fields_frame, textvariable=field_vars['value'], 
                             width=30).grid(row=row, column=1, pady=5)
                    row += 1
            
            # Description field (always present)
            ttk.Label(fields_frame, text="Description:").grid(row=row, column=0, 
                                                             sticky=tk.W, pady=5)
            field_vars['description'] = tk.StringVar()
            ttk.Entry(fields_frame, textvariable=field_vars['description'], 
                     width=30).grid(row=row, column=1, pady=5)
            
        action_type_var.trace('w', update_fields)
        update_fields()  # Initial field setup
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def add_action():
            """Add the action to the list"""
            action_type = ActionType(action_type_var.get())
            
            # Create action based on type and fields
            action_data = {
                'type': action_type,
                'description': field_vars.get('description', tk.StringVar()).get()
            }
            
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
            if action_data.get('description'):
                display_text += f" - {action_data['description']}"
            self.actions_listbox.insert(tk.END, display_text)
            
            # Store action data
            if not hasattr(self, 'actions_data'):
                self.actions_data = []
            self.actions_data.append(action_data)
            
            dialog.destroy()
            
        ModernButton(button_frame, text="Add", command=add_action).pack(side=tk.LEFT, padx=5)
        ModernButton(button_frame, text="Cancel", 
                    command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def _edit_action(self):
        """Edit selected action"""
        selection = self.actions_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an action to edit")
            return
            
        # TODO: Implement edit functionality
        messagebox.showinfo("Edit Action", "Edit functionality coming soon!")
        
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
            
            # Run automation
            engine = WebAutomationEngine(config)
            
            # Create event loop for thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run automation
            results = loop.run_until_complete(engine.run_automation())
            
            # Update UI with results
            self.root.after(0, self._automation_complete, results)
            
        except Exception as e:
            self.log_queue.put(('error', f"Automation error: {str(e)}"))
            self.root.after(0, self._automation_complete, {'success': False})
            
    def _automation_complete(self, results):
        """Handle automation completion"""
        # Re-enable buttons
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
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
        # TODO: Implement proper cancellation
        messagebox.showinfo("Stop", "Stop functionality coming soon!")
        
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

def main():
    """Main entry point for GUI"""
    root = tk.Tk()
    app = AutomationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
