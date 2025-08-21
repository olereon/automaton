#!/usr/bin/env python3
"""
Comprehensive test suite for Edit Action functionality
Tests all action types with complete field parity between Add and Edit dialogs
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from unittest.mock import Mock, patch
import tkinter as tk
from tkinter import ttk

from core.engine import ActionType

def create_test_action_data():
    """Create comprehensive test action data for all action types"""
    return {
        ActionType.LOGIN: {
            'type': ActionType.LOGIN,
            'description': 'Test login action',
            'selector': None,
            'value': {
                'username': 'testuser@example.com',
                'password': 'testpass123',
                'username_selector': 'input[type="email"]',
                'password_selector': 'input[type="password"]',
                'submit_selector': 'button[type="submit"]'
            },
            'timeout': 5000
        },
        ActionType.CHECK_ELEMENT: {
            'type': ActionType.CHECK_ELEMENT,
            'description': 'Test check element action',
            'selector': '.test-element',
            'value': {
                'check': 'contains',
                'value': 'Expected text',
                'attribute': 'text'
            },
            'timeout': 3000
        },
        ActionType.CONDITIONAL_WAIT: {
            'type': ActionType.CONDITIONAL_WAIT,
            'description': 'Test conditional wait action',
            'selector': None,
            'value': {
                'condition': 'check_passed',
                'wait_time': 5000,
                'max_retries': 3,
                'retry_delay': 1000
            },
            'timeout': 2000
        },
        ActionType.SKIP_IF: {
            'type': ActionType.SKIP_IF,
            'description': 'Test skip if action',
            'selector': None,
            'value': {
                'condition': 'check_failed',
                'skip_count': 2,
                'reason': 'Skip when check fails'
            },
            'timeout': 2000
        },
        ActionType.UPLOAD_IMAGE: {
            'type': ActionType.UPLOAD_IMAGE,
            'description': 'Test upload image action',
            'selector': 'input[type="file"]',
            'value': '/path/to/test/image.png',
            'timeout': 1000
        },
        ActionType.IF_BEGIN: {
            'type': ActionType.IF_BEGIN,
            'description': 'Test if begin action',
            'selector': None,
            'value': {
                'condition': 'check_passed'
            },
            'timeout': 2000
        },
        ActionType.SET_VARIABLE: {
            'type': ActionType.SET_VARIABLE,
            'description': 'Test set variable action',
            'selector': None,
            'value': {
                'variable': 'test_var',
                'value': 'test_value'
            },
            'timeout': 2000
        },
        ActionType.INCREMENT_VARIABLE: {
            'type': ActionType.INCREMENT_VARIABLE,
            'description': 'Test increment variable action',
            'selector': None,
            'value': {
                'variable': 'counter',
                'amount': 5
            },
            'timeout': 2000
        },
        ActionType.LOG_MESSAGE: {
            'type': ActionType.LOG_MESSAGE,
            'description': 'Test log message action',
            'selector': None,
            'value': {
                'message': 'Test log message',
                'log_file': 'logs/test.log',
                'level': 'info'
            },
            'timeout': 2000
        }
    }

class TestEditActionComprehensive(unittest.TestCase):
    """Test Edit Action functionality with complete field coverage"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Mock the GUI class methods we need
        self.mock_gui = Mock()
        self.mock_gui.settings = {'font_size': 20, 'dark_mode': False}
        self.mock_gui.actions_data = []
        
        # Import the GUI class
        from interfaces.gui import AutomationGUI
        self.gui_class = AutomationGUI
        
    def tearDown(self):
        """Clean up test environment"""
        self.root.destroy()
        
    def test_login_action_all_fields_present(self):
        """Test that LOGIN action Edit dialog has all required fields"""
        action_data = create_test_action_data()[ActionType.LOGIN]
        
        # Create mock GUI instance
        gui = self.gui_class(self.root)
        
        # Mock the field creation to track what fields are created
        created_fields = []
        original_create_fields = gui._create_action_fields
        
        def mock_create_fields(parent, action_type, field_vars, action_data=None):
            created_fields.append({
                'action_type': action_type,
                'field_vars_keys': list(field_vars.keys()) if field_vars else [],
                'has_action_data': action_data is not None
            })
            return original_create_fields(parent, action_type, field_vars, action_data)
        
        gui._create_action_fields = mock_create_fields
        
        # Test the edit dialog creation
        with patch.object(gui, '_apply_dialog_theme'), \
             patch.object(gui, '_center_dialog'), \
             patch('tkinter.messagebox.showinfo'):
            
            # Mock the dialog creation to avoid actual GUI display
            with patch('tkinter.Toplevel') as mock_toplevel:
                mock_dialog = Mock()
                mock_dialog.winfo_children.return_value = []
                mock_toplevel.return_value = mock_dialog
                
                # Test edit dialog with LOGIN action
                gui.actions_data = [action_data]
                
                # The method should create comprehensive fields for LOGIN
                field_vars = {}
                gui._create_action_fields(tk.Frame(self.root), ActionType.LOGIN, field_vars, action_data)
                
                # Verify all LOGIN fields are created
                expected_fields = ['description', 'username', 'password', 'username_selector', 
                                 'password_selector', 'submit_selector', 'timeout']
                
                for field in expected_fields:
                    self.assertIn(field, field_vars, 
                                f"LOGIN action missing field: {field}")
                
    def test_check_element_action_all_fields_present(self):
        """Test that CHECK_ELEMENT action Edit dialog has all required fields"""
        action_data = create_test_action_data()[ActionType.CHECK_ELEMENT]
        
        gui = self.gui_class(self.root)
        field_vars = {}
        gui._create_action_fields(tk.Frame(self.root), ActionType.CHECK_ELEMENT, field_vars, action_data)
        
        # Verify all CHECK_ELEMENT fields are created
        expected_fields = ['description', 'selector', 'check_type', 'expected_value', 
                          'attribute', 'timeout']
        
        for field in expected_fields:
            self.assertIn(field, field_vars, 
                        f"CHECK_ELEMENT action missing field: {field}")
                        
    def test_conditional_wait_action_all_fields_present(self):
        """Test that CONDITIONAL_WAIT action Edit dialog has all required fields"""
        action_data = create_test_action_data()[ActionType.CONDITIONAL_WAIT]
        
        gui = self.gui_class(self.root)
        field_vars = {}
        gui._create_action_fields(tk.Frame(self.root), ActionType.CONDITIONAL_WAIT, field_vars, action_data)
        
        # Verify all CONDITIONAL_WAIT fields are created
        expected_fields = ['description', 'condition', 'wait_time', 'max_retries', 
                          'retry_delay', 'timeout']
        
        for field in expected_fields:
            self.assertIn(field, field_vars, 
                        f"CONDITIONAL_WAIT action missing field: {field}")
                        
    def test_skip_if_action_all_fields_present(self):
        """Test that SKIP_IF action Edit dialog has all required fields"""
        action_data = create_test_action_data()[ActionType.SKIP_IF]
        
        gui = self.gui_class(self.root)
        field_vars = {}
        gui._create_action_fields(tk.Frame(self.root), ActionType.SKIP_IF, field_vars, action_data)
        
        # Verify all SKIP_IF fields are created
        expected_fields = ['description', 'condition', 'skip_count', 'reason', 'timeout']
        
        for field in expected_fields:
            self.assertIn(field, field_vars, 
                        f"SKIP_IF action missing field: {field}")
                        
    def test_upload_image_action_all_fields_present(self):
        """Test that UPLOAD_IMAGE action Edit dialog has all required fields"""
        action_data = create_test_action_data()[ActionType.UPLOAD_IMAGE]
        
        gui = self.gui_class(self.root)
        field_vars = {}
        gui._create_action_fields(tk.Frame(self.root), ActionType.UPLOAD_IMAGE, field_vars, action_data)
        
        # Verify all UPLOAD_IMAGE fields are created
        expected_fields = ['description', 'selector', 'file_path', 'timeout']
        
        for field in expected_fields:
            self.assertIn(field, field_vars, 
                        f"UPLOAD_IMAGE action missing field: {field}")
                        
    def test_field_data_population(self):
        """Test that existing action data properly populates edit fields"""
        test_data = create_test_action_data()
        
        for action_type, action_data in test_data.items():
            with self.subTest(action_type=action_type):
                gui = self.gui_class(self.root)
                field_vars = {}
                gui._create_action_fields(tk.Frame(self.root), action_type, field_vars, action_data)
                
                # Verify description is populated
                if 'description' in field_vars:
                    self.assertEqual(field_vars['description'].get(), action_data['description'])
                
                # Verify complex value fields are populated for specific action types
                if action_type == ActionType.LOGIN and 'username' in field_vars:
                    self.assertEqual(field_vars['username'].get(), 
                                   action_data['value']['username'])
                
                if action_type == ActionType.CHECK_ELEMENT and 'expected_value' in field_vars:
                    self.assertEqual(field_vars['expected_value'].get(), 
                                   action_data['value']['value'])
                                   
    def test_collect_action_data_comprehensive(self):
        """Test that _collect_action_data works with all field types"""
        gui = self.gui_class(self.root)
        
        # Test LOGIN action data collection
        field_vars = {
            'description': tk.StringVar(value='Test login'),
            'username': tk.StringVar(value='testuser'),
            'password': tk.StringVar(value='testpass'),
            'username_selector': tk.StringVar(value='#username'),
            'password_selector': tk.StringVar(value='#password'),
            'submit_selector': tk.StringVar(value='#submit'),
            'timeout': tk.StringVar(value='5000')
        }
        
        collected_data = gui._collect_action_data(ActionType.LOGIN, field_vars)
        
        self.assertEqual(collected_data['type'], ActionType.LOGIN)
        self.assertEqual(collected_data['description'], 'Test login')
        self.assertEqual(collected_data['value']['username'], 'testuser')
        self.assertEqual(collected_data['value']['password'], 'testpass')
        self.assertEqual(collected_data['timeout'], 5000)
        
    def test_edit_dialog_saves_correctly(self):
        """Test that edit dialog saves all data correctly"""
        action_data = create_test_action_data()[ActionType.LOGIN]
        
        gui = self.gui_class(self.root)
        gui.actions_data = [action_data]
        
        # Mock the update display method
        updated_data = None
        def mock_update_display(index, data):
            nonlocal updated_data
            updated_data = data
            
        gui._update_action_display = mock_update_display
        
        # Simulate editing the action
        with patch.object(gui, '_apply_dialog_theme'), \
             patch.object(gui, '_center_dialog'), \
             patch('tkinter.messagebox.showinfo'):
            
            # Create field vars with modified data
            field_vars = {
                'description': tk.StringVar(value='Modified login'),
                'username': tk.StringVar(value='newuser'),
                'password': tk.StringVar(value='newpass'),
                'username_selector': tk.StringVar(value='#new-username'),
                'password_selector': tk.StringVar(value='#new-password'),
                'submit_selector': tk.StringVar(value='#new-submit'),
                'timeout': tk.StringVar(value='7000')
            }
            
            # Collect the modified data
            modified_data = gui._collect_action_data(ActionType.LOGIN, field_vars)
            
            # Update the action
            gui.actions_data[0] = modified_data
            mock_update_display(0, modified_data)
            
            # Verify the data was updated correctly
            self.assertEqual(updated_data['description'], 'Modified login')
            self.assertEqual(updated_data['value']['username'], 'newuser')
            self.assertEqual(updated_data['timeout'], 7000)

