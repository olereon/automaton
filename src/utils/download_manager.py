#!/usr/bin/env python3
"""
Download Manager for Web Automation

This module provides comprehensive download management for automated web tasks,
including proper file handling, path management, and download monitoring.
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import aiofiles
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class DownloadConfig:
    """Configuration for download management"""
    base_download_path: str = "/home/olereon/workspace/github.com/olereon/automaton/downloads/vids"
    organize_by_date: bool = True
    organize_by_type: bool = False
    max_wait_time: int = 300  # 5 minutes max wait
    check_interval: int = 1   # Check every second
    auto_rename_duplicates: bool = True
    verify_downloads: bool = True
    create_download_log: bool = True


@dataclass
class DownloadInfo:
    """Information about a download"""
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    download_time: datetime
    source_url: str
    mime_type: str = None
    checksum: str = None
    status: str = "pending"  # pending, downloading, completed, failed


class DownloadManager:
    """Manages automated downloads with proper file handling"""
    
    def __init__(self, config: DownloadConfig = None):
        self.config = config or DownloadConfig()
        self.downloads: List[DownloadInfo] = []
        self.download_callbacks: Dict[str, Callable] = {}
        
        # Ensure download directory exists
        self._setup_download_directory()
    
    def _setup_download_directory(self):
        """Setup the download directory structure"""
        base_path = Path(self.config.base_download_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories if needed
        if self.config.organize_by_date:
            today = datetime.now().strftime("%Y-%m-%d")
            date_path = base_path / today
            date_path.mkdir(exist_ok=True)
        
        if self.config.organize_by_type:
            type_dirs = ["videos", "images", "documents", "archives", "other"]
            for type_dir in type_dirs:
                (base_path / type_dir).mkdir(exist_ok=True)
        
        logger.info(f"Download directory setup complete: {base_path}")
    
    def get_download_path(self, filename: str, mime_type: str = None) -> Path:
        """Get the appropriate download path for a file"""
        base_path = Path(self.config.base_download_path)
        
        # Add date organization
        if self.config.organize_by_date:
            today = datetime.now().strftime("%Y-%m-%d")
            base_path = base_path / today
        
        # Add type organization
        if self.config.organize_by_type and mime_type:
            type_folder = self._get_type_folder(filename, mime_type)
            base_path = base_path / type_folder
        
        # Ensure directory exists
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Handle duplicate filenames
        final_path = base_path / filename
        if self.config.auto_rename_duplicates and final_path.exists():
            final_path = self._get_unique_filename(final_path)
        
        return final_path
    
    def _get_type_folder(self, filename: str, mime_type: str) -> str:
        """Determine the appropriate type folder for a file"""
        filename_lower = filename.lower()
        
        # Video files
        if any(ext in filename_lower for ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']) or \
           'video' in mime_type:
            return "videos"
        
        # Image files
        if any(ext in filename_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']) or \
           'image' in mime_type:
            return "images"
        
        # Document files
        if any(ext in filename_lower for ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']) or \
           'document' in mime_type or 'text' in mime_type:
            return "documents"
        
        # Archive files
        if any(ext in filename_lower for ext in ['.zip', '.rar', '.7z', '.tar', '.gz']) or \
           'archive' in mime_type or 'compressed' in mime_type:
            return "archives"
        
        return "other"
    
    def _get_unique_filename(self, filepath: Path) -> Path:
        """Generate a unique filename by adding a counter"""
        base = filepath.stem
        extension = filepath.suffix
        parent = filepath.parent
        counter = 1
        
        while True:
            new_name = f"{base}_{counter}{extension}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    async def handle_playwright_download(self, page, download_trigger_selector: str, 
                                       expected_filename: str = None, 
                                       timeout: int = None) -> DownloadInfo:
        """Handle download using Playwright's download API"""
        timeout = timeout or self.config.max_wait_time * 1000  # Convert to milliseconds
        
        logger.info(f"Starting download by clicking: {download_trigger_selector}")
        
        try:
            # Set up download expectation
            async with page.expect_download(timeout=timeout) as download_info:
                # Trigger the download
                await page.click(download_trigger_selector)
            
            download = await download_info.value
            
            # Get download information
            suggested_filename = download.suggested_filename
            actual_filename = expected_filename or suggested_filename
            
            if not actual_filename:
                actual_filename = f"download_{int(time.time())}"
            
            # Determine download path
            download_path = self.get_download_path(actual_filename)
            
            logger.info(f"Saving download to: {download_path}")
            
            # Save the download
            await download.save_as(str(download_path))
            
            # Create download info
            download_info_obj = DownloadInfo(
                filename=download_path.name,
                original_filename=suggested_filename,
                file_path=str(download_path),
                file_size=download_path.stat().st_size if download_path.exists() else 0,
                download_time=datetime.now(),
                source_url=page.url,
                status="completed"
            )
            
            # Verify download if enabled
            if self.config.verify_downloads:
                await self._verify_download(download_info_obj)
            
            # Add to downloads list
            self.downloads.append(download_info_obj)
            
            # Log download if enabled
            if self.config.create_download_log:
                await self._log_download(download_info_obj)
            
            logger.info(f"Download completed successfully: {download_path}")
            return download_info_obj
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            # Create failed download info
            failed_download = DownloadInfo(
                filename=expected_filename or "unknown",
                original_filename=expected_filename or "unknown",
                file_path="",
                file_size=0,
                download_time=datetime.now(),
                source_url=page.url,
                status="failed"
            )
            self.downloads.append(failed_download)
            raise
    
    async def handle_direct_download(self, page, download_url: str, 
                                   filename: str = None) -> DownloadInfo:
        """Handle direct download from a URL"""
        logger.info(f"Starting direct download from: {download_url}")
        
        try:
            # Navigate to download URL or use fetch
            response = await page.goto(download_url)
            
            if not filename:
                # Extract filename from URL or response headers
                filename = self._extract_filename_from_url(download_url)
                if not filename:
                    content_disposition = response.headers.get('content-disposition', '')
                    filename = self._extract_filename_from_header(content_disposition)
                if not filename:
                    filename = f"download_{int(time.time())}"
            
            # Get content
            content = await response.body()
            
            # Determine download path
            download_path = self.get_download_path(filename)
            
            # Save content
            async with aiofiles.open(download_path, 'wb') as f:
                await f.write(content)
            
            # Create download info
            download_info_obj = DownloadInfo(
                filename=download_path.name,
                original_filename=filename,
                file_path=str(download_path),
                file_size=len(content),
                download_time=datetime.now(),
                source_url=download_url,
                mime_type=response.headers.get('content-type', ''),
                status="completed"
            )
            
            # Verify download if enabled
            if self.config.verify_downloads:
                await self._verify_download(download_info_obj)
            
            # Add to downloads list
            self.downloads.append(download_info_obj)
            
            # Log download if enabled
            if self.config.create_download_log:
                await self._log_download(download_info_obj)
            
            logger.info(f"Direct download completed: {download_path}")
            return download_info_obj
            
        except Exception as e:
            logger.error(f"Direct download failed: {e}")
            raise
    
    async def wait_for_download_completion(self, download_path: Path, 
                                         max_wait: int = None) -> bool:
        """Wait for a download to complete by monitoring file changes"""
        max_wait = max_wait or self.config.max_wait_time
        start_time = time.time()
        last_size = -1
        stable_count = 0
        
        logger.info(f"Waiting for download completion: {download_path}")
        
        while time.time() - start_time < max_wait:
            if download_path.exists():
                current_size = download_path.stat().st_size
                
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    # File size hasn't changed for 3 consecutive checks
                    if stable_count >= 3:
                        logger.info(f"Download completed: {download_path} ({current_size} bytes)")
                        return True
                else:
                    stable_count = 0
                    last_size = current_size
                    logger.debug(f"Download in progress: {current_size} bytes")
            
            await asyncio.sleep(self.config.check_interval)
        
        logger.warning(f"Download timeout after {max_wait} seconds")
        return False
    
    def _extract_filename_from_url(self, url: str) -> str:
        """Extract filename from URL"""
        try:
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            filename = Path(unquote(parsed.path)).name
            return filename if filename and '.' in filename else None
        except:
            return None
    
    def _extract_filename_from_header(self, content_disposition: str) -> str:
        """Extract filename from Content-Disposition header"""
        try:
            if 'filename=' in content_disposition:
                filename_part = content_disposition.split('filename=')[1]
                filename = filename_part.strip().strip('"').strip("'")
                return filename
        except:
            pass
        return None
    
    async def _verify_download(self, download_info: DownloadInfo):
        """Verify download integrity"""
        try:
            filepath = Path(download_info.file_path)
            if not filepath.exists():
                download_info.status = "failed"
                return
            
            # Check file size
            actual_size = filepath.stat().st_size
            download_info.file_size = actual_size
            
            if actual_size == 0:
                download_info.status = "failed"
                logger.warning(f"Downloaded file is empty: {filepath}")
                return
            
            # Calculate checksum
            if self.config.verify_downloads:
                checksum = await self._calculate_checksum(filepath)
                download_info.checksum = checksum
            
            download_info.status = "completed"
            logger.info(f"Download verified: {filepath} ({actual_size} bytes)")
            
        except Exception as e:
            logger.error(f"Download verification failed: {e}")
            download_info.status = "failed"
    
    async def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file"""
        try:
            hash_sha256 = hashlib.sha256()
            async with aiofiles.open(filepath, 'rb') as f:
                async for chunk in f:
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Checksum calculation failed: {e}")
            return ""
    
    async def _log_download(self, download_info: DownloadInfo):
        """Log download information to file"""
        try:
            log_file = Path(self.config.base_download_path) / "download_log.json"
            
            # Load existing log
            downloads_log = []
            if log_file.exists():
                async with aiofiles.open(log_file, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        downloads_log = json.loads(content)
            
            # Add new download
            download_dict = {
                "filename": download_info.filename,
                "original_filename": download_info.original_filename,
                "file_path": download_info.file_path,
                "file_size": download_info.file_size,
                "download_time": download_info.download_time.isoformat(),
                "source_url": download_info.source_url,
                "mime_type": download_info.mime_type,
                "checksum": download_info.checksum,
                "status": download_info.status
            }
            downloads_log.append(download_dict)
            
            # Save updated log
            async with aiofiles.open(log_file, 'w') as f:
                await f.write(json.dumps(downloads_log, indent=2))
            
            logger.debug(f"Download logged to: {log_file}")
            
        except Exception as e:
            logger.error(f"Download logging failed: {e}")
    
    def get_downloads_summary(self) -> Dict[str, Any]:
        """Get summary of all downloads"""
        completed = [d for d in self.downloads if d.status == "completed"]
        failed = [d for d in self.downloads if d.status == "failed"]
        
        total_size = sum(d.file_size for d in completed)
        
        return {
            "total_downloads": len(self.downloads),
            "completed": len(completed),
            "failed": len(failed),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "download_directory": self.config.base_download_path,
            "downloads": [
                {
                    "filename": d.filename,
                    "file_path": d.file_path,
                    "size_mb": round(d.file_size / (1024 * 1024), 2),
                    "status": d.status,
                    "download_time": d.download_time.isoformat()
                }
                for d in self.downloads
            ]
        }
    
    async def cleanup_failed_downloads(self):
        """Remove failed download files"""
        for download in self.downloads:
            if download.status == "failed" and download.file_path:
                try:
                    filepath = Path(download.file_path)
                    if filepath.exists() and filepath.stat().st_size == 0:
                        filepath.unlink()
                        logger.info(f"Removed failed download: {filepath}")
                except Exception as e:
                    logger.error(f"Failed to remove failed download: {e}")


# Factory function for easy usage
def create_download_manager(base_path: str = None, 
                          organize_by_date: bool = True,
                          organize_by_type: bool = False) -> DownloadManager:
    """Create a download manager with common configuration"""
    config = DownloadConfig(
        base_download_path=base_path or "/home/olereon/Downloads/automaton_vids",
        organize_by_date=organize_by_date,
        organize_by_type=organize_by_type
    )
    return DownloadManager(config)