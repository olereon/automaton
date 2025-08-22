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
    thumbnail_selector: str = ".thumbnail-item, .thumsItem"  # Multiple possible selectors
    
    # Button panel and icon-based selectors
    button_panel_selector: str = ".sc-eYHxxX.fmURBt"  # Static button panel selector
    download_icon_href: str = "#icon-icon_tongyong_20px_xiazai"  # Download icon SVG reference
    download_button_index: int = 2  # 3rd button (0-indexed)
    
    # Text-based selectors
    download_no_watermark_text: str = "Download without Watermark"
    
    # Legacy selectors (kept for backward compatibility)
    download_button_selector: str = "[data-spm-anchor-id='a2ty_o02.30365920.0.i1.6daf47258YB5qi']"
    download_no_watermark_selector: str = "[data-spm-anchor-id='a2ty_o02.30365920.0.i2.6daf47258YB5qi']"
    
    generation_date_selector: str = ".sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)"
    prompt_selector: str = ".sc-jJRqov.cxtNJi span[aria-describedby]"
    
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
            
            # Extract generation date with fallback strategies
            try:
                logger.debug(f"Attempting to extract date using selector: {self.config.generation_date_selector}")
                date_element = await page.wait_for_selector(
                    self.config.generation_date_selector, 
                    timeout=5000
                )
                if date_element:
                    date_text = await date_element.text_content()
                    metadata['generation_date'] = date_text.strip() if date_text else "Unknown Date"
                    logger.debug(f"Extracted date: {metadata['generation_date']}")
                else:
                    raise Exception("Date element not found")
            except Exception as e:
                logger.warning(f"Primary date selector failed: {e}")
                
                # Fallback: Look for any element containing "Creation Time"
                try:
                    logger.debug("Trying fallback date extraction...")
                    # Look for the Creation Time container and get the next span
                    creation_time_elements = await page.query_selector_all("*:has-text('Creation Time')")
                    for element in creation_time_elements:
                        parent = element
                        # Try to find the date span in the same container
                        date_spans = await parent.query_selector_all("span.sc-cSMkSB.hUjUPD")
                        if len(date_spans) >= 2:  # First is "Creation Time", second is the date
                            date_text = await date_spans[1].text_content()
                            metadata['generation_date'] = date_text.strip() if date_text else "Unknown Date"
                            logger.debug(f"Extracted date via fallback: {metadata['generation_date']}")
                            break
                    else:
                        metadata['generation_date'] = "Unknown Date"
                except Exception as fallback_e:
                    logger.warning(f"Fallback date extraction failed: {fallback_e}")
                    metadata['generation_date'] = "Unknown Date"
            
            # Extract prompt with fallback strategies  
            try:
                logger.debug(f"Attempting to extract prompt using selector: {self.config.prompt_selector}")
                prompt_element = await page.wait_for_selector(
                    self.config.prompt_selector, 
                    timeout=5000
                )
                if prompt_element:
                    prompt_text = await prompt_element.text_content()
                    metadata['prompt'] = prompt_text.strip() if prompt_text else "Unknown Prompt"
                    logger.debug(f"Extracted prompt: {metadata['prompt'][:100]}...")
                else:
                    raise Exception("Prompt element not found")
            except Exception as e:
                logger.warning(f"Primary prompt selector failed: {e}")
                
                # Fallback: Look for any span with aria-describedby attribute
                try:
                    logger.debug("Trying fallback prompt extraction...")
                    prompt_elements = await page.query_selector_all("span[aria-describedby]")
                    if prompt_elements:
                        # Use the first one that has substantial text content
                        for element in prompt_elements:
                            text = await element.text_content()
                            if text and len(text.strip()) > 20:  # Substantial content
                                metadata['prompt'] = text.strip()
                                logger.debug(f"Extracted prompt via fallback: {metadata['prompt'][:100]}...")
                                break
                        else:
                            metadata['prompt'] = "Unknown Prompt"
                    else:
                        metadata['prompt'] = "Unknown Prompt"
                except Exception as fallback_e:
                    logger.warning(f"Fallback prompt extraction failed: {fallback_e}")
                    metadata['prompt'] = "Unknown Prompt"
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return None
    
    async def find_and_click_download_button(self, page) -> bool:
        """Find and click the download button using multiple strategies"""
        logger.debug("Attempting to find download button...")
        
        # Strategy 1: Try button panel approach (most reliable)
        try:
            logger.debug(f"Strategy 1: Looking for button panel with selector {self.config.button_panel_selector}")
            button_panels = await page.query_selector_all(self.config.button_panel_selector)
            
            for panel in button_panels:
                # Get all span elements with SVG icons
                buttons = await panel.query_selector_all("span[role='img']")
                logger.debug(f"Found {len(buttons)} buttons in panel")
                
                if len(buttons) > self.config.download_button_index:
                    # Click the download button (3rd button, index 2)
                    download_button = buttons[self.config.download_button_index]
                    await download_button.click()
                    logger.info("Successfully clicked download button using panel strategy")
                    return True
        except Exception as e:
            logger.debug(f"Strategy 1 failed: {e}")
        
        # Strategy 2: Try to find by SVG icon reference
        try:
            logger.debug(f"Strategy 2: Looking for SVG with href {self.config.download_icon_href}")
            svg_selector = f"svg use[href='{self.config.download_icon_href}']"
            svg_element = await page.wait_for_selector(svg_selector, timeout=5000)
            if svg_element:
                # Click the parent span element
                parent_span = await svg_element.evaluate_handle("el => el.closest('span[role=\"img\"]')")
                await parent_span.click()
                logger.info("Successfully clicked download button using SVG icon strategy")
                return True
        except Exception as e:
            logger.debug(f"Strategy 2 failed: {e}")
        
        # Strategy 3: Legacy selector (fallback)
        try:
            logger.debug(f"Strategy 3: Using legacy selector {self.config.download_button_selector}")
            await page.click(self.config.download_button_selector, timeout=5000)
            logger.info("Successfully clicked download button using legacy selector")
            return True
        except Exception as e:
            logger.debug(f"Strategy 3 failed: {e}")
        
        logger.error("All strategies failed to find download button")
        return False
    
    async def find_and_click_no_watermark(self, page) -> bool:
        """Find and click the 'Download without Watermark' option"""
        logger.debug("Attempting to find 'Download without Watermark' option...")
        
        # Wait for download options to appear after clicking download button
        await page.wait_for_timeout(2000)
        
        # Strategy 1: Use CSS selector first (highest priority)
        try:
            logger.debug(f"Strategy 1: Using CSS selector {self.config.download_no_watermark_selector}")
            element = await page.wait_for_selector(self.config.download_no_watermark_selector, timeout=3000)
            if element and await element.is_visible():
                await element.click()
                logger.info(f"Successfully clicked 'Download without Watermark' using CSS selector: {self.config.download_no_watermark_selector}")
                return True
        except Exception as e:
            logger.debug(f"CSS selector strategy failed: {e}")
        
        # Strategy 2: Direct text match for 'Download without Watermark'
        try:
            logger.debug("Strategy 2: Looking for exact text 'Download without Watermark'")
            
            # Find all clickable elements that might contain the text
            clickable_selectors = [
                "*:has-text('Download without Watermark')",
                "div:has-text('Download without Watermark')", 
                "span:has-text('Download without Watermark')",
                "button:has-text('Download without Watermark')",
                "a:has-text('Download without Watermark')"
            ]
            
            for selector in clickable_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        await element.click()
                        logger.info(f"Successfully clicked 'Download without Watermark' using text selector: {selector}")
                        return True
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Playwright text selector strategy failed: {e}")
        
        # Strategy 3: Manual element search with exact text matching
        try:
            logger.debug("Strategy 3: Manual element search with exact text matching")
            
            # Get all potentially clickable elements
            elements = await page.query_selector_all("div, span, button, a, p, li, td")
            
            for element in elements:
                try:
                    text_content = await element.text_content()
                    if text_content and 'Download without Watermark' in text_content.strip():
                        # Verify element is visible and clickable
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if is_visible and is_enabled:
                            await element.click()
                            logger.info(f"Successfully clicked 'Download without Watermark' - found text: '{text_content.strip()}'")
                            return True
                        else:
                            logger.debug(f"Found text but element not clickable - visible: {is_visible}, enabled: {is_enabled}")
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Manual search strategy failed: {e}")
        
        # Strategy 4: XPath with exact text match
        try:
            logger.debug("Strategy 4: XPath with exact text match")
            xpath_selectors = [
                "//div[contains(text(), 'Download without Watermark')]",
                "//span[contains(text(), 'Download without Watermark')]", 
                "//button[contains(text(), 'Download without Watermark')]",
                "//a[contains(text(), 'Download without Watermark')]",
                "//*[contains(text(), 'Download without Watermark')]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    element = await page.wait_for_selector(f"xpath={xpath}", timeout=2000)
                    if element and await element.is_visible():
                        await element.click()
                        logger.info(f"Successfully clicked 'Download without Watermark' using XPath: {xpath}")
                        return True
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"XPath strategy failed: {e}")
        
        logger.error("All strategies failed to find 'Download without Watermark' option")
        return False
    
    async def download_single_generation(self, page, thumbnail_index: int) -> bool:
        """Download a single generation and handle all associated tasks"""
        try:
            logger.info(f"Starting download for thumbnail {thumbnail_index}")
            
            # Click on thumbnail to load generation details
            # Try multiple thumbnail selectors
            thumbnail_clicked = False
            for selector in self.config.thumbnail_selector.split(", "):
                try:
                    thumbnail_selector = f"{selector}:nth-child({thumbnail_index + 1})"
                    await page.click(thumbnail_selector, timeout=10000)
                    await page.wait_for_timeout(2000)  # Wait for content to load
                    thumbnail_clicked = True
                    logger.debug(f"Successfully clicked thumbnail using selector: {selector}")
                    break
                except Exception as e:
                    logger.debug(f"Thumbnail selector {selector} failed: {e}")
            
            if not thumbnail_clicked:
                logger.error(f"Failed to click thumbnail {thumbnail_index}")
                return False
            
            # Set up download handling before clicking download button
            download_path = Path(self.config.downloads_folder)
            logger.debug(f"Monitoring download directory: {download_path}")
            
            # Get initial file list
            initial_files = set(download_path.glob('*')) if download_path.exists() else set()
            logger.debug(f"Initial files in directory: {len(initial_files)}")
            
            # Extract metadata before download
            metadata_dict = await self.extract_metadata_from_page(page)
            if not metadata_dict:
                logger.warning(f"Failed to extract metadata for thumbnail {thumbnail_index}, continuing anyway")
                metadata_dict = {'generation_date': 'Unknown', 'prompt': 'Unknown'}
            
            # Get next file ID
            file_id = self.logger.get_next_file_id()
            
            # Start download process
            download_start_time = time.time()
            
            # Set up download event listener
            download_promise = None
            
            def handle_download(download):
                nonlocal download_promise
                download_promise = download
                logger.info(f"Download started: {download.suggested_filename}")
            
            # Add download listener to page
            page.on("download", handle_download)
            
            # Click download button using enhanced strategies
            if not await self.find_and_click_download_button(page):
                logger.error("Failed to click download button")
                page.remove_listener("download", handle_download)
                return False
            
            # Wait for download modal/options to appear and try to find watermark option
            logger.debug("Waiting for download options to appear...")
            await page.wait_for_timeout(1000)
            
            # Try to click download without watermark with more aggressive timing
            watermark_clicked = False
            for attempt in range(3):
                logger.debug(f"Attempt {attempt + 1} to find 'Download without Watermark'")
                
                if await self.find_and_click_no_watermark(page):
                    watermark_clicked = True
                    break
                    
                # Wait a bit more if first attempts fail
                if attempt < 2:
                    await page.wait_for_timeout(1500)
            
            if not watermark_clicked:
                logger.warning("Failed to click 'Download without Watermark' after multiple attempts")
                
                # Check if download started anyway (sometimes download button alone is enough)
                logger.debug("Checking if download started without watermark option...")
                await page.wait_for_timeout(1000)
                
                # Look for download-related elements to see if download is in progress
                download_indicators = [
                    ".download-progress", ".downloading", "[data-downloading]",
                    "text=Downloading", "text=Download started"
                ]
                
                download_started = False
                for indicator in download_indicators:
                    try:
                        element = await page.wait_for_selector(indicator, timeout=1000)
                        if element:
                            logger.info(f"Download appears to have started (found: {indicator})")
                            download_started = True
                            break
                    except:
                        continue
                
                if not download_started:
                    logger.debug("No download indicators found, trying download button again")
                    # Sometimes clicking download button again helps
                    await self.find_and_click_download_button(page)
            else:
                logger.info("Successfully clicked 'Download without Watermark' option")
            
            # Wait longer and check for additional UI elements
            await page.wait_for_timeout(2000)
            
            # Check if any additional confirmation dialogs or buttons appeared
            logger.debug("Checking for any additional confirmation buttons...")
            confirmation_buttons = [
                "button:has-text('Confirm')",
                "button:has-text('Download')", 
                "button:has-text('OK')",
                "button:has-text('Yes')",
                "[role='button']:has-text('Download')",
                ".download-confirm"
            ]
            
            for button_selector in confirmation_buttons:
                try:
                    button = await page.wait_for_selector(button_selector, timeout=2000)
                    if button and await button.is_visible():
                        await button.click()
                        logger.info(f"Clicked additional confirmation button: {button_selector}")
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            # Wait a bit more for download to start
            await page.wait_for_timeout(3000)
            
            # Handle Playwright download if detected
            downloaded_file = None
            if download_promise:
                try:
                    logger.info("Processing Playwright download...")
                    # Define the target path for the download
                    target_filename = f"{file_id}_temp.mp4"
                    target_path = download_path / target_filename
                    
                    # Save the download
                    await download_promise.save_as(str(target_path))
                    downloaded_file = target_path
                    logger.info(f"Download saved via Playwright: {downloaded_file.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to save Playwright download: {e}")
            else:
                logger.debug("No Playwright download event detected")
            
            # Fallback: Try file system detection if Playwright download didn't work
            if not downloaded_file:
                logger.debug("Playwright download not detected, trying file system detection...")
                
                # Try multiple approaches to detect download
                for attempt in range(3):
                    # Method 1: Wait using file manager
                    logger.debug(f"Download detection attempt {attempt + 1}/3")
                    downloaded_file = await self.file_manager.wait_for_download(
                        timeout=15  # Shorter timeout per attempt
                    )
                    
                    if downloaded_file:
                        logger.info(f"Download detected via file manager: {downloaded_file.name}")
                        break
                        
                    # Method 2: Check if any new files appeared in the directory
                    logger.debug("Checking for new files in download directory...")
                    current_files = set(download_path.glob('*')) if download_path.exists() else set()
                    new_files = current_files - initial_files
                    
                    if new_files:
                        # Found new files, use the most recent one
                        downloaded_file = max(new_files, key=lambda f: f.stat().st_mtime)
                        logger.info(f"Found new file via directory scan: {downloaded_file.name}")
                        break
                    
                    # Wait a bit more before next attempt
                    if attempt < 2:
                        logger.debug("No download detected, waiting longer...")
                        await page.wait_for_timeout(5000)
            
            # Clean up download listener
            page.remove_listener("download", handle_download)
            
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