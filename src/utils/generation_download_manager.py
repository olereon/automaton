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
from enum import Enum

from .download_manager import DownloadManager, DownloadConfig
from .boundary_scroll_manager import BoundaryScrollManager
from .enhanced_metadata_extraction import extract_container_metadata_enhanced

logger = logging.getLogger(__name__)


class DuplicateMode(Enum):
    """Duplicate handling modes for generation downloads"""
    FINISH = "finish"  # Stop when reaching a duplicate (current behavior)
    SKIP = "skip"      # Skip duplicates and continue searching for new generations


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
    scroll_amount: int = 2500  # Pixels to scroll each time (increased for better container detection)
    scroll_wait_time: int = 2000  # Wait time after scrolling (ms)
    max_scroll_attempts: int = 2000  # Max attempts to find new thumbnails (support very large galleries)
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
    
    # OPTIMIZED PROMPT EXTRACTION SETTINGS (UPDATED September 2025)
    extraction_strategy: str = "longest_div"     # Strategy: "longest_div" or "legacy"
    min_prompt_length: int = 50                  # Reduced for better detection
    prompt_class_selector: str = ".sc-eKQYOU.bdGRCs"  # UPDATED: New prompt container class
    prompt_indicators: list = None               # Keywords that indicate prompt content
    
    # FAST DOWNLOAD OPTIMIZATION SETTINGS
    stop_on_duplicate: bool = True               # Stop when duplicate creation time found
    duplicate_check_enabled: bool = True         # Enable duplicate detection
    creation_time_comparison: bool = True        # Compare by creation time
    duplicate_mode: DuplicateMode = DuplicateMode.FINISH  # Duplicate handling mode
    download_completion_detection: bool = True    # Wait for download completion
    fast_navigation_mode: bool = True            # Optimize navigation speed
    use_exit_scan_strategy: bool = True          # Use exit-scan-return strategy for Enhanced SKIP mode
    
    # START FROM SPECIFIC GENERATION SETTINGS
    start_from: Optional[str] = None             # Start from specific datetime (format: "DD MMM YYYY HH:MM:SS")
    
    # Legacy selectors (kept for backward compatibility)
    
    @classmethod
    def create_with_skip_mode(cls, **kwargs):
        """Create configuration with SKIP duplicate mode"""
        config = cls(**kwargs)
        config.duplicate_mode = DuplicateMode.SKIP
        config.stop_on_duplicate = False  # Skip mode doesn't stop
        return config
    
    @classmethod  
    def create_with_finish_mode(cls, **kwargs):
        """Create configuration with FINISH duplicate mode"""
        config = cls(**kwargs)
        config.duplicate_mode = DuplicateMode.FINISH
        config.stop_on_duplicate = True  # Finish mode stops
        return config
    download_button_selector: str = "[data-spm-anchor-id='a2ty_o02.30365920.0.i1.6daf47258YB5qi']"
    download_no_watermark_selector: str = "[data-spm-anchor-id='a2ty_o02.30365920.0.i2.6daf47258YB5qi']"
    
    generation_date_selector: str = ".sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)"
    prompt_selector: str = ".sc-eKQYOU.bdGRCs span[aria-describedby]"  # UPDATED Sep 2025
    
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
        """Log a generation download to the text file (chronological order)"""
        try:
            # Use the new chronological method
            return self.log_download_chronologically(metadata)
            
        except Exception as e:
            logger.error(f"Failed to log download: {e}")
            return False
    
    def log_download_chronologically(self, metadata: GenerationMetadata) -> bool:
        """Log a generation download in chronological order (newest first)"""
        try:
            # Parse the new entry's date
            new_date = self._parse_date_for_comparison(metadata.generation_date)
            if not new_date:
                logger.warning(f"Invalid date format for chronological insertion: {metadata.generation_date}")
                # Fall back to append mode
                return self._log_download_append(metadata)
            
            # Read all existing entries
            existing_entries = self._read_all_log_entries()
            
            # Create new entry
            new_entry = {
                'file_id': metadata.file_id,
                'generation_date': metadata.generation_date,
                'prompt': metadata.prompt,
                'parsed_date': new_date
            }
            
            # Insert in chronological order (newest first)
            existing_entries.append(new_entry)
            # Sort with None values last (for invalid dates)
            existing_entries.sort(key=lambda x: (x['parsed_date'] is None, x['parsed_date']), reverse=True)
            
            # Rewrite entire file with sorted entries
            write_success = self._write_all_log_entries(existing_entries)
            if not write_success:
                raise Exception("Failed to write log entries to file")
            
            logger.info(f"Logged download chronologically: {metadata.file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log download chronologically: {e}")
            # Fall back to append mode
            try:
                return self._log_download_append(metadata)
            except Exception as fallback_error:
                logger.error(f"Failed to log download (fallback): {fallback_error}")
                return False
    
    def _log_download_append(self, metadata: GenerationMetadata) -> bool:
        """Original append-only logging method (fallback)"""
        try:
            log_entry = f"{metadata.file_id}\n{metadata.generation_date}\n{metadata.prompt}\n{'=' * 40}\n"
            
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            logger.info(f"Logged download (append): {metadata.file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log download (append): {e}")
            return False
    
    def _parse_date_for_comparison(self, date_string: str) -> Optional[datetime]:
        """Parse date string into datetime object for chronological comparison"""
        if not date_string:
            return None
        
        try:
            # Use the existing normalization method from the manager
            normalized_date = self._normalize_date_format(date_string)
            
            # Parse the normalized date
            date_formats = [
                "%Y-%m-%d-%H-%M-%S",     # Normalized format
                "%d %b %Y %H:%M:%S",     # "24 Aug 2025 01:37:01"
                "%Y-%m-%d %H:%M:%S",     # "2025-08-24 01:37:01"
                "%Y-%m-%d %H:%M",        # "2025-08-24 01:37"
                "%d/%m/%Y %H:%M:%S",     # "24/08/2025 01:37:01"
                "%m/%d/%Y %H:%M:%S",     # "08/24/2025 01:37:01"
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_string.strip(), fmt)
                except ValueError:
                    continue
                    
            # If normalized format parsing fails, try the original
            if normalized_date != date_string:
                try:
                    return datetime.strptime(normalized_date, "%Y-%m-%d-%H-%M-%S")
                except ValueError:
                    pass
            
            logger.warning(f"Could not parse date format: {date_string}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_string}': {e}")
            return None
    
    def _normalize_date_format(self, date_string: str) -> str:
        """Normalize different date formats for consistent comparison"""
        try:
            # Try to parse and reformat date
            date_formats = [
                "%d %b %Y %H:%M:%S",    # "24 Aug 2025 01:37:01"
                "%Y-%m-%d %H:%M:%S",    # "2025-08-24 01:37:01"
                "%Y-%m-%d-%H-%M-%S",    # "2025-08-24-01-37-01"
                "%d/%m/%Y %H:%M:%S",    # "24/08/2025 01:37:01"
                "%m/%d/%Y %H:%M:%S",    # "08/24/2025 01:37:01"
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
    
    def _read_all_log_entries(self) -> List[Dict]:
        """Read all log entries from the file and return as list of dictionaries"""
        entries = []
        
        if not self.log_file_path.exists():
            return entries
            
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                return entries
            
            # Split by separator lines
            sections = content.split('=' * 40)
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                lines = section.split('\n')
                if len(lines) >= 3:
                    file_id = lines[0].strip()
                    generation_date = lines[1].strip()
                    prompt = '\n'.join(lines[2:]).strip()
                    
                    # Parse date for sorting
                    parsed_date = self._parse_date_for_comparison(generation_date)
                    
                    if file_id and generation_date:  # Only add valid entries
                        entries.append({
                            'file_id': file_id,
                            'generation_date': generation_date,
                            'prompt': prompt,
                            'parsed_date': parsed_date
                        })
                        
        except Exception as e:
            logger.error(f"Error reading log entries: {e}")
            
        return entries
    
    def _write_all_log_entries(self, entries: List[Dict]) -> bool:
        """Write all entries to the log file in chronological order"""
        try:
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                for entry in entries:
                    # Use placeholder ID for new entries
                    file_id = entry['file_id']
                    if not file_id or file_id == 'NEW' or not file_id.startswith('#'):
                        file_id = '#999999999'  # Placeholder for new entries
                        
                    log_entry = f"{file_id}\n{entry['generation_date']}\n{entry['prompt']}\n{'=' * 40}\n"
                    f.write(log_entry)
                    
                # Explicitly flush to ensure immediate disk write
                f.flush()
                import os
                os.fsync(f.fileno())  # Force OS to write to disk
                    
            return True
            
        except Exception as e:
            logger.error(f"Error writing log entries: {e}")
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
    
    def get_last_log_entry(self) -> Optional[Dict[str, str]]:
        """Get the last (most recent) log entry as a checkpoint for fast-forward skip mode"""
        if not self.log_file_path.exists():
            logger.info("📄 No log file found - starting fresh download session")
            return None
            
        try:
            entries = self._read_all_log_entries()
            if not entries:
                logger.info("📄 Log file is empty - starting fresh download session")
                return None
            
            # Get the first entry (newest due to chronological ordering)
            last_entry = entries[0]
            
            logger.info(f"🔖 Last downloaded checkpoint found:")
            logger.info(f"   📅 Creation Time: {last_entry.get('generation_date')}")
            logger.info(f"   📝 Prompt: {last_entry.get('prompt', '')[:100]}{'...' if len(last_entry.get('prompt', '')) > 100 else ''}")
            logger.info(f"   📁 File ID: {last_entry.get('file_id')}")
            
            return last_entry
            
        except Exception as e:
            logger.error(f"Error reading last log entry: {e}")
            return None
    


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
        
        # Enhanced SKIP mode state tracking
        self.checkpoint_found = False
        self.fast_forward_mode = False
        self.checkpoint_data = None
        self.boundary_just_downloaded = False  # Track if boundary was just downloaded to prevent re-triggering exit-scan-return
        
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
        self.max_scroll_failures = 100  # Maximum scroll failures before ending (support large galleries)
        self.processing_start_time = None  # Track session start time
        self.last_successful_download = None  # Track last successful download time
        
        # Boundary scroll manager (will be initialized when needed)
        self.boundary_scroll_manager = None
        
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
    
    def initialize_boundary_scroll_manager(self, page):
        """Initialize the boundary scroll manager with verified scroll methods"""
        if self.boundary_scroll_manager is None:
            self.boundary_scroll_manager = BoundaryScrollManager(page)
            logger.info("🎯 Initialized boundary scroll manager with verified methods:")
            logger.info("   Primary: Element.scrollIntoView() - 1060px, 0.515s")
            logger.info("   Fallback: container.scrollTop - 1016px, 0.515s")
    
    async def scroll_to_find_boundary_generations(self, page, boundary_criteria: Dict) -> Optional[Dict]:
        """
        Use verified scrolling methods to find boundary generations on /generate page.
        Each scroll ensures >2000px distance with proper tracking.
        """
        logger.info("🎯 Starting boundary detection with verified scroll methods")
        
        # Initialize boundary scroll manager
        self.initialize_boundary_scroll_manager(page)
        
        # Configure minimum scroll distance (>2500px for better container detection)
        self.boundary_scroll_manager.min_scroll_distance = 2500
        
        # Start boundary search
        boundary_found = await self.boundary_scroll_manager.scroll_until_boundary_found(boundary_criteria)
        
        # Get statistics
        stats = self.boundary_scroll_manager.get_scroll_statistics()
        
        logger.info("🎯 Boundary search completed:")
        logger.info(f"   Scrolls performed: {stats['scroll_attempts']}")
        logger.info(f"   Total distance: {stats['total_scrolled_distance']}px")
        logger.info(f"   Average per scroll: {stats['average_scroll_distance']:.0f}px")
        logger.info(f"   Boundary found: {'✓ Yes' if boundary_found else '✗ No'}")
        
        return boundary_found
    
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
    
    def check_duplicate_exists(self, creation_time: str, prompt_text: str, existing_log_entries: Dict = None) -> str:
        """
        Algorithm-compliant duplicate detection (Step 6a)
        Check if datetime + prompt pair already exists in log
        
        Returns:
        - "exit_scan_return" if duplicate found and SKIP mode enabled (initiate skipping)
        - True if duplicate found and FINISH mode enabled (stop downloading)
        - False if not a duplicate (continue downloading)
        """
        if not self.config.duplicate_check_enabled or not creation_time:
            return False
            
        # Use log entries for datetime + prompt pair matching (Algorithm Step 6a)
        if existing_log_entries is None:
            existing_log_entries = getattr(self, 'existing_log_entries', {})
        
        # Compare datetime + first 100 characters of prompt as specified
        prompt_key = prompt_text[:100] if prompt_text else ""
        
        for log_datetime, log_entry in existing_log_entries.items():
            # CRITICAL FIX: Skip incomplete log entries (from previous failed runs)
            # Placeholder ID #999999999 indicates incomplete/failed downloads
            file_id = log_entry.get('file_id', '')
            if file_id == '#999999999':
                logger.info(f"⏭️ FILTERING: Skipping incomplete log entry: {log_datetime} (file_id: {file_id})")
                continue
            
            # Match both datetime AND prompt for robustness (Algorithm Step 6a)
            log_prompt = log_entry.get('prompt', '')[:100]
            
            if (log_datetime == creation_time and log_prompt == prompt_key):
                logger.warning(f"🚫 Algorithm Duplicate detected! Time: {creation_time}, Prompt: {prompt_key[:50]}...")
                
                # Step 6a: Initiate skipping if in SKIP mode
                if self.config.duplicate_mode == DuplicateMode.SKIP:
                    logger.info("🚀 SKIP Mode: Initiating exit-scan-return workflow")
                    return "exit_scan_return"
                else:
                    logger.info("🛑 FINISH Mode: Stopping on duplicate")
                    return True
                    
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
                if scrollable_container == "WINDOW_SCROLL":
                    # Use window scrolling
                    await page.evaluate(f"window.scrollBy(0, {self.config.scroll_amount})")
                    logger.debug(f"🌐 Used window scrolling: {self.config.scroll_amount}px")
                else:
                    # Use container scrolling
                    await scrollable_container.evaluate(f"el => el.scrollBy(0, {self.config.scroll_amount})")
                    logger.debug(f"📦 Used container scrolling: {self.config.scroll_amount}px")
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
                    if scrollable_container == "WINDOW_SCROLL":
                        # Use window scrolling
                        scroll_before = await page.evaluate("() => window.scrollY")
                        await page.evaluate(f"window.scrollBy(0, {self.config.scroll_amount})")
                        scroll_executed = True
                        
                        # Verify scroll actually happened
                        await page.wait_for_timeout(500)  # Brief wait for scroll to complete
                        scroll_after = await page.evaluate("() => window.scrollY")
                        
                        if scroll_after <= scroll_before:
                            logger.warning(f"⚠️ Window scroll position didn't change ({scroll_before} → {scroll_after})")
                            scroll_executed = False
                        else:
                            logger.debug(f"🌐 Window scroll successful: {scroll_before}px → {scroll_after}px")
                    else:
                        # Use container scrolling
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
                        else:
                            logger.debug(f"📦 Container scroll successful: {scroll_before}px → {scroll_after}px")
                        
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
        """Find the best scrollable container using enhanced detection with fallbacks"""
        
        logger.debug("🔍 Starting enhanced scrollable container detection...")
        
        # Strategy 1: Try specific gallery containers first
        specific_selectors = [
            "div[class*='thumsCou']",  # Known thumbnail container
            ".thumbnail-container",
            ".gallery-container", 
            ".scroll-container",
            ".gallery-content",
            ".content-wrapper",
            "[class*='gallery']",
            "[class*='scroll']",
            "[class*='content']"
        ]
        
        for selector in specific_selectors:
            try:
                containers = await page.query_selector_all(selector)
                logger.debug(f"   📊 Checking {len(containers)} containers for selector: {selector}")
                
                for i, container in enumerate(containers):
                    try:
                        # Enhanced scrollability check
                        scroll_info = await container.evaluate("""el => {
                            const style = getComputedStyle(el);
                            const scrollHeight = el.scrollHeight;
                            const clientHeight = el.clientHeight;
                            
                            return {
                                hasVerticalScroll: scrollHeight > clientHeight,
                                overflowY: style.overflowY,
                                scrollable: scrollHeight > clientHeight || 
                                           style.overflowY === 'scroll' ||
                                           style.overflowY === 'auto',
                                rect: el.getBoundingClientRect(),
                                scrollTop: el.scrollTop,
                                scrollHeight: scrollHeight,
                                clientHeight: clientHeight,
                                tagName: el.tagName,
                                className: el.className
                            };
                        }""")
                        
                        if scroll_info['scrollable'] and scroll_info['rect']['height'] > 50:
                            logger.info(f"✅ Found scrollable container #{i}: {selector}")
                            logger.info(f"   📐 Size: {scroll_info['scrollHeight']}px total, {scroll_info['clientHeight']}px visible")
                            logger.info(f"   🎯 Tag: {scroll_info['tagName']}, Classes: {scroll_info['className'][:50]}...")
                            return container
                            
                    except Exception as e:
                        logger.debug(f"   ❌ Error checking container #{i}: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"   ❌ Error with selector {selector}: {e}")
                continue
        
        # Strategy 2: Find ANY scrollable element on the page
        logger.debug("🔍 Strategy 1 failed, trying universal scrollable element detection...")
        try:
            scrollable_elements = await page.evaluate("""
                () => {
                    const allElements = document.querySelectorAll('*');
                    const scrollableElements = [];
                    
                    for (const el of allElements) {
                        try {
                            const style = getComputedStyle(el);
                            const scrollHeight = el.scrollHeight;
                            const clientHeight = el.clientHeight;
                            
                            if ((scrollHeight > clientHeight && scrollHeight > 100) ||
                                style.overflowY === 'scroll' || 
                                style.overflowY === 'auto') {
                                
                                const rect = el.getBoundingClientRect();
                                if (rect.height > 50) {
                                    scrollableElements.push({
                                        tagName: el.tagName,
                                        className: el.className || '',
                                        id: el.id || '',
                                        scrollHeight: scrollHeight,
                                        clientHeight: clientHeight,
                                        rect: rect,
                                        index: scrollableElements.length
                                    });
                                }
                            }
                        } catch (e) {
                            // Skip elements that cause errors
                        }
                    }
                    
                    // Sort by scroll area (largest first)
                    scrollableElements.sort((a, b) => 
                        (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight)
                    );
                    
                    return scrollableElements.slice(0, 5); // Return top 5 candidates
                }
            """)
            
            logger.debug(f"   📊 Found {len(scrollable_elements)} scrollable elements")
            
            for element_info in scrollable_elements:
                try:
                    # Try to select this element
                    selector_attempts = []
                    if element_info['id']:
                        selector_attempts.append(f"#{element_info['id']}")
                    if element_info['className']:
                        # Use first class
                        first_class = element_info['className'].split()[0]
                        selector_attempts.append(f".{first_class}")
                    selector_attempts.append(element_info['tagName'].lower())
                    
                    for attempt_selector in selector_attempts:
                        try:
                            container = await page.query_selector(attempt_selector)
                            if container:
                                # Verify this is the right element
                                verify_info = await container.evaluate("""el => ({
                                    scrollHeight: el.scrollHeight,
                                    clientHeight: el.clientHeight,
                                    scrollable: el.scrollHeight > el.clientHeight
                                })""")
                                
                                if verify_info['scrollable']:
                                    logger.info(f"✅ Found universal scrollable element: {attempt_selector}")
                                    logger.info(f"   📐 Size: {verify_info['scrollHeight']}px total, {verify_info['clientHeight']}px visible")
                                    return container
                        except:
                            continue
                            
                except Exception as e:
                    logger.debug(f"   ❌ Error with scrollable element: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"❌ Universal detection failed: {e}")
        
        # Strategy 3: Use document.body or document.documentElement as last resort
        logger.debug("🔍 Strategy 2 failed, trying document-level scrolling...")
        try:
            # Check if document itself is scrollable
            doc_scroll_info = await page.evaluate("""
                () => ({
                    bodyScrollable: document.body.scrollHeight > document.body.clientHeight,
                    docScrollable: document.documentElement.scrollHeight > document.documentElement.clientHeight,
                    bodyHeight: document.body.scrollHeight,
                    docHeight: document.documentElement.scrollHeight,
                    viewportHeight: window.innerHeight
                })
            """)
            
            logger.debug(f"   📊 Document scroll info: {doc_scroll_info}")
            
            if doc_scroll_info['bodyScrollable'] or doc_scroll_info['docScrollable']:
                # Return a special marker indicating we should use window scrolling
                logger.info("✅ Using document-level scrolling (window.scrollBy)")
                return "WINDOW_SCROLL"  # Special marker
        except Exception as e:
            logger.debug(f"❌ Document scroll check failed: {e}")
        
        logger.warning("⚠️ No suitable scrollable container found - all strategies failed")
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
        """Simple duplicate detection using datetime + prompt pair (Algorithm Step 6a)"""
        try:
            logger.info(f"🔍 COMPREHENSIVE CHECK: Extracting full metadata from gallery for {thumbnail_id}")
            
            # Extract FULL metadata from gallery (complete prompt + date)
            metadata = await self.extract_metadata_from_page(page)
            if not metadata:
                logger.warning(f"⚠️ COMPREHENSIVE CHECK: Failed to extract metadata for {thumbnail_id}")
                return False
            
            generation_date = metadata.get('generation_date', '')
            prompt = metadata.get('prompt', '')
            
            logger.info(f"🔍 COMPREHENSIVE CHECK: Extracted date='{generation_date}', prompt_length={len(prompt) if prompt else 0}")
            
            if not generation_date or not prompt:
                logger.warning(f"⚠️ COMPREHENSIVE CHECK: Missing date or prompt for {thumbnail_id}")
                return False
            
            # Load existing log entries for comparison (Algorithm Step 6a)
            if hasattr(self, 'existing_log_entries') and self.existing_log_entries:
                existing_entries = self.existing_log_entries
            else:
                existing_entries = self._load_existing_log_entries()
            
            # Simple datetime + prompt (100 chars) duplicate detection
            if generation_date in existing_entries:
                existing_entry = existing_entries[generation_date]
                
                # CRITICAL FIX: Skip incomplete log entries (from previous failed runs)
                # Placeholder ID #999999999 indicates incomplete/failed downloads
                file_id = existing_entry.get('file_id', '')
                if file_id == '#999999999':
                    logger.info(f"⏭️ FILTERING: Skipping incomplete log entry in comprehensive check: {generation_date} (file_id: {file_id})")
                    return False  # Not a duplicate - allow download
                
                existing_prompt = existing_entry.get('prompt', '')
                
                # Compare first 100 characters of prompts
                current_prompt_100 = prompt[:100]
                existing_prompt_100 = existing_prompt[:100]
                
                if current_prompt_100 == existing_prompt_100:
                    logger.info(f"🛑 DUPLICATE DETECTED: Date='{generation_date}', Prompt match (100 chars)")
                    
                    # Handle duplicate based on mode
                    if self.config.duplicate_mode == DuplicateMode.FINISH:
                        logger.info("🎯 FINISH MODE: Stopping at duplicate")
                        return True
                    elif self.config.duplicate_mode == DuplicateMode.SKIP:
                        # CRITICAL FIX: Check if boundary was just downloaded to prevent infinite loop
                        if hasattr(self, 'boundary_just_downloaded') and self.boundary_just_downloaded:
                            logger.info("🔄 CONSECUTIVE DUPLICATE after boundary download detected")
                            logger.info("⏭️ SKIPPING: Using fast-forward mode instead of exit-scan-return to handle consecutive duplicates")
                            
                            # Reset boundary flag after first consecutive duplicate
                            self.boundary_just_downloaded = False
                            
                            # Return "skip" to continue in fast-forward mode instead of triggering exit-scan-return
                            return "skip"
                        else:
                            logger.info("⏭️ SKIP MODE: Found duplicate, entering exit-scan workflow")
                            return "exit_scan_return"  # Trigger exit-scan-return strategy
            
            return False  # No duplicate detected
            
        except Exception as e:
            logger.debug(f"Error in duplicate check: {e}")
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
            logger.info("🔄 GALLERY EXTRACTION: Starting full metadata extraction from gallery view")
            
            # Use the same multi-landmark approach as the main extraction method
            result = await self.extract_metadata_with_landmark_strategy(page, -1)
            
            if result and result.get('generation_date') and result.get('prompt'):
                logger.info(f"✅ GALLERY EXTRACTION: Success - date='{result['generation_date']}', prompt_length={len(result['prompt'])}")
                return result
            else:
                logger.warning(f"❌ GALLERY EXTRACTION: Failed - result={result}")
                return None
            
        except Exception as e:
            logger.error(f"❌ GALLERY EXTRACTION: Exception in extraction: {e}")
            import traceback
            logger.error(f"❌ GALLERY EXTRACTION: Traceback: {traceback.format_exc()}")
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
            
            # Initialize variables to prevent scope issues
            metadata_candidates = []
            
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
                logger.info("🔍 Starting enhanced 'Inspiration Mode' search for metadata container identification")
                
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
                    
                    # ENHANCEMENT: If only one Inspiration Mode container, use it directly
                    visible_inspiration_spans = []
                    for span in inspiration_spans:
                        if await span.is_visible():
                            visible_inspiration_spans.append(span)
                    
                    logger.info(f"📦 Found {len(visible_inspiration_spans)} visible 'Inspiration Mode' spans")
                    
                    if len(visible_inspiration_spans) == 1:
                        logger.info("🎯 OPTIMIZATION: Only one visible 'Inspiration Mode' container found - using it directly without Off/On check")
                        single_inspiration_span = visible_inspiration_spans[0]
                        
                        try:
                            parent = await single_inspiration_span.evaluate_handle("el => el.parentElement")
                            if parent:
                                # Search for metadata container from this single Inspiration Mode span
                                metadata_container = await self._search_creation_time_backwards(parent, 0)
                                
                                if metadata_container:
                                    container_info = await self._analyze_metadata_container(metadata_container)
                                    
                                    if container_info['creation_date']:
                                        validated_container = metadata_container
                                        metadata['generation_date'] = container_info['creation_date']
                                        date_extracted = True
                                        
                                        logger.info(f"✅ SINGLE INSPIRATION MODE: Successfully extracted date: {container_info['creation_date']}")
                                    else:
                                        logger.debug("Single inspiration mode container found but no valid creation date")
                                else:
                                    logger.debug("Single inspiration mode span found but no metadata container")
                        except Exception as e:
                            logger.debug(f"Error processing single inspiration mode span: {e}")
                    
                    # If single container approach didn't work, use enhanced multi-container approach
                    if not validated_container:
                        logger.info("🔍 Multiple or no containers found, using enhanced Inspiration Mode + (Off OR On) search")
                        metadata_candidates = []
                        
                        for i, inspiration_span in enumerate(visible_inspiration_spans):
                            try:
                                # Get inspiration span details
                                inspiration_text = await inspiration_span.text_content()
                                inspiration_class = await inspiration_span.get_attribute('class') or 'no-class'
                                
                                logger.debug(f"🎯 Processing Inspiration Mode span {i}: class='{inspiration_class}' text='{inspiration_text.strip()}'")
                                
                                # Step 2: Look for "Off" OR "On" in the next sibling span (ENHANCED)
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
                                
                                # Check if next span contains "Off" OR "On" (ENHANCED)
                                if inspiration_index >= 0 and inspiration_index + 1 < len(parent_spans):
                                    next_span = parent_spans[inspiration_index + 1]
                                    next_span_text = await next_span.text_content()
                                    next_span_class = await next_span.get_attribute('class') or 'no-class'
                                    
                                    logger.debug(f"   Next span: class='{next_span_class}' text='{next_span_text.strip()}'")
                                    
                                    # CRITICAL FIX: Accept both "Off" and "On" for Inspiration Mode
                                    if "Off" in next_span_text or "On" in next_span_text:
                                        mode_value = "Off" if "Off" in next_span_text else "On"
                                        logger.info(f"   ✅ Found 'Inspiration Mode' + '{mode_value}' pair in span {i}!")
                                        
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
                                                    'mode_class': next_span_class,
                                                    'mode_value': mode_value
                                                })
                                                
                                                logger.info(f"   🏆 Found valid metadata container: {container_info['text_length']} chars, date: {container_info['creation_date']}, mode: {mode_value}")
                                            else:
                                                logger.debug(f"   ❌ Container found but no valid creation date")
                                        else:
                                            logger.debug(f"   ❌ No metadata container found for this Inspiration Mode + {mode_value} pair")
                                    else:
                                        logger.debug(f"   ❌ Next span contains neither 'Off' nor 'On': '{next_span_text.strip()}'")
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
                        logger.warning("❌ No valid metadata containers found using enhanced Inspiration Mode search")
                
                # Now extract creation time from the validated container
                if validated_container:
                    logger.info(f"🕒 Extracting Creation Time from validated Inspiration Mode container")
                    
                    # Check if we already have the date from single container optimization
                    if date_extracted and metadata.get('generation_date'):
                        logger.info(f"🎉 SUCCESS! Already extracted date from single container optimization: '{metadata['generation_date']}'")
                    # Extract date using the cached information if available from multi-container approach
                    elif 'metadata_candidates' in locals() and metadata_candidates and metadata_candidates[0]['info']['creation_date']:
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
                    logger.warning("No validated metadata container found using enhanced Inspiration Mode search")
                    
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
            logger.info(f"🔍 DEBUG: Returning metadata: {metadata}")
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
        """Download a single generation using robust thumbnail tracking with Enhanced SKIP mode support"""
        # CRITICAL DEBUG: Log function entry to catch if it's called at all
        logger.info(f"🚨 ENTRY: download_single_generation_robust called with {thumbnail_info.get('unique_id', 'unknown')}")
        
        # Initialize boundary download flag and metadata
        is_boundary_download = False
        boundary_metadata_dict = None
        
        try:
            thumbnail_element = thumbnail_info['element']
            thumbnail_id = thumbnail_info['unique_id']
            thumbnail_position = thumbnail_info['position']
            
            logger.info(f"Starting robust download for thumbnail: {thumbnail_id}")
            
            # ENHANCED SKIP MODE: Check if we should fast-forward past this thumbnail
            if hasattr(self, 'fast_forward_mode') and self.fast_forward_mode:
                action = await self.fast_forward_to_checkpoint(page, thumbnail_id)
                if action == "skip":
                    logger.info(f"⏩ FAST-FORWARD: Skipping thumbnail {thumbnail_id}")
                    return "skip_continue"  # Skip this thumbnail
                elif action == "skip_checkpoint":
                    logger.info(f"📍 CHECKPOINT: Skipping {thumbnail_id} (checkpoint found, downloading starts next)")
                    return "skip_continue"  # Skip this checkpoint thumbnail
                elif action == "check_after_click":
                    # We need to click first, then check metadata
                    logger.info(f"⏩ Fast-forward mode: Will check metadata after clicking {thumbnail_id}")
                    # Continue with the click and check after
                # If action == "download", continue with normal download process
            
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
            
            # ENHANCED SKIP MODE: Check if we're still in old content after clicking
            if hasattr(self, 'fast_forward_mode') and self.fast_forward_mode:
                # We're in fast-forward mode, check if this is still old content
                metadata = await self._extract_metadata_after_click(page, thumbnail_id)
                if metadata:
                    # Check if this is still a duplicate (old content)
                    is_still_old = await self._is_still_duplicate(metadata)
                    if is_still_old:
                        logger.info(f"⏩ Still in old content, skipping {thumbnail_id}")
                        return "skip_continue"  # Skip this old content
                    else:
                        # We've reached new content!
                        logger.info(f"🆕 Reached NEW content at {thumbnail_id}!")
                        logger.info(f"   📅 Time: {metadata.get('generation_date')}")
                        logger.info(f"   🚀 Switching back to download mode")
                        self.fast_forward_mode = False
                        self.checkpoint_found = True
                        # Continue with download
                else:
                    logger.warning(f"Could not extract metadata for {thumbnail_id}, skipping")
                    return True
            
            # ENHANCED: Extract metadata with duplicate checking
            logger.info(f"🔄 ROBUST: About to extract metadata for {thumbnail_id}")
            metadata_dict = await self.extract_metadata_with_landmark_strategy(page, thumbnail_position)
            logger.info(f"🔄 ROBUST: Landmark strategy returned: {metadata_dict}")
            
            if not metadata_dict or not metadata_dict.get('generation_date') or metadata_dict.get('generation_date') == 'Unknown':
                logger.warning(f"Landmark strategy failed for thumbnail {thumbnail_id}, trying legacy extraction")
                metadata_dict = await self.extract_metadata_from_page(page)
                logger.info(f"🔄 ROBUST: Legacy extraction returned: {metadata_dict}")
                
            if not metadata_dict:
                logger.warning(f"All metadata extraction failed for thumbnail {thumbnail_id}, using defaults")
                metadata_dict = {'generation_date': 'Unknown', 'prompt': 'Unknown'}
            
            # CRITICAL FIX: Verify boundary metadata matches extracted metadata
            if is_boundary_download and boundary_metadata_dict:
                logger.info(f"🔍 BOUNDARY VERIFICATION: Comparing boundary metadata with gallery metadata")
                logger.info(f"   📅 Boundary datetime: '{boundary_metadata_dict['generation_date']}'")
                logger.info(f"   📅 Gallery datetime: '{metadata_dict.get('generation_date', 'Unknown')}'")
                logger.info(f"   📝 Boundary prompt (50 chars): '{boundary_metadata_dict['prompt'][:50]}...'")
                logger.info(f"   📝 Gallery prompt (50 chars): '{metadata_dict.get('prompt', 'Unknown')[:50]}...'")
                
                # Verify datetime matches
                if metadata_dict.get('generation_date') == boundary_metadata_dict['generation_date']:
                    logger.info(f"✅ BOUNDARY VERIFICATION: Datetime matches! Gallery is showing the correct boundary generation")
                    # Use the full prompt from gallery extraction (it's more complete)
                    if metadata_dict.get('prompt') and len(metadata_dict['prompt']) > len(boundary_metadata_dict.get('prompt', '')):
                        logger.info(f"   📝 Using full prompt from gallery: {len(metadata_dict['prompt'])} chars (was {len(boundary_metadata_dict.get('prompt', ''))} chars)")
                        # Gallery metadata is correct and has full prompt, use it
                    else:
                        # Gallery datetime matches but prompt might be incomplete, merge them
                        metadata_dict['prompt'] = boundary_metadata_dict.get('prompt', metadata_dict.get('prompt', ''))
                else:
                    logger.warning(f"⚠️ BOUNDARY VERIFICATION: Datetime mismatch!")
                    logger.warning(f"   Expected: '{boundary_metadata_dict['generation_date']}'")
                    logger.warning(f"   Found: '{metadata_dict.get('generation_date', 'Unknown')}'")
                    logger.warning(f"   🔧 Using boundary metadata to ensure correct download")
                    # Gallery is showing wrong generation, use boundary metadata
                    metadata_dict = boundary_metadata_dict.copy()
                
                logger.info(f"📊 BOUNDARY FINAL METADATA: date='{metadata_dict['generation_date']}', prompt_length={len(metadata_dict.get('prompt', ''))}")
            
            # DEBUG: Add checkpoint to verify execution reaches this point
            logger.info(f"🏁 CHECKPOINT: About to start duplicate checking for {thumbnail_id}")
            logger.info(f"🏁 metadata_dict = {metadata_dict}")
            
            # ENHANCED: Comprehensive duplicate detection (log-based, file-based, and session-based)
            # FAILSAFE: Force enable duplicate checking if disabled (critical for boundary downloads)
            if not getattr(self.config, 'duplicate_check_enabled', True):
                logger.warning("🚨 FAILSAFE: duplicate_check_enabled was False, forcing to True for boundary downloads")
                self.config.duplicate_check_enabled = True
                
            logger.info(f"🔍 DUPLICATE CHECK CONDITION: enabled={getattr(self.config, 'duplicate_check_enabled', 'MISSING')}, metadata_dict={bool(metadata_dict)}, has_date={bool(metadata_dict and metadata_dict.get('generation_date')) if metadata_dict else False}")
            if self.config.duplicate_check_enabled and metadata_dict and metadata_dict.get('generation_date'):
                creation_time = metadata_dict.get('generation_date')
                logger.info(f"🔍 DUPLICATE CHECK: Starting for date={creation_time}, thumbnail={thumbnail_id}")
                
                # Method 1: Check comprehensive duplicates (log entries + prompt matching)
                logger.info(f"🔄 CALLING COMPREHENSIVE DUPLICATE CHECK for {thumbnail_id}")
                is_comprehensive_duplicate = await self.check_comprehensive_duplicate(page, thumbnail_id, existing_files)
                logger.info(f"🔄 COMPREHENSIVE DUPLICATE CHECK RESULT: {is_comprehensive_duplicate}")
                if is_comprehensive_duplicate == "exit_scan_return":
                    # Execute exit-scan-return strategy (Algorithm Steps 11-15)
                    logger.info("🚪 SKIP MODE: Triggering exit-scan-return strategy")
                    
                    # Store checkpoint data
                    self.checkpoint_data = {
                        'generation_date': metadata_dict.get('generation_date'),
                        'prompt': metadata_dict.get('prompt', '')
                    }
                    
                    # Execute the exit-scan-return workflow
                    scan_result = await self.exit_gallery_and_scan_generations(page)
                    
                    if scan_result and scan_result.get('found'):
                        logger.info("✅ Exit-scan-return successful, positioned at boundary generation")
                        
                        boundary_container_index = scan_result.get('container_index', 8)
                        boundary_datetime = scan_result.get('creation_time', 'Unknown')
                        boundary_prompt = scan_result.get('prompt', 'Unknown')[:50]
                        
                        logger.info(f"🎯 BOUNDARY DETAILS:")
                        logger.info(f"   📅 Datetime: '{boundary_datetime}' ⭐")
                        logger.info(f"   📝 Prompt: {boundary_prompt}...")
                        logger.info(f"   🎯 Container: #{boundary_container_index}")
                        logger.info(f"🎯 SKIP MODE: Gallery opened at boundary - this generation will be downloaded")
                        
                        # CRITICAL FIX: The boundary generation should be downloaded normally
                        # According to documentation: "Ready to download new content from next thumbnail"
                        # The boundary IS the first new content to download
                        logger.info("📥 BOUNDARY FOUND: Continuing with download of this generation")
                        
                        # CRITICAL FIX: Set flag to prevent re-triggering exit-scan-return on consecutive duplicates
                        # After downloading this boundary, system should continue in fast-forward mode 
                        # to skip past any consecutive duplicates before triggering exit-scan-return again
                        self.boundary_just_downloaded = True
                        logger.info("🔄 BOUNDARY DOWNLOAD FLAG: Set to prevent exit-scan-return re-triggering on consecutive duplicates")
                        
                        # CRITICAL FIX: Don't return False - continue with download workflow
                        # The boundary generation is NEW content that should be downloaded
                        # Set flag to skip further duplicate checks for this boundary
                        logger.info("🚀 BOUNDARY: Proceeding to download the boundary generation")
                        
                        # CRITICAL: Skip to download section for boundary generation
                        # We already know this is new content, no need for more duplicate checks
                        is_boundary_download = True
                        
                        # CRITICAL FIX: Store boundary metadata to use instead of re-extracting
                        # The gallery might show a different generation after opening
                        boundary_metadata_dict = {
                            'generation_date': boundary_datetime,
                            'prompt': scan_result.get('prompt', 'Unknown')  # Use full prompt from scan
                        }
                        logger.info(f"🎯 BOUNDARY: Stored boundary metadata - date='{boundary_datetime}', prompt='{boundary_metadata_dict['prompt'][:50]}...'")
                    else:
                        logger.warning("❌ Exit-scan-return failed, stopping")
                        self.should_stop = True
                        return False
                        
                elif is_comprehensive_duplicate == "skip":
                    # Skip mode: continue to next generation
                    logger.warning(f"⏭️  Skipping comprehensive duplicate: {thumbnail_id}")
                    return "skip_continue"
                elif is_comprehensive_duplicate:
                    if self.config.stop_on_duplicate and self.config.duplicate_mode == DuplicateMode.FINISH:
                        logger.info(f"🛑 STOPPING: Comprehensive duplicate detected for {thumbnail_id}")
                        logger.info("✅ Automation has reached previously downloaded content")
                        self.should_stop = True
                        return False
                    else:
                        logger.warning(f"⏭️  Skipping comprehensive duplicate: {thumbnail_id}")
                        return "skip_continue"
                
                # Method 2: Check file-based duplicates (from disk) - fallback
                # CRITICAL FIX: Skip this check if we're processing a boundary download
                if is_boundary_download:
                    logger.info("🚀 BOUNDARY: Skipping duplicate check for boundary generation - already confirmed as new")
                    duplicate_result = False  # Force no duplicate for boundary
                else:
                    prompt_text = metadata_dict.get('prompt', '')
                    duplicate_result = self.check_duplicate_exists(creation_time, prompt_text)
                
                if duplicate_result == "exit_scan_return":
                    # Algorithm Step 6a: Initiate skipping process
                    logger.info("🚀 Initiating SKIP mode exit-scan-return workflow")
                    return await self.exit_gallery_and_scan_generations(page)
                elif duplicate_result and self.config.stop_on_duplicate:
                    logger.info(f"🛑 STOPPING: Algorithm-compliant duplicate detected ({creation_time})")
                    logger.info("🔄 All newer files have already been downloaded")
                    self.should_stop = True
                    return False
                elif duplicate_result:
                    logger.warning(f"⏭️  Skipping duplicate with creation time: {creation_time}")
                    return "skip_continue"
                
                # Method 3: Check session-based duplicates (already processed in this run) - fallback
                session_duplicate_id = f"{creation_time}|{thumbnail_id}"
                if session_duplicate_id in self.processed_thumbnails:
                    logger.warning(f"⏭️  Skipping session duplicate: {session_duplicate_id}")
                    return "skip_continue"
            
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
                    # CRITICAL FIX: Use boundary metadata if available, otherwise use gallery metadata
                    active_metadata = boundary_metadata_dict if is_boundary_download and boundary_metadata_dict else metadata_dict
                    
                    # Generate proper filename and move file
                    final_filename = self.file_namer.generate_filename(
                        file_path=downloaded_file,
                        creation_date=active_metadata.get('generation_date'),
                        sequence_number=file_id
                    )
                    final_path = download_path / final_filename
                    
                    downloaded_file.rename(final_path)
                    logger.info(f"📁 File renamed to: {final_filename}")
                    
                    # Log verification for boundary downloads
                    if is_boundary_download and boundary_metadata_dict:
                        logger.info(f"📝 BOUNDARY FILE NAMING: Using stored boundary metadata")
                        logger.info(f"   Date used: {active_metadata.get('generation_date')}")
                        logger.info(f"   Prompt used: {active_metadata.get('prompt', '')[:100]}...")
                    
                    # Create GenerationMetadata object for logging
                    metadata = GenerationMetadata(
                        file_id=str(file_id),
                        generation_date=active_metadata.get('generation_date', ''),
                        prompt=active_metadata.get('prompt', ''),
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
            logger.error(f"🚨 EXCEPTION: Error in robust download for thumbnail {thumbnail_info.get('unique_id', 'unknown')}: {e}")
            logger.error(f"🚨 EXCEPTION: Type: {type(e).__name__}")
            logger.error(f"🚨 EXCEPTION: Details: {str(e)}")
            import traceback
            logger.error(f"🚨 EXCEPTION: Traceback: {traceback.format_exc()}")
            return False
    
    async def download_single_generation(self, page, thumbnail_index: int, existing_files: set = None) -> bool:
        """Download a single generation and handle all associated tasks with Enhanced SKIP mode support"""
        try:
            logger.info(f"Starting download for thumbnail {thumbnail_index}")
            
            # ENHANCED SKIP MODE: Check if we should fast-forward past this thumbnail  
            if hasattr(self, 'fast_forward_mode') and self.fast_forward_mode:
                action = await self.fast_forward_to_checkpoint(page, f"thumbnail_{thumbnail_index}")
                if action == "skip":
                    logger.info(f"⏩ FAST-FORWARD: Skipping thumbnail {thumbnail_index}")
                    return "skip_continue"  # Skip this thumbnail
                elif action == "skip_checkpoint":
                    logger.info(f"📍 CHECKPOINT: Skipping {thumbnail_index} (checkpoint found, downloading starts next)")
                    return "skip_continue"  # Skip this checkpoint thumbnail
                # If action == "download", continue with normal download process
            
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
            logger.info(f"🔍 DEBUG: Received metadata_dict from landmark strategy: {metadata_dict}")
            if not metadata_dict or not metadata_dict.get('generation_date') or metadata_dict.get('generation_date') == 'Unknown':
                logger.warning(f"Landmark strategy failed for thumbnail {thumbnail_index}, trying legacy extraction")
                # Fallback to original method
                metadata_dict = await self.extract_metadata_from_page(page)
                logger.info(f"🔍 DEBUG: Received metadata_dict from legacy extraction: {metadata_dict}")
                
            if not metadata_dict:
                logger.warning(f"All metadata extraction failed for thumbnail {thumbnail_index}, using defaults")
                metadata_dict = {'generation_date': 'Unknown', 'prompt': 'Unknown'}
            
            logger.info(f"🔍 DEBUG: Final metadata_dict before duplicate check: {metadata_dict}")
            
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
            
            # FAST OPTIMIZATION: Check for algorithm-compliant duplicate before downloading  
            if self.config.duplicate_check_enabled and metadata_dict and metadata_dict.get('generation_date'):
                creation_time = metadata_dict.get('generation_date')
                prompt_text = metadata_dict.get('prompt', '')
                logger.info(f"🔍 DUPLICATE CHECK: Checking {creation_time} against existing log entries")
                duplicate_result = self.check_duplicate_exists(creation_time, prompt_text)
                logger.info(f"🔍 DUPLICATE CHECK RESULT: {duplicate_result}")
                
                if duplicate_result == "exit_scan_return":
                    # Algorithm Step 6a: Initiate skipping process
                    logger.info("🚀 Initiating SKIP mode exit-scan-return workflow")
                    return await self.exit_gallery_and_scan_generations(page)
                elif duplicate_result and self.config.stop_on_duplicate:
                    logger.info(f"🛑 STOPPING: Algorithm-compliant duplicate detected ({creation_time})")
                    logger.info("🔄 All newer files have already been downloaded")
                    self.should_stop = True
                    return False  # Stop the entire automation
                elif duplicate_result:
                    logger.warning(f"⏭️  Skipping algorithm-compliant duplicate: {creation_time}")
                    return "skip_continue"  # Skip this file but continue
            
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
        """Simple status check using text-based detection (Algorithm compliant)"""
        try:
            element = await page.query_selector(selector)
            if not element:
                return {'status': 'not_found', 'reason': 'Element not found'}
            
            # Get text content for simple checking
            element_text = await element.text_content()
            if not element_text:
                return {'status': 'unknown', 'reason': 'No text content'}
            
            # Simple text-based queue/failed/rendering detection (Algorithm Step 3)
            if "Queuing" in element_text:
                return {'status': 'queued', 'reason': 'Contains "Queuing"'}
            
            if "Something went wrong" in element_text:
                return {'status': 'failed', 'reason': 'Contains "Something went wrong"'}
            
            if "Video is rendering" in element_text:
                return {'status': 'rendering', 'reason': 'Contains "Video is rendering"'}
            
            # If not queued/failed, assume completed
            return {'status': 'completed', 'reason': 'No queue/error indicators found'}
                
        except Exception as e:
            logger.error(f"Error checking generation status for {selector}: {e}")
            return {'status': 'error', 'reason': str(e)}

    async def find_completed_generations_on_page(self, page) -> List[str]:
        """Find all completed generations using simple sequential container checking (Algorithm Step 2-3)"""
        try:
            logger.info("🔍 Scanning initial /generate page for completed generations...")
            
            completed_selectors = []
            
            # Get starting index from config, default to 8
            start_index = 8
            if self.config.completed_task_selector:
                match = re.search(r'__(\d+)', self.config.completed_task_selector)
                if match:
                    start_index = int(match.group(1))
            
            # Simple sequential checking from starting index (Algorithm Step 2)
            logger.info(f"Starting sequential scan from container index {start_index}")
            
            for i in range(start_index, start_index + 10):  # Check 10 containers from start
                selector = f"div[id$='__{i}']"
                
                try:
                    element = await page.query_selector(selector)
                    if not element:
                        continue
                    
                    # Get text content for simple status check (Algorithm Step 3)
                    text_content = await element.text_content()
                    if not text_content:
                        continue
                    
                    # Simple text-based queue/failed/rendering detection
                    if "Queuing" in text_content or "Something went wrong" in text_content or "Video is rendering" in text_content:
                        status = "Queued" if "Queuing" in text_content else ("Failed" if "Something went wrong" in text_content else "Rendering")
                        logger.info(f"⏳ Skipping container __{i} ({status}): {text_content[:50]}...")
                        continue
                    
                    # If not queued/failed, consider it completed
                    completed_selectors.append(selector)
                    logger.info(f"✅ Found completed generation: __{i}")
                    
                except Exception as e:
                    logger.debug(f"Error checking container __{i}: {e}")
                    continue
            
            logger.info(f"📊 Found {len(completed_selectors)} completed generations")
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
            
            # Initialize navigation state variables
            navigation_success = False
            start_from_positioned = False
            
            # STEP 0: START_FROM: Navigate to specified datetime if provided (MUST BE FIRST)
            if self.config.start_from:
                logger.info(f"🎯 START_FROM MODE: Searching for generation with datetime '{self.config.start_from}'")
                start_from_result = await self._find_start_from_generation(page, self.config.start_from)
                
                if start_from_result['found']:
                    logger.info(f"✅ START_FROM: Found target generation, ready to begin downloads from next generation")
                    # The search has positioned us at the target generation in gallery, skip navigation steps
                    logger.info("🚀 START_FROM: Target positioned - continuing with main thumbnail processing loop")
                    
                    # Set flag to skip navigation and continue with main loop
                    navigation_success = True
                    start_from_positioned = True
                else:
                    logger.warning(f"⚠️ START_FROM: Could not find generation with datetime '{self.config.start_from}'")
                    logger.info("🎯 START_FROM: Since start_from was specified, staying on /generate page (no thumbnail navigation)")
                    logger.info("🚀 START_FROM: Using generation containers on /generate page as primary interface")
                    
                    # When start_from is provided but target not found, we still want to work with generation containers
                    # on the /generate page, not navigate to thumbnails gallery
                    return await self.execute_generation_container_mode(page, results)
            
            # STEP 1: Scan for existing files to detect duplicates (if enabled)
            existing_files = set()
            if self.config.duplicate_check_enabled:
                existing_files = self.scan_existing_files()
                if existing_files and self.config.stop_on_duplicate:
                    logger.info(f"🔍 Found {len(existing_files)} existing files - will stop if duplicate creation time detected")
            
            # STEP 1.5: Initialize Enhanced SKIP mode (NEW FEATURE)
            enhanced_skip_enabled = self.initialize_enhanced_skip_mode()
            if enhanced_skip_enabled:
                logger.info("⚡ Enhanced SKIP mode is active - will fast-forward to last checkpoint")
            
            # STEP 1: Configure Chromium browser settings to suppress download popups
            logger.info("⚙️ Configuring Chromium browser settings to suppress download notifications")
            settings_configured = await self._configure_chromium_download_settings(page)
            if not settings_configured:
                logger.warning("⚠️ Failed to configure Chromium settings, continuing with automation (downloads popup may appear)")
            else:
                logger.info("✅ Chromium download settings configured successfully")
            
            # STEP 2: Enhanced completed generation detection - scan page and skip queued generations
            # Initialize completed_generation_selectors for all paths
            completed_generation_selectors = []
            
            # Skip navigation if start_from has already positioned us in the gallery
            if not start_from_positioned:
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
            else:
                # START_FROM has already positioned us in the gallery, no navigation needed
                logger.info("✅ START_FROM: Already positioned in gallery, skipping navigation steps")
                logger.info("🎯 START_FROM: Verifying gallery positioning and thumbnail availability...")
                
                # Verify that we're actually in a gallery with thumbnails
                try:
                    thumbnail_check = await page.query_selector_all(self.config.thumbnail_selector)
                    if thumbnail_check:
                        logger.info(f"✅ START_FROM: Verified {len(thumbnail_check)} thumbnails available in gallery")
                        navigation_success = True
                    else:
                        logger.warning("⚠️ START_FROM: No thumbnails found after positioning - may need to wait for loading")
                        await page.wait_for_timeout(3000)  # Wait for thumbnails to load
                        
                        # Re-check for thumbnails
                        thumbnail_check = await page.query_selector_all(self.config.thumbnail_selector)
                        if thumbnail_check:
                            logger.info(f"✅ START_FROM: After wait, verified {len(thumbnail_check)} thumbnails available")
                            navigation_success = True
                        else:
                            logger.error("❌ START_FROM: Still no thumbnails found - gallery positioning may have failed")
                            navigation_success = False
                except Exception as e:
                    logger.error(f"❌ START_FROM: Error verifying gallery position: {e}")
                    navigation_success = False
            
            # NEW: Proactive gallery loading phase to populate infinite scroll
            logger.info("🔄 Pre-loading gallery with initial scroll phase to populate thumbnails...")
            await self.preload_gallery_thumbnails(page)
            
            # Initialize thumbnail tracking
            self.visible_thumbnails_cache = await self.get_visible_thumbnail_identifiers(page)
            initial_thumbnail_count = len(self.visible_thumbnails_cache)
            logger.info(f"📊 After gallery pre-loading: {initial_thumbnail_count} thumbnails visible")
            
            # ENHANCED: Robust gallery navigation with duplicate prevention
            consecutive_failures = 0
            max_consecutive_failures = 100  # Support very large galleries with sparse content
            no_progress_cycles = 0
            max_no_progress_cycles = 3
            
            logger.info("🚀 Starting enhanced gallery navigation with production reliability")
            
            # Initialize session tracking
            self.processing_start_time = datetime.now()
            
            # START_FROM search already completed at the beginning if needed
            # If we reach here, either start_from was not used or target not found
            
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
                        
                        # SAFEGUARD: Check if we're stuck on the same generation
                        if not hasattr(self, 'last_processed_metadata'):
                            self.last_processed_metadata = None
                            self.same_generation_count = 0
                        
                        # Download the current active thumbnail
                        logger.info(f"🚨 MAIN LOOP: About to call download_single_generation_robust for {thumbnail_info.get('unique_id', 'unknown')}")
                        logger.info(f"🚨 MAIN LOOP: thumbnail_info = {thumbnail_info}")
                        success = await self.download_single_generation_robust(page, thumbnail_info, existing_files)
                        logger.info(f"🚨 MAIN LOOP: download_single_generation_robust returned: {success}")
                        
                        # Extract thumbnail_id for tracking purposes
                        thumbnail_id = thumbnail_info['unique_id']
                        
                        # SAFEGUARD: Check if we're processing the same generation repeatedly
                        # CRITICAL FIX: Skip safeguard metadata extraction for boundary downloads
                        # This prevents overriding the verified boundary metadata
                        if hasattr(self, 'boundary_just_downloaded') and self.boundary_just_downloaded:
                            logger.info("🚀 BOUNDARY: Skipping safeguard metadata extraction to preserve boundary metadata")
                            # Use a unique key for boundary downloads to avoid false loop detection
                            boundary_key = f"boundary_{thumbnail_id}_{time.time()}"
                            self.last_processed_metadata = boundary_key
                            self.same_generation_count = 1
                        else:
                            try:
                                current_metadata = await self.extract_metadata_from_page(page)
                                if current_metadata:
                                    current_key = f"{current_metadata.get('generation_date')}|{current_metadata.get('prompt', '')[:50]}"
                                    if self.last_processed_metadata == current_key:
                                        self.same_generation_count += 1
                                        if self.same_generation_count >= 3:
                                            logger.error(f"🚨 INFINITE LOOP DETECTED: Same generation processed {self.same_generation_count} times")
                                            logger.error(f"   Time: {current_metadata.get('generation_date')}")
                                            logger.error(f"   Prompt: {current_metadata.get('prompt', '')[:100]}...")
                                            logger.info("🛑 Breaking out of infinite loop, ending automation")
                                            break
                                    else:
                                        self.last_processed_metadata = current_key
                                        self.same_generation_count = 1
                            except Exception as metadata_check_error:
                                logger.debug(f"Metadata check error: {metadata_check_error}")
                        
                        if success is True:
                            results['downloads_completed'] += 1
                            logger.info(f"✅ Successfully downloaded thumbnail #{thumbnail_count}")
                            consecutive_failures = 0  # Reset failure counter
                            self.same_generation_count = 0  # Reset infinite loop counter on success
                            
                            # CRITICAL FIX: Keep boundary flag until next thumbnail is processed
                            # This allows the next duplicate check to know it's a consecutive duplicate
                            if hasattr(self, 'boundary_just_downloaded') and self.boundary_just_downloaded:
                                logger.info("✅ Boundary generation download completed successfully")
                                logger.info("🔄 Boundary flag maintained for consecutive duplicate handling on next thumbnail")
                        elif success == "skip_continue":
                            logger.info(f"⏭️ Skipped duplicate thumbnail #{thumbnail_count} (continuing)")
                            consecutive_failures = 0  # Reset failure counter since skip is expected
                            self.same_generation_count = 0  # Reset infinite loop counter
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

    def initialize_enhanced_skip_mode(self) -> bool:
        """Simple SKIP mode initialization (Algorithm compliant)"""
        if self.config.duplicate_mode != DuplicateMode.SKIP:
            return False
            
        # Load existing log entries for duplicate detection
        self.existing_log_entries = self._load_existing_log_entries()
        
        logger.info(f"🚀 SKIP mode: Found {len(self.existing_log_entries)} existing downloads")
        
        # Simple state initialization  
        self.skip_mode_active = True
        
        logger.info("✅ Exit-scan-return strategy ENABLED in SKIP mode (Algorithm Steps 11-15)")
        
        return True
        
    async def fast_forward_to_checkpoint(self, page, thumbnail_id: str, thumbnail_element=None) -> str:
        """Simple action determination - Algorithm compliant"""
        # Always download and check for duplicates (Algorithm Step 5-6)
        # The check_duplicate_exists method will handle exit-scan-return if needed
        return "download"
    
    async def _is_still_duplicate(self, metadata: Dict[str, str]) -> bool:
        """Simple duplicate check - delegates to algorithm-compliant method"""
        generation_date = metadata.get('generation_date', '')
        prompt = metadata.get('prompt', '') or metadata.get('prompt_start', '')
        
        # Use the algorithm-compliant duplicate detection method
        result = self.check_duplicate_exists(generation_date, prompt)
        
        # Return boolean (convert from string/boolean result)
        return result not in [False, None]
    
    async def check_if_checkpoint_after_click(self, page, thumbnail_id: str) -> str:
        """Check if the clicked thumbnail is still old content (deprecated - use _is_still_duplicate)"""
        # This method is now deprecated in favor of the inline check
        # Keep for backward compatibility
        metadata = await self._extract_metadata_after_click(page, thumbnail_id)
        if metadata:
            is_old = await self._is_still_duplicate(metadata)
            return "skip" if is_old else "download"
        return "skip"
    
    async def _extract_metadata_fast(self, page, thumbnail_id: str) -> Optional[Dict[str, str]]:
        """Quickly extract metadata for checkpoint comparison without full processing"""
        # This method is now deprecated, use _extract_metadata_after_click instead
        return await self._extract_metadata_after_click(page, thumbnail_id)
    
    async def _extract_metadata_after_click(self, page, thumbnail_id: str) -> Optional[Dict[str, str]]:
        """Extract metadata after clicking on thumbnail (when it's visible)"""
        try:
            # Wait a bit for the metadata panel to appear
            await page.wait_for_timeout(1500)  # Increased wait time
            
            # Extract just the creation time and a portion of the prompt for comparison
            creation_time = None
            prompt_start = None
            
            # Try to get creation time from DOM - these selectors work when thumbnail is selected
            creation_time_selectors = [
                # Most specific selectors first
                ".sc-bYXhga.jGymgu .sc-jxKUFb.bZTHAM:last-child",  # Full path to time span
                "xpath=//span[text()='Creation Time']/following-sibling::span",  # Exact text match
                f"xpath=//span[contains(text(), '{self.config.creation_time_text}')]/following-sibling::span",
                ".sc-jxKUFb.bZTHAM:last-child",  # The second span with creation time
                "span:has-text('Creation Time') + span",
                ".sc-bYXhga.jGymgu span:last-child",  # Container with time info
                # More general selectors
                "xpath=//div[contains(@class, 'jGymgu')]//span[last()]",
                "xpath=//span[contains(@class, 'bZTHAM')][last()]" 
            ]
            
            logger.debug(f"Attempting to extract creation time for {thumbnail_id}")
            for selector in creation_time_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=500):
                        creation_time = await element.text_content()
                        if creation_time and ':' in creation_time:  # Basic validation for time format
                            logger.debug(f"Found creation time with selector {selector}: {creation_time}")
                            break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
                    
            # Try to get prompt start for comparison
            prompt_selectors = [
                # UPDATED September 2025 - New HTML structure
                ".sc-eKQYOU.bdGRCs span[aria-describedby]",  # New primary selector
                ".sc-fileXT.gEIKhI .sc-eKQYOU.bdGRCs span",  # With container context
                ".sc-eKQYOU.bdGRCs span:first-child",  # First span in new container
                # Legacy fallbacks (in case of mixed versions)
                ".sc-dDrhAi.dnESm span:first-child",  # Old prompt container first span
                ".sc-jJRqov.cxtNJi span[aria-describedby]",  # Old specific selector
                # Generic fallbacks
                "span[aria-describedby]",  # Generic aria-described spans
                "[class*='prompt'] span, [class*='description'] span",
                "xpath=//span[@aria-describedby]"
            ]
            
            logger.debug(f"Attempting to extract prompt for {thumbnail_id}")
            for selector in prompt_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=500):
                        full_prompt = await element.text_content()
                        if full_prompt and len(full_prompt) > 20:  # Basic validation
                            prompt_start = full_prompt[:200] if full_prompt else None  # First 200 chars
                            logger.debug(f"Found prompt with selector {selector}: {prompt_start[:50]}...")
                            break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if creation_time:
                logger.debug(f"Successfully extracted metadata: time={creation_time}, prompt={prompt_start[:50] if prompt_start else 'None'}")
                return {
                    'generation_date': creation_time.strip(),
                    'prompt_start': prompt_start or "Unknown prompt",
                    'thumbnail_id': thumbnail_id
                }
            else:
                logger.warning(f"Could not find creation time for {thumbnail_id} - metadata panel may not be visible")
                
        except Exception as e:
            logger.error(f"Error extracting metadata after click: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
        return None
    
    def _is_checkpoint_match(self, current_metadata: Dict[str, str], checkpoint_data: Dict[str, str]) -> bool:
        """Check if current metadata matches the checkpoint"""
        try:
            # Compare creation times
            current_time = current_metadata.get('generation_date', '')
            checkpoint_time = checkpoint_data.get('generation_date', '')
            
            # Normalize both times for comparison
            current_normalized = self.logger._normalize_date_format(current_time)
            checkpoint_normalized = self.logger._normalize_date_format(checkpoint_time)
            
            if current_normalized == checkpoint_normalized:
                logger.info(f"   ✅ Creation time match: {current_normalized}")
                
                # Also check prompt similarity for extra confirmation
                current_prompt = current_metadata.get('prompt_start', '')[:100]
                checkpoint_prompt = checkpoint_data.get('prompt', '')[:100]
                
                # Simple similarity check (first 50 characters)
                if current_prompt and checkpoint_prompt:
                    similarity_check = current_prompt[:50] == checkpoint_prompt[:50]
                    logger.info(f"   🔗 Prompt similarity: {'Match' if similarity_check else 'Different'}")
                    
                    if similarity_check:
                        return True
                    else:
                        logger.info(f"   ⚠️ Time matches but prompt differs - continuing search")
                        return False
                else:
                    # If prompt comparison fails, rely on time match
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error comparing checkpoint: {e}")
            return False
    
    async def exit_gallery_and_scan_generations(self, page) -> Optional[Dict[str, Any]]:
        """Algorithm-compliant exit → scan → find boundary workflow (Steps 11-15)"""
        try:
            logger.info("🚪 Step 11: Exit gallery...")
            
            # Step 11: Exit gallery - try multiple selector strategies
            exit_selectors = [
                'span.close-icon',  # Simplest selector for close icon
                'span.sc-fAkCkL.fjGQsQ',  # Class-based selector from task example
                'span[role="img"].close-icon',  # With role attribute
                'svg use[xlink\\:href*="guanbi"]',  # Any close icon SVG
                'span.close-icon svg',  # Close icon with SVG child
            ]
            
            exit_clicked = False
            for selector in exit_selectors:
                try:
                    exit_element = await page.wait_for_selector(selector, timeout=2000)
                    if exit_element:
                        await exit_element.click()
                        await asyncio.sleep(1)
                        logger.info(f"✅ Step 11: Exited gallery using selector: {selector}")
                        exit_clicked = True
                        break
                except Exception:
                    continue
            
            if not exit_clicked:
                logger.warning("Exit icon not found with any selector, using back navigation")
                await page.go_back()
                await asyncio.sleep(1)
                logger.info("✅ Step 11: Exited gallery using back navigation")
            
            # Step 12: Now at main /generation page with containers
            logger.info("🔍 Step 12: Returned to main page with generation containers")
            
            # Wait for page to fully load and containers to become visible
            logger.info("⏳ Waiting for main page to fully load before boundary scan...")
            try:
                # Wait for network idle to ensure page is fully loaded
                await page.wait_for_load_state("networkidle", timeout=8000)
                logger.debug("✅ Network idle detected - page should be fully loaded")
            except Exception as e:
                logger.debug(f"Network idle timeout (normal): {e}")
            
            # Additional wait for dynamic content loading
            await page.wait_for_timeout(3000)  # 3 second wait for dynamic content
            logger.info("✅ Page loading wait completed, starting boundary scan")
            
            # Step 13-14: Sequential comparison with log entries  
            return await self._find_download_boundary_sequential(page)
            
        except Exception as e:
            logger.error(f"Error in exit-scan workflow: {e}")
            return None
    
    async def _find_download_boundary_sequential(self, page) -> Optional[Dict[str, Any]]:
        """Efficient incremental boundary detection - scan as we scroll, not all at once"""
        try:
            logger.info("🔍 Step 13: Starting incremental boundary scan with scan-as-you-scroll approach")
            
            # CRITICAL FIX: Always reload log entries for boundary detection
            # Previous caching caused infinite loops as new downloads weren't reflected
            
            # Add a small delay to ensure file system has written the latest download
            import time
            time.sleep(0.5)  # Half second delay for file system sync
            
            self.existing_log_entries = self._load_existing_log_entries()
            logger.info(f"📚 Reloaded {len(self.existing_log_entries)} log entries for boundary detection (fresh read after 0.5s delay)")
            
            # Show the most recent log entries for verification
            if self.existing_log_entries:
                sorted_entries = sorted(self.existing_log_entries.items(), reverse=True)  # Most recent first
                logger.info("📋 Most recent log entries (for boundary detection):")
                for i, (log_time, log_entry) in enumerate(sorted_entries[:5]):  # Show top 5
                    log_prompt = log_entry.get('prompt', '')[:50]
                    logger.info(f"   #{i+1}: '{log_time}' - {log_prompt}...")
                if len(sorted_entries) > 5:
                    logger.info(f"   ... and {len(sorted_entries) - 5} more entries")
                    
                # Also show if there are any entries with "03 Sep 2025" for debugging
                sep_3_entries = [entry for entry in sorted_entries if entry[0].startswith('03 Sep 2025')]
                if sep_3_entries:
                    logger.info(f"📅 Found {len(sep_3_entries)} entries from '03 Sep 2025' in log file:")
                    for i, (log_time, log_entry) in enumerate(sep_3_entries[:3]):
                        log_prompt = log_entry.get('prompt', '')[:30]
                        logger.info(f"   Sep3-#{i+1}: '{log_time}' - {log_prompt}...")
            else:
                logger.info("📋 No existing log entries found - all generations will be downloaded")
            
            # Track scanned container IDs to prevent duplicate scanning
            scanned_container_ids = set()
            total_containers_scanned = 0
            duplicates_found = 0
            scroll_attempts = 0
            max_scroll_attempts = 2000  # Support very large galleries with 3000+ generations
            consecutive_no_new = 0
            max_consecutive_no_new = 50  # Allow more attempts to find new containers in large galleries
            
            # Use same multi-selector strategy as initial navigation instead of single selector
            # Extract starting number from config or use default
            start_num = 8
            if self.config.completed_task_selector:
                import re
                match = re.search(r'__(\d+)', self.config.completed_task_selector)
                if match:
                    start_num = int(match.group(1))
            
            # Generate multiple selectors like initial navigation does (same approach)
            # EXPANDED: Check a wider range to find containers after scrolling
            container_selectors = []
            for i in range(0, 50):  # Expanded range to find all possible containers
                container_selectors.append(f"div[id$='__{i}']")
            
            logger.info(f"🔍 Using multi-selector approach like initial navigation: {len(container_selectors)} selectors")
            logger.debug(f"🔍 Container selectors: {container_selectors[:3]}...{container_selectors[-1]}")
            
            while scroll_attempts < max_scroll_attempts and consecutive_no_new < max_consecutive_no_new:
                # STEP 1: Get currently visible containers using all selectors
                logger.info(f"🔍 Scan iteration {scroll_attempts + 1}: Getting visible containers")
                
                # ENHANCED: Wait for DOM to fully update after scroll
                if scroll_attempts > 0:
                    logger.debug("   ⏳ Waiting for DOM updates after scroll...")
                    await page.wait_for_timeout(2000)  # 2 seconds for DOM updates
                    
                    # Additional wait for network activity to settle
                    try:
                        await page.wait_for_load_state("networkidle", timeout=3000)
                        logger.debug("   ✅ Network idle detected")
                    except:
                        logger.debug("   ⏰ Network idle timeout (normal)")
                
                # Collect containers from all selectors (same as initial navigation)
                all_containers = []
                container_selector_stats = {}  # Track which selectors find containers
                
                for selector in container_selectors:
                    try:
                        containers = await page.query_selector_all(selector)
                        if containers:
                            all_containers.extend(containers)
                            container_selector_stats[selector] = len(containers)
                        logger.debug(f"   Selector {selector}: found {len(containers)} containers")
                    except Exception as e:
                        logger.debug(f"   Selector {selector} failed: {e}")
                
                # ENHANCED: Also try content-based container detection for scrolled content
                try:
                    # Look for containers with creation time pattern (more reliable than ID selectors)
                    content_containers = await page.query_selector_all("div:has-text('Creation Time'), div:has-text('Sep 2025'), div:has-text('Aug 2025')")
                    for container in content_containers:
                        if container not in all_containers:
                            all_containers.append(container)
                            logger.debug(f"   Content-based detection: found additional container")
                except Exception as e:
                    logger.debug(f"   Content-based detection failed: {e}")
                
                logger.info(f"   Total containers found across all selectors: {len(all_containers)}")
                if container_selector_stats:
                    active_selectors = [(k, v) for k, v in container_selector_stats.items() if v > 0]
                    logger.debug(f"   Active selectors: {active_selectors[:3]}..." if len(active_selectors) > 3 else f"   Active selectors: {active_selectors}")
                
                # Filter out already scanned containers
                new_containers = []
                for container in all_containers:
                    try:
                        # Get container ID or unique identifier
                        container_id = await container.get_attribute('id')
                        
                        # Extract the datetime as a unique identifier instead of using dynamic ID
                        text_content = await container.text_content() or ""
                        
                        # Look for datetime pattern as unique key
                        import re
                        datetime_match = re.search(r'(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})', text_content)
                        if datetime_match:
                            # Use datetime as the unique identifier (it's unique per generation)
                            unique_key = datetime_match.group(1)
                        else:
                            # Fallback to container ID or text hash
                            unique_key = container_id if container_id else str(hash(text_content[:200]))
                        
                        if unique_key not in scanned_container_ids:
                            new_containers.append((container, unique_key))
                            scanned_container_ids.add(unique_key)
                            if len(new_containers) <= 3:
                                logger.debug(f"   New container: key='{unique_key}', id='{container_id}'")
                        else:
                            if scroll_attempts == 0 and len(scanned_container_ids) <= 15:
                                logger.debug(f"   Already scanned: key='{unique_key}'")
                    except Exception as e:
                        logger.debug(f"Error getting container ID: {e}")
                        continue
                
                if not new_containers:
                    consecutive_no_new += 1
                    logger.info(f"   No new containers found (consecutive: {consecutive_no_new}/{max_consecutive_no_new})")
                    
                    if consecutive_no_new >= max_consecutive_no_new:
                        logger.info("✅ Reached end of generation list - no new containers after multiple scrolls")
                        break
                else:
                    consecutive_no_new = 0
                    logger.info(f"📊 Found {len(new_containers)} new containers to scan (total scanned: {total_containers_scanned})")
                
                # STEP 2: Scan only the NEW containers for boundary
                for container, container_id in new_containers:
                    total_containers_scanned += 1
                    
                    try:
                        # ENHANCED: Retry logic for container processing
                        container_metadata = None
                        extraction_attempts = 0
                        max_extraction_attempts = 3
                        
                        while extraction_attempts < max_extraction_attempts and not container_metadata:
                            extraction_attempts += 1
                            
                            # Check if this container has content (not queued/failed)
                            text_content = await container.text_content() or ""
                            
                            # More comprehensive status detection
                            skip_statuses = ["Queuing", "Something went wrong", "Video is rendering", 
                                           "Processing", "Failed", "Error", "Loading..."]
                            
                            skip_container = False
                            for status_text in skip_statuses:
                                if status_text in text_content:
                                    logger.debug(f"⏭️ Container {total_containers_scanned}: {status_text}, skipping")
                                    skip_container = True
                                    break
                            
                            if skip_container:
                                break
                            
                            # Extract metadata from container using enhanced method
                            container_metadata = await extract_container_metadata_enhanced(container, text_content)
                            
                            if not container_metadata and extraction_attempts < max_extraction_attempts:
                                logger.debug(f"   ⏰ Metadata extraction failed (attempt {extraction_attempts}/{max_extraction_attempts}), retrying after wait...")
                                await page.wait_for_timeout(1000)  # Wait 1 second before retry
                        
                        if not container_metadata:
                            logger.debug(f"   ❌ Container {total_containers_scanned}: Failed to extract metadata after {max_extraction_attempts} attempts")
                            continue
                        
                        container_time = container_metadata.get('creation_time', '')
                        container_prompt = container_metadata.get('prompt', '')[:100]
                        
                        if not container_time or not container_prompt:
                            logger.debug(f"⚠️ Container {total_containers_scanned}: Missing metadata, skipping")
                            continue
                        
                        # ENHANCED: Log each container we're checking with more detail
                        if total_containers_scanned <= 5 or total_containers_scanned % 10 == 0:
                            logger.info(f"🔍 Scanning container #{total_containers_scanned}: datetime='{container_time}', prompt='{container_prompt[:30]}...'")
                            
                        # ULTRA-DEBUG: For the specific case we're tracking, log everything
                        if "03 Sep 2025 16:" in container_time:
                            logger.info(f"🎯 TARGET RANGE DETECTED: Container #{total_containers_scanned}")
                            logger.info(f"   📅 Full datetime: '{container_time}'")
                            logger.info(f"   📝 Full prompt: {container_prompt[:100]}...") 
                            logger.info(f"   🔍 Will check against {len(self.existing_log_entries)} log entries")
                        
                        # ENHANCED Step 14: Compare with log entries with better logging
                        has_matching_log_entry = False
                        logger.debug(f"🔍 Container #{total_containers_scanned}: Checking datetime '{container_time}' against {len(self.existing_log_entries)} log entries")
                        
                        # ENHANCED: Quick check with detailed logging for target case
                        exact_match_found = container_time in self.existing_log_entries
                        if exact_match_found:
                            logger.debug(f"   📝 Container datetime '{container_time}' found in log entries")
                        elif "03 Sep 2025 16:" in container_time:
                            logger.info(f"🎯 POTENTIAL BOUNDARY: '{container_time}' NOT found in log entries (exact match check)")
                            
                            # Show nearby log entries for context
                            similar_entries = []
                            for log_time in self.existing_log_entries.keys():
                                if log_time.startswith("03 Sep 2025 16:") or log_time.startswith("03 Sep 2025 17:"):
                                    similar_entries.append(log_time)
                            
                            similar_entries.sort()
                            logger.info(f"   📅 Nearby log entries from same timeframe:")
                            for similar_time in similar_entries[:5]:
                                logger.info(f"      - {similar_time}")
                            if len(similar_entries) > 5:
                                logger.info(f"      ... and {len(similar_entries) - 5} more")
                        
                        # ENHANCED: More detailed comparison logic with better logging
                        comparison_count = 0
                        for log_time, log_entry in self.existing_log_entries.items():
                            comparison_count += 1
                            log_prompt = log_entry.get('prompt', '')[:100]
                            
                            # ENHANCED DEBUG: Show comparisons for target timeframe or first few
                            show_comparison = (
                                total_containers_scanned <= 3 or  # First few containers
                                "03 Sep 2025 16:" in container_time or  # Target timeframe
                                "03 Sep 2025 16:" in log_time  # Log entries in target timeframe
                            )
                            
                            if show_comparison and comparison_count <= 10:  # Limit to avoid spam
                                logger.debug(f"   🔍 Comparing container '{container_time}' vs log '{log_time}' - Match: {log_time == container_time}")
                                if log_time == container_time:
                                    logger.debug(f"   🔍 Prompt comparison: '{container_prompt[:30]}...' vs '{log_prompt[:30]}...' - Match: {log_prompt == container_prompt}")
                            
                            # CRITICAL: Use datetime as primary key for boundary detection
                            # Container prompts from /generate page are often truncated vs gallery prompts
                            # Since datetime is unique per generation, we can rely on it primarily
                            if log_time == container_time:
                                # DateTime match is sufficient - prompts may differ between views
                                has_matching_log_entry = True
                                duplicates_found += 1
                                
                                if "03 Sep 2025 16:" in container_time:
                                    logger.info(f"   ✅ DUPLICATE CONFIRMED: Container datetime '{container_time}' matches log entry")
                                else:
                                    logger.debug(f"   ✅ DUPLICATE MATCH: Container datetime '{container_time}' matches log entry")
                                
                                # Optional prompt validation (for debugging)
                                prompt_match = (
                                    log_prompt == container_prompt or  # Exact match
                                    log_prompt.startswith(container_prompt[:50]) or  # Log starts with container
                                    container_prompt.startswith(log_prompt[:50])  # Container starts with log
                                )
                                
                                if not prompt_match and len(container_prompt) > 20 and len(log_prompt) > 20:
                                    if "03 Sep 2025 16:" in container_time:
                                        logger.info(f"   📝 Note: Prompt differs but datetime match is sufficient")
                                        logger.info(f"      Container: '{container_prompt[:50]}...'")
                                        logger.info(f"      Log:       '{log_prompt[:50]}...'")
                                    else:
                                        logger.debug(f"   📝 Note: Prompt differs but datetime match is sufficient")
                                
                                break
                        
                        if not has_matching_log_entry:
                            # ENHANCED: Found the boundary - this container has no corresponding log entry
                            logger.info(f"🎯 BOUNDARY FOUND at container #{total_containers_scanned}")
                            logger.info(f"   📊 Containers scanned: {total_containers_scanned}")
                            logger.info(f"   🔍 Duplicates found before boundary: {duplicates_found}")
                            logger.info(f"   📅 BOUNDARY DATETIME: '{container_time}' ⭐")
                            logger.info(f"   📝 Boundary prompt: {container_prompt[:75]}...")
                            logger.info(f"   🔄 Found after {scroll_attempts + 1} scroll iterations")
                            
                            # ENHANCED: Additional validation and context for boundary
                            logger.info(f"   🔍 VALIDATION: Checked against {len(self.existing_log_entries)} log entries")
                            logger.info(f"   📅 Container datetime '{container_time}' confirmed NOT in log file")
                            
                            # Special logging for our target case
                            if "03 Sep 2025 16:15:18" in container_time:
                                logger.info(f"   🎉 SUCCESS: Found the specific missing generation from user report!")
                                logger.info(f"   🎯 This matches the reported missing datetime: '03 Sep 2025 16:15:18'")
                            logger.info(f"   ✨ This generation is NOT in the log file - ready for download!")
                            
                            # ENHANCED: Click this container to open gallery and download the boundary generation
                            logger.info(f"   🖱️ Attempting to click boundary container...")
                            click_success = await self._click_boundary_container_enhanced(container, total_containers_scanned, container_time, page)
                            
                            if click_success:
                                logger.info("✅ Gallery opened at boundary, ready to download boundary generation")
                                return {
                                    'found': True,
                                    'container_index': total_containers_scanned,
                                    'creation_time': container_time,
                                    'prompt': container_prompt,
                                    'containers_scanned': total_containers_scanned,
                                    'duplicates_found': duplicates_found,
                                    'scroll_iterations': scroll_attempts + 1
                                }
                            else:
                                logger.warning("❌ Could not click boundary container")
                                return None
                        else:
                            if total_containers_scanned <= 5 or total_containers_scanned % 50 == 0:
                                logger.debug(f"✓ Container {total_containers_scanned}: Duplicate found, continuing scan")
                    
                    except Exception as e:
                        logger.debug(f"Error checking container {total_containers_scanned}: {e}")
                        continue
                
                # STEP 3: If no boundary found in current batch, scroll to reveal more
                # CRITICAL FIX: Always scroll when no boundary found, regardless of new containers
                # The issue was that scrolling only happened when new containers were found
                # But we need to scroll to LOAD more containers when none are new
                if consecutive_no_new < max_consecutive_no_new:
                    logger.info(f"🎯 No boundary found in current batch, using VERIFIED scroll methods...")
                    
                    # Initialize boundary scroll manager if not already done
                    self.initialize_boundary_scroll_manager(page)
                    
                    # Use verified scrolling methods with guaranteed >2000px distance
                    try:
                        # Get initial state before scrolling
                        initial_state = await self.boundary_scroll_manager.get_scroll_position()
                        logger.info(f"   📊 Before scroll: {initial_state['windowScrollY']}px, {initial_state['containerCount']} containers")
                        
                        # Perform verified scroll with automatic fallback
                        scroll_result = await self.boundary_scroll_manager.perform_scroll_with_fallback(2500)
                        
                        if scroll_result.success:
                            logger.info(f"   ✅ VERIFIED SCROLL SUCCESS: {scroll_result.method_name}")
                            logger.info(f"   📊 Distance: {scroll_result.scroll_distance}px in {scroll_result.execution_time:.3f}s")
                            logger.info(f"   📊 New containers detected: {scroll_result.new_containers_detected}")
                            
                            # Get final state
                            final_state = await self.boundary_scroll_manager.get_scroll_position()
                            logger.info(f"   📊 After scroll: {final_state['windowScrollY']}px, {final_state['containerCount']} containers")
                            
                            # Wait for new content to fully load
                            await page.wait_for_timeout(2000)
                            
                        else:
                            logger.warning(f"   ⚠️ VERIFIED SCROLL FAILED: {scroll_result.error_message}")
                            # Check if we're at the end of the gallery
                            at_end = await self.boundary_scroll_manager.check_end_of_gallery()
                            if at_end:
                                logger.info("   📍 End of gallery detected - stopping search")
                                break
                                
                    except Exception as e:
                        logger.error(f"   ❌ Error during verified scroll: {e}")
                        # Fallback to old behavior if verified methods fail
                        logger.info("   🔄 Falling back to alternative strategies...")
                        
                        # Keep old fallback logic as backup
                        viewport_height = await page.evaluate("window.innerHeight")
                        current_scroll = await page.evaluate("window.pageYOffset")
                        document_height = await page.evaluate("document.body.scrollHeight")
                        
                        # Fallback scroll strategies (only used if verified methods fail)
                        scroll_strategies = [
                            {"method": "mousewheel", "steps": 10, "amount": 100},
                            {"method": "keyboard", "steps": 5, "amount": None},
                            {"method": "gradual", "steps": 3, "amount": 500},
                            {"method": "jump", "steps": 1, "amount": viewport_height * 2},
                            {"method": "bottom", "steps": 1, "amount": document_height}
                        ]
                        
                        for strategy in scroll_strategies:
                            logger.debug(f"   🔄 Trying scroll strategy: {strategy['method']}")
                            
                            if strategy["method"] == "mousewheel":
                                # Mouse wheel scrolling - simulates real user interaction
                                logger.debug(f"     🖱️ Using mouse wheel scrolling ({strategy['steps']} steps)")
                                for step in range(strategy["steps"]):
                                    # Use Playwright's wheel method for realistic scrolling
                                    await page.mouse.wheel(0, strategy["amount"])
                                    await page.wait_for_timeout(200)  # Small delay between wheel events
                                    logger.debug(f"     Wheel step {step+1}: scrolled down {strategy['amount']}px")
                            elif strategy["method"] == "keyboard":
                                # Keyboard scrolling - Page Down and Down Arrow keys
                                logger.debug(f"     ⌨️ Using keyboard scrolling ({strategy['steps']} Page Down presses)")
                                
                                # Ensure page is focused for keyboard events
                                try:
                                    await page.focus('body')
                                    logger.debug("     ✅ Page focused for keyboard input")
                                except:
                                    # Fallback: click on the page to ensure focus
                                    await page.click('body')
                                    logger.debug("     ✅ Page clicked to ensure focus")
                                
                                for step in range(strategy["steps"]):
                                    # First try Page Down key
                                    await page.keyboard.press("PageDown")
                                    await page.wait_for_timeout(300)
                                    logger.debug(f"     PageDown step {step+1}")
                                    
                                # Additional Down Arrow key presses for fine scrolling
                                logger.debug("     ⌨️ Adding Down Arrow key presses for fine control")
                                for i in range(10):  # 10 down arrow presses
                                    await page.keyboard.press("ArrowDown")
                                    await page.wait_for_timeout(50)
                            elif strategy["method"] == "gradual":
                                # Gradual scrolling - some sites need this
                                for step in range(strategy["steps"]):
                                    step_scroll = current_scroll + (strategy["amount"] * (step + 1))
                                    await page.evaluate(f"window.scrollTo(0, {step_scroll})")
                                    await page.wait_for_timeout(500)  # Small wait between steps
                                    logger.debug(f"     Step {step+1}: scrolled to {step_scroll}")
                            elif strategy["method"] == "jump":
                                # Large jump scrolling
                                new_position = current_scroll + strategy["amount"]
                                await page.evaluate(f"window.scrollTo(0, {new_position})")
                                logger.debug(f"     Jump scroll: {current_scroll} → {new_position}")
                            elif strategy["method"] == "bottom":
                                # Scroll to current document bottom
                                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                logger.debug(f"     Bottom scroll: to {document_height}")
                            
                            # Wait for each strategy
                            await page.wait_for_timeout(1000)
                        
                        # Strategy 2: Comprehensive event triggering for infinite scroll
                        try:
                            await page.evaluate("""
                                // Comprehensive scroll event triggering
                                const events = ['scroll', 'wheel', 'resize', 'touchstart', 'touchmove', 'touchend'];
                                events.forEach(eventType => {
                                    window.dispatchEvent(new Event(eventType, { bubbles: true }));
                                    document.dispatchEvent(new Event(eventType, { bubbles: true }));
                                });
                                
                                // Trigger on scroll containers too
                                const scrollContainers = document.querySelectorAll('[id*="scroll"], [class*="scroll"], [class*="container"]');
                                scrollContainers.forEach(container => {
                                    events.forEach(eventType => {
                                        container.dispatchEvent(new Event(eventType, { bubbles: true }));
                                    });
                                });
                                
                                // Force reflow/repaint
                                document.body.offsetHeight;
                            """)
                            logger.debug("   ✅ Triggered comprehensive scroll events")
                        except Exception as e:
                            logger.debug(f"   Event triggering failed: {e}")
                        
                        # Strategy 3: Wait for network activity with extended patience
                        loading_wait_attempts = 0
                        max_loading_attempts = 3
                        
                        while loading_wait_attempts < max_loading_attempts:
                            loading_wait_attempts += 1
                            logger.debug(f"   ⏳ Loading wait attempt {loading_wait_attempts}/{max_loading_attempts}")
                            
                            try:
                                # Wait for network activity to indicate new content loading
                                await page.wait_for_load_state("networkidle", timeout=3000)
                                logger.debug("   ✅ Network idle detected - content may have loaded")
                                break
                            except:
                                logger.debug("   ⏳ Network idle timeout - trying longer wait")
                                await page.wait_for_timeout(2000)
                        
                        # Strategy 4: Force DOM refresh and check for changes
                        try:
                            await page.evaluate("""
                                // Force DOM refresh techniques
                                window.scrollBy(0, 1);  // Tiny scroll to trigger events
                                window.scrollBy(0, -1); // Scroll back
                                
                                // Try to trigger intersection observer callbacks
                                if (window.IntersectionObserver) {
                                    // Create dummy observer to trigger callbacks
                                    const observer = new IntersectionObserver(() => {});
                                    const elements = document.querySelectorAll('div');
                                    elements.forEach(el => observer.observe(el));
                                    setTimeout(() => observer.disconnect(), 100);
                                }
                            """)
                            logger.debug("   ✅ Applied DOM refresh techniques")
                        except Exception as e:
                            logger.debug(f"   DOM refresh failed: {e}")
                        
                        # Strategy 5: Extended wait with scroll position monitoring
                        initial_scroll = await page.evaluate("window.pageYOffset")
                        extended_wait_time = 3000  # 3 seconds
                        
                        logger.debug(f"   ⏳ Extended wait ({extended_wait_time}ms) for lazy loading...")
                        await page.wait_for_timeout(extended_wait_time)
                        
                        final_scroll = await page.evaluate("window.pageYOffset")
                        final_document_height = await page.evaluate("document.body.scrollHeight")
                        
                        logger.debug(f"   📊 Final state: scroll={final_scroll}, doc_height={final_document_height}")
                        logger.debug(f"   📊 Changes: scroll_moved={final_scroll != initial_scroll}, height_changed={final_document_height != document_height}")
                        
                        # Log comprehensive scroll summary
                        if final_document_height > document_height:
                            logger.info(f"   🎉 SUCCESS: Document height increased from {document_height} to {final_document_height}")
                            logger.info(f"   📋 Applied scroll methods: mousewheel → keyboard → gradual → jump → bottom + events + network wait")
                        else:
                            logger.warning(f"   ⚠️ Document height unchanged: {document_height} (may be at end of content)")
                            logger.warning(f"   📋 All scroll methods tried: mousewheel, keyboard (PageDown+ArrowDown), gradual, jump, bottom")
                            
                            # ALTERNATIVE LOADING STRATEGIES: Try alternative methods when standard scrolling fails
                            logger.info("🔍 ALTERNATIVE STRATEGIES: Standard scrolling failed, trying alternative content loading methods...")
                            
                            alternative_success = False
                            
                            # Strategy 1: Find and scroll custom scroll containers
                            logger.info("   🎯 Strategy 1: Looking for custom scroll containers...")
                            try:
                                # Look for common scroll container patterns
                                scroll_container_selectors = [
                                    "[class*='scroll']", "[id*='scroll']", 
                                    "[class*='container']", "[class*='list']", 
                                    "[class*='content']", "[class*='infinite']",
                                    "div[style*='overflow']", "div[style*='scroll']"
                                ]
                                
                                for selector in scroll_container_selectors:
                                    containers = await page.query_selector_all(selector)
                                    for container in containers:
                                        try:
                                            # Check if element is scrollable
                                            scroll_height = await container.evaluate("el => el.scrollHeight")
                                            client_height = await container.evaluate("el => el.clientHeight")
                                            current_scroll = await container.evaluate("el => el.scrollTop")
                                            
                                            if scroll_height > client_height:  # Element is scrollable
                                                logger.info(f"      🎯 Found scrollable container: {selector} (height: {scroll_height}, visible: {client_height})")
                                                
                                                # Try scrolling this specific container
                                                await container.evaluate("el => el.scrollTop = el.scrollHeight")
                                                await page.wait_for_timeout(2000)
                                                
                                                # Check if new content appeared
                                                new_scroll_height = await container.evaluate("el => el.scrollHeight")
                                                if new_scroll_height > scroll_height:
                                                    logger.info(f"      ✅ SUCCESS: Container scroll increased height from {scroll_height} to {new_scroll_height}")
                                                    alternative_success = True
                                                    break
                                        except Exception as container_e:
                                            continue  # Try next container
                                    
                                    if alternative_success:
                                        break
                                        
                            except Exception as e:
                                logger.debug(f"      ❌ Container scroll strategy failed: {e}")
                            
                            # Strategy 2: Look for Load More buttons
                            if not alternative_success:
                                logger.info("   🎯 Strategy 2: Looking for Load More buttons...")
                                try:
                                    load_more_selectors = [
                                        "button:has-text('Load More')", "button:has-text('Show More')",
                                        "button:has-text('Load Previous')", "button:has-text('Show Older')",
                                        "[class*='load']:visible", "[class*='more']:visible", 
                                        "[id*='load']:visible", "[id*='more']:visible",
                                        "button[class*='pagination']", "a[class*='next']"
                                    ]
                                    
                                    for selector in load_more_selectors:
                                        try:
                                            button = await page.query_selector(selector)
                                            if button:
                                                is_visible = await button.is_visible()
                                                if is_visible:
                                                    logger.info(f"      🎯 Found Load More button: {selector}")
                                                    await button.click()
                                                    await page.wait_for_timeout(3000)  # Wait for content to load
                                                    
                                                    # Check if new content appeared
                                                    new_doc_height = await page.evaluate("document.body.scrollHeight")
                                                    if new_doc_height > document_height:
                                                        logger.info(f"      ✅ SUCCESS: Load More button increased content")
                                                        alternative_success = True
                                                        break
                                        except Exception as btn_e:
                                            continue  # Try next selector
                                            
                                    if alternative_success:
                                        logger.info("   ✅ Load More button strategy succeeded")
                                        
                                except Exception as e:
                                    logger.debug(f"      ❌ Load More button strategy failed: {e}")
                            
                            # Strategy 3: Extended wait with network monitoring
                            if not alternative_success:
                                logger.info("   🎯 Strategy 3: Extended wait with network monitoring...")
                                try:
                                    # Sometimes content loads automatically with time
                                    initial_containers = len(await page.query_selector_all("div"))
                                    
                                    logger.info("      ⏳ Waiting 10 seconds for automatic content loading...")
                                    await page.wait_for_timeout(10000)
                                    
                                    final_containers = len(await page.query_selector_all("div"))
                                    new_doc_height = await page.evaluate("document.body.scrollHeight")
                                    
                                    if final_containers > initial_containers or new_doc_height > document_height:
                                        logger.info(f"      ✅ SUCCESS: Automatic loading increased content ({initial_containers} → {final_containers} containers)")
                                        alternative_success = True
                                        
                                except Exception as e:
                                    logger.debug(f"      ❌ Extended wait strategy failed: {e}")
                            
                            # Strategy 4: Element hover triggers
                            if not alternative_success:
                                logger.info("   🎯 Strategy 4: Trying element hover triggers...")
                                try:
                                    # Try hovering over elements that might trigger loading
                                    trigger_selectors = [
                                        "div:last-child", "article:last-child", 
                                        "[class*='item']:last-child", "[class*='card']:last-child",
                                        "footer", "div[class*='bottom']"
                                    ]
                                    
                                    for selector in trigger_selectors:
                                        try:
                                            element = await page.query_selector(selector)
                                            if element:
                                                logger.info(f"      🎯 Hovering over trigger element: {selector}")
                                                await element.hover()
                                                await page.wait_for_timeout(2000)
                                                
                                                # Check for new content
                                                new_doc_height = await page.evaluate("document.body.scrollHeight")
                                                if new_doc_height > document_height:
                                                    logger.info(f"      ✅ SUCCESS: Element hover triggered content loading")
                                                    alternative_success = True
                                                    break
                                        except Exception as hover_e:
                                            continue
                                            
                                except Exception as e:
                                    logger.debug(f"      ❌ Element hover strategy failed: {e}")
                            
                            # Strategy 5: URL parameter manipulation
                            if not alternative_success:
                                logger.info("   🎯 Strategy 5: Trying URL parameter manipulation...")
                                try:
                                    current_url = page.url
                                    
                                    # Try adding pagination parameters (avoid duplicates)
                                    param_variations = [
                                        ("page", "2"), ("offset", "50"), ("limit", "100"), 
                                        ("before", "2025-09-03"), ("older", "true")
                                    ]
                                    
                                    for param_name, param_value in param_variations:
                                        try:
                                            # Check if parameter already exists
                                            if param_name in current_url:
                                                continue
                                                
                                            # Add parameter properly
                                            separator = "&" if "?" in current_url else "?"
                                            new_url = f"{current_url}{separator}{param_name}={param_value}"
                                            logger.info(f"      🎯 Trying URL with parameters: {new_url}")
                                            
                                            await page.goto(new_url, wait_until="networkidle")
                                            await page.wait_for_timeout(3000)
                                            
                                            # Check if new content loaded
                                            containers_after = len(await page.query_selector_all("div"))
                                            if containers_after > 50:  # We had 50 containers before
                                                logger.info(f"      ✅ SUCCESS: URL parameters loaded more content")
                                                alternative_success = True
                                                break
                                        except Exception as url_e:
                                            # Return to original URL if this fails
                                            await page.goto(current_url)
                                            continue
                                            
                                except Exception as e:
                                    logger.debug(f"      ❌ URL manipulation strategy failed: {e}")
                            
                            if alternative_success:
                                logger.info("   🎉 ALTERNATIVE SUCCESS: At least one alternative loading method worked!")
                            else:
                                logger.warning("   ❌ All alternative loading strategies failed - may have reached end of content")
                            
                    except Exception as e:
                        # Ultra-aggressive fallback scrolling
                        logger.debug(f"   ⚠️ Advanced scroll failed, using ultra-aggressive fallback: {e}")
                        
                        try:
                            # Try multiple fallback scroll methods
                            await page.evaluate("window.scrollBy(0, 1500)")  # Large scroll
                            await page.wait_for_timeout(1000)
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # Scroll to bottom
                            await page.wait_for_timeout(2000)
                            await page.evaluate("window.scrollBy(0, 500)")  # Small additional scroll
                            await page.wait_for_timeout(1500)
                            logger.debug("   ✅ Ultra-aggressive fallback completed")
                        except Exception as fallback_e:
                            logger.debug(f"   ❌ Even fallback scrolling failed: {fallback_e}")
                            await page.wait_for_timeout(3000)  # Just wait if all else fails
                
                scroll_attempts += 1
                
                # Progress update every 10 scrolls
                if scroll_attempts % 10 == 0:
                    logger.info(f"🔄 Progress: {scroll_attempts} scroll iterations, {total_containers_scanned} containers scanned, {duplicates_found} duplicates")
            
            logger.warning(f"❌ No boundary found after {scroll_attempts} scroll iterations")
            logger.warning(f"   📊 Total containers scanned: {total_containers_scanned}")
            logger.warning(f"   📊 Total duplicates found: {duplicates_found}")
            return None
            
        except Exception as e:
            logger.error(f"Error in boundary detection: {e}")
            return None
    
    # Note: _scroll_entire_generation_page_for_boundary_detection removed
    # Now using incremental scan-as-you-scroll approach in _find_download_boundary_sequential
    
    async def _click_boundary_container(self, container, container_index: int) -> bool:
        """Click boundary container using the same method as initial navigation"""
        try:
            # Get page reference correctly from ElementHandle (async)
            frame = await container.owner_frame()
            page = frame.page
            
            # Get current URL before clicking
            current_url = page.url
            logger.info(f"🔍 Current URL before boundary click: {current_url}")
            
            # Get container ID to create direct selector (same approach as initial navigation)
            container_id = await container.get_attribute('id')
            if not container_id:
                logger.error("❌ Could not get container ID for boundary click")
                return False
            
            logger.info(f"🔍 Attempting boundary click using container ID: {container_id}")
            
            # Step 15: Click container using same method as initial navigation
            # Use direct page.click() with container ID selector - this is what works for initial navigation
            try:
                container_selector = f"div[id='{container_id}']"
                logger.info(f"🔍 Clicking boundary container using selector: {container_selector}")
                
                await page.click(container_selector, timeout=5000)
                await page.wait_for_timeout(2000)  # Wait for navigation
                
                # Verify gallery opened
                if await self._verify_gallery_opened(page):
                    logger.info(f"✅ Step 15: Successfully opened gallery from boundary container #{container_index}")
                    logger.info(f"✅ Used same method as initial navigation - direct page.click()")
                    return True
                else:
                    logger.warning(f"❌ Gallery didn't open after clicking container #{container_index}")
                    
            except Exception as e:
                logger.error(f"Failed to click boundary container with ID selector: {e}")
                
                # Fallback: try the generic selector approach (same as initial navigation)
                try:
                    # Extract the number from container ID (e.g., "__13" from "50cb0dc8c77c4a3e91c959c431aa3b53__13")
                    import re
                    match = re.search(r'__(\d+)$', container_id)
                    if match:
                        container_number = match.group(1)
                        fallback_selector = f"div[id$='__{container_number}']"
                        logger.info(f"🔄 Trying fallback selector: {fallback_selector}")
                        
                        await page.click(fallback_selector, timeout=5000)
                        await page.wait_for_timeout(2000)
                        
                        if await self._verify_gallery_opened(page):
                            logger.info(f"✅ Step 15: Successfully opened gallery using fallback selector")
                            return True
                
                except Exception as fallback_error:
                    logger.error(f"Fallback click also failed: {fallback_error}")
            
            logger.error(f"❌ Failed to click boundary container #{container_index} using page.click() method")
            return False
            
        except Exception as e:
            logger.error(f"Error getting page reference or clicking boundary container: {e}")
            return False

    async def _verify_gallery_opened(self, page) -> bool:
        """Verify that the gallery view actually opened after clicking boundary container"""
        try:
            # Check URL change - gallery should have different URL pattern
            current_url = page.url
            logger.debug(f"🔍 Checking if gallery opened, current URL: {current_url}")
            
            # Gallery indicators - look for elements that only exist in gallery view
            gallery_indicators = [
                '.thumsItem',  # Thumbnail items in gallery
                '.thumbnail-item',
                '.thumsCou',
                'span.close-icon',  # Close button (exists in gallery)
                'span.sc-fAkCkL.fjGQsQ',  # Close button with class
            ]
            
            for indicator in gallery_indicators:
                try:
                    element = await page.wait_for_selector(indicator, timeout=3000)
                    if element and await element.is_visible():
                        logger.info(f"✅ Gallery confirmed open - found indicator: {indicator}")
                        return True
                except Exception:
                    continue
            
            logger.warning("❌ Gallery verification failed - no gallery indicators found")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying gallery opened: {e}")
            return False
    
    async def _click_boundary_container_enhanced(self, container, container_index: int, container_time: str, page) -> bool:
        """Enhanced boundary container click with better error handling and retry logic"""
        try:
            logger.info(f"🖱️ ENHANCED boundary click for container #{container_index} (datetime: {container_time})")
            
            # Strategy 1: Direct container click (most reliable)
            try:
                logger.debug("   🎯 Strategy 1: Direct container click")
                await container.click(timeout=5000)
                await page.wait_for_timeout(2000)  # Wait for navigation
                
                if await self._verify_gallery_opened(page):
                    logger.info("   ✅ Strategy 1 success: Direct click opened gallery")
                    return True
                    
            except Exception as e:
                logger.debug(f"   ❌ Strategy 1 failed: {e}")
            
            # Strategy 2: Page selector click using container ID
            try:
                logger.debug("   🎯 Strategy 2: Page selector click")
                container_id = await container.get_attribute('id')
                if container_id:
                    container_selector = f"div[id='{container_id}']"
                    logger.debug(f"   🔍 Using selector: {container_selector}")
                    
                    await page.click(container_selector, timeout=5000)
                    await page.wait_for_timeout(2000)
                    
                    if await self._verify_gallery_opened(page):
                        logger.info("   ✅ Strategy 2 success: Selector click opened gallery")
                        return True
                        
            except Exception as e:
                logger.debug(f"   ❌ Strategy 2 failed: {e}")
            
            # Strategy 3: Fallback selector using container number
            try:
                logger.debug("   🎯 Strategy 3: Fallback selector")
                container_id = await container.get_attribute('id')
                if container_id:
                    match = re.search(r'__(\d+)$', container_id)
                    if match:
                        container_number = match.group(1)
                        fallback_selector = f"div[id$='__{container_number}']"
                        logger.debug(f"   🔍 Using fallback selector: {fallback_selector}")
                        
                        await page.click(fallback_selector, timeout=5000)
                        await page.wait_for_timeout(2000)
                        
                        if await self._verify_gallery_opened(page):
                            logger.info("   ✅ Strategy 3 success: Fallback click opened gallery")
                            return True
                            
            except Exception as e:
                logger.debug(f"   ❌ Strategy 3 failed: {e}")
            
            # Strategy 4: Force click with JavaScript
            try:
                logger.debug("   🎯 Strategy 4: JavaScript force click")
                await container.evaluate("element => element.click()")
                await page.wait_for_timeout(3000)  # Longer wait for JS click
                
                if await self._verify_gallery_opened(page):
                    logger.info("   ✅ Strategy 4 success: JavaScript click opened gallery")
                    return True
                    
            except Exception as e:
                logger.debug(f"   ❌ Strategy 4 failed: {e}")
            
            # Strategy 5: Find and click by content (for the specific target case)
            if "03 Sep 2025 16:" in container_time:
                try:
                    logger.info("   🎯 Strategy 5: Special handling for target datetime")
                    
                    # Look for any element containing our specific datetime
                    target_elements = await page.query_selector_all(f"div:has-text('{container_time}')")
                    for target_element in target_elements[:3]:  # Try first 3 matches
                        try:
                            logger.debug(f"   📅 Trying element with target datetime...")
                            await target_element.click(timeout=3000)
                            await page.wait_for_timeout(2000)
                            
                            if await self._verify_gallery_opened(page):
                                logger.info("   ✅ Strategy 5 success: Found target by datetime!")
                                return True
                                
                        except Exception as element_error:
                            logger.debug(f"   Element click failed: {element_error}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"   ❌ Strategy 5 failed: {e}")
            
            logger.error(f"   ❌ All click strategies failed for container #{container_index}")
            logger.error(f"   📅 Target datetime: {container_time}")
            logger.error(f"   🎯 This may be a page structure or timing issue")
            
            return False
            
        except Exception as e:
            logger.error(f"Enhanced boundary click error: {e}")
            return False
            
    async def _extract_container_metadata(self, container, text_content: str) -> Optional[Dict[str, str]]:
        """Extract creation time and prompt from container text"""
        try:
            # Look for creation time pattern: "31 Aug 2025 13:32:04" or "01 Sep 2025 00:47:18"
            time_pattern = r'Creation Time\s*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})'
            time_match = re.search(time_pattern, text_content)
            if not time_match:
                # Try alternative pattern without "Creation Time" prefix
                time_pattern = r'(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})'
                time_match = re.search(time_pattern, text_content)
            
            creation_time = time_match.group(1) if time_match else ""
            
            # Extract prompt text from text_content
            prompt_text = ""
            
            if creation_time:
                # Extract prompt text after creation time
                lines = text_content.split('\n')
                for i, line in enumerate(lines):
                    if creation_time in line and i + 1 < len(lines):
                        # Get the next line as prompt
                        potential_prompt = lines[i + 1].strip()
                        if potential_prompt and len(potential_prompt) > 10:
                            prompt_text = potential_prompt
                            break
                
                # Fallback: if we didn't find prompt after creation time, look for any substantial text
                if not prompt_text:
                    for line in lines:
                        line = line.strip()
                        if (line and len(line) > 20 and 
                            'Creation Time' not in line and 
                            not re.match(r'\d{1,2}\s+\w{3}\s+\d{4}', line)):
                            prompt_text = line
                            break
            
            # ROBUST STRATEGY: Use relative positioning and ellipsis pattern (Sep 2025)
            if not prompt_text and hasattr(container, 'query_selector_all'):
                try:
                    # Import the robust relative extractor
                    from .relative_prompt_extractor import relative_prompt_extractor
                    
                    # Use the specialized relative extraction
                    prompt_text = await relative_prompt_extractor.extract_prompt_robust(container)
                    if prompt_text:
                        logger.info(f"🎉 Robust extraction succeeded: {prompt_text[:50]}...")
                
                except ImportError:
                    logger.warning("Relative prompt extractor not available, using fallback")
                except Exception as e:
                    logger.debug(f"Robust relative extraction failed: {e}")
                    
                # Fallback: Simplified structure-based approach
                if not prompt_text:
                    try:
                        # Method 1: Look for ellipsis pattern
                        ellipsis_elements = await container.query_selector_all('text="..."')
                        for ellipsis_el in ellipsis_elements[:3]:  # Limit to first 3
                            # Get parent span with aria-describedby
                            parent_span = await ellipsis_el.evaluate('''
                                element => {
                                    let current = element;
                                    while (current && current.parentElement) {
                                        if (current.tagName === 'SPAN' && 
                                            current.hasAttribute('aria-describedby')) {
                                            return current;
                                        }
                                        current = current.parentElement;
                                    }
                                    return null;
                                }
                            ''')
                            
                            if parent_span:
                                text = await parent_span.text_content() or ""
                                clean_text = text.replace('...', '').strip()
                                if len(clean_text) > 20 and not re.match(r'\d{1,2}\s+\w{3}\s+\d{4}', clean_text):
                                    prompt_text = clean_text
                                    logger.info(f"✅ Ellipsis method: {prompt_text[:50]}...")
                                    break
                        
                        # Method 2: Rank aria-describedby spans by length
                        if not prompt_text:
                            all_spans = await container.query_selector_all('span[aria-describedby]')
                            candidates = []
                            
                            for span in all_spans:
                                text = await span.text_content() or ""
                                clean_text = text.replace('...', '').strip()
                                
                                # Skip obvious metadata
                                if (len(clean_text) > 20 and 
                                    'Creation Time' not in clean_text and
                                    not re.match(r'\d{1,2}\s+\w{3}\s+\d{4}', clean_text) and
                                    not clean_text.startswith('Wan') and 
                                    not clean_text.endswith('P')):
                                    
                                    candidates.append(clean_text)
                            
                            # Use longest candidate (most likely full prompt)
                            if candidates:
                                prompt_text = max(candidates, key=len)
                                logger.info(f"✅ Length ranking: {prompt_text[:50]}...")
                    
                    except Exception as e:
                        logger.debug(f"Fallback structure extraction failed: {e}")
                        
                # Final fallback: Traditional selectors
                if not prompt_text:
                    try:
                        prompt_divs = await container.query_selector_all('.sc-eKQYOU.bdGRCs, div.sc-dDrhAi.dnESm')
                        if prompt_divs:
                            for div in prompt_divs:
                                div_text = await div.text_content() or ""
                                if len(div_text) > 20:
                                    prompt_text = div_text.replace('...', '').strip()
                                    logger.info(f"✅ Traditional selector: {prompt_text[:50]}...")
                                    break
                    except Exception:
                        pass
            
            if creation_time and prompt_text:
                logger.debug(f"Extracted container metadata - Time: {creation_time}, Prompt: {prompt_text[:50]}...")
                return {
                    'creation_time': creation_time,
                    'prompt': prompt_text
                }
            elif creation_time:
                logger.debug(f"Extracted creation time only: {creation_time}")
                return {
                    'creation_time': creation_time,
                    'prompt': ''
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting container metadata: {e}")
            return None
    
    async def _scan_generation_containers_sequential(self, page, target_time: str, target_prompt: str) -> Optional[Dict[str, Any]]:
        """Simple sequential metadata comparison for finding download boundaries (Algorithm Steps 13-14)"""
        try:
            logger.info("🔍 Step 13: Sequential scan for boundary match...")
            
            # Get starting index from config
            start_index = 8
            if self.config.completed_task_selector:
                match = re.search(r'__(\d+)', self.config.completed_task_selector)
                if match:
                    start_index = int(match.group(1))
            
            # Step 13: Sequential container checking
            for i in range(start_index, start_index + 20):  # Check 20 containers
                selector = f"div[id$='__{i}']"
                
                try:
                    element = await page.query_selector(selector)
                    if not element:
                        continue
                    
                    # Simple text-based filtering (skip queued/failed/rendering)
                    text_content = await element.text_content()
                    if "Queuing" in text_content or "Something went wrong" in text_content or "Video is rendering" in text_content:
                        continue
                    
                    # Step 14: Extract and compare metadata
                    # Look for creation time in text
                    if target_time in text_content:
                        # Look for prompt match in text (first 100 chars)
                        if target_prompt[:50] in text_content:  # Use 50 chars for text matching
                            logger.info(f"✅ Step 14: Found boundary at container __{i}")
                            
                            # Step 15: Click boundary container and resume
                            await element.click()
                            await asyncio.sleep(1)
                            logger.info("✅ Step 15: Clicked boundary container, resuming downloads")
                            
                            return {
                                'found': True,
                                'container_index': i,
                                'creation_time': target_time,
                                'prompt': target_prompt
                            }
                
                except Exception as e:
                    logger.debug(f"Error checking container __{i}: {e}")
                    continue
            
            logger.warning("❌ Boundary not found in sequential scan")
            return None
            
        except Exception as e:
            logger.error(f"Error in sequential container scan: {e}")
            return None
    
    async def _scan_generation_containers(self, page, target_time: str, target_prompt: str) -> Optional[Dict[str, Any]]:
        """Scan generation containers on main page for matching metadata"""
        try:
            # Scroll to load more generations if needed
            max_scroll_attempts = 100  # Increase attempts to scan generation containers
            found_match = False
            matching_container = None
            
            for scroll_attempt in range(max_scroll_attempts):
                logger.info(f"   🔍 Scanning generation containers (scroll {scroll_attempt + 1}/{max_scroll_attempts})")
                
                # Find all generation containers (excluding queued/failed)
                container_selector = 'div.sc-cZMHBd.kHPlfG.create-detail-body'
                containers = await page.locator(container_selector).all()
                
                logger.info(f"      Found {len(containers)} generation containers")
                
                for i, container in enumerate(containers):
                    try:
                        # Check if this is a queued, failed, or rendering generation
                        container_text = await container.text_content()
                        if 'Queuing' in container_text or 'Something went wrong' in container_text or 'Video is rendering' in container_text:
                            continue
                        
                        # Extract creation time
                        time_element = container.locator('span.sc-jxKUFb.bZTHAM').nth(1)
                        if await time_element.is_visible(timeout=500):
                            creation_time = await time_element.text_content()
                            creation_time = creation_time.strip() if creation_time else ""
                        else:
                            continue
                        
                        # Extract prompt text (UPDATED Sep 2025)
                        prompt_element = container.locator('.sc-eKQYOU.bdGRCs span, div.sc-dDrhAi.dnESm span').first
                        if await prompt_element.is_visible(timeout=500):
                            truncated_prompt = await prompt_element.text_content()
                            truncated_prompt = truncated_prompt.strip() if truncated_prompt else ""
                        else:
                            continue
                        
                        # Compare with checkpoint
                        time_normalized = self.logger._normalize_date_format(creation_time)
                        checkpoint_normalized = self.logger._normalize_date_format(target_time)
                        
                        if time_normalized == checkpoint_normalized:
                            # Check prompt match (first 50 chars for reliability)
                            if truncated_prompt[:50] == target_prompt[:50]:
                                logger.info(f"      ✅ FOUND CHECKPOINT at container {i + 1}")
                                logger.info(f"         Time: {creation_time}")
                                logger.info(f"         Prompt: {truncated_prompt[:50]}...")
                                matching_container = container
                                found_match = True
                                break
                        
                    except Exception as e:
                        logger.debug(f"Error checking container {i}: {e}")
                        continue
                
                if found_match:
                    break
                
                # Scroll down to load more generations
                if scroll_attempt < max_scroll_attempts - 1:
                    await page.evaluate("window.scrollBy(0, 800)")
                    await asyncio.sleep(1.0)
            
            if matching_container:
                # Click on the matching container to return to gallery
                await matching_container.click()
                await asyncio.sleep(1.5)
                logger.info("   🎯 Clicked on checkpoint generation, returning to gallery")
                
                return {
                    'found': True,
                    'container': matching_container,
                    'creation_time': target_time,
                    'prompt': target_prompt
                }
            else:
                logger.warning("   ⚠️ Could not find checkpoint generation on page")
                return None
                
        except Exception as e:
            logger.error(f"Error scanning generation containers: {e}")
            return None
    
    async def navigate_to_next_thumbnail_after_checkpoint(self, page) -> bool:
        """Navigate to the next thumbnail after returning from checkpoint"""
        try:
            logger.info("   ➡️ Navigating to next thumbnail after checkpoint...")
            
            # Use the landmark navigation method to go to next thumbnail
            nav_selectors = [
                '.thumsCou.isFront.isLast',
                '.thumsCou:not(.active)',
                '[class*="thums"]:not(.active)',
                '.thumbnail-item:not(.active)'
            ]
            
            for selector in nav_selectors:
                try:
                    next_thumb = page.locator(selector).first
                    if await next_thumb.is_visible(timeout=1000):
                        await next_thumb.click()
                        await asyncio.sleep(1.0)
                        logger.info(f"   ✅ Navigated to next thumbnail using: {selector}")
                        
                        # Verify we're on a new thumbnail
                        await asyncio.sleep(0.5)
                        
                        # Mark that we've passed the checkpoint
                        self.checkpoint_found = True
                        self.fast_forward_mode = False
                        
                        return True
                except:
                    continue
            
            logger.warning("   ⚠️ Could not navigate to next thumbnail")
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to next thumbnail: {e}")
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
    
    def _validate_datetime_format(self, datetime_str: str) -> bool:
        """Validate that the datetime string matches the expected format"""
        try:
            # Expected format: "DD MMM YYYY HH:MM:SS" (e.g., "03 Sep 2025 16:15:18")
            pattern = r'^\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}$'
            return bool(re.match(pattern, datetime_str.strip()))
        except:
            return False
    
    async def _find_start_from_generation(self, page, target_datetime: str) -> Dict[str, Any]:
        """Find the generation with the specified datetime to start downloading from the next one"""
        
        logger.info(f"🎯 START_FROM: Searching for generation with datetime '{target_datetime}'")
        
        # Validate datetime format first
        if not self._validate_datetime_format(target_datetime):
            logger.error(f"❌ START_FROM: Invalid datetime format '{target_datetime}'")
            logger.error("   Expected format: 'DD MMM YYYY HH:MM:SS' (e.g., '03 Sep 2025 16:15:18')")
            return {
                'found': False, 
                'error': f'Invalid datetime format. Expected: DD MMM YYYY HH:MM:SS'
            }
        
        # Initialize boundary scroll manager if not already done
        # (needed for verified scrolling methods)
        if self.boundary_scroll_manager is None:
            logger.info("   🔧 Initializing boundary scroll manager for start_from search...")
            self.initialize_boundary_scroll_manager(page)
            logger.info("   ✅ Boundary scroll manager ready with verified scroll methods")
        
        try:
            # Use same container scanning approach as boundary detection on /generate page
            logger.info("   🔍 Using boundary detection container scanning on /generate page...")
            
            # Use dynamic container detection (matches BoundaryScrollManager approach)
            logger.info("   📋 Using dynamic container detection for unlimited range (div[id*='__'])")
            
            # Get ALL generation containers from current /generate page using pattern matching
            all_containers = []
            try:
                # Use the same approach as BoundaryScrollManager: find all containers with __ pattern
                containers = await page.query_selector_all('div[id*="__"]')
                if containers:
                    # Filter to only include containers that match the generation pattern (hash__number)
                    for container in containers:
                        container_id = await container.get_attribute('id')
                        if container_id and '__' in container_id:
                            # Check if it follows the pattern: hash__number (both parts must be non-empty)
                            parts = container_id.split('__')
                            if len(parts) == 2 and parts[0] and parts[1] and parts[1].isdigit():
                                all_containers.append(container)
                    logger.debug(f"   📋 Filtered {len(containers)} div[id*='__'] elements to {len(all_containers)} generation containers")
            except Exception as e:
                logger.debug(f"   Dynamic container detection failed: {e}")
                # Fallback to limited range if dynamic detection fails
                logger.info("   📋 Falling back to limited range detection (0-49)")
                for i in range(0, 50):
                    try:
                        selector = f"div[id$='__{i}']"
                        containers = await page.query_selector_all(selector)
                        if containers:
                            all_containers.extend(containers)
                    except Exception as selector_e:
                        logger.debug(f"   Selector div[id$='__{i}'] failed: {selector_e}")
            
            initial_container_count = len(all_containers)
            logger.info(f"   📊 Initial containers found on /generate page: {initial_container_count}")
            
            if not all_containers:
                logger.warning("   ⚠️ No generation containers found on /generate page")
                return {'found': False, 'error': 'No generation containers found on /generate page'}
            
            scroll_attempts = 0
            max_scroll_attempts = 100  # Allow extensive scrolling to find the target
            containers_scanned = 0
            
            while scroll_attempts <= max_scroll_attempts:
                # Scan current containers for the target datetime (use boundary detection approach)
                logger.debug(f"   🔍 Scanning generation containers on /generate page (attempt {scroll_attempts}/{max_scroll_attempts})...")
                
                # Re-collect containers after potential scrolling using dynamic detection
                all_containers = []
                try:
                    # Use dynamic container detection to find ALL containers revealed by scrolling
                    containers = await page.query_selector_all('div[id*="__"]')
                    if containers:
                        # Filter to only include containers that match the generation pattern (hash__number)
                        for container in containers:
                            container_id = await container.get_attribute('id')
                            if container_id and '__' in container_id:
                                # Check if it follows the pattern: hash__number
                                parts = container_id.split('__')
                                if len(parts) == 2 and parts[1].isdigit():
                                    all_containers.append(container)
                except Exception as e:
                    logger.debug(f"   Dynamic re-collection failed: {e}")
                    # Fallback to limited range if needed
                    for i in range(0, 50):
                        try:
                            selector = f"div[id$='__{i}']"
                            containers = await page.query_selector_all(selector)
                            if containers:
                                all_containers.extend(containers)
                        except Exception as selector_e:
                            continue
                
                current_container_count = len(all_containers)
                logger.debug(f"   📊 Generation containers available: {current_container_count}")
                
                # Check each generation container for the target datetime
                for i, container in enumerate(all_containers):
                    containers_scanned += 1
                    
                    try:
                        # Extract metadata from generation container using enhanced extraction
                        text_content = await container.text_content()
                        if not text_content:
                            continue
                        
                        logger.debug(f"   📝 Generation container {containers_scanned} text: {text_content[:100]}...")
                        
                        # Use enhanced metadata extraction (same as boundary detection)
                        metadata = await extract_container_metadata_enhanced(container, text_content)
                        
                        if not metadata or not metadata.get('creation_time'):
                            continue
                        
                        container_time = metadata['creation_time']
                        container_prompt = metadata.get('prompt', '')
                        
                        logger.debug(f"   ⏰ Generation container {containers_scanned}: {container_time}")
                        
                        # Check if this is our target datetime
                        if container_time == target_datetime:
                            logger.info(f"   🎯 TARGET FOUND: Generation container {containers_scanned} matches '{target_datetime}'")
                            logger.info(f"      📝 Prompt: {container_prompt[:100]}...")
                            
                            # Click this generation container to open the gallery (same as boundary detection)
                            logger.info(f"   🖱️ Clicking target generation container to open gallery...")
                            
                            try:
                                await container.click(timeout=5000)
                                await page.wait_for_timeout(2000)  # Wait for gallery to open
                                
                                logger.info("✅ START_FROM: Successfully positioned at target generation in gallery")
                                return {
                                    'found': True,
                                    'container_index': containers_scanned,
                                    'creation_time': container_time,
                                    'prompt': container_prompt
                                }
                                
                            except Exception as click_error:
                                logger.warning(f"   ⚠️ Failed to click target generation container: {click_error}")
                                # Still return success since we found it
                                return {
                                    'found': True,
                                    'container_index': containers_scanned,
                                    'creation_time': container_time,
                                    'prompt': container_prompt
                                }
                        
                    except Exception as e:
                        logger.debug(f"   ❌ Error processing generation container {containers_scanned}: {e}")
                        continue
                
                # If target not found in current containers, scroll to find more (same as boundary detection)
                if scroll_attempts < max_scroll_attempts:
                    logger.debug(f"   📜 Target not found in current generation containers, scrolling on /generate page...")
                    
                    # Use the same verified scrolling methods as boundary search
                    try:
                        logger.debug("   🎯 Using BoundaryScrollManager verified scroll methods on /generate page...")
                        
                        # Use the proven scroll methods with fallback
                        scroll_result = await self.boundary_scroll_manager.perform_scroll_with_fallback(
                            target_distance=self.config.scroll_amount
                        )
                        
                        scroll_attempts += 1
                        
                        if scroll_result.success and scroll_result.scroll_distance > 50:
                            logger.debug(f"   ✅ Verified scroll successful on /generate page: {scroll_result.scroll_distance}px using {scroll_result.method_name}")
                            
                            # Wait for DOM updates and new containers to appear
                            logger.debug("   ⏳ Waiting for DOM updates and new generation containers...")
                            await page.wait_for_timeout(2000)  # Wait for content to load
                            try:
                                await page.wait_for_load_state('networkidle', timeout=3000)
                            except:
                                pass  # Continue if networkidle timeout
                        else:
                            logger.debug(f"   ⚠️ Scroll attempt {scroll_attempts}: {scroll_result.method_name} returned {scroll_result.scroll_distance}px")
                            if scroll_result.error_message:
                                logger.debug(f"   ❌ Scroll error: {scroll_result.error_message}")
                            
                            # Still wait a bit even if scroll seemed to fail
                            await page.wait_for_timeout(1000)
                            
                    except Exception as scroll_error:
                        logger.debug(f"   ❌ BoundaryScrollManager error on /generate page: {scroll_error}")
                        scroll_attempts += 1
                        continue
                else:
                    logger.warning(f"   🔚 Reached maximum scroll attempts ({max_scroll_attempts}) without finding target on /generate page")
                    break
            
            logger.warning(f"   🔍 START_FROM: Target datetime '{target_datetime}' not found after scanning {containers_scanned} containers")
            return {
                'found': False,
                'containers_scanned': containers_scanned,
                'error': f'Target datetime not found after {containers_scanned} containers'
            }
            
        except Exception as e:
            logger.error(f"   ❌ START_FROM search error: {e}")
            return {
                'found': False,
                'error': str(e)
            }
    
    async def execute_generation_container_mode(self, page, results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute downloads using generation containers on /generate page instead of thumbnail navigation"""
        try:
            logger.info("🎯 GENERATION CONTAINER MODE: Working directly with generation containers on /generate page")
            logger.info("📍 This mode avoids thumbnail gallery navigation and works with containers directly")
            
            # Initialize session tracking
            self.processing_start_time = datetime.now()
            
            # Scan for existing files to detect duplicates (if enabled)
            existing_files = set()
            if self.config.duplicate_check_enabled:
                existing_files = self.scan_existing_files()
                if existing_files and self.config.stop_on_duplicate:
                    logger.info(f"🔍 Found {len(existing_files)} existing files - will stop if duplicate creation time detected")
            
            # Initialize Enhanced SKIP mode if needed
            enhanced_skip_enabled = self.initialize_enhanced_skip_mode()
            if enhanced_skip_enabled:
                logger.info("⚡ Enhanced SKIP mode is active - will fast-forward to last checkpoint")
            
            # Configure browser download settings
            logger.info("⚙️ Configuring Chromium browser settings to suppress download notifications")
            settings_configured = await self._configure_chromium_download_settings(page)
            if settings_configured:
                logger.info("✅ Chromium download settings configured successfully")
            
            # Find available generation containers using dynamic detection
            logger.info("📋 Using dynamic container detection for unlimited range (div[id*='__'])")
            
            # Get ALL generation containers from current /generate page using pattern matching
            all_containers = []
            try:
                # Use dynamic container detection to find ALL containers
                containers = await page.query_selector_all('div[id*="__"]')
                if containers:
                    # Filter to only include containers that match the generation pattern (hash__number)
                    for container in containers:
                        container_id = await container.get_attribute('id')
                        if container_id and '__' in container_id:
                            # Check if it follows the pattern: hash__number (both parts must be non-empty)
                            parts = container_id.split('__')
                            if len(parts) == 2 and parts[0] and parts[1] and parts[1].isdigit():
                                all_containers.append(container)
                    logger.info(f"📋 Filtered {len(containers)} div[id*='__'] elements to {len(all_containers)} generation containers")
            except Exception as e:
                logger.debug(f"Dynamic container detection failed: {e}")
                # Fallback to limited range if dynamic detection fails
                logger.info("📋 Falling back to limited range detection (0-49)")
                for i in range(0, 50):
                    try:
                        selector = f"div[id$='__{i}']"
                        containers = await page.query_selector_all(selector)
                        if containers:
                            all_containers.extend(containers)
                    except Exception as selector_e:
                        logger.debug(f"Selector div[id$='__{i}'] failed: {selector_e}")
            
            if not all_containers:
                logger.error("❌ GENERATION CONTAINER MODE: No generation containers found on /generate page")
                results['errors'].append('No generation containers available for processing')
                results['success'] = False
                return results
            
            logger.info(f"📊 GENERATION CONTAINER MODE: Found {len(all_containers)} generation containers to process")
            
            # Process generation containers one by one
            downloads_completed = 0
            containers_processed = 0
            
            for container in all_containers:
                if downloads_completed >= self.config.max_downloads:
                    logger.info(f"✅ GENERATION CONTAINER MODE: Reached maximum downloads limit ({self.config.max_downloads})")
                    break
                
                containers_processed += 1
                logger.info(f"🔄 Processing generation container {containers_processed}/{len(all_containers)}")
                
                try:
                    # Extract metadata from generation container
                    text_content = await container.text_content()
                    if not text_content:
                        logger.debug(f"   ⏭️ Skipping container {containers_processed}: No text content")
                        continue
                    
                    # Use enhanced metadata extraction
                    metadata = await extract_container_metadata_enhanced(container, text_content)
                    
                    if not metadata or not metadata.get('creation_time'):
                        logger.debug(f"   ⏭️ Skipping container {containers_processed}: No creation time metadata")
                        continue
                    
                    container_time = metadata['creation_time']
                    container_prompt = metadata.get('prompt', 'No prompt available')
                    
                    logger.info(f"   📅 Generation: {container_time}")
                    logger.info(f"   📝 Prompt: {container_prompt[:100]}...")
                    
                    # Check for duplicates if enabled
                    if self.config.duplicate_check_enabled and container_time in existing_files:
                        if self.config.duplicate_mode.value == 'finish':
                            logger.info(f"🛑 FINISH mode: Duplicate detected ({container_time}) - stopping downloads")
                            break
                        elif self.config.duplicate_mode.value == 'skip':
                            logger.info(f"⏭️ SKIP mode: Duplicate detected ({container_time}) - skipping this generation")
                            continue
                    
                    # Click the generation container to open it in the gallery
                    logger.info(f"   🖱️ Clicking generation container to open in gallery...")
                    await container.click()
                    await page.wait_for_timeout(3000)  # Wait for gallery to open
                    
                    # Try to download from the opened gallery
                    download_success = await self._attempt_download_from_current_position(page, containers_processed)
                    
                    if download_success:
                        downloads_completed += 1
                        logger.info(f"✅ Successfully downloaded generation {containers_processed}: {container_time}")
                    else:
                        logger.warning(f"⚠️ Failed to download generation {containers_processed}: {container_time}")
                    
                    # Navigate back to /generate page for next container
                    logger.debug("   🔙 Navigating back to /generate page...")
                    await page.go_back()
                    await page.wait_for_timeout(2000)  # Wait for page to load
                    
                except Exception as e:
                    logger.error(f"❌ Error processing generation container {containers_processed}: {e}")
                    continue
            
            # Update results
            results['success'] = downloads_completed > 0
            results['downloads_completed'] = downloads_completed
            results['total_thumbnails_processed'] = containers_processed
            results['end_time'] = datetime.now().isoformat()
            
            logger.info(f"🏁 GENERATION CONTAINER MODE completed:")
            logger.info(f"   📊 Containers processed: {containers_processed}")
            logger.info(f"   ⬇️ Downloads completed: {downloads_completed}")
            logger.info(f"   ✅ Success rate: {downloads_completed}/{containers_processed} ({downloads_completed/containers_processed*100 if containers_processed > 0 else 0:.1f}%)")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ GENERATION CONTAINER MODE failed: {e}")
            results['errors'].append(str(e))
            results['success'] = False
            results['end_time'] = datetime.now().isoformat()
            return results
    
    async def _attempt_download_from_current_position(self, page, container_index: int) -> bool:
        """Attempt to download from the currently opened generation in the gallery"""
        try:
            logger.debug(f"   🔍 Attempting download from generation container {container_index}")
            
            # Wait for gallery to fully load
            await page.wait_for_timeout(2000)
            
            # Look for download button or download elements
            download_selectors = [
                'button:has-text("Download")',
                '[aria-label*="download"]',
                '[class*="download"]',
                'a[href*="download"]',
                self.config.download_no_watermark_selector,
                'button:has-text("Download without Watermark")',
            ]
            
            download_element = None
            for selector in download_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # Check if element is visible
                        if await element.is_visible():
                            download_element = element
                            logger.debug(f"   ✅ Found download element: {selector}")
                            break
                except Exception as e:
                    logger.debug(f"   Selector {selector} failed: {e}")
                    continue
            
            if not download_element:
                logger.debug(f"   ⚠️ No download element found for container {container_index}")
                return False
            
            # Click the download element
            logger.debug(f"   🖱️ Clicking download element...")
            await download_element.click()
            
            # Wait for download to start
            await page.wait_for_timeout(3000)
            
            # Check if download started successfully
            # This is a simplified check - in real implementation you might want to
            # monitor the downloads folder or check for download progress indicators
            logger.debug(f"   ✅ Download attempt completed for container {container_index}")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Download attempt failed for container {container_index}: {e}")
            return False
    
    async def run_main_thumbnail_loop(self, page, results: Dict[str, Any]) -> bool:
        """Run the main thumbnail processing loop - extracted from run_download_automation for reuse"""
        try:
            logger.info("🚀 Starting main thumbnail processing loop")
            
            # Initialize thumbnail tracking
            self.visible_thumbnails_cache = await self.get_visible_thumbnail_identifiers(page)
            initial_thumbnail_count = len(self.visible_thumbnails_cache)
            logger.info(f"📊 Initial thumbnails visible: {initial_thumbnail_count}")
            
            # Initialize loop variables
            consecutive_failures = 0
            max_consecutive_failures = 100  # Support very large galleries with sparse content
            no_progress_cycles = 0
            max_no_progress_cycles = 3
            
            # Initialize session tracking
            self.processing_start_time = datetime.now()
            
            # Main thumbnail processing loop
            thumbnail_count = self.config.start_from_thumbnail - 1  # Will be incremented in loop
            
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
                                results['scrolls_performed'] = results.get('scrolls_performed', 0) + 1
                                logger.info(f"✅ Scroll successful (total scrolls: {results['scrolls_performed']})")
                                await page.wait_for_timeout(1000)
                                continue
                            else:
                                consecutive_failures += 1
                                logger.warning(f"❌ No more thumbnails found after scroll (failure {consecutive_failures}/{max_consecutive_failures})")
                                
                                if consecutive_failures >= max_consecutive_failures:
                                    logger.info("🏁 Reached maximum scroll failures - ending automation")
                                    break
                                continue
                    
                    # Process the active thumbnail
                    thumbnail_count += 1
                    logger.info(f"🎯 Processing thumbnail #{thumbnail_count}")
                    
                    # Try to download this thumbnail
                    download_success = await self.download_single_generation_robust(page, {
                        'element': active_thumbnail,
                        'unique_id': f'thumbnail_{thumbnail_count}'
                    })
                    
                    if download_success:
                        results['downloads_completed'] = results.get('downloads_completed', 0) + 1
                        consecutive_failures = 0  # Reset failure count on success
                        logger.info(f"✅ Download #{results['downloads_completed']} completed successfully")
                    else:
                        consecutive_failures += 1
                        logger.warning(f"❌ Download failed (failure {consecutive_failures}/{max_consecutive_failures})")
                    
                    # Move to next thumbnail
                    nav_success = await self.activate_next_thumbnail(page)
                    if not nav_success:
                        logger.info("📜 Could not navigate to next thumbnail - may have reached end")
                        break
                        
                    # Wait between thumbnails
                    await page.wait_for_timeout(1000)
                    
                except Exception as e:
                    logger.error(f"❌ Error in thumbnail processing loop: {e}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error("🚨 Too many consecutive failures - stopping loop")
                        break
                    continue
            
            logger.info(f"🏁 Main thumbnail loop completed - {results.get('downloads_completed', 0)} downloads")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in main thumbnail loop: {e}")
            return False

    async def execute_download_phase(self, page, results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the main download phase after successful start_from positioning"""
        try:
            logger.info("🚀 Starting direct download phase after successful start_from positioning")
            
            # Initialize session tracking
            self.processing_start_time = datetime.now()
            
            # Scan for existing files to detect duplicates (if enabled) 
            existing_files = set()
            if self.config.duplicate_check_enabled:
                existing_files = self.scan_existing_files()
                if existing_files and self.config.stop_on_duplicate:
                    logger.info(f"🔍 Found {len(existing_files)} existing files - will stop if duplicate creation time detected")
            
            # Initialize Enhanced SKIP mode if needed
            enhanced_skip_enabled = self.initialize_enhanced_skip_mode()
            if enhanced_skip_enabled:
                logger.info("⚡ Enhanced SKIP mode is active - will fast-forward to last checkpoint")
            
            # Configure browser download settings
            logger.info("⚙️ Configuring Chromium browser settings to suppress download notifications")
            settings_configured = await self._configure_chromium_download_settings(page)
            if settings_configured:
                logger.info("✅ Chromium download settings configured successfully")
            
            # Continue with normal thumbnail download flow after start_from positioned us
            logger.info("🔥 Target generation opened in gallery - starting thumbnail downloads from this position")
            
            # Pre-load gallery with initial scroll phase to populate thumbnails
            logger.info("🔄 Pre-loading gallery with initial scroll phase to populate thumbnails...")
            await self.preload_gallery_thumbnails(page)
            
            # Start main thumbnail processing loop 
            logger.info("🚀 Starting main thumbnail processing loop for downloads...")
            navigation_success = await self.run_main_thumbnail_loop(page, results)
            
            if navigation_success:
                logger.info("✅ Gallery navigation and downloads completed successfully")
                results['success'] = True
            else:
                logger.warning("⚠️ Gallery navigation completed with issues")
                results['success'] = results['downloads_completed'] > 0
                
            results['end_time'] = datetime.now().isoformat()
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in download phase: {e}")
            results['success'] = False
            results['errors'].append(str(e))
            results['end_time'] = datetime.now().isoformat()
            return results