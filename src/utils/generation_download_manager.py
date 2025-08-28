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
    """Configuration for generation download automation with optimized prompt extraction"""
    # Directory paths
    downloads_folder: str = "/home/olereon/workspace/github.com/olereon/automaton/downloads/vids"
    logs_folder: str = "/home/olereon/workspace/github.com/olereon/automaton/logs"
    
    # Selectors for page elements
    completed_task_selector: str = "div[id$='__8']"  # 9th item (index 8)
    thumbnail_container_selector: str = ".thumsInner"  # Main thumbnail container
    thumbnail_selector: str = ".thumsItem, .thumbnail-item, .gallery-item, .generation-item, div[class*='thum'], div[class*='gallery'], img[class*='thumbnail']"  # Multiple possible selectors
    
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
    
    # OPTIMIZED PROMPT EXTRACTION SETTINGS
    extraction_strategy: str = "longest_div"     # Strategy: "longest_div" or "legacy"
    min_prompt_length: int = 150                 # Minimum chars for full prompt detection
    prompt_class_selector: str = "div.sc-dDrhAi.dnESm"  # Target prompt div class
    prompt_indicators: list = None               # Keywords that indicate prompt content
    
    # FAST DOWNLOAD OPTIMIZATION SETTINGS
    stop_on_duplicate: bool = True               # Stop when duplicate creation time found
    duplicate_check_enabled: bool = True         # Enable duplicate detection
    creation_time_comparison: bool = True        # Compare by creation time
    download_completion_detection: bool = True    # Wait for download completion
    fast_navigation_mode: bool = True            # Optimize navigation speed
    
    # Legacy selectors (kept for backward compatibility)
    download_button_selector: str = "[data-spm-anchor-id='a2ty_o02.30365920.0.i1.6daf47258YB5qi']"
    download_no_watermark_selector: str = "[data-spm-anchor-id='a2ty_o02.30365920.0.i2.6daf47258YB5qi']"
    
    generation_date_selector: str = ".sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)"
    prompt_selector: str = ".sc-jJRqov.cxtNJi span[aria-describedby]"
    
    # Download settings
    max_downloads: int = 50
    start_from_thumbnail: int = 1  # Thumbnail number to start from (1-based)
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
    
    def __post_init__(self):
        """Initialize computed fields after dataclass creation"""
        if self.prompt_indicators is None:
            # Default prompt indicators for content detection
            self.prompt_indicators = [
                'camera', 'scene', 'shot', 'frame', 'view', 'angle', 'light', 
                'shows', 'reveals', 'begins', 'starts', 'opens', 'focuses',
                'character', 'person', 'figure', 'subject', 'object'
            ]


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
        self.file_namer = EnhancedFileNamer(config)
        
        # Initialize debug logger
        try:
            from .generation_debug_logger import GenerationDebugLogger
            self.debug_logger = GenerationDebugLogger(config.logs_folder)
            logger.info("🔍 Debug logging enabled")
            
            # Log configuration for debugging
            self.debug_logger.log_configuration({
                "use_descriptive_naming": config.use_descriptive_naming,
                "unique_id": config.unique_id,
                "naming_format": config.naming_format,
                "date_format": config.date_format,
                "max_downloads": config.max_downloads,
                "downloads_folder": config.downloads_folder,
                "creation_time_text": config.creation_time_text,
                "prompt_ellipsis_pattern": config.prompt_ellipsis_pattern
            })
            
        except ImportError:
            self.debug_logger = None
            logger.warning("Debug logger not available")
        
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
        
        # ENHANCED: Robust gallery navigation state with comprehensive tracking
        self.processed_thumbnails = set()  # Track thumbnails processed in this session
        self.visible_thumbnails_cache = []  # Cache of currently visible thumbnails
        self.current_gallery_position = 0  # Absolute position in gallery
        self.total_thumbnails_seen = 0
        self.current_scroll_position = 0
        self.last_scroll_thumbnail_count = 0
        self.gallery_end_detected = False  # Track if we've reached the end
        self.consecutive_same_thumbnails = 0  # Track cycling through same content
        
        # Enhanced state tracking for production reliability
        self.content_signatures = set()  # Track content signatures for duplicate detection
        self.failed_thumbnail_ids = set()  # Track thumbnails that failed processing
        self.scroll_failure_count = 0  # Track consecutive scroll failures
        self.max_scroll_failures = 5  # Maximum scroll failures before ending
        self.processing_start_time = None  # Track session start time
        self.last_successful_download = None  # Track last successful download time
        
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
    
    def scan_existing_files(self) -> set:
        """Scan downloads folder for existing files and extract creation times"""
        if not self.config.duplicate_check_enabled:
            return set()
            
        existing_times = set()
        downloads_path = Path(self.config.downloads_folder)
        
        if not downloads_path.exists():
            logger.info("📁 Downloads folder does not exist yet")
            return existing_times
        
        logger.info(f"🔍 Scanning existing files in: {downloads_path}")
        
        # Pattern to match files with creation time: video_2025-08-27-02-20-06_gen_#000000001.mp4
        import re
        file_pattern = re.compile(r'video_(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})_')
        
        file_count = 0
        for file_path in downloads_path.glob("*.mp4"):
            match = file_pattern.search(file_path.name)
            if match:
                creation_time = match.group(1)
                existing_times.add(creation_time)
                logger.debug(f"   📄 Found: {file_path.name} -> {creation_time}")
                file_count += 1
        
        logger.info(f"✅ Found {file_count} existing files with {len(existing_times)} unique creation times")
        return existing_times
    
    def check_duplicate_exists(self, creation_time: str, existing_files: set) -> bool:
        """Check if a file with the given creation time already exists"""
        if not self.config.duplicate_check_enabled or not creation_time:
            return False
            
        # Convert format if needed: "27 Aug 2025 02:20:06" -> "2025-08-27-02-20-06" 
        try:
            from datetime import datetime
            # Parse: "27 Aug 2025 02:20:06"
            dt = datetime.strptime(creation_time.strip(), "%d %b %Y %H:%M:%S")
            formatted_time = dt.strftime("%Y-%m-%d-%H-%M-%S")
            
            if formatted_time in existing_files:
                logger.warning(f"🚫 Duplicate detected! Creation time {creation_time} -> {formatted_time} already exists")
                return True
                
        except ValueError:
            try:
                # Parse: "2025-08-27-02-20-06" format
                dt = datetime.strptime(creation_time.strip(), "%Y-%m-%d-%H-%M-%S")
                if creation_time in existing_files:
                    logger.warning(f"🚫 Duplicate detected! Creation time {creation_time} already exists")
                    return True
            except ValueError:
                logger.warning(f"⚠️ Could not parse creation time format: {creation_time}")
                
        return False
    
    async def wait_for_download_completion(self, page, expected_filename: str = None, timeout: int = 10000) -> bool:
        """Wait for download to complete by monitoring downloads folder"""
        if not self.config.download_completion_detection:
            # If completion detection is disabled, just wait a fixed time
            await page.wait_for_timeout(2000)
            return True
            
        downloads_path = Path(self.config.downloads_folder)
        start_time = time.time()
        timeout_seconds = timeout / 1000
        
        logger.debug(f"⏳ Waiting for download completion (timeout: {timeout_seconds}s)")
        
        initial_files = set(f.name for f in downloads_path.glob("*.mp4")) if downloads_path.exists() else set()
        
        while (time.time() - start_time) < timeout_seconds:
            if downloads_path.exists():
                current_files = set(f.name for f in downloads_path.glob("*.mp4"))
                new_files = current_files - initial_files
                
                if new_files:
                    new_file = list(new_files)[0]  # Get the first new file
                    logger.info(f"✅ Download completed: {new_file}")
                    return True
            
            await asyncio.sleep(0.5)  # Check every 500ms
        
        logger.warning(f"⏰ Download completion timeout after {timeout_seconds}s")
        return False
    
    async def get_unique_thumbnail_identifier(self, page, thumbnail_element) -> Optional[str]:
        """Get a unique identifier for a thumbnail based on its content with enhanced stability"""
        try:
            # Try multiple methods to get a unique identifier
            identifier_parts = []
            
            # Method 1: Try to get creation time or date from thumbnail (MOST RELIABLE)
            try:
                date_elements = await thumbnail_element.query_selector_all('[class*="time"], [class*="date"], span[title]')
                for elem in date_elements:
                    text = await elem.text_content()
                    if text and any(word in text.lower() for word in ['aug', 'jul', 'sep', '2025', '2024']):
                        identifier_parts.append(f"date:{text.strip()}")
                        break
            except:
                pass
            
            # Method 2: Try to get image source or background image with enhanced matching
            try:
                img_elements = await thumbnail_element.query_selector_all('img')
                for img in img_elements:
                    src = await img.get_attribute('src')
                    if src:
                        # Extract unique part from URL (e.g., filename or ID)
                        import re
                        # Look for long alphanumeric sequences or hashes
                        match = re.search(r'([a-fA-F0-9]{16,}|[a-zA-Z0-9_-]{16,})', src)
                        if match:
                            identifier_parts.append(f"img:{match.group(1)}")
                            break
            except:
                pass
            
            # Method 3: Try to get unique data attributes
            try:
                for attr in ['data-id', 'data-key', 'data-item', 'data-spm-anchor-id', 'id']:
                    value = await thumbnail_element.get_attribute(attr)
                    if value and len(value) > 5:  # Ensure meaningful values
                        identifier_parts.append(f"{attr}:{value}")
                        break
            except:
                pass
            
            # Method 4: Enhanced DOM-based identifier using multiple attributes
            try:
                dom_signature = await thumbnail_element.evaluate("""
                    el => {
                        // Create a stable signature from multiple DOM attributes
                        const parts = [];
                        
                        // Get class signature (sorted for stability)
                        if (el.className && el.className.length > 0) {
                            const classes = el.className.split(' ').filter(c => c.length > 0).sort();
                            if (classes.length > 0) {
                                parts.push(`cls:${classes.join(',')}`);
                            }
                        }
                        
                        // Get index within parent (stable for gallery order)
                        try {
                            const siblings = Array.from(el.parentElement.children);
                            const index = siblings.indexOf(el);
                            if (index >= 0) {
                                parts.push(`idx:${index}`);
                            }
                        } catch(e) {}
                        
                        // Get inner text hash for uniqueness (if present)
                        const text = (el.textContent || '').trim();
                        if (text.length > 0 && text.length < 100) {
                            // Create simple text hash
                            let hash = 0;
                            for (let i = 0; i < text.length; i++) {
                                hash = ((hash << 5) - hash + text.charCodeAt(i)) & 0xffffffff;
                            }
                            parts.push(`txt:${Math.abs(hash)}`);
                        }
                        
                        return parts.join('|');
                    }
                """)
                if dom_signature and len(dom_signature) > 5:
                    identifier_parts.append(f"dom:{dom_signature}")
            except:
                pass
            
            # Method 5: Use position-based fallback ONLY if no other identifier found
            # Position should NOT be primary as it changes after downloads
            if not identifier_parts:
                try:
                    bbox = await thumbnail_element.bounding_box()
                    if bbox:
                        position = f"pos:{int(bbox['x'])}_{int(bbox['y'])}"
                        identifier_parts.append(position)
                except:
                    pass
            
            # Create composite identifier
            if identifier_parts:
                # Use the FIRST (most reliable) identifier, but combine multiple for uniqueness
                if len(identifier_parts) == 1:
                    unique_id = identifier_parts[0]
                else:
                    # Combine top 2 most reliable identifiers
                    unique_id = f"{identifier_parts[0]}#{identifier_parts[1] if len(identifier_parts) > 1 else ''}"
                
                logger.debug(f"Generated enhanced unique ID: {unique_id}")
                return unique_id
            else:
                # Fallback: use element handle reference
                fallback_id = f"elem:{id(thumbnail_element)}"
                logger.warning(f"Using fallback identifier: {fallback_id}")
                return fallback_id
                
        except Exception as e:
            logger.debug(f"Could not get unique identifier for thumbnail: {e}")
            return None
    
    async def refresh_element_reference(self, page, unique_id: str) -> Optional[object]:
        """Refresh a stale element reference by finding it again using unique ID"""
        try:
            logger.debug(f"Refreshing element reference for: {unique_id}")
            
            # Get all current thumbnail elements
            thumbnail_elements = await page.query_selector_all(f"{self.config.thumbnail_container_selector} {self.config.thumbnail_selector}")
            
            for element in thumbnail_elements:
                try:
                    # Get identifier for this element
                    element_id = await self.get_unique_thumbnail_identifier(page, element)
                    
                    # Check if this matches our target
                    if element_id == unique_id:
                        logger.debug(f"Found fresh element reference for: {unique_id}")
                        return element
                        
                except Exception as e:
                    logger.debug(f"Error checking element during refresh: {e}")
                    continue
            
            logger.warning(f"Could not find fresh element reference for: {unique_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error refreshing element reference: {e}")
            return None

    async def get_robust_thumbnail_list(self, page) -> List[Dict[str, Any]]:
        """Get list of thumbnails with unique identifiers and enhanced metadata tracking"""
        try:
            # Get all thumbnail elements with retry on failure
            thumbnail_elements = []
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    thumbnail_elements = await page.query_selector_all(f"{self.config.thumbnail_container_selector} {self.config.thumbnail_selector}")
                    if thumbnail_elements:
                        break
                except Exception as e:
                    logger.debug(f"Retry {retry_count + 1} getting thumbnail elements: {e}")
                    await page.wait_for_timeout(1000)
                    retry_count += 1
            
            if not thumbnail_elements:
                logger.warning("No thumbnail elements found after retries")
                return []
            
            thumbnails = []
            for i, element in enumerate(thumbnail_elements):
                try:
                    # Get unique identifier for this thumbnail
                    unique_id = await self.get_unique_thumbnail_identifier(page, element)
                    
                    if not unique_id:
                        logger.debug(f"Could not generate unique ID for thumbnail {i}")
                        continue
                    
                    # Check if element is visible with retry
                    is_visible = False
                    try:
                        is_visible = await element.is_visible()
                        # Double check visibility with bounding box
                        bbox = await element.bounding_box()
                        if bbox and (bbox['width'] == 0 or bbox['height'] == 0):
                            is_visible = False
                    except:
                        # If visibility check fails, assume not visible
                        is_visible = False
                    
                    # Get bounding box for position tracking
                    bbox = None
                    try:
                        bbox = await element.bounding_box()
                    except:
                        pass
                    
                    thumbnail_info = {
                        'element': element,
                        'unique_id': unique_id,
                        'position': i,
                        'visible': is_visible,
                        'bbox': bbox,
                        'processed': unique_id in self.processed_thumbnails if unique_id else False,
                        'last_seen': datetime.now().isoformat()
                    }
                    
                    thumbnails.append(thumbnail_info)
                    
                except Exception as e:
                    logger.debug(f"Error processing thumbnail {i}: {e}")
                    continue
            
            logger.debug(f"Found {len(thumbnails)} thumbnails ({sum(1 for t in thumbnails if t['visible'])} visible, {sum(1 for t in thumbnails if t['processed'])} processed)")
            return thumbnails
            
        except Exception as e:
            logger.error(f"Error getting robust thumbnail list: {e}")
            return []
    
    async def find_next_unprocessed_thumbnail(self, page) -> Optional[Dict[str, Any]]:
        """Find the next thumbnail that hasn't been processed yet"""
        try:
            thumbnails = await self.get_robust_thumbnail_list(page)
            
            # Find first unprocessed, visible thumbnail
            for thumbnail in thumbnails:
                if thumbnail['visible'] and not thumbnail['processed'] and thumbnail['unique_id']:
                    logger.info(f"🎯 Found next unprocessed thumbnail: {thumbnail['unique_id']} (position {thumbnail['position']})")
                    return thumbnail
            
            # If no unprocessed visible thumbnails, check if we need to scroll
            visible_count = sum(1 for t in thumbnails if t['visible'])
            unprocessed_count = sum(1 for t in thumbnails if not t['processed'] and t['unique_id'])
            
            logger.info(f"📊 Thumbnail status: {visible_count} visible, {unprocessed_count} unprocessed")
            
            if unprocessed_count == 0:
                logger.warning("⚠️ No unprocessed thumbnails found - may have reached end of gallery")
                self.gallery_end_detected = True
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding next unprocessed thumbnail: {e}")
            return None
    
    # NEW: Active-class landmark-based navigation methods
    async def find_active_thumbnail(self, page) -> Optional[object]:
        """Find the currently active (selected) thumbnail using the 'active' class landmark"""
        try:
            # Look for thumbnail container with 'active' class (exclude mask elements)
            active_selector = "div.thumsCou.active"
            active_element = await page.query_selector(active_selector)
            
            if active_element:
                # Get class attribute to verify it contains 'active' and is not a mask
                class_attr = await active_element.get_attribute('class')
                if 'active' in class_attr and '-mask' not in class_attr:
                    logger.debug(f"🎯 Found active thumbnail with classes: {class_attr}")
                    return active_element
                else:
                    logger.debug(f"⚠️ Element found but is invalid: {class_attr}")
            
            # Alternative selector patterns (all excluding masks)
            alternative_selectors = [
                "div[class*='thumsCou'][class*='active']:not([class*='mask'])",
                "div[class~='thumsCou'][class*='active']",
                ".thumsCou.active:not(.thumsCou-mask)"
            ]
            
            for selector in alternative_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.debug(f"✅ Found active thumbnail using alternative selector: {selector}")
                        return element
                except Exception as e:
                    logger.debug(f"Alternative selector {selector} failed: {e}")
                    continue
            
            logger.debug("🔍 No active thumbnail found")
            return None
            
        except Exception as e:
            logger.error(f"Error finding active thumbnail: {e}")
            return None
    
    async def find_next_thumbnail_after_active(self, page, skip_active: bool = True) -> Optional[object]:
        """Find the next thumbnail container after the active one"""
        try:
            # Get all thumbnail containers (excluding mask elements)
            # Use more specific selector to avoid matching 'thumsCou-mask' elements
            all_thumbnail_containers = await page.query_selector_all("div.thumsCou")
            
            # If that doesn't work, try alternative approach with filtering
            if not all_thumbnail_containers:
                logger.debug("🔍 Trying alternative selector for thumbnail containers")
                potential_containers = await page.query_selector_all("div[class*='thumsCou']")
                all_thumbnail_containers = []
                
                # Filter out mask elements
                for container in potential_containers:
                    class_attr = await container.get_attribute('class') or ''
                    # Exclude elements with '-mask' in the class
                    if 'thumsCou' in class_attr and '-mask' not in class_attr:
                        all_thumbnail_containers.append(container)
                
                logger.debug(f"📊 Filtered to {len(all_thumbnail_containers)} actual thumbnail containers (excluded masks)")
            
            if not all_thumbnail_containers:
                logger.debug("🔍 No thumbnail containers found")
                return None
            
            logger.debug(f"📊 Found {len(all_thumbnail_containers)} thumbnail containers total")
            
            # Find the active thumbnail index
            active_index = -1
            for i, container in enumerate(all_thumbnail_containers):
                class_attr = await container.get_attribute('class') or ''
                if 'active' in class_attr:
                    active_index = i
                    logger.debug(f"🎯 Active thumbnail found at index {i} with classes: {class_attr}")
                    break
            
            if active_index == -1:
                logger.debug("⚠️ No active thumbnail found, returning first non-mask container")
                # Return first container that's not a mask
                for container in all_thumbnail_containers:
                    class_attr = await container.get_attribute('class') or ''
                    if '-mask' not in class_attr:
                        logger.debug(f"🎯 Returning first non-mask container with classes: {class_attr}")
                        return container
                return None
            
            # Find next thumbnail after active
            start_index = active_index + 1 if skip_active else active_index
            
            for i in range(start_index, len(all_thumbnail_containers)):
                container = all_thumbnail_containers[i]
                class_attr = await container.get_attribute('class') or ''
                
                # Look for non-active, non-mask thumbnail containers
                if 'thumsCou' in class_attr and 'active' not in class_attr and '-mask' not in class_attr:
                    logger.debug(f"✅ Found next thumbnail container at index {i} with classes: {class_attr}")
                    return container
            
            logger.debug("🏁 No more thumbnail containers found after active one")
            return None
            
        except Exception as e:
            logger.error(f"Error finding next thumbnail after active: {e}")
            return None
    
    async def activate_next_thumbnail(self, page) -> bool:
        """Click on the next thumbnail to make it active (landmark-based navigation)"""
        try:
            # Find the next thumbnail after the currently active one
            next_thumbnail = await self.find_next_thumbnail_after_active(page, skip_active=True)
            
            if not next_thumbnail:
                logger.debug("🔍 No next thumbnail found to activate")
                return False
            
            # Get some info about what we're clicking
            class_attr = await next_thumbnail.get_attribute('class') or ''
            
            # Verify this is not a mask element
            if '-mask' in class_attr:
                logger.warning(f"⚠️ Skipping mask element: {class_attr}")
                return False
            
            logger.info(f"🖱️ Activating next thumbnail with classes: {class_attr}")
            logger.debug(f"Will try multiple click strategies to handle overlay interception")
            
            # Multiple click strategies to handle overlay interception
            click_success = False
            
            # Strategy 1: Click the image inside the container (avoids most overlays)
            try:
                img_element = await next_thumbnail.query_selector('img')
                if img_element:
                    logger.debug("🎨 Strategy 1: Clicking image element inside thumbnail container")
                    await img_element.click(timeout=3000)
                    click_success = True
            except Exception as img_error:
                logger.debug(f"Image click failed: {img_error}")
            
            # Strategy 2: Force click the container (bypasses overlay interception)
            if not click_success:
                try:
                    logger.debug("🔨 Strategy 2: Force clicking thumbnail container")
                    await next_thumbnail.click(force=True, timeout=3000)
                    click_success = True
                except Exception as force_error:
                    logger.debug(f"Force click failed: {force_error}")
            
            # Strategy 3: Use page.click with coordinates (ultimate fallback)
            if not click_success:
                try:
                    logger.debug("🎯 Strategy 3: Clicking at container coordinates")
                    # Get the bounding box and click at center
                    box = await next_thumbnail.bounding_box()
                    if box:
                        center_x = box['x'] + box['width'] / 2
                        center_y = box['y'] + box['height'] / 2
                        await page.click(f"css=body", position={'x': center_x, 'y': center_y}, force=True)
                        click_success = True
                except Exception as coord_error:
                    logger.debug(f"Coordinate click failed: {coord_error}")
            
            # Strategy 4: Dispatch click event directly (last resort)
            if not click_success:
                try:
                    logger.debug("🪄 Strategy 4: Dispatching click event directly")
                    await next_thumbnail.dispatch_event('click')
                    click_success = True
                except Exception as dispatch_error:
                    logger.error(f"All click strategies failed: {dispatch_error}")
                    return False
            
            # Brief wait for the activation to take effect
            await page.wait_for_timeout(500)
            
            # Verify the thumbnail became active
            updated_class = await next_thumbnail.get_attribute('class') or ''
            if 'active' in updated_class:
                logger.info(f"✅ Successfully activated thumbnail - new classes: {updated_class}")
                return True
            else:
                # Sometimes the active class moves to a different element, let's check
                active_element = await self.find_active_thumbnail(page)
                if active_element:
                    logger.info("✅ Thumbnail activation successful (active class detected)")
                    return True
                else:
                    logger.warning(f"⚠️ Click succeeded but thumbnail may not be active: {updated_class}")
                    return True  # Still return True as the click succeeded
                    
        except Exception as e:
            logger.error(f"Error activating next thumbnail: {e}")
            return False
    
    async def navigate_to_next_thumbnail_landmark(self, page) -> bool:
        """Navigate to next thumbnail using active-class landmark approach"""
        try:
            logger.info("🧭 Using landmark-based thumbnail navigation")
            
            # Step 1: Find current active thumbnail (for reference)
            current_active = await self.find_active_thumbnail(page)
            if current_active:
                current_class = await current_active.get_attribute('class') or ''
                logger.debug(f"📍 Current active thumbnail classes: {current_class}")
            else:
                logger.debug("📍 No currently active thumbnail detected")
            
            # Step 2: Activate the next thumbnail
            success = await self.activate_next_thumbnail(page)
            
            if success:
                logger.info("✅ Successfully navigated to next thumbnail using landmark method")
                return True
            else:
                logger.warning("⚠️ Failed to navigate to next thumbnail - may need scrolling")
                return False
                
        except Exception as e:
            logger.error(f"Error in landmark-based navigation: {e}")
            return False
    
    async def preload_gallery_thumbnails(self, page) -> bool:
        """Pre-load the gallery by scrolling to reveal all available thumbnails"""
        try:
            logger.info("🔄 Pre-loading gallery thumbnails with advanced infinite scroll triggers...")
            
            # Track initial state
            initial_count = len(await self.get_visible_thumbnail_identifiers(page))
            logger.info(f"📊 Initial thumbnail count: {initial_count}")
            
            # Diagnose scroll environment
            await self._diagnose_scroll_environment(page)
            
            # Try multiple scroll strategies
            strategies = [
                self._try_enhanced_infinite_scroll_triggers,
                self._try_network_idle_scroll,
                self._try_intersection_observer_scroll,
                self._try_manual_element_scroll
            ]
            
            total_successful_scrolls = 0
            final_count = initial_count
            
            for strategy_idx, strategy in enumerate(strategies):
                logger.info(f"🎯 Trying scroll strategy {strategy_idx + 1}/{len(strategies)}: {strategy.__name__}")
                
                try:
                    strategy_result = await strategy(page)
                    if strategy_result > 0:
                        total_successful_scrolls += strategy_result
                        current_count = len(await self.get_visible_thumbnail_identifiers(page))
                        if current_count > final_count:
                            final_count = current_count
                            logger.info(f"✅ Strategy {strategy_idx + 1} successful: +{strategy_result} scrolls, {current_count} thumbnails")
                            break  # Found working strategy
                    else:
                        logger.debug(f"⚠️ Strategy {strategy_idx + 1} failed or no progress")
                        
                except Exception as e:
                    logger.debug(f"❌ Strategy {strategy_idx + 1} error: {e}")
                    continue
            
            logger.info(f"🎉 Pre-loading complete: {initial_count} → {final_count} thumbnails ({total_successful_scrolls} successful scrolls)")
            
            # Scroll back to top to start from beginning
            if total_successful_scrolls > 0:
                logger.info("⬆️ Scrolling back to top of gallery")
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(1000)
            
            return final_count > initial_count
            
        except Exception as e:
            logger.error(f"Error in gallery pre-loading: {e}")
            return False

    async def _diagnose_scroll_environment(self, page) -> None:
        """Diagnose the scroll environment to understand why infinite scroll may not work"""
        try:
            logger.info("🔍 Diagnosing scroll environment...")
            
            # Check page dimensions and viewport
            viewport_info = await page.evaluate("""() => {
                return {
                    windowHeight: window.innerHeight,
                    windowWidth: window.innerWidth,
                    documentHeight: document.documentElement.scrollHeight,
                    documentWidth: document.documentElement.scrollWidth,
                    scrollY: window.scrollY,
                    scrollX: window.scrollX,
                    maxScrollY: document.documentElement.scrollHeight - window.innerHeight,
                    userAgent: navigator.userAgent,
                    hasIntersectionObserver: 'IntersectionObserver' in window
                }
            }""")
            
            logger.info(f"📱 Viewport: {viewport_info['windowWidth']}x{viewport_info['windowHeight']}")
            logger.info(f"📄 Document: {viewport_info['documentWidth']}x{viewport_info['documentHeight']}")
            logger.info(f"📍 Scroll position: ({viewport_info['scrollX']}, {viewport_info['scrollY']}) / max: {viewport_info['maxScrollY']}")
            logger.info(f"🔬 IntersectionObserver available: {viewport_info['hasIntersectionObserver']}")
            
            # Check for infinite scroll indicators
            scroll_indicators = await page.evaluate("""() => {
                const indicators = [];
                
                // Look for common infinite scroll patterns
                if (document.querySelector('[data-infinite-scroll]')) indicators.push('data-infinite-scroll');
                if (document.querySelector('.infinite-scroll')) indicators.push('.infinite-scroll');
                if (document.querySelector('[data-scroll-loading]')) indicators.push('data-scroll-loading');
                
                // Check for loading indicators
                const loadingElements = document.querySelectorAll('[class*="loading"], [class*="spinner"], [class*="loader"]');
                if (loadingElements.length > 0) indicators.push(`${loadingElements.length} loading elements`);
                
                // Check for scroll event listeners
                const hasScrollListeners = window.addEventListener.toString().includes('scroll') || 
                                         document.addEventListener.toString().includes('scroll');
                                         
                return {
                    indicators,
                    totalElements: document.querySelectorAll('*').length,
                    scripts: document.scripts.length,
                    hasScrollListeners
                };
            }""")
            
            logger.info(f"🎯 Scroll indicators found: {scroll_indicators['indicators']}")
            logger.info(f"📊 Total DOM elements: {scroll_indicators['totalElements']}, Scripts: {scroll_indicators['scripts']}")
            
        except Exception as e:
            logger.debug(f"Error diagnosing scroll environment: {e}")

    async def _try_enhanced_infinite_scroll_triggers(self, page) -> int:
        """Try enhanced infinite scroll triggering with network monitoring"""
        try:
            logger.debug("🚀 Trying enhanced infinite scroll triggers...")
            
            successful_scrolls = 0
            max_attempts = 8
            
            for attempt in range(max_attempts):
                # Get baseline
                before_count = len(await self.get_visible_thumbnail_identifiers(page))
                
                # Multiple scroll triggers in sequence
                await page.evaluate(f"""
                    // Trigger multiple scroll events
                    window.scrollBy(0, {self.config.scroll_amount});
                    
                    // Dispatch manual scroll events
                    window.dispatchEvent(new Event('scroll'));
                    document.dispatchEvent(new Event('scroll'));
                    
                    // Trigger at bottom detection
                    const scrollPercent = (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight;
                    if (scrollPercent > 0.8) {{
                        window.dispatchEvent(new CustomEvent('nearBottom'));
                        document.dispatchEvent(new CustomEvent('loadMore'));
                    }}
                """)
                
                # Wait for network activity
                await page.wait_for_timeout(2000)
                
                # Try additional triggers
                await page.evaluate("""
                    // Simulate user interaction that might trigger infinite scroll
                    const gallery = document.querySelector('.thumsInner, .gallery-container, [class*="gallery"]');
                    if (gallery) {
                        gallery.dispatchEvent(new Event('scroll'));
                        gallery.scrollTop += 100;
                    }
                    
                    // Try intersection observer trigger simulation
                    const lastThumbnail = document.querySelector('.thumsCou:last-child, .thumbnail:last-child');
                    if (lastThumbnail) {
                        lastThumbnail.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                """)
                
                # Wait for potential network requests
                await page.wait_for_timeout(3000)
                
                # Check for new content
                after_count = len(await self.get_visible_thumbnail_identifiers(page))
                new_thumbnails = after_count - before_count
                
                if new_thumbnails > 0:
                    successful_scrolls += 1
                    logger.debug(f"✅ Enhanced trigger {attempt + 1}: +{new_thumbnails} thumbnails")
                else:
                    logger.debug(f"⚠️ Enhanced trigger {attempt + 1}: no new content")
                    break
                    
            return successful_scrolls
            
        except Exception as e:
            logger.debug(f"Enhanced scroll triggers failed: {e}")
            return 0

    async def _try_network_idle_scroll(self, page) -> int:
        """Try scrolling with network idle detection"""
        try:
            logger.debug("🌐 Trying network idle scroll strategy...")
            
            successful_scrolls = 0
            
            for attempt in range(5):
                before_count = len(await self.get_visible_thumbnail_identifiers(page))
                
                # Scroll and wait for network idle
                await page.evaluate(f"window.scrollBy(0, {self.config.scroll_amount})")
                
                try:
                    # Wait for network idle (no requests for 500ms)
                    await page.wait_for_load_state("networkidle", timeout=5000)
                    logger.debug(f"Network idle detected after scroll {attempt + 1}")
                except:
                    # Fallback to timed wait
                    await page.wait_for_timeout(3000)
                
                after_count = len(await self.get_visible_thumbnail_identifiers(page))
                if after_count > before_count:
                    successful_scrolls += 1
                    logger.debug(f"✅ Network idle scroll {attempt + 1}: +{after_count - before_count} thumbnails")
                else:
                    break
                    
            return successful_scrolls
            
        except Exception as e:
            logger.debug(f"Network idle scroll failed: {e}")
            return 0

    async def _try_intersection_observer_scroll(self, page) -> int:
        """Try using intersection observer to trigger loading"""
        try:
            logger.debug("👁️ Trying intersection observer scroll strategy...")
            
            # Set up intersection observer for infinite scroll
            await page.evaluate("""
                if ('IntersectionObserver' in window) {
                    const observer = new IntersectionObserver((entries) => {
                        entries.forEach(entry => {
                            if (entry.isIntersecting) {
                                // Trigger potential load more events
                                window.dispatchEvent(new CustomEvent('loadMore'));
                                document.dispatchEvent(new CustomEvent('infiniteScroll'));
                                
                                // Try to find and trigger any load buttons
                                const loadButton = document.querySelector('[class*="load-more"], [class*="show-more"], [data-load-more]');
                                if (loadButton) loadButton.click();
                            }
                        });
                    }, { threshold: 0.1 });
                    
                    // Observe the last thumbnail
                    const lastThumbnail = document.querySelector('.thumsCou:last-child');
                    if (lastThumbnail) {
                        observer.observe(lastThumbnail);
                        window.scrollToLastThumbnail = () => lastThumbnail.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            """)
            
            successful_scrolls = 0
            
            for attempt in range(3):
                before_count = len(await self.get_visible_thumbnail_identifiers(page))
                
                # Trigger intersection observer
                await page.evaluate("if (window.scrollToLastThumbnail) window.scrollToLastThumbnail()")
                await page.wait_for_timeout(2000)
                
                # Manual scroll as backup
                await page.evaluate(f"window.scrollBy(0, {self.config.scroll_amount})")
                await page.wait_for_timeout(2000)
                
                after_count = len(await self.get_visible_thumbnail_identifiers(page))
                if after_count > before_count:
                    successful_scrolls += 1
                else:
                    break
                    
            return successful_scrolls
            
        except Exception as e:
            logger.debug(f"Intersection observer scroll failed: {e}")
            return 0

    async def _try_manual_element_scroll(self, page) -> int:
        """Try scrolling specific gallery elements"""
        try:
            logger.debug("🎯 Trying manual element scroll strategy...")
            
            # Find gallery containers
            gallery_selectors = [
                ".thumsInner",
                ".gallery-container",
                "[class*='gallery']",
                "[class*='grid']",
                ".content-wrapper"
            ]
            
            successful_scrolls = 0
            
            for selector in gallery_selectors:
                try:
                    containers = await page.query_selector_all(selector)
                    
                    for container in containers:
                        before_count = len(await self.get_visible_thumbnail_identifiers(page))
                        
                        # Try scrolling this specific container
                        await container.evaluate(f"el => el.scrollBy(0, {self.config.scroll_amount})")
                        await page.wait_for_timeout(1500)
                        
                        after_count = len(await self.get_visible_thumbnail_identifiers(page))
                        if after_count > before_count:
                            successful_scrolls += 1
                            logger.debug(f"✅ Element scroll on {selector}: +{after_count - before_count} thumbnails")
                            return successful_scrolls
                            
                except Exception as e:
                    logger.debug(f"Element scroll failed for {selector}: {e}")
                    continue
                    
            return successful_scrolls
            
        except Exception as e:
            logger.debug(f"Manual element scroll failed: {e}")
            return 0

    async def scroll_and_find_more_thumbnails(self, page) -> bool:
        """Scroll the gallery and check for new thumbnails using landmark approach"""
        try:
            logger.info("📜 Scrolling to find more thumbnails...")
            
            # Get thumbnail count before scroll (excluding masks)
            before_containers = await page.query_selector_all("div.thumsCou")
            if not before_containers:
                # Fallback with filtering
                all_elements = await page.query_selector_all("div[class*='thumsCou']")
                before_containers = []
                for elem in all_elements:
                    class_attr = await elem.get_attribute('class') or ''
                    if 'thumsCou' in class_attr and '-mask' not in class_attr:
                        before_containers.append(elem)
            
            before_count = len(before_containers)
            
            # Find scrollable container and scroll
            scrollable_container = await self._find_scrollable_container(page)
            if scrollable_container:
                await scrollable_container.evaluate(f"el => el.scrollBy(0, {self.config.scroll_amount})")
                await page.wait_for_timeout(1000)  # Wait for new content to load
                
                # Check if new thumbnails appeared (excluding masks)
                after_containers = await page.query_selector_all("div.thumsCou")
                if not after_containers:
                    # Fallback with filtering
                    all_elements = await page.query_selector_all("div[class*='thumsCou']")
                    after_containers = []
                    for elem in all_elements:
                        class_attr = await elem.get_attribute('class') or ''
                        if 'thumsCou' in class_attr and '-mask' not in class_attr:
                            after_containers.append(elem)
                
                after_count = len(after_containers)
                
                if after_count > before_count:
                    new_count = after_count - before_count
                    logger.info(f"✅ Scroll successful: {new_count} new thumbnail containers loaded")
                    return True
                else:
                    logger.debug(f"📊 Scroll completed but no new containers ({before_count} → {after_count})")
                    return False
            else:
                logger.warning("⚠️ Could not find scrollable container")
                return False
                
        except Exception as e:
            logger.error(f"Error scrolling for more thumbnails: {e}")
            return False
    
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
    
    async def validate_page_state_changed(self, page, thumbnail_index: int) -> bool:
        """Validate that clicking a thumbnail actually changed the page content"""
        try:
            # Wait for any animations or transitions to complete
            await page.wait_for_timeout(500)
            
            # Check if the creation time element exists (indicates detail view loaded)
            creation_time_visible = await page.is_visible(f"span:has-text('{self.config.creation_time_text}')")
            
            if self.debug_logger:
                self.debug_logger.log_step(thumbnail_index, "PAGE_STATE_VALIDATION", {
                    "creation_time_visible": creation_time_visible,
                    "thumbnail_index": thumbnail_index,
                    "validation_method": "creation_time_visibility"
                })
            
            return creation_time_visible
            
        except Exception as e:
            if self.debug_logger:
                self.debug_logger.log_step(thumbnail_index, "PAGE_STATE_VALIDATION", {
                    "error": str(e),
                    "success": False
                }, success=False, error=str(e))
            
            logger.debug(f"Page state validation failed: {e}")
            return False
    
    async def validate_content_loaded_for_thumbnail(self, page, thumbnail_index: int) -> bool:
        """Ensure that the content for the specific thumbnail is fully loaded"""
        try:
            # Wait for creation time element to be stable
            try:
                await page.wait_for_selector(f"span:has-text('{self.config.creation_time_text}')", timeout=5000)
            except Exception:
                logger.warning(f"Creation time element not found for thumbnail {thumbnail_index}")
            
            # Additional validation: check if prompt content is present
            prompt_elements = await page.query_selector_all("span[aria-describedby]")
            prompt_found = len(prompt_elements) > 0
            
            if self.debug_logger:
                self.debug_logger.log_step(thumbnail_index, "CONTENT_VALIDATION", {
                    "prompt_elements_found": len(prompt_elements),
                    "content_loaded": prompt_found,
                    "thumbnail_index": thumbnail_index
                })
            
            return prompt_found
            
        except Exception as e:
            if self.debug_logger:
                self.debug_logger.log_step(thumbnail_index, "CONTENT_VALIDATION", {
                    "error": str(e),
                    "success": False
                }, success=False, error=str(e))
            
            logger.debug(f"Content validation failed: {e}")
            return False
    
    async def _find_selected_thumbnail_date(self, page, date_candidates: list) -> Optional[str]:
        """Find the date that belongs to the currently selected/active thumbnail using advanced context analysis"""
        try:
            # Strategy 1: Visual indicators and proximity analysis
            # Look for visual state indicators that show which thumbnail is currently active
            selected_indicators = [
                ".selected",
                ".active", 
                ".current",
                ".highlighted",
                "[aria-selected='true']",
                ".thumsItem.selected",
                ".thumbnail-item.active",
                ".current-item",
                ".focus",
                ".focused"
            ]
            
            for indicator in selected_indicators:
                try:
                    selected_elements = await page.query_selector_all(indicator)
                    if selected_elements:
                        # For each selected element, try to find associated date
                        for element in selected_elements:
                            # Look for Creation Time span near this selected element
                            creation_time_near = await element.query_selector("span:has-text('Creation Time')")
                            if creation_time_near:
                                parent = await creation_time_near.evaluate_handle("el => el.parentElement")
                                spans = await parent.query_selector_all("span")
                                if len(spans) >= 2:
                                    date_text = await spans[1].text_content()
                                    if date_text and date_text.strip():
                                        logger.debug(f"Found selected thumbnail date via {indicator}: {date_text.strip()}")
                                        return date_text.strip()
                except Exception:
                    continue
            
            # Strategy 2: Context-based analysis - find the date in the main detail/focus area
            # Look for Creation Time elements that appear in singular, focused contexts
            try:
                focus_selectors = [
                    ".modal-content span:has-text('Creation Time')",
                    ".dialog span:has-text('Creation Time')",  
                    ".popup span:has-text('Creation Time')",
                    ".panel span:has-text('Creation Time')",
                    ".detail span:has-text('Creation Time')",
                    ".main-content span:has-text('Creation Time')",
                    ".content-area span:has-text('Creation Time')"
                ]
                
                for selector in focus_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) == 1:  # Single focused element indicates active content
                        element = elements[0]
                        parent = await element.evaluate_handle("el => el.parentElement")
                        spans = await parent.query_selector_all("span")
                        if len(spans) >= 2:
                            date_text = await spans[1].text_content()
                            if date_text and date_text.strip():
                                logger.debug(f"Found focused date via {selector}: {date_text.strip()}")
                                return date_text.strip()
            except Exception:
                pass
            
            # Strategy 3: Viewport positioning analysis
            # Find the Creation Time element that is most prominently positioned (center, top, etc.)
            try:
                creation_elements = await page.query_selector_all("span:has-text('Creation Time')")
                if len(creation_elements) > 1:
                    best_element = None
                    best_score = -1
                    
                    for element in creation_elements:
                        try:
                            # Get element position and visibility metrics
                            bounds = await element.bounding_box()
                            if not bounds:
                                continue
                            
                            # Score based on position (higher score for more central/prominent positions)
                            viewport = await page.viewport_size()
                            center_x = viewport['width'] / 2
                            center_y = viewport['height'] / 2
                            
                            # Distance from center (closer is better)
                            distance_from_center = ((bounds['x'] + bounds['width']/2 - center_x)**2 + 
                                                   (bounds['y'] + bounds['height']/2 - center_y)**2) ** 0.5
                            
                            # Normalize distance score (lower distance = higher score)
                            distance_score = max(0, 1 - distance_from_center / (max(viewport['width'], viewport['height']) / 2))
                            
                            # Bonus for elements higher on the page (detail areas often at top)
                            top_bonus = max(0, 1 - bounds['y'] / viewport['height']) * 0.3
                            
                            # Bonus for larger elements (more prominent)
                            size_bonus = min(1, (bounds['width'] * bounds['height']) / (viewport['width'] * viewport['height'])) * 0.2
                            
                            total_score = distance_score + top_bonus + size_bonus
                            
                            if total_score > best_score:
                                best_score = total_score
                                best_element = element
                        except Exception:
                            continue
                    
                    if best_element:
                        parent = await best_element.evaluate_handle("el => el.parentElement")
                        spans = await parent.query_selector_all("span")
                        if len(spans) >= 2:
                            date_text = await spans[1].text_content()
                            if date_text and date_text.strip():
                                logger.debug(f"Found best positioned date (score: {best_score:.2f}): {date_text.strip()}")
                                return date_text.strip()
            except Exception as e:
                logger.debug(f"Viewport positioning analysis failed: {e}")
                    
            return None
            
        except Exception as e:
            logger.debug(f"Error finding selected thumbnail date: {e}")
            return None
    
    def _calculate_element_context_score(self, element_bounds, element_visibility: bool) -> float:
        """Calculate a context score for an element based on its position and visibility"""
        score = 0.0
        
        # Visibility is crucial
        if element_visibility:
            score += 0.5
        else:
            return score  # Skip other scoring if not visible
        
        # Position scoring (if bounds are available)
        if element_bounds:
            # Score based on position - prefer elements higher on the page (detail areas)
            y_position = element_bounds.get('y', 0)
            height = element_bounds.get('height', 0)
            
            # Normalize to 0-1 scale (assuming page height of ~2000px)
            normalized_y = max(0, min(1, y_position / 2000))
            
            # Higher elements get better scores (detail content usually at top)
            position_score = max(0, 1 - normalized_y) * 0.3
            score += position_score
            
            # Size scoring - larger elements might be more important  
            width = element_bounds.get('width', 0)
            area = width * height
            if area > 0:
                # Normalize area score (capped at reasonable UI element size)
                size_score = min(0.1, area / 50000)  # More conservative size scoring
                score += size_score
        
        return score
    
    async def _validate_thumbnail_context(self, page, thumbnail_index: int) -> Dict[str, Any]:
        """Validate that we're extracting metadata from the correct thumbnail context"""
        try:
            validation_data = {
                'thumbnail_index': thumbnail_index,
                'has_active_thumbnail': False,
                'active_thumbnail_info': None,
                'detail_panel_loaded': False,
                'metadata_elements_count': 0
            }
            
            # Check if there's a clear active/selected thumbnail
            try:
                active_selectors = ['.selected', '.active', '.current', '.highlighted']
                for selector in active_selectors:
                    active_elements = await page.query_selector_all(selector)
                    if active_elements:
                        validation_data['has_active_thumbnail'] = True
                        validation_data['active_thumbnail_info'] = {
                            'selector': selector,
                            'count': len(active_elements)
                        }
                        break
            except Exception:
                pass
            
            # Check if detail panel/modal is loaded
            try:
                detail_indicators = [
                    'span:has-text("Creation Time")',
                    'span[aria-describedby]',
                    '.modal', '.dialog', '.detail-panel'
                ]
                
                for indicator in detail_indicators:
                    elements = await page.query_selector_all(indicator)
                    if elements:
                        validation_data['detail_panel_loaded'] = True
                        validation_data['metadata_elements_count'] += len(elements)
            except Exception:
                pass
            
            return validation_data
            
        except Exception as e:
            logger.debug(f"Context validation failed: {e}")
            return {'error': str(e)}
    
    def _select_best_date_candidate(self, date_candidates: list) -> str:
        """Select the best date candidate using confidence scoring and smart heuristics"""
        if not date_candidates:
            return "Unknown Date"
        
        if len(date_candidates) == 1:
            return date_candidates[0]['extracted_date']
        
        # Enhanced strategy with confidence scoring
        date_counts = {}
        element_positions = {}
        
        for candidate in date_candidates:
            date = candidate['extracted_date']
            date_counts[date] = date_counts.get(date, 0) + 1
            
            # Track element positions for additional context
            if date not in element_positions:
                element_positions[date] = []
            element_positions[date].append(candidate['element_index'])
        
        # Calculate confidence scores for each unique date
        date_scores = {}
        total_candidates = len(date_candidates)
        
        for date, count in date_counts.items():
            score = 0.0
            
            # Get candidates for this date to access context information
            date_candidates_for_this_date = [c for c in date_candidates if c['extracted_date'] == date]
            
            # Frequency analysis (balanced approach - don't automatically prefer unique dates)
            if count == 1:
                score += 0.3  # Moderate bonus for unique dates (but context matters more)
            elif count <= 3:
                score += 0.1  # Small bonus for reasonable duplication
            else:
                score -= 0.1 * (count - 3)  # Only penalize excessive duplication
            
            # Context score analysis (use the best context score for this date - MOST IMPORTANT)
            context_scores = [c.get('context_score', 0.0) for c in date_candidates_for_this_date]
            best_context_score = max(context_scores) if context_scores else 0.0
            score += best_context_score * 2.0  # Double the weight of context score
            
            # Position analysis (earlier elements might be more relevant, but context score is more important)
            avg_position = sum(element_positions[date]) / len(element_positions[date])
            position_score = max(0, 1.0 - (avg_position / total_candidates)) * 0.2  # Reduced weight
            score += position_score
            
            # Element visibility bonus
            visible_count = sum(1 for c in date_candidates_for_this_date if c.get('element_visible', False))
            visibility_ratio = visible_count / len(date_candidates_for_this_date)
            score += visibility_ratio * 0.3
            
            # Recency bonus (try to parse date and prefer more recent)
            try:
                parsed_date = datetime.strptime(date, "%d %b %Y %H:%M:%S")
                # Bonus for dates within the last 30 days
                days_ago = (datetime.now() - parsed_date).days
                if days_ago <= 30:
                    score += 0.2
                elif days_ago <= 90:
                    score += 0.1
            except:
                # Can't parse date, neutral score
                pass
            
            date_scores[date] = score
            logger.debug(f"Date candidate scoring: {date} -> {score:.2f} (count: {count}, avg_pos: {avg_position:.1f}, context: {best_context_score:.2f}, visible: {visibility_ratio:.1f})")
        
        # Select the date with the highest confidence score
        best_date = max(date_scores.items(), key=lambda x: x[1])
        logger.info(f"Selected best date candidate: {best_date[0]} (confidence: {best_date[1]:.2f})")
        
        return best_date[0]
    
    async def scroll_thumbnail_gallery(self, page) -> bool:
        """Enhanced scroll method with multiple validation and recovery mechanisms"""
        try:
            logger.info("🔄 Scrolling thumbnail gallery with enhanced detection...")
            
            # Phase 1: Get comprehensive before-scroll state
            before_scroll_thumbnails = await self.get_robust_thumbnail_list(page)
            before_scroll_ids = [t['unique_id'] for t in before_scroll_thumbnails if t['unique_id']]
            before_count = len(before_scroll_ids)
            
            logger.debug(f"Thumbnails before scroll: {before_count} total, {sum(1 for t in before_scroll_thumbnails if t['visible'])} visible")
            
            # Phase 2: Multi-strategy scrollable container detection
            scrollable_container = await self._find_scrollable_container(page)
            
            # Phase 3: Execute scroll with validation
            scroll_executed = False
            
            if scrollable_container:
                try:
                    # Get scroll position before
                    scroll_before = await scrollable_container.evaluate("el => el.scrollTop")
                    
                    # Execute scroll
                    await scrollable_container.evaluate(f"el => el.scrollBy(0, {self.config.scroll_amount})")
                    scroll_executed = True
                    
                    # Verify scroll actually happened
                    await page.wait_for_timeout(500)  # Brief wait for scroll to complete
                    scroll_after = await scrollable_container.evaluate("el => el.scrollTop")
                    
                    if scroll_after <= scroll_before:
                        logger.warning(f"⚠️ Container scroll position didn't change ({scroll_before} → {scroll_after})")
                        scroll_executed = False
                        
                except Exception as e:
                    logger.debug(f"Container scroll failed: {e}")
                    scroll_executed = False
            
            # Phase 4: Fallback scrolling methods
            if not scroll_executed:
                logger.debug("Trying fallback scroll methods...")
                
                # Method 1: Page scroll
                try:
                    await page.evaluate(f"window.scrollBy(0, {self.config.scroll_amount})")
                    scroll_executed = True
                    logger.debug("Used page scroll fallback")
                except Exception as e:
                    logger.debug(f"Page scroll failed: {e}")
                
                # Method 2: Keyboard scroll
                if not scroll_executed:
                    try:
                        await page.keyboard.press("PageDown")
                        scroll_executed = True
                        logger.debug("Used keyboard scroll fallback")
                    except Exception as e:
                        logger.debug(f"Keyboard scroll failed: {e}")
                
                # Method 3: Mouse wheel scroll
                if not scroll_executed:
                    try:
                        await page.mouse.wheel(0, self.config.scroll_amount)
                        scroll_executed = True
                        logger.debug("Used mouse wheel scroll fallback")
                    except Exception as e:
                        logger.debug(f"Mouse wheel scroll failed: {e}")
            
            if not scroll_executed:
                logger.error("❌ All scroll methods failed")
                return False
            
            # Phase 5: Wait for content to load with progressive checks
            await self._wait_for_scroll_content_load(page)
            
            # Phase 6: Multi-method validation of new content
            validation_results = await self._validate_scroll_success(page, before_scroll_ids, before_count)
            
            if validation_results['success']:
                # Update internal state
                self.visible_thumbnails_cache = validation_results['current_ids']
                self.current_scroll_position += self.config.scroll_amount
                self.last_scroll_thumbnail_count = validation_results['current_count']
                
                logger.info(f"✅ Enhanced scroll successful: {before_count} → {validation_results['current_count']} thumbnails ({validation_results['new_count']} new)")
                return True
            else:
                logger.warning(f"⚠️ Enhanced scroll validation failed: {validation_results['reason']}")
                return False
                
        except Exception as e:
            logger.error(f"Error in enhanced scroll: {e}")
            return False
    
    async def _find_scrollable_container(self, page) -> Optional[object]:
        """Find the best scrollable container using enhanced detection"""
        container_selectors = [
            self.config.thumbnail_container_selector,
            ".thumbnail-container",
            ".gallery-container", 
            ".scroll-container",
            ".gallery-content",
            ".content-wrapper",
            # Parent container patterns
            f"{self.config.thumbnail_container_selector}",
            f"{self.config.thumbnail_selector}:first-child",
        ]
        
        for selector in container_selectors:
            try:
                containers = await page.query_selector_all(selector)
                
                for container in containers:
                    try:
                        # Enhanced scrollability check
                        scroll_info = await container.evaluate("""el => {
                            const style = getComputedStyle(el);
                            const scrollHeight = el.scrollHeight;
                            const clientHeight = el.clientHeight;
                            const scrollWidth = el.scrollWidth;
                            const clientWidth = el.clientWidth;
                            
                            return {
                                hasVerticalScroll: scrollHeight > clientHeight,
                                hasHorizontalScroll: scrollWidth > clientWidth,
                                overflowY: style.overflowY,
                                overflowX: style.overflowX,
                                scrollable: scrollHeight > clientHeight || 
                                           scrollWidth > clientWidth ||
                                           style.overflowY === 'scroll' ||
                                           style.overflowY === 'auto' ||
                                           style.overflowX === 'scroll' ||
                                           style.overflowX === 'auto',
                                rect: el.getBoundingClientRect(),
                                scrollTop: el.scrollTop,
                                scrollLeft: el.scrollLeft
                            };
                        }""")
                        
                        if scroll_info['scrollable'] and scroll_info['rect']['height'] > 100:
                            logger.debug(f"Found scrollable container: {selector} (scrollHeight: {scroll_info.get('hasVerticalScroll', False)})")
                            return container
                            
                    except Exception as e:
                        logger.debug(f"Error checking container {selector}: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
        
        logger.debug("No suitable scrollable container found")
        return None
    
    async def _wait_for_scroll_content_load(self, page) -> None:
        """Wait for content to load after scroll with progressive validation"""
        # Initial wait
        await page.wait_for_timeout(self.config.scroll_wait_time)
        
        # Progressive content load detection
        stable_count = 0
        last_element_count = 0
        
        for check in range(3):  # Check 3 times over 1.5 seconds
            try:
                current_elements = await page.query_selector_all(f"{self.config.thumbnail_container_selector} {self.config.thumbnail_selector}")
                current_count = len(current_elements)
                
                if current_count == last_element_count:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_element_count = current_count
                
                if stable_count >= 2:  # Content stable for 2 checks
                    logger.debug(f"Content stable at {current_count} elements")
                    break
                    
                await page.wait_for_timeout(500)  # Wait 500ms between checks
                
            except Exception as e:
                logger.debug(f"Error during content load check {check}: {e}")
                break
    
    async def _validate_scroll_success(self, page, before_scroll_ids: List[str], before_count: int) -> Dict[str, Any]:
        """Multi-method validation of scroll success"""
        try:
            # Get current state
            current_thumbnails = await self.get_robust_thumbnail_list(page)
            current_ids = [t['unique_id'] for t in current_thumbnails if t['unique_id']]
            current_count = len(current_ids)
            
            # Method 1: New thumbnail detection (primary)
            truly_new_ids = [tid for tid in current_ids if tid not in before_scroll_ids]
            new_count = len(truly_new_ids)
            
            # Method 2: Total count increase validation
            count_increased = current_count > before_count
            
            # Method 3: Visibility validation (check if more thumbnails are now visible)
            visible_count = sum(1 for t in current_thumbnails if t['visible'])
            before_visible = sum(1 for tid in before_scroll_ids if tid in self.visible_thumbnails_cache)
            
            # Method 4: Position-based validation (check if we have thumbnails at new positions)
            max_before_position = max([i for i, tid in enumerate(before_scroll_ids)] + [-1])
            max_current_position = max([t['position'] for t in current_thumbnails] + [-1])
            position_advanced = max_current_position > max_before_position
            
            # Evaluate success criteria
            primary_success = new_count >= self.config.scroll_detection_threshold
            secondary_success = count_increased and (visible_count > before_visible or position_advanced)
            
            success = primary_success or secondary_success
            
            result = {
                'success': success,
                'current_ids': current_ids,
                'current_count': current_count,
                'new_count': new_count,
                'visible_count': visible_count,
                'position_advanced': position_advanced,
                'reason': ''
            }
            
            if not success:
                if new_count == 0 and not count_increased:
                    result['reason'] = f"No new content detected (threshold: {self.config.scroll_detection_threshold})"
                elif new_count < self.config.scroll_detection_threshold:
                    result['reason'] = f"Insufficient new thumbnails ({new_count} < {self.config.scroll_detection_threshold})"
                else:
                    result['reason'] = "Secondary validation failed"
            
            logger.debug(f"Scroll validation: new={new_count}, count_change={before_count}→{current_count}, visible_change={before_visible}→{visible_count}, pos_advanced={position_advanced}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating scroll success: {e}")
            return {
                'success': False,
                'current_ids': before_scroll_ids,
                'current_count': before_count,
                'new_count': 0,
                'visible_count': 0,
                'position_advanced': False,
                'reason': f"Validation error: {e}"
            }
    
    async def _robust_thumbnail_click(self, page, thumbnail_element, thumbnail_id: str) -> bool:
        """Enhanced thumbnail click with comprehensive stale element recovery"""
        try:
            max_click_attempts = 3
            
            for attempt in range(max_click_attempts):
                try:
                    logger.debug(f"Click attempt {attempt + 1} for thumbnail: {thumbnail_id}")
                    
                    # Ensure element is scrolled into view
                    await thumbnail_element.scroll_into_view_if_needed()
                    await page.wait_for_timeout(300)  # Brief wait for scroll
                    
                    # Check if element is still visible and attached
                    is_visible = await thumbnail_element.is_visible()
                    if not is_visible:
                        logger.debug(f"Thumbnail {thumbnail_id} not visible, attempt {attempt + 1}")
                        if attempt < max_click_attempts - 1:  # Not the last attempt
                            await page.wait_for_timeout(500)
                            continue
                        else:
                            return False
                    
                    # Perform the click
                    await thumbnail_element.click(timeout=8000)
                    logger.info(f"✅ Successfully clicked thumbnail: {thumbnail_id}")
                    return True
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    logger.debug(f"Click attempt {attempt + 1} failed for {thumbnail_id}: {e}")
                    
                    # Check if it's a stale element reference
                    if any(keyword in error_msg for keyword in ["not attached", "detached", "stale", "intercepts pointer"]):
                        logger.info(f"🔄 Stale element detected, refreshing reference for {thumbnail_id}")
                        
                        # Try to refresh the element reference
                        fresh_element = await self.refresh_element_reference(page, thumbnail_id)
                        if fresh_element:
                            thumbnail_element = fresh_element  # Use fresh element for next attempt
                            logger.debug(f"Refreshed element reference for {thumbnail_id}")
                        else:
                            logger.warning(f"Could not refresh element reference for {thumbnail_id}")
                            if attempt == max_click_attempts - 1:  # Last attempt
                                return False
                    
                    # Wait before retry
                    if attempt < max_click_attempts - 1:
                        await page.wait_for_timeout(1000)
            
            logger.error(f"All click attempts failed for thumbnail: {thumbnail_id}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error in robust click for {thumbnail_id}: {e}")
            return False
    
    def _load_existing_log_entries(self) -> Dict[str, Dict[str, str]]:
        """Load existing log entries from generation_downloads.txt"""
        log_entries = {}
        log_path = Path(self.config.logs_folder) / "generation_downloads.txt"
        
        if not log_path.exists():
            logger.debug("No existing log file found for duplicate detection")
            return log_entries
            
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_id = None
            current_date = None
            current_prompt = None
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and separators
                if not line or line.startswith('========'):
                    continue
                
                # Check if this is an ID line (starts with #)
                if line.startswith('#'):
                    # Save previous entry if complete
                    if current_id and current_date and current_prompt:
                        log_entries[current_date] = {
                            'id': current_id,
                            'date': current_date,
                            'prompt': current_prompt
                        }
                    
                    # Start new entry
                    current_id = line
                    current_date = None
                    current_prompt = None
                
                # Check if this is a date line (contains date pattern)
                elif current_id and not current_date and self._is_valid_date_text(line):
                    current_date = line
                
                # Everything else is prompt text (if we have ID and date)
                elif current_id and current_date and not current_prompt:
                    current_prompt = line
            
            # Save the last entry
            if current_id and current_date and current_prompt:
                log_entries[current_date] = {
                    'id': current_id,
                    'date': current_date,
                    'prompt': current_prompt
                }
            
            logger.info(f"📋 Loaded {len(log_entries)} existing log entries for duplicate detection")
            return log_entries
            
        except Exception as e:
            logger.error(f"Error loading existing log entries: {e}")
            return {}

    async def check_comprehensive_duplicate(self, page, thumbnail_id: str, existing_files: set = None) -> bool:
        """Enhanced duplicate detection using multiple comparison methods"""
        try:
            # Method 1: Extract creation metadata for comparison
            metadata = await self.extract_metadata_from_page(page)
            if not metadata:
                logger.debug(f"No metadata extracted for duplicate check: {thumbnail_id}")
                return False
            
            generation_date = metadata.get('generation_date', '')
            prompt = metadata.get('prompt', '')
            
            # Method 2: Load and compare with existing log entries (DATE + PROMPT match)
            if generation_date and prompt:
                existing_entries = self._load_existing_log_entries()
                
                # Check for exact date match
                if generation_date in existing_entries:
                    existing_entry = existing_entries[generation_date]
                    
                    # Compare prompts (truncated since logs may be truncated with "...")
                    existing_prompt = existing_entry['prompt']
                    current_prompt_start = prompt[:100] if len(prompt) > 100 else prompt
                    existing_prompt_start = existing_prompt.replace('...', '').strip()
                    
                    # Check if prompts match (allowing for truncation)
                    if (existing_prompt_start in current_prompt_start or 
                        current_prompt_start in existing_prompt_start):
                        logger.info(f"🛑 DUPLICATE DETECTED: Date='{generation_date}', Prompt match found")
                        logger.info(f"   Existing: {existing_prompt_start[:100]}...")
                        logger.info(f"   Current:  {current_prompt_start[:100]}...")
                        
                        # Log termination message
                        if self.config.stop_on_duplicate:
                            logger.info("🎯 AUTOMATION COMPLETE: Reached previously downloaded content")
                            logger.info("✅ All new generations have been processed successfully")
                        
                        return True
            
            # Method 3: Compare with existing files (if provided)
            if existing_files and generation_date:
                # Try different date format comparisons
                date_formats_to_check = [
                    generation_date,
                    self._normalize_date_format(generation_date)
                ]
                
                for date_format in date_formats_to_check:
                    if date_format in existing_files:
                        logger.info(f"🔍 Duplicate detected by date comparison: {date_format}")
                        return True
            
            # Method 4: Compare with processed thumbnails in current session
            if thumbnail_id in self.processed_thumbnails:
                logger.info(f"🔍 Duplicate detected in current session: {thumbnail_id}")
                return True
            
            # Method 5: Content-based duplicate detection
            if hasattr(self, 'content_signatures'):
                content_signature = f"{generation_date}#{prompt[:50] if prompt else 'no_prompt'}"
                if content_signature in self.content_signatures:
                    logger.info(f"🔍 Duplicate detected by content signature: {content_signature}")
                    return True
                else:
                    self.content_signatures.add(content_signature)
            else:
                # Initialize content signatures tracking
                self.content_signatures = set()
                content_signature = f"{generation_date}#{prompt[:50] if prompt else 'no_prompt'}"
                self.content_signatures.add(content_signature)
            
            return False  # No duplicate detected
            
        except Exception as e:
            logger.debug(f"Error in comprehensive duplicate check: {e}")
            return False
    
    def _normalize_date_format(self, date_string: str) -> str:
        """Normalize different date formats for consistent comparison"""
        try:
            # Try to parse and reformat date
            date_formats = [
                "%d %b %Y %H:%M:%S",    # "24 Aug 2025 01:37:01"
                "%Y-%m-%d %H:%M:%S",    # "2025-08-24 01:37:01"
                "%Y-%m-%d-%H-%M-%S",    # "2025-08-24-01-37-01"
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_string.strip(), fmt)
                    return parsed_date.strftime("%Y-%m-%d-%H-%M-%S")  # Standardized format
                except ValueError:
                    continue
            
            # If no format matches, return original
            return date_string
            
        except Exception:
            return date_string
    
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
        """UPDATED: Extract generation metadata using multi-landmark validation (same as landmark strategy)"""
        try:
            logger.debug("Fallback extraction using multi-landmark validation")
            
            # Use the same multi-landmark approach as the main extraction method
            return await self.extract_metadata_with_landmark_strategy(page, -1)
            
        except Exception as e:
            logger.error(f"Error in fallback multi-landmark extraction: {e}")
            return {'generation_date': 'Unknown Date', 'prompt': 'Unknown Prompt'}
    
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
        
        # Strategy 3: Enhanced SVG icon approach with better error handling
        try:
            logger.debug(f"Strategy 3: Looking for SVG with href {self.config.download_icon_href}")
            svg_selector = f"svg use[href='{self.config.download_icon_href}']"
            svg_element = await page.wait_for_selector(svg_selector, timeout=5000)
            if svg_element:
                # Click the parent span element with proper wait
                parent_span = await svg_element.evaluate_handle("el => el.closest('span[role=\"img\"]')")
                if parent_span:
                    # Ensure element is clickable
                    is_visible = await parent_span.evaluate("el => el && el.offsetParent !== null")
                    if is_visible:
                        await parent_span.click()
                        # Add small wait to ensure click is processed
                        await page.wait_for_timeout(500)
                        logger.info("Successfully clicked download button using SVG icon strategy")
                        return True
                    else:
                        logger.debug("SVG parent element not visible")
                else:
                    logger.debug("Could not find parent span for SVG element")
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
        
        logger.error("All download button strategies failed")
        return False
    
    async def _perform_landmark_readiness_checks(self, page) -> Dict[str, bool]:
        """Perform comprehensive landmark readiness checks to ensure content is loaded"""
        try:
            checks = {
                'creation_time_visible': False,
                'prompt_content_visible': False,
                'media_content_visible': False,
                'button_panel_visible': False
            }
            
            # Check for Creation Time landmark
            try:
                creation_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
                if creation_elements:
                    # Verify at least one is visible
                    for element in creation_elements:
                        if await element.is_visible():
                            checks['creation_time_visible'] = True
                            break
            except Exception:
                pass
            
            # Check for prompt content (ellipsis pattern)
            try:
                prompt_elements = await page.query_selector_all(f"*:has-text('{self.config.prompt_ellipsis_pattern}')")
                if prompt_elements:
                    checks['prompt_content_visible'] = len(prompt_elements) > 0
            except Exception:
                pass
            
            # Check for media content indicators
            try:
                media_indicators = await page.query_selector_all("video, img[src*='http'], canvas")
                checks['media_content_visible'] = len(media_indicators) > 0
            except Exception:
                pass
            
            # Check for button panel
            try:
                button_panels = await page.query_selector_all(self.config.button_panel_selector)
                if button_panels:
                    for panel in button_panels:
                        if await panel.is_visible():
                            checks['button_panel_visible'] = True
                            break
            except Exception:
                pass
            
            logger.debug(f"Landmark readiness checks: {checks}")
            return checks
            
        except Exception as e:
            logger.error(f"Error in landmark readiness checks: {e}")
            return {
                'creation_time_visible': False,
                'prompt_content_visible': False,
                'media_content_visible': False,
                'button_panel_visible': False
            }
    
    async def extract_metadata_with_landmark_strategy(self, page, thumbnail_index: int) -> Optional[Dict[str, str]]:
        """Extract metadata using prompt-first validation approach after thumbnail selection"""
        try:
            logger.debug(f"Starting prompt-first metadata extraction for thumbnail {thumbnail_index}")
            
            metadata = {}
            extraction_timestamp = datetime.now().isoformat()
            
            # LANDMARK STRATEGY: Wait for landmarks to be available
            landmark_wait_attempts = 0
            max_landmark_wait = 3
            landmarks_ready = False
            
            while landmark_wait_attempts < max_landmark_wait and not landmarks_ready:
                landmark_wait_attempts += 1
                
                landmark_checks = await self._perform_landmark_readiness_checks(page)
                
                if landmark_checks['creation_time_visible']:
                    landmarks_ready = True
                    logger.debug(f"Landmarks ready after {landmark_wait_attempts} attempts")
                else:
                    logger.debug(f"Landmarks not ready (attempt {landmark_wait_attempts}), waiting...")
                    await page.wait_for_timeout(1500)
            
            if not landmarks_ready:
                logger.warning(f"Landmarks not ready after {max_landmark_wait} attempts, proceeding with extraction")
            
            # STEP 1: Find the correct metadata container and extract prompt using "Inspiration Mode" + "Off" pattern
            metadata_container = None
            prompt_extracted = False
            
            try:
                logger.info("🔍 Starting prompt extraction")
                
                # Check if we have cached selectors for this session
                if not hasattr(self, '_cached_selectors'):
                    self._cached_selectors = {}
                
                # NEW STRATEGY: Use optimized longest-div extraction for full prompts
                logger.info("🔍 Using optimized longest-div extraction strategy for full prompts")
                
                # OPTIMIZED EXTRACTION: Direct longest-div strategy
                prompt_extracted = await self._extract_full_prompt_optimized(page, metadata)
                        
            except Exception as e:
                logger.debug(f"Error in Inspiration Mode prompt extraction: {e}")
            
            # STEP 2: Use "Inspiration Mode" + "Off" search pattern to find the correct metadata container
            date_extracted = False
            validated_container = None
            
            try:
                logger.info("🔍 Starting 'Inspiration Mode' + 'Off' search for metadata container identification")
                
                # Cache for validated selectors during this session
                if not hasattr(self, '_cached_selectors'):
                    self._cached_selectors = {}
                
                # DISABLED: Caching causes all subsequent thumbnails to use the same Creation Time
                # The cached selector points to the FIRST thumbnail's metadata container,
                # not the currently active one. Each thumbnail needs fresh metadata search.
                # if 'creation_time_container_selector' in self._cached_selectors:
                #     logger.info("📋 Using cached Creation Time container selector")
                #     ... caching code removed to fix duplicate Creation Time issue
                
                # Always perform fresh search for each thumbnail to get correct metadata
                logger.info("🔄 Performing fresh metadata container search for current thumbnail")
                
                # If no cached selector worked, perform fresh search
                if not validated_container:
                    # Step 1: Find all spans containing "Inspiration Mode"
                    inspiration_spans = await page.query_selector_all("span:has-text('Inspiration Mode')")
                    logger.info(f"📦 Found {len(inspiration_spans)} spans containing 'Inspiration Mode'")
                    
                    metadata_candidates = []
                    
                    for i, inspiration_span in enumerate(inspiration_spans):
                        try:
                            if not await inspiration_span.is_visible():
                                logger.debug(f"Inspiration Mode span {i} not visible, skipping")
                                continue
                            
                            # Get inspiration span details
                            inspiration_text = await inspiration_span.text_content()
                            inspiration_class = await inspiration_span.get_attribute('class') or 'no-class'
                            
                            logger.debug(f"🎯 Processing Inspiration Mode span {i}: class='{inspiration_class}' text='{inspiration_text.strip()}'")
                            
                            # Step 2: Look for "Off" in the next sibling span
                            parent = await inspiration_span.evaluate_handle("el => el.parentElement")
                            if not parent:
                                logger.debug(f"   No parent element for span {i}")
                                continue
                            
                            parent_spans = await parent.query_selector_all("span")
                            logger.debug(f"   Parent has {len(parent_spans)} spans")
                            
                            # Find the inspiration span index in parent
                            inspiration_index = -1
                            for j, span in enumerate(parent_spans):
                                span_text = await span.text_content()
                                if "Inspiration Mode" in span_text:
                                    inspiration_index = j
                                    break
                            
                            # Check if next span contains "Off"
                            if inspiration_index >= 0 and inspiration_index + 1 < len(parent_spans):
                                next_span = parent_spans[inspiration_index + 1]
                                next_span_text = await next_span.text_content()
                                next_span_class = await next_span.get_attribute('class') or 'no-class'
                                
                                logger.debug(f"   Next span: class='{next_span_class}' text='{next_span_text.strip()}'")
                                
                                if "Off" in next_span_text:
                                    logger.info(f"   ✅ Found 'Inspiration Mode' + 'Off' pair in span {i}!")
                                    
                                    # Step 3: Search backwards for "Creation Time" + date
                                    metadata_container = await self._search_creation_time_backwards(parent, i)
                                    
                                    if metadata_container:
                                        # Analyze this metadata container
                                        container_info = await self._analyze_metadata_container(metadata_container)
                                        
                                        if container_info['creation_date']:
                                            metadata_candidates.append({
                                                'container': metadata_container,
                                                'info': container_info,
                                                'index': i,
                                                'inspiration_class': inspiration_class,
                                                'off_class': next_span_class
                                            })
                                            
                                            logger.info(f"   🏆 Found valid metadata container: {container_info['text_length']} chars, date: {container_info['creation_date']}")
                                        else:
                                            logger.debug(f"   ❌ Container found but no valid creation date")
                                    else:
                                        logger.debug(f"   ❌ No metadata container found for this Inspiration Mode + Off pair")
                                else:
                                    logger.debug(f"   ❌ Next span does not contain 'Off': '{next_span_text.strip()}'")
                            else:
                                logger.debug(f"   ❌ No next sibling span found or inspiration span not found in parent")
                            
                        except Exception as e:
                            logger.debug(f"Error processing inspiration span {i}: {e}")
                            continue
                    
                    # Select the best metadata candidate
                    if metadata_candidates:
                        # Sort by container size (smaller is better for metadata)
                        metadata_candidates.sort(key=lambda x: x['info']['text_length'])
                        best_candidate = metadata_candidates[0]
                        validated_container = best_candidate['container']
                        
                        logger.info(f"🏆 Selected best metadata container:")
                        logger.info(f"   Index: {best_candidate['index']}")
                        logger.info(f"   Container class: {best_candidate['info']['class']}")
                        logger.info(f"   Text length: {best_candidate['info']['text_length']} chars")
                        logger.info(f"   Creation date: {best_candidate['info']['creation_date']}")
                        
                        # DISABLED: Do NOT cache the selector as it causes duplicate Creation Time
                        # Each thumbnail has its own unique metadata container that must be found fresh
                        # try:
                        #     container_class = best_candidate['info']['class']
                        #     if container_class and container_class != 'no-class':
                        #         class_selector = f".{container_class.replace(' ', '.')}"
                        #         self._cached_selectors['creation_time_container_selector'] = class_selector
                        #         logger.info(f"💾 Cached Creation Time container selector: {class_selector}")
                        # except Exception as e:
                        #     logger.debug(f"Error caching selector: {e}")
                        logger.info("📌 Not caching selector - each thumbnail needs fresh metadata search")
                    else:
                        logger.warning("❌ No valid metadata containers found using Inspiration Mode + Off search")
                
                # Now extract creation time from the validated container
                if validated_container:
                    logger.info(f"🕒 Extracting Creation Time from validated Inspiration Mode container")
                    
                    # Extract date using the cached information if available
                    if 'metadata_candidates' in locals() and metadata_candidates and metadata_candidates[0]['info']['creation_date']:
                        creation_date = metadata_candidates[0]['info']['creation_date']
                        metadata['generation_date'] = creation_date
                        date_extracted = True
                        logger.info(f"🎉 SUCCESS! Extracted date from Inspiration Mode container: '{creation_date}'")
                    else:
                        # Fallback extraction if cached info not available
                        creation_time_spans = await validated_container.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
                        logger.info(f"   Found {len(creation_time_spans)} 'Creation Time' spans in validated container")
                        
                        for j, time_span in enumerate(creation_time_spans):
                            try:
                                if not await time_span.is_visible():
                                    logger.debug(f"   Creation Time span {j}: Not visible, skipping")
                                    continue
                                
                                logger.info(f"   📍 Processing Creation Time span {j}...")
                                
                                # Get the parent div of the "Creation Time" span
                                time_parent = await time_span.evaluate_handle("el => el.parentElement")
                                if not time_parent:
                                    logger.debug(f"   Creation Time span {j}: No parent element, skipping")
                                    continue
                                
                                # Find all spans in this parent (should be the date container div)
                                parent_spans = await time_parent.query_selector_all("span")
                                logger.debug(f"   Creation Time parent {j} has {len(parent_spans)} spans")
                                
                                # The structure should be: <span>Creation Time</span><span>26 Aug 2025 19:08:21</span>
                                if len(parent_spans) >= 2:
                                    date_span = parent_spans[1]  # Second span contains the actual date
                                    date_text = await date_span.text_content()
                                    
                                    if date_text and date_text.strip() != self.config.creation_time_text:
                                        cleaned_date = date_text.strip()
                                        
                                        # Validate this looks like a proper date format
                                        if self._is_valid_date_text(cleaned_date):
                                            metadata['generation_date'] = cleaned_date
                                            date_extracted = True
                                            logger.info(f"🎉 SUCCESS! Extracted date from validated container: '{cleaned_date}'")
                                            break
                                        else:
                                            logger.warning(f"   ❌ Date candidate failed format validation: '{cleaned_date}'")
                                    else:
                                        logger.debug(f"   Date text is empty or same as Creation Time label")
                                else:
                                    logger.warning(f"   ❌ Parent has only {len(parent_spans)} spans, expected at least 2")
                                
                            except Exception as e:
                                logger.error(f"   ❌ Error processing Creation Time span {j}: {e}")
                                continue
                        
                        if date_extracted:
                            logger.info(f"🎉 SUCCESS! Inspiration Mode search extracted correct date from validated container")
                        else:
                            logger.warning("Found validated container but failed to extract date from it")
                else:
                    logger.warning("No validated metadata container found using Inspiration Mode + Off search")
                    
            except Exception as e:
                logger.error(f"Error in multi-landmark metadata extraction: {e}")
            
            # STEP 3: Fallback - if multi-landmark approach failed, try prompt-based container
            if not date_extracted and metadata_container and prompt_extracted:
                try:
                    logger.debug("Multi-landmark failed, trying prompt-based metadata container")
                    
                    creation_time_elements = await metadata_container.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
                    logger.debug(f"Found {len(creation_time_elements)} creation time elements in prompt-based container")
                    
                    for j, time_element in enumerate(creation_time_elements):
                        try:
                            if not await time_element.is_visible():
                                continue
                            
                            time_parent = await time_element.evaluate_handle("el => el.parentElement")
                            if not time_parent:
                                continue
                                
                            spans = await time_parent.query_selector_all("span")
                            
                            if len(spans) >= 2:
                                date_span = spans[1]
                                date_text = await date_span.text_content()
                                if date_text and date_text.strip() != self.config.creation_time_text:
                                    cleaned_date = date_text.strip()
                                    if len(cleaned_date) > 10 and ('Aug' in cleaned_date or '2025' in cleaned_date):
                                        metadata['generation_date'] = cleaned_date
                                        date_extracted = True
                                        logger.info(f"Extracted date from prompt-based container: {cleaned_date}")
                                        break
                        except Exception as e:
                            logger.debug(f"Error processing time element {j}: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error extracting date from prompt-based container: {e}")
            
            # STEP 4: Final fallback - traditional approach (least reliable)
            if not date_extracted:
                logger.warning("All advanced approaches failed, falling back to traditional date extraction")
                try:
                    creation_time_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
                    logger.debug(f"Final fallback: Found {len(creation_time_elements)} creation time elements on page")
                    
                    for element in creation_time_elements:
                        try:
                            if not await element.is_visible():
                                continue
                            
                            parent = await element.evaluate_handle("el => el.parentElement")
                            if not parent:
                                continue
                                
                            spans = await parent.query_selector_all("span")
                            
                            if len(spans) >= 2:
                                date_span = spans[1]
                                date_text = await date_span.text_content()
                                if date_text and date_text.strip() != self.config.creation_time_text:
                                    metadata['generation_date'] = date_text.strip()
                                    date_extracted = True
                                    logger.debug(f"Final fallback extracted date: {date_text.strip()}")
                                    break
                        except Exception as e:
                            logger.debug(f"Error in final fallback date extraction: {e}")
                            continue
                    
                except Exception as e:
                    logger.debug(f"Error in final fallback date extraction: {e}")
            
            # Log extraction results
            if self.debug_logger:
                self.debug_logger.log_step(thumbnail_index, "LANDMARK_EXTRACTION_COMPLETE", {
                    "date_extracted": date_extracted,
                    "prompt_extracted": prompt_extracted,
                    "extraction_timestamp": extraction_timestamp,
                    "landmarks_ready": landmarks_ready,
                    "landmark_wait_attempts": landmark_wait_attempts,
                    "used_metadata_container": metadata_container is not None
                })
            
            # Provide defaults for failed extractions
            if not date_extracted:
                metadata['generation_date'] = 'Unknown Date'
                logger.debug("Date extraction failed, using default")
            
            if not prompt_extracted:
                metadata['prompt'] = 'Unknown Prompt'
                logger.debug("Prompt extraction failed, using default")
            
            logger.info(f"Prompt-first extraction completed for thumbnail {thumbnail_index}: date={date_extracted}, prompt={prompt_extracted}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error in prompt-first metadata extraction: {e}")
            return {'generation_date': 'Unknown Date', 'prompt': 'Unknown Prompt'}
    
    async def _perform_comprehensive_state_validation(self, page, thumbnail_index: int) -> Dict[str, bool]:
        """Perform comprehensive state validation to check if thumbnail click was successful"""
        try:
            validations = {
                'content_changed': False,
                'detail_panel_loaded': False,
                'active_thumbnail_detected': False,
                'landmark_elements_visible': False
            }
            
            # Check for content changes using multiple indicators
            try:
                # Check for creation time text (indicates detail view loaded)
                creation_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
                validations['landmark_elements_visible'] = len([e for e in creation_elements if await e.is_visible()]) > 0
            except Exception:
                pass
            
            # Check for detail panel indicators
            try:
                # Look for typical detail panel elements
                detail_indicators = [
                    ".detail-panel", ".details", "[data-detail]", 
                    ".generation-info", ".metadata-panel"
                ]
                
                for indicator in detail_indicators:
                    elements = await page.query_selector_all(indicator)
                    if any(await e.is_visible() for e in elements):
                        validations['detail_panel_loaded'] = True
                        break
            except Exception:
                pass
            
            # Check for active thumbnail indicators
            try:
                active_selectors = [
                    ".thumbnail-active", ".selected", ".current",
                    "[data-active='true']", ".thumbnail.active"
                ]
                
                for selector in active_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        validations['active_thumbnail_detected'] = True
                        break
            except Exception:
                pass
            
            # Overall content change assessment
            validations['content_changed'] = any([
                validations['landmark_elements_visible'],
                validations['detail_panel_loaded']
            ])
            
            logger.debug(f"State validation for thumbnail {thumbnail_index}: {validations}")
            return validations
            
        except Exception as e:
            logger.error(f"Error in comprehensive state validation: {e}")
            return {
                'content_changed': False,
                'detail_panel_loaded': False,
                'active_thumbnail_detected': False,
                'landmark_elements_visible': False
            }
    
    async def execute_download_sequence(self, page) -> bool:
        """Execute the complete download sequence: SVG icon → watermark option"""
        try:
            logger.debug("Starting enhanced download sequence...")
            
            # Step 1: Click the download button (SVG icon)
            download_button_clicked = await self.find_and_click_download_button(page)
            if not download_button_clicked:
                logger.error("Failed to click download button in sequence")
                return False
            
            logger.debug("Download button clicked successfully, waiting for options...")
            
            # Step 2: Wait for download options to appear
            await page.wait_for_timeout(1500)
            
            # Step 3: Look for and click the watermark option with enhanced strategy
            watermark_clicked = await self._enhanced_watermark_click_sequence(page)
            
            if watermark_clicked:
                logger.info("Complete download sequence successful: SVG → watermark")
                
                # CRITICAL FIX: Close overlay popup with thumbs-up click to enable next thumbnail navigation
                logger.debug("🔧 Closing overlay popup to enable next thumbnail navigation...")
                overlay_closed = await self.close_overlay_popup_with_thumbs_up(page)
                
                if overlay_closed:
                    logger.info("✅ Overlay popup closed - next thumbnail navigation should work")
                else:
                    logger.warning("⚠️ Could not close overlay - navigation may be blocked")
                
                return True
            else:
                logger.warning("Watermark option not found, but download button was clicked")
                # Check if download started anyway
                download_started = await self._check_download_initiated(page)
                if download_started:
                    logger.info("Download appears to have started without watermark option")
                    
                    # Also close overlay popup in this case
                    logger.debug("🔧 Closing overlay popup after direct download...")
                    await self.close_overlay_popup_with_thumbs_up(page)
                    
                    return True
                else:
                    logger.warning("No download activity detected after button click")
                    return False
            
        except Exception as e:
            logger.error(f"Error in download sequence: {e}")
            return False
    
    async def _enhanced_watermark_click_sequence(self, page) -> bool:
        """Enhanced sequence for finding and clicking the watermark option"""
        try:
            logger.debug("Starting enhanced watermark click sequence...")
            
            # Multiple attempts with different strategies
            for attempt in range(3):
                logger.debug(f"Watermark click attempt {attempt + 1}/3")
                
                # Strategy 1: CSS selector (most reliable if available)
                if await self._try_watermark_css_selector(page):
                    return True
                
                # Strategy 2: Text-based search
                if await self._try_watermark_text_search(page):
                    return True
                
                # Strategy 3: Advanced DOM traversal
                if await self._try_watermark_dom_traversal(page):
                    return True
                
                # Wait before next attempt
                if attempt < 2:
                    await page.wait_for_timeout(1500)
            
            logger.debug("All watermark click strategies failed")
            return False
            
        except Exception as e:
            logger.error(f"Error in enhanced watermark sequence: {e}")
            return False
    
    async def _try_watermark_css_selector(self, page) -> bool:
        """Try clicking watermark option using CSS selector with enhanced targeting"""
        try:
            # Strategy 1: Try the original CSS selector
            element = await page.wait_for_selector(self.config.download_no_watermark_selector, timeout=3000)
            if element and await element.is_visible():
                await element.click()
                logger.info(f"Clicked watermark using original CSS selector: {self.config.download_no_watermark_selector}")
                return True
        except Exception as e:
            logger.debug(f"Original CSS selector strategy failed: {e}")
        
        # Strategy 2: Try targeting the specific DOM structure from the user's example
        try:
            # Look for the specific watermark SVG icon and its parent containers
            enhanced_selectors = [
                # Target the icon-block container directly
                'div.icon-block:has(use[xlink:href="#icon-icon_gongneng_20px_wushuiyin"])',
                'div.line:has(use[xlink:href="#icon-icon_gongneng_20px_wushuiyin"])',
                # Target by the watermark text in the specific structure
                f'div.icon-block:has(.text:has-text("{self.config.download_no_watermark_text}"))',
                f'div.line:has(.text:has-text("{self.config.download_no_watermark_text}"))',
                # Target the anticon container and go up to clickable parent
                'div.line:has(.anticon.lineIcon)',
                'div.icon-block:has(.anticon.lineIcon)'
            ]
            
            for selector in enhanced_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        await element.click()
                        logger.info(f"Clicked watermark using enhanced CSS selector: {selector}")
                        return True
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Enhanced CSS selector strategy failed: {e}")
        
        return False
    
    async def _try_watermark_text_search(self, page) -> bool:
        """Try clicking watermark option using text search with parent container approach"""
        try:
            # Strategy 1: Look for the specific SVG icon first (most reliable)
            svg_selectors = [
                'use[xlink:href="#icon-icon_gongneng_20px_wushuiyin"]',
                'svg use[xlink:href="#icon-icon_gongneng_20px_wushuiyin"]',
                'svg:has(use[xlink:href="#icon-icon_gongneng_20px_wushuiyin"])'
            ]
            
            for svg_selector in svg_selectors:
                try:
                    svg_element = await page.wait_for_selector(svg_selector, timeout=2000)
                    if svg_element:
                        # Find the clickable parent container (icon-block or line)
                        parent_containers = [
                            await svg_element.query_selector('xpath=ancestor::div[contains(@class, "icon-block")]'),
                            await svg_element.query_selector('xpath=ancestor::div[contains(@class, "line")]'),
                            await svg_element.query_selector('xpath=ancestor::div[contains(@class, "anticon")]/../..'),
                            await svg_element.query_selector('xpath=ancestor::*[contains(text(), "Download without Watermark")]/..')
                        ]
                        
                        for container in parent_containers:
                            if container and await container.is_visible():
                                await container.click()
                                logger.info(f"Clicked watermark using SVG parent container approach")
                                return True
                except Exception:
                    continue
            
            # Strategy 2: Look for text and find parent container
            text_element = None
            try:
                # Find element containing the watermark text
                text_selectors = [
                    f"div.text:has-text('{self.config.download_no_watermark_text}')",
                    f"*:has-text('{self.config.download_no_watermark_text}'):not(body):not(html)"
                ]
                
                for text_selector in text_selectors:
                    text_element = await page.wait_for_selector(text_selector, timeout=2000)
                    if text_element:
                        break
                
                if text_element:
                    # Navigate up to find clickable parent
                    parent_containers = [
                        await text_element.query_selector('xpath=ancestor::div[contains(@class, "icon-block")]'),
                        await text_element.query_selector('xpath=ancestor::div[contains(@class, "line")]'),
                        await text_element.query_selector('xpath=../..'),  # Go up 2 levels
                        await text_element.query_selector('xpath=..')      # Go up 1 level
                    ]
                    
                    for container in parent_containers:
                        if container and await container.is_visible():
                            # Validate this looks like a button container
                            class_name = await container.get_attribute('class') or ''
                            if 'icon' in class_name.lower() or 'line' in class_name.lower() or 'button' in class_name.lower():
                                await container.click()
                                logger.info(f"Clicked watermark using text parent container approach")
                                return True
                            
            except Exception as e:
                logger.debug(f"Text-based parent search failed: {e}")
            
            # Strategy 3: Fallback to direct text matching (original approach)
            selectors = [
                f"*:has-text('{self.config.download_no_watermark_text}')",
                f"div:has-text('{self.config.download_no_watermark_text}')",
                f"span:has-text('{self.config.download_no_watermark_text}')",
                f"button:has-text('{self.config.download_no_watermark_text}')"
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        await element.click()
                        logger.info(f"Clicked watermark using fallback text selector: {selector}")
                        return True
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Text search strategy failed: {e}")
        return False
    
    async def _try_watermark_dom_traversal(self, page) -> bool:
        """Try clicking watermark option using DOM traversal with parent container logic"""
        try:
            # Strategy 1: Look for elements with watermark text and find their clickable parents
            elements = await page.query_selector_all("div, span, button, a, p")
            
            text_elements = []
            for element in elements:
                try:
                    text_content = await element.text_content()
                    if text_content and self.config.download_no_watermark_text in text_content.strip():
                        if await element.is_visible():
                            text_elements.append(element)
                except Exception:
                    continue
            
            # For each text element, try to find clickable parent
            for text_element in text_elements:
                try:
                    # Try different parent levels
                    parent_candidates = []
                    current = text_element
                    
                    # Go up the DOM tree looking for clickable parents
                    for level in range(5):  # Check up to 5 parent levels
                        try:
                            parent = await current.query_selector('xpath=..')
                            if parent:
                                parent_candidates.append(parent)
                                current = parent
                            else:
                                break
                        except:
                            break
                    
                    # Try clicking each parent from most specific to most general
                    for parent in parent_candidates:
                        try:
                            if await parent.is_visible():
                                # Check if this parent looks like a clickable container
                                tag_name = await parent.evaluate('el => el.tagName.toLowerCase()')
                                class_name = await parent.get_attribute('class') or ''
                                
                                # Prefer containers that look clickable
                                clickable_indicators = [
                                    'icon' in class_name.lower(),
                                    'line' in class_name.lower(), 
                                    'button' in class_name.lower(),
                                    'click' in class_name.lower(),
                                    tag_name in ['button', 'a', 'div']
                                ]
                                
                                if any(clickable_indicators):
                                    await parent.click()
                                    logger.info(f"Clicked watermark using DOM traversal parent container (tag: {tag_name}, class: {class_name})")
                                    return True
                        except Exception:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error processing text element: {e}")
                    continue
            
            # Strategy 2: Fallback to direct text element clicking (original approach)
            for element in text_elements:
                try:
                    if await element.is_visible() and await element.is_enabled():
                        await element.click()
                        logger.info("Clicked watermark using DOM traversal direct text")
                        return True
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"DOM traversal strategy failed: {e}")
        return False
    
    async def _check_download_initiated(self, page) -> bool:
        """Check if download has been initiated by looking for download indicators"""
        try:
            indicators = [
                ".download-progress", ".downloading", "[data-downloading]",
                "text=Downloading", "text=Download started", ".download-initiated"
            ]
            
            for indicator in indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=1000)
                    if element:
                        logger.debug(f"Download indicator found: {indicator}")
                        return True
                except Exception:
                    continue
            
            return False
        except Exception:
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
    
    async def close_overlay_popup_with_thumbs_up(self, page) -> bool:
        """Click the thumbs-up icon to close overlay popup after download"""
        try:
            logger.debug("🎯 Attempting to close overlay popup with thumbs-up click...")
            
            # Wait a moment for the overlay to fully appear
            await page.wait_for_timeout(1000)
            
            # Strategy 1: Target the specific thumbs-up icon using the provided HTML structure
            thumbs_up_selectors = [
                # Most specific: First span in the icon container with the thumbs-up SVG
                "div.sc-bcyJnU.gucrTM span:first-child svg use[href*='icon_tongyong_20px_zan']",
                "div.sc-bcyJnU.gucrTM span:first-child",
                
                # Fallback: Look for thumbs-up icon by SVG use element
                "svg use[href*='icon_tongyong_20px_zan']",
                "svg use[xlink\\:href*='icon_tongyong_20px_zan']",
                
                # More general: First clickable span in icon panel
                "div.sc-bcyJnU span[role='img']:first-child",
                "span[role='img'] svg use[href*='zan']",
                
                # Generic: Any thumbs-up like icon
                "span[style*='cursor: pointer'] svg use[href*='zan']",
                "[class*='anticon'] svg use[href*='zan']"
            ]
            
            for selector in thumbs_up_selectors:
                try:
                    logger.debug(f"Trying thumbs-up selector: {selector}")
                    element = await page.wait_for_selector(selector, timeout=3000)
                    
                    if element and await element.is_visible():
                        # Get the clickable parent (span element)
                        clickable_element = element
                        if selector.endswith('svg') or selector.endswith('use') or 'svg use' in selector:
                            # If we found the SVG/use, get the parent span
                            clickable_element = await element.query_selector('xpath=ancestor::span[@role="img"]')
                            if not clickable_element:
                                clickable_element = await element.query_selector('xpath=ancestor::span')
                        
                        if clickable_element:
                            await clickable_element.click()
                            logger.info(f"✅ Successfully clicked thumbs-up icon using selector: {selector}")
                            
                            # Wait to ensure overlay closes
                            await page.wait_for_timeout(500)
                            return True
                    
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # Strategy 2: Look for any clickable element in the icon panel area
            try:
                logger.debug("Strategy 2: Looking for first clickable icon in panel...")
                
                icon_panel_selectors = [
                    "div.sc-bcyJnU.gucrTM span[role='img']:first-child",
                    "div[class*='gucrTM'] span:first-child",
                    "[role='img'][style*='cursor: pointer']:first-of-type"
                ]
                
                for panel_selector in icon_panel_selectors:
                    element = await page.query_selector(panel_selector)
                    if element and await element.is_visible():
                        await element.click()
                        logger.info(f"✅ Clicked first icon in panel using: {panel_selector}")
                        await page.wait_for_timeout(500)
                        return True
                        
            except Exception as e:
                logger.debug(f"Icon panel strategy failed: {e}")
            
            logger.warning("❌ Could not find thumbs-up icon to close overlay")
            return False
            
        except Exception as e:
            logger.error(f"Error closing overlay with thumbs-up: {e}")
            return False
    
    async def navigate_to_starting_thumbnail(self, page, target_thumbnail_number: int) -> bool:
        """Navigate to the specified starting thumbnail number"""
        try:
            if target_thumbnail_number <= 1:
                logger.info("Starting from thumbnail #1 - no navigation needed")
                return True
            
            logger.info(f"🧭 Navigating to starting thumbnail #{target_thumbnail_number}...")
            
            current_position = 1
            max_navigation_attempts = target_thumbnail_number * 2  # Safety limit
            navigation_attempts = 0
            
            while current_position < target_thumbnail_number and navigation_attempts < max_navigation_attempts:
                navigation_attempts += 1
                
                # Find current active thumbnail
                active_thumbnail = await self.find_active_thumbnail(page)
                if not active_thumbnail:
                    logger.error(f"❌ Could not find active thumbnail at position {current_position}")
                    return False
                
                # Navigate to next thumbnail
                logger.debug(f"📍 Current position: {current_position}, target: {target_thumbnail_number}")
                navigation_success = await self.navigate_to_next_thumbnail_landmark(page)
                
                if navigation_success:
                    current_position += 1
                    logger.debug(f"✅ Successfully navigated to thumbnail #{current_position}")
                    
                    # Add a small delay between navigation steps
                    await page.wait_for_timeout(500)
                else:
                    logger.warning(f"⚠️ Navigation failed at position {current_position}")
                    
                    # Try scrolling if navigation fails (might be end of visible thumbnails)
                    logger.debug("🔄 Attempting scroll to reveal more thumbnails...")
                    await page.evaluate(f"window.scrollBy(0, {self.config.scroll_amount})")
                    await page.wait_for_timeout(self.config.scroll_wait_time)
                    
                    # Retry navigation after scroll
                    navigation_success = await self.navigate_to_next_thumbnail_landmark(page)
                    if navigation_success:
                        current_position += 1
                        logger.debug(f"✅ Successfully navigated after scroll to thumbnail #{current_position}")
                    else:
                        logger.error(f"❌ Navigation failed even after scrolling at position {current_position}")
                        break
            
            if current_position >= target_thumbnail_number:
                logger.info(f"🎯 Successfully navigated to starting thumbnail #{target_thumbnail_number}")
                return True
            else:
                logger.error(f"❌ Failed to reach target thumbnail #{target_thumbnail_number}, stopped at #{current_position}")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to starting thumbnail: {e}")
            return False
    
    async def close_download_shelf(self, page) -> None:
        """Attempt to close Chrome download shelf / Recent Downloads popup"""
        try:
            # Method 1: Keyboard shortcut to close download shelf
            try:
                await page.keyboard.press("Control+Shift+J")  # Toggle download shelf
                await page.wait_for_timeout(100)
                await page.keyboard.press("Control+Shift+J")  # Toggle again to close
                logger.debug("Attempted to close download shelf with keyboard shortcut")
            except:
                pass
            
            # Method 2: Click outside the download area to dismiss
            try:
                await page.mouse.click(100, 100)  # Click in top left corner
                logger.debug("Clicked outside download area to dismiss popup")
            except:
                pass
            
            # Method 3: Press Escape to close any popups
            # DISABLED: Escape key press causes gallery to close and navigate back to main page
            # This breaks multi-thumbnail automation by leaving the detail view
            try:
                # await page.keyboard.press("Escape")  # REMOVED - causes navigation issues
                logger.debug("Skipped Escape key press to avoid navigation issues")
            except:
                pass
            
            # Method 4: Try to find and close the download shelf UI element
            try:
                # Common selectors for download shelf close button
                close_selectors = [
                    "#download-shelf-close",
                    "[aria-label='Close downloads']",
                    ".download-shelf-close-button",
                    "button[title='Close']",
                    "[role='button'][aria-label*='Close']"
                ]
                
                for selector in close_selectors:
                    try:
                        close_button = await page.query_selector(selector)
                        if close_button:
                            await close_button.click()
                            logger.info(f"Closed download shelf using selector: {selector}")
                            break
                    except:
                        continue
            except:
                pass
                
            # Method 5: Execute JavaScript to hide download-related elements
            try:
                await page.evaluate("""
                    // Hide download shelf and related UI elements
                    const downloadElements = document.querySelectorAll(
                        '#download-shelf, .download-shelf, .downloads-bar, ' +
                        '[role="alert"], .download-started-animation, ' +
                        '.download-notification, .download-bubble'
                    );
                    downloadElements.forEach(el => {
                        if (el) {
                            el.style.display = 'none';
                            el.style.visibility = 'hidden';
                        }
                    });
                """)
                logger.debug("Executed JavaScript to hide download UI elements")
            except:
                pass
                
        except Exception as e:
            logger.debug(f"Error closing download shelf: {e}")
    
    async def download_single_generation_robust(self, page, thumbnail_info: Dict[str, Any], existing_files: set = None) -> bool:
        """Download a single generation using robust thumbnail tracking"""
        try:
            thumbnail_element = thumbnail_info['element']
            thumbnail_id = thumbnail_info['unique_id']
            thumbnail_position = thumbnail_info['position']
            
            logger.info(f"Starting robust download for thumbnail: {thumbnail_id}")
            
            # DEBUG: Log thumbnail click attempt
            if self.debug_logger:
                self.debug_logger.log_step(thumbnail_position, "ROBUST_THUMBNAIL_CLICK_START", {
                    "thumbnail_id": thumbnail_id,
                    "thumbnail_position": thumbnail_position,
                    "page_url": page.url,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Enhanced click with comprehensive stale element recovery
            click_success = await self._robust_thumbnail_click(page, thumbnail_element, thumbnail_id)
                
            if not click_success:
                logger.error(f"Failed to click thumbnail {thumbnail_id} after all retry attempts")
                return False
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # ENHANCED: Extract metadata with duplicate checking
            metadata_dict = await self.extract_metadata_with_landmark_strategy(page, thumbnail_position)
            if not metadata_dict or not metadata_dict.get('generation_date') or metadata_dict.get('generation_date') == 'Unknown':
                logger.warning(f"Landmark strategy failed for thumbnail {thumbnail_id}, trying legacy extraction")
                metadata_dict = await self.extract_metadata_from_page(page)
                
            if not metadata_dict:
                logger.warning(f"All metadata extraction failed for thumbnail {thumbnail_id}, using defaults")
                metadata_dict = {'generation_date': 'Unknown', 'prompt': 'Unknown'}
            
            # ENHANCED: Comprehensive duplicate detection (log-based, file-based, and session-based)
            if self.config.duplicate_check_enabled and metadata_dict and metadata_dict.get('generation_date'):
                creation_time = metadata_dict.get('generation_date')
                
                # Method 1: Check comprehensive duplicates (log entries + prompt matching)
                is_comprehensive_duplicate = await self.check_comprehensive_duplicate(page, thumbnail_id, existing_files)
                if is_comprehensive_duplicate:
                    if self.config.stop_on_duplicate:
                        logger.info(f"🛑 STOPPING: Comprehensive duplicate detected for {thumbnail_id}")
                        logger.info("✅ Automation has reached previously downloaded content")
                        self.should_stop = True
                        return False
                    else:
                        logger.warning(f"⏭️  Skipping comprehensive duplicate: {thumbnail_id}")
                        return True
                
                # Method 2: Check file-based duplicates (from disk) - fallback
                if existing_files and self.check_duplicate_exists(creation_time, existing_files):
                    if self.config.stop_on_duplicate:
                        logger.info(f"🛑 STOPPING: File-based duplicate detected ({creation_time})")
                        logger.info("🔄 All newer files have already been downloaded")
                        self.should_stop = True
                        return False
                    else:
                        logger.warning(f"⏭️  Skipping file duplicate with creation time: {creation_time}")
                        return True
                
                # Method 3: Check session-based duplicates (already processed in this run) - fallback
                session_duplicate_id = f"{creation_time}|{thumbnail_id}"
                if session_duplicate_id in self.processed_thumbnails:
                    logger.warning(f"⏭️  Skipping session duplicate: {session_duplicate_id}")
                    return True
            
            # Continue with download process using existing logic...
            file_id = self.logger.get_next_file_id()
            download_start_time = time.time()
            
            # Set up download handling
            download_path = Path(self.config.downloads_folder)
            logger.debug(f"Monitoring download directory: {download_path}")
            
            download_promise = None
            def handle_download(download):
                nonlocal download_promise
                download_promise = download
                logger.info(f"Download started: {download.suggested_filename}")
            
            page.on("download", handle_download)
            
            try:
                # Trigger download using existing download sequence
                download_triggered = await self.execute_download_sequence(page)
                
                if not download_triggered:
                    logger.warning(f"Failed to trigger download for thumbnail {thumbnail_id}")
                    return False
                
                # FAST OPTIMIZATION: Use download completion detection
                if self.config.fast_navigation_mode:
                    await page.wait_for_timeout(1000)
                    completion_success = await self.wait_for_download_completion(
                        page, 
                        timeout=self.config.download_timeout if hasattr(self.config, 'download_timeout') else 8000
                    )
                    if not completion_success:
                        logger.warning(f"⏰ Download may still be in progress for thumbnail {thumbnail_id}")
                else:
                    await page.wait_for_timeout(3000)
                
                # Handle download completion and file naming
                downloaded_file = None
                if download_promise:
                    try:
                        target_filename = f"{file_id}_temp.mp4"
                        target_path = download_path / target_filename
                        await download_promise.save_as(str(target_path))
                        downloaded_file = target_path
                        logger.info(f"Download saved: {downloaded_file.name}")
                    except Exception as e:
                        logger.error(f"Failed to save download: {e}")
                
                # Fallback file detection if needed
                if not downloaded_file:
                    downloaded_file = await self.file_manager.wait_for_download(timeout=10)
                
                if downloaded_file and downloaded_file.exists():
                    # Generate proper filename and move file
                    final_filename = self.file_namer.generate_filename(
                        file_path=downloaded_file,
                        creation_date=metadata_dict.get('generation_date'),
                        sequence_number=file_id
                    )
                    final_path = download_path / final_filename
                    
                    downloaded_file.rename(final_path)
                    logger.info(f"📁 File renamed to: {final_filename}")
                    
                    # Create GenerationMetadata object for logging
                    metadata = GenerationMetadata(
                        file_id=str(file_id),
                        generation_date=metadata_dict.get('generation_date', ''),
                        prompt=metadata_dict.get('prompt', ''),
                        download_timestamp=datetime.now().isoformat(),
                        file_path=str(final_path),
                        original_filename=downloaded_file.name,
                        file_size=final_path.stat().st_size if final_path.exists() else 0,
                        download_duration=time.time() - download_start_time
                    )
                    
                    # Log to file (remove incorrect await)
                    self.logger.log_download(metadata)
                    
                    self.downloads_completed += 1
                    logger.info(f"✅ Successfully downloaded: {final_filename}")
                    return True
                else:
                    logger.error(f"Download file not found for thumbnail {thumbnail_id}")
                    return False
                    
            finally:
                # Remove download listener
                page.remove_listener("download", handle_download)
            
        except Exception as e:
            logger.error(f"Error in robust download for thumbnail {thumbnail_info.get('unique_id', 'unknown')}: {e}")
            return False
    
    async def download_single_generation(self, page, thumbnail_index: int, existing_files: set = None) -> bool:
        """Download a single generation and handle all associated tasks"""
        try:
            logger.info(f"Starting download for thumbnail {thumbnail_index}")
            
            # DEBUG: Log thumbnail click attempt
            if self.debug_logger:
                self.debug_logger.log_step(thumbnail_index, "THUMBNAIL_CLICK_START", {
                    "thumbnail_index": thumbnail_index,
                    "page_url": page.url,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Click on thumbnail to load generation details
            # Try multiple thumbnail selectors with enhanced error handling
            thumbnail_clicked = False
            click_attempts = 0
            max_click_attempts = 3
            
            for selector in self.config.thumbnail_selector.split(", "):
                if thumbnail_clicked:
                    break
                    
                for attempt in range(max_click_attempts):
                    try:
                        thumbnail_selector = f"{selector}:nth-child({thumbnail_index + 1})"
                        
                        # First verify the element exists and is visible
                        element = await page.query_selector(thumbnail_selector)
                        if not element:
                            logger.debug(f"Element not found: {thumbnail_selector}")
                            continue
                            
                        is_visible = await element.is_visible()
                        if not is_visible:
                            logger.debug(f"Element not visible: {thumbnail_selector}")
                            continue
                        
                        # Try clicking with timeout
                        await page.click(thumbnail_selector, timeout=5000)
                        
                        # CRITICAL FIX: Enhanced validation with multiple checks
                        await page.wait_for_timeout(1500)  # Initial wait for UI update
                        
                        # Multiple validation approaches for state change
                        state_validations = await self._perform_comprehensive_state_validation(page, thumbnail_index)
                        
                        # Check if any validation method confirms state change
                        state_changed = any([
                            state_validations.get('content_changed', False),
                            state_validations.get('detail_panel_loaded', False),
                            state_validations.get('active_thumbnail_detected', False)
                        ])
                        
                        if not state_changed:
                            logger.debug(f"Initial state validation failed for {thumbnail_selector}, trying extended wait")
                            # Extended wait and retry
                            await page.wait_for_timeout(3000)
                            state_validations = await self._perform_comprehensive_state_validation(page, thumbnail_index)
                            state_changed = any([
                                state_validations.get('content_changed', False),
                                state_validations.get('detail_panel_loaded', False),
                                state_validations.get('active_thumbnail_detected', False)
                            ])
                            
                            # Log detailed validation results
                            if self.debug_logger:
                                self.debug_logger.log_step(thumbnail_index, "EXTENDED_STATE_VALIDATION", state_validations)
                        
                        if state_changed:
                            thumbnail_clicked = True
                            logger.info(f"Successfully clicked thumbnail using selector: {selector} (attempt {attempt + 1})")
                            
                            # DEBUG: Log successful thumbnail click with validation details
                            if self.debug_logger:
                                self.debug_logger.log_thumbnail_click(
                                    thumbnail_index=thumbnail_index,
                                    thumbnail_selector=thumbnail_selector,
                                    click_success=True
                                )
                                self.debug_logger.log_step(thumbnail_index, "THUMBNAIL_CLICK_SUCCESS", {
                                    "selector": selector,
                                    "attempt": attempt + 1,
                                    "state_validations": state_validations
                                })
                            break
                        else:
                            logger.debug(f"State validation failed for {thumbnail_selector}, attempt {attempt + 1}")
                            logger.debug(f"Validation details: {state_validations}")
                            
                    except Exception as e:
                        click_attempts += 1
                        logger.debug(f"Thumbnail selector {selector} failed (attempt {attempt + 1}): {e}")
                        if self.debug_logger:
                            self.debug_logger.log_thumbnail_click(
                                thumbnail_index=thumbnail_index,
                                thumbnail_selector=f"{selector}:nth-child({thumbnail_index + 1})",
                                click_success=False
                            )
                        
                        # Wait before retrying
                        if attempt < max_click_attempts - 1:
                            await page.wait_for_timeout(1000)
                            
                if thumbnail_clicked:
                    break
            
            if not thumbnail_clicked:
                logger.error(f"Failed to click thumbnail {thumbnail_index}")
                return False
            
            # Set up download handling before clicking download button
            download_path = Path(self.config.downloads_folder)
            logger.debug(f"Monitoring download directory: {download_path}")
            
            # Get initial file list
            initial_files = set(download_path.glob('*')) if download_path.exists() else set()
            logger.debug(f"Initial files in directory: {len(initial_files)}")
            
            # CRITICAL FIX: Enhanced content loading validation with landmark-based approach
            await page.wait_for_timeout(1500)  # Increased wait time
            
            # Validate content is properly loaded for this thumbnail
            content_loaded = await self.validate_content_loaded_for_thumbnail(page, thumbnail_index)
            
            # Enhanced context validation with multiple checks
            context_validation = await self._validate_thumbnail_context(page, thumbnail_index)
            if self.debug_logger:
                self.debug_logger.log_step(thumbnail_index, "PRE_EXTRACTION_CONTEXT_VALIDATION", {
                    **context_validation,
                    "content_loaded": content_loaded,
                    "timestamp": datetime.now().isoformat()
                })
            
            # CRITICAL: More robust content validation with retries
            validation_attempts = 0
            max_validation_attempts = 3
            content_ready = False
            
            while validation_attempts < max_validation_attempts and not content_ready:
                validation_attempts += 1
                
                # Check for landmark elements that indicate content is loaded
                landmark_checks = await self._perform_landmark_readiness_checks(page)
                
                if landmark_checks['creation_time_visible'] and (landmark_checks['prompt_content_visible'] or landmark_checks['media_content_visible']):
                    content_ready = True
                    logger.info(f"Landmark validation passed for thumbnail {thumbnail_index} (attempt {validation_attempts})")
                else:
                    logger.debug(f"Landmark validation failed for thumbnail {thumbnail_index} (attempt {validation_attempts}): {landmark_checks}")
                    if validation_attempts < max_validation_attempts:
                        await page.wait_for_timeout(2000)  # Wait before retry
            
            if not content_ready:
                logger.warning(f"Content readiness validation failed after {max_validation_attempts} attempts for thumbnail {thumbnail_index}")
                # Continue but log the issue
            
            # LANDMARK STRATEGY: Extract metadata using enhanced landmark-based approach
            metadata_dict = await self.extract_metadata_with_landmark_strategy(page, thumbnail_index)
            if not metadata_dict or not metadata_dict.get('generation_date') or metadata_dict.get('generation_date') == 'Unknown':
                logger.warning(f"Landmark strategy failed for thumbnail {thumbnail_index}, trying legacy extraction")
                # Fallback to original method
                metadata_dict = await self.extract_metadata_from_page(page)
                
            if not metadata_dict:
                logger.warning(f"All metadata extraction failed for thumbnail {thumbnail_index}, using defaults")
                metadata_dict = {'generation_date': 'Unknown', 'prompt': 'Unknown'}
            
            # DEBUG: Log extracted metadata with enhanced details and landmark info
            if self.debug_logger:
                extraction_success = bool(metadata_dict and metadata_dict.get('generation_date', 'Unknown') != 'Unknown')
                self.debug_logger.log_metadata_extraction(
                    thumbnail_index=thumbnail_index,
                    extraction_method="enhanced_landmark_strategy",
                    extracted_data=metadata_dict,
                    success=extraction_success
                )
                
                # Also log extraction strategy effectiveness
                self.debug_logger.log_step(thumbnail_index, "METADATA_EXTRACTION_RESULT", {
                    "success": extraction_success,
                    "method": "enhanced_landmark_strategy",
                    "has_date": bool(metadata_dict.get('generation_date') != 'Unknown'),
                    "has_prompt": bool(metadata_dict.get('prompt') != 'Unknown'),
                    "extraction_confidence": "high" if extraction_success else "low"
                })
            
            # FAST OPTIMIZATION: Check for duplicate creation time before downloading
            if self.config.duplicate_check_enabled and metadata_dict and metadata_dict.get('generation_date'):
                creation_time = metadata_dict.get('generation_date')
                if self.check_duplicate_exists(creation_time, existing_files):
                    if self.config.stop_on_duplicate:
                        logger.info(f"🛑 STOPPING: Duplicate creation time detected ({creation_time})")
                        logger.info("🔄 All newer files have already been downloaded")
                        self.should_stop = True
                        return False  # Stop the entire automation
                    else:
                        logger.warning(f"⏭️  Skipping duplicate file with creation time: {creation_time}")
                        return True  # Skip this file but continue
            
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
            
            # CRITICAL FIX: Enhanced download button sequence with proper SVG → Watermark flow
            download_initiated = await self.execute_download_sequence(page)
            if not download_initiated:
                logger.error("Failed to execute download sequence")
                page.remove_listener("download", handle_download)
                return False
            
            # The download sequence is now handled in execute_download_sequence method
            # This includes both the SVG icon click and watermark option handling
            logger.debug("Download sequence completed, checking for additional confirmations...")
            
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
            
            # FAST OPTIMIZATION: Quick wait for download to start, then check completion
            if self.config.fast_navigation_mode:
                await page.wait_for_timeout(1000)  # Reduced from 3000ms
                # Use fast completion detection
                completion_success = await self.wait_for_download_completion(
                    page, 
                    timeout=self.config.download_timeout if hasattr(self.config, 'download_timeout') else 8000
                )
                if not completion_success:
                    logger.warning(f"⏰ Download may still be in progress for thumbnail {thumbnail_index}")
            else:
                # Legacy wait time for compatibility
                await page.wait_for_timeout(3000)
            
            # Try to close Chrome download shelf if it appears
            await self.close_download_shelf(page)
            
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
            
            # DEBUG: Log file naming process
            if self.debug_logger:
                self.debug_logger.log_file_naming(
                    thumbnail_index=thumbnail_index,
                    original_filename=downloaded_file.name,
                    new_filename="PENDING",  # Will be updated after renaming
                    naming_data={
                        'use_descriptive_naming': self.config.use_descriptive_naming,
                        'unique_id': self.config.unique_id,
                        'creation_date': creation_date,
                        'naming_format': self.config.naming_format,
                        'date_format': self.config.date_format,
                        'extracted_metadata': metadata_dict
                    },
                    success=True
                )
            
            renamed_file = self.file_manager.rename_file(
                downloaded_file, 
                new_id=file_id,  # Legacy fallback
                creation_date=creation_date
            )
            if not renamed_file:
                logger.error(f"Failed to rename downloaded file")
                
                # DEBUG: Log renaming failure
                if self.debug_logger:
                    self.debug_logger.log_file_naming(
                        thumbnail_index=thumbnail_index,
                        original_filename=downloaded_file.name,
                        new_filename="FAILED",
                        naming_data={'error': 'rename_file returned None'},
                        success=False,
                        error="rename_file method returned None"
                    )
                return False
            
            # DEBUG: Log successful renaming
            if self.debug_logger:
                self.debug_logger.log_file_naming(
                    thumbnail_index=thumbnail_index,
                    original_filename=downloaded_file.name,
                    new_filename=renamed_file.name,
                    naming_data={
                        'use_descriptive_naming': self.config.use_descriptive_naming,
                        'unique_id': self.config.unique_id,
                        'creation_date': creation_date,
                        'naming_format': self.config.naming_format,
                        'date_format': self.config.date_format,
                        'final_result': str(renamed_file)
                    },
                    success=True
                )
            
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
                
                # Close download shelf again after successful download
                await self.close_download_shelf(page)
                
                return True
            else:
                logger.error(f"Failed to log download for {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in download_single_generation: {e}")
            return False
    
    async def check_generation_status(self, page, selector: str) -> Dict[str, Any]:
        """Check the status of a generation container to determine if it's completed, queued, or failed"""
        try:
            element = await page.query_selector(selector)
            if not element:
                return {'status': 'not_found', 'reason': 'Element not found'}
            
            # Get the text content to analyze
            element_text = await element.text_content()
            element_html = await element.inner_html()
            
            logger.debug(f"Checking generation status for {selector}")
            logger.debug(f"Element text: {element_text[:200] if element_text else 'None'}...")
            
            # Check for queuing status (highest priority)
            queuing_indicators = [
                "Queuing…",
                "Queuing...", 
                "In queue",
                "Waiting in queue",
                "Processing...",
                "Generating..."
            ]
            
            for indicator in queuing_indicators:
                if indicator in element_text:
                    logger.info(f"🔄 Generation {selector} is queued/processing - contains: '{indicator}'")
                    return {'status': 'queued', 'reason': indicator}
            
            # Check for failed generation patterns
            failed_generation_patterns = [
                "Failed to generate", 
                "Generation failed",
                "Error occurred", 
                "Try again later",
                "Generation error",
                "Something went wrong"
            ]
            
            for pattern in failed_generation_patterns:
                if pattern in element_text:
                    logger.warning(f"❌ Generation {selector} failed - contains: '{pattern}'")
                    return {'status': 'failed', 'reason': pattern}
            
            # Check if it's a valid completed generation
            # Look for thumbnail image or video content indicators
            has_thumbnail = await element.query_selector('img, video, .thumbnail') is not None
            has_content_indicators = any(indicator in element_text for indicator in [
                'Image to video',
                'Creation Time', 
                'Download',
                'Generate',
                'seconds'  # Duration indicator
            ])
            
            if has_thumbnail or has_content_indicators:
                logger.info(f"✅ Generation {selector} appears completed")
                return {'status': 'completed', 'reason': 'Has thumbnail or content indicators'}
            else:
                logger.debug(f"❓ Generation {selector} status unclear - no clear indicators")
                return {'status': 'unclear', 'reason': 'No clear completion indicators'}
                
        except Exception as e:
            logger.error(f"Error checking generation status for {selector}: {e}")
            return {'status': 'error', 'reason': str(e)}

    async def find_completed_generations_on_page(self, page) -> List[str]:
        """Find all completed generations on the initial /generate page, skipping queued ones"""
        try:
            logger.info("🔍 Scanning initial /generate page for completed generations...")
            
            completed_selectors = []
            
            # Check all potential generation containers (usually __1 through __10)
            for i in range(1, 11):  # Check first 10 containers
                selector = f"div[id$='__{i}']"
                status_info = await self.check_generation_status(page, selector)
                
                logger.debug(f"Container __{i}: Status = {status_info['status']} ({status_info['reason']})")
                
                if status_info['status'] == 'completed':
                    completed_selectors.append(selector)
                    logger.info(f"✅ Found completed generation: __{i}")
                elif status_info['status'] == 'queued':
                    logger.info(f"⏳ Skipping queued generation: __{i}")
                elif status_info['status'] == 'failed':
                    logger.warning(f"❌ Skipping failed generation: __{i}")
                else:
                    logger.debug(f"❓ Unknown status for __{i}: {status_info}")
            
            logger.info(f"📊 Found {len(completed_selectors)} completed generations out of 10 checked")
            
            if len(completed_selectors) == 0:
                logger.warning("⚠️ No completed generations found on initial page!")
                # Fallback: try the configured selector anyway
                if self.config.completed_task_selector:
                    logger.info(f"🔄 Fallback: trying configured selector {self.config.completed_task_selector}")
                    completed_selectors = [self.config.completed_task_selector]
            
            return completed_selectors
            
        except Exception as e:
            logger.error(f"Error finding completed generations: {e}")
            return []

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
            logger.info("🚀 Starting generation download automation with intelligent completed generation detection")
            
            # STEP 0: Scan for existing files to detect duplicates (if enabled)
            existing_files = set()
            if self.config.duplicate_check_enabled:
                existing_files = self.scan_existing_files()
                if existing_files and self.config.stop_on_duplicate:
                    logger.info(f"🔍 Found {len(existing_files)} existing files - will stop if duplicate creation time detected")
            
            # STEP 1: Configure Chromium browser settings to suppress download popups
            logger.info("⚙️ Configuring Chromium browser settings to suppress download notifications")
            settings_configured = await self._configure_chromium_download_settings(page)
            if not settings_configured:
                logger.warning("⚠️ Failed to configure Chromium settings, continuing with automation (downloads popup may appear)")
            else:
                logger.info("✅ Chromium download settings configured successfully")
            
            # STEP 2: Enhanced completed generation detection - scan page and skip queued generations
            navigation_success = False
            
            # Use the new intelligent detection system
            completed_generation_selectors = await self.find_completed_generations_on_page(page)
            
            if completed_generation_selectors:
                logger.info(f"🎯 Found {len(completed_generation_selectors)} completed generations, trying to navigate...")
                
                # Try each completed generation until one works
                for selector in completed_generation_selectors:
                    try:
                        logger.info(f"🔄 Attempting to navigate using completed generation: {selector}")
                        
                        # Try to click the element
                        await page.click(selector, timeout=5000)
                        await page.wait_for_timeout(2000)  # Wait for navigation
                        
                        # Verify navigation worked by checking for thumbnails
                        try:
                            await page.wait_for_selector(self.config.thumbnail_selector, timeout=3000)
                            logger.info(f"🎉 Successfully navigated to gallery using {selector}")
                            navigation_success = True
                            break
                        except:
                            logger.debug(f"No thumbnails found after clicking {selector}, trying next...")
                            continue
                            
                    except Exception as e:
                        logger.debug(f"Failed to navigate using {selector}: {e}")
                        continue
                        
            else:
                logger.warning("⚠️ No completed generations detected on initial page, trying fallback navigation...")
                
                # Fallback to configured selector if provided
                if self.config.completed_task_selector:
                    try:
                        logger.info(f"🔄 Trying configured selector: {self.config.completed_task_selector}")
                        await page.click(self.config.completed_task_selector, timeout=5000)
                        await page.wait_for_timeout(2000)
                        
                        # Check for thumbnails
                        try:
                            await page.wait_for_selector(self.config.thumbnail_selector, timeout=3000)
                            logger.info(f"🎉 Successfully navigated using configured selector")
                            navigation_success = True
                        except:
                            logger.warning("Configured selector navigation failed - no thumbnails found")
                            
                    except Exception as e:
                        logger.warning(f"Failed to use configured selector: {e}")
                
                # If still no success, try sequential approach as final fallback
                if not navigation_success:
                    logger.info("🔄 Trying sequential selector approach as final fallback...")
                    
                    # Extract starting number from config or use default
                    start_num = 8
                    if self.config.completed_task_selector:
                        import re
                        match = re.search(r'__(\d+)', self.config.completed_task_selector)
                        if match:
                            start_num = int(match.group(1))
                    
                    # Try selectors sequentially
                    for i in range(start_num, min(start_num + 5, 30)):  # Limit to 5 attempts
                        selector = f"div[id$='__{i}']"
                        try:
                            element = await page.query_selector(selector)
                            if not element:
                                continue
                            
                            await page.click(selector, timeout=5000)
                            await page.wait_for_timeout(2000)
                            
                            try:
                                await page.wait_for_selector(self.config.thumbnail_selector, timeout=3000)
                                logger.info(f"🎉 Sequential fallback navigation successful using {selector}")
                                navigation_success = True
                                break
                            except:
                                continue
                                
                        except Exception as e:
                            logger.debug(f"Sequential fallback failed for {selector}: {e}")
                            continue
            
            if not navigation_success:
                logger.warning("⚠️ Failed to navigate using any sequential selector, trying enhanced navigation...")
                try:
                    # Strategy 1: Direct URL navigation
                    await page.goto("https://wan.video/generate#completed", wait_until="networkidle", timeout=30000)
                    logger.info("Navigated to completed tasks via direct URL")
                    navigation_success = True
                except Exception as e:
                    logger.warning(f"Direct navigation failed, trying alternative: {e}")
                    try:
                        # Strategy 2: Click on completed tab if available
                        completed_tab_selectors = [
                            "button:has-text('Completed')",
                            "a:has-text('Completed')",
                            "div:has-text('Completed'):not(:has(div))",
                            "[data-tab='completed']",
                            ".tab-completed"
                        ]

                        for selector in completed_tab_selectors:
                            try:
                                await page.click(selector, timeout=5000)
                                logger.info(f"Clicked completed tab using: {selector}")
                                navigation_success = True
                                break
                            except:
                                continue
                    except:
                        logger.warning("Could not click completed tab, continuing with current page")

                # Wait for page to stabilize
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)  # Give dynamic content time to load
                
            if not navigation_success:
                error_msg = "Failed to navigate to completed tasks using any method"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            logger.info("Navigated to completed tasks page")
            
            # STEP 3: Navigate to starting thumbnail if specified (AFTER gallery is loaded)
            if self.config.start_from_thumbnail > 1:
                logger.info(f"🎯 Starting download from thumbnail #{self.config.start_from_thumbnail}")
                starting_navigation_success = await self.navigate_to_starting_thumbnail(page, self.config.start_from_thumbnail)
                
                if not starting_navigation_success:
                    logger.error(f"❌ Failed to navigate to starting thumbnail #{self.config.start_from_thumbnail}")
                    results['errors'].append(f"Failed to navigate to starting thumbnail #{self.config.start_from_thumbnail}")
                    results['success'] = False
                    return results
                
                logger.info(f"✅ Successfully positioned at starting thumbnail #{self.config.start_from_thumbnail}")
            else:
                logger.info("📍 Starting from thumbnail #1 (beginning of gallery)")
            
            # Wait for initial thumbnails to load
            try:

                        # Enhanced thumbnail detection with multiple strategies
                        thumbnail_found = False
                        thumbnail_strategies = [
                            # Strategy 1: Wait for configured selectors
                            {"method": "selector", "value": self.config.thumbnail_selector},
                            # Strategy 2: Wait for images in gallery
                            {"method": "selector", "value": "img[src*='wan']"},
                            # Strategy 3: Wait for any clickable items in container
                            {"method": "selector", "value": f"{self.config.thumbnail_container_selector} > div"},
                            # Strategy 4: Wait for generation items
                            {"method": "selector", "value": "div[id*='generation']"},
                            # Strategy 5: Generic image search
                            {"method": "selector", "value": "img[width][height]"}
                        ]

                        for strategy in thumbnail_strategies:
                            try:
                                elements = await page.wait_for_selector(
                                    strategy["value"], 
                                    timeout=5000,
                                    state="visible"
                                )
                                if elements:
                                    thumbnail_found = True
                                    actual_selector = strategy["value"]
                                    logger.info(f"Thumbnails found using strategy: {strategy['method']} with selector: {actual_selector}")
                                    # Update config to use working selector
                                    self.config.thumbnail_selector = actual_selector
                                    break
                            except Exception as e:
                                logger.debug(f"Strategy {strategy['method']} failed: {e}")
                                continue

                        if not thumbnail_found:
                            # Final fallback: Check if there are any images on the page
                            all_images = await page.query_selector_all("img")
                            if all_images:
                                logger.info(f"Found {len(all_images)} images on page, attempting to use them as thumbnails")
                                self.config.thumbnail_selector = "img"
                                thumbnail_found = True
                            else:
                                raise Exception("No thumbnails found with any strategy")

            except Exception as e:
                error_msg = f"Initial thumbnails did not load: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                return results
            
            # NEW: Proactive gallery loading phase to populate infinite scroll
            logger.info("🔄 Pre-loading gallery with initial scroll phase to populate thumbnails...")
            await self.preload_gallery_thumbnails(page)
            
            # Initialize thumbnail tracking
            self.visible_thumbnails_cache = await self.get_visible_thumbnail_identifiers(page)
            initial_thumbnail_count = len(self.visible_thumbnails_cache)
            logger.info(f"📊 After gallery pre-loading: {initial_thumbnail_count} thumbnails visible")
            
            # ENHANCED: Robust gallery navigation with duplicate prevention
            consecutive_failures = 0
            max_consecutive_failures = 5
            no_progress_cycles = 0
            max_no_progress_cycles = 3
            
            logger.info("🚀 Starting enhanced gallery navigation with production reliability")
            
            # Initialize session tracking
            self.processing_start_time = datetime.now()
            
            # NEW: Simplified landmark-based navigation loop
            # Start counting from the specified starting thumbnail
            thumbnail_count = self.config.start_from_thumbnail - 1  # Will be incremented to correct number in loop
            consecutive_failures = 0  # Initialize at the beginning
            
            while self.should_continue_downloading() and not self.gallery_end_detected:
                try:
                    # Find current active thumbnail to process
                    active_thumbnail = await self.find_active_thumbnail(page)
                    
                    if not active_thumbnail:
                        logger.info("📜 No active thumbnail found, attempting to find any thumbnail...")
                        
                        # Try to find any thumbnail container and click it to make it active
                        all_containers = await page.query_selector_all("div[class*='thumsCou']")
                        if all_containers:
                            first_container = all_containers[0]
                            logger.info("🎯 Clicking first thumbnail container to make it active")
                            await first_container.click(timeout=3000)
                            await page.wait_for_timeout(500)
                            active_thumbnail = await self.find_active_thumbnail(page)
                        
                        if not active_thumbnail:
                            # Try scrolling to find more thumbnails
                            logger.info("📜 No thumbnails available, attempting scroll...")
                            scroll_success = await self.scroll_and_find_more_thumbnails(page)
                            if scroll_success:
                                results['scrolls_performed'] += 1
                                self.scroll_failure_count = 0
                                logger.info(f"✅ Scroll successful (total scrolls: {results['scrolls_performed']})")
                                await page.wait_for_timeout(1000)
                                continue
                            else:
                                self.scroll_failure_count += 1
                                logger.warning(f"⚠️ Scroll failed (failures: {self.scroll_failure_count}/{self.max_scroll_failures})")
                                
                                if self.scroll_failure_count >= self.max_scroll_failures:
                                    logger.info("🏁 Gallery end reached - too many scroll failures")
                                    self.gallery_end_detected = True
                                    break
                                
                                await page.wait_for_timeout(2000)
                                continue
                    
                    # Process current active thumbnail
                    if active_thumbnail:
                        thumbnail_count += 1
                        logger.info(f"🎯 Processing thumbnail #{thumbnail_count} (active landmark method)")
                        
                        # Create simplified thumbnail info for the download method
                        thumbnail_info = {
                            'element': active_thumbnail,
                            'unique_id': f"landmark_thumbnail_{thumbnail_count}",
                            'position': thumbnail_count - 1,
                            'visible': True,
                            'processed': False
                        }
                        
                        # Download the current active thumbnail
                        success = await self.download_single_generation_robust(page, thumbnail_info, existing_files)
                        
                        # Extract thumbnail_id for tracking purposes
                        thumbnail_id = thumbnail_info['unique_id']
                        
                        if success:
                            results['downloads_completed'] += 1
                            logger.info(f"✅ Successfully downloaded thumbnail #{thumbnail_count}")
                            consecutive_failures = 0  # Reset failure counter
                        else:
                            consecutive_failures += 1
                            logger.warning(f"⚠️ Failed to download thumbnail #{thumbnail_count} (consecutive failures: {consecutive_failures})")
                            
                            if consecutive_failures >= max_consecutive_failures:
                                logger.warning(f"🛑 Too many consecutive failures ({consecutive_failures}), stopping...")
                                break
                        
                        # Navigate to next thumbnail using landmark method
                        logger.info("🧭 Navigating to next thumbnail using landmark method...")
                        navigation_success = await self.navigate_to_next_thumbnail_landmark(page)
                        
                        if not navigation_success:
                            # Try scrolling to find more thumbnails
                            logger.info("📜 Navigation failed, trying scroll...")
                            scroll_success = await self.scroll_and_find_more_thumbnails(page)
                            if scroll_success:
                                results['scrolls_performed'] += 1
                                logger.info(f"✅ Scroll successful, continuing... (total scrolls: {results['scrolls_performed']})")
                                no_progress_cycles = 0
                            else:
                                no_progress_cycles += 1
                                logger.warning(f"⚠️ No navigation progress possible (cycle {no_progress_cycles}/{max_no_progress_cycles})")
                                
                                if no_progress_cycles >= max_no_progress_cycles:
                                    logger.info("🏁 Gallery end reached - no more navigation possible")
                                    self.gallery_end_detected = True
                                    break
                        else:
                            no_progress_cycles = 0  # Reset when navigation succeeds
                        
                        # Brief wait between thumbnails
                        await page.wait_for_timeout(1000)
                    
                except Exception as processing_error:
                    logger.error(f"Error during landmark-based thumbnail processing: {processing_error}")
                    consecutive_failures += 1
                    
                    # Ensure thumbnail_count is defined for error messages
                    if 'thumbnail_count' not in locals():
                        thumbnail_count = 0
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(f"🛑 Too many consecutive processing errors ({consecutive_failures}), stopping...")
                        break
                    
                    # Try to recover by finding any active thumbnail or navigating
                    logger.info("🔄 Attempting recovery...")
                    try:
                        # Try to navigate to next thumbnail to recover from error
                        recovery_success = await self.navigate_to_next_thumbnail_landmark(page)
                        if not recovery_success:
                            # Try scrolling as recovery
                            await self.scroll_and_find_more_thumbnails(page)
                    except Exception as recovery_error:
                        logger.error(f"Recovery attempt failed: {recovery_error}")
                    
                    await page.wait_for_timeout(2000)
                    continue
                
                if success:
                    # Mark thumbnail as processed and update tracking
                    self.processed_thumbnails.add(thumbnail_id)
                    results['downloads_completed'] = self.downloads_completed
                    consecutive_failures = 0  # Reset failure counter on success
                    self.last_successful_download = datetime.now()
                    logger.info(f"✅ Progress: {self.downloads_completed}/{self.config.max_downloads} downloads completed")
                    logger.info(f"📊 Session processed: {len(self.processed_thumbnails)} unique thumbnails")
                else:
                    # Track failed thumbnails to avoid reprocessing
                    self.failed_thumbnail_ids.add(thumbnail_id)
                    error_msg = f"Failed to download thumbnail: {thumbnail_id}"
                    logger.warning(error_msg)
                    results['errors'].append(error_msg)
                    consecutive_failures += 1
                    
                    # Enhanced failure handling
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(f"❌ Too many consecutive failures ({consecutive_failures}), stopping automation")
                        break
                    
                    # Log failure patterns for debugging
                    if len(self.failed_thumbnail_ids) > 0 and len(self.failed_thumbnail_ids) % 5 == 0:
                        failure_rate = len(self.failed_thumbnail_ids) / (len(self.processed_thumbnails) + len(self.failed_thumbnail_ids))
                        logger.warning(f"⚠️ High failure rate detected: {failure_rate:.2%} ({len(self.failed_thumbnail_ids)} failed)")
                
                results['total_thumbnails_processed'] = len(self.processed_thumbnails)
                
                # Smart delay between downloads based on fast mode
                delay = 1000 if self.config.fast_navigation_mode else 2000
                await page.wait_for_timeout(delay)
                
                # Log progress every 5 downloads
                if self.downloads_completed % 5 == 0 and self.downloads_completed > 0:
                    logger.info(f"📈 Batch progress: {len(self.processed_thumbnails)} thumbnails processed, {results['downloads_completed']} successful downloads")
            
            # Set final results
            results['success'] = True
            results['downloads_completed'] = self.downloads_completed
            
            if self.downloads_completed == 0:
                results['success'] = False
                results['errors'].append("No downloads were completed successfully")
            
            logger.info(f"🎉 Download automation completed successfully!")
            # Generate comprehensive session statistics
            session_duration = (datetime.now() - self.processing_start_time).total_seconds() if self.processing_start_time else 0
            avg_download_time = session_duration / results['downloads_completed'] if results['downloads_completed'] > 0 else 0
            success_rate = results['downloads_completed'] / (len(self.processed_thumbnails) + len(self.failed_thumbnail_ids)) if (len(self.processed_thumbnails) + len(self.failed_thumbnail_ids)) > 0 else 0
            
            logger.info(f"📊 Enhanced session statistics:")
            logger.info(f"   💾 Downloads: {results['downloads_completed']}/{self.config.max_downloads}")
            logger.info(f"   🔄 Scrolls performed: {results['scrolls_performed']}")
            logger.info(f"   🎯 Thumbnails processed: {results['total_thumbnails_processed']}")
            logger.info(f"   ❌ Failed thumbnails: {len(self.failed_thumbnail_ids)}")
            logger.info(f"   📈 Success rate: {success_rate:.1%}")
            logger.info(f"   ⏱️ Session duration: {session_duration:.1f}s")
            logger.info(f"   🚀 Avg per download: {avg_download_time:.1f}s")
            
        except Exception as e:
            error_msg = f"Critical error in download automation: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
        
        finally:
            results['end_time'] = datetime.now().isoformat()
            logger.info(f"🏁 Download automation session ended. Total downloads: {results['downloads_completed']}")
        
        return results
    
    async def _search_creation_time_backwards(self, parent_element, span_index: int) -> Optional[object]:
        """Search backwards from 'Inspiration Mode' parent to find 'Creation Time' + date"""
        logger.debug(f"   🔍 Searching backwards for 'Creation Time' + date from span {span_index}")
        
        try:
            # Get the parent container (likely the metadata container)
            metadata_container = await parent_element.evaluate_handle("el => el.parentElement")
            if not metadata_container:
                logger.debug("   ❌ No metadata container found")
                return None
            
            # Look for all child divs that might contain Creation Time
            child_divs = await metadata_container.query_selector_all("div")
            logger.debug(f"   📦 Found {len(child_divs)} child divs in metadata container")
            
            for i, div in enumerate(child_divs):
                try:
                    div_text = await div.text_content() or ""
                    
                    if "Creation Time" in div_text:
                        logger.debug(f"   ✅ Found 'Creation Time' in div {i}: '{div_text[:100]}...'")
                        
                        # Look for spans within this div
                        div_spans = await div.query_selector_all("span")
                        logger.debug(f"     Div has {len(div_spans)} spans")
                        
                        # Find Creation Time span and check for date in next span
                        creation_time_index = -1
                        for j, span in enumerate(div_spans):
                            span_text = await span.text_content() or ""
                            if "Creation Time" in span_text:
                                creation_time_index = j
                                break
                        
                        # Check if next span contains the date
                        if creation_time_index >= 0 and creation_time_index + 1 < len(div_spans):
                            date_span = div_spans[creation_time_index + 1]
                            date_text = await date_span.text_content() or ""
                            
                            # Validate this looks like a date
                            if self._is_valid_date_text(date_text):
                                logger.debug(f"     ✅ Found valid Creation Time date: '{date_text.strip()}'")
                                return metadata_container
                            else:
                                logger.debug(f"     ❌ Next span doesn't look like date: '{date_text.strip()}'")
                
                except Exception as e:
                    logger.debug(f"Error processing div {i}: {e}")
                    continue
            
            logger.debug("   ❌ No 'Creation Time' + date pair found")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for Creation Time: {e}")
            return None

    async def _analyze_metadata_container(self, metadata_container) -> Dict[str, Any]:
        """Analyze the metadata container properties and extract creation date"""
        try:
            container_text = await metadata_container.text_content() or ""
            container_class = await metadata_container.get_attribute('class') or 'no-class'
            container_id = await metadata_container.get_attribute('id') or 'no-id'
            
            # Get bounding box if possible
            bounding_box = None
            try:
                bounding_box = await metadata_container.bounding_box()
            except:
                pass
            
            # Extract creation date
            creation_date = None
            try:
                creation_time_spans = await metadata_container.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
                for time_span in creation_time_spans:
                    time_parent = await time_span.evaluate_handle("el => el.parentElement")
                    if time_parent:
                        parent_spans = await time_parent.query_selector_all("span")
                        if len(parent_spans) >= 2:
                            date_span = parent_spans[1]
                            date_text = await date_span.text_content()
                            if date_text and self._is_valid_date_text(date_text):
                                creation_date = date_text.strip()
                                break
            except Exception as e:
                logger.debug(f"Error extracting creation date: {e}")
            
            container_info = {
                'class': container_class,
                'id': container_id,
                'text_length': len(container_text),
                'text_sample': container_text[:300] + "..." if len(container_text) > 300 else container_text,
                'bounding_box': bounding_box,
                'creation_date': creation_date
            }
            
            logger.debug(f"   📦 Metadata container: class='{container_class}' id='{container_id}' text_length={len(container_text)} date={creation_date}")
            
            return container_info
            
        except Exception as e:
            logger.error(f"Error analyzing metadata container: {e}")
            return {'class': 'error', 'id': 'error', 'text_length': 0, 'text_sample': '', 'bounding_box': None, 'creation_date': None}

    def _is_valid_date_text(self, text: str) -> bool:
        """Check if text looks like a valid date"""
        if not text or len(text.strip()) < 10:
            return False
        
        text = text.strip()
        
        # Check for date indicators
        date_indicators = ['Aug', '2025', ':', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Sep', 'Oct', 'Nov', 'Dec']
        matches = sum(1 for indicator in date_indicators if indicator in text)
        
        return matches >= 2  # Should have at least month and year or time

    async def _search_prompt_in_container(self, metadata_container, span_index: int, page=None) -> Optional[Dict[str, str]]:
        """Search for prompt text within the metadata container using ellipsis pattern"""
        logger.debug(f"   🔍 Searching for prompt in metadata container from span {span_index}")
        
        try:
            # Look for ellipsis pattern within this container
            ellipsis_elements = await metadata_container.query_selector_all(f"*:has-text('{self.config.prompt_ellipsis_pattern}')")
            logger.debug(f"   📦 Found {len(ellipsis_elements)} elements with ellipsis in container")
            
            for i, element in enumerate(ellipsis_elements):
                try:
                    if not await element.is_visible():
                        continue
                    
                    # Look for span with aria-describedby within this element
                    prompt_span = await element.query_selector("span[aria-describedby]")
                    if prompt_span:
                        prompt_text = await prompt_span.text_content()
                        
                        # Check if prompt is truncated (ends with ellipsis or is suspiciously around 102 chars)
                        is_truncated = (prompt_text and (
                            len(prompt_text.strip()) in range(100, 106)  # Common truncation length
                        ))
                        
                        if is_truncated:
                            logger.debug(f"   ⚠️ Prompt appears truncated at {len(prompt_text)} chars: '{prompt_text[:50]}...'")
                            # Try to get full text from aria-describedby tooltip or other sources
                            try:
                                # First try: Get the full text from the tooltip/describedby element
                                aria_id = await prompt_span.get_attribute('aria-describedby')
                                if aria_id:
                                    tooltip_element = await metadata_container.query_selector(f"#{aria_id}")
                                    if tooltip_element:
                                        full_text = await tooltip_element.text_content()
                                        if full_text and len(full_text) > len(prompt_text):
                                            prompt_text = full_text
                                            logger.info(f"   ✅ Got full prompt from tooltip: {len(full_text)} chars")
                                
                                # Second try: Check if there's a title attribute with full text
                                title_text = await prompt_span.get_attribute('title')
                                if title_text and len(title_text) > len(prompt_text):
                                    prompt_text = title_text
                                    logger.info(f"   ✅ Got full prompt from title attribute: {len(title_text)} chars")
                                
                                # Third try: Click on prompt to expand it if possible
                                try:
                                    await prompt_span.click()
                                    await prompt_span.evaluate("el => new Promise(resolve => setTimeout(resolve, 500))")
                                    # Re-get the text after clicking
                                    expanded_text = await prompt_span.text_content()
                                    if expanded_text and len(expanded_text) > len(prompt_text):
                                        prompt_text = expanded_text
                                        logger.info(f"   ✅ Got full prompt after expansion: {len(expanded_text)} chars")
                                except:
                                    pass
                                    
                            except Exception as e:
                                logger.debug(f"   Error trying to get full prompt text: {e}")
                        
                        if prompt_text and self._is_valid_prompt_text(prompt_text):
                            logger.info(f"   ✅ Found valid prompt text ({len(prompt_text)} chars): '{prompt_text[:50]}...'")
                            
                            # Try to create a selector for this span
                            selector = None
                            try:
                                aria_describedby = await prompt_span.get_attribute('aria-describedby')
                                if aria_describedby:
                                    selector = f"span[aria-describedby='{aria_describedby}']"
                            except:
                                pass
                            
                            return {
                                'text': prompt_text.strip(),
                                'selector': selector
                            }
                        else:
                            logger.debug(f"   ❌ Invalid prompt text: '{prompt_text[:30]}...'")
                
                except Exception as e:
                    logger.debug(f"Error processing ellipsis element {i}: {e}")
                    continue
            
            logger.debug("   ❌ No valid prompt found in container")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for prompt in container: {e}")
            return None

    def _is_valid_prompt_text(self, text: str) -> bool:
        """Check if text looks like a valid prompt"""
        if not text:
            return False
        
        text = text.strip()
        
        # Basic length check
        if len(text) < 20 or len(text) > 1000:
            return False
        
        # Should not contain technical indicators
        invalid_indicators = [
            ':', '{', '}', 'anticon', 'display:', 'px', 'html', 'css', 
            'javascript', 'style', 'class', 'div', 'span'
        ]
        
        for indicator in invalid_indicators:
            if indicator in text.lower():
                return False
        
        # Should look like natural text
        if not text[0].isupper():
            return False
        
        # Should contain common words
        common_words = ['the', 'a', 'and', 'with', 'of', 'to', 'in', 'is', 'are', 'was', 'were']
        if not any(word in text.lower() for word in common_words):
            return False
        
        return True

    async def _extract_full_prompt_optimized(self, page, metadata: Dict[str, str]) -> bool:
        """
        Optimized prompt extraction using longest-div strategy.
        
        Based on analysis: DOM contains ~31 prompt divs with class 'sc-dDrhAi dnESm'
        - 30 divs have truncated text (103-106 chars)
        - 1 div has full prompt text (325+ chars)
        
        This method finds the div with longest text content.
        
        Returns:
            bool: True if full prompt was extracted successfully
        """
        try:
            logger.debug("🔍 Starting optimized longest-div prompt extraction")
            
            # Find all prompt divs with the configured class selector
            prompt_divs = await page.query_selector_all(self.config.prompt_class_selector)
            logger.info(f"📦 Found {len(prompt_divs)} prompt divs with selector '{self.config.prompt_class_selector}'")
            
            if not prompt_divs:
                logger.warning(f"⚠️ No prompt divs found with selector: {self.config.prompt_class_selector}")
                return False
            
            # Find the div with the longest text content (this should be the full prompt)
            longest_div = None
            longest_text = ""
            longest_length = 0
            
            for i, div in enumerate(prompt_divs):
                try:
                    if not await div.is_visible():
                        continue
                    
                    div_text = await div.text_content()
                    if not div_text:
                        continue
                    
                    # Look for divs that contain the expected prompt content
                    div_text_clean = div_text.strip()
                    text_length = len(div_text_clean)
                    
                    # Check if this looks like a prompt (contains configured prompt indicators)
                    contains_prompt_words = any(word in div_text_clean.lower() for word in self.config.prompt_indicators)
                    
                    if contains_prompt_words and text_length > 50:  # Must be substantial text
                        logger.debug(f"📏 Prompt div {i+1}: {text_length} chars - '{div_text_clean[:60]}...'")
                        
                        if text_length > longest_length:
                            longest_length = text_length
                            longest_text = div_text_clean
                            longest_div = div
                            logger.debug(f"🏆 New longest: {text_length} chars")
                            
                except Exception as e:
                    logger.debug(f"Error processing prompt div {i}: {e}")
                    continue
            
            # Use the longest text found (must be significantly longer than truncated text)
            if longest_div and longest_length > self.config.min_prompt_length:
                logger.info(f"🎉 SUCCESS! Found full prompt with {longest_length} characters")
                logger.info(f"📝 Full prompt preview: {longest_text[:100]}...")
                
                # Validate the text quality
                if self._is_valid_prompt_text(longest_text):
                    metadata['prompt'] = longest_text
                    logger.info(f"✅ Full prompt extracted and validated ({longest_length} chars)")
                    return True
                else:
                    logger.warning(f"⚠️ Longest text failed validation: {longest_length} chars")
                    
            elif longest_length > 0:
                logger.warning(f"⚠️ Longest prompt found was only {longest_length} chars (expected >150)")
                logger.warning(f"⚠️ Text preview: '{longest_text[:100]}...'")
            else:
                logger.warning("⚠️ No prompt text found in any div")
            
            # Fallback: use the longest text even if it's truncated
            if longest_text and self._is_valid_prompt_text(longest_text):
                metadata['prompt'] = longest_text
                logger.info(f"📝 Using longest available text as fallback ({longest_length} chars)")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Error in optimized prompt extraction: {e}")
            return False

    async def _configure_chromium_download_settings(self, page) -> bool:
        """Configure Chromium browser settings to suppress download notifications"""
        try:
            logger.info("🔧 Chromium download notification suppression is handled by browser launch arguments")
            logger.info("✅ Browser was launched with comprehensive download suppression flags:")
            logger.info("   - --disable-features=DownloadShelf")
            logger.info("   - --disable-download-notification")
            logger.info("   - --disable-features=DownloadBubble,DownloadBubbleV2")
            logger.info("   - --disable-features=DownloadNotification")
            logger.info("📄 No runtime settings changes required - download popups are suppressed at browser level")
            
            # Small delay to simulate configuration time
            await page.wait_for_timeout(500)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in download settings configuration: {e}")
            return False

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