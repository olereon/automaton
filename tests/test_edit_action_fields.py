#!/usr/bin/env python3
"""
Test script to verify that all Edit Action windows have the correct input fields
matching their corresponding Add Action windows.
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'src'))

from core.engine import ActionType
from interfaces.gui import AutomationGUI
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import MagicMock, patch


class TestEditActionFields(unittest.TestCase):
    """Test that Edit Action dialogs have all required fields for each action type"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        self.gui = AutomationGUI(self.root)
        self.gui.actions_data = []
        
    def tearDown(self):
        """Clean up after test"""
        self.root.destroy()
        
    def test_all_action_types_have_fields(self):
        """Test that all action types are properly handled in _create_action_fields"""
        
        # List of all action types and their expected fields
        action_field_map = {
            ActionType.LOGIN: ['username', 'password', 'username_selector', 'password_selector', 'submit_selector', 'description', 'timeout'],
            ActionType.EXPAND_DIALOG: ['selector', 'description', 'timeout'],
            ActionType.INPUT_TEXT: ['selector', 'value', 'description', 'timeout'],
            ActionType.UPLOAD_IMAGE: ['selector', 'file_path', 'description', 'timeout'],
            ActionType.TOGGLE_SETTING: ['selector', 'value', 'description', 'timeout'],
            ActionType.CLICK_BUTTON: ['selector', 'description', 'timeout'],
            ActionType.CHECK_QUEUE: ['selector', 'value', 'description', 'timeout'],
            ActionType.CHECK_ELEMENT: ['selector', 'check_type', 'expected_value', 'attribute', 'description', 'timeout'],
            ActionType.CONDITIONAL_WAIT: ['condition', 'wait_time', 'max_retries', 'retry_from_action', 'retry_delay', 'description', 'timeout'],
            ActionType.SKIP_IF: ['condition', 'skip_count', 'reason', 'description', 'timeout'],
            ActionType.IF_BEGIN: ['condition', 'description', 'timeout'],
            ActionType.ELIF: ['condition', 'description', 'timeout'],
            ActionType.ELSE: ['description'],  # No timeout for simple block controls
            ActionType.IF_END: ['description'],
            ActionType.WHILE_BEGIN: ['condition', 'description', 'timeout'],
            ActionType.WHILE_END: ['description'],
            ActionType.BREAK: ['description'],
            ActionType.CONTINUE: ['description'],
            ActionType.STOP_AUTOMATION: ['description'],
            ActionType.DOWNLOAD_FILE: ['selector', 'description', 'timeout'],
            ActionType.REFRESH_PAGE: ['description'],
            ActionType.SWITCH_PANEL: ['selector', 'description', 'timeout'],
            ActionType.WAIT: ['value', 'description', 'timeout'],
            ActionType.WAIT_FOR_ELEMENT: ['selector', 'description', 'timeout'],
            ActionType.SET_VARIABLE: ['variable', 'value', 'description', 'timeout'],
            ActionType.INCREMENT_VARIABLE: ['variable', 'amount', 'description', 'timeout'],
            ActionType.LOG_MESSAGE: ['message', 'log_file', 'level', 'description', 'timeout'],
        }
        
        results = []
        
        for action_type in ActionType:
            # Create a test frame
            test_frame = ttk.Frame(self.root)
            field_vars = {}
            
            # Call _create_action_fields for this action type
            self.gui._create_action_fields(test_frame, action_type, field_vars, action_data=None)
            
            # Check if expected fields are present
            expected_fields = action_field_map.get(action_type, ['description'])
            missing_fields = []
            
            for field in expected_fields:
                if field not in field_vars:
                    missing_fields.append(field)
            
            # Check for unexpected fields
            unexpected_fields = []
            for field in field_vars:
                if field not in expected_fields:
                    unexpected_fields.append(field)
            
            # Record results
            result = {
                'action_type': action_type.value,
                'expected_fields': expected_fields,
                'actual_fields': list(field_vars.keys()),
                'missing_fields': missing_fields,
                'unexpected_fields': unexpected_fields,
                'status': 'PASS' if not missing_fields and not unexpected_fields else 'FAIL'
            }
            results.append(result)
            
            # Clean up
            test_frame.destroy()
        
        # Print test results
        print("\n" + "="*80)
        print("EDIT ACTION FIELD TEST RESULTS")
        print("="*80)
        
        passed = 0
        failed = 0
        
        for result in results:
            status_symbol = "✓" if result['status'] == 'PASS' else "✗"
            print(f"\n{status_symbol} {result['action_type']}: {result['status']}")
            
            if result['missing_fields']:
                print(f"  Missing fields: {', '.join(result['missing_fields'])}")
            if result['unexpected_fields']:
                print(f"  Unexpected fields: {', '.join(result['unexpected_fields'])}")
            
            if result['status'] == 'PASS':
                passed += 1
            else:
                failed += 1
        
        print("\n" + "-"*80)
        print(f"SUMMARY: {passed} PASSED, {failed} FAILED out of {len(results)} action types")
        print("="*80)
        
        # Assert all tests passed
        self.assertEqual(failed, 0, f"{failed} action types have incorrect fields in Edit dialog")
        
    def test_edit_dialog_data_collection(self):
        """Test that _collect_action_data properly handles all action types"""
        
        test_cases = [
            (ActionType.LOGIN, {'username': 'test', 'password': 'pass', 'username_selector': '#user', 
                               'password_selector': '#pass', 'submit_selector': '#submit'}),
            (ActionType.TOGGLE_SETTING, {'selector': '#toggle', 'value': True}),
            (ActionType.CHECK_QUEUE, {'selector': '.queue', 'value': 'Completed'}),
            (ActionType.EXPAND_DIALOG, {'selector': '#dialog'}),
            (ActionType.DOWNLOAD_FILE, {'selector': '.download-btn'}),
            (ActionType.SWITCH_PANEL, {'selector': '#panel-2'}),
        ]
        
        for action_type, test_data in test_cases:
            field_vars = {}
            
            # Create StringVar/BooleanVar objects for test data
            for key, value in test_data.items():
                if isinstance(value, bool):
                    field_vars[key] = tk.BooleanVar(value=value)
                else:
                    field_vars[key] = tk.StringVar(value=value)
            
            # Add description and timeout
            field_vars['description'] = tk.StringVar(value='Test action')
            field_vars['timeout'] = tk.StringVar(value='5000')
            
            # Call _collect_action_data
            result = self.gui._collect_action_data(action_type, field_vars)
            
            # Verify result
            self.assertEqual(result['type'], action_type, f"Action type mismatch for {action_type.value}")
            self.assertEqual(result['description'], 'Test action', f"Description mismatch for {action_type.value}")
            
            # Check specific fields based on action type
            if action_type == ActionType.LOGIN:
                self.assertIsInstance(result['value'], dict)
                self.assertEqual(result['value']['username'], 'test')
            elif action_type == ActionType.TOGGLE_SETTING:
                self.assertEqual(result['value'], True)
                self.assertEqual(result['selector'], '#toggle')
            elif action_type in [ActionType.CHECK_QUEUE]:
                self.assertEqual(result['selector'], test_data['selector'])
                self.assertEqual(result['value'], test_data['value'])
            elif action_type in [ActionType.EXPAND_DIALOG, ActionType.DOWNLOAD_FILE, ActionType.SWITCH_PANEL]:
                self.assertEqual(result['selector'], test_data['selector'])
        
        print("\nData collection test passed for all tested action types!")


if __name__ == '__main__':
    # Run the tests
    unittest.main(argv=[''], exit=False, verbosity=2)