class TestEditActionFieldParity(unittest.TestCase):
    """Test that Edit Action has complete field parity with Add Action"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()
        
    def tearDown(self):
        """Clean up test environment"""
        self.root.destroy()
        
    def test_all_action_types_have_field_parity(self):
        """Test that all action types have the same fields in Add and Edit dialogs"""
        from interfaces.gui import AutomationGUI
        
        gui = AutomationGUI(self.root)
        test_data = create_test_action_data()
        
        for action_type in ActionType:
            with self.subTest(action_type=action_type):
                # Create fields for Add Action (new action)
                add_field_vars = {}
                gui._create_action_fields(tk.Frame(self.root), action_type, add_field_vars, None)
                
                # Create fields for Edit Action (existing action)
                edit_field_vars = {}
                action_data = test_data.get(action_type, {
                    'type': action_type,
                    'description': 'Test action',
                    'selector': None,
                    'value': None,
                    'timeout': 2000
                })
                gui._create_action_fields(tk.Frame(self.root), action_type, edit_field_vars, action_data)
                
                # Compare field sets
                add_fields = set(add_field_vars.keys())
                edit_fields = set(edit_field_vars.keys())
                
                self.assertEqual(add_fields, edit_fields, 
                               f"Field parity mismatch for {action_type}: "
                               f"Add fields: {add_fields}, Edit fields: {edit_fields}")

def run_tests():
    """Run all Edit Action tests"""
    print("🧪 Running Comprehensive Edit Action Tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTest(unittest.makeSuite(TestEditActionComprehensive))
    suite.addTest(unittest.makeSuite(TestEditActionFieldParity))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Test Results Summary:")
    print(f"✅ Tests Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests Failed: {len(result.failures)}")
    print(f"🚨 Test Errors: {len(result.errors)}")
    print(f"📈 Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
            
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)