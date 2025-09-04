#!/usr/bin/env python3.11
"""
Test User Reported Scenario
===========================
Test the exact scenario reported by the user to ensure it's resolved:
- 0 completed generations found on /generate page  
- start_from target not found
- Should use generation container mode instead of thumbnail navigation
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig


class TestUserReportedScenario:
    """Test the exact scenario reported by the user"""
    
    @pytest.fixture
    def config_with_start_from(self):
        """Create config matching user's scenario"""
        config = GenerationDownloadConfig()
        config.start_from = "03 Sep 2025 16:15:18"  # User's example datetime
        config.max_downloads = 50
        return config
    
    @pytest.fixture
    def download_manager(self, config_with_start_from):
        """Create download manager with user's config"""
        return GenerationDownloadManager(config_with_start_from)
    
    @pytest.mark.asyncio
    async def test_user_reported_scenario_zero_completed_generations(self, download_manager):
        """Test the exact scenario: 0 completed generations + start_from target not found"""
        
        # Mock page object
        mock_page = AsyncMock()
        
        # Simulate the exact conditions from user's logs:
        # "Found 0 completed generations"
        # "No completed generations detected on initial page"
        
        # Mock containers exist but none match the start_from target
        mock_container = AsyncMock()
        mock_container.text_content.return_value = "Creation Time 04 Sep 2025 10:20:30\nSome different prompt..."
        
        def mock_query_selector_all(selector):
            # Return containers for some selectors (simulating containers exist but target not found)
            if selector in ["div[id$='__0']", "div[id$='__1']"]:
                return [mock_container]  # Return container but it won't match target datetime
            else:
                return []
        
        mock_page.query_selector_all.side_effect = mock_query_selector_all
        
        # Mock metadata extraction to return different datetime than target
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced') as mock_extract:
            mock_extract.return_value = {
                'creation_time': '04 Sep 2025 10:20:30',  # Different from target
                'prompt': 'Some different prompt...'
            }
            
            # Mock the fallback generation container mode (what should be called)
            with patch.object(download_manager, 'execute_generation_container_mode') as mock_container_mode:
                mock_container_mode.return_value = {
                    'success': True,
                    'downloads_completed': 2,
                    'errors': [],
                    'start_time': '2025-09-04T10:00:00',
                    'end_time': '2025-09-04T10:30:00'
                }
                
                # Mock the methods that should NOT be called (normal thumbnail navigation)
                with patch.object(download_manager, 'find_completed_generations_on_page') as mock_find_completed:
                    mock_find_completed.return_value = []  # 0 completed generations (user's scenario)
                    
                    with patch.object(download_manager, '_configure_chromium_download_settings') as mock_config:
                        mock_config.return_value = True
                    
                        # Run the automation with user's exact scenario  
                        result = await download_manager.run_download_automation(mock_page)
                        
                        # Verify the fix works:
                        
                        # 1. start_from search was attempted (target not found)
                        # This happens inside run_download_automation
                        
                        # 2. execute_generation_container_mode was called (NOT thumbnail navigation)
                        mock_container_mode.assert_called_once()
                        
                        # 3. Normal completed generation detection should NOT be called
                        # because start_from bypasses it entirely
                        mock_find_completed.assert_not_called()
                        
                        # 4. Result should come from generation container mode
                        assert result['success'] == True
                        assert result['downloads_completed'] == 2
                        
                        print("✅ USER SCENARIO FIXED:")
                        print("   • 0 completed generations found")  
                        print("   • start_from target not found")
                        print("   • Uses generation container mode (NOT thumbnail navigation)")
                        print("   • Bypasses normal queue detection completely")
    
    @pytest.mark.asyncio 
    async def test_expected_log_flow_for_user_scenario(self, download_manager):
        """Test that the log messages match what user should now see"""
        
        # Mock page object
        mock_page = AsyncMock()
        
        # Mock containers with no target match
        mock_container = AsyncMock()
        mock_container.text_content.return_value = "Creation Time 04 Sep 2025 10:20:30\nPrompt..."
        
        def mock_query_selector_all(selector):
            if selector == "div[id$='__0']":
                return [mock_container]
            else:
                return []
        
        mock_page.query_selector_all.side_effect = mock_query_selector_all
        
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced') as mock_extract:
            mock_extract.return_value = {
                'creation_time': '04 Sep 2025 10:20:30',  # Different from target
                'prompt': 'Some prompt...'
            }
            
            with patch.object(download_manager, 'execute_generation_container_mode') as mock_container_mode:
                mock_container_mode.return_value = {
                    'success': True,
                    'downloads_completed': 1
                }
                
                # Capture logs to verify correct flow
                import logging
                
                # Enable logging capture
                logger = logging.getLogger('src.utils.generation_download_manager')
                logger.setLevel(logging.INFO)
                
                with patch.object(logger, 'info') as mock_log_info:
                    with patch.object(logger, 'warning') as mock_log_warning:
                        
                        result = await download_manager.run_download_automation(mock_page)
                        
                        # Verify the expected log messages are generated
                        log_messages = [call.args[0] for call in mock_log_info.call_args_list]
                        warning_messages = [call.args[0] for call in mock_log_warning.call_args_list]
                        
                        # Should see these log messages (or similar):
                        start_from_logs = [msg for msg in log_messages if 'START_FROM' in msg]
                        container_mode_logs = [msg for msg in log_messages if 'GENERATION CONTAINER MODE' in msg]
                        
                        # User should see clear indication of what's happening
                        assert len(start_from_logs) > 0, "Should see START_FROM log messages"
                        
                        print("✅ EXPECTED LOG FLOW FOR USER:")
                        print("   📋 START_FROM mode logs:", len(start_from_logs))
                        print("   🎯 Generation container mode logs:", len(container_mode_logs))
                        print("   ⚠️  Warning logs:", len(warning_messages))
                        
                        # Most importantly: Should see explicit "no thumbnail navigation" log message
                        no_thumbnail_logs = [msg for msg in log_messages + warning_messages 
                                           if 'no thumbnail navigation' in msg.lower()]
                        assert len(no_thumbnail_logs) > 0, f"Should see 'no thumbnail navigation' log message"
                        
                        # Should NOT see actual thumbnail navigation activity logs
                        bad_thumbnail_logs = [msg for msg in log_messages + warning_messages 
                                            if ('thumbnail' in msg.lower() or 'completed task' in msg.lower()) 
                                            and 'no thumbnail navigation' not in msg.lower()]
                        assert len(bad_thumbnail_logs) == 0, f"Should not see actual thumbnail navigation activity: {bad_thumbnail_logs}"
                        
                        print("   ✅ Explicit 'no thumbnail navigation' message found (confirmed fix)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])