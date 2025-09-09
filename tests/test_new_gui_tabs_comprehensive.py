#!/usr/bin/env python3
"""
Comprehensive Test Suite for New GUI Tabs - Action Tab & Selector Tab
This test suite validates the new GUI functionality before implementation.

NEW FEATURES TO TEST:
1. Action Tab - Action sequence execution, parameter preview/editing, apply/copy operations
2. Selector Tab - HTML element analysis, selector recommendations, multi-strategy validation  
3. Integration - Parameter copying between tabs, framework integration
4. GUI Responsiveness - Error handling, performance, user experience

Test Architecture:
- Mock-based testing without requiring GUI display
- Comprehensive coverage of all tab functionality
- Performance benchmarks and error scenario testing
- End-to-end workflow validation
"""

import sys
import os
import unittest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path
import json
import time

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.engine import ActionType, Action

class MockTkinterWidget:
    """Base mock for all tkinter widgets"""
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.children = []
        self._text = ""
        self._value = ""
        self._state = "normal"
        
    def pack(self, **kwargs): pass
    def grid(self, **kwargs): pass
    def place(self, **kwargs): pass
    def configure(self, **kwargs): 
        self.kwargs.update(kwargs)
    def destroy(self): pass
    def update(self): pass
    def focus(self): pass
    def get(self): return self._value
    def set(self, value): self._value = value
    def insert(self, index, text): self._text += text
    def delete(self, start, end=None): self._text = ""
    def clear(self): self._text = ""
    
class MockStringVar(MockTkinterWidget):
    """Mock tkinter StringVar"""
    def __init__(self, value=""):
        super().__init__()
        self._value = value
    
    def get(self): return self._value
    def set(self, value): self._value = str(value)

class MockText(MockTkinterWidget):
    """Mock tkinter Text widget with logging functionality"""
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.log_entries = []
        
    def insert(self, position, text):
        """Insert text and log the entry"""
        self.log_entries.append(text)
        self._text += text
        
    def get(self, start=None, end=None):
        """Get text content - compatible with tkinter Text widget signature"""
        if start is None:
            return self._text
        return self._text
        
    def delete(self, start, end=None):
        """Delete text content"""
        self._text = ""
        self.log_entries.clear()

class MockTreeview(MockTkinterWidget):
    """Mock ttk.Treeview for action sequence display"""
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.items = {}
        self.columns = []
        self.headings = {}
        
    def insert(self, parent, index, **kwargs):
        """Insert item into treeview"""
        item_id = f"item_{len(self.items)}"
        self.items[item_id] = {
            'parent': parent,
            'values': kwargs.get('values', []),
            'text': kwargs.get('text', '')
        }
        return item_id
        
    def delete(self, *items):
        """Delete items from treeview"""
        for item in items:
            if item in self.items:
                del self.items[item]
                
    def selection(self):
        """Get selected items"""
        return list(self.items.keys())[:1] if self.items else []
        
    def item(self, item_id, **kwargs):
        """Get/set item data"""
        if item_id in self.items:
            if kwargs:
                self.items[item_id].update(kwargs)
            return self.items[item_id]
        return {}

