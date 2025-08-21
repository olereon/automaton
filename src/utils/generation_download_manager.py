#!/usr/bin/env python3
"""
Generation Download Manager
Comprehensive system for automating the download of generated content with metadata tracking.
"""

import os
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
import re
from dataclasses import dataclass, asdict

from .download_manager import DownloadManager, DownloadConfig

logger = logging.getLogger(__name__)


@dataclass
class GenerationMetadata:
    """Metadata for a generation download"""
    file_id: str
    generation_date: str
    prompt: str
    download_timestamp: str
    file_path: str
    original_filename: str = ""
    file_size: int = 0
    download_duration: float = 0.0


@dataclass
class GenerationDownloadConfig:
    """Configuration for generation download automation"""
    # Directory paths
    downloads_folder: str = "/home/olereon/workspace/github.com/olereon/automaton/downloads/vids"
    logs_folder: str = "/home/olereon/workspace/github.com/olereon/automaton/logs"
    
    # Selectors for page elements
    completed_task_selector: str = "div[id$='__8']"  # 9th item (index 8)
    thumbnail_container_selector: str = ".thumbnail-container"
    thumbnail_selector: str = ".thumbnail-item"
    download_button_selector: str = "[data-spm-anchor-id='a2ty_o02.30365920.0.i1.6daf47258YB5qi']"
    download_no_watermark_selector: str = "[data-spm-anchor-id='a2ty_o02.30365920.0.i2.6daf47258YB5qi']"
    generation_date_selector: str = ".sc-eWXuyo.gwshYN"
    prompt_selector: str = "span[aria-describedby]"
    
    # Download settings
    max_downloads: int = 50
    download_timeout: int = 120000  # 2 minutes
    verification_timeout: int = 30000  # 30 seconds
    retry_attempts: int = 3
    
    # File management
    log_filename: str = "generation_downloads.txt"
    starting_file_id: int = 1
    id_format: str = "#{:09d}"  # #000000001 format


class GenerationDownloadLogger:
    """Handles logging of generation download metadata"""
    
    def __init__(self, config: GenerationDownloadConfig):
        self.config = config
        self.log_file_path = Path(config.logs_folder) / config.log_filename
        self.ensure_log_directory()
        
    def ensure_log_directory(self):
        """Ensure the logs directory exists"""
        Path(self.config.logs_folder).mkdir(parents=True, exist_ok=True)
        
    def get_next_file_id(self) -> str:
        """Get the next sequential file ID"""
        if not self.log_file_path.exists():
            return self.config.id_format.format(self.config.starting_file_id)
            
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                return self.config.id_format.format(self.config.starting_file_id)
                
            # Find the last file ID in the log
            lines = content.split('\n')
            last_id = self.config.starting_file_id
            
            for line in lines:
                if line.startswith('#'):
                    # Extract number from format like #000000057
                    match = re.match(r'#(\d+)', line)
                    if match:
                        last_id = max(last_id, int(match.group(1)))
                        
            return self.config.id_format.format(last_id + 1)
            
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return self.config.id_format.format(self.config.starting_file_id)
    
    def log_download(self, metadata: GenerationMetadata) -> bool:
        """Log a generation download to the text file"""
        try:
            log_entry = f"{metadata.file_id}\n{metadata.generation_date}\n{metadata.prompt}\n{'=' * 40}\n"
            
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            logger.info(f"Logged download: {metadata.file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log download: {e}")
            return False
    
    def get_download_count(self) -> int:
        """Get the current number of logged downloads"""
        if not self.log_file_path.exists():
            return 0
            
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Count delimiter lines to determine number of entries
            return content.count('=' * 40)
            
        except Exception as e:
            logger.error(f"Error counting downloads: {e}")
            return 0


