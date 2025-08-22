#!/usr/bin/env python3
"""
Test GUI stop integration without opening actual GUI
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock
import threading
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType
from core.controller import AutomationController


class TestGUIStopIntegration(unittest.TestCase):
    """Test the actual GUI stop workflow without GUI"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = AutomationConfig(
            name="Test Stop Integration",
            url="https://example.com",
            actions=[
                Action(type=ActionType.WAIT, value=500, description="Wait 0.5s"),
                Action(type=ActionType.WAIT, value=500, description="Wait 0.5s"), 
                Action(type=ActionType.WAIT, value=500, description="Wait 0.5s"),
                Action(type=ActionType.WAIT, value=500, description="Wait 0.5s"),
                Action(type=ActionType.WAIT, value=500, description="Wait 0.5s"),
            ]
        )
    
    def test_gui_workflow_simulation(self):
        """Test the complete GUI stop workflow"""
        # Simulate GUI controller creation and management
        controller = None
        engine = None
        
        try:
            # Step 1: Create controller (like GUI does)
            controller = AutomationController()
            
            # Step 2: Reset and start controller (like GUI _run_automation_thread)
            controller.reset_automation()
            controller.start_automation(total_actions=len(self.config.actions))
            
            # Step 3: Create engine with controller (like GUI does)
            with patch('core.engine.async_playwright') as mock_playwright:
                # Setup minimal mocking for browser
                mock_browser = Mock()
                mock_page = Mock()
                mock_context = Mock()
                
                mock_playwright.return_value.__aenter__.return_value.chromium.launch = AsyncMock(return_value=mock_browser)
                mock_browser.new_context = AsyncMock(return_value=mock_context)
                mock_context.new_page = AsyncMock(return_value=mock_page)
                mock_page.goto = AsyncMock()
                mock_page.wait_for_load_state = AsyncMock()
                mock_page.url = "https://example.com"
                mock_page.is_closed.return_value = False
                mock_browser.is_connected.return_value = True
                mock_browser.close = AsyncMock()
                
                engine = WebAutomationEngine(self.config, controller=controller)
                
                # Step 4: Start automation in background thread (like GUI does)
                automation_result = {'completed': False, 'error': None}
                
                def run_automation():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        results = loop.run_until_complete(engine.run_automation())
                        automation_result['results'] = results
                        automation_result['completed'] = True
                    except Exception as e:
                        automation_result['error'] = str(e)
                        automation_result['completed'] = True
                
                automation_thread = threading.Thread(target=run_automation, daemon=True)
                start_time = time.time()
                automation_thread.start()
                
                # Step 5: Wait a moment then simulate stop button click
                time.sleep(0.3)  # Let automation start
                
                # Simulate GUI stop button logic
                stop_success = controller.stop_automation(emergency=False)
                self.assertTrue(stop_success, "Stop signal should be sent successfully")
                
                # Step 6: Wait for automation to complete
                automation_thread.join(timeout=5.0)
                
                # Verify automation stopped quickly
                end_time = time.time()
                execution_time = end_time - start_time
                self.assertLess(execution_time, 2.0, "Automation should stop within 2 seconds")
                
                # Verify automation completed (either normally or via stop)
                self.assertTrue(automation_result['completed'], "Automation should complete")
                
                # If there was an error, it should be KeyboardInterrupt (stop signal)
                if automation_result['error']:
                    self.assertIn("stopped", automation_result['error'].lower(), 
                                f"Error should indicate stop: {automation_result['error']}")
                
                print(f"✅ Automation stopped in {execution_time:.2f}s")
                
        finally:
            # Cleanup
            if controller:
                controller.reset_automation()


class AsyncMock(Mock):
    """Mock class for async functions"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)