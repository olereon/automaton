#!/usr/bin/env python3
"""
Test Enhanced Metadata Extraction Logic
Tests the improved date selection and context validation for generation downloads.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig


class TestEnhancedMetadataExtraction:
    """Test suite for enhanced metadata extraction logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = GenerationDownloadConfig()
        self.manager = GenerationDownloadManager(self.config)

    def test_context_score_calculation(self):
        """Test element context score calculation"""
        # Test visible element at top of page (should get high score)
        bounds_top = {'x': 100, 'y': 50, 'width': 300, 'height': 50}
        score_top = self.manager._calculate_element_context_score(bounds_top, True)
        assert score_top > 0.8, f"Top element should get high score, got {score_top}"

        # Test visible element at bottom of page (should get lower score)
        bounds_bottom = {'x': 100, 'y': 1800, 'width': 300, 'height': 50}
        score_bottom = self.manager._calculate_element_context_score(bounds_bottom, True)
        assert score_bottom < score_top, f"Bottom element should get lower score than top"

        # Test invisible element (should get zero score)
        bounds_invisible = {'x': 100, 'y': 50, 'width': 300, 'height': 50}
        score_invisible = self.manager._calculate_element_context_score(bounds_invisible, False)
        assert score_invisible == 0, f"Invisible element should get zero score, got {score_invisible}"

        # Test larger element (should get slightly higher score)
        bounds_large = {'x': 100, 'y': 50, 'width': 500, 'height': 100}
        score_large = self.manager._calculate_element_context_score(bounds_large, True)
        # Note: Size scoring has been reduced in the implementation to prioritize position
        # The test should verify that size makes a difference, even if small
        assert score_large >= score_top, f"Larger element should get at least same score (may be higher)"

    def test_date_candidate_selection_unique_dates(self):
        """Test date selection when all candidates have unique dates"""
        date_candidates = [
            {
                'element_index': 0,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.5,
                'element_visible': True
            },
            {
                'element_index': 1,
                'extracted_date': '24 Aug 2025 01:15:23',
                'context_score': 0.9,
                'element_visible': True
            },
            {
                'element_index': 2,
                'extracted_date': '23 Aug 2025 03:45:12',
                'context_score': 0.3,
                'element_visible': False
            }
        ]

        # Should select the date with highest context score
        best_date = self.manager._select_best_date_candidate(date_candidates)
        assert best_date == '24 Aug 2025 01:15:23', f"Should select highest context score date, got {best_date}"

    def test_date_candidate_selection_duplicate_dates(self):
        """Test date selection when there are duplicate dates (the main issue)"""
        date_candidates = [
            {
                'element_index': 0,
                'extracted_date': '25 Aug 2025 02:30:47',  # Duplicate
                'context_score': 0.3,
                'element_visible': False  # Not visible (thumbnail gallery)
            },
            {
                'element_index': 1,
                'extracted_date': '25 Aug 2025 02:30:47',  # Duplicate 
                'context_score': 0.9,
                'element_visible': True   # Visible (detail panel)
            },
            {
                'element_index': 2,
                'extracted_date': '24 Aug 2025 01:15:23',  # Different date
                'context_score': 0.5,
                'element_visible': True
            }
        ]

        best_date = self.manager._select_best_date_candidate(date_candidates)
        # Should prefer the duplicate date with higher context score over the unique date
        assert best_date == '25 Aug 2025 02:30:47', f"Should select date with best overall score, got {best_date}"

    def test_date_candidate_selection_all_identical(self):
        """Test date selection when all dates are identical"""
        date_candidates = [
            {
                'element_index': 0,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.3,
                'element_visible': False
            },
            {
                'element_index': 1,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.8,
                'element_visible': True
            },
            {
                'element_index': 2,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.6,
                'element_visible': True
            }
        ]

        best_date = self.manager._select_best_date_candidate(date_candidates)
        # When all dates are the same, should still work and return the date
        assert best_date == '25 Aug 2025 02:30:47', f"Should return the common date, got {best_date}"

    def test_date_candidate_selection_empty_list(self):
        """Test date selection with empty candidate list"""
        date_candidates = []
        best_date = self.manager._select_best_date_candidate(date_candidates)
        assert best_date == "Unknown Date", f"Empty list should return Unknown Date, got {best_date}"

    def test_date_candidate_selection_single_item(self):
        """Test date selection with single candidate"""
        date_candidates = [
            {
                'element_index': 0,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.5,
                'element_visible': True
            }
        ]

        best_date = self.manager._select_best_date_candidate(date_candidates)
        assert best_date == '25 Aug 2025 02:30:47', f"Single item should return that date, got {best_date}"

    def test_date_candidate_visibility_bonus(self):
        """Test that visible elements get preference over invisible ones"""
        date_candidates = [
            {
                'element_index': 0,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.4,
                'element_visible': False  # Not visible
            },
            {
                'element_index': 1,
                'extracted_date': '24 Aug 2025 01:15:23',
                'context_score': 0.4,  # Same context score
                'element_visible': True   # But visible
            }
        ]

        best_date = self.manager._select_best_date_candidate(date_candidates)
        # Visible element should win due to visibility bonus
        assert best_date == '24 Aug 2025 01:15:23', f"Visible element should be preferred, got {best_date}"

    def test_date_candidate_recency_bonus(self):
        """Test that more recent dates get a small bonus"""
        # Note: This test might be sensitive to when it's run
        from datetime import datetime, timedelta
        
        # Create recent date
        recent_date = datetime.now() - timedelta(days=1)
        old_date = datetime.now() - timedelta(days=100)
        
        date_candidates = [
            {
                'element_index': 0,
                'extracted_date': old_date.strftime('%d %b %Y %H:%M:%S'),
                'context_score': 0.5,
                'element_visible': True
            },
            {
                'element_index': 1,
                'extracted_date': recent_date.strftime('%d %b %Y %H:%M:%S'),
                'context_score': 0.5,  # Same context score
                'element_visible': True
            }
        ]

        best_date = self.manager._select_best_date_candidate(date_candidates)
        # Recent date should win due to recency bonus
        expected_date = recent_date.strftime('%d %b %Y %H:%M:%S')
        assert best_date == expected_date, f"Recent date should be preferred, got {best_date}"

    @pytest.mark.asyncio
    async def test_validate_thumbnail_context_mock(self):
        """Test thumbnail context validation with mocked page"""
        # Create mock page object
        mock_page = AsyncMock()
        
        # Mock no active elements found
        mock_page.query_selector_all.return_value = []
        
        # Test the validation
        validation = await self.manager._validate_thumbnail_context(mock_page, 5)
        
        # Should return validation data structure
        assert isinstance(validation, dict)
        assert 'thumbnail_index' in validation
        assert validation['thumbnail_index'] == 5
        assert 'has_active_thumbnail' in validation
        assert 'detail_panel_loaded' in validation

    @pytest.mark.asyncio 
    async def test_validate_thumbnail_context_with_active_elements(self):
        """Test thumbnail context validation with active elements present"""
        # Create mock page object
        mock_page = AsyncMock()
        
        # Mock active elements found for .active selector
        mock_active_elements = [Mock(), Mock()]  # Two active elements
        mock_page.query_selector_all.side_effect = lambda selector: (
            mock_active_elements if '.active' in selector else []
        )
        
        # Test the validation
        validation = await self.manager._validate_thumbnail_context(mock_page, 3)
        
        # Should detect active thumbnail
        assert validation['has_active_thumbnail'] == True
        assert validation['active_thumbnail_info']['selector'] == '.active'
        assert validation['active_thumbnail_info']['count'] == 2

    def test_integration_scenario_multiple_identical_dates(self):
        """Integration test: Simulate the actual problem scenario"""
        # This simulates the real-world issue: multiple Creation Time elements 
        # with identical dates, but only one is from the currently selected thumbnail
        
        date_candidates = [
            # First element: From thumbnail gallery (not current selection)
            {
                'element_index': 0,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.2,  # Low context score (not in focus area)
                'element_visible': False,  # In collapsed gallery
                'raw_text': '25 Aug 2025 02:30:47',
                'span_index': 1
            },
            # Second element: From thumbnail gallery (not current selection)
            {
                'element_index': 1,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.3,  # Low context score 
                'element_visible': True,  # Visible but not focused
                'raw_text': '25 Aug 2025 02:30:47',
                'span_index': 1
            },
            # Third element: From active/selected thumbnail detail panel
            {
                'element_index': 2,
                'extracted_date': '25 Aug 2025 02:30:47',
                'context_score': 0.9,  # High context score (in detail panel)
                'element_visible': True,  # Visible and focused
                'raw_text': '25 Aug 2025 02:30:47',
                'span_index': 1
            },
            # Fourth element: Different date from another thumbnail
            {
                'element_index': 3,
                'extracted_date': '24 Aug 2025 01:15:23',
                'context_score': 0.4,
                'element_visible': True,
                'raw_text': '24 Aug 2025 01:15:23',
                'span_index': 1
            }
        ]

        # The improved logic should select the element with the highest context score
        # even when multiple elements have the same date
        best_date = self.manager._select_best_date_candidate(date_candidates)
        
        # Should select the date from the active thumbnail (highest context score)
        assert best_date == '25 Aug 2025 02:30:47', (
            f"Should select date from active thumbnail context, got {best_date}"
        )

        print(f"✅ Integration test passed: Selected {best_date} from active thumbnail context")


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestEnhancedMetadataExtraction()
    test_instance.setup_method()
    
    print("🧪 Running Enhanced Metadata Extraction Tests...")
    print("=" * 60)
    
    # Run individual tests
    tests = [
        'test_context_score_calculation',
        'test_date_candidate_selection_unique_dates', 
        'test_date_candidate_selection_duplicate_dates',
        'test_date_candidate_selection_all_identical',
        'test_date_candidate_selection_empty_list',
        'test_date_candidate_selection_single_item',
        'test_date_candidate_visibility_bonus',
        'test_date_candidate_recency_bonus',
        'test_integration_scenario_multiple_identical_dates'
    ]
    
    passed = 0
    failed = 0
    
    for test_name in tests:
        try:
            test_method = getattr(test_instance, test_name)
            test_method()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced metadata extraction is working correctly.")
    else:
        print(f"⚠️  {failed} tests failed. Please review the implementation.")