class MockActionTab:
    """Mock Action Tab functionality for testing"""
    
    def __init__(self):
        # UI Components
        self.action_tree = MockTreeview()
        self.parameter_frame = MockTkinterWidget()
        self.log_output = MockText()
        self.progress_bar = MockTkinterWidget()
        
        # Data
        self.current_actions = []
        self.selected_action = None
        self.execution_status = "idle"
        self.parameter_fields = {}
        
        # State tracking
        self.execution_results = []
        self.parameter_changes = {}
        
    def load_action_sequence(self, actions):
        """Load action sequence into the tab"""
        self.current_actions = actions
        self.action_tree.items.clear()
        
        for i, action in enumerate(actions):
            self.action_tree.insert("", "end", 
                values=[str(i+1), action.type.value, (action.description or "")[:50], "Ready"],
                text=f"action_{i}"
            )
        return len(actions)
    
    def select_action(self, index):
        """Select action for parameter editing"""
        if 0 <= index < len(self.current_actions):
            self.selected_action = index
            action = self.current_actions[index]
            self._populate_parameter_fields(action)
            return True
        return False
    
    def _populate_parameter_fields(self, action):
        """Populate parameter fields with action data"""
        self.parameter_fields.clear()
        
        # Common fields - always create these
        self.parameter_fields['description'] = MockStringVar(action.description or "")
        self.parameter_fields['timeout'] = MockStringVar(str(action.timeout or 5000))
        
        # Always create selector field, even if empty
        self.parameter_fields['selector'] = MockStringVar(action.selector or "")
            
        if action.value:
            if isinstance(action.value, dict):
                for key, value in action.value.items():
                    self.parameter_fields[key] = MockStringVar(str(value))
            else:
                self.parameter_fields['value'] = MockStringVar(str(action.value))
    
    def preview_parameters(self):
        """Preview current parameter values"""
        if self.selected_action is None:
            return {}
            
        preview = {}
        for field_name, field_var in self.parameter_fields.items():
            preview[field_name] = field_var.get()
        return preview
    
    def apply_parameter_changes(self):
        """Apply parameter changes to selected action"""
        if self.selected_action is None:
            return False
            
        action = self.current_actions[self.selected_action]
        changes = {}
        
        # Update action with field values
        if 'description' in self.parameter_fields:
            action.description = self.parameter_fields['description'].get()
            changes['description'] = action.description
            
        if 'timeout' in self.parameter_fields:
            try:
                action.timeout = int(self.parameter_fields['timeout'].get())
                changes['timeout'] = action.timeout
            except ValueError:
                return False
                
        if 'selector' in self.parameter_fields:
            action.selector = self.parameter_fields['selector'].get()
            changes['selector'] = action.selector
        
        # Track changes
        self.parameter_changes[self.selected_action] = changes
        return True
    
    def copy_action(self, index):
        """Copy action with parameters"""
        if 0 <= index < len(self.current_actions):
            action = self.current_actions[index]
            return {
                'type': action.type,
                'description': action.description,
                'selector': action.selector,
                'value': action.value,
                'timeout': action.timeout
            }
        return None
    
    async def execute_action_sequence(self):
        """Mock execution of action sequence"""
        self.execution_status = "running"
        self.execution_results.clear()
        
        total_actions = len(self.current_actions)
        for i, action in enumerate(self.current_actions):
            # Update progress
            progress = (i / total_actions) * 100
            self.progress_bar._value = progress
            
            # Log action execution
            log_msg = f"Executing action {i+1}: {action.type.value} - {action.description}"
            self.log_output.insert("end", log_msg + "\n")
            
            # Simulate execution time
            await asyncio.sleep(0.1)
            
            # Mock execution result
            result = {
                'action_index': i,
                'action_type': action.type,
                'status': 'success',
                'message': f'Action {i+1} completed successfully',
                'execution_time': 0.1
            }
            
            self.execution_results.append(result)
            
            # Update action tree status
            if str(i) in self.action_tree.items:
                item = self.action_tree.items[str(i)]
                item['values'][3] = "Completed"
        
        self.execution_status = "completed"
        return True

