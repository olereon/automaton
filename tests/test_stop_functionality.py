#!/usr/bin/env python3
"""
Test automation stop functionality
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import Mock, patch
import threading
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType
from core.controller import AutomationController


class TestStopFunctionality(unittest.TestCase):
    """Test automation stop functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = AutomationConfig(
            name="Test Stop",
            url="https://example.com",
            actions=[
                Action(type=ActionType.WAIT, value=1000, description="Wait 1s"),
                Action(type=ActionType.WAIT, value=1000, description="Wait 1s"), 
                Action(type=ActionType.WAIT, value=1000, description="Wait 1s"),
                Action(type=ActionType.WAIT, value=1000, description="Wait 1s"),
                Action(type=ActionType.WAIT, value=1000, description="Wait 1s"),
            ]
        )
    
    def test_controller_stop_signal(self):
        """Test that controller can send and receive stop signals"""
        controller = AutomationController()
        
        # Start automation first
        controller.start_automation(total_actions=5)
        
        # Initially should not be stopped
        self.assertFalse(asyncio.run(controller.check_should_stop()))
        
        # Send stop signal
        success = controller.stop_automation()
        self.assertTrue(success)
        
        # Should now be stopped
        self.assertTrue(asyncio.run(controller.check_should_stop()))
    
    def test_engine_with_controller_stop(self):
        """Test that engine with controller responds to stop signals"""
        controller = AutomationController()
        
        # Mock browser operations to avoid actual browser startup
        with patch('core.engine.async_playwright') as mock_playwright:
            mock_browser = Mock()
            mock_page = Mock()
            mock_context = Mock()
            
            # Setup mock chain
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            mock_page.goto = Mock()
            mock_page.wait_for_load_state = Mock()
            mock_page.url = "https://example.com"
            mock_page.is_closed.return_value = False
            mock_browser.is_connected.return_value = True
            
            # Create engine with controller
            engine = WebAutomationEngine(self.config, controller=controller)
            
            # Start automation in a separate thread
            automation_thread = threading.Thread(
                target=lambda: asyncio.run(engine.run_automation()),
                daemon=True
            )
            
            start_time = time.time()
            automation_thread.start()
            
            # Wait a moment then send stop signal
            time.sleep(0.5)
            controller.stop_automation()
            
            # Wait for automation to complete
            automation_thread.join(timeout=5.0)
            end_time = time.time()
            
            # Should have stopped quickly (within 2 seconds)
            execution_time = end_time - start_time
            self.assertLess(execution_time, 2.0, "Automation should stop quickly when stop signal is sent")
    
    def test_engine_without_controller_continues(self):
        """Test that engine without controller continues running"""
        # Mock browser operations
        with patch('core.engine.async_playwright') as mock_playwright:
            mock_browser = Mock()
            mock_page = Mock()
            mock_context = Mock()
            
            # Setup mock chain
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            mock_page.goto = Mock()
            mock_page.wait_for_load_state = Mock()
            mock_page.url = "https://example.com"
            mock_page.is_closed.return_value = False
            mock_browser.is_connected.return_value = True
            
            # Create engine WITHOUT controller
            engine = WebAutomationEngine(self.config)
            
            # This should complete all actions since no controller is stopping it
            # We'll run with a timeout to avoid hanging
            try:
                results = asyncio.run(asyncio.wait_for(engine.run_automation(), timeout=10.0))
                # Should complete all actions if not stopped
                self.assertEqual(results['actions_completed'], len(self.config.actions))
            except asyncio.TimeoutError:
                self.fail("Engine without controller should complete normally")
    
    def test_emergency_stop(self):
        """Test emergency stop functionality"""
        controller = AutomationController()
        
        # Start automation first
        controller.start_automation(total_actions=5)
        
        # Send emergency stop
        success = controller.stop_automation(emergency=True)
        self.assertTrue(success)
        
        # Should be stopped and emergency
        self.assertTrue(asyncio.run(controller.check_should_stop()))
        self.assertTrue(asyncio.run(controller.check_emergency_stop()))


class TestGUIControllerIntegration(unittest.TestCase):
    """Test GUI controller integration without actually starting GUI"""
    
    def test_gui_controller_creation(self):
        """Test that GUI can create and use controller"""
        # Simulate GUI controller creation
        controller = AutomationController()
        
        # Start automation first
        controller.start_automation(total_actions=10)
        
        # Test stop signal
        success = controller.stop_automation()
        self.assertTrue(success)
        
        # Test reset
        controller.reset_automation()
        self.assertFalse(asyncio.run(controller.check_should_stop()))


if __name__ == '__main__':
    unittest.main(verbosity=2)