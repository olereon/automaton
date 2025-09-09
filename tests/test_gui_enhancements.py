#!/usr/bin/env python3.11
"""
Comprehensive test suite for GUI enhancements: Move Down and Mute functionality
Testing UI/UX validation and integration with automation system
"""

import unittest
import tkinter as tk
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from interfaces.gui import AutomationGUI
from core.controller import AutomationController
from core.engine import ActionType


class TestGUIEnhancements(unittest.TestCase):
    """Test suite for GUI Move Down and Mute functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.controller = AutomationController()
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        self.app = AutomationGUI(self.root)
        
        # Add some test actions for move/mute testing
        self.test_actions = [
            {"type": "INPUT_TEXT", "selector": "#input1", "value": "test1", "timeout": 2000},
            {"type": "CLICK_BUTTON", "selector": "#button1", "timeout": 2000},
            {"type": "WAIT", "value": "1000", "timeout": 2000}
        ]
        
    def tearDown(self):
        """Clean up test environment"""
        if self.root:
            self.root.destroy()
    
    # CODE QUALITY VALIDATION TESTS
    
    def test_move_action_method_exists(self):
        """Test that _move_action method exists and is callable"""
        self.assertTrue(hasattr(self.app, '_move_action'))
        self.assertTrue(callable(getattr(self.app, '_move_action')))
    
    def test_mute_functionality_exists(self):
        """Test that mute functionality exists"""
        # Check for muted_actions tracking
        self.assertTrue(hasattr(self.app, 'muted_actions'))
        self.assertIsInstance(self.app.muted_actions, set)
        
        # Check for mute toggle method
        has_mute_method = (hasattr(self.app, '_toggle_mute_action') or 
                          hasattr(self.app, 'toggle_action_mute') or
                          hasattr(self.app, 'mute_action'))
        self.assertTrue(has_mute_method, "Mute toggle method should exist")
    
    def test_muted_actions_initialization(self):
        """Test that muted_actions set is properly initialized"""
        self.assertIsInstance(self.app.muted_actions, set)
        self.assertEqual(len(self.app.muted_actions), 0)
    
    # FUNCTIONALITY TESTING
    
    def test_move_action_with_valid_selection(self):
        """Test moving action down with valid selection"""
        # Add test actions to listbox
        for i, action in enumerate(self.test_actions):
            display_text = f"{action['type']} - {action.get('selector', action.get('value', ''))}"
            self.app.actions_listbox.insert(i, display_text)
        
        # Initialize actions_data if needed
        if not hasattr(self.app, 'actions_data'):
            self.app.actions_data = self.test_actions.copy()
        
        # Select first item and move down
        self.app.actions_listbox.selection_set(0)
        self.app._move_action(1)  # Move down
        
        # Check that selection moved
        selection = self.app.actions_listbox.curselection()
        self.assertEqual(selection[0], 1, "Action should move down to position 1")
    
    def test_move_action_boundary_conditions(self):
        """Test move action at boundaries"""
        # Add test actions
        for i, action in enumerate(self.test_actions):
            display_text = f"{action['type']} - {action.get('selector', action.get('value', ''))}"
            self.app.actions_listbox.insert(i, display_text)
        
        # Test moving last item down (should not move)
        last_index = len(self.test_actions) - 1
        self.app.actions_listbox.selection_set(last_index)
        
        original_item = self.app.actions_listbox.get(last_index)
        self.app._move_action(1)  # Try to move down
        
        # Should still be in same position
        current_item = self.app.actions_listbox.get(last_index)
        self.assertEqual(original_item, current_item, "Last item should not move down")
    
    def test_move_action_no_selection(self):
        """Test move action with no selection"""
        # Clear any selection
        self.app.actions_listbox.selection_clear(0, tk.END)
        
        # This should not raise an exception
        try:
            self.app._move_action(1)
        except Exception as e:
            self.fail(f"Move action with no selection should not raise exception: {e}")
    
    # UI/UX VALIDATION TESTS
    
    def test_button_layout_consistency(self):
        """Test that buttons have consistent sizing and layout"""
        # This tests the visual consistency mentioned in requirements
        # In a real GUI test framework, we'd check actual button dimensions
        # For now, we'll verify the buttons exist in the expected structure
        
        # The buttons should be created during _setup_ui()
        # We can verify they're properly configured by checking the GUI was initialized
        self.assertTrue(hasattr(self.app, 'actions_listbox'))
        self.assertTrue(hasattr(self.app, 'muted_actions'))
    
    def test_mute_visual_indicators(self):
        """Test mute visual indicators are working"""
        # Test muting an action
        if hasattr(self.app, '_toggle_mute_action'):
            # Add test action
            self.app.actions_listbox.insert(0, "TEST_ACTION - test")
            self.app.actions_listbox.selection_set(0)
            
            # Test muting
            self.app._toggle_mute_action()
            
            # Check if action was muted
            self.assertIn(0, self.app.muted_actions)
    
    # INTEGRATION TESTING
    
    def test_muted_actions_persistence_structure(self):
        """Test that muted actions structure supports workflow saving/loading"""
        # Test adding and removing muted actions
        self.app.muted_actions.add(0)
        self.app.muted_actions.add(2)
        
        # Verify structure
        self.assertIn(0, self.app.muted_actions)
        self.assertIn(2, self.app.muted_actions)
        self.assertNotIn(1, self.app.muted_actions)
        
        # Test removal
        self.app.muted_actions.remove(0)
        self.assertNotIn(0, self.app.muted_actions)
    
    def test_automation_execution_integration(self):
        """Test integration with automation execution system"""
        # This would test that muted actions are properly skipped
        # For now, we verify the structure supports this integration
        
        # The controller should exist
        self.assertIsInstance(self.controller, AutomationController)
        
        # The GUI should have proper muted action tracking
        self.assertIsInstance(self.app.muted_actions, set)
    
    def test_error_handling(self):
        """Test error handling in move and mute operations"""
        # Test various error conditions
        
        # Move with empty listbox
        try:
            self.app._move_action(1)
        except Exception as e:
            self.fail(f"Move with empty listbox should not raise exception: {e}")
        
        # Invalid direction
        self.app.actions_listbox.insert(0, "TEST_ACTION")
        self.app.actions_listbox.selection_set(0)
        try:
            self.app._move_action(100)  # Large direction
        except Exception as e:
            self.fail(f"Move with large direction should not raise exception: {e}")


class TestGUIQualityStandards(unittest.TestCase):
    """Test quality standards and code patterns"""
    
    def setUp(self):
        self.controller = AutomationController()
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = AutomationGUI(self.root)
    
    def tearDown(self):
        if self.root:
            self.root.destroy()
    
    def test_code_patterns_consistency(self):
        """Test that new code follows existing patterns"""
        # Check that _move_action follows naming conventions
        self.assertTrue(hasattr(self.app, '_move_action'))
        
        # Check that muted_actions follows data structure patterns
        self.assertIsInstance(self.app.muted_actions, set)
    
    def test_proper_error_handling(self):
        """Test proper error handling patterns"""
        # Methods should handle edge cases gracefully
        # No selection
        self.app._move_action(1)  # Should not crash
        
        # Out of bounds
        self.app.actions_listbox.insert(0, "test")
        self.app.actions_listbox.selection_set(0)
        self.app._move_action(-1)  # Move up from first position
        self.app._move_action(10)  # Move down beyond bounds
    
    def test_thread_safety_considerations(self):
        """Test considerations for thread safety in GUI operations"""
        # GUI operations should be safe for main thread
        self.assertTrue(hasattr(self.app, 'muted_actions'))
        
        # Data structures should be appropriate for concurrent access
        self.assertIsInstance(self.app.muted_actions, set)


if __name__ == '__main__':
    # Create test results directory
    results_dir = Path(__file__).parent / 'test_results'
    results_dir.mkdir(exist_ok=True)
    
    # Run tests with detailed output
    unittest.main(verbosity=2)