class GenerationFileManager:
    """Handles file operations for downloaded generations"""
    
    def __init__(self, config: GenerationDownloadConfig):
        self.config = config
        self.downloads_path = Path(config.downloads_folder)
        self.ensure_downloads_directory()
        
    def ensure_downloads_directory(self):
        """Ensure the downloads directory exists"""
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        
    async def wait_for_download(self, timeout: int = 30) -> Optional[Path]:
        """Wait for a new file to appear in downloads folder"""
        initial_files = set(self.downloads_path.glob('*'))
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_files = set(self.downloads_path.glob('*'))
            new_files = current_files - initial_files
            
            if new_files:
                # Return the newest file
                newest_file = max(new_files, key=lambda f: f.stat().st_mtime)
                logger.info(f"New download detected: {newest_file.name}")
                return newest_file
                
            await asyncio.sleep(1)
            
        logger.warning(f"No new download detected within {timeout} seconds")
        return None
    
    def rename_file(self, file_path: Path, new_id: str) -> Optional[Path]:
        """Rename downloaded file with the new ID"""
        try:
            # Extract file extension
            extension = file_path.suffix
            new_filename = f"{new_id}{extension}"
            new_path = file_path.parent / new_filename
            
            # Rename the file
            file_path.rename(new_path)
            logger.info(f"Renamed {file_path.name} to {new_filename}")
            return new_path
            
        except Exception as e:
            logger.error(f"Failed to rename file {file_path}: {e}")
            return None
    
    def verify_file(self, file_path: Path) -> bool:
        """Verify that the downloaded file is valid"""
        try:
            if not file_path.exists():
                return False
                
            # Check file size (should be > 0)
            if file_path.stat().st_size == 0:
                logger.warning(f"Downloaded file is empty: {file_path}")
                return False
                
            # Additional verification can be added here
            # (e.g., file type validation, corruption checks)
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying file {file_path}: {e}")
            return False


