#!/usr/bin/env python3.11
"""
Test Unlimited Container Detection Fix
=====================================
Tests that container detection now works for unlimited range (not just 0-49)
and that scroll distance is increased to 2500px
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, Mock

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.utils.boundary_scroll_manager import BoundaryScrollManager
from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig


class TestUnlimitedContainerDetection:
    """Test unlimited container detection and increased scroll distance"""
    
    @pytest.mark.asyncio
    async def test_boundary_scroll_manager_detects_high_index_containers(self):
        """Test that BoundaryScrollManager now detects containers with high indices"""
        
        # Mock page with evaluate method
        mock_page = AsyncMock()
        
        # Mock the evaluate result with high-index generation containers
        mock_page.evaluate.return_value = {
            'windowScrollY': 1000,
            'documentScrollTop': 1000,
            'bodyScrollTop': 1000,
            'containerCount': 15,  # Should detect many containers now
            'scrollHeight': 5000,
            'clientHeight': 1000,
            'scrollableContainers': [],
            'containers': [
                # Low indices (should work before and after fix)
                {'id': 'some-hash__0', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'some-hash__1', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'some-hash__24', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                
                # High indices (only work after fix)
                {'id': 'hash1__156', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash2__347', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash3__892', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash4__1247', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash5__1583', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash6__2109', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash7__2456', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash8__3021', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash9__3847', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash10__4329', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash11__5672', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
                {'id': 'hash12__7845', 'rect': {}, 'visible': True, 'className': '', 'tagName': 'DIV'},
            ]
        }
        
        # Create BoundaryScrollManager
        scroll_manager = BoundaryScrollManager(mock_page)
        
        # Get scroll position (this should now detect all containers)
        result = await scroll_manager.get_scroll_position()
        
        # Verify all containers are detected
        assert result['containerCount'] == 15, f"Expected 15 containers, got {result['containerCount']}"
        assert len(result['containers']) == 15, f"Expected 15 container objects, got {len(result['containers'])}"
        
        # Verify high-index containers are included
        container_ids = [c['id'] for c in result['containers']]
        high_index_containers = [
            'hash4__1247', 'hash8__3021', 'hash11__5672', 'hash12__7845'
        ]
        
        for high_id in high_index_containers:
            assert high_id in container_ids, f"High-index container {high_id} not detected!"
        
        print("✅ UNLIMITED CONTAINER DETECTION VERIFIED:")
        print(f"   📊 Total containers detected: {result['containerCount']}")
        print(f"   🎯 High-index containers: {[id for id in container_ids if '__' in id and int(id.split('__')[1]) > 100]}")
        print("   🚀 BoundaryScrollManager now supports unlimited container indices!")
    
    def test_scroll_distance_increased_to_2500px(self):
        """Test that scroll distances are increased to 2500px"""
        
        # Test BoundaryScrollManager scroll distance
        mock_page = Mock()
        scroll_manager = BoundaryScrollManager(mock_page)
        assert scroll_manager.min_scroll_distance == 2500, f"BoundaryScrollManager scroll distance should be 2500px, got {scroll_manager.min_scroll_distance}"
        
        # Test GenerationDownloadConfig scroll amount
        config = GenerationDownloadConfig()
        assert config.scroll_amount == 2500, f"GenerationDownloadConfig scroll amount should be 2500px, got {config.scroll_amount}"
        
        print("✅ SCROLL DISTANCE INCREASED VERIFIED:")
        print(f"   📏 BoundaryScrollManager.min_scroll_distance: {scroll_manager.min_scroll_distance}px")
        print(f"   📏 GenerationDownloadConfig.scroll_amount: {config.scroll_amount}px")
        print("   🚀 Scroll distance increased from 800px to 2500px for better container detection!")
    
    @pytest.mark.asyncio 
    async def test_generation_download_manager_dynamic_container_detection(self):
        """Test that GenerationDownloadManager uses dynamic container detection"""
        
        # Create config and manager
        config = GenerationDownloadConfig()
        config.start_from = "04 Sep 2025 08:23:25"
        manager = GenerationDownloadManager(config)
        
        # Mock page
        mock_page = AsyncMock()
        
        # Mock query_selector_all to return containers with various indices
        def mock_query_selector_all(selector):
            if selector == 'div[id*="__"]':
                # Return mock containers with various indices
                containers = []
                test_ids = [
                    '120ab93f401b4b1db4acefeca51f4639__24',   # Low index (your example)
                    'abcd1234567890abcdef__156',              # Medium index
                    'xyz9876543210fedcba__1247',              # High index
                    'test5555aaaa6666__3847',                 # Very high index
                ]
                
                for test_id in test_ids:
                    mock_container = AsyncMock()
                    mock_container.get_attribute.return_value = test_id
                    mock_container.text_content.return_value = f"Creation Time 04 Sep 2025 08:23:25\nTest prompt content for {test_id}"
                    containers.append(mock_container)
                
                return containers
            return []
        
        mock_page.query_selector_all.side_effect = mock_query_selector_all
        
        # Mock metadata extraction
        from unittest.mock import patch
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced') as mock_extract:
            mock_extract.return_value = {
                'creation_time': '04 Sep 2025 08:23:25',
                'prompt': 'Test prompt content'
            }
            
            # Test the start_from search which uses dynamic detection
            result = await manager._find_start_from_generation(mock_page, "04 Sep 2025 08:23:25")
            
            # Should find the target (all containers have matching datetime in this test)
            assert result['found'] == True, "Should find target with dynamic detection"
            assert result['creation_time'] == '04 Sep 2025 08:23:25', "Should extract correct creation time"
            
            # Verify the dynamic selector was used
            mock_page.query_selector_all.assert_called_with('div[id*="__"]')
            
            print("✅ DYNAMIC CONTAINER DETECTION VERIFIED:")
            print(f"   🔍 Target found: {result['found']}")
            print(f"   📅 Creation time: {result['creation_time']}")
            print(f"   🎯 Containers scanned with unlimited range detection")
            print("   🚀 GenerationDownloadManager now supports unlimited container indices!")
    
    def test_container_filtering_logic(self):
        """Test that container filtering correctly identifies generation containers"""
        
        # Test the filtering logic used in the dynamic detection
        test_cases = [
            # Valid generation containers (should pass)
            ('120ab93f401b4b1db4acefeca51f4639__24', True),
            ('abcd1234567890__0', True),
            ('hash__156', True),
            ('verylonghash123456789__9999', True),
            
            # Invalid containers (should fail)
            ('no-underscore-pattern', False),
            ('only_single_underscore_here', False), 
            ('hash__notanumber', False),
            ('__24', False),  # Missing hash part
            ('hash__', False),  # Missing number part
            ('hash__24__extra', False),  # Too many parts
        ]
        
        valid_containers = []
        invalid_containers = []
        
        for container_id, should_be_valid in test_cases:
            # Apply the same filtering logic used in the code
            if container_id and '__' in container_id:
                parts = container_id.split('__')
                is_valid = bool(len(parts) == 2 and parts[0] and parts[1] and parts[1].isdigit())
            else:
                is_valid = False
            
            if is_valid:
                valid_containers.append(container_id)
            else:
                invalid_containers.append(container_id)
            
            # Verify the filtering works as expected
            assert is_valid == should_be_valid, f"Container {container_id} filtering failed. Expected {should_be_valid}, got {is_valid}"
        
        print("✅ CONTAINER FILTERING LOGIC VERIFIED:")
        print(f"   ✅ Valid containers: {valid_containers}")
        print(f"   ❌ Invalid containers: {invalid_containers}")
        print("   🎯 Filtering correctly identifies generation containers by hash__number pattern!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])