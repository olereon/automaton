#!/usr/bin/env python3.11
"""
Pytest configuration and fixtures for generation download tests
Provides shared test fixtures, mock objects, and utilities
"""

import pytest
import tempfile
import shutil
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationDownloadConfig,
    GenerationDownloadManager,
    GenerationMetadata
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config(temp_dir):
    """Create test configuration"""
    config = GenerationDownloadConfig()
    config.downloads_folder = os.path.join(temp_dir, 'downloads')
    config.logs_folder = os.path.join(temp_dir, 'logs')
    config.duplicate_mode = "skip"
    config.use_exit_scan_strategy = True
    
    # Create directories
    os.makedirs(config.downloads_folder, exist_ok=True)
    os.makedirs(config.logs_folder, exist_ok=True)
    
    return config


@pytest.fixture
def manager(test_config):
    """Create GenerationDownloadManager with test config"""
    return GenerationDownloadManager(test_config)


@pytest.fixture
def sample_log_entries():
    """Sample log entries for testing"""
    return [
        {
            "file_id": "#000000001",
            "generation_date": "30 Aug 2025 05:15:30",
            "prompt": "A serene mountain landscape with snow-capped peaks",
            "download_timestamp": "2025-08-30T05:16:45.123456",
            "file_path": "/downloads/vids/video_001.mp4",
            "original_filename": "temp_download_001.mp4",
            "file_size": 2457600,
            "download_duration": 3.2
        },
        {
            "file_id": "#000000002",
            "generation_date": "30 Aug 2025 05:11:29",
            "prompt": "The camera begins with a tight close-up of the witch's dual-col",
            "download_timestamp": "2025-08-30T05:12:15.654321",
            "file_path": "/downloads/vids/video_002.mp4",
            "original_filename": "temp_download_002.mp4",
            "file_size": 3145728,
            "download_duration": 4.1
        },
        {
            "file_id": "#000000003",
            "generation_date": "30 Aug 2025 05:08:15",
            "prompt": "Urban street art on brick walls with vibrant colors",
            "download_timestamp": "2025-08-30T05:09:30.987654",
            "file_path": "/downloads/vids/video_003.mp4",
            "original_filename": "temp_download_003.mp4",
            "file_size": 1863680,
            "download_duration": 2.8
        }
    ]


@pytest.fixture
def log_file_with_entries(test_config, sample_log_entries):
    """Create log file with sample entries"""
    log_file = os.path.join(test_config.logs_folder, 'generation_downloads.txt')
    
    with open(log_file, 'w') as f:
        for entry in sample_log_entries:
            f.write(json.dumps(entry) + '\n')
            
    return log_file


@pytest.fixture
def mock_page():
    """Create mock Playwright page"""
    page = Mock()
    page.url = AsyncMock(return_value="https://example.com")
    page.goto = AsyncMock(return_value=Mock(status=200))
    page.go_back = AsyncMock(return_value=True)
    page.click = AsyncMock(return_value=True)
    page.query_selector = AsyncMock(return_value=None)
    page.query_selector_all = AsyncMock(return_value=[])
    page.wait_for_load_state = AsyncMock(return_value=True)
    page.evaluate = AsyncMock(return_value=True)
    
    def locator(selector):
        mock_locator = Mock()
        mock_locator.first = Mock(return_value=mock_locator)
        mock_locator.click = AsyncMock(return_value=True)
        mock_locator.count = AsyncMock(return_value=0)
        mock_locator.text_content = AsyncMock(return_value="")
        return mock_locator
    
    page.locator = locator
    
    return page


@pytest.fixture
def mock_generation_containers():
    """Create mock generation containers for testing"""
    containers = []
    
    test_data = [
        {
            "time": "30 Aug 2025 05:20:00",
            "prompt": "Modern cityscape with glass towers",
            "state": "completed"
        },
        {
            "time": "30 Aug 2025 05:15:30", 
            "prompt": "A serene mountain landscape with snow-capped peaks",
            "state": "completed"
        },
        {
            "time": "30 Aug 2025 05:12:45",
            "prompt": "Queuing…",
            "state": "queuing"
        },
        {
            "time": "30 Aug 2025 05:11:29",
            "prompt": "The camera begins with a tight close-up of the witch's dual-col",
            "state": "completed"
        },
        {
            "time": "30 Aug 2025 05:10:15",
            "prompt": "Something went wrong",
            "state": "failed"
        }
    ]
    
    for data in test_data:
        container = Mock()
        container.click = AsyncMock(return_value=True)
        container.query_selector = AsyncMock()
        container.query_selector_all = AsyncMock(return_value=[])
        
        # Mock prompt element
        prompt_elem = Mock()
        prompt_elem.text_content = AsyncMock(return_value=data["prompt"])
        
        # Mock time element  
        time_elem = Mock()
        time_elem.text_content = AsyncMock(return_value=data["time"])
        
        # Configure container queries
        async def query_side_effect(selector, prompt=data["prompt"], time=data["time"]):
            if 'dnESm' in selector or 'prompt' in selector.lower():
                return prompt_elem if prompt != "Queuing…" and prompt != "Something went wrong" else None
            elif 'jGymgu' in selector or 'time' in selector.lower():
                return Mock()  # Time container
            return None
            
        async def query_all_side_effect(selector, time=data["time"]):
            if 'time' in selector.lower() or 'bZTHAM' in selector:
                return [time_elem]
            return []
            
        container.query_selector.side_effect = query_side_effect
        container.query_selector_all.side_effect = query_all_side_effect
        
        containers.append(container)
        
    return containers


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        'generation_date': '30 Aug 2025 05:11:29',
        'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col',
        'file_size': 3145728,
        'duration': 15.5
    }