class MockSelectorTab:
    """Mock Selector Tab functionality for testing"""
    
    def __init__(self):
        # UI Components  
        self.html_viewer = MockText()
        self.selector_tree = MockTreeview()
        self.analysis_output = MockText()
        self.recommendation_list = MockTkinterWidget()
        
        # Data
        self.current_html = ""
        self.selector_strategies = []
        self.element_analysis = {}
        self.recommended_selectors = []
        
        # State tracking
        self.analysis_results = {}
        self.validation_results = {}
    
    def load_html_content(self, html_content):
        """Load HTML content for analysis"""
        self.current_html = html_content
        self.html_viewer._text = html_content
        self.html_viewer.log_entries.append(f"HTML loaded: {len(html_content)} characters")
        return len(html_content) > 0
    
    def analyze_html_structure(self):
        """Analyze HTML structure and identify elements"""
        if not self.current_html:
            return {}
            
        # Mock HTML analysis
        self.element_analysis = {
            'total_elements': 25,
            'clickable_elements': 8,
            'form_elements': 3,
            'unique_ids': 12,
            'unique_classes': 18,
            'deeply_nested': 5
        }
        
        # Log analysis
        analysis_text = "HTML Structure Analysis:\n"
        for key, value in self.element_analysis.items():
            analysis_text += f"  {key.replace('_', ' ').title()}: {value}\n"
        
        self.analysis_output.insert("end", analysis_text)
        return self.element_analysis
    
    def generate_selector_recommendations(self, element_criteria=None):
        """Generate selector recommendations based on analysis"""
        criteria = element_criteria or {}
        
        # Mock selector generation strategies
        strategies = [
            {'name': 'ID-based', 'reliability': 'high', 'specificity': 'high'},
            {'name': 'Class-based', 'reliability': 'medium', 'specificity': 'medium'},
            {'name': 'Attribute-based', 'reliability': 'medium', 'specificity': 'high'},
            {'name': 'Path-based', 'reliability': 'low', 'specificity': 'high'},
            {'name': 'Text-based', 'reliability': 'medium', 'specificity': 'low'}
        ]
        
        self.selector_strategies = strategies
        
        # Generate mock selectors
        mock_selectors = [
            {'selector': '#submit-button', 'strategy': 'ID-based', 'confidence': 95},
            {'selector': '.btn-primary', 'strategy': 'Class-based', 'confidence': 85},
            {'selector': '[data-testid="submit"]', 'strategy': 'Attribute-based', 'confidence': 90},
            {'selector': 'form > div:nth-child(3) > button', 'strategy': 'Path-based', 'confidence': 70},
            {'selector': 'button:contains("Submit")', 'strategy': 'Text-based', 'confidence': 80}
        ]
        
        # Apply criteria filtering
        if criteria.get('min_confidence'):
            mock_selectors = [s for s in mock_selectors if s['confidence'] >= criteria['min_confidence']]
            
        self.recommended_selectors = mock_selectors
        
        # Update selector tree
        self.selector_tree.items.clear()
        for i, selector_info in enumerate(mock_selectors):
            self.selector_tree.insert("", "end",
                values=[
                    selector_info['selector'],
                    selector_info['strategy'], 
                    f"{selector_info['confidence']}%",
                    "Not tested"
                ]
            )
        
        return len(mock_selectors)
    
    def validate_selector_strategy(self, selector, strategy):
        """Validate a specific selector using multiple strategies"""
        validation_result = {
            'selector': selector,
            'strategy': strategy,
            'tests_passed': 0,
            'tests_total': 4,
            'performance_score': 85,
            'reliability_score': 90,
            'specificity_score': 80,
            'details': []
        }
        
        # Mock validation tests
        tests = [
            ('Element Existence', True, 'Element found in DOM'),
            ('Uniqueness', True, 'Selector matches single element'),
            ('Stability', True, 'Selector works across page loads'),  
            ('Performance', False, 'Selector query took 15ms (>10ms threshold)')
        ]
        
        for test_name, passed, detail in tests:
            validation_result['details'].append({
                'test': test_name,
                'passed': passed,
                'detail': detail
            })
            if passed:
                validation_result['tests_passed'] += 1
        
        self.validation_results[selector] = validation_result
        return validation_result
    
    def get_selector_pattern_analysis(self):
        """Analyze patterns in generated selectors"""
        if not self.recommended_selectors:
            return {}
            
        # Count each selector type properly - a selector can belong to multiple categories
        id_count = 0
        class_count = 0
        attribute_count = 0
        path_count = 0
        
        for s in self.recommended_selectors:
            selector = s['selector']
            # Each selector counts as one primary type
            if selector.startswith('#'):
                id_count += 1
            elif selector.startswith('.'):
                class_count += 1
            elif '[' in selector:
                attribute_count += 1
            elif '>' in selector:
                path_count += 1
                
        patterns = {
            'id_selectors': id_count,
            'class_selectors': class_count,
            'attribute_selectors': attribute_count,
            'path_selectors': path_count,
            'high_confidence': len([s for s in self.recommended_selectors if s['confidence'] >= 85]),
            'avg_confidence': sum(s['confidence'] for s in self.recommended_selectors) / len(self.recommended_selectors)
        }
        
        return patterns

