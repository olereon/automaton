#!/usr/bin/env python3.11
"""
Test script for new Action and Selector tabs functionality
Tests the integration and key features without requiring GUI interaction
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

import tkinter as tk
from interfaces.gui import AutomationGUI
from core.engine import ActionType, Action

def test_action_tab_integration():
    """Test Action tab integration and functionality"""
    print("🧪 Testing Action Tab Integration...")
    
    # Create a root window (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create GUI instance
        app = AutomationGUI(root)
        
        # Test 1: Verify new tabs exist
        assert hasattr(app, 'action_frame'), "Action tab frame not found"
        assert hasattr(app, 'selector_frame'), "Selector tab frame not found"
        print("✅ New tab frames created successfully")
        
        # Test 2: Verify action tab variables exist
        assert hasattr(app, 'action_type_var'), "Action type variable not found"
        assert hasattr(app, 'action_selector_var'), "Action selector variable not found"
        assert hasattr(app, 'action_value_var'), "Action value variable not found"
        assert hasattr(app, 'action_timeout_var'), "Action timeout variable not found"
        print("✅ Action tab variables initialized")
        
        # Test 3: Verify selector tab variables exist
        assert hasattr(app, 'selector_url_var'), "Selector URL variable not found"
        assert hasattr(app, 'selector_element_var'), "Selector element variable not found"
        assert hasattr(app, 'selector_strategy_var'), "Selector strategy variable not found"
        print("✅ Selector tab variables initialized")
        
        # Test 4: Verify action sequence list exists
        assert hasattr(app, 'action_sequence_list'), "Action sequence list not found"
        assert isinstance(app.action_sequence_list, list), "Action sequence list is not a list"
        print("✅ Action sequence list initialized")
        
        # Test 5: Test action parameter functionality
        app.action_type_var.set("input_text")
        app.action_selector_var.set("#test-input")
        app.action_value_var.set("test value")
        app.action_timeout_var.set("5000")
        
        # Simulate adding to action sequence
        app._add_to_action_sequence()
        
        assert len(app.action_sequence_list) == 1, "Action not added to sequence"
        action = app.action_sequence_list[0]
        assert action.type == ActionType.INPUT_TEXT, "Action type not set correctly"
        assert action.selector == "#test-input", "Action selector not set correctly"
        assert action.value == "test value", "Action value not set correctly"
        assert action.timeout == 5000, "Action timeout not set correctly"
        print("✅ Action creation and sequence management works")
        
        # Test 6: Test selector generation
        selectors = app._get_sample_selectors("test-btn", "all")
        assert len(selectors) > 0, "No selectors generated"
        assert any("test-btn" in selector[1] for selector in selectors), "Identifier not found in selectors"
        print("✅ Selector generation works")
        
        # Test 7: Test Apply to Main functionality 
        initial_actions = len(getattr(app, 'actions', []))
        app._apply_action_to_main()
        
        # Check if action was added
        current_actions = len(getattr(app, 'actions', []))
        assert current_actions == initial_actions + 1, "Action not applied to main"
        print("✅ Apply to Main functionality works")
        
        print("🎉 All Action Tab tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        root.destroy()
    
    return True

def test_selector_tab_integration():
    """Test Selector tab integration and functionality"""
    print("\n🧪 Testing Selector Tab Integration...")
    
    # Create a root window (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create GUI instance
        app = AutomationGUI(root)
        
        # Test 1: Test selector strategy variations
        strategies = ["id", "class", "css", "xpath", "text", "attribute", "dynamic"]
        
        for strategy in strategies:
            selectors = app._get_sample_selectors("test-element", strategy)
            assert len(selectors) > 0, f"No selectors generated for strategy: {strategy}"
            print(f"✅ Strategy '{strategy}' generates {len(selectors)} selectors")
        
        # Test 2: Test TreeView integration
        assert hasattr(app, 'selector_results_tree'), "Selector results tree not found"
        
        # Add a test selector to the tree
        app.selector_results_tree.insert('', 'end', text="1", 
                                        values=("ID", "#test-id", "High", "Low", "1"))
        
        # Test selection functionality (simulate)
        children = app.selector_results_tree.get_children()
        assert len(children) >= 1, "Selector not added to tree"
        print("✅ TreeView integration works")
        
        # Test 3: Test selector-to-action integration
        app.selector_element_var.set("login-btn")
        app._generate_selectors()
        
        # Check if selectors were added to tree
        children = app.selector_results_tree.get_children()
        assert len(children) > 1, "Selectors not generated and added to tree"
        print("✅ Selector generation and display works")
        
        print("🎉 All Selector Tab tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        root.destroy()
    
    return True

def test_tab_integration():
    """Test integration between tabs"""
    print("\n🧪 Testing Cross-Tab Integration...")
    
    # Create a root window (hidden)
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create GUI instance
        app = AutomationGUI(root)
        
        # Test 1: Generate selector and use in Action tab
        app.selector_element_var.set("submit-button")
        app._generate_selectors()
        
        # Simulate selecting first selector and using in action tab
        children = app.selector_results_tree.get_children()
        if children:
            # Simulate selection
            first_child = children[0]
            app.selector_results_tree.selection_set(first_child)
            
            # Use selector in action tab
            app._use_selector_in_action()
            
            # Verify selector was set in action tab
            selector_value = app.action_selector_var.get()
            assert selector_value != "", "Selector not copied to action tab"
            print(f"✅ Selector-to-Action integration works: {selector_value}")
        
        # Test 2: Create action and apply to main
        app.action_type_var.set("click_button")
        app.action_timeout_var.set("8000")
        
        initial_actions = len(getattr(app, 'actions', []))
        app._apply_action_to_main()
        current_actions = len(getattr(app, 'actions', []))
        
        assert current_actions > initial_actions, "Action not applied to main tab"
        print("✅ Action-to-Main integration works")
        
        print("🎉 All Cross-Tab Integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        root.destroy()
    
    return True

def main():
    """Run all tests"""
    print("🚀 Running New Tabs Functionality Tests\n")
    
    success = True
    
    # Run individual tests
    success &= test_action_tab_integration()
    success &= test_selector_tab_integration() 
    success &= test_tab_integration()
    
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '❌ SOME TESTS FAILED!'}")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)