@pytest.fixture
def test_thumbnails():
    """Sample thumbnail data for testing"""
    return [
        {
            'id': 'thumb_1',
            'metadata': {
                'generation_date': '30 Aug 2025 06:00:00',
                'prompt': 'Brand new content not in logs'
            },
            'has_video': True,
            'is_duplicate': False
        },
        {
            'id': 'thumb_2',
            'metadata': {
                'generation_date': '30 Aug 2025 05:45:00', 
                'prompt': 'Another new generation'
            },
            'has_video': True,
            'is_duplicate': False
        },
        {
            'id': 'thumb_3',
            'metadata': {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col'
            },
            'has_video': True,
            'is_duplicate': True  # Matches sample_log_entries[1]
        },
        {
            'id': 'thumb_4',
            'metadata': {
                'generation_date': '30 Aug 2025 05:08:15',
                'prompt': 'Urban street art on brick walls with vibrant colors'
            },
            'has_video': True,
            'is_duplicate': True  # Matches sample_log_entries[2]
        }
    ]


@pytest.fixture
def checkpoint_data():
    """Checkpoint data for exit-scan-return testing"""
    return {
        'generation_date': '30 Aug 2025 05:11:29',
        'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col',
        'file_id': '#000000002'
    }


class MockPageWithThumbnails:
    """Enhanced mock page with thumbnail navigation capabilities"""
    
    def __init__(self, thumbnails):
        self.thumbnails = thumbnails
        self.current_index = 0
        self.navigation_history = []
        self.clicks = []
        
    async def goto(self, url, **kwargs):
        self.navigation_history.append(('goto', url))
        return Mock(status=200)
        
    async def url(self):
        return "https://example.com/gallery" if self.current_index >= 0 else "https://example.com"
        
    async def go_back(self):
        self.navigation_history.append(('back', None))
        return True
        
    async def click(self, selector, **kwargs):
        self.clicks.append(selector)
        
        if 'next' in selector or 'arrow' in selector:
            if self.current_index < len(self.thumbnails) - 1:
                self.current_index += 1
                
        return True
        
    async def query_selector(self, selector):
        if self.current_index < 0 or self.current_index >= len(self.thumbnails):
            return None
            
        current = self.thumbnails[self.current_index]
        
        if 'prompt' in selector.lower() or 'metadata' in selector.lower():
            elem = Mock()
            elem.text_content = AsyncMock(return_value=current['metadata']['prompt'])
            return elem
        elif 'time' in selector.lower() or 'date' in selector.lower():
            elem = Mock()  
            elem.text_content = AsyncMock(return_value=current['metadata']['generation_date'])
            return elem
            
        return None
        
    async def query_selector_all(self, selector):
        if 'container' in selector and 'create-detail-body' in selector:
            # Return containers for exit-scan-return
            containers = []
            for thumb in self.thumbnails:
                container = Mock()
                container.click = AsyncMock(return_value=True)
                container.query_selector = AsyncMock()
                
                async def query_side_effect(sel, metadata=thumb['metadata']):
                    if 'prompt' in sel.lower() or 'dnESm' in sel:
                        elem = Mock()
                        elem.text_content = AsyncMock(return_value=metadata['prompt'])
                        return elem
                    elif 'time' in sel.lower() or 'jGymgu' in sel:
                        return Mock()
                    return None
                    
                container.query_selector.side_effect = query_side_effect
                containers.append(container)
                
            return containers
            
        return []
        
    def locator(self, selector):
        mock_locator = Mock()
        mock_locator.first = Mock(return_value=mock_locator)
        mock_locator.click = AsyncMock(return_value=True)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.text_content = AsyncMock(return_value="Mock content")
        return mock_locator


@pytest.fixture
def mock_page_with_thumbnails(test_thumbnails):
    """Create enhanced mock page with thumbnail data"""
    return MockPageWithThumbnails(test_thumbnails)


@pytest.fixture
def large_log_file(test_config):
    """Create large log file for performance testing"""
    log_file = os.path.join(test_config.logs_folder, 'large_test.txt')
    
    with open(log_file, 'w') as f:
        for i in range(1000):
            entry = {
                "file_id": f"#000{i:06d}",
                "generation_date": f"30 Aug 2025 {5 + (i % 10):02d}:{10 + (i % 50):02d}:{20 + (i % 40):02d}",
                "prompt": f"Large test prompt {i} with detailed content",
                "download_timestamp": "2025-08-30T05:16:45.123456",
                "file_path": f"/downloads/vids/video_{i:06d}.mp4",
                "original_filename": f"temp_download_{i:06d}.mp4",
                "file_size": 2457600 + i * 1000,
                "download_duration": 3.2 + (i * 0.001)
            }
            f.write(json.dumps(entry) + '\n')
            
    yield log_file
    
    if os.path.exists(log_file):
        os.remove(log_file)


# Test utilities
def assert_valid_metadata(metadata):
    """Assert that metadata object is valid"""
    assert hasattr(metadata, 'file_id')
    assert hasattr(metadata, 'generation_date')
    assert hasattr(metadata, 'prompt')
    assert len(metadata.generation_date) > 0
    assert len(metadata.prompt) > 0


def create_test_entry(file_id, date, prompt):
    """Create test log entry"""
    return {
        "file_id": file_id,
        "generation_date": date,
        "prompt": prompt,
        "download_timestamp": datetime.now().isoformat(),
        "file_path": f"/test/{file_id}.mp4",
        "original_filename": f"temp_{file_id}.mp4",
        "file_size": 2000000,
        "download_duration": 3.0
    }


# Performance test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


# Skip slow tests by default unless specifically requested
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers"""
    if config.getoption("--runslow"):
        return
        
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--runperf", action="store_true", default=False, help="run performance tests"
    )