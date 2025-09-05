"""
Unified Scroll Manager - Phase 2 Optimization
Consolidates 11+ scroll methods into intelligent, performance-tracked system

Performance Target: 2-5 seconds saved per scroll operation
Code Reduction: 800-1000 lines consolidated
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class ScrollStrategy(Enum):
    """Scroll strategy types ordered by performance preference"""
    CONTAINER_TOP = "container_top"           # Fastest - direct container manipulation
    ELEMENT_INTO_VIEW = "element_into_view"   # Reliable - browser native scrolling
    ENHANCED_TRIGGERS = "enhanced_triggers"   # Complex - multiple trigger points
    INTERSECTION_OBSERVER = "intersection_observer"  # Advanced - observer pattern
    MANUAL_ELEMENT = "manual_element"         # Fallback - element-by-element
    NETWORK_IDLE = "network_idle"            # Slowest - wait for network


@dataclass
class ScrollResult:
    """Standardized scroll operation result"""
    success: bool
    content_loaded: int
    time_taken: float
    strategy_used: ScrollStrategy
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ScrollPerformanceMetrics:
    """Track scroll strategy performance for intelligent selection"""
    strategy: ScrollStrategy
    success_rate: float = 0.0
    average_time: float = 0.0
    content_efficiency: float = 0.0  # content_loaded / time_taken
    total_attempts: int = 0
    successful_attempts: int = 0
    last_used: float = 0.0


class UnifiedScrollManager:
    """
    Unified scroll management system that consolidates all scroll operations
    into intelligent, performance-tracked execution
    
    Replaces 11+ methods:
    - scroll_to_find_boundary_generations
    - _try_enhanced_infinite_scroll_triggers  
    - _try_network_idle_scroll
    - _try_intersection_observer_scroll
    - _try_manual_element_scroll
    - scroll_and_find_more_thumbnails
    - scroll_thumbnail_gallery
    - _find_scrollable_container
    - _wait_for_scroll_content_load
    - _validate_scroll_success
    - _diagnose_scroll_environment
    """
    
    def __init__(self):
        self.performance_metrics: Dict[ScrollStrategy, ScrollPerformanceMetrics] = {}
        self.initialize_performance_tracking()
        
        # Optimization settings
        self.max_scroll_distance = 2500
        self.scroll_batch_size = 5
        self.scroll_wait_time = 0.5  # Reduced from 1.0s
        self.max_attempts = 5  # Reduced from 10
        
        # Container cache for performance
        self.container_cache: Dict[str, Any] = {}
        self.cache_ttl = 30  # seconds
        
    def initialize_performance_tracking(self):
        """Initialize performance tracking for all strategies"""
        for strategy in ScrollStrategy:
            self.performance_metrics[strategy] = ScrollPerformanceMetrics(strategy=strategy)
    
    async def scroll_to_load_content(self, 
                                   page,
                                   container_selector: str = None,
                                   target_element_selector: str = None,
                                   max_distance: float = None,
                                   expected_content_increase: int = 1,
                                   boundary_criteria: Dict = None) -> ScrollResult:
        """
        Unified entry point for all scroll operations
        
        Args:
            page: Playwright page object
            container_selector: CSS selector for scroll container
            target_element_selector: Specific element to scroll to
            max_distance: Maximum scroll distance (defaults to class setting)
            expected_content_increase: Minimum content increase to consider success
            boundary_criteria: Specific criteria for boundary detection
            
        Returns:
            ScrollResult with success status, content loaded, time taken, strategy used
        """
        start_time = time.time()
        max_distance = max_distance or self.max_scroll_distance
        
        # Get initial content count
        initial_content = await self._get_content_count(page)
        
        # Select optimal strategy based on performance history and context
        strategy = self._select_optimal_strategy(boundary_criteria is not None)
        
        try:
            result = await self._execute_strategy(
                strategy, page, container_selector, target_element_selector,
                max_distance, expected_content_increase, boundary_criteria
            )
            
            # Update performance metrics
            execution_time = time.time() - start_time
            content_loaded = result.content_loaded if result.success else 0
            
            self._update_performance_metrics(strategy, result.success, execution_time, content_loaded)
            
            result.time_taken = execution_time
            result.strategy_used = strategy
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_performance_metrics(strategy, False, execution_time, 0)
            
            return ScrollResult(
                success=False,
                content_loaded=0,
                time_taken=execution_time,
                strategy_used=strategy,
                error=str(e)
            )
    
    def _select_optimal_strategy(self, is_boundary_search: bool = False) -> ScrollStrategy:
        """
        Intelligently select scroll strategy based on performance history and context
        
        Args:
            is_boundary_search: True if searching for specific boundary content
            
        Returns:
            Optimal ScrollStrategy for current context
        """
        # For boundary searches, prefer strategies with higher success rates
        if is_boundary_search:
            strategies_by_success = sorted(
                self.performance_metrics.items(),
                key=lambda x: (x[1].success_rate, -x[1].average_time),
                reverse=True
            )
        else:
            # For general content loading, prefer strategies with best efficiency
            strategies_by_efficiency = sorted(
                self.performance_metrics.items(),
                key=lambda x: (x[1].content_efficiency, x[1].success_rate),
                reverse=True
            )
            strategies_by_success = strategies_by_efficiency
        
        # Return best performing strategy, fallback to CONTAINER_TOP if no history
        if strategies_by_success and strategies_by_success[0][1].total_attempts > 0:
            return strategies_by_success[0][0]
        
        return ScrollStrategy.CONTAINER_TOP  # Default fastest strategy
    
    async def _execute_strategy(self, 
                              strategy: ScrollStrategy,
                              page,
                              container_selector: str,
                              target_element_selector: str,
                              max_distance: float,
                              expected_content_increase: int,
                              boundary_criteria: Dict) -> ScrollResult:
        """Execute the selected scroll strategy"""
        
        if strategy == ScrollStrategy.CONTAINER_TOP:
            return await self._scroll_via_container_top(
                page, container_selector, max_distance, expected_content_increase
            )
        
        elif strategy == ScrollStrategy.ELEMENT_INTO_VIEW:
            return await self._scroll_via_element_into_view(
                page, target_element_selector, expected_content_increase
            )
        
        elif strategy == ScrollStrategy.ENHANCED_TRIGGERS:
            return await self._scroll_via_enhanced_triggers(
                page, max_distance, expected_content_increase
            )
        
        elif strategy == ScrollStrategy.INTERSECTION_OBSERVER:
            return await self._scroll_via_intersection_observer(
                page, expected_content_increase
            )
        
        elif strategy == ScrollStrategy.MANUAL_ELEMENT:
            return await self._scroll_via_manual_element(
                page, max_distance, expected_content_increase
            )
        
        elif strategy == ScrollStrategy.NETWORK_IDLE:
            return await self._scroll_via_network_idle(
                page, expected_content_increase
            )
        
        else:
            raise ValueError(f"Unknown scroll strategy: {strategy}")
    
    async def _scroll_via_container_top(self, 
                                       page,
                                       container_selector: str,
                                       max_distance: float,
                                       expected_content_increase: int) -> ScrollResult:
        """Fastest scroll method - direct container manipulation"""
        
        container = await self._get_scrollable_container(page, container_selector)
        if not container:
            return ScrollResult(success=False, content_loaded=0, time_taken=0.0, strategy_used=ScrollStrategy.CONTAINER_TOP)
        
        initial_count = await self._get_content_count(page)
        scrolled_distance = 0
        
        for attempt in range(self.max_attempts):
            # Scroll by batch
            scroll_amount = min(self.max_scroll_distance / self.scroll_batch_size, max_distance - scrolled_distance)
            
            await page.evaluate(f"""
                (container, scrollAmount) => {{
                    container.scrollTop += scrollAmount;
                }}
            """, container, scroll_amount)
            
            scrolled_distance += scroll_amount
            
            # Wait for content load
            await asyncio.sleep(self.scroll_wait_time)
            
            # Check for new content
            current_count = await self._get_content_count(page)
            content_loaded = current_count - initial_count
            
            if content_loaded >= expected_content_increase:
                return ScrollResult(
                    success=True,
                    content_loaded=content_loaded,
                    time_taken=0.0,  # Will be set by caller
                    strategy_used=ScrollStrategy.CONTAINER_TOP
                )
            
            if scrolled_distance >= max_distance:
                break
        
        # Return partial success if any content was loaded
        final_count = await self._get_content_count(page)
        content_loaded = final_count - initial_count
        
        return ScrollResult(
            success=content_loaded > 0,
            content_loaded=content_loaded,
            time_taken=0.0,  # Will be set by caller
            strategy_used=ScrollStrategy.CONTAINER_TOP
        )
    
    async def _scroll_via_element_into_view(self, 
                                          page,
                                          target_element_selector: str,
                                          expected_content_increase: int) -> ScrollResult:
        """Reliable scroll method - browser native scrolling"""
        
        if not target_element_selector:
            # Fall back to general scrolling
            return await self._scroll_via_container_top(page, None, self.max_scroll_distance, expected_content_increase)
        
        initial_count = await self._get_content_count(page)
        
        try:
            # Find target element and scroll to it
            await page.evaluate(f"""
                () => {{
                    const element = document.querySelector('{target_element_selector}');
                    if (element) {{
                        element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    }}
                }}
            """)
            
            # Wait for scroll completion and content load
            await asyncio.sleep(self.scroll_wait_time * 2)  # Longer wait for smooth scroll
            
            final_count = await self._get_content_count(page)
            content_loaded = final_count - initial_count
            
            return ScrollResult(
                success=content_loaded >= expected_content_increase,
                content_loaded=content_loaded,
                time_taken=0.0,  # Will be set by caller
                strategy_used=ScrollStrategy.ELEMENT_INTO_VIEW
            )
            
        except Exception as e:
            return ScrollResult(
                success=False,
                content_loaded=0,
                time_taken=0.0,
                strategy_used=ScrollStrategy.ELEMENT_INTO_VIEW,
                error=str(e)
            )
    
    async def _scroll_via_enhanced_triggers(self,
                                          page,
                                          max_distance: float,
                                          expected_content_increase: int) -> ScrollResult:
        """Complex scroll method - multiple trigger points"""
        
        initial_count = await self._get_content_count(page)
        content_loaded = 0
        
        # Multiple trigger strategies
        triggers = [
            "window.scrollTo(0, document.body.scrollHeight);",
            "window.scrollBy(0, 1000);",
            "document.documentElement.scrollTop = document.documentElement.scrollHeight;",
            "const event = new Event('scroll'); window.dispatchEvent(event);"
        ]
        
        for trigger in triggers:
            try:
                await page.evaluate(trigger)
                await asyncio.sleep(self.scroll_wait_time)
                
                current_count = await self._get_content_count(page)
                content_loaded = current_count - initial_count
                
                if content_loaded >= expected_content_increase:
                    break
                    
            except Exception:
                continue  # Try next trigger
        
        return ScrollResult(
            success=content_loaded >= expected_content_increase,
            content_loaded=content_loaded,
            time_taken=0.0,  # Will be set by caller
            strategy_used=ScrollStrategy.ENHANCED_TRIGGERS
        )
    
    async def _scroll_via_intersection_observer(self,
                                              page,
                                              expected_content_increase: int) -> ScrollResult:
        """Advanced scroll method - intersection observer pattern"""
        
        initial_count = await self._get_content_count(page)
        
        try:
            # Set up intersection observer for dynamic loading
            await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        const observer = new IntersectionObserver((entries) => {
                            entries.forEach((entry) => {
                                if (entry.isIntersecting) {
                                    window.scrollBy(0, 500);
                                }
                            });
                        });
                        
                        // Observe bottom elements
                        const bottomElements = Array.from(document.querySelectorAll('*')).slice(-5);
                        bottomElements.forEach(el => observer.observe(el));
                        
                        setTimeout(() => {
                            observer.disconnect();
                            resolve();
                        }, 3000);  // 3 second timeout
                    });
                }
            """)
            
            final_count = await self._get_content_count(page)
            content_loaded = final_count - initial_count
            
            return ScrollResult(
                success=content_loaded >= expected_content_increase,
                content_loaded=content_loaded,
                time_taken=0.0,  # Will be set by caller
                strategy_used=ScrollStrategy.INTERSECTION_OBSERVER
            )
            
        except Exception as e:
            return ScrollResult(
                success=False,
                content_loaded=0,
                time_taken=0.0,
                strategy_used=ScrollStrategy.INTERSECTION_OBSERVER,
                error=str(e)
            )
    
    async def _scroll_via_manual_element(self,
                                       page,
                                       max_distance: float,
                                       expected_content_increase: int) -> ScrollResult:
        """Fallback scroll method - element by element"""
        
        initial_count = await self._get_content_count(page)
        scrolled_distance = 0
        
        for attempt in range(self.max_attempts):
            try:
                # Find scrollable elements and scroll them
                await page.evaluate(f"""
                    () => {{
                        const scrollableElements = Array.from(document.querySelectorAll('*'))
                            .filter(el => el.scrollHeight > el.clientHeight);
                        
                        scrollableElements.forEach(el => {{
                            el.scrollTop += {self.max_scroll_distance / self.max_attempts};
                        }});
                    }}
                """)
                
                scrolled_distance += (self.max_scroll_distance / self.max_attempts)
                await asyncio.sleep(self.scroll_wait_time)
                
                current_count = await self._get_content_count(page)
                content_loaded = current_count - initial_count
                
                if content_loaded >= expected_content_increase or scrolled_distance >= max_distance:
                    break
                    
            except Exception:
                continue
        
        final_count = await self._get_content_count(page)
        content_loaded = final_count - initial_count
        
        return ScrollResult(
            success=content_loaded > 0,
            content_loaded=content_loaded,
            time_taken=0.0,  # Will be set by caller
            strategy_used=ScrollStrategy.MANUAL_ELEMENT
        )
    
    async def _scroll_via_network_idle(self,
                                     page,
                                     expected_content_increase: int) -> ScrollResult:
        """Slowest but most reliable - wait for network idle"""
        
        initial_count = await self._get_content_count(page)
        
        try:
            # Scroll and wait for network idle
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_load_state("networkidle", timeout=5000)
            
            final_count = await self._get_content_count(page)
            content_loaded = final_count - initial_count
            
            return ScrollResult(
                success=content_loaded >= expected_content_increase,
                content_loaded=content_loaded,
                time_taken=0.0,  # Will be set by caller
                strategy_used=ScrollStrategy.NETWORK_IDLE
            )
            
        except Exception as e:
            return ScrollResult(
                success=False,
                content_loaded=0,
                time_taken=0.0,
                strategy_used=ScrollStrategy.NETWORK_IDLE,
                error=str(e)
            )
    
    async def _get_scrollable_container(self, page, container_selector: str = None) -> Optional[Any]:
        """Get scrollable container with caching"""
        
        cache_key = container_selector or "default"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.container_cache:
            cached_item = self.container_cache[cache_key]
            if current_time - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['container']
        
        # Find container
        container = None
        if container_selector:
            container = await page.query_selector(container_selector)
        
        if not container:
            # Find any scrollable container
            container = await page.evaluate("""
                () => {
                    const containers = Array.from(document.querySelectorAll('*'))
                        .filter(el => el.scrollHeight > el.clientHeight)
                        .sort((a, b) => b.scrollHeight - a.scrollHeight);
                    return containers[0] || document.documentElement;
                }
            """)
        
        # Cache result
        self.container_cache[cache_key] = {
            'container': container,
            'timestamp': current_time
        }
        
        return container
    
    async def _get_content_count(self, page) -> int:
        """Get current content count for comparison"""
        try:
            return await page.evaluate("""
                () => {
                    // Count various content indicators
                    const thumbnails = document.querySelectorAll('.thumsItem, .thumbnail-item, [class*="thumb"], [class*="item"]').length;
                    const containers = document.querySelectorAll('[class*="container"], [class*="card"]').length;
                    const images = document.querySelectorAll('img').length;
                    
                    return Math.max(thumbnails, containers / 2, images / 3);
                }
            """)
        except:
            return 0
    
    def _update_performance_metrics(self, 
                                   strategy: ScrollStrategy,
                                   success: bool,
                                   execution_time: float,
                                   content_loaded: int):
        """Update performance metrics for strategy selection optimization"""
        
        metrics = self.performance_metrics[strategy]
        metrics.total_attempts += 1
        
        if success:
            metrics.successful_attempts += 1
        
        # Update success rate
        metrics.success_rate = metrics.successful_attempts / metrics.total_attempts
        
        # Update average time
        if metrics.total_attempts == 1:
            metrics.average_time = execution_time
        else:
            metrics.average_time = (metrics.average_time * (metrics.total_attempts - 1) + execution_time) / metrics.total_attempts
        
        # Update content efficiency
        if execution_time > 0:
            current_efficiency = content_loaded / execution_time
            if metrics.total_attempts == 1:
                metrics.content_efficiency = current_efficiency
            else:
                metrics.content_efficiency = (metrics.content_efficiency * (metrics.total_attempts - 1) + current_efficiency) / metrics.total_attempts
        
        metrics.last_used = time.time()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for analysis"""
        
        report = {
            'strategies': {},
            'summary': {
                'total_scroll_operations': sum(m.total_attempts for m in self.performance_metrics.values()),
                'overall_success_rate': 0.0,
                'average_content_efficiency': 0.0,
                'best_strategy': None,
                'time_saved_estimate': 0.0
            }
        }
        
        # Calculate metrics for each strategy
        total_attempts = 0
        total_successful = 0
        total_efficiency = 0.0
        strategies_with_data = 0
        
        for strategy, metrics in self.performance_metrics.items():
            if metrics.total_attempts > 0:
                report['strategies'][strategy.value] = {
                    'success_rate': f"{metrics.success_rate:.2%}",
                    'average_time': f"{metrics.average_time:.2f}s",
                    'content_efficiency': f"{metrics.content_efficiency:.2f}",
                    'total_attempts': metrics.total_attempts,
                    'successful_attempts': metrics.successful_attempts
                }
                
                total_attempts += metrics.total_attempts
                total_successful += metrics.successful_attempts
                total_efficiency += metrics.content_efficiency
                strategies_with_data += 1
        
        # Calculate summary metrics
        if total_attempts > 0:
            report['summary']['overall_success_rate'] = f"{(total_successful / total_attempts):.2%}"
        
        if strategies_with_data > 0:
            report['summary']['average_content_efficiency'] = f"{(total_efficiency / strategies_with_data):.2f}"
            
            # Find best strategy
            best_strategy = max(
                [(s, m) for s, m in self.performance_metrics.items() if m.total_attempts > 0],
                key=lambda x: (x[1].success_rate * x[1].content_efficiency),
                default=(None, None)
            )[0]
            
            if best_strategy:
                report['summary']['best_strategy'] = best_strategy.value
        
        # Estimate time saved (conservative estimate)
        baseline_time = 3.0  # Average time for old scroll methods
        if strategies_with_data > 0:
            avg_optimized_time = sum(m.average_time for m in self.performance_metrics.values() if m.total_attempts > 0) / strategies_with_data
            time_saved_per_operation = max(0, baseline_time - avg_optimized_time)
            report['summary']['time_saved_estimate'] = f"{time_saved_per_operation * total_attempts:.2f}s total"
        
        return report


# Global instance for reuse
unified_scroll_manager = UnifiedScrollManager()