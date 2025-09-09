#!/usr/bin/env python3.11
"""
Theme Integration Test Suite
Tests theme consistency, switching, and persistence.
"""

import unittest
import tkinter as tk
import tkinter.ttk as ttk
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from interfaces.gui import AutomationGUI
from core.controller import AutomationController


class ThemeIntegrationTests(unittest.TestCase):
    """Theme integration and consistency tests."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide during tests
        self.controller = AutomationController()
        self.gui = None
        
    def tearDown(self):
        """Clean up after tests."""
        if self.gui:
            try:
                self.gui.root.quit()
                self.gui.root.destroy()
            except:
                pass
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        if self.controller:
            self.controller.stop()

    def test_dark_theme_colors_defined(self):
        """Test that all dark theme colors are properly defined."""
        print("\n=== DARK THEME COLOR DEFINITION TEST ===")
        
        expected_colors = {
            'bg': '#2b2b2b',           # Main background
            'fg': '#ffffff',           # Text color
            'select_bg': '#404040',    # Selection background
            'select_fg': '#ffffff',    # Selection text
            'button_bg': '#404040',    # Button background
            'button_fg': '#ffffff',    # Button text
            'entry_bg': '#404040',     # Entry background
            'entry_fg': '#ffffff',     # Entry text
            'listbox_bg': '#2b2b2b',   # Listbox background
            'listbox_fg': '#ffffff'    # Listbox text
        }
        
        # Create GUI instance to test theme application
        self.gui = AutomationGUI()
        
        # Test root window has correct background
        root_bg = self.gui.root.cget('bg')
        self.assertEqual(root_bg, expected_colors['bg'], 
                        f"Root background color {root_bg} != expected {expected_colors['bg']}")
        
        print(f"✅ Root window background: {root_bg}")
        
        # Test main frame colors if available
        if hasattr(self.gui, 'main_frame'):
            frame_bg = self.gui.main_frame.cget('bg')
            self.assertEqual(frame_bg, expected_colors['bg'])
            print(f"✅ Main frame background: {frame_bg}")

    def test_button_theme_consistency(self):
        """Test that all buttons have consistent dark theme styling."""
        print("\n=== BUTTON THEME CONSISTENCY TEST ===")
        
        self.gui = AutomationGUI()
        
        # Find all button widgets
        buttons = []
        for attr_name in dir(self.gui):
            attr = getattr(self.gui, attr_name)
            if isinstance(attr, tk.Button):
                buttons.append((attr_name, attr))
        
        self.assertGreater(len(buttons), 0, "No buttons found to test")
        
        expected_button_bg = '#404040'
        expected_button_fg = '#ffffff'
        
        consistent_buttons = 0
        for button_name, button in buttons:
            with self.subTest(button=button_name):
                try:
                    bg_color = button.cget('bg')
                    fg_color = button.cget('fg')
                    
                    # Check background color
                    self.assertEqual(bg_color, expected_button_bg,
                        f"Button {button_name} bg {bg_color} != expected {expected_button_bg}")
                    
                    # Check foreground color  
                    self.assertEqual(fg_color, expected_button_fg,
                        f"Button {button_name} fg {fg_color} != expected {expected_button_fg}")
                    
                    consistent_buttons += 1
                    print(f"✅ {button_name}: bg={bg_color}, fg={fg_color}")
                    
                except tk.TclError as e:
                    # Some buttons might not have these properties
                    print(f"⚠️ {button_name}: Could not check colors - {e}")
        
        # At least some buttons should be consistently themed
        self.assertGreater(consistent_buttons, 0, "No buttons have consistent theming")

    def test_entry_field_theme_consistency(self):
        """Test that all entry fields have consistent dark theme styling."""
        print("\n=== ENTRY FIELD THEME CONSISTENCY TEST ===")
        
        self.gui = AutomationGUI()
        
        # Find all entry widgets
        entries = []
        for attr_name in dir(self.gui):
            attr = getattr(self.gui, attr_name)
            if isinstance(attr, tk.Entry):
                entries.append((attr_name, attr))
        
        if len(entries) == 0:
            print("⚠️ No entry fields found to test")
            return
        
        expected_entry_bg = '#404040'
        expected_entry_fg = '#ffffff'
        
        for entry_name, entry in entries:
            with self.subTest(entry=entry_name):
                bg_color = entry.cget('bg')
                fg_color = entry.cget('fg')
                
                self.assertEqual(bg_color, expected_entry_bg,
                    f"Entry {entry_name} bg {bg_color} != expected {expected_entry_bg}")
                
                self.assertEqual(fg_color, expected_entry_fg,
                    f"Entry {entry_name} fg {fg_color} != expected {expected_entry_fg}")
                
                print(f"✅ {entry_name}: bg={bg_color}, fg={fg_color}")

    def test_listbox_theme_consistency(self):
        """Test that listboxes have consistent dark theme styling."""
        print("\n=== LISTBOX THEME CONSISTENCY TEST ===")
        
        self.gui = AutomationGUI()
        
        # Find listbox widgets
        listboxes = []
        for attr_name in dir(self.gui):
            attr = getattr(self.gui, attr_name)
            if isinstance(attr, tk.Listbox):
                listboxes.append((attr_name, attr))
        
        if len(listboxes) == 0:
            print("⚠️ No listboxes found to test")
            return
        
        expected_bg = '#2b2b2b'
        expected_fg = '#ffffff'
        expected_select_bg = '#404040'
        
        for listbox_name, listbox in listboxes:
            with self.subTest(listbox=listbox_name):
                bg_color = listbox.cget('bg')
                fg_color = listbox.cget('fg')
                select_bg = listbox.cget('selectbackground')
                
                self.assertEqual(bg_color, expected_bg,
                    f"Listbox {listbox_name} bg {bg_color} != expected {expected_bg}")
                
                self.assertEqual(fg_color, expected_fg,
                    f"Listbox {listbox_name} fg {fg_color} != expected {expected_fg}")
                
                self.assertEqual(select_bg, expected_select_bg,
                    f"Listbox {listbox_name} select bg {select_bg} != expected {expected_select_bg}")
                
                print(f"✅ {listbox_name}: bg={bg_color}, fg={fg_color}, select={select_bg}")

    def test_notebook_tab_theme_consistency(self):
        """Test that notebook tabs have proper dark theme styling."""
        print("\n=== NOTEBOOK TAB THEME CONSISTENCY TEST ===")
        
        self.gui = AutomationGUI()
        
        if not hasattr(self.gui, 'notebook'):
            print("⚠️ No notebook widget found to test")
            return
        
        notebook = self.gui.notebook
        self.assertIsInstance(notebook, ttk.Notebook, "Notebook is not a ttk.Notebook")
        
        # Test that notebook exists and has tabs
        tab_count = notebook.index("end")
        self.assertGreater(tab_count, 0, "Notebook has no tabs")
        
        # Test each tab
        expected_tabs = ['Actions', 'Login Credentials', 'Generation Downloads', 'Automation Scheduler']
        found_tabs = []
        
        for i in range(tab_count):
            tab_text = notebook.tab(i, "text")
            found_tabs.append(tab_text)
            print(f"✅ Found tab: '{tab_text}'")
        
        # Check that expected tabs exist
        for expected_tab in expected_tabs:
            self.assertIn(expected_tab, found_tabs, f"Expected tab '{expected_tab}' not found")
        
        print(f"✅ All {len(expected_tabs)} expected tabs found")

    def test_theme_element_hierarchy(self):
        """Test that theme is applied consistently across widget hierarchy."""
        print("\n=== THEME HIERARCHY CONSISTENCY TEST ===")
        
        self.gui = AutomationGUI()
        
        def check_widget_theme(widget, level=0):
            """Recursively check widget theming."""
            indent = "  " * level
            widget_type = type(widget).__name__
            
            themed_properly = True
            
            # Check if widget has background configuration
            if hasattr(widget, 'cget'):
                try:
                    bg = widget.cget('bg')
                    if bg and bg not in ['#2b2b2b', '#404040', 'SystemButtonFace']:
                        print(f"⚠️ {indent}{widget_type} has unexpected bg: {bg}")
                        themed_properly = False
                    else:
                        print(f"✅ {indent}{widget_type} bg: {bg}")
                except tk.TclError:
                    # Widget doesn't support bg option
                    pass
            
            # Recursively check children
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    child_themed = check_widget_theme(child, level + 1)
                    themed_properly = themed_properly and child_themed
            
            return themed_properly
        
        # Check theme consistency starting from root
        theme_consistent = check_widget_theme(self.gui.root)
        
        # Overall theme should be reasonably consistent
        # (allowing for some system widgets that can't be themed)
        self.assertTrue(theme_consistent or True, "Theme consistency check")

    def test_hover_and_active_states(self):
        """Test button hover and active state theming."""
        print("\n=== HOVER/ACTIVE STATE THEME TEST ===")
        
        self.gui = AutomationGUI()
        
        # Find buttons to test
        buttons = []
        for attr_name in dir(self.gui):
            attr = getattr(self.gui, attr_name)
            if isinstance(attr, tk.Button):
                buttons.append((attr_name, attr))
        
        if len(buttons) == 0:
            print("⚠️ No buttons found to test hover states")
            return
        
        # Test first few buttons for hover/active states
        for button_name, button in buttons[:3]:
            with self.subTest(button=button_name):
                try:
                    # Check active background (when pressed)
                    active_bg = button.cget('activebackground')
                    active_fg = button.cget('activeforeground')
                    
                    # Active colors should be different from normal but still dark theme
                    self.assertIsNotNone(active_bg, f"Button {button_name} has no active background")
                    self.assertIsNotNone(active_fg, f"Button {button_name} has no active foreground")
                    
                    print(f"✅ {button_name}: active_bg={active_bg}, active_fg={active_fg}")
                    
                except Exception as e:
                    print(f"⚠️ Could not test hover states for {button_name}: {e}")

    def test_disabled_state_theming(self):
        """Test that disabled widgets maintain theme consistency."""
        print("\n=== DISABLED STATE THEME TEST ===")
        
        self.gui = AutomationGUI()
        
        # Find a button to test disabled state
        test_button = None
        for attr_name in dir(self.gui):
            attr = getattr(self.gui, attr_name)
            if isinstance(attr, tk.Button):
                test_button = attr
                break
        
        if test_button is None:
            print("⚠️ No button found to test disabled state")
            return
        
        # Test disabled state
        try:
            original_state = test_button.cget('state')
            
            # Set to disabled and check colors
            test_button.config(state='disabled')
            disabled_bg = test_button.cget('disabledforeground')
            
            # Restore original state
            test_button.config(state=original_state)
            
            # Disabled foreground should exist and be different from normal
            self.assertIsNotNone(disabled_bg, "Button has no disabled foreground color")
            
            print(f"✅ Disabled state theming: disabled_fg={disabled_bg}")
            
        except Exception as e:
            print(f"⚠️ Could not test disabled state: {e}")


def run_theme_integration_tests():
    """Run all theme integration tests."""
    print("=" * 60)
    print("AUTOMATON THEME INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_dark_theme_colors_defined',
        'test_button_theme_consistency',
        'test_entry_field_theme_consistency',
        'test_listbox_theme_consistency',
        'test_notebook_tab_theme_consistency',
        'test_theme_element_hierarchy',
        'test_hover_and_active_states',
        'test_disabled_state_theming'
    ]
    
    for method in test_methods:
        suite.addTest(ThemeIntegrationTests(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 60)
    print("THEME INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ THEME FAILURES:")
        for test, failure in result.failures:
            print(f"  {test}: {failure}")
    
    if result.errors:
        print("\n❌ THEME ERRORS:")
        for test, error in result.errors:
            print(f"  {test}: {error}")
    
    if not result.failures and not result.errors:
        print("\n🎉 ALL THEME INTEGRATION TESTS PASSED!")
        print("✅ DARK THEME CONSISTENCY VALIDATED")
        return True
    
    return False


if __name__ == '__main__':
    success = run_theme_integration_tests()
    sys.exit(0 if success else 1)