class GenerationDownloadManager:
    """Main manager for generation download automation"""
    
    def __init__(self, config: GenerationDownloadConfig):
        self.config = config
        self.logger = GenerationDownloadLogger(config)
        self.file_manager = GenerationFileManager(config)
        
        # Initialize download manager
        download_config = DownloadConfig(
            base_download_path=config.downloads_folder,
            organize_by_date=False,
            organize_by_type=False,
            max_wait_time=config.download_timeout // 1000,
            auto_rename_duplicates=False,
            verify_downloads=True,
            create_download_log=True
        )
        self.download_manager = DownloadManager(download_config)
        
        # State tracking
        self.current_thumbnail_index = 0
        self.downloads_completed = 0
        self.should_stop = False
        
    def should_continue_downloading(self) -> bool:
        """Check if we should continue downloading"""
        if self.should_stop:
            return False
            
        if self.downloads_completed >= self.config.max_downloads:
            logger.info(f"Reached maximum downloads limit: {self.config.max_downloads}")
            return False
            
        return True
    
    def request_stop(self):
        """Request to stop the download process"""
        self.should_stop = True
        logger.info("Stop requested for generation downloads")
    
    async def extract_metadata_from_page(self, page) -> Optional[Dict[str, str]]:
        """Extract generation metadata from the current page"""
        try:
            metadata = {}
            
            # Extract generation date
            try:
                date_element = await page.wait_for_selector(
                    self.config.generation_date_selector, 
                    timeout=5000
                )
                if date_element:
                    metadata['generation_date'] = await date_element.text_content()
            except Exception as e:
                logger.warning(f"Could not extract generation date: {e}")
                metadata['generation_date'] = "Unknown Date"
            
            # Extract prompt
            try:
                prompt_element = await page.wait_for_selector(
                    self.config.prompt_selector, 
                    timeout=5000
                )
                if prompt_element:
                    metadata['prompt'] = await prompt_element.text_content()
            except Exception as e:
                logger.warning(f"Could not extract prompt: {e}")
                metadata['prompt'] = "Unknown Prompt"
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return None
    
    async def download_single_generation(self, page, thumbnail_index: int) -> bool:
        """Download a single generation and handle all associated tasks"""
        try:
            logger.info(f"Starting download for thumbnail {thumbnail_index}")
            
            # Click on thumbnail to load generation details
            thumbnail_selector = f"{self.config.thumbnail_selector}:nth-child({thumbnail_index + 1})"
            try:
                await page.click(thumbnail_selector, timeout=10000)
                await page.wait_for_timeout(2000)  # Wait for content to load
            except Exception as e:
                logger.error(f"Failed to click thumbnail {thumbnail_index}: {e}")
                return False
            
            # Extract metadata before download
            metadata_dict = await self.extract_metadata_from_page(page)
            if not metadata_dict:
                logger.error(f"Failed to extract metadata for thumbnail {thumbnail_index}")
                return False
            
            # Get next file ID
            file_id = self.logger.get_next_file_id()
            
            # Start download process
            download_start_time = time.time()
            
            # Click download button
            try:
                await page.click(self.config.download_button_selector, timeout=10000)
                await page.wait_for_timeout(1000)
            except Exception as e:
                logger.error(f"Failed to click download button: {e}")
                return False
            
            # Click download without watermark
            try:
                await page.click(self.config.download_no_watermark_selector, timeout=10000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                logger.error(f"Failed to click download without watermark: {e}")
                return False
            
            # Wait for download to complete
            downloaded_file = await self.file_manager.wait_for_download(
                timeout=self.config.verification_timeout // 1000
            )
            
            if not downloaded_file:
                logger.error(f"Download did not complete for thumbnail {thumbnail_index}")
                return False
            
            # Verify downloaded file
            if not self.file_manager.verify_file(downloaded_file):
                logger.error(f"Downloaded file verification failed: {downloaded_file}")
                return False
            
            # Rename file with ID
            renamed_file = self.file_manager.rename_file(downloaded_file, file_id)
            if not renamed_file:
                logger.error(f"Failed to rename downloaded file")
                return False
            
            # Create metadata object
            download_duration = time.time() - download_start_time
            metadata = GenerationMetadata(
                file_id=file_id,
                generation_date=metadata_dict.get('generation_date', 'Unknown'),
                prompt=metadata_dict.get('prompt', 'Unknown'),
                download_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                file_path=str(renamed_file),
                original_filename=downloaded_file.name,
                file_size=renamed_file.stat().st_size,
                download_duration=download_duration
            )
            
            # Log the download
            if self.logger.log_download(metadata):
                self.downloads_completed += 1
                logger.info(f"Successfully completed download {self.downloads_completed}: {file_id}")
                return True
            else:
                logger.error(f"Failed to log download for {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in download_single_generation: {e}")
            return False
    
    async def run_download_automation(self, page) -> Dict[str, Any]:
        """Run the complete generation download automation"""
        results = {
            'success': False,
            'downloads_completed': 0,
            'errors': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        try:
            logger.info("Starting generation download automation")
            
            # Navigate to completed tasks (9th item, index 8)
            try:
                await page.click(self.config.completed_task_selector, timeout=15000)
                await page.wait_for_timeout(3000)  # Wait for page to load
                logger.info("Navigated to completed tasks page")
            except Exception as e:
                error_msg = f"Failed to navigate to completed tasks: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Wait for thumbnails to load
            try:
                await page.wait_for_selector(self.config.thumbnail_selector, timeout=15000)
                logger.info("Thumbnails loaded successfully")
            except Exception as e:
                error_msg = f"Thumbnails did not load: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Get total number of thumbnails
            thumbnail_elements = await page.query_selector_all(self.config.thumbnail_selector)
            total_thumbnails = len(thumbnail_elements)
            logger.info(f"Found {total_thumbnails} thumbnails to process")
            
            # Process each thumbnail
            thumbnail_index = 0
            while self.should_continue_downloading() and thumbnail_index < total_thumbnails:
                success = await self.download_single_generation(page, thumbnail_index)
                
                if success:
                    results['downloads_completed'] = self.downloads_completed
                    logger.info(f"Progress: {self.downloads_completed}/{self.config.max_downloads}")
                else:
                    error_msg = f"Failed to download thumbnail {thumbnail_index}"
                    logger.warning(error_msg)
                    results['errors'].append(error_msg)
                
                thumbnail_index += 1
                
                # Small delay between downloads
                await page.wait_for_timeout(2000)
            
            # Set final results
            results['success'] = True
            results['downloads_completed'] = self.downloads_completed
            
            if self.downloads_completed == 0:
                results['success'] = False
                results['errors'].append("No downloads were completed successfully")
            
        except Exception as e:
            error_msg = f"Critical error in download automation: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
        
        finally:
            results['end_time'] = datetime.now().isoformat()
            logger.info(f"Download automation completed. Downloads: {results['downloads_completed']}")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the download manager"""
        return {
            'downloads_completed': self.downloads_completed,
            'current_thumbnail_index': self.current_thumbnail_index,
            'should_stop': self.should_stop,
            'max_downloads': self.config.max_downloads,
            'log_file_path': str(self.logger.log_file_path),
            'downloads_folder': self.config.downloads_folder,
            'total_logged_downloads': self.logger.get_download_count()
        }