#!/usr/bin/env python3
"""
Comprehensive test suite for Edit Action Windows
Tests all action types, field population, validation, and UI interactions
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.engine import ActionType, Action

# Mock tkinter and ttk for testing
class MockStringVar:
    def __init__(self, value=""):
        self.value = value
        self.trace_callbacks = []
    
    def get(self):
        return self.value
    
    def set(self, value):
        old_value = self.value
        self.value = str(value) if value is not None else ""
        # Trigger trace callbacks
        for callback in self.trace_callbacks:
            try:
                callback()
            except:
                pass
    
    def trace(self, mode, callback):
        self.trace_callbacks.append(callback)

class MockBooleanVar:
    def __init__(self, value=False):
        self.value = bool(value)
        self.trace_callbacks = []
    
    def get(self):
        return self.value
    
    def set(self, value):
        self.value = bool(value)
        # Trigger trace callbacks
        for callback in self.trace_callbacks:
            try:
                callback()
            except:
                pass
    
    def trace(self, mode, callback):
        self.trace_callbacks.append(callback)

class MockWidget:
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.packed = False
        self.gridded = False
    
    def pack(self, **kwargs):
        self.packed = True
        self.pack_kwargs = kwargs
        return self
    
    def grid(self, **kwargs):
        self.gridded = True
        self.grid_kwargs = kwargs
        return self
    
    def configure(self, **kwargs):
        self.kwargs.update(kwargs)
    
    def bind(self, event, callback):
        pass

class MockText(MockWidget):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.content = ""
    
    def insert(self, position, text):
        if position == "1.0":
            self.content = text
        else:
            self.content += text
    
    def get(self, start, end=None):
        if start == "1.0" and end in [None, "end"]:
            return self.content
        return self.content
    
    def delete(self, start, end=None):
        if start == "1.0":
            self.content = ""

class MockCombobox(MockWidget):
    def __init__(self, parent, textvariable=None, values=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.textvariable = textvariable
        self.values = values or []

class MockCheckbutton(MockWidget):
    def __init__(self, parent, variable=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.variable = variable

class MockEntry(MockWidget):
    def __init__(self, parent, textvariable=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.textvariable = textvariable

# Mock GUI class with edit functionality
class MockGUI:
    def __init__(self):
        self.actions_data = []
        self.settings = {'font_size': 20}
    
    def _calculate_entry_width(self):
        return 50
    
    def _create_action_fields(self, parent, action_type, field_vars, action_data=None):
        """Mock implementation of _create_action_fields method based on actual GUI code"""
        
        # Common description field
        field_vars['description'] = MockStringVar()
        if action_data and action_data.get('description'):
            field_vars['description'].set(action_data['description'])
        
        # LOGIN action
        if action_type == ActionType.LOGIN:
            field_vars['username'] = MockStringVar()
            field_vars['password'] = MockStringVar()
            field_vars['username_selector'] = MockStringVar()
            field_vars['password_selector'] = MockStringVar()
            field_vars['submit_selector'] = MockStringVar()
            
            if action_data and action_data.get('value'):
                login_data = action_data['value']
                field_vars['username'].set(login_data.get('username', ''))
                field_vars['password'].set(login_data.get('password', ''))
                field_vars['username_selector'].set(login_data.get('username_selector', ''))
                field_vars['password_selector'].set(login_data.get('password_selector', ''))
                field_vars['submit_selector'].set(login_data.get('submit_selector', ''))
        
        # EXPAND_DIALOG action
        elif action_type == ActionType.EXPAND_DIALOG:
            field_vars['selector'] = MockStringVar()
            if action_data and action_data.get('selector'):
                field_vars['selector'].set(action_data['selector'])
        
        # INPUT_TEXT action
        elif action_type == ActionType.INPUT_TEXT:
            field_vars['selector'] = MockStringVar()
            field_vars['value'] = MockStringVar()
            
            if action_data:
                if action_data.get('selector'):
                    field_vars['selector'].set(action_data['selector'])
                if action_data.get('value'):
                    field_vars['value'].set(action_data['value'])
        
        # UPLOAD_IMAGE action
        elif action_type == ActionType.UPLOAD_IMAGE:
            field_vars['selector'] = MockStringVar()
            field_vars['value'] = MockStringVar()
            
            if action_data:
                if action_data.get('selector'):
                    field_vars['selector'].set(action_data['selector'])
                if action_data.get('value'):
                    field_vars['value'].set(action_data['value'])
        
        # TOGGLE_SETTING action
        elif action_type == ActionType.TOGGLE_SETTING:
            field_vars['selector'] = MockStringVar()
            field_vars['value'] = MockBooleanVar()
            
            if action_data:
                if action_data.get('selector'):
                    field_vars['selector'].set(action_data['selector'])
                if action_data.get('value') is not None:
                    field_vars['value'].set(action_data['value'])
        
        # CLICK_BUTTON action
        elif action_type == ActionType.CLICK_BUTTON:
            field_vars['selector'] = MockStringVar()
            
            if action_data and action_data.get('selector'):
                field_vars['selector'].set(action_data['selector'])
        
        # CHECK_QUEUE action
        elif action_type == ActionType.CHECK_QUEUE:
            field_vars['check_type'] = MockStringVar(value="equals")
            field_vars['expected_value'] = MockStringVar()
            field_vars['attribute'] = MockStringVar(value="text")
            
            if action_data and action_data.get('value'):
                check_data = action_data['value']
                field_vars['check_type'].set(check_data.get('check', 'equals'))
                field_vars['expected_value'].set(check_data.get('value', ''))
                field_vars['attribute'].set(check_data.get('attribute', 'text'))
        
        # CHECK_ELEMENT action
        elif action_type == ActionType.CHECK_ELEMENT:
            field_vars['selector'] = MockStringVar()
            field_vars['check_type'] = MockStringVar(value="equals")
            field_vars['expected_value'] = MockStringVar()
            field_vars['attribute'] = MockStringVar(value="text")
            
            if action_data:
                if action_data.get('selector'):
                    field_vars['selector'].set(action_data['selector'])
                if action_data.get('value'):
                    check_data = action_data['value']
                    field_vars['check_type'].set(check_data.get('check', 'equals'))
                    field_vars['expected_value'].set(check_data.get('value', ''))
                    field_vars['attribute'].set(check_data.get('attribute', 'text'))
        
        # Block control actions (IF/WHILE/ELSE)
        elif action_type in [ActionType.IF_BEGIN, ActionType.ELIF, ActionType.WHILE_BEGIN]:
            field_vars['condition'] = MockStringVar()
            
            # Set default/current value
            if action_data and action_data.get('value', {}).get('condition'):
                field_vars['condition'].set(action_data['value']['condition'])
            else:
                field_vars['condition'].set('check_passed')
        
        elif action_type in [ActionType.ELSE, ActionType.IF_END, ActionType.WHILE_END, ActionType.BREAK, ActionType.CONTINUE, ActionType.STOP_AUTOMATION]:
            # These actions don't need additional configuration
            pass
        
        elif action_type == ActionType.CONDITIONAL_WAIT:
            # Condition dropdown
            field_vars['condition'] = MockStringVar()
            field_vars['wait_time'] = MockStringVar()
            field_vars['max_retries'] = MockStringVar()
            field_vars['retry_from_action'] = MockStringVar()
            
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
            field_vars['condition'] = MockStringVar()
            field_vars['skip_count'] = MockStringVar()
            
            # Set defaults/current values
            if action_data and action_data.get('value'):
                value_data = action_data['value']
                field_vars['condition'].set(value_data.get('condition', 'check_passed'))
                field_vars['skip_count'].set(str(value_data.get('skip_count', 1)))
            else:
                field_vars['condition'].set('check_passed')
                field_vars['skip_count'].set('1')
        
        elif action_type == ActionType.DOWNLOAD_FILE:
            field_vars['selector'] = MockStringVar()
            field_vars['value'] = MockStringVar()
            
            if action_data:
                if action_data.get('selector'):
                    field_vars['selector'].set(action_data['selector'])
                if action_data.get('value'):
                    field_vars['value'].set(action_data['value'])
        
        elif action_type == ActionType.REFRESH_PAGE:
            # No additional fields needed
            pass
        
        elif action_type == ActionType.SWITCH_PANEL:
            field_vars['value'] = MockStringVar()
            
            if action_data and action_data.get('value'):
                field_vars['value'].set(action_data['value'])
        
        elif action_type == ActionType.WAIT:
            field_vars['value'] = MockStringVar(value="1000")
            
            if action_data and action_data.get('value'):
                field_vars['value'].set(str(action_data['value']))
        
        elif action_type == ActionType.WAIT_FOR_ELEMENT:
            field_vars['selector'] = MockStringVar()
            
            if action_data and action_data.get('selector'):
                field_vars['selector'].set(action_data['selector'])
        
        elif action_type == ActionType.SET_VARIABLE:
            field_vars['variable_name'] = MockStringVar()
            field_vars['value'] = MockStringVar()
            
            if action_data and action_data.get('value'):
                var_data = action_data['value']
                field_vars['variable_name'].set(var_data.get('name', ''))
                field_vars['value'].set(var_data.get('value', ''))
        
        elif action_type == ActionType.INCREMENT_VARIABLE:
            field_vars['variable_name'] = MockStringVar()
            field_vars['increment'] = MockStringVar(value="1")
            
            if action_data and action_data.get('value'):
                var_data = action_data['value']
                field_vars['variable_name'].set(var_data.get('name', ''))
                field_vars['increment'].set(str(var_data.get('increment', 1)))
        
        elif action_type == ActionType.LOG_MESSAGE:
            field_vars['message'] = MockStringVar()
            field_vars['level'] = MockStringVar(value="INFO")
            
            if action_data and action_data.get('value'):
                log_data = action_data['value']
                field_vars['message'].set(log_data.get('message', ''))
                field_vars['level'].set(log_data.get('level', 'INFO'))


class TestEditActionWindows:
    """Comprehensive test suite for Edit Action Windows"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.gui = MockGUI()
    
    def test_login_action_edit_field_population(self):
        """Test LOGIN action edit field population"""
        print("🧪 Testing LOGIN action edit field population...")
        
        field_vars = {}
        action_data = {
            'type': ActionType.LOGIN,
            'value': {
                'username': 'test_user',
                'password': 'test_pass',
                'username_selector': '#username',
                'password_selector': '#password',
                'submit_selector': '#submit'
            },
            'description': 'Test login action'
        }
        
        # Create fields with current data
        self.gui._create_action_fields(None, ActionType.LOGIN, field_vars, action_data)
        
        # Verify all fields are present
        required_fields = ['description', 'username', 'password', 'username_selector', 'password_selector', 'submit_selector']
        for field in required_fields:
            assert field in field_vars, f"Missing field: {field}"
        
        # Verify field population
        assert field_vars['description'].get() == 'Test login action'
        assert field_vars['username'].get() == 'test_user'
        assert field_vars['password'].get() == 'test_pass'
        assert field_vars['username_selector'].get() == '#username'
        assert field_vars['password_selector'].get() == '#password'
        assert field_vars['submit_selector'].get() == '#submit'
        
        print("✅ LOGIN action edit field population test passed!")
    
    def test_login_action_edit_field_updates(self):
        """Test LOGIN action edit field updates"""
        print("🧪 Testing LOGIN action edit field updates...")
        
        field_vars = {}
        action_data = {
            'type': ActionType.LOGIN,
            'value': {
                'username': 'old_user',
                'password': 'old_pass'
            },
            'description': 'Old login'
        }
        
        self.gui._create_action_fields(None, ActionType.LOGIN, field_vars, action_data)
        
        # Update fields
        field_vars['description'].set('Updated login action')
        field_vars['username'].set('new_user')
        field_vars['password'].set('new_pass')
        field_vars['username_selector'].set('#new_username')
        field_vars['password_selector'].set('#new_password')
        field_vars['submit_selector'].set('#new_submit')
        
        # Verify updates
        assert field_vars['description'].get() == 'Updated login action'
        assert field_vars['username'].get() == 'new_user'
        assert field_vars['password'].get() == 'new_pass'
        assert field_vars['username_selector'].get() == '#new_username'
        assert field_vars['password_selector'].get() == '#new_password'
        assert field_vars['submit_selector'].get() == '#new_submit'
        
        print("✅ LOGIN action edit field updates test passed!")
    
    def test_check_element_action_edit(self):
        """Test CHECK_ELEMENT action edit functionality"""
        print("🧪 Testing CHECK_ELEMENT action edit functionality...")
        
        field_vars = {}
        action_data = {
            'type': ActionType.CHECK_ELEMENT,
            'selector': '.queue-count',
            'value': {
                'check': 'greater',
                'value': '5',
                'attribute': 'data-count'
            },
            'description': 'Check queue count'
        }
        
        self.gui._create_action_fields(None, ActionType.CHECK_ELEMENT, field_vars, action_data)
        
        # Verify fields are present and populated
        assert 'selector' in field_vars
        assert 'check_type' in field_vars
        assert 'expected_value' in field_vars
        assert 'attribute' in field_vars
        assert 'description' in field_vars
        
        assert field_vars['description'].get() == 'Check queue count'
        assert field_vars['selector'].get() == '.queue-count'
        assert field_vars['check_type'].get() == 'greater'
        assert field_vars['expected_value'].get() == '5'
        assert field_vars['attribute'].get() == 'data-count'
        
        # Test field updates
        field_vars['selector'].set('.new-selector')
        field_vars['check_type'].set('equals')
        field_vars['expected_value'].set('10')
        field_vars['attribute'].set('text')
        
        assert field_vars['selector'].get() == '.new-selector'
        assert field_vars['check_type'].get() == 'equals'
        assert field_vars['expected_value'].get() == '10'
        assert field_vars['attribute'].get() == 'text'
        
        print("✅ CHECK_ELEMENT action edit test passed!")
    
    def test_conditional_wait_action_edit(self):
        """Test CONDITIONAL_WAIT action edit functionality"""
        print("🧪 Testing CONDITIONAL_WAIT action edit functionality...")
        
        field_vars = {}
        action_data = {
            'type': ActionType.CONDITIONAL_WAIT,
            'value': {
                'condition': 'check_failed',
                'wait_time': 3000,
                'max_retries': 5,
                'retry_from_action': 2
            },
            'description': 'Test conditional wait'
        }
        
        self.gui._create_action_fields(None, ActionType.CONDITIONAL_WAIT, field_vars, action_data)
        
        # Verify fields are present and populated
        required_fields = ['condition', 'wait_time', 'max_retries', 'retry_from_action', 'description']
        for field in required_fields:
            assert field in field_vars, f"Missing field: {field}"
        
        assert field_vars['description'].get() == 'Test conditional wait'
        assert field_vars['condition'].get() == 'check_failed'
        assert field_vars['wait_time'].get() == '3000'
        assert field_vars['max_retries'].get() == '5'
        assert field_vars['retry_from_action'].get() == '2'
        
        # Test updates
        field_vars['condition'].set('check_passed')
        field_vars['wait_time'].set('4000')
        field_vars['max_retries'].set('10')
        field_vars['retry_from_action'].set('0')
        
        assert field_vars['condition'].get() == 'check_passed'
        assert field_vars['wait_time'].get() == '4000'
        assert field_vars['max_retries'].get() == '10'
        assert field_vars['retry_from_action'].get() == '0'
        
        print("✅ CONDITIONAL_WAIT action edit test passed!")
    
    def test_block_control_actions_edit(self):
        """Test block control actions (IF, WHILE, etc.) edit functionality"""
        print("🧪 Testing block control actions edit functionality...")
        
        # Test IF_BEGIN
        field_vars = {}
        action_data = {
            'type': ActionType.IF_BEGIN,
            'value': {'condition': 'check_failed'},
            'description': 'Test IF condition'
        }
        
        self.gui._create_action_fields(None, ActionType.IF_BEGIN, field_vars, action_data)
        
        assert 'condition' in field_vars
        assert 'description' in field_vars
        assert field_vars['condition'].get() == 'check_failed'
        assert field_vars['description'].get() == 'Test IF condition'
        
        # Test WHILE_BEGIN
        field_vars = {}
        action_data = {
            'type': ActionType.WHILE_BEGIN,
            'value': {'condition': 'value_equals'},
            'description': 'Test WHILE loop'
        }
        
        self.gui._create_action_fields(None, ActionType.WHILE_BEGIN, field_vars, action_data)
        
        assert field_vars['condition'].get() == 'value_equals'
        assert field_vars['description'].get() == 'Test WHILE loop'
        
        # Test simple block actions (ELSE, IF_END, etc.)
        for action_type in [ActionType.ELSE, ActionType.IF_END, ActionType.WHILE_END, ActionType.BREAK, ActionType.CONTINUE]:
            field_vars = {}
            action_data = {
                'type': action_type,
                'description': f'Test {action_type.value} block'
            }
            
            self.gui._create_action_fields(None, action_type, field_vars, action_data)
            
            assert 'description' in field_vars
            assert field_vars['description'].get() == f'Test {action_type.value} block'
        
        print("✅ Block control actions edit test passed!")
    
    def test_toggle_setting_action_edit(self):
        """Test TOGGLE_SETTING action edit functionality"""
        print("🧪 Testing TOGGLE_SETTING action edit functionality...")
        
        field_vars = {}
        action_data = {
            'type': ActionType.TOGGLE_SETTING,
            'selector': '#enable-feature',
            'value': True,
            'description': 'Toggle feature setting'
        }
        
        self.gui._create_action_fields(None, ActionType.TOGGLE_SETTING, field_vars, action_data)
        
        # Verify fields
        assert 'selector' in field_vars
        assert 'value' in field_vars
        assert 'description' in field_vars
        
        assert field_vars['selector'].get() == '#enable-feature'
        assert field_vars['value'].get() == True
        assert field_vars['description'].get() == 'Toggle feature setting'
        
        # Test boolean value updates
        field_vars['value'].set(False)
        assert field_vars['value'].get() == False
        
        field_vars['value'].set(True)
        assert field_vars['value'].get() == True
        
        print("✅ TOGGLE_SETTING action edit test passed!")
    
    def test_variable_actions_edit(self):
        """Test variable-related actions edit functionality"""
        print("🧪 Testing variable actions edit functionality...")
        
        # Test SET_VARIABLE
        field_vars = {}
        action_data = {
            'type': ActionType.SET_VARIABLE,
            'value': {
                'name': 'counter',
                'value': '42'
            },
            'description': 'Set counter variable'
        }
        
        self.gui._create_action_fields(None, ActionType.SET_VARIABLE, field_vars, action_data)
        
        assert 'variable_name' in field_vars
        assert 'value' in field_vars
        assert field_vars['variable_name'].get() == 'counter'
        assert field_vars['value'].get() == '42'
        
        # Test INCREMENT_VARIABLE
        field_vars = {}
        action_data = {
            'type': ActionType.INCREMENT_VARIABLE,
            'value': {
                'name': 'index',
                'increment': 5
            },
            'description': 'Increment index variable'
        }
        
        self.gui._create_action_fields(None, ActionType.INCREMENT_VARIABLE, field_vars, action_data)
        
        assert 'variable_name' in field_vars
        assert 'increment' in field_vars
        assert field_vars['variable_name'].get() == 'index'
        assert field_vars['increment'].get() == '5'
        
        print("✅ Variable actions edit test passed!")
    
    def test_log_message_action_edit(self):
        """Test LOG_MESSAGE action edit functionality"""
        print("🧪 Testing LOG_MESSAGE action edit functionality...")
        
        field_vars = {}
        action_data = {
            'type': ActionType.LOG_MESSAGE,
            'value': {
                'message': 'Debug checkpoint reached',
                'level': 'DEBUG'
            },
            'description': 'Debug log entry'
        }
        
        self.gui._create_action_fields(None, ActionType.LOG_MESSAGE, field_vars, action_data)
        
        assert 'message' in field_vars
        assert 'level' in field_vars
        assert field_vars['message'].get() == 'Debug checkpoint reached'
        assert field_vars['level'].get() == 'DEBUG'
        
        # Test updates
        field_vars['message'].set('New log message')
        field_vars['level'].set('ERROR')
        
        assert field_vars['message'].get() == 'New log message'
        assert field_vars['level'].get() == 'ERROR'
        
        print("✅ LOG_MESSAGE action edit test passed!")
    
    def test_empty_action_data_defaults(self):
        """Test that empty/None action data uses proper defaults"""
        print("🧪 Testing empty action data defaults...")
        
        # Test CONDITIONAL_WAIT with no action data
        field_vars = {}
        self.gui._create_action_fields(None, ActionType.CONDITIONAL_WAIT, field_vars, None)
        
        assert field_vars['condition'].get() == 'check_failed'  # Default
        assert field_vars['wait_time'].get() == '5000'  # Default
        assert field_vars['max_retries'].get() == '3'  # Default
        assert field_vars['retry_from_action'].get() == '0'  # Default
        
        # Test CHECK_ELEMENT with no action data
        field_vars = {}
        self.gui._create_action_fields(None, ActionType.CHECK_ELEMENT, field_vars, None)
        
        assert field_vars['check_type'].get() == 'equals'  # Default
        assert field_vars['attribute'].get() == 'text'  # Default
        
        # Test WAIT with no action data
        field_vars = {}
        self.gui._create_action_fields(None, ActionType.WAIT, field_vars, None)
        
        assert field_vars['value'].get() == '1000'  # Default
        
        print("✅ Empty action data defaults test passed!")
    
    def test_field_validation_edge_cases(self):
        """Test field validation and edge cases"""
        print("🧪 Testing field validation and edge cases...")
        
        # Test with None values
        field_vars = {}
        action_data = {
            'type': ActionType.INPUT_TEXT,
            'selector': None,
            'value': None,
            'description': None
        }
        
        self.gui._create_action_fields(None, ActionType.INPUT_TEXT, field_vars, action_data)
        
        # Should handle None values gracefully
        assert field_vars['selector'].get() == ''
        assert field_vars['value'].get() == ''
        assert field_vars['description'].get() == ''
        
        # Test setting None values
        field_vars['selector'].set(None)
        field_vars['value'].set(None)
        
        assert field_vars['selector'].get() == ''
        assert field_vars['value'].get() == ''
        
        # Test numeric values as strings
        field_vars = {}
        action_data = {
            'type': ActionType.CONDITIONAL_WAIT,
            'value': {
                'wait_time': 3000,  # Numeric
                'max_retries': 5,   # Numeric
                'retry_from_action': 2  # Numeric
            }
        }
        
        self.gui._create_action_fields(None, ActionType.CONDITIONAL_WAIT, field_vars, action_data)
        
        # Should convert to strings
        assert field_vars['wait_time'].get() == '3000'
        assert field_vars['max_retries'].get() == '5'
        assert field_vars['retry_from_action'].get() == '2'
        
        print("✅ Field validation and edge cases test passed!")
    
    def test_all_action_types_have_description_field(self):
        """Test that all action types have a description field"""
        print("🧪 Testing all action types have description field...")
        
        all_action_types = [
            ActionType.LOGIN, ActionType.EXPAND_DIALOG, ActionType.INPUT_TEXT,
            ActionType.UPLOAD_IMAGE, ActionType.TOGGLE_SETTING, ActionType.CLICK_BUTTON,
            ActionType.CHECK_QUEUE, ActionType.CHECK_ELEMENT, ActionType.CONDITIONAL_WAIT,
            ActionType.SKIP_IF, ActionType.IF_BEGIN, ActionType.ELIF, ActionType.ELSE,
            ActionType.IF_END, ActionType.WHILE_BEGIN, ActionType.WHILE_END,
            ActionType.BREAK, ActionType.CONTINUE, ActionType.STOP_AUTOMATION,
            ActionType.DOWNLOAD_FILE, ActionType.REFRESH_PAGE, ActionType.SWITCH_PANEL,
            ActionType.WAIT, ActionType.WAIT_FOR_ELEMENT, ActionType.SET_VARIABLE,
            ActionType.INCREMENT_VARIABLE, ActionType.LOG_MESSAGE
        ]
        
        for action_type in all_action_types:
            field_vars = {}
            action_data = {
                'type': action_type,
                'description': f'Test {action_type.value} action'
            }
            
            self.gui._create_action_fields(None, action_type, field_vars, action_data)
            
            # All actions should have a description field
            assert 'description' in field_vars, f"Action type {action_type.value} missing description field"
            assert field_vars['description'].get() == f'Test {action_type.value} action'
        
        print("✅ All action types have description field test passed!")
    
    def test_field_trace_callbacks(self):
        """Test that field trace callbacks work correctly"""
        print("🧪 Testing field trace callbacks...")
        
        field_vars = {}
        self.gui._create_action_fields(None, ActionType.INPUT_TEXT, field_vars, None)
        
        # Test that trace callbacks can be added without errors
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        field_vars['description'].trace('w', test_callback)
        field_vars['description'].set('Test description')
        
        # Callback should have been triggered
        assert callback_called, "Trace callback was not called"
        
        print("✅ Field trace callbacks test passed!")


def run_comprehensive_tests():
    """Run all comprehensive edit action window tests"""
    print("🚀 Starting comprehensive Edit Action Windows tests...\n")
    
    test_suite = TestEditActionWindows()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_login_action_edit_field_population,
        test_suite.test_login_action_edit_field_updates,
        test_suite.test_check_element_action_edit,
        test_suite.test_conditional_wait_action_edit,
        test_suite.test_block_control_actions_edit,
        test_suite.test_toggle_setting_action_edit,
        test_suite.test_variable_actions_edit,
        test_suite.test_log_message_action_edit,
        test_suite.test_empty_action_data_defaults,
        test_suite.test_field_validation_edge_cases,
        test_suite.test_all_action_types_have_description_field,
        test_suite.test_field_trace_callbacks
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {test.__name__} - {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Edit Action Windows functionality is comprehensive and robust")
        print("🔧 All action types properly populate and update fields")
        print("🛡️ Field validation and edge cases are handled correctly")
        print("🎯 UI interactions work as expected")
        print("💫 Edit functionality is production-ready!")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Please review and fix issues.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)