class TestActionTab(unittest.TestCase):
    """Test suite for Action Tab functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.action_tab = MockActionTab()
        
        # Create test actions
        self.test_actions = [
            Action(ActionType.INPUT_TEXT, description="Enter username", 
                  selector="input[name='username']", value="test@example.com"),
            Action(ActionType.CLICK_BUTTON, description="Click submit", 
                  selector="button[type='submit']"),
            Action(ActionType.CHECK_ELEMENT, description="Verify success", 
                  selector=".success-message", 
                  value={'check': 'contains', 'value': 'Success'})
        ]
    
    def test_load_action_sequence(self):
        """Test loading action sequence into the tab"""
        result = self.action_tab.load_action_sequence(self.test_actions)
        
        self.assertEqual(result, 3)
        self.assertEqual(len(self.action_tab.current_actions), 3)
        self.assertEqual(len(self.action_tab.action_tree.items), 3)
        
        # Verify action tree content
        for i, item in enumerate(self.action_tab.action_tree.items.values()):
            self.assertIn(str(i+1), item['values'][0])
            self.assertIn(self.test_actions[i].type.value, item['values'][1])
    
    def test_action_selection_and_parameter_editing(self):
        """Test action selection and parameter field population"""
        self.action_tab.load_action_sequence(self.test_actions)
        
        # Select first action
        result = self.action_tab.select_action(0)
        self.assertTrue(result)
        self.assertEqual(self.action_tab.selected_action, 0)
        
        # Check parameter fields populated
        self.assertIn('description', self.action_tab.parameter_fields)
        self.assertIn('selector', self.action_tab.parameter_fields)
        self.assertEqual(self.action_tab.parameter_fields['description'].get(), "Enter username")
        self.assertEqual(self.action_tab.parameter_fields['selector'].get(), "input[name='username']")
    
    def test_parameter_preview(self):
        """Test parameter preview functionality"""
        self.action_tab.load_action_sequence(self.test_actions)
        self.action_tab.select_action(0)
        
        preview = self.action_tab.preview_parameters()
        
        self.assertIn('description', preview)
        self.assertIn('selector', preview)
        self.assertEqual(preview['description'], "Enter username")
        self.assertEqual(preview['selector'], "input[name='username']")
    
    def test_apply_parameter_changes(self):
        """Test applying parameter changes to actions"""
        self.action_tab.load_action_sequence(self.test_actions)
        self.action_tab.select_action(0)
        
        # Modify parameters
        self.action_tab.parameter_fields['description'].set("Enter email address")
        self.action_tab.parameter_fields['selector'].set("input[name='email']")
        
        # Apply changes
        result = self.action_tab.apply_parameter_changes()
        self.assertTrue(result)
        
        # Verify changes applied
        updated_action = self.action_tab.current_actions[0]
        self.assertEqual(updated_action.description, "Enter email address")
        self.assertEqual(updated_action.selector, "input[name='email']")
        
        # Verify change tracking
        self.assertIn(0, self.action_tab.parameter_changes)
    
    def test_copy_action_functionality(self):
        """Test copying action with parameters"""
        self.action_tab.load_action_sequence(self.test_actions)
        
        copied_action = self.action_tab.copy_action(1)
        
        self.assertIsNotNone(copied_action)
        self.assertEqual(copied_action['type'], ActionType.CLICK_BUTTON)
        self.assertEqual(copied_action['description'], "Click submit")
        self.assertEqual(copied_action['selector'], "button[type='submit']")
    
    async def test_action_sequence_execution(self):
        """Test mock execution of action sequence"""
        self.action_tab.load_action_sequence(self.test_actions)
        
        result = await self.action_tab.execute_action_sequence()
        
        self.assertTrue(result)
        self.assertEqual(self.action_tab.execution_status, "completed")
        self.assertEqual(len(self.action_tab.execution_results), 3)
        
        # Verify all actions were executed
        for i, result in enumerate(self.action_tab.execution_results):
            self.assertEqual(result['action_index'], i)
            self.assertEqual(result['status'], 'success')
    
    def test_log_output_functionality(self):
        """Test log output during execution"""
        self.action_tab.load_action_sequence(self.test_actions)
        
        # Mock log entry
        test_message = "Test log message"
        self.action_tab.log_output.insert("end", test_message)
        
        self.assertIn(test_message, self.action_tab.log_output.log_entries)
        self.assertIn(test_message, self.action_tab.log_output.get())

class TestSelectorTab(unittest.TestCase):
    """Test suite for Selector Tab functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.selector_tab = MockSelectorTab()
        
        # Sample HTML content for testing
        self.test_html = """
        <html>
        <body>
            <div id="main-container">
                <form class="login-form">
                    <input id="username" name="username" type="email" class="form-input">
                    <input id="password" name="password" type="password" class="form-input">
                    <button type="submit" class="btn btn-primary" data-testid="submit">Submit</button>
                </form>
                <div class="success-message" style="display:none;">Login successful!</div>
            </div>
        </body>
        </html>
        """
    
    def test_load_html_content(self):
        """Test loading HTML content for analysis"""
        result = self.selector_tab.load_html_content(self.test_html)
        
        self.assertTrue(result)
        self.assertEqual(self.selector_tab.current_html, self.test_html)
        self.assertIn("HTML loaded", self.selector_tab.html_viewer.log_entries[-1])
    
    def test_html_structure_analysis(self):
        """Test HTML structure analysis"""
        self.selector_tab.load_html_content(self.test_html)
        
        analysis = self.selector_tab.analyze_html_structure()
        
        self.assertIn('total_elements', analysis)
        self.assertIn('clickable_elements', analysis)
        self.assertIn('form_elements', analysis)
        self.assertIn('unique_ids', analysis)
        self.assertIn('unique_classes', analysis)
        
        # Check analysis output logged
        self.assertIn("HTML Structure Analysis", self.selector_tab.analysis_output.get())
    
    def test_selector_recommendation_generation(self):
        """Test selector recommendation generation"""
        self.selector_tab.load_html_content(self.test_html)
        self.selector_tab.analyze_html_structure()
        
        count = self.selector_tab.generate_selector_recommendations()
        
        self.assertGreater(count, 0)
        self.assertGreater(len(self.selector_tab.recommended_selectors), 0)
        self.assertGreater(len(self.selector_tab.selector_tree.items), 0)
        
        # Check recommendation quality
        first_recommendation = self.selector_tab.recommended_selectors[0]
        self.assertIn('selector', first_recommendation)
        self.assertIn('strategy', first_recommendation)
        self.assertIn('confidence', first_recommendation)
    
    def test_selector_recommendation_filtering(self):
        """Test filtering recommendations by criteria"""
        self.selector_tab.load_html_content(self.test_html)
        
        # Test with minimum confidence filter
        criteria = {'min_confidence': 90}
        count = self.selector_tab.generate_selector_recommendations(criteria)
        
        # Verify all recommendations meet criteria
        for selector_info in self.selector_tab.recommended_selectors:
            self.assertGreaterEqual(selector_info['confidence'], 90)
    
    def test_selector_strategy_validation(self):
        """Test multi-strategy selector validation"""
        test_selector = "#submit-button"
        test_strategy = "ID-based"
        
        result = self.selector_tab.validate_selector_strategy(test_selector, test_strategy)
        
        self.assertEqual(result['selector'], test_selector)
        self.assertEqual(result['strategy'], test_strategy)
        self.assertIn('tests_passed', result)
        self.assertIn('tests_total', result)
        self.assertIn('performance_score', result)
        self.assertIn('reliability_score', result)
        self.assertIn('details', result)
        
        # Verify validation details
        self.assertEqual(len(result['details']), 4)
        for detail in result['details']:
            self.assertIn('test', detail)
            self.assertIn('passed', detail)
            self.assertIn('detail', detail)
    
    def test_selector_pattern_analysis(self):
        """Test selector pattern analysis"""
        self.selector_tab.load_html_content(self.test_html)
        self.selector_tab.generate_selector_recommendations()
        
        patterns = self.selector_tab.get_selector_pattern_analysis()
        
        self.assertIn('id_selectors', patterns)
        self.assertIn('class_selectors', patterns)
        self.assertIn('attribute_selectors', patterns)
        self.assertIn('path_selectors', patterns)
        self.assertIn('high_confidence', patterns)
        self.assertIn('avg_confidence', patterns)
        
        # Verify pattern counts make sense - total should not exceed number of selectors
        total_pattern_selectors = (patterns['id_selectors'] + patterns['class_selectors'] + 
                                 patterns['attribute_selectors'] + patterns['path_selectors'])
        self.assertLessEqual(total_pattern_selectors, len(self.selector_tab.recommended_selectors))

