#!/usr/bin/env python3.11
"""
Test Suite for Boundary Scroll Manager
=====================================
Comprehensive tests for the verified scrolling methods and boundary detection.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.utils.boundary_scroll_manager import BoundaryScrollManager, ScrollResult


class TestBoundaryScrollManager:
    """Test cases for BoundaryScrollManager"""
    
    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page"""
        page = AsyncMock()
        page.evaluate = AsyncMock()
        return page
    
    @pytest.fixture
    def manager(self, mock_page):
        """Create BoundaryScrollManager instance with mocked page"""
        return BoundaryScrollManager(mock_page)
    
    @pytest.mark.asyncio
    async def test_get_scroll_position(self, manager, mock_page):
        """Test scroll position retrieval"""
        # Mock the evaluate response
        mock_response = {
            'windowScrollY': 1000,
            'documentScrollTop': 1000,
            'containerCount': 20,
            'scrollHeight': 5000,
            'clientHeight': 800,
            'containers': [
                {'id': 'gen1', 'rect': {'top': 100, 'bottom': 200}, 'visible': True},
                {'id': 'gen2', 'rect': {'top': 900, 'bottom': 1000}, 'visible': False}
            ]
        }
        mock_page.evaluate.return_value = mock_response
        
        result = await manager.get_scroll_position()
        
        assert result['windowScrollY'] == 1000
        assert result['containerCount'] == 20
        assert len(result['containers']) == 2
        mock_page.evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_new_containers(self, manager, mock_page):
        """Test new container detection"""
        # Mock get_scroll_position to return different container sets
        initial_containers = [
            {'id': 'gen1', 'rect': {'top': 100, 'bottom': 200}, 'visible': True},
            {'id': 'gen2', 'rect': {'top': 300, 'bottom': 400}, 'visible': True}
        ]
        
        # Mock the current state with additional containers
        mock_page.evaluate.return_value = {
            'containers': [
                {'id': 'gen1', 'rect': {'top': 100, 'bottom': 200}, 'visible': True},
                {'id': 'gen2', 'rect': {'top': 300, 'bottom': 400}, 'visible': True},
                {'id': 'gen3', 'rect': {'top': 500, 'bottom': 600}, 'visible': True},  # New
                {'id': 'gen4', 'rect': {'top': 700, 'bottom': 800}, 'visible': True}   # New
            ]
        }
        
        has_new, new_containers = await manager.detect_new_containers(initial_containers)
        
        assert has_new is True
        assert len(new_containers) == 2
        assert {c['id'] for c in new_containers} == {'gen3', 'gen4'}
    
    @pytest.mark.asyncio
    async def test_scroll_method_1_element_scrollintoview(self, manager, mock_page):
        """Test primary scroll method: Element.scrollIntoView()"""
        # Mock initial state
        initial_state = {
            'windowScrollY': 1000,
            'containerCount': 10
        }
        
        # Mock final state
        final_state = {
            'windowScrollY': 3500,  # 2500px scrolled
            'containerCount': 15
        }
        
        # Mock get_scroll_position to return different values on each call
        mock_page.evaluate.side_effect = [
            # First call for initial state
            initial_state,
            # Scroll operation (returns True)
            True,
            # Final call for final state
            final_state
        ]
        
        result = await manager.scroll_method_1_element_scrollintoview(2000)
        
        assert result.method_name == "Element.scrollIntoView()"
        assert result.success is True
        assert result.scroll_distance == 2500  # 3500 - 1000
        assert result.containers_before == 10
        assert result.containers_after == 15
        assert result.new_containers_detected is True
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_scroll_method_2_container_scrolltop(self, manager, mock_page):
        """Test fallback scroll method: container.scrollTop"""
        # Mock initial state
        initial_state = {
            'windowScrollY': 500,
            'containerCount': 8
        }
        
        # Mock final state
        final_state = {
            'windowScrollY': 2600,  # 2100px scrolled
            'containerCount': 12
        }
        
        # Mock get_scroll_position calls
        mock_page.evaluate.side_effect = [
            initial_state,
            True,  # Scroll operation
            final_state
        ]
        
        result = await manager.scroll_method_2_container_scrolltop(2000)
        
        assert result.method_name == "container.scrollTop"
        assert result.success is True
        assert result.scroll_distance == 2100
        assert result.containers_before == 8
        assert result.containers_after == 12
        assert result.new_containers_detected is True
    
    @pytest.mark.asyncio
    async def test_perform_scroll_with_fallback_primary_success(self, manager, mock_page):
        """Test scroll with fallback when primary method succeeds"""
        # Mock successful primary scroll
        with patch.object(manager, 'scroll_method_1_element_scrollintoview') as mock_primary:
            mock_result = ScrollResult("Element.scrollIntoView()")
            mock_result.success = True
            mock_result.scroll_distance = 2200
            mock_primary.return_value = mock_result
            
            result = await manager.perform_scroll_with_fallback(2000)
            
            assert result.method_name == "Element.scrollIntoView()"
            assert result.success is True
            assert manager.total_scrolled_distance == 2200
            assert manager.scroll_attempts == 1
            
            # Fallback should not be called
            mock_primary.assert_called_once_with(2000)
    
    @pytest.mark.asyncio
    async def test_perform_scroll_with_fallback_uses_fallback(self, manager, mock_page):
        """Test scroll with fallback when primary method fails"""
        with patch.object(manager, 'scroll_method_1_element_scrollintoview') as mock_primary, \
             patch.object(manager, 'scroll_method_2_container_scrolltop') as mock_fallback:
            
            # Mock failed primary
            primary_result = ScrollResult("Element.scrollIntoView()")
            primary_result.success = False
            primary_result.scroll_distance = 100  # Too small
            mock_primary.return_value = primary_result
            
            # Mock successful fallback
            fallback_result = ScrollResult("container.scrollTop")
            fallback_result.success = True
            fallback_result.scroll_distance = 2100
            mock_fallback.return_value = fallback_result
            
            result = await manager.perform_scroll_with_fallback(2000)
            
            assert result.method_name == "container.scrollTop"
            assert result.success is True
            assert manager.total_scrolled_distance == 2100
            assert manager.scroll_attempts == 1
            
            mock_primary.assert_called_once()
            mock_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_matches_boundary_criteria(self, manager):
        """Test boundary criteria matching logic"""
        container = {
            'id': 'generation-#000001',
            'text': 'This is an older generation sample',
            'attributes': {
                'data-status': 'completed',
                'data-type': 'image'
            },
            'dataset': {
                'generationId': '000001',
                'status': 'completed'
            }
        }
        
        # Test generation ID pattern matching
        criteria1 = {'generation_id_pattern': '#000001'}
        assert manager._matches_boundary_criteria(container, criteria1) is True
        
        # Test text content matching
        criteria2 = {'text_contains': 'older generation'}
        assert manager._matches_boundary_criteria(container, criteria2) is True
        
        # Test attribute matching
        criteria3 = {'attribute_matches': {'data-status': 'completed'}}
        assert manager._matches_boundary_criteria(container, criteria3) is True
        
        # Test dataset matching
        criteria4 = {'dataset_matches': {'status': 'completed'}}
        assert manager._matches_boundary_criteria(container, criteria4) is True
        
        # Test non-matching criteria
        criteria_no_match = {'generation_id_pattern': '#999999'}
        assert manager._matches_boundary_criteria(container, criteria_no_match) is False
    
    @pytest.mark.asyncio
    async def test_check_end_of_gallery(self, manager, mock_page):
        """Test end of gallery detection"""
        # Mock end reached
        mock_page.evaluate.return_value = True
        
        result = await manager.check_end_of_gallery()
        assert result is True
        
        # Mock end not reached
        mock_page.evaluate.return_value = False
        
        result = await manager.check_end_of_gallery()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_detect_boundary_in_batch(self, manager, mock_page):
        """Test boundary detection in container batch"""
        containers = [
            {'id': 'gen1'},
            {'id': 'gen2'},
            {'id': 'generation-#000001'}  # This should match
        ]
        
        boundary_criteria = {'generation_id_pattern': '#000001'}
        
        # Mock page.evaluate to return container details
        def mock_evaluate(script):
            if 'generation-#000001' in script:
                return {
                    'id': 'generation-#000001',
                    'text': 'Sample boundary generation',
                    'className': 'generation-card',
                    'dataset': {},
                    'attributes': {'data-generation-id': '000001'}
                }
            return None
        
        mock_page.evaluate.side_effect = mock_evaluate
        
        boundary = await manager.detect_boundary_in_batch(containers, boundary_criteria)
        
        assert boundary is not None
        assert boundary['id'] == 'generation-#000001'
    
    @pytest.mark.asyncio
    async def test_scroll_until_boundary_found_success(self, manager, mock_page):
        """Test complete boundary search with successful find"""
        boundary_criteria = {'generation_id_pattern': '#000001'}
        
        with patch.object(manager, 'get_scroll_position') as mock_get_pos, \
             patch.object(manager, 'perform_scroll_with_fallback') as mock_scroll, \
             patch.object(manager, 'detect_new_containers') as mock_detect, \
             patch.object(manager, 'detect_boundary_in_batch') as mock_boundary:
            
            # Mock initial state
            mock_get_pos.return_value = {
                'containers': [{'id': 'gen1'}, {'id': 'gen2'}]
            }
            
            # Mock successful scroll
            scroll_result = ScrollResult("Element.scrollIntoView()")
            scroll_result.success = True
            scroll_result.scroll_distance = 2200
            mock_scroll.return_value = scroll_result
            
            # Mock new containers detected
            new_containers = [{'id': 'generation-#000001'}]
            mock_detect.return_value = (True, new_containers)
            
            # Mock boundary found
            boundary_found = {'id': 'generation-#000001', 'text': 'boundary'}
            mock_boundary.return_value = boundary_found
            
            result = await manager.scroll_until_boundary_found(boundary_criteria)
            
            assert result == boundary_found
            assert manager.scroll_attempts == 1
            assert manager.total_scrolled_distance == 2200
    
    @pytest.mark.asyncio
    async def test_scroll_until_boundary_found_end_reached(self, manager, mock_page):
        """Test boundary search when end of gallery is reached"""
        boundary_criteria = {'generation_id_pattern': '#000001'}
        
        with patch.object(manager, 'get_scroll_position') as mock_get_pos, \
             patch.object(manager, 'perform_scroll_with_fallback') as mock_scroll, \
             patch.object(manager, 'check_end_of_gallery') as mock_end_check:
            
            mock_get_pos.return_value = {'containers': []}
            
            # Mock failed scroll
            scroll_result = ScrollResult("Element.scrollIntoView()")
            scroll_result.success = False
            scroll_result.scroll_distance = 0
            mock_scroll.return_value = scroll_result
            
            # Mock end of gallery reached
            mock_end_check.return_value = True
            
            result = await manager.scroll_until_boundary_found(boundary_criteria)
            
            assert result is None
            mock_end_check.assert_called()
    
    def test_get_scroll_statistics(self, manager):
        """Test scroll statistics reporting"""
        # Set some test values
        manager.total_scrolled_distance = 8400
        manager.scroll_attempts = 4
        manager.min_scroll_distance = 2000
        
        stats = manager.get_scroll_statistics()
        
        assert stats['total_scrolled_distance'] == 8400
        assert stats['scroll_attempts'] == 4
        assert stats['average_scroll_distance'] == 2100  # 8400 / 4
        assert stats['min_scroll_distance'] == 2000


if __name__ == "__main__":
    # Run tests with pytest
    import subprocess
    subprocess.run(["python3.11", "-m", "pytest", __file__, "-v"])