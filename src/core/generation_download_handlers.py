#!/usr/bin/env python3
"""
Generation Download Action Handlers
Handlers for generation download automation actions in the WebAutomationEngine.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class GenerationDownloadHandlers:
    """Mixin class providing generation download action handlers"""
    
    def __init_generation_downloads__(self):
        """Initialize generation download system"""
        self._generation_download_manager = None
        self._generation_downloads_active = False
        
    async def _handle_start_generation_downloads(self, action) -> Dict[str, Any]:
        """Handle START_GENERATION_DOWNLOADS action"""
        try:
            from ..utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig
            
            # Parse configuration from action value
            config_data = action.value if action.value else {}
            
            # Create configuration with defaults and user overrides
            config = GenerationDownloadConfig(
                downloads_folder=config_data.get('downloads_folder', '/home/olereon/workspace/github.com/olereon/automaton/downloads/vids'),
                logs_folder=config_data.get('logs_folder', '/home/olereon/workspace/github.com/olereon/automaton/logs'),
                max_downloads=config_data.get('max_downloads', 50),
                download_timeout=config_data.get('download_timeout', 120000),
                verification_timeout=config_data.get('verification_timeout', 30000),
                retry_attempts=config_data.get('retry_attempts', 3),
                # Update selectors if provided
                completed_task_selector=config_data.get('completed_task_selector', "div[id$='__8']"),
                thumbnail_selector=config_data.get('thumbnail_selector', '.thumbnail-item'),
                
                # Enhanced selector configuration
                button_panel_selector=config_data.get('button_panel_selector', '.sc-eYHxxX.fmURBt'),
                download_icon_href=config_data.get('download_icon_href', '#icon-icon_tongyong_20px_xiazai'),
                download_button_index=config_data.get('download_button_index', 2),
                download_no_watermark_text=config_data.get('download_no_watermark_text', 'Download without Watermark'),
                
                # Legacy and CSS selectors
                download_button_selector=config_data.get('download_button_selector', 
                    "[data-spm-anchor-id='a2ty_o02.30365920.0.i1.6daf47258YB5qi']"),
                download_no_watermark_selector=config_data.get('download_no_watermark_selector',
                    ".sc-fbUgXY.hMAwvg"),  # Updated default to the new selector
                generation_date_selector=config_data.get('generation_date_selector', 
                    '.sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)'),
                prompt_selector=config_data.get('prompt_selector', 
                    '.sc-jJRqov.cxtNJi span[aria-describedby]')
            )
            
            # Initialize the generation download manager
            self._generation_download_manager = GenerationDownloadManager(config)
            self._generation_downloads_active = True
            
            logger.info("Generation download manager initialized")
            logger.info(f"Max downloads: {config.max_downloads}")
            logger.info(f"Downloads folder: {config.downloads_folder}")
            logger.info(f"Logs folder: {config.logs_folder}")
            
            # Configure browser downloads to go to our directory
            try:
                # Set up download path in browser context
                context = self.page.context
                await context.route("**", lambda route: route.continue_())
                logger.debug(f"Browser download path configured to: {config.downloads_folder}")
            except Exception as e:
                logger.warning(f"Could not configure browser download path: {e}")
            
            # Start the download automation
            results = await self._generation_download_manager.run_download_automation(self.page)
            
            # Mark as inactive when complete
            self._generation_downloads_active = False
            
            return {
                'success': results['success'],
                'downloads_completed': results['downloads_completed'],
                'errors': results['errors'],
                'start_time': results['start_time'],
                'end_time': results['end_time'],
                'manager_status': self._generation_download_manager.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error in start_generation_downloads: {e}")
            self._generation_downloads_active = False
            return {
                'success': False,
                'error': str(e),
                'downloads_completed': 0
            }
    
    async def _handle_stop_generation_downloads(self, action) -> Dict[str, Any]:
        """Handle STOP_GENERATION_DOWNLOADS action"""
        try:
            if not self._generation_download_manager:
                logger.warning("No generation download manager active to stop")
                return {
                    'success': False,
                    'message': 'No active generation download process',
                    'was_active': False
                }
            
            # Request stop
            self._generation_download_manager.request_stop()
            self._generation_downloads_active = False
            
            logger.info("Generation downloads stop requested")
            
            # Get final status
            status = self._generation_download_manager.get_status()
            
            return {
                'success': True,
                'message': 'Generation downloads stopped',
                'was_active': True,
                'final_status': status
            }
            
        except Exception as e:
            logger.error(f"Error stopping generation downloads: {e}")
            return {
                'success': False,
                'error': str(e),
                'was_active': self._generation_downloads_active
            }
    
    async def _handle_check_generation_status(self, action) -> Dict[str, Any]:
        """Handle CHECK_GENERATION_STATUS action"""
        try:
            if not self._generation_download_manager:
                return {
                    'success': True,
                    'active': False,
                    'message': 'No generation download manager initialized'
                }
            
            status = self._generation_download_manager.get_status()
            
            return {
                'success': True,
                'active': self._generation_downloads_active,
                'status': status,
                'message': f"Downloads completed: {status['downloads_completed']}/{status['max_downloads']}"
            }
            
        except Exception as e:
            logger.error(f"Error checking generation status: {e}")
            return {
                'success': False,
                'error': str(e),
                'active': False
            }