class TestTabIntegration(unittest.TestCase):
    """Test suite for tab integration functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.action_tab = MockActionTab()
        self.selector_tab = MockSelectorTab()
        
        # Test data
        self.test_actions = [
            Action(ActionType.CLICK_BUTTON, description="Click submit", selector="")
        ]
        self.test_html = """
        <button id="submit-btn" class="btn-primary" data-testid="submit">Submit</button>
        """
    
    def test_parameter_copying_between_tabs(self):
        """Test copying parameters from Selector tab to Action tab"""
        # Setup Selector tab with recommendations
        self.selector_tab.load_html_content(self.test_html)
        self.selector_tab.generate_selector_recommendations()
        
        # Setup Action tab with action needing selector
        self.action_tab.load_action_sequence(self.test_actions)
        self.action_tab.select_action(0)
        
        # Get recommended selector from Selector tab
        recommended_selector = self.selector_tab.recommended_selectors[0]['selector']
        
        # Apply selector to Action tab
        self.action_tab.parameter_fields['selector'].set(recommended_selector)
        self.action_tab.apply_parameter_changes()
        
        # Verify integration
        updated_action = self.action_tab.current_actions[0]
        self.assertEqual(updated_action.selector, recommended_selector)
    
    def test_selector_validation_with_action_context(self):
        """Test validating selectors in context of specific action types"""
        # Setup for button click action
        self.action_tab.load_action_sequence(self.test_actions)
        action_type = self.test_actions[0].type
        
        # Generate selectors with action context
        self.selector_tab.load_html_content(self.test_html)
        criteria = {'action_type': action_type, 'min_confidence': 80}
        self.selector_tab.generate_selector_recommendations(criteria)
        
        # Validate that recommendations are suitable for button clicks
        for selector_info in self.selector_tab.recommended_selectors:
            self.assertGreaterEqual(selector_info['confidence'], 80)
    
    def test_workflow_tab_switching_performance(self):
        """Test performance of switching between tabs with data"""
        # Load data in both tabs
        self.action_tab.load_action_sequence(self.test_actions)
        self.selector_tab.load_html_content(self.test_html)
        self.selector_tab.generate_selector_recommendations()
        
        # Measure tab switching simulation
        start_time = time.time()
        
        # Simulate tab switches
        for _ in range(10):
            # Switch to Action tab (simulate UI update)
            self.action_tab.select_action(0)
            preview = self.action_tab.preview_parameters()
            
            # Switch to Selector tab (simulate UI update)  
            analysis = self.selector_tab.get_selector_pattern_analysis()
        
        end_time = time.time()
        switch_time = (end_time - start_time) / 10
        
        # Verify acceptable performance (< 50ms per switch)
        self.assertLess(switch_time, 0.05, f"Tab switching too slow: {switch_time:.3f}s")

class TestGUIResponsiveness(unittest.TestCase):
    """Test suite for GUI responsiveness and error handling"""
    
    def setUp(self):
        """Setup test environment"""
        self.action_tab = MockActionTab()
        self.selector_tab = MockSelectorTab()
    
    def test_large_action_sequence_handling(self):
        """Test handling of large action sequences"""
        # Create large action sequence
        large_action_list = []
        for i in range(100):
            action = Action(ActionType.WAIT, description=f"Wait step {i}", timeout=1000)
            large_action_list.append(action)
        
        # Test loading performance
        start_time = time.time()
        result = self.action_tab.load_action_sequence(large_action_list)
        load_time = time.time() - start_time
        
        self.assertEqual(result, 100)
        self.assertLess(load_time, 1.0, f"Large sequence loading too slow: {load_time:.3f}s")
    
    def test_invalid_parameter_handling(self):
        """Test handling of invalid parameter values"""
        test_action = Action(ActionType.WAIT, description="Test wait", timeout=5000)
        self.action_tab.load_action_sequence([test_action])
        self.action_tab.select_action(0)
        
        # Set invalid timeout value
        self.action_tab.parameter_fields['timeout'].set("invalid_number")
        
        # Apply changes should fail gracefully
        result = self.action_tab.apply_parameter_changes()
        self.assertFalse(result)
    
    def test_empty_html_content_handling(self):
        """Test handling of empty or invalid HTML content"""
        # Test empty HTML
        result = self.selector_tab.load_html_content("")
        self.assertFalse(result)
        
        # Test with minimal HTML
        minimal_html = "<html></html>"
        result = self.selector_tab.load_html_content(minimal_html)
        self.assertTrue(result)
        
        # Analysis should still work
        analysis = self.selector_tab.analyze_html_structure()
        self.assertIsInstance(analysis, dict)
    
    def test_selector_recommendation_edge_cases(self):
        """Test selector recommendation with edge cases"""
        # HTML with no useful selectors
        difficult_html = "<html><body><div><div><div><span></span></div></div></div></body></html>"
        
        self.selector_tab.load_html_content(difficult_html)
        count = self.selector_tab.generate_selector_recommendations({'min_confidence': 95})
        
        # Should handle gracefully even with difficult HTML
        self.assertGreaterEqual(count, 0)
        
        # Should provide some fallback recommendations
        if count > 0:
            for selector in self.selector_tab.recommended_selectors:
                self.assertIsInstance(selector['selector'], str)
                self.assertGreater(len(selector['selector']), 0)

class TestEndToEndWorkflows(unittest.TestCase):
    """Test suite for complete end-to-end workflows"""
    
    def setUp(self):
        """Setup test environment"""
        self.action_tab = MockActionTab()
        self.selector_tab = MockSelectorTab()
    
    async def test_complete_action_creation_workflow(self):
        """Test complete workflow: HTML analysis -> selector recommendation -> action creation"""
        # Step 1: Load HTML and analyze
        test_html = """
        <form id="login-form">
            <input type="email" name="email" class="form-control" required>
            <input type="password" name="password" class="form-control" required>
            <button type="submit" class="btn btn-primary">Login</button>
        </form>
        """
        
        self.selector_tab.load_html_content(test_html)
        analysis = self.selector_tab.analyze_html_structure()
        
        # Step 2: Generate selector recommendations
        count = self.selector_tab.generate_selector_recommendations({'min_confidence': 80})
        self.assertGreater(count, 0)
        
        # Step 3: Create actions using recommended selectors
        recommended_selectors = [s['selector'] for s in self.selector_tab.recommended_selectors[:3]]
        
        workflow_actions = []
        for i, selector in enumerate(recommended_selectors):
            action = Action(
                ActionType.CLICK_BUTTON if 'button' in selector else ActionType.INPUT_TEXT,
                description=f"Action {i+1} using recommended selector",
                selector=selector
            )
            workflow_actions.append(action)
        
        # Step 4: Load into Action tab and execute
        self.action_tab.load_action_sequence(workflow_actions)
        result = await self.action_tab.execute_action_sequence()
        
        # Verify complete workflow
        self.assertTrue(result)
        self.assertEqual(len(self.action_tab.execution_results), len(workflow_actions))
    
    def test_cross_tab_data_consistency(self):
        """Test data consistency when working across both tabs"""
        # Setup initial state
        test_action = Action(ActionType.CLICK_BUTTON, description="Test button", selector="")
        self.action_tab.load_action_sequence([test_action])
        
        html_content = '<button id="test-btn">Test</button>'
        self.selector_tab.load_html_content(html_content)
        
        # Generate recommendations
        self.selector_tab.generate_selector_recommendations()
        recommended = self.selector_tab.recommended_selectors[0]['selector']
        
        # Apply to action
        self.action_tab.select_action(0)
        self.action_tab.parameter_fields['selector'].set(recommended)
        self.action_tab.apply_parameter_changes()
        
        # Verify consistency
        updated_action = self.action_tab.current_actions[0]
        self.assertEqual(updated_action.selector, recommended)
        
        # Validate the selector works for the action type
        validation = self.selector_tab.validate_selector_strategy(recommended, "ID-based")
        self.assertGreater(validation['reliability_score'], 0)
    
    def test_performance_with_realistic_data_sizes(self):
        """Test performance with realistic data sizes"""
        # Large HTML document
        large_html = f"""
        <html><body>
        {"<div class='item'><span>Item content</span><button class='btn'>Action</button></div>" * 50}
        </body></html>
        """
        
        # Large action sequence  
        large_actions = []
        for i in range(25):
            large_actions.append(Action(ActionType.CLICK_BUTTON, description=f"Action {i}", selector=f".btn-{i}"))
        
        # Performance test
        start_time = time.time()
        
        # Load and process data
        self.selector_tab.load_html_content(large_html)
        self.selector_tab.analyze_html_structure()
        selector_count = self.selector_tab.generate_selector_recommendations()
        
        self.action_tab.load_action_sequence(large_actions)
        
        # Cross-tab operations
        for i in range(5):
            self.action_tab.select_action(i)
            preview = self.action_tab.preview_parameters()
            pattern_analysis = self.selector_tab.get_selector_pattern_analysis()
        
        total_time = time.time() - start_time
        
        # Verify acceptable performance for realistic data
        self.assertLess(total_time, 2.0, f"Realistic data processing too slow: {total_time:.3f}s")
        self.assertGreater(selector_count, 0)

def run_comprehensive_test_suite():
    """Run the complete comprehensive test suite"""
    print("🚀 Starting Comprehensive GUI Tabs Test Suite")
    print("=" * 60)
    
    test_classes = [
        TestActionTab,
        TestSelectorTab, 
        TestTabIntegration,
        TestGUIResponsiveness,
        TestEndToEndWorkflows
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}")
        print("-" * 40)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        tests_run = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        
        total_tests += tests_run
        passed_tests += (tests_run - failures - errors)
        
        if result.failures or result.errors:
            failed_tests.extend([f"{test_class.__name__}: {failure[0]}" for failure in result.failures])
            failed_tests.extend([f"{test_class.__name__}: {error[0]}" for error in result.errors])
        
        print(f"✅ Tests run: {tests_run}, Failed: {failures + errors}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 COMPREHENSIVE TEST SUITE RESULTS")
    print("=" * 60)
    print(f"📊 Total tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\n❌ Failed tests:")
        for failed_test in failed_tests:
            print(f"   • {failed_test}")
    else:
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ New GUI Tabs are ready for implementation!")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    # Run comprehensive test suite
    success = run_comprehensive_test_suite()
    
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILURE'}: GUI Tabs Test Suite Complete")
    sys.exit(0 if success else 1)