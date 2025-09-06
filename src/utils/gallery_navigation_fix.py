"""
Gallery Navigation Fix - September 2025
Robust thumbnail selection and navigation with duplicate cycle prevention

Fixes:
1. Multi-thumbnail selection issue (only one active at a time)
2. Duplicate detection enhancement for identical content  
3. Forward progression without cycles
4. Clear state management
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Set, Tuple

logger = logging.getLogger(__name__)


class RobustGalleryNavigator:
    """Enhanced gallery navigation with cycle prevention and robust state management"""
    
    def __init__(self):
        self.processed_thumbnails: Set[str] = set()
        self.navigation_history: List[str] = []
        self.last_processed_metadata: Dict[str, Any] = {}
        self.cycle_detection_window = 5  # Detect cycles within last 5 thumbnails
        
    async def get_single_active_thumbnail(self, page) -> Optional[object]:
        """
        Get exactly ONE active thumbnail, ensuring no multi-selection
        
        Returns:
            The single active thumbnail element, or None if multiple/none found
        """
        try:
            # Find all potential active thumbnails
            active_thumbnails = await page.query_selector_all("div.thumsCou.active")
            
            if not active_thumbnails:
                logger.debug("🔍 No active thumbnails found")
                return None
                
            if len(active_thumbnails) == 1:
                # Perfect - exactly one active thumbnail
                thumbnail = active_thumbnails[0]
                class_attr = await thumbnail.get_attribute('class') or ''
                logger.debug(f"✅ Single active thumbnail found: {class_attr}")
                return thumbnail
            
            # PROBLEM: Multiple active thumbnails detected
            logger.warning(f"⚠️ MULTI-SELECTION DETECTED: {len(active_thumbnails)} active thumbnails found")
            
            # Clear all active states first
            await self._clear_all_active_states(page)
            
            # Wait a moment for state to settle
            await page.wait_for_timeout(500)
            
            # Find the "best" thumbnail to activate (first visible one)
            best_thumbnail = await self._find_best_thumbnail_to_activate(page, active_thumbnails)
            if best_thumbnail:
                await self._activate_single_thumbnail(page, best_thumbnail)
                return best_thumbnail
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting single active thumbnail: {e}")
            return None
    
    async def _clear_all_active_states(self, page):
        """Clear all active states by clicking elsewhere first"""
        try:
            # Click on an empty area to deselect all thumbnails
            await page.click('body', timeout=2000)
            await page.wait_for_timeout(200)
            
            # Verify all are deselected
            active_count = await page.evaluate("""
                () => document.querySelectorAll('div.thumsCou.active').length
            """)
            logger.debug(f"🧹 Cleared active states - remaining active: {active_count}")
            
        except Exception as e:
            logger.debug(f"Error clearing active states: {e}")
    
    async def _find_best_thumbnail_to_activate(self, page, candidates: List) -> Optional[object]:
        """Find the best thumbnail from candidates to activate"""
        try:
            for thumbnail in candidates:
                # Check visibility and position
                is_visible = await thumbnail.is_visible()
                if not is_visible:
                    continue
                    
                # Get position info
                bounding_box = await thumbnail.bounding_box()
                if not bounding_box:
                    continue
                
                # Prefer thumbnails in the upper portion (likely earlier in sequence)
                class_attr = await thumbnail.get_attribute('class') or ''
                logger.debug(f"📍 Candidate thumbnail: {class_attr}, y={bounding_box['y']}")
                
                # Use first visible candidate for now
                return thumbnail
                
            return None
            
        except Exception as e:
            logger.error(f"Error finding best thumbnail: {e}")
            return None
    
    async def _activate_single_thumbnail(self, page, thumbnail) -> bool:
        """Activate a single thumbnail ensuring clean state"""
        try:
            # Get thumbnail identifier for tracking
            thumbnail_id = await self._get_thumbnail_identifier(thumbnail)
            
            # Click to activate
            await thumbnail.click(timeout=3000)
            await page.wait_for_timeout(300)
            
            # Verify it's now the only active one
            active_count = await page.evaluate("""
                () => document.querySelectorAll('div.thumsCou.active').length
            """)
            
            if active_count == 1:
                logger.info(f"✅ Successfully activated single thumbnail: {thumbnail_id}")
                return True
            else:
                logger.warning(f"⚠️ Activation resulted in {active_count} active thumbnails")
                return False
                
        except Exception as e:
            logger.error(f"Error activating single thumbnail: {e}")
            return False
    
    async def navigate_to_next_unprocessed_thumbnail(self, page) -> Tuple[bool, Optional[str]]:
        """
        Navigate to the next unprocessed thumbnail with cycle prevention
        
        Returns:
            Tuple of (success, thumbnail_id)
        """
        try:
            # Get current active thumbnail
            current_active = await self.get_single_active_thumbnail(page)
            if not current_active:
                logger.error("❌ No single active thumbnail found for navigation")
                return False, None
            
            # Get current thumbnail identifier
            current_id = await self._get_thumbnail_identifier(current_active)
            
            # Check for cycles
            if self._detect_navigation_cycle(current_id):
                logger.error(f"🔄 CYCLE DETECTED: Thumbnail {current_id} creates cycle")
                return False, None
            
            # Find all available thumbnails
            all_thumbnails = await page.query_selector_all("div.thumsCou:not([class*='mask'])")
            logger.debug(f"📊 Found {len(all_thumbnails)} total thumbnails")
            
            # Find current position
            current_position = -1
            for i, thumb in enumerate(all_thumbnails):
                thumb_id = await self._get_thumbnail_identifier(thumb)
                if thumb_id == current_id:
                    current_position = i
                    break
            
            if current_position == -1:
                logger.error(f"❌ Could not find current position for {current_id}")
                return False, None
            
            logger.debug(f"📍 Current position: {current_position}/{len(all_thumbnails)}")
            
            # Find next unprocessed thumbnail
            next_thumbnail = None
            next_position = current_position + 1
            
            for i in range(next_position, len(all_thumbnails)):
                candidate = all_thumbnails[i]
                candidate_id = await self._get_thumbnail_identifier(candidate)
                
                if candidate_id not in self.processed_thumbnails:
                    next_thumbnail = candidate
                    next_position = i
                    logger.debug(f"🎯 Found unprocessed thumbnail at position {i}: {candidate_id}")
                    break
            
            if not next_thumbnail:
                logger.info("📜 No more unprocessed thumbnails found")
                return False, None
            
            # Clear current selection first
            await self._clear_all_active_states(page)
            
            # Activate the next thumbnail
            success = await self._activate_single_thumbnail(page, next_thumbnail)
            if success:
                next_id = await self._get_thumbnail_identifier(next_thumbnail)
                self.navigation_history.append(next_id)
                logger.info(f"✅ Successfully navigated to thumbnail {next_position}: {next_id}")
                return True, next_id
            else:
                logger.error(f"❌ Failed to activate next thumbnail at position {next_position}")
                return False, None
                
        except Exception as e:
            logger.error(f"Error navigating to next thumbnail: {e}")
            return False, None
    
    def _detect_navigation_cycle(self, thumbnail_id: str) -> bool:
        """Detect if navigating to this thumbnail would create a cycle"""
        if len(self.navigation_history) < 2:
            return False
        
        # Check if this ID appears in recent history
        recent_history = self.navigation_history[-self.cycle_detection_window:]
        cycle_count = recent_history.count(thumbnail_id)
        
        if cycle_count > 0:
            logger.warning(f"⚠️ Thumbnail {thumbnail_id} appeared {cycle_count} times in recent history")
            return cycle_count >= 2  # Allow once, block twice
        
        return False
    
    async def _get_thumbnail_identifier(self, thumbnail) -> str:
        """Get a unique identifier for a thumbnail"""
        try:
            # Use position and class attributes as identifier
            class_attr = await thumbnail.get_attribute('class') or ''
            
            # Get position info
            bounding_box = await thumbnail.bounding_box()
            position_key = f"{int(bounding_box['y'])}" if bounding_box else "unknown"
            
            # Create composite identifier
            identifier = f"thumb_{position_key}_{hash(class_attr) % 10000}"
            return identifier
            
        except Exception as e:
            logger.error(f"Error getting thumbnail identifier: {e}")
            return f"thumb_error_{id(thumbnail)}"
    
    def mark_thumbnail_processed(self, thumbnail_id: str, metadata: Dict[str, Any]):
        """Mark a thumbnail as processed to avoid re-processing"""
        self.processed_thumbnails.add(thumbnail_id)
        self.last_processed_metadata[thumbnail_id] = metadata
        logger.debug(f"📝 Marked thumbnail {thumbnail_id} as processed")
    
    def is_content_duplicate(self, current_metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Enhanced duplicate detection using content comparison
        
        Returns:
            Tuple of (is_duplicate, reason)
        """
        if not current_metadata:
            return False, "No metadata to compare"
        
        current_date = current_metadata.get('generation_date', '')
        current_prompt = current_metadata.get('prompt', '')
        
        if not current_date or not current_prompt:
            return False, "Incomplete metadata"
        
        # Check against recently processed thumbnails
        for thumb_id, prev_metadata in self.last_processed_metadata.items():
            prev_date = prev_metadata.get('generation_date', '')
            prev_prompt = prev_metadata.get('prompt', '')
            
            # Exact date + prompt match = duplicate
            if current_date == prev_date and current_prompt == prev_prompt:
                return True, f"Exact match with {thumb_id}"
            
            # Similar prompt (90%+ match) + same date = likely duplicate
            if current_date == prev_date and self._calculate_text_similarity(current_prompt, prev_prompt) > 0.9:
                return True, f"High similarity with {thumb_id}"
        
        return False, "No duplicates found"
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity between two strings"""
        if not text1 or not text2:
            return 0.0
        
        # Simple character-based similarity
        len1, len2 = len(text1), len(text2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
        
        # Count matching characters in order
        matches = 0
        min_len = min(len1, len2)
        
        for i in range(min_len):
            if text1[i] == text2[i]:
                matches += 1
        
        similarity = matches / max_len
        return similarity
    
    def get_navigation_stats(self) -> Dict[str, Any]:
        """Get navigation statistics"""
        return {
            'total_processed': len(self.processed_thumbnails),
            'navigation_history_length': len(self.navigation_history),
            'recent_history': self.navigation_history[-5:] if self.navigation_history else [],
            'cycle_detection_active': True,
            'processed_thumbnails': list(self.processed_thumbnails)
        }
    
    def reset_navigation_state(self):
        """Reset navigation state for new session"""
        self.processed_thumbnails.clear()
        self.navigation_history.clear()
        self.last_processed_metadata.clear()
        logger.info("🔄 Navigation state reset for new session")


# Global instance
gallery_navigator = RobustGalleryNavigator()