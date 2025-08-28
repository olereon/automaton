#!/usr/bin/env python3
"""
Test queue detection and generation status checking functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig


class MockElement:
    """Mock Playwright element for testing"""
    
    def __init__(self, text_content: str = "", inner_html: str = "", has_thumbnail: bool = False):
        self._text_content = text_content
        self._inner_html = inner_html
        self._has_thumbnail = has_thumbnail
    
    async def text_content(self):
        return self._text_content
    
    async def inner_html(self):
        return self._inner_html
    
    async def query_selector(self, selector: str):
        if 'img' in selector or 'video' in selector or 'thumbnail' in selector:
            return MockElement() if self._has_thumbnail else None
        return None


class MockPage:
    """Mock Playwright page for testing"""
    
    def __init__(self, elements_data: dict):
        self.elements_data = elements_data  # selector -> MockElement data
    
    async def query_selector(self, selector: str):
        if selector in self.elements_data:
            data = self.elements_data[selector]
            return MockElement(
                text_content=data.get('text', ''),
                inner_html=data.get('html', ''),
                has_thumbnail=data.get('thumbnail', False)
            )
        return None


async def test_queue_detection():
    """Test detection of queued generations"""
    print("🔍 Testing queue detection...")
    
    # Create test configuration
    config = GenerationDownloadConfig(
        downloads_folder="/tmp/test",
        logs_folder="/tmp/test"
    )
    
    manager = GenerationDownloadManager(config)
    
    # Test queued generation
    queued_page_data = {
        "div[id$='__1']": {
            'text': 'Image to video Queuing…some other text',
            'thumbnail': False
        }
    }
    
    mock_page = MockPage(queued_page_data)
    status = await manager.check_generation_status(mock_page, "div[id$='__1']")
    
    assert status['status'] == 'queued', f"Expected 'queued' but got '{status['status']}'"
    assert 'Queuing…' in status['reason'], f"Expected 'Queuing…' in reason but got '{status['reason']}'"
    print("✅ Queue detection test passed")


async def test_completed_detection():
    """Test detection of completed generations"""
    print("🔍 Testing completed generation detection...")
    
    config = GenerationDownloadConfig(
        downloads_folder="/tmp/test",
        logs_folder="/tmp/test"
    )
    
    manager = GenerationDownloadManager(config)
    
    # Test completed generation with thumbnail
    completed_page_data = {
        "div[id$='__2']": {
            'text': 'Image to video Creation Time Download 5 seconds',
            'thumbnail': True
        }
    }
    
    mock_page = MockPage(completed_page_data)
    status = await manager.check_generation_status(mock_page, "div[id$='__2']")
    
    assert status['status'] == 'completed', f"Expected 'completed' but got '{status['status']}'"
    print("✅ Completed generation detection test passed")


async def test_failed_detection():
    """Test detection of failed generations"""
    print("🔍 Testing failed generation detection...")
    
    config = GenerationDownloadConfig(
        downloads_folder="/tmp/test",
        logs_folder="/tmp/test"
    )
    
    manager = GenerationDownloadManager(config)
    
    # Test failed generation
    failed_page_data = {
        "div[id$='__3']": {
            'text': 'Something went wrong. Please try again later.',
            'thumbnail': False
        }
    }
    
    mock_page = MockPage(failed_page_data)
    status = await manager.check_generation_status(mock_page, "div[id$='__3']")
    
    assert status['status'] == 'failed', f"Expected 'failed' but got '{status['status']}'"
    assert 'Something went wrong' in status['reason'], f"Expected failure reason but got '{status['reason']}'"
    print("✅ Failed generation detection test passed")


async def test_mixed_page_detection():
    """Test detection of mixed generations on a page"""
    print("🔍 Testing mixed page detection scenario...")
    
    config = GenerationDownloadConfig(
        downloads_folder="/tmp/test",
        logs_folder="/tmp/test"
    )
    
    manager = GenerationDownloadManager(config)
    
    # Simulate a typical page with 10 containers
    mixed_page_data = {
        "div[id$='__1']": {'text': 'Image to video Creation Time Download 5 seconds', 'thumbnail': True},  # completed
        "div[id$='__2']": {'text': 'Image to video Queuing…', 'thumbnail': False},  # queued
        "div[id$='__3']": {'text': 'Image to video Queuing…waiting', 'thumbnail': False},  # queued
        "div[id$='__4']": {'text': 'Something went wrong. Please try again later.', 'thumbnail': False},  # failed
        "div[id$='__5']": {'text': 'Image to video Creation Time Download 3 seconds', 'thumbnail': True},  # completed
        "div[id$='__6']": {'text': 'Image to video Processing...', 'thumbnail': False},  # queued
        "div[id$='__7']": {'text': 'Image to video Creation Time Download 7 seconds', 'thumbnail': True},  # completed
        "div[id$='__8']": {'text': 'Image to video Queuing…', 'thumbnail': False},  # queued
        "div[id$='__9']": {'text': 'Generation failed', 'thumbnail': False},  # failed
        "div[id$='__10']": {'text': 'Image to video Creation Time Download 2 seconds', 'thumbnail': True},  # completed
    }
    
    mock_page = MockPage(mixed_page_data)
    
    # Mock the find_completed_generations_on_page method to use our mock page
    original_method = manager.find_completed_generations_on_page
    
    async def mock_find_completed_generations(page):
        completed_selectors = []
        
        for i in range(1, 11):
            selector = f"div[id$='__{i}']"
            status_info = await manager.check_generation_status(page, selector)
            
            if status_info['status'] == 'completed':
                completed_selectors.append(selector)
        
        return completed_selectors
    
    # Test the detection
    completed_selectors = await mock_find_completed_generations(mock_page)
    
    expected_completed = ["div[id$='__1']", "div[id$='__5']", "div[id$='__7']", "div[id$='__10']"]
    
    assert len(completed_selectors) == 4, f"Expected 4 completed generations but found {len(completed_selectors)}"
    assert set(completed_selectors) == set(expected_completed), f"Expected {expected_completed} but got {completed_selectors}"
    
    print(f"✅ Mixed page detection test passed - found {len(completed_selectors)} completed generations")
    print(f"   Completed: {completed_selectors}")


async def run_all_tests():
    """Run all queue detection tests"""
    print("🚀 Starting queue detection tests...")
    print("=" * 60)
    
    try:
        await test_queue_detection()
        await test_completed_detection()
        await test_failed_detection()
        await test_mixed_page_detection()
        
        print("=" * 60)
        print("🎉 All queue detection tests passed!")
        print("\n📋 Test Results Summary:")
        print("   ✅ Queued generation detection")
        print("   ✅ Completed generation detection")
        print("   ✅ Failed generation detection")
        print("   ✅ Mixed page scenario detection")
        print("\n🎯 Key Benefits:")
        print("   • Skips 'Queuing…' generations automatically")
        print("   • Identifies only completed generations for processing")
        print("   • Handles failed generations gracefully")
        print("   • Processes up to 4 completed generations from initial page")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)