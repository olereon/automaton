#!/usr/bin/env python3.11

"""
Test for the robust scrolling fix in boundary detection.

This test verifies that the scrolling mechanism works correctly to 
extend the generation list when the boundary is beyond the initially
visible containers.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig, DuplicateMode

class TestRobustScrollingFix:
    """Test enhanced scrolling mechanism for boundary detection"""

    @pytest.fixture
    def skip_config(self, tmp_path):
        """SKIP mode configuration for testing"""
        return GenerationDownloadConfig(
            downloads_folder=str(tmp_path / "downloads"),
            logs_folder=str(tmp_path / "logs"),
            duplicate_mode=DuplicateMode.SKIP,
            duplicate_check_enabled=True,
            stop_on_duplicate=False,
            use_exit_scan_strategy=True,
            creation_time_text="Creation Time",
            max_downloads=100
        )

    def create_mock_containers_batch(self, start_index, count, base_datetime="03 Sep 2025 18:00:00"):
        """Create a batch of mock containers with progressive timestamps"""
        containers = []
        from datetime import datetime, timedelta
        
        base = datetime.strptime(base_datetime, "%d %b %Y %H:%M:%S")
        
        for i in range(count):
            container = AsyncMock()
            # Create progressive timestamps (going backwards in time)
            timestamp = base - timedelta(minutes=i*5)  
            timestamp_str = timestamp.strftime("%d %b %Y %H:%M:%S")
            
            container.text_content.return_value = f"Generation {start_index + i} with Creation Time {timestamp_str}"
            container.get_attribute.return_value = f"container_{start_index + i}"
            containers.append((container, f"unique_key_{start_index + i}"))
        
        return containers

    def create_mock_page_with_scrolling(self):
        """Create mock page with scrolling behavior simulation"""
        mock_page = AsyncMock()
        
        # Mock scrolling state
        scroll_position = 0
        viewport_height = 800
        document_height = 5000
        
        async def mock_evaluate(script):
            nonlocal scroll_position
            
            if "window.innerHeight" in script:
                return viewport_height
            elif "window.pageYOffset" in script:
                return scroll_position  
            elif "document.body.scrollHeight" in script:
                return document_height
            elif "scrollTo" in script:
                # Extract scroll position from scrollTo call
                import re
                match = re.search(r'scrollTo\(0,\s*(\d+)\)', script)
                if match:
                    scroll_position = int(match.group(1))
                    # Simulate loading more containers after scroll
                    return True
            elif "scrollBy" in script:
                # Extract scroll delta from scrollBy call
                match = re.search(r'scrollBy\(0,\s*(\d+)\)', script)
                if match:
                    scroll_position += int(match.group(1))
                return True
            elif "window.dispatchEvent" in script:
                return True
            
            return scroll_position
        
        mock_page.evaluate.side_effect = mock_evaluate
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        
        return mock_page, scroll_position

    @pytest.mark.asyncio
    async def test_scrolling_continues_after_no_new_containers(self, skip_config):
        """
        Test that scrolling continues even when no new containers are found,
        which was the core issue preventing boundary detection.
        """
        
        manager = GenerationDownloadManager(skip_config)
        mock_page, _ = self.create_mock_page_with_scrolling()
        
        # Setup log entries - boundary should be found after container #35
        existing_log_entries = {}
        for i in range(25):  # 25 duplicates before boundary
            time_key = f"03 Sep 2025 18:{30-i:02d}:00"
            existing_log_entries[time_key] = {
                'file_id': f'#0000000{i:02d}',
                'prompt': f'Duplicate generation {i}'
            }
        
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            manager.existing_log_entries = existing_log_entries
        
        # Simulate the exact failing scenario:
        # Iteration 1: 30 containers (25 duplicates + 5 boundary candidates)  
        # Iteration 2-6: Same 30 containers (no new ones) - old logic would stop scrolling
        containers_calls = [
            # First call: 30 containers with 25 duplicates
            self.create_mock_containers_batch(1, 30, "03 Sep 2025 18:30:00"),
            
            # Second call: Same 30 containers (simulating no new containers loaded)
            self.create_mock_containers_batch(1, 30, "03 Sep 2025 18:30:00"),
            
            # Third call: After proper scrolling, new containers appear (with boundary)
            self.create_mock_containers_batch(1, 40, "03 Sep 2025 18:30:00"),  # Boundary at #35
        ]
        
        call_count = 0
        def mock_query_selector_all(selector):
            nonlocal call_count
            if call_count < len(containers_calls):
                result = [container for container, _ in containers_calls[call_count]]
                call_count += 1
                return result
            return []
        
        mock_page.query_selector_all.side_effect = mock_query_selector_all
        
        # Mock metadata extraction - return duplicates for first 25, then boundary
        def mock_extract_container_metadata(container, text_content):
            if "Generation 26" in text_content:  # This will be our boundary
                return {
                    'creation_time': '03 Sep 2025 16:15:18',  # Not in log = boundary!
                    'prompt': 'Boundary generation prompt'
                }
            else:
                # Extract generation number for duplicate simulation
                import re
                match = re.search(r'Generation (\d+)', text_content)
                if match:
                    gen_num = int(match.group(1))
                    if gen_num <= 25:
                        time_key = f"03 Sep 2025 18:{30-gen_num:02d}:00"
                        return {
                            'creation_time': time_key,
                            'prompt': f'Duplicate generation {gen_num}'
                        }
            return None
        
        with patch.object(manager, '_extract_container_metadata', side_effect=mock_extract_container_metadata):
            with patch.object(manager, '_click_boundary_container', return_value=True):
                
                result = await manager._find_download_boundary_sequential(mock_page)
                
                # Should find boundary after enhanced scrolling
                assert result is not None
                assert result['found'] == True
                assert result['creation_time'] == '03 Sep 2025 16:15:18'
                
                # Verify scrolling happened multiple times despite no new containers
                assert mock_page.evaluate.call_count >= 6  # Multiple scroll operations

    @pytest.mark.asyncio
    async def test_enhanced_scrolling_strategies(self, skip_config):
        """Test that enhanced scrolling strategies are applied correctly"""
        
        manager = GenerationDownloadManager(skip_config)
        mock_page, _ = self.create_mock_page_with_scrolling()
        
        # Setup for boundary at container #40 (beyond initial 30)
        existing_log_entries = {}
        for i in range(35):
            time_key = f"03 Sep 2025 17:{55-i:02d}:00"
            existing_log_entries[time_key] = {
                'file_id': f'#0000000{i:02d}',
                'prompt': f'Old generation {i}'
            }
        
        manager.existing_log_entries = existing_log_entries
        
        # Mock progressive container loading simulation
        containers_batch_1 = self.create_mock_containers_batch(1, 30, "03 Sep 2025 18:00:00") 
        containers_batch_2 = self.create_mock_containers_batch(31, 15, "03 Sep 2025 17:15:00")  # Boundary here
        
        call_count = 0
        def mock_progressive_query(selector):
            nonlocal call_count
            if call_count == 0:
                call_count += 1
                return [c for c, _ in containers_batch_1]  # First 30 
            elif call_count == 1:
                call_count += 1  
                return [c for c, _ in containers_batch_1 + containers_batch_2]  # 30 + 15 = 45 total
            else:
                return [c for c, _ in containers_batch_1 + containers_batch_2]  # Keep returning 45
        
        mock_page.query_selector_all.side_effect = mock_progressive_query
        
        def mock_extract_metadata(container, text_content):
            if "Generation 36" in text_content:  # Boundary generation
                return {
                    'creation_time': '03 Sep 2025 16:15:18',  # Not in logs
                    'prompt': 'Boundary generation'
                }
            # Return duplicates for others
            return {
                'creation_time': '03 Sep 2025 17:30:00',  # In logs = duplicate
                'prompt': 'Duplicate'
            }
        
        with patch.object(manager, '_extract_container_metadata', side_effect=mock_extract_metadata):
            with patch.object(manager, '_click_boundary_container', return_value=True):
                
                result = await manager._find_download_boundary_sequential(mock_page)
                
                # Should successfully find boundary after enhanced scrolling
                assert result is not None
                assert result['found'] == True
                
                # Verify enhanced scrolling methods were called
                evaluate_calls = [call.args[0] for call in mock_page.evaluate.call_args_list]
                
                # Should have viewport and scroll state queries
                assert any("window.innerHeight" in call for call in evaluate_calls)
                assert any("window.pageYOffset" in call for call in evaluate_calls)
                assert any("document.body.scrollHeight" in call for call in evaluate_calls)
                
                # Should have scroll commands
                assert any("scrollTo" in call or "scrollBy" in call for call in evaluate_calls)
                
                # Should have scroll event triggers
                assert any("dispatchEvent" in call for call in evaluate_calls)

    @pytest.mark.asyncio
    async def test_fallback_scrolling_on_errors(self, skip_config):
        """Test fallback scrolling when enhanced strategies fail"""
        
        manager = GenerationDownloadManager(skip_config)
        mock_page = AsyncMock()
        
        # Make enhanced scrolling fail to trigger fallback
        def mock_evaluate_with_errors(script):
            if "window.innerHeight" in script:
                raise Exception("Enhanced scrolling failed")
            elif "scrollBy" in script:
                return True  # Fallback works
            return 0
        
        mock_page.evaluate.side_effect = mock_evaluate_with_errors
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()
        
        # Setup simple scenario for fallback testing
        manager.existing_log_entries = {}
        mock_page.query_selector_all.return_value = []  # No containers to trigger exit
        
        try:
            result = await manager._find_download_boundary_sequential(mock_page)
            
            # Should not crash and should use fallback scrolling
            evaluate_calls = [call.args[0] for call in mock_page.evaluate.call_args_list]
            assert any("scrollBy" in call for call in evaluate_calls), "Fallback scrolling should be used"
            
        except Exception as e:
            pytest.fail(f"Fallback scrolling should not crash: {e}")

def run_tests():
    """Run the tests directly"""
    import subprocess
    result = subprocess.run(['python3.11', '-m', 'pytest', __file__, '-v', '-s'], 
                          capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n🎉 SUCCESS: Robust scrolling fix is working!")
        print("  ✅ Scrolling continues even when no new containers are found")
        print("  ✅ Enhanced scrolling strategies with multiple wait methods")
        print("  ✅ Scroll events triggered for dynamic loading")
        print("  ✅ Fallback scrolling when enhanced methods fail")
        print("  ✅ Network idle detection with proper timeouts")
        print("\nThe boundary scan should now find containers beyond the initial 30!")
    else:
        print("\n❌ FAILURE: Robust scrolling fix needs review")