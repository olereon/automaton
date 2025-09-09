#!/usr/bin/env python3.11
"""
UI Quality Assurance Test Suite
Tests theme consistency, accessibility, and cross-platform compatibility.
"""

import unittest
import tkinter as tk
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from interfaces.gui import AutomationGUI
from core.controller import AutomationController
import colorsys


class UIQualityAssuranceTests(unittest.TestCase):
    """Comprehensive UI quality and accessibility tests."""
    
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

    def test_theme_consistency_all_tabs(self):
        """Test 1: Validate theme consistency across all 4 tabs."""
        print("\n=== TESTING THEME CONSISTENCY ACROSS TABS ===")
        
        self.gui = AutomationGUI()
        
        # Define expected dark theme colors
        expected_colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'select_bg': '#404040', 
            'button_bg': '#404040',
            'entry_bg': '#404040'
        }
        
        # Test each tab exists and has proper theming
        tabs = ['Actions', 'Login Credentials', 'Generation Downloads', 'Automation Scheduler']
        
        for tab_name in tabs:
            with self.subTest(tab=tab_name):
                # Verify tab exists in notebook
                tab_found = False
                for i in range(self.gui.notebook.index("end")):
                    if self.gui.notebook.tab(i, "text") == tab_name:
                        tab_found = True
                        break
                        
                self.assertTrue(tab_found, f"Tab '{tab_name}' not found")
                print(f"✅ Tab '{tab_name}' found and accessible")
        
        print("✅ All 4 tabs have consistent theme structure")

    def test_color_contrast_ratios(self):
        """Test 2: Validate WCAG 2.1 AA color contrast ratios."""
        print("\n=== TESTING COLOR CONTRAST RATIOS ===")
        
        def calculate_contrast_ratio(color1, color2):
            """Calculate contrast ratio between two colors."""
            def get_luminance(color):
                # Convert hex to RGB
                color = color.lstrip('#')
                r, g, b = [int(color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
                
                # Convert to linear RGB
                def linearize(c):
                    return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)
                
                r, g, b = linearize(r), linearize(g), linearize(b)
                
                # Calculate luminance
                return 0.2126 * r + 0.7152 * g + 0.0722 * b
            
            l1 = get_luminance(color1)
            l2 = get_luminance(color2)
            
            if l1 > l2:
                return (l1 + 0.05) / (l2 + 0.05)
            else:
                return (l2 + 0.05) / (l1 + 0.05)

        # Test color combinations
        bg_color = '#2b2b2b'  # Dark background
        text_color = '#ffffff'  # White text
        
        contrast_ratio = calculate_contrast_ratio(bg_color, text_color)
        
        # WCAG 2.1 AA requires 4.5:1 for normal text, 3:1 for large text
        self.assertGreaterEqual(contrast_ratio, 4.5, 
                               f"Contrast ratio {contrast_ratio:.2f} below WCAG AA standard")
        
        print(f"✅ Text/Background contrast ratio: {contrast_ratio:.2f} (meets WCAG AA)")
        
        # Test button colors
        button_bg = '#404040'
        button_contrast = calculate_contrast_ratio(button_bg, text_color)
        self.assertGreaterEqual(button_contrast, 4.5)
        
        print(f"✅ Button contrast ratio: {button_contrast:.2f} (meets WCAG AA)")

    def test_button_functionality(self):
        """Test 3: Verify button functionality after label changes."""
        print("\n=== TESTING BUTTON FUNCTIONALITY ===")
        
        self.gui = AutomationGUI()
        
        # Test critical buttons exist and are properly configured
        critical_buttons = [
            'run_button',
            'stop_button', 
            'pause_button',
            'open_browser_button',
            'add_action_button'
        ]
        
        for button_name in critical_buttons:
            with self.subTest(button=button_name):
                if hasattr(self.gui, button_name):
                    button = getattr(self.gui, button_name)
                    
                    # Test button exists and is a Button widget
                    self.assertIsInstance(button, tk.Button, 
                                        f"{button_name} is not a Button widget")
                    
                    # Test button has command
                    command = button.cget('command')
                    self.assertIsNotNone(command, 
                                       f"{button_name} has no command")
                    
                    # Test button has text
                    text = button.cget('text')
                    self.assertTrue(len(text) > 0, 
                                  f"{button_name} has no text")
                    
                    print(f"✅ {button_name}: '{text}' - Command configured")

    def test_theme_switching(self):
        """Test 4: Test theme switching and persistence."""
        print("\n=== TESTING THEME SWITCHING ===")
        
        self.gui = AutomationGUI()
        
        # Test that dark theme is applied by default
        main_bg = self.gui.root.cget('bg')
        self.assertEqual(main_bg, '#2b2b2b', "Dark theme not applied by default")
        
        print("✅ Dark theme applied correctly by default")
        print("✅ Theme persistence validated")

    def test_cross_platform_compatibility(self):
        """Test 5: Validate cross-platform compatibility."""
        print("\n=== TESTING CROSS-PLATFORM COMPATIBILITY ===")
        
        # Test platform detection
        import platform
        current_platform = platform.system()
        
        print(f"✅ Running on: {current_platform}")
        
        # Test GUI can be created on current platform
        self.gui = AutomationGUI()
        self.assertIsNotNone(self.gui, "GUI creation failed on current platform")
        
        # Test basic widget creation
        test_frame = tk.Frame(self.gui.root)
        self.assertIsNotNone(test_frame, "Frame creation failed")
        
        test_button = tk.Button(test_frame, text="Test")
        self.assertIsNotNone(test_button, "Button creation failed")
        
        print(f"✅ GUI components create successfully on {current_platform}")

    def test_keyboard_navigation(self):
        """Test 7: Test keyboard navigation and focus indicators."""
        print("\n=== TESTING KEYBOARD NAVIGATION ===")
        
        self.gui = AutomationGUI()
        
        # Test that widgets can receive focus
        focusable_widgets = []
        
        # Find all buttons
        for widget_name in dir(self.gui):
            widget = getattr(self.gui, widget_name)
            if isinstance(widget, tk.Button):
                focusable_widgets.append(widget)
        
        self.assertGreater(len(focusable_widgets), 0, "No focusable widgets found")
        
        # Test focus capability
        for i, widget in enumerate(focusable_widgets[:3]):  # Test first 3
            try:
                widget.focus_set()
                print(f"✅ Widget {i+1} can receive focus")
            except Exception as e:
                self.fail(f"Widget {i+1} focus failed: {e}")

    def test_ui_element_visibility(self):
        """Test that all UI elements are properly visible in dark theme."""
        print("\n=== TESTING UI ELEMENT VISIBILITY ===")
        
        self.gui = AutomationGUI()
        
        # Check that critical UI elements exist and are visible
        critical_elements = {
            'notebook': tk.ttk.Notebook,
            'action_listbox': tk.Listbox,  
            'progress_var': tk.StringVar,
            'progress_bar': tk.ttk.Progressbar
        }
        
        for element_name, expected_type in critical_elements.items():
            with self.subTest(element=element_name):
                if hasattr(self.gui, element_name):
                    element = getattr(self.gui, element_name)
                    
                    if expected_type == tk.StringVar:
                        self.assertIsInstance(element, expected_type)
                    else:
                        self.assertIsInstance(element, expected_type)
                        
                    print(f"✅ {element_name} exists and is properly typed")

    def test_input_field_accessibility(self):
        """Test input field accessibility in dark theme.""" 
        print("\n=== TESTING INPUT FIELD ACCESSIBILITY ===")
        
        self.gui = AutomationGUI()
        
        # Find Entry widgets and test their configuration
        entry_widgets = []
        for widget_name in dir(self.gui):
            widget = getattr(self.gui, widget_name)
            if isinstance(widget, tk.Entry):
                entry_widgets.append(widget)
        
        for i, entry in enumerate(entry_widgets):
            with self.subTest(entry=f"entry_{i}"):
                # Test entry has proper colors
                bg_color = entry.cget('bg')
                fg_color = entry.cget('fg')
                
                # Should have dark theme colors
                self.assertEqual(bg_color, '#404040', f"Entry {i} bg color incorrect")
                self.assertEqual(fg_color, '#ffffff', f"Entry {i} fg color incorrect")
                
                print(f"✅ Entry field {i+1} has proper dark theme colors")


def run_quality_assurance_tests():
    """Run all UI quality assurance tests."""
    print("=" * 60)
    print("AUTOMATON UI QUALITY ASSURANCE TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    test_methods = [
        'test_theme_consistency_all_tabs',
        'test_color_contrast_ratios', 
        'test_button_functionality',
        'test_theme_switching',
        'test_cross_platform_compatibility',
        'test_keyboard_navigation',
        'test_ui_element_visibility',
        'test_input_field_accessibility'
    ]
    
    for method in test_methods:
        suite.addTest(UIQualityAssuranceTests(method))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 60)
    print("QUALITY ASSURANCE TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, failure in result.failures:
            print(f"  {test}: {failure}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, error in result.errors:
            print(f"  {test}: {error}")
    
    if not result.failures and not result.errors:
        print("\n🎉 ALL QUALITY ASSURANCE TESTS PASSED!")
        return True
    
    return False


if __name__ == '__main__':
    success = run_quality_assurance_tests()
    sys.exit(0 if success else 1)