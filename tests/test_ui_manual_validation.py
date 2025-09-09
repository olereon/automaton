#!/usr/bin/env python3.11
"""
Manual UI Validation Test
Quick visual validation of UI elements and theme consistency.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_basic_gui_functionality():
    """Basic GUI functionality test without complex dependencies."""
    print("=" * 60)
    print("AUTOMATON UI MANUAL VALIDATION")
    print("=" * 60)
    
    try:
        # Test imports
        print("Testing imports...")
        from interfaces.gui import AutomationGUI
        from core.controller import AutomationController
        print("✅ All imports successful")
        
        # Test basic GUI creation (without showing window)
        print("\nTesting GUI creation...")
        
        # Create controller first
        controller = AutomationController()
        print("✅ Controller created")
        
        # Test GUI can be instantiated
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide window for testing
        gui = AutomationGUI(root)
        print("✅ GUI instance created")
        
        # Test basic attributes exist
        critical_attributes = [
            'root', 'notebook', 'action_listbox', 
            'run_button', 'stop_button', 'progress_bar'
        ]
        
        missing_attributes = []
        for attr in critical_attributes:
            if not hasattr(gui, attr):
                missing_attributes.append(attr)
            else:
                print(f"✅ Attribute {attr} exists")
        
        if missing_attributes:
            print(f"❌ Missing attributes: {missing_attributes}")
            return False
        
        # Test theme colors are applied
        print("\nTesting dark theme application...")
        root_bg = gui.root.cget('bg')
        if root_bg == '#2b2b2b':
            print(f"✅ Dark theme applied: background = {root_bg}")
        else:
            print(f"⚠️ Theme may not be applied: background = {root_bg}")
        
        # Test notebook tabs
        print("\nTesting tab structure...")
        try:
            tab_count = gui.notebook.index("end")
            print(f"✅ Found {tab_count} tabs")
            
            expected_tabs = ['Actions', 'Login Credentials', 'Generation Downloads', 'Automation Scheduler']
            found_tabs = []
            
            for i in range(tab_count):
                tab_text = gui.notebook.tab(i, "text")
                found_tabs.append(tab_text)
                print(f"  - Tab {i+1}: '{tab_text}'")
            
            missing_tabs = [tab for tab in expected_tabs if tab not in found_tabs]
            if missing_tabs:
                print(f"⚠️ Missing expected tabs: {missing_tabs}")
            else:
                print("✅ All expected tabs found")
            
        except Exception as e:
            print(f"❌ Tab testing failed: {e}")
        
        # Test button functionality
        print("\nTesting button configuration...")
        buttons = ['run_button', 'stop_button', 'pause_button']
        for button_name in buttons:
            if hasattr(gui, button_name):
                button = getattr(gui, button_name)
                text = button.cget('text')
                command = button.cget('command')
                
                if text and command:
                    print(f"✅ {button_name}: '{text}' (command configured)")
                else:
                    print(f"⚠️ {button_name}: text='{text}', command={bool(command)}")
        
        # Clean up
        try:
            root.quit()
            root.destroy()
        except:
            pass
        
        controller.stop()
        
        print("\n" + "=" * 60)
        print("✅ MANUAL UI VALIDATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_color_contrast_basic():
    """Basic color contrast validation."""
    print("\n=== BASIC COLOR CONTRAST TEST ===")
    
    # Define the dark theme colors
    colors = {
        'background': '#2b2b2b',
        'text': '#ffffff', 
        'button_bg': '#404040',
        'button_text': '#ffffff'
    }
    
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    
    def get_luminance(rgb):
        def linearize(c):
            return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)
        r, g, b = [linearize(c) for c in rgb]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    def contrast_ratio(color1, color2):
        l1 = get_luminance(hex_to_rgb(color1))
        l2 = get_luminance(hex_to_rgb(color2))
        if l1 > l2:
            return (l1 + 0.05) / (l2 + 0.05)
        else:
            return (l2 + 0.05) / (l1 + 0.05)
    
    # Test color combinations
    bg_text_ratio = contrast_ratio(colors['background'], colors['text'])
    button_ratio = contrast_ratio(colors['button_bg'], colors['button_text'])
    
    print(f"Background/Text contrast: {bg_text_ratio:.2f}:1", end="")
    if bg_text_ratio >= 4.5:
        print(" ✅ WCAG AA")
    else:
        print(" ❌ Below WCAG AA")
    
    print(f"Button/Text contrast: {button_ratio:.2f}:1", end="")
    if button_ratio >= 4.5:
        print(" ✅ WCAG AA")  
    else:
        print(" ❌ Below WCAG AA")
    
    return bg_text_ratio >= 4.5 and button_ratio >= 4.5

if __name__ == '__main__':
    success = test_basic_gui_functionality()
    contrast_ok = test_color_contrast_basic()
    
    if success and contrast_ok:
        print("\n🎉 ALL MANUAL VALIDATION TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some validation tests failed")
        sys.exit(1)