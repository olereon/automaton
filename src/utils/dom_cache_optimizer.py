"""
DOM Cache Optimizer - Phase 2 Optimization
Implements intelligent caching and reuse of DOM selectors and elements

Performance Target: 1-3 seconds saved per operation
Code Reduction: Eliminates redundant DOM queries
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import json


class CacheStrategy(Enum):
    """DOM caching strategies"""
    AGGRESSIVE = "aggressive"    # Cache everything, 30s TTL
    BALANCED = "balanced"       # Cache selectors only, 15s TTL
    CONSERVATIVE = "conservative"  # Cache successful queries only, 5s TTL


@dataclass
class CacheEntry:
    """DOM cache entry with metadata"""
    element: Any
    selector: str
    timestamp: float
    access_count: int = 0
    last_access: float = 0.0
    page_url: str = ""
    success_rate: float = 1.0


@dataclass
class QueryPerformanceMetrics:
    """Track query performance for optimization"""
    selector: str
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_query_time: float = 0.0
    success_rate: float = 1.0
    first_query_time: float = 0.0
    last_query_time: float = 0.0


class DOMCacheOptimizer:
    """
    Intelligent DOM query caching and optimization system
    
    Features:
    - Selector result caching with TTL
    - Query performance tracking
    - Automatic cache invalidation
    - Memory usage optimization
    - Intelligent prefetching
    """
    
    def __init__(self, cache_strategy: CacheStrategy = CacheStrategy.BALANCED):
        self.cache_strategy = cache_strategy
        self.cache: Dict[str, CacheEntry] = {}
        self.performance_metrics: Dict[str, QueryPerformanceMetrics] = {}
        
        # Configuration based on strategy
        self.ttl = self._get_ttl_for_strategy(cache_strategy)
        self.max_cache_size = self._get_max_cache_size(cache_strategy)
        self.enable_prefetching = cache_strategy == CacheStrategy.AGGRESSIVE
        
        # Common selectors to prefetch
        self.common_selectors = [
            '.thumsItem', '.thumbnail-item', '.sc-eKQYOU.bdGRCs',
            '.sc-fileXT.gEIKhI', '.sc-hAYgFD.fLPdud',
            'button[aria-label="Close"]', '.ant-modal-close',
            '[class*="thumb"]', '[class*="container"]', '[class*="item"]'
        ]
        
        # Performance tracking
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_time_saved = 0.0
    
    def _get_ttl_for_strategy(self, strategy: CacheStrategy) -> float:
        """Get TTL based on caching strategy"""
        if strategy == CacheStrategy.AGGRESSIVE:
            return 30.0
        elif strategy == CacheStrategy.BALANCED:
            return 15.0
        else:  # CONSERVATIVE
            return 5.0
    
    def _get_max_cache_size(self, strategy: CacheStrategy) -> int:
        """Get maximum cache size based on strategy"""
        if strategy == CacheStrategy.AGGRESSIVE:
            return 1000
        elif strategy == CacheStrategy.BALANCED:
            return 500
        else:  # CONSERVATIVE
            return 100
    
    async def query_cached(self, page, selector: str, timeout: float = 5000) -> Optional[Any]:
        """
        Execute cached DOM query with performance tracking
        
        Args:
            page: Playwright page object
            selector: CSS selector
            timeout: Query timeout in milliseconds
            
        Returns:
            Element or None if not found
        """
        start_time = time.time()
        self.total_queries += 1
        
        # Initialize performance metrics for new selectors
        if selector not in self.performance_metrics:
            self.performance_metrics[selector] = QueryPerformanceMetrics(
                selector=selector,
                first_query_time=start_time
            )
        
        metrics = self.performance_metrics[selector]
        metrics.total_queries += 1
        metrics.last_query_time = start_time
        
        # Check cache first
        cache_key = self._get_cache_key(page, selector)
        cached_entry = self._get_from_cache(cache_key)
        
        if cached_entry:
            # Cache hit!
            self.cache_hits += 1
            metrics.cache_hits += 1
            cached_entry.access_count += 1
            cached_entry.last_access = start_time
            
            # Verify element is still valid (for aggressive caching)
            if self.cache_strategy == CacheStrategy.AGGRESSIVE:
                try:
                    # Quick validity check
                    await page.evaluate("element => element.isConnected", cached_entry.element)
                    
                    # Update performance metrics
                    query_time = time.time() - start_time
                    self._update_query_metrics(metrics, query_time, True)
                    
                    return cached_entry.element
                except:
                    # Element is stale, remove from cache
                    self._remove_from_cache(cache_key)
        
        # Cache miss - execute query
        self.cache_misses += 1
        metrics.cache_misses += 1
        
        try:
            element = await page.query_selector(selector)
            query_time = time.time() - start_time
            
            # Update performance metrics
            success = element is not None
            self._update_query_metrics(metrics, query_time, success)
            
            # Cache successful results (based on strategy)
            if self._should_cache_result(element, selector):
                self._add_to_cache(cache_key, element, selector, page)
            
            return element
            
        except Exception as e:
            query_time = time.time() - start_time
            self._update_query_metrics(metrics, query_time, False)
            return None
    
    async def query_selector_all_cached(self, page, selector: str, timeout: float = 5000) -> List[Any]:
        """
        Execute cached query_selector_all with performance tracking
        
        Args:
            page: Playwright page object  
            selector: CSS selector
            timeout: Query timeout in milliseconds
            
        Returns:
            List of elements (may be empty)
        """
        start_time = time.time()
        
        # For querySelectorAll, we cache the count and use it for optimization
        cache_key = f"{self._get_cache_key(page, selector)}_all"
        cached_entry = self._get_from_cache(cache_key)
        
        if cached_entry and isinstance(cached_entry.element, list):
            # Validate cached list is still accurate
            try:
                current_count = await page.evaluate(f"document.querySelectorAll('{selector}').length")
                if current_count == len(cached_entry.element):
                    self.cache_hits += 1
                    cached_entry.access_count += 1
                    cached_entry.last_access = start_time
                    return cached_entry.element
            except:
                self._remove_from_cache(cache_key)
        
        # Execute fresh query
        try:
            elements = await page.query_selector_all(selector)
            query_time = time.time() - start_time
            
            # Cache results
            if self._should_cache_result(elements, selector):
                self._add_to_cache(cache_key, elements, selector, page)
            
            return elements
            
        except Exception:
            return []
    
    async def wait_for_selector_cached(self, page, selector: str, timeout: float = 5000) -> Optional[Any]:
        """
        Execute cached wait_for_selector with intelligent timeout optimization
        
        Args:
            page: Playwright page object
            selector: CSS selector  
            timeout: Maximum wait time in milliseconds
            
        Returns:
            Element when it appears, or None if timeout
        """
        start_time = time.time()
        
        # Check if we've seen this selector recently (might appear faster)
        metrics = self.performance_metrics.get(selector)
        if metrics and metrics.success_rate > 0.8:
            # This selector usually succeeds, try shorter timeout first
            optimized_timeout = min(timeout, timeout * 0.6)
        else:
            optimized_timeout = timeout
        
        try:
            element = await page.wait_for_selector(selector, timeout=optimized_timeout)
            query_time = time.time() - start_time
            
            # Update metrics
            if selector not in self.performance_metrics:
                self.performance_metrics[selector] = QueryPerformanceMetrics(
                    selector=selector,
                    first_query_time=start_time
                )
            
            self._update_query_metrics(self.performance_metrics[selector], query_time, element is not None)
            
            # Cache successful result
            if element and self._should_cache_result(element, selector):
                cache_key = self._get_cache_key(page, selector)
                self._add_to_cache(cache_key, element, selector, page)
            
            return element
            
        except Exception:
            # If optimized timeout failed, try with full timeout
            if optimized_timeout < timeout:
                try:
                    element = await page.wait_for_selector(selector, timeout=timeout - optimized_timeout)
                    query_time = time.time() - start_time
                    
                    if selector in self.performance_metrics:
                        self._update_query_metrics(self.performance_metrics[selector], query_time, element is not None)
                    
                    return element
                except:
                    pass
            
            return None
    
    async def prefetch_common_selectors(self, page):
        """Prefetch commonly used selectors for performance"""
        if not self.enable_prefetching:
            return
        
        prefetch_tasks = []
        for selector in self.common_selectors:
            # Only prefetch if not already cached
            cache_key = self._get_cache_key(page, selector)
            if cache_key not in self.cache:
                prefetch_tasks.append(self._prefetch_selector(page, selector))
        
        if prefetch_tasks:
            # Execute prefetching in parallel
            await asyncio.gather(*prefetch_tasks, return_exceptions=True)
    
    async def _prefetch_selector(self, page, selector: str):
        """Prefetch a single selector"""
        try:
            element = await page.query_selector(selector)
            if element:
                cache_key = self._get_cache_key(page, selector)
                self._add_to_cache(cache_key, element, selector, page)
        except:
            pass  # Silently ignore prefetch failures
    
    def _get_cache_key(self, page, selector: str) -> str:
        """Generate cache key based on page URL and selector"""
        try:
            page_url = page.url
        except:
            page_url = "unknown"
        
        # Normalize URL for caching
        normalized_url = page_url.split('?')[0]  # Remove query parameters
        return f"{normalized_url}#{selector}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[CacheEntry]:
        """Get entry from cache with TTL validation"""
        if cache_key not in self.cache:
            return None
        
        entry = self.cache[cache_key]
        current_time = time.time()
        
        # Check TTL
        if current_time - entry.timestamp > self.ttl:
            self._remove_from_cache(cache_key)
            return None
        
        return entry
    
    def _add_to_cache(self, cache_key: str, element: Any, selector: str, page):
        """Add entry to cache with automatic cleanup"""
        current_time = time.time()
        
        # Cleanup if cache is full
        if len(self.cache) >= self.max_cache_size:
            self._cleanup_cache(0.3)  # Remove 30% of oldest entries
        
        try:
            page_url = page.url
        except:
            page_url = "unknown"
        
        self.cache[cache_key] = CacheEntry(
            element=element,
            selector=selector,
            timestamp=current_time,
            access_count=1,
            last_access=current_time,
            page_url=page_url
        )
    
    def _remove_from_cache(self, cache_key: str):
        """Remove entry from cache"""
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def _should_cache_result(self, element: Any, selector: str) -> bool:
        """Determine if result should be cached based on strategy"""
        if self.cache_strategy == CacheStrategy.CONSERVATIVE:
            return element is not None  # Only cache successful queries
        elif self.cache_strategy == CacheStrategy.BALANCED:
            return True  # Cache all queries
        else:  # AGGRESSIVE
            return True  # Cache everything
    
    def _cleanup_cache(self, cleanup_ratio: float = 0.3):
        """Clean up cache by removing oldest/least used entries"""
        if not self.cache:
            return
        
        entries_to_remove = int(len(self.cache) * cleanup_ratio)
        if entries_to_remove == 0:
            return
        
        # Sort by last access time and access count
        cache_items = list(self.cache.items())
        cache_items.sort(key=lambda x: (x[1].last_access, x[1].access_count))
        
        # Remove oldest entries
        for i in range(entries_to_remove):
            cache_key = cache_items[i][0]
            del self.cache[cache_key]
    
    def _update_query_metrics(self, metrics: QueryPerformanceMetrics, query_time: float, success: bool):
        """Update performance metrics for a query"""
        # Update average query time
        if metrics.total_queries == 1:
            metrics.average_query_time = query_time
        else:
            metrics.average_query_time = (
                (metrics.average_query_time * (metrics.total_queries - 1)) + query_time
            ) / metrics.total_queries
        
        # Update success rate
        if success:
            metrics.success_rate = (
                (metrics.success_rate * (metrics.total_queries - 1)) + 1.0
            ) / metrics.total_queries
        else:
            metrics.success_rate = (
                (metrics.success_rate * (metrics.total_queries - 1)) + 0.0  
            ) / metrics.total_queries
    
    def clear_cache(self):
        """Clear all cached entries"""
        self.cache.clear()
    
    def clear_expired_cache(self):
        """Clear only expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        
        if self.total_queries == 0:
            return {"message": "No queries executed yet"}
        
        cache_hit_rate = (self.cache_hits / self.total_queries) * 100
        cache_miss_rate = (self.cache_misses / self.total_queries) * 100
        
        # Calculate time savings estimate
        average_query_time = 0.05  # 50ms average DOM query
        time_saved = self.cache_hits * average_query_time
        
        stats = {
            'cache_performance': {
                'total_queries': self.total_queries,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'hit_rate': f"{cache_hit_rate:.1f}%",
                'miss_rate': f"{cache_miss_rate:.1f}%"
            },
            'cache_status': {
                'current_size': len(self.cache),
                'max_size': self.max_cache_size,
                'utilization': f"{(len(self.cache) / self.max_cache_size) * 100:.1f}%",
                'ttl': f"{self.ttl}s",
                'strategy': self.cache_strategy.value
            },
            'performance_impact': {
                'estimated_time_saved': f"{time_saved:.3f}s",
                'average_time_per_hit': f"{average_query_time * 1000:.1f}ms",
                'queries_per_cache_entry': f"{self.total_queries / max(1, len(self.cache)):.1f}"
            },
            'top_selectors': {}
        }
        
        # Top performing selectors
        if self.performance_metrics:
            top_selectors = sorted(
                [(selector, metrics) for selector, metrics in self.performance_metrics.items()],
                key=lambda x: x[1].total_queries,
                reverse=True
            )[:10]
            
            for selector, metrics in top_selectors:
                hit_rate = (metrics.cache_hits / metrics.total_queries * 100) if metrics.total_queries > 0 else 0
                stats['top_selectors'][selector] = {
                    'total_queries': metrics.total_queries,
                    'cache_hit_rate': f"{hit_rate:.1f}%",
                    'success_rate': f"{metrics.success_rate * 100:.1f}%",
                    'average_time': f"{metrics.average_query_time * 1000:.1f}ms"
                }
        
        return stats
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for optimizing DOM queries"""
        
        recommendations = {
            'cache_optimization': [],
            'selector_optimization': [],
            'performance_optimization': []
        }
        
        # Cache recommendations
        hit_rate = (self.cache_hits / max(1, self.total_queries)) * 100
        
        if hit_rate < 30:
            recommendations['cache_optimization'].append(
                "Consider using AGGRESSIVE caching strategy for better hit rates"
            )
        elif hit_rate > 80:
            recommendations['cache_optimization'].append(
                "Excellent cache performance! Consider increasing cache size"
            )
        
        if len(self.cache) / self.max_cache_size > 0.9:
            recommendations['cache_optimization'].append(
                "Cache utilization is high - consider increasing max_cache_size"
            )
        
        # Selector recommendations
        if self.performance_metrics:
            slow_selectors = [
                (selector, metrics) for selector, metrics in self.performance_metrics.items()
                if metrics.average_query_time > 0.1  # Slower than 100ms
            ]
            
            if slow_selectors:
                recommendations['selector_optimization'].append(
                    f"Consider optimizing slow selectors: {[s[0] for s in slow_selectors[:3]]}"
                )
            
            low_success_selectors = [
                (selector, metrics) for selector, metrics in self.performance_metrics.items()
                if metrics.success_rate < 0.5 and metrics.total_queries > 5
            ]
            
            if low_success_selectors:
                recommendations['selector_optimization'].append(
                    f"Review low-success selectors: {[s[0] for s in low_success_selectors[:3]]}"
                )
        
        # Performance recommendations
        if self.cache_strategy == CacheStrategy.CONSERVATIVE and hit_rate > 50:
            recommendations['performance_optimization'].append(
                "Consider upgrading to BALANCED caching strategy"
            )
        
        if not self.enable_prefetching and len(self.common_selectors) > 5:
            recommendations['performance_optimization'].append(
                "Consider enabling prefetching for common selectors"
            )
        
        return recommendations


# Global instances for different strategies
dom_cache_aggressive = DOMCacheOptimizer(CacheStrategy.AGGRESSIVE)
dom_cache_balanced = DOMCacheOptimizer(CacheStrategy.BALANCED)
dom_cache_conservative = DOMCacheOptimizer(CacheStrategy.CONSERVATIVE)

# Default instance
dom_cache = dom_cache_balanced