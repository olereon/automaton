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


class EnhancedFileNamer:
    """Handles enhanced file naming with descriptive conventions"""
    
    # Media type mappings based on file extensions
    MEDIA_TYPE_MAP = {
        # Video extensions
        'mp4': 'vid', 'avi': 'vid', 'mov': 'vid', 'mkv': 'vid', 'webm': 'vid',
        'wmv': 'vid', 'flv': 'vid', 'mpg': 'vid', 'mpeg': 'vid', 'm4v': 'vid',
        
        # Image extensions  
        'jpg': 'img', 'jpeg': 'img', 'png': 'img', 'gif': 'img', 'bmp': 'img',
        'tiff': 'img', 'tif': 'img', 'webp': 'img', 'svg': 'img', 'ico': 'img',
        
        # Audio extensions
        'mp3': 'aud', 'wav': 'aud', 'flac': 'aud', 'aac': 'aud', 'ogg': 'aud',
        'wma': 'aud', 'm4a': 'aud', 'opus': 'aud', 'aiff': 'aud'
    }
    
    def __init__(self, config: 'GenerationDownloadConfig'):
        self.config = config
    
    def get_media_type(self, file_extension: str) -> str:
        """Determine media type from file extension"""
        ext = file_extension.lower().lstrip('.')
        return self.MEDIA_TYPE_MAP.get(ext, 'file')  # Default to 'file' for unknown types
    
    def parse_creation_date(self, date_string: str) -> str:
        """Parse and format creation date for filename"""
        try:
            if not date_string or date_string == "Unknown Date":
                # Use current timestamp as fallback
                return datetime.now().strftime(self.config.date_format)
            
            # Try to parse common date formats from webpage
            date_formats = [
                "%d %b %Y %H:%M:%S",    # "24 Aug 2025 01:37:01"
                "%Y-%m-%d %H:%M:%S",    # "2025-08-24 01:37:01" 
                "%d/%m/%Y %H:%M:%S",    # "24/08/2025 01:37:01"
                "%m/%d/%Y %H:%M:%S",    # "08/24/2025 01:37:01"
                "%Y-%m-%d",             # "2025-08-24"
                "%d %b %Y",             # "24 Aug 2025"
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_string.strip(), fmt)
                    break
                except ValueError:
                    continue
            
            if parsed_date:
                return parsed_date.strftime(self.config.date_format)
            else:
                logger.warning(f"Could not parse date '{date_string}', using current time")
                return datetime.now().strftime(self.config.date_format)
                
        except Exception as e:
            logger.error(f"Error parsing creation date: {e}")
            return datetime.now().strftime(self.config.date_format)
    
    def generate_filename(self, file_path: Path, creation_date: str = None, 
                         sequence_number: int = None) -> str:
        """Generate descriptive filename based on configuration"""
        try:
            # Get file extension
            extension = file_path.suffix
            
            if not self.config.use_descriptive_naming:
                # Fall back to sequential naming
                if sequence_number is not None:
                    return f"{self.config.id_format.format(sequence_number)}{extension}"
                else:
                    return file_path.name  # Keep original name
            
            # Generate descriptive filename
            media_type = self.get_media_type(extension)
            formatted_date = self.parse_creation_date(creation_date)
            
            # Build filename using template
            filename_base = self.config.naming_format.format(
                media_type=media_type,
                creation_date=formatted_date,
                unique_id=self.config.unique_id
            )
            
            # Add extension
            new_filename = f"{filename_base}{extension}"
            
            # Sanitize filename for filesystem compatibility
            new_filename = self.sanitize_filename(new_filename)
            
            logger.debug(f"Generated descriptive filename: {new_filename}")
            return new_filename
            
        except Exception as e:
            logger.error(f"Error generating filename: {e}")
            # Fallback to original or sequential naming
            if sequence_number is not None:
                return f"{self.config.id_format.format(sequence_number)}{extension}"
            else:
                return file_path.name
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Replace spaces with underscores (optional)
        sanitized = sanitized.replace(' ', '_')
        
        # Limit filename length (most filesystems support 255 chars)
        if len(sanitized) > 200:  # Leave room for extension
            name_part = sanitized.rsplit('.', 1)[0][:190]
            ext_part = sanitized.rsplit('.', 1)[1] if '.' in sanitized else ''
            sanitized = f"{name_part}.{ext_part}" if ext_part else name_part
        
        return sanitized


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
    thumbnail_container_selector: str = ".thumsInner"  # Main thumbnail container
    thumbnail_selector: str = ".thumbnail-item, .thumsItem"  # Multiple possible selectors
    
    # Scrolling configuration
    scroll_batch_size: int = 10  # Number of downloads before scrolling
    scroll_amount: int = 600  # Pixels to scroll each time
    scroll_wait_time: int = 2000  # Wait time after scrolling (ms)
    max_scroll_attempts: int = 5  # Max attempts to find new thumbnails
    scroll_detection_threshold: int = 3  # Min new thumbnails to consider scroll successful
    
    # Button panel and icon-based selectors
    button_panel_selector: str = ".sc-eYHxxX.fmURBt"  # Static button panel selector
    download_icon_href: str = "#icon-icon_tongyong_20px_xiazai"  # Download icon SVG reference
    download_button_index: int = 2  # 3rd button (0-indexed)
    
    # Text-based landmark selectors (MOST ROBUST)
    image_to_video_text: str = "Image to video"  # Landmark for finding download button
    creation_time_text: str = "Creation Time"    # Landmark for finding date
    prompt_ellipsis_pattern: str = "</span>..."  # Pattern for finding prompt
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
    id_format: str = "#{:09d}"  # #000000001 format (legacy)
    
    # Enhanced naming configuration
    use_descriptive_naming: bool = True  # Enable new naming convention
    unique_id: str = "gen"  # User-defined unique identifier
    naming_format: str = "{media_type}_{creation_date}_{unique_id}"  # Naming template
    date_format: str = "%Y-%m-%d-%H-%M-%S"  # Date format for filename


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
        self.file_namer = EnhancedFileNamer(config)
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
    
    def rename_file(self, file_path: Path, new_id: str = None, creation_date: str = None) -> Optional[Path]:
        """Rename downloaded file with enhanced naming or legacy ID"""
        try:
            if self.config.use_descriptive_naming and creation_date:
                # Use enhanced descriptive naming
                new_filename = self.file_namer.generate_filename(
                    file_path=file_path,
                    creation_date=creation_date
                )
            elif new_id:
                # Use legacy sequential naming
                extension = file_path.suffix
                new_filename = f"{new_id}{extension}"
            else:
                # Keep original filename if no naming method specified
                logger.warning("No naming method specified, keeping original filename")
                return file_path
            
            new_path = file_path.parent / new_filename
            
            # Check if file already exists and create unique name if needed
            counter = 1
            original_new_path = new_path
            while new_path.exists():
                name_part = original_new_path.stem
                extension_part = original_new_path.suffix
                new_path = original_new_path.parent / f"{name_part}_{counter}{extension_part}"
                counter += 1
                
                if counter > 999:  # Safety limit
                    logger.error(f"Could not create unique filename after 999 attempts")
                    return None
            
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
        
        # Scrolling state
        self.visible_thumbnails_cache = []  # Cache of currently visible thumbnails
        self.total_thumbnails_seen = 0
        self.current_scroll_position = 0
        self.last_scroll_thumbnail_count = 0
        
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
    
    async def get_visible_thumbnail_identifiers(self, page) -> List[str]:
        """Get unique identifiers for currently visible thumbnails"""
        try:
            # Get all currently visible thumbnail elements
            thumbnail_elements = await page.query_selector_all(f"{self.config.thumbnail_container_selector} {self.config.thumbnail_selector}")
            
            identifiers = []
            for element in thumbnail_elements:
                try:
                    # Try to get a unique identifier from the thumbnail
                    # Method 1: Check for data attributes
                    data_id = await element.get_attribute("data-spm-anchor-id")
                    if data_id:
                        identifiers.append(data_id)
                        continue
                    
                    # Method 2: Get image src as unique identifier
                    img_element = await element.query_selector("img")
                    if img_element:
                        img_src = await img_element.get_attribute("src")
                        if img_src:
                            # Extract unique part of the URL (the hash/ID part)
                            if "/framecut/" in img_src:
                                unique_id = img_src.split("/framecut/")[1].split("/")[0]
                                identifiers.append(unique_id)
                                continue
                    
                    # Method 3: Use element index as fallback
                    element_index = len(identifiers)
                    identifiers.append(f"thumb_{element_index}")
                    
                except Exception as e:
                    logger.debug(f"Error getting thumbnail identifier: {e}")
                    continue
            
            logger.debug(f"Found {len(identifiers)} visible thumbnails")
            return identifiers
            
        except Exception as e:
            logger.error(f"Error getting visible thumbnails: {e}")
            return []
    
    async def scroll_thumbnail_gallery(self, page) -> bool:
        """Scroll the thumbnail gallery to reveal more thumbnails"""
        try:
            logger.info("🔄 Scrolling thumbnail gallery to reveal more generations...")
            
            # Get current visible thumbnails before scrolling
            before_scroll_ids = await self.get_visible_thumbnail_identifiers(page)
            before_count = len(before_scroll_ids)
            
            logger.debug(f"Thumbnails before scroll: {before_count}")
            
            # Find the scrollable container
            container_selectors = [
                self.config.thumbnail_container_selector,
                ".thumbnail-container",
                ".gallery-container", 
                ".scroll-container",
                # Fallback to parent containers
                f"{self.config.thumbnail_container_selector} .."
            ]
            
            scrollable_container = None
            for selector in container_selectors:
                try:
                    container = await page.wait_for_selector(selector, timeout=3000)
                    if container:
                        # Check if this element is scrollable
                        is_scrollable = await container.evaluate("""el => {
                            return el.scrollHeight > el.clientHeight || 
                                   el.scrollWidth > el.clientWidth ||
                                   getComputedStyle(el).overflowY === 'scroll' ||
                                   getComputedStyle(el).overflowY === 'auto';
                        }""")
                        
                        if is_scrollable:
                            scrollable_container = container
                            logger.debug(f"Found scrollable container: {selector}")
                            break
                except:
                    continue
            
            if not scrollable_container:
                logger.warning("Could not find scrollable container, trying page scroll")
                # Fallback to page scrolling
                await page.evaluate(f"window.scrollBy(0, {self.config.scroll_amount})")
            else:
                # Scroll the container
                await scrollable_container.evaluate(f"el => el.scrollBy(0, {self.config.scroll_amount})")
            
            # Wait for new content to load
            await page.wait_for_timeout(self.config.scroll_wait_time)
            
            # Check if new thumbnails appeared
            after_scroll_ids = await self.get_visible_thumbnail_identifiers(page)
            after_count = len(after_scroll_ids)
            
            # Find truly new thumbnails (not just moved into view)
            new_thumbnails = [tid for tid in after_scroll_ids if tid not in before_scroll_ids]
            new_count = len(new_thumbnails)
            
            logger.info(f"📊 Scroll result: {before_count} → {after_count} thumbnails ({new_count} new)")
            
            if new_count >= self.config.scroll_detection_threshold:
                self.visible_thumbnails_cache = after_scroll_ids
                self.current_scroll_position += self.config.scroll_amount
                logger.info("✅ Successfully scrolled and found new thumbnails")
                return True
            else:
                logger.warning(f"⚠️ Scroll did not reveal enough new thumbnails (found {new_count}, need {self.config.scroll_detection_threshold})")
                return False
                
        except Exception as e:
            logger.error(f"Error scrolling thumbnail gallery: {e}")
            return False
    
    async def ensure_sufficient_thumbnails(self, page, required_count: int = 1) -> bool:
        """Ensure there are sufficient thumbnails visible for continued processing"""
        try:
            current_thumbnails = await self.get_visible_thumbnail_identifiers(page)
            available_count = len(current_thumbnails)
            
            logger.debug(f"Current thumbnails available: {available_count}, required: {required_count}")
            
            if available_count >= required_count:
                return True
            
            # Try to scroll to get more thumbnails
            scroll_attempts = 0
            while scroll_attempts < self.config.max_scroll_attempts and available_count < required_count:
                scroll_attempts += 1
                logger.info(f"🔄 Scroll attempt {scroll_attempts}/{self.config.max_scroll_attempts} to get more thumbnails")
                
                scroll_success = await self.scroll_thumbnail_gallery(page)
                if not scroll_success:
                    logger.warning(f"Scroll attempt {scroll_attempts} failed")
                    await page.wait_for_timeout(1000)  # Brief wait before retry
                    continue
                
                # Check if we now have enough thumbnails
                current_thumbnails = await self.get_visible_thumbnail_identifiers(page)
                available_count = len(current_thumbnails)
                
                if available_count >= required_count:
                    logger.info(f"✅ Successfully obtained {available_count} thumbnails after {scroll_attempts} scroll attempts")
                    return True
            
            logger.warning(f"⚠️ Could not obtain sufficient thumbnails after {scroll_attempts} attempts (have {available_count}, need {required_count})")
            return available_count > 0  # Return true if we have any thumbnails at all
            
        except Exception as e:
            logger.error(f"Error ensuring sufficient thumbnails: {e}")
            return False
    
    async def extract_metadata_from_page(self, page) -> Optional[Dict[str, str]]:
        """Extract generation metadata from the current page using text-based landmarks"""
        try:
            metadata = {}
            
            # Extract generation date using "Creation Time" text landmark (MOST ROBUST)
            try:
                logger.debug(f"Extracting date using '{self.config.creation_time_text}' text landmark")
                
                # Find elements containing the landmark text
                creation_time_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
                
                date_found = False
                for element in creation_time_elements:
                    try:
                        # Get the parent container
                        parent = await element.evaluate_handle("el => el.parentElement")
                        
                        # Find all spans in the parent
                        spans = await parent.query_selector_all("span")
                        
                        # The date should be in the second span (after "Creation Time")
                        if len(spans) >= 2:
                            date_span = spans[1]
                            date_text = await date_span.text_content()
                            if date_text and date_text.strip() != self.config.creation_time_text:
                                extracted_date = date_text.strip()
                                metadata['generation_date'] = extracted_date
                                logger.debug(f"Extracted date via 'Creation Time' landmark: {extracted_date}")
                                date_found = True
                                break
                    except Exception as inner_e:
                        logger.debug(f"Failed to process Creation Time element: {inner_e}")
                        continue
                
                if not date_found:
                    # Fallback to selector-based approach
                    logger.debug("Trying selector-based date extraction")
                    date_element = await page.wait_for_selector(
                        self.config.generation_date_selector, 
                        timeout=3000
                    )
                    if date_element:
                        date_text = await date_element.text_content()
                        metadata['generation_date'] = date_text.strip() if date_text else "Unknown Date"
                    else:
                        metadata['generation_date'] = "Unknown Date"
                        
            except Exception as e:
                logger.warning(f"Date extraction failed: {e}")
                metadata['generation_date'] = "Unknown Date"
            
            # Extract prompt using "..." pattern landmark (MOST ROBUST)
            try:
                logger.debug(f"Extracting prompt using '{self.config.prompt_ellipsis_pattern}' pattern landmark")
                
                # Find all divs that might contain the prompt
                prompt_containers = await page.query_selector_all("div")
                
                prompt_found = False
                for container in prompt_containers:
                    try:
                        # Get the HTML content
                        html_content = await container.evaluate("el => el.innerHTML")
                        
                        # Check if it contains the pattern
                        if self.config.prompt_ellipsis_pattern in html_content and "aria-describedby" in html_content:
                            # Find the span with aria-describedby
                            prompt_spans = await container.query_selector_all("span[aria-describedby]")
                            
                            for span in prompt_spans:
                                # Try multiple methods to extract text
                                text_content = await span.text_content()
                                inner_text = None
                                inner_html = None
                                
                                try:
                                    inner_text = await span.evaluate("el => el.innerText")
                                    logger.debug(f"innerText length: {len(inner_text) if inner_text else 0} chars")
                                except Exception as e:
                                    logger.debug(f"innerText failed: {e}")
                                
                                try:
                                    inner_html = await span.inner_html()
                                    logger.debug(f"innerHTML length: {len(inner_html)} chars")
                                    
                                    # Try to extract text from HTML by removing tags
                                    import re
                                    html_text = re.sub(r'<[^>]+>', '', inner_html)
                                    logger.debug(f"HTML text extraction length: {len(html_text)} chars")
                                    if html_text:
                                        logger.debug(f"HTML text sample: {html_text[:200]}...")
                                        
                                except Exception as e:
                                    logger.debug(f"innerHTML failed: {e}")
                                
                                # Compare all extraction methods
                                logger.debug(f"text_content length: {len(text_content) if text_content else 0} chars")
                                if text_content:
                                    logger.debug(f"text_content sample: {text_content[:200]}...")
                                
                                # Choose the longest/best extraction method
                                candidates = [
                                    ('text_content', text_content),
                                    ('inner_text', inner_text),
                                    ('html_text', html_text if 'html_text' in locals() else None)
                                ]
                                
                                best_method = None
                                best_text = None
                                max_length = 0
                                
                                for method_name, text in candidates:
                                    if text and len(text.strip()) > max_length:
                                        max_length = len(text.strip())
                                        best_method = method_name
                                        best_text = text.strip()
                                
                                if best_text and len(best_text) > 20:  # Substantial content
                                    full_prompt = best_text
                                    metadata['prompt'] = full_prompt
                                    logger.debug(f"Extracted prompt via '...' pattern using {best_method}: Length {len(full_prompt)} chars")
                                    logger.debug(f"Prompt start: {full_prompt[:100]}...")
                                    
                                    # Log the end of the prompt too
                                    if len(full_prompt) > 100:
                                        logger.debug(f"Prompt ending: ...{full_prompt[-50:]}")
                                    
                                    prompt_found = True
                                    break
                            
                            if prompt_found:
                                break
                                
                    except Exception as inner_e:
                        continue
                
                if not prompt_found:
                    # Try alternative approach: Look for the full prompt in title attribute or data attributes
                    logger.debug("Trying alternative prompt extraction methods")
                    
                    # Method 1: Check for title attributes that might contain the full text
                    try:
                        title_elements = await page.query_selector_all("[title*='camera'], [title*='giant'], [title*='frost']")
                        for element in title_elements:
                            title_text = await element.get_attribute("title")
                            if title_text and len(title_text.strip()) > 102:  # Longer than current truncated version
                                full_prompt = title_text.strip()
                                metadata['prompt'] = full_prompt
                                logger.debug(f"Extracted full prompt from title attribute: Length {len(full_prompt)} chars")
                                prompt_found = True
                                break
                    except Exception as e:
                        logger.debug(f"Title attribute search failed: {e}")
                    
                    # Method 2: Look for aria-label or data attributes
                    if not prompt_found:
                        try:
                            aria_elements = await page.query_selector_all("[aria-label*='camera'], [aria-label*='giant']")
                            for element in aria_elements:
                                aria_text = await element.get_attribute("aria-label")
                                if aria_text and len(aria_text.strip()) > 102:
                                    full_prompt = aria_text.strip()
                                    metadata['prompt'] = full_prompt
                                    logger.debug(f"Extracted full prompt from aria-label: Length {len(full_prompt)} chars")
                                    prompt_found = True
                                    break
                        except Exception as e:
                            logger.debug(f"Aria-label search failed: {e}")
                    
                    # Method 3: Look for the parent element that might contain the full text
                    if not prompt_found:
                        try:
                            logger.debug("Looking for parent elements with full prompt text")
                            # Find spans with aria-describedby and check their parents
                            spans_with_aria = await page.query_selector_all("span[aria-describedby]")
                            for span in spans_with_aria:
                                # Check various parent levels
                                for level in range(1, 4):  # Check 3 levels up
                                    try:
                                        parent_js = "el => " + "el.parentElement." * level + "textContent"
                                        parent_text = await span.evaluate(parent_js)
                                        if parent_text and len(parent_text.strip()) > 102:
                                            full_prompt = parent_text.strip()
                                            metadata['prompt'] = full_prompt
                                            logger.debug(f"Extracted full prompt from parent level {level}: Length {len(full_prompt)} chars")
                                            prompt_found = True
                                            break
                                    except:
                                        continue
                                if prompt_found:
                                    break
                        except Exception as e:
                            logger.debug(f"Parent element search failed: {e}")
                    
                    # Method 4: Check for CSS overflow/truncation and try to get full text
                    if not prompt_found:
                        try:
                            logger.debug("Checking for CSS truncation and attempting to get full text")
                            spans_with_aria = await page.query_selector_all("span[aria-describedby]")
                            for span in spans_with_aria:
                                # Check computed styles for truncation indicators
                                computed_style = await span.evaluate("""el => {
                                    const style = window.getComputedStyle(el);
                                    return {
                                        textOverflow: style.textOverflow,
                                        overflow: style.overflow,
                                        whiteSpace: style.whiteSpace,
                                        maxWidth: style.maxWidth,
                                        width: style.width
                                    };
                                }""")
                                logger.debug(f"Element computed style: {computed_style}")
                                
                                # Try to temporarily remove CSS truncation
                                full_text = await span.evaluate("""el => {
                                    // Store original styles
                                    const originalStyles = {
                                        textOverflow: el.style.textOverflow,
                                        overflow: el.style.overflow,
                                        whiteSpace: el.style.whiteSpace,
                                        maxWidth: el.style.maxWidth,
                                        width: el.style.width
                                    };
                                    
                                    // Temporarily remove truncation
                                    el.style.textOverflow = 'clip';
                                    el.style.overflow = 'visible';
                                    el.style.whiteSpace = 'normal';
                                    el.style.maxWidth = 'none';
                                    el.style.width = 'auto';
                                    
                                    // Get the text content
                                    const fullText = el.textContent || el.innerText;
                                    
                                    // Restore original styles
                                    Object.keys(originalStyles).forEach(prop => {
                                        if (originalStyles[prop]) {
                                            el.style[prop] = originalStyles[prop];
                                        } else {
                                            el.style.removeProperty(prop.replace(/([A-Z])/g, '-$1').toLowerCase());
                                        }
                                    });
                                    
                                    return fullText;
                                }""")
                                
                                if full_text and len(full_text.strip()) > 102:
                                    full_prompt = full_text.strip()
                                    metadata['prompt'] = full_prompt
                                    logger.debug(f"Extracted full prompt by removing CSS truncation: Length {len(full_prompt)} chars")
                                    prompt_found = True
                                    break
                        except Exception as e:
                            logger.debug(f"CSS truncation removal failed: {e}")
                    
                    # Fallback to selector-based approach
                    if not prompt_found:
                        logger.debug("Trying selector-based prompt extraction")
                        prompt_element = await page.wait_for_selector(
                            self.config.prompt_selector, 
                            timeout=3000
                        )
                        if prompt_element:
                            prompt_text = await prompt_element.text_content()
                            full_prompt = prompt_text.strip() if prompt_text else "Unknown Prompt"
                            metadata['prompt'] = full_prompt
                            logger.debug(f"Extracted prompt via selector: {full_prompt[:100]}... (Length: {len(full_prompt)} chars)")
                        else:
                            # Last resort: any span with aria-describedby
                            prompt_elements = await page.query_selector_all("span[aria-describedby]")
                            for element in prompt_elements:
                                text = await element.text_content()
                                if text and len(text.strip()) > 20:
                                    full_prompt = text.strip()
                                    metadata['prompt'] = full_prompt
                                    logger.debug(f"Extracted prompt via fallback: {full_prompt[:100]}... (Length: {len(full_prompt)} chars)")
                                    break
                            else:
                                metadata['prompt'] = "Unknown Prompt"
                            
            except Exception as e:
                logger.warning(f"Prompt extraction failed: {e}")
                metadata['prompt'] = "Unknown Prompt"
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return None
    
    async def find_and_click_download_button(self, page) -> bool:
        """Find and click the download button using multiple strategies"""
        logger.debug("Attempting to find download button...")
        
        # Strategy 1: Text-based landmark approach using "Image to video" (MOST ROBUST)
        try:
            logger.debug(f"Strategy 1: Using text-based landmark '{self.config.image_to_video_text}' to find download button")
            
            # Find elements containing the landmark text
            image_to_video_elements = await page.query_selector_all(f"span:has-text('{self.config.image_to_video_text}')")
            
            for element in image_to_video_elements:
                try:
                    # Navigate to the parent container (should be the first div)
                    parent_container = await element.evaluate_handle("el => el.closest('.sc-jxKUFb') || el.parentElement.parentElement")
                    
                    # Find the second div that contains the buttons
                    button_divs = await parent_container.query_selector_all("div")
                    
                    if len(button_divs) >= 2:
                        # The second div should contain the 5 button spans
                        button_container = button_divs[1]
                        button_spans = await button_container.query_selector_all("span[role='img']")
                        
                        logger.debug(f"Found {len(button_spans)} button spans in container")
                        
                        if len(button_spans) >= 3:
                            # The download button is the 3rd span (index 2)
                            download_button = button_spans[2]
                            await download_button.click()
                            logger.info("Successfully clicked download button using 'Image to video' text landmark strategy")
                            return True
                except Exception as inner_e:
                    logger.debug(f"Failed to process 'Image to video' element: {inner_e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Text-based landmark strategy failed: {e}")
        
        # Strategy 2: Try button panel approach (fallback)
        try:
            logger.debug(f"Strategy 2: Looking for button panel with selector {self.config.button_panel_selector}")
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
            logger.debug(f"Strategy 2 failed: {e}")
        
        # Strategy 3: Try to find by SVG icon reference
        try:
            logger.debug(f"Strategy 3: Looking for SVG with href {self.config.download_icon_href}")
            svg_selector = f"svg use[href='{self.config.download_icon_href}']"
            svg_element = await page.wait_for_selector(svg_selector, timeout=5000)
            if svg_element:
                # Click the parent span element
                parent_span = await svg_element.evaluate_handle("el => el.closest('span[role=\"img\"]')")
                await parent_span.click()
                logger.info("Successfully clicked download button using SVG icon strategy")
                return True
        except Exception as e:
            logger.debug(f"Strategy 3 failed: {e}")
        
        # Strategy 4: Legacy selector (fallback)
        try:
            logger.debug(f"Strategy 4: Using legacy selector {self.config.download_button_selector}")
            await page.click(self.config.download_button_selector, timeout=5000)
            logger.info("Successfully clicked download button using legacy selector")
            return True
        except Exception as e:
            logger.debug(f"Strategy 4 failed: {e}")
        
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
            
            # Rename file with enhanced naming
            creation_date = metadata_dict.get('generation_date', 'Unknown Date')
            renamed_file = self.file_manager.rename_file(
                downloaded_file, 
                new_id=file_id,  # Legacy fallback
                creation_date=creation_date
            )
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
        """Run the complete generation download automation with intelligent scrolling"""
        results = {
            'success': False,
            'downloads_completed': 0,
            'errors': [],
            'scrolls_performed': 0,
            'total_thumbnails_processed': 0,
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        try:
            logger.info("🚀 Starting generation download automation with infinite scroll support")
            
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
            
            # Wait for initial thumbnails to load
            try:
                await page.wait_for_selector(self.config.thumbnail_selector, timeout=15000)
                logger.info("Initial thumbnails loaded successfully")
            except Exception as e:
                error_msg = f"Initial thumbnails did not load: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # Initialize thumbnail tracking
            self.visible_thumbnails_cache = await self.get_visible_thumbnail_identifiers(page)
            initial_thumbnail_count = len(self.visible_thumbnails_cache)
            logger.info(f"📊 Initial batch: {initial_thumbnail_count} thumbnails visible")
            
            # Main processing loop with intelligent scrolling
            thumbnail_index = 0
            consecutive_failures = 0
            max_consecutive_failures = 5
            
            while self.should_continue_downloading():
                # Check if we need to scroll to get more thumbnails
                if thumbnail_index > 0 and thumbnail_index % self.config.scroll_batch_size == 0:
                    logger.info(f"📥 Completed {thumbnail_index} downloads, checking for more thumbnails...")
                    
                    # Ensure we have sufficient thumbnails for continued processing
                    if not await self.ensure_sufficient_thumbnails(page, required_count=3):
                        logger.warning("⚠️ Could not load more thumbnails, checking if we've reached the end")
                        
                        # Try one more scroll to be sure we've reached the end
                        final_scroll_success = await self.scroll_thumbnail_gallery(page)
                        if final_scroll_success:
                            results['scrolls_performed'] += 1
                            logger.info("✅ Found more thumbnails after final scroll attempt")
                            continue
                        else:
                            logger.info("🏁 Reached the end of available thumbnails")
                            break
                    
                    results['scrolls_performed'] += 1
                    logger.info(f"✅ Successfully scrolled (total scrolls: {results['scrolls_performed']})")
                
                # Get currently visible thumbnails
                current_visible = await self.get_visible_thumbnail_identifiers(page)
                if not current_visible:
                    logger.warning("No thumbnails currently visible")
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("Too many consecutive failures, stopping automation")
                        break
                    await page.wait_for_timeout(2000)
                    continue
                
                # Calculate the actual thumbnail index within the currently visible set
                visible_index = thumbnail_index % len(current_visible)
                
                logger.info(f"🎯 Processing thumbnail {thumbnail_index + 1} (visible index: {visible_index + 1}/{len(current_visible)})")
                
                # Download the current thumbnail
                success = await self.download_single_generation(page, visible_index)
                
                if success:
                    results['downloads_completed'] = self.downloads_completed
                    consecutive_failures = 0  # Reset failure counter on success
                    logger.info(f"✅ Progress: {self.downloads_completed}/{self.config.max_downloads} downloads completed")
                else:
                    error_msg = f"Failed to download thumbnail at visible index {visible_index}"
                    logger.warning(error_msg)
                    results['errors'].append(error_msg)
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(f"❌ Too many consecutive failures ({consecutive_failures}), stopping automation")
                        break
                
                thumbnail_index += 1
                results['total_thumbnails_processed'] = thumbnail_index
                
                # Small delay between downloads
                await page.wait_for_timeout(2000)
                
                # Log progress every 5 downloads
                if thumbnail_index % 5 == 0:
                    logger.info(f"📈 Batch progress: {thumbnail_index} thumbnails processed, {results['downloads_completed']} successful downloads")
            
            # Set final results
            results['success'] = True
            results['downloads_completed'] = self.downloads_completed
            
            if self.downloads_completed == 0:
                results['success'] = False
                results['errors'].append("No downloads were completed successfully")
            
            logger.info(f"🎉 Download automation completed successfully!")
            logger.info(f"📊 Final stats: {results['downloads_completed']} downloads, {results['scrolls_performed']} scrolls, {results['total_thumbnails_processed']} thumbnails processed")
            
        except Exception as e:
            error_msg = f"Critical error in download automation: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
        
        finally:
            results['end_time'] = datetime.now().isoformat()
            logger.info(f"🏁 Download automation session ended. Total downloads: {results['downloads_completed']}")
        
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
            'total_logged_downloads': self.logger.get_download_count(),
            
            # Scrolling status
            'scroll_config': {
                'batch_size': self.config.scroll_batch_size,
                'scroll_amount': self.config.scroll_amount,
                'wait_time': self.config.scroll_wait_time,
                'max_attempts': self.config.max_scroll_attempts,
                'detection_threshold': self.config.scroll_detection_threshold
            },
            'scroll_state': {
                'visible_thumbnails_cached': len(self.visible_thumbnails_cache),
                'total_thumbnails_seen': self.total_thumbnails_seen,
                'current_scroll_position': self.current_scroll_position,
                'last_scroll_thumbnail_count': self.last_scroll_thumbnail_count
            }
        }