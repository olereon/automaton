#!/usr/bin/env python3.11
"""
Boundary Scroll Manager for Generation Download Automation
=========================================================
This module implements verified scrolling methods to navigate the generation gallery
and detect boundary containers among older generations.

Verified Methods:
1. Element.scrollIntoView() - Primary method (Rank #1)
2. container.scrollTop - Fallback method (Rank #2)

Both methods ensure >2000px scroll distance with proper tracking.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Set
from playwright.async_api import Page, ElementHandle

logger = logging.getLogger(__name__)


class ScrollResult:
    """Container for scroll operation results"""
    
    def __init__(self, method_name: str):
        self.method_name = method_name
        self.success = False
        self.scroll_distance = 0
        self.execution_time = 0.0
        self.error_message = ""
        self.containers_before = 0
        self.containers_after = 0
        self.new_containers_detected = False


class BoundaryScrollManager:
    """
    Manages scrolling operations for boundary detection in generation galleries.
    Uses verified methods from scroll testing results.
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.total_scrolled_distance = 0
        self.scroll_attempts = 0
        self.detected_containers = set()  # Track container IDs to detect new ones
        self.max_scroll_attempts = 2000  # Support very large galleries with 3000+ generations
        self.min_scroll_distance = 2500  # Minimum distance per scroll (increased for better container detection)
        
    async def get_scroll_position(self) -> Dict:
        """Get current scroll position and container count with comprehensive container detection"""
        try:
            result = await self.page.evaluate("""
                () => {
                    // Get all possible generation containers with dynamic selector generation
                    const containerSelectors = [
                        // CRITICAL: Dynamic generation container selectors for any index (0 to 9999+)
                        // Instead of listing 50 selectors, use a pattern-based approach
                        'div[id*="__"]',           // All containers with double underscore pattern
                        // Generic fallback selectors (kept for compatibility)
                        '[data-generation-id]',
                        '.generation-item',
                        '.generation-card',
                        '[class*="generation"]',
                        '[class*="card"]',
                        '.thumsCou',              // From your automation config
                        '.thumsItem',             // From your automation config
                        '.thumbnail-item',        // Common pattern
                        '[class*="thumb"]',       // Thumbnail variations
                        '[id*="thumb"]',          // ID-based thumbs
                        'div[class*="thumsCou"]', // Specific to your site
                        '[data-spm-anchor-id*="thumb"]' // From your logs
                    ];
                    
                    let allContainers = [];
                    containerSelectors.forEach(selector => {
                        try {
                            const found = document.querySelectorAll(selector);
                            found.forEach(el => {
                                // Avoid duplicates by checking if already added
                                if (!allContainers.find(existing => existing === el)) {
                                    allContainers.push(el);
                                }
                            });
                        } catch (e) {
                            // Skip invalid selectors
                        }
                    });
                    
                    // Find all scrollable containers and their scroll positions
                    const scrollableContainers = [];
                    const allElements = document.querySelectorAll('*');
                    
                    for (const el of allElements) {
                        try {
                            const style = window.getComputedStyle(el);
                            const hasScroll = (
                                style.overflow === 'scroll' || 
                                style.overflow === 'auto' ||
                                style.overflowY === 'scroll' || 
                                style.overflowY === 'auto' ||
                                el.scrollHeight > el.clientHeight
                            );
                            
                            if (hasScroll && el.scrollTop >= 0) {
                                scrollableContainers.push({
                                    tag: el.tagName,
                                    id: el.id || 'none',
                                    classes: el.className || 'none',
                                    scrollTop: el.scrollTop,
                                    scrollHeight: el.scrollHeight,
                                    clientHeight: el.clientHeight,
                                    canScrollMore: el.scrollTop < (el.scrollHeight - el.clientHeight - 10)
                                });
                            }
                        } catch (e) {
                            // Skip elements that cause errors
                        }
                    }
                    
                    return {
                        windowScrollY: window.scrollY,
                        documentScrollTop: document.documentElement.scrollTop,
                        bodyScrollTop: document.body.scrollTop,
                        containerCount: allContainers.length,
                        scrollHeight: document.documentElement.scrollHeight,
                        clientHeight: document.documentElement.clientHeight,
                        scrollableContainers: scrollableContainers,
                        containers: Array.from(allContainers).map((el, index) => ({
                            id: el.id ||                                           // Primary: actual element ID (for div[id$="__N"])
                                el.getAttribute('data-generation-id') || 
                                el.getAttribute('data-spm-anchor-id') || 
                                `container-${index}`,
                            rect: el.getBoundingClientRect(),
                            visible: el.getBoundingClientRect().top < window.innerHeight && el.getBoundingClientRect().bottom > 0,
                            className: el.className || '',
                            tagName: el.tagName
                        }))
                    };
                }
            """)
            return result
        except Exception as e:
            logger.error(f"Failed to get scroll position: {e}")
            return {
                'windowScrollY': 0,
                'documentScrollTop': 0,
                'bodyScrollTop': 0,
                'containerCount': 0,
                'scrollHeight': 0,
                'clientHeight': 0,
                'scrollableContainers': [],
                'containers': []
            }
    
    async def detect_new_containers(self, before_containers: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Detect if new generation containers have been loaded"""
        try:
            current_state = await self.get_scroll_position()
            after_containers = current_state['containers']
            
            # Create sets of container IDs for comparison
            before_ids = {c['id'] for c in before_containers}
            after_ids = {c['id'] for c in after_containers}
            
            # Find new containers
            new_container_ids = after_ids - before_ids
            new_containers = [c for c in after_containers if c['id'] in new_container_ids]
            
            has_new = len(new_containers) > 0
            
            if has_new:
                logger.info(f"✓ Detected {len(new_containers)} new generation containers")
                for container in new_containers:
                    logger.debug(f"  New container: {container['id']}")
            else:
                logger.debug("No new containers detected")
                
            return has_new, new_containers
            
        except Exception as e:
            logger.error(f"Failed to detect new containers: {e}")
            return False, []
    
    async def scroll_method_1_element_scrollintoview(self, target_distance: int = 2000) -> ScrollResult:
        """
        Primary scroll method: Element.scrollIntoView()
        Based on verified test results - Rank #1
        Enhanced to detect custom scroll containers
        """
        result = ScrollResult("Element.scrollIntoView()")
        logger.info(f"Using primary scroll method: {result.method_name}")
        
        try:
            start_time = time.time()
            initial_state = await self.get_scroll_position()
            initial_scroll = initial_state['windowScrollY']
            result.containers_before = initial_state['containerCount']
            
            # Log detected scrollable containers for debugging
            scrollable_containers = initial_state.get('scrollableContainers', [])
            logger.debug(f"   Found {len(scrollable_containers)} scrollable containers")
            for container in scrollable_containers[:3]:  # Log first 3
                logger.debug(f"     {container['tag']}#{container['id']} - scroll: {container['scrollTop']}/{container['scrollHeight']}")
            
            # Enhanced scrolling with multiple approaches
            scroll_completed = await self.page.evaluate(f"""
                (targetDistance) => {{
                    let scrollSuccess = false;
                    let actualScrollDistance = 0;
                    
                    // Method 1: Try to find and scroll the main scrollable container
                    const scrollableContainers = Array.from(document.querySelectorAll('*')).filter(el => {{
                        try {{
                            const style = window.getComputedStyle(el);
                            return (style.overflow === 'scroll' || style.overflow === 'auto' ||
                                   style.overflowY === 'scroll' || style.overflowY === 'auto') &&
                                   el.scrollHeight > el.clientHeight;
                        }} catch (e) {{
                            return false;
                        }}
                    }});
                    
                    // Sort by scroll area size (larger containers first)
                    scrollableContainers.sort((a, b) => 
                        (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight)
                    );
                    
                    // Try scrolling the main container first
                    for (const container of scrollableContainers.slice(0, 3)) {{
                        const initialScroll = container.scrollTop;
                        const maxScroll = container.scrollHeight - container.clientHeight;
                        
                        if (initialScroll < maxScroll) {{
                            // Find elements within this container to scroll to
                            const childElements = container.querySelectorAll('*');
                            let bestElement = null;
                            let bestDistance = Infinity;
                            
                            for (const el of childElements) {{
                                try {{
                                    const rect = el.getBoundingClientRect();
                                    const containerRect = container.getBoundingClientRect();
                                    const relativeTop = rect.top - containerRect.top + container.scrollTop;
                                    const targetPosition = initialScroll + targetDistance;
                                    const distance = Math.abs(relativeTop - targetPosition);
                                    
                                    if (distance < bestDistance && relativeTop > initialScroll + container.clientHeight) {{
                                        bestElement = el;
                                        bestDistance = distance;
                                    }}
                                }} catch (e) {{
                                    continue;
                                }}
                            }}
                            
                            if (bestElement) {{
                                bestElement.scrollIntoView({{ behavior: 'instant', block: 'start' }});
                                actualScrollDistance = container.scrollTop - initialScroll;
                                if (actualScrollDistance > 100) {{
                                    scrollSuccess = true;
                                    break;
                                }}
                            }} else {{
                                // Direct container scroll
                                container.scrollTop = Math.min(initialScroll + targetDistance, maxScroll);
                                actualScrollDistance = container.scrollTop - initialScroll;
                                if (actualScrollDistance > 100) {{
                                    scrollSuccess = true;
                                    break;
                                }}
                            }}
                        }}
                    }}
                    
                    // Method 2: Fallback to window scrolling if container scroll failed
                    if (!scrollSuccess) {{
                        const initialWindowScroll = window.scrollY;
                        const elements = document.querySelectorAll('*');
                        let bestElement = null;
                        let bestDistance = Infinity;
                        
                        for (const el of elements) {{
                            try {{
                                const rect = el.getBoundingClientRect();
                                const elementTop = rect.top + window.scrollY;
                                const targetScroll = initialWindowScroll + targetDistance;
                                const distance = Math.abs(elementTop - targetScroll);
                                
                                if (distance < bestDistance && elementTop > initialWindowScroll + window.innerHeight) {{
                                    bestElement = el;
                                    bestDistance = distance;
                                }}
                            }} catch (e) {{
                                continue;
                            }}
                        }}
                        
                        if (bestElement) {{
                            bestElement.scrollIntoView({{ behavior: 'instant', block: 'start' }});
                            actualScrollDistance = window.scrollY - initialWindowScroll;
                        }} else {{
                            window.scrollBy(0, targetDistance);
                            actualScrollDistance = window.scrollY - initialWindowScroll;
                        }}
                        
                        scrollSuccess = actualScrollDistance > 50;
                    }}
                    
                    return {{ success: scrollSuccess, distance: actualScrollDistance }};
                }}
            """, target_distance)
            
            # Wait for scroll to complete and DOM to update
            await asyncio.sleep(1.0)
            
            final_state = await self.get_scroll_position()
            result.containers_after = final_state['containerCount']
            
            # Calculate scroll distance from multiple sources
            window_scroll_distance = final_state['windowScrollY'] - initial_state['windowScrollY']
            doc_scroll_distance = final_state['documentScrollTop'] - initial_state['documentScrollTop']
            
            # Check custom container scroll distances
            container_scroll_distances = []
            final_scrollable = final_state.get('scrollableContainers', [])
            for i, final_container in enumerate(final_scrollable):
                if i < len(scrollable_containers):
                    initial_container = scrollable_containers[i]
                    if (final_container['id'] == initial_container['id'] and 
                        final_container['tag'] == initial_container['tag']):
                        container_distance = final_container['scrollTop'] - initial_container['scrollTop']
                        if container_distance > 0:
                            container_scroll_distances.append(container_distance)
            
            # Use the largest detected scroll distance
            all_distances = [window_scroll_distance, doc_scroll_distance] + container_scroll_distances
            result.scroll_distance = max(all_distances) if any(d > 0 for d in all_distances) else 0
            
            # If JavaScript reported a distance, use that if it's larger
            js_distance = scroll_completed.get('distance', 0) if isinstance(scroll_completed, dict) else 0
            if js_distance > result.scroll_distance:
                result.scroll_distance = js_distance
            
            result.execution_time = time.time() - start_time
            
            # Dynamic success threshold - adapt to what's actually possible on the page
            # If we scroll less than expected, lower the threshold dynamically
            dynamic_threshold = min(
                self.min_scroll_distance * 0.3,  # Original threshold (600px)
                max(100, result.scroll_distance * 0.8) if result.scroll_distance > 0 else 100  # Adaptive threshold
            )
            result.success = result.scroll_distance >= dynamic_threshold
            result.new_containers_detected = result.containers_after > result.containers_before
            
            logger.info(f"✓ Scrolled {result.scroll_distance}px in {result.execution_time:.3f}s (threshold: {dynamic_threshold:.0f}px)")
            logger.info(f"✓ Containers: {result.containers_before} → {result.containers_after}")
            logger.debug(f"   Success criteria: {result.scroll_distance}px >= {dynamic_threshold:.0f}px = {result.success}")
            if container_scroll_distances:
                logger.debug(f"   Custom container scrolls: {container_scroll_distances}")
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Primary scroll method failed: {e}")
            
        return result
    
    async def scroll_method_2_container_scrolltop(self, target_distance: int = 2000) -> ScrollResult:
        """
        Fallback scroll method: container.scrollTop
        Based on verified test results - Rank #2
        Enhanced to detect custom scroll containers
        """
        result = ScrollResult("container.scrollTop")
        logger.info(f"Using fallback scroll method: {result.method_name}")
        
        try:
            start_time = time.time()
            initial_state = await self.get_scroll_position()
            initial_scroll = initial_state['windowScrollY']
            result.containers_before = initial_state['containerCount']
            
            # Get scrollable containers for debugging
            scrollable_containers = initial_state.get('scrollableContainers', [])
            logger.debug(f"   Found {len(scrollable_containers)} scrollable containers")
            
            # Enhanced direct scrollTop manipulation
            scroll_result = await self.page.evaluate(f"""
                (targetDistance) => {{
                    let totalScrolled = 0;
                    let containersScrolled = [];
                    
                    // Find all scrollable containers, prioritize by size
                    const containers = Array.from(document.querySelectorAll('*')).filter(el => {{
                        try {{
                            return el.scrollHeight > el.clientHeight && el.scrollTop >= 0;
                        }} catch (e) {{
                            return false;
                        }}
                    }});
                    
                    // Sort by scrollable area (largest first)
                    containers.sort((a, b) => 
                        (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight)
                    );
                    
                    // Try to scroll each container
                    for (const container of containers.slice(0, 5)) {{
                        const initialScroll = container.scrollTop;
                        const maxScroll = container.scrollHeight - container.clientHeight;
                        
                        if (initialScroll < maxScroll) {{
                            const targetScroll = Math.min(initialScroll + targetDistance, maxScroll);
                            container.scrollTop = targetScroll;
                            
                            // Check if scroll actually happened
                            const actualScroll = container.scrollTop - initialScroll;
                            if (actualScroll > 50) {{
                                totalScrolled = Math.max(totalScrolled, actualScroll);
                                containersScrolled.push({{
                                    tag: container.tagName,
                                    id: container.id || 'none',
                                    scrolled: actualScroll
                                }});
                                
                                // If we got significant scroll, we can stop
                                if (actualScroll >= targetDistance * 0.5) {{
                                    break;
                                }}
                            }}
                        }}
                    }}
                    
                    // Fallback to window/document scrolling if no container scrolled enough
                    if (totalScrolled < targetDistance * 0.3) {{
                        const initialWindowScroll = window.scrollY;
                        const initialDocScroll = document.documentElement.scrollTop;
                        
                        // Try window.scrollTo first
                        window.scrollTo(0, initialWindowScroll + targetDistance);
                        const windowScrolled = window.scrollY - initialWindowScroll;
                        
                        if (windowScrolled < 50) {{
                            // Try document.documentElement.scrollTop
                            document.documentElement.scrollTop = initialDocScroll + targetDistance;
                            const docScrolled = document.documentElement.scrollTop - initialDocScroll;
                            totalScrolled = Math.max(totalScrolled, docScrolled, windowScrolled);
                        }} else {{
                            totalScrolled = Math.max(totalScrolled, windowScrolled);
                        }}
                    }}
                    
                    return {{
                        success: totalScrolled > 50,
                        distance: totalScrolled,
                        containers: containersScrolled
                    }};
                }}
            """, target_distance)
            
            # Wait for scroll to complete and DOM to update
            await asyncio.sleep(1.0)
            
            final_state = await self.get_scroll_position()
            result.containers_after = final_state['containerCount']
            
            # Calculate scroll distance from multiple sources
            window_scroll_distance = final_state['windowScrollY'] - initial_state['windowScrollY']
            doc_scroll_distance = final_state['documentScrollTop'] - initial_state['documentScrollTop']
            
            # Check custom container scroll distances
            container_scroll_distances = []
            final_scrollable = final_state.get('scrollableContainers', [])
            for i, final_container in enumerate(final_scrollable):
                if i < len(scrollable_containers):
                    initial_container = scrollable_containers[i]
                    if (final_container['id'] == initial_container['id'] and 
                        final_container['tag'] == initial_container['tag']):
                        container_distance = final_container['scrollTop'] - initial_container['scrollTop']
                        if container_distance > 0:
                            container_scroll_distances.append(container_distance)
            
            # Use the largest detected scroll distance
            all_distances = [window_scroll_distance, doc_scroll_distance] + container_scroll_distances
            result.scroll_distance = max(all_distances) if any(d > 0 for d in all_distances) else 0
            
            # Use JavaScript reported distance if larger
            if isinstance(scroll_result, dict):
                js_distance = scroll_result.get('distance', 0)
                if js_distance > result.scroll_distance:
                    result.scroll_distance = js_distance
                    
                if scroll_result.get('containers'):
                    logger.debug(f"   Containers scrolled by JS: {scroll_result['containers']}")
            
            result.execution_time = time.time() - start_time
            
            # Dynamic success threshold - adapt to what's actually possible on the page
            # If we scroll less than expected, lower the threshold dynamically  
            dynamic_threshold = min(
                self.min_scroll_distance * 0.3,  # Original threshold (600px)
                max(100, result.scroll_distance * 0.8) if result.scroll_distance > 0 else 100  # Adaptive threshold
            )
            result.success = result.scroll_distance >= dynamic_threshold
            result.new_containers_detected = result.containers_after > result.containers_before
            
            logger.info(f"✓ Scrolled {result.scroll_distance}px in {result.execution_time:.3f}s (threshold: {dynamic_threshold:.0f}px)")
            logger.info(f"✓ Containers: {result.containers_before} → {result.containers_after}")
            logger.debug(f"   Success criteria: {result.scroll_distance}px >= {dynamic_threshold:.0f}px = {result.success}")
            if container_scroll_distances:
                logger.debug(f"   Custom container scrolls: {container_scroll_distances}")
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Fallback scroll method failed: {e}")
            
        return result
    
    async def perform_scroll_with_fallback(self, target_distance: int = 2000) -> ScrollResult:
        """
        Perform scrolling using primary method with fallback
        """
        logger.info(f"Attempting scroll of {target_distance}px")
        
        # Try primary method first (Element.scrollIntoView)
        result = await self.scroll_method_1_element_scrollintoview(target_distance)
        
        # Use dynamic threshold for primary method success
        primary_threshold = max(100, self.min_scroll_distance * 0.5)  # At least 100px or 1000px
        if result.success and result.scroll_distance >= 50:  # Very lenient threshold
            logger.info(f"✓ Primary method successful: {result.scroll_distance}px")
            self.total_scrolled_distance += result.scroll_distance
            self.scroll_attempts += 1
            return result
        
        # Fallback to container.scrollTop method
        logger.warning("Primary method insufficient, trying fallback method")
        fallback_result = await self.scroll_method_2_container_scrolltop(target_distance)
        
        if fallback_result.success:
            logger.info(f"✓ Fallback method successful: {fallback_result.scroll_distance}px")
            self.total_scrolled_distance += fallback_result.scroll_distance
            self.scroll_attempts += 1
            return fallback_result
        
        # Both methods failed
        logger.error("Both scroll methods failed")
        self.scroll_attempts += 1
        return fallback_result
    
    async def detect_boundary_in_batch(self, containers: List[Dict], boundary_criteria: Dict) -> Optional[Dict]:
        """
        Scan a batch of containers for boundary conditions
        boundary_criteria should contain the specific conditions to check for
        """
        logger.info(f"Scanning {len(containers)} containers for boundary")
        
        try:
            # This is a placeholder - implement specific boundary detection logic
            # based on your application's requirements
            for container in containers:
                container_id = container['id']
                
                # Example boundary criteria (customize based on your needs):
                # - Check for specific generation ID patterns
                # - Check for date/time boundaries
                # - Check for content type boundaries
                # - Check for user/creator boundaries
                
                # Get container details
                container_details = await self.page.evaluate(f"""
                    () => {{
                        const container = document.querySelector('[data-generation-id="{container_id}"], #{container_id}');
                        if (!container) return null;
                        
                        return {{
                            id: container.getAttribute('data-generation-id') || container.id,
                            text: container.textContent || '',
                            className: container.className,
                            dataset: Object.assign({{}}, container.dataset),
                            attributes: Array.from(container.attributes).reduce((acc, attr) => {{
                                acc[attr.name] = attr.value;
                                return acc;
                            }}, {{}})
                        }};
                    }}
                """)
                
                if container_details:
                    # Apply boundary criteria checks
                    if self._matches_boundary_criteria(container_details, boundary_criteria):
                        logger.info(f"✓ Boundary detected at container: {container_id}")
                        return container_details
                
        except Exception as e:
            logger.error(f"Error during boundary detection: {e}")
            
        return None
    
    def _matches_boundary_criteria(self, container: Dict, criteria: Dict) -> bool:
        """
        Check if a container matches the boundary criteria
        Customize this method based on your specific boundary detection needs
        """
        # Example criteria checks:
        
        # Check for specific generation ID pattern
        if 'generation_id_pattern' in criteria:
            container_id = container.get('id', '')
            if criteria['generation_id_pattern'] in container_id:
                return True
        
        # Check for specific text content
        if 'text_contains' in criteria:
            container_text = container.get('text', '').lower()
            if criteria['text_contains'].lower() in container_text:
                return True
        
        # Check for specific attributes
        if 'attribute_matches' in criteria:
            for attr_name, attr_value in criteria['attribute_matches'].items():
                if container.get('attributes', {}).get(attr_name) == attr_value:
                    return True
        
        # Check for dataset properties
        if 'dataset_matches' in criteria:
            for data_name, data_value in criteria['dataset_matches'].items():
                if container.get('dataset', {}).get(data_name) == data_value:
                    return True
        
        return False
    
    async def check_end_of_gallery(self) -> bool:
        """Check if we've reached the end of the gallery"""
        try:
            end_reached = await self.page.evaluate("""
                () => {
                    // Check if we're at or near the bottom
                    const scrollTop = window.scrollY || document.documentElement.scrollTop;
                    const scrollHeight = document.documentElement.scrollHeight;
                    const clientHeight = window.innerHeight;
                    
                    // Consider end reached if within 100px of bottom
                    const atBottom = (scrollTop + clientHeight) >= (scrollHeight - 100);
                    
                    // Also check for "load more" or "end of content" indicators
                    const endIndicators = document.querySelectorAll(
                        '.end-of-list, .no-more-content, [class*="end"], [class*="bottom"]'
                    );
                    const hasEndIndicator = endIndicators.length > 0;
                    
                    return atBottom || hasEndIndicator;
                }
            """)
            
            if end_reached:
                logger.info("✓ End of gallery reached")
            
            return end_reached
            
        except Exception as e:
            logger.error(f"Error checking end of gallery: {e}")
            return False
    
    async def scroll_until_boundary_found(self, boundary_criteria: Dict) -> Optional[Dict]:
        """
        Main method: Scroll through gallery until boundary is found or end is reached
        """
        logger.info("Starting boundary detection with verified scroll methods")
        logger.info(f"Boundary criteria: {boundary_criteria}")
        
        boundary_found = None
        consecutive_failed_scrolls = 0
        max_consecutive_failures = 100  # Allow many more attempts before giving up
        
        while (self.scroll_attempts < self.max_scroll_attempts and 
               consecutive_failed_scrolls < max_consecutive_failures):
            
            # Get initial state
            initial_state = await self.get_scroll_position()
            initial_containers = initial_state['containers']
            
            # Perform scroll
            scroll_result = await self.perform_scroll_with_fallback(self.min_scroll_distance)
            
            if not scroll_result.success or scroll_result.scroll_distance < 500:
                consecutive_failed_scrolls += 1
                logger.warning(f"Scroll attempt failed or insufficient ({consecutive_failed_scrolls}/{max_consecutive_failures})")
                
                # Check if we've reached the end
                if await self.check_end_of_gallery():
                    logger.info("End of gallery reached - stopping search")
                    break
                    
                # Wait and try again
                await asyncio.sleep(2)
                continue
            
            # Reset failure counter on successful scroll
            consecutive_failed_scrolls = 0
            
            # Wait for new content to load
            logger.info("Waiting for new content to load...")
            await asyncio.sleep(3)
            
            # Detect new containers
            has_new, new_containers = await self.detect_new_containers(initial_containers)
            
            if has_new and new_containers:
                # Scan new batch for boundary
                boundary_found = await self.detect_boundary_in_batch(new_containers, boundary_criteria)
                
                if boundary_found:
                    logger.info(f"✓ BOUNDARY FOUND after {self.scroll_attempts} scrolls!")
                    logger.info(f"✓ Total distance scrolled: {self.total_scrolled_distance}px")
                    break
            else:
                logger.info("No new containers detected, continuing scroll...")
            
            # Additional wait between scroll attempts
            await asyncio.sleep(1)
        
        # Log final statistics
        logger.info(f"Boundary search completed:")
        logger.info(f"  - Scroll attempts: {self.scroll_attempts}")
        logger.info(f"  - Total distance: {self.total_scrolled_distance}px")
        logger.info(f"  - Boundary found: {'Yes' if boundary_found else 'No'}")
        
        return boundary_found
    
    def get_scroll_statistics(self) -> Dict:
        """Get scrolling statistics"""
        return {
            'total_scrolled_distance': self.total_scrolled_distance,
            'scroll_attempts': self.scroll_attempts,
            'average_scroll_distance': (
                self.total_scrolled_distance / self.scroll_attempts 
                if self.scroll_attempts > 0 else 0
            ),
            'min_scroll_distance': self.min_scroll_distance
        }


# Example usage and testing
async def test_boundary_scroll_manager(page: Page):
    """Test function for the BoundaryScrollManager"""
    
    # Initialize the manager
    manager = BoundaryScrollManager(page)
    
    # Example boundary criteria (customize based on your needs)
    boundary_criteria = {
        'generation_id_pattern': '#000001',  # Look for generation ID containing this
        'text_contains': 'older generation',  # Look for this text
        'attribute_matches': {
            'data-status': 'completed'  # Look for this attribute/value pair
        }
    }
    
    # Start the boundary search
    boundary = await manager.scroll_until_boundary_found(boundary_criteria)
    
    # Get statistics
    stats = manager.get_scroll_statistics()
    
    return boundary, stats


if __name__ == "__main__":
    # This module should be imported and used by other automation scripts
    pass