#!/usr/bin/env python3
"""
Performance-Optimized Landmark-Based Metadata Extractor

This module provides a high-performance implementation of landmark-based metadata
extraction with advanced caching, memory optimization, and parallel processing capabilities.
"""

import asyncio
import logging
import time
import weakref
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
import json
import re
import gc

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking for extraction operations"""
    extraction_count: int = 0
    total_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_peak: float = 0.0
    error_count: int = 0
    average_time: float = 0.0
    success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass 
class CachedElement:
    """Cached element information with TTL"""
    element_info: Any
    bounds: Optional[Dict[str, float]]
    text_content: Optional[str]
    timestamp: datetime
    access_count: int = 0
    ttl_seconds: int = 300  # 5 minutes default TTL
    
    def is_expired(self) -> bool:
        """Check if cached element has expired"""
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)
    
    def touch(self):
        """Update access time and count"""
        self.timestamp = datetime.now()
        self.access_count += 1


class SpatialCache:
    """High-performance spatial caching system for DOM elements"""
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 60):
        self.cache = OrderedDict()
        self.spatial_index = defaultdict(list)  # Spatial indexing by regions
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'cleanups': 0
        }
    
    def _get_spatial_key(self, bounds: Dict[str, float], grid_size: int = 100) -> str:
        """Generate spatial grid key for element bounds"""
        if not bounds:
            return "no_bounds"
        
        grid_x = int(bounds['x'] // grid_size)
        grid_y = int(bounds['y'] // grid_size)
        return f"{grid_x}:{grid_y}"
    
    async def get_elements_in_region(self, center_bounds: Dict[str, float], 
                                   radius: float = 200) -> List[Any]:
        """Get cached elements within radius of center point"""
        if not center_bounds:
            return []
        
        center_x = center_bounds['x'] + center_bounds['width'] / 2
        center_y = center_bounds['y'] + center_bounds['height'] / 2
        
        nearby_elements = []
        
        # Check multiple grid cells around the center
        grid_size = 100
        search_range = int(radius / grid_size) + 1
        
        for dx in range(-search_range, search_range + 1):
            for dy in range(-search_range, search_range + 1):
                grid_x = int(center_x // grid_size) + dx
                grid_y = int(center_y // grid_size) + dy
                spatial_key = f"{grid_x}:{grid_y}"
                
                for cache_key in self.spatial_index.get(spatial_key, []):
                    if cache_key in self.cache:
                        cached = self.cache[cache_key]
                        if not cached.is_expired():
                            if cached.bounds:
                                elem_x = cached.bounds['x'] + cached.bounds['width'] / 2
                                elem_y = cached.bounds['y'] + cached.bounds['height'] / 2
                                distance = ((elem_x - center_x) ** 2 + (elem_y - center_y) ** 2) ** 0.5
                                
                                if distance <= radius:
                                    cached.touch()
                                    nearby_elements.append(cached.element_info)
                                    self._stats['hits'] += 1
        
        return nearby_elements
    
    def put(self, key: str, element_info: Any, bounds: Optional[Dict[str, float]] = None,
            text_content: Optional[str] = None, ttl_seconds: int = 300):
        """Store element in cache with spatial indexing"""
        cached_element = CachedElement(
            element_info=element_info,
            bounds=bounds,
            text_content=text_content,
            timestamp=datetime.now(),
            ttl_seconds=ttl_seconds
        )
        
        # Add to main cache
        self.cache[key] = cached_element
        
        # Add to spatial index
        if bounds:
            spatial_key = self._get_spatial_key(bounds)
            if key not in self.spatial_index[spatial_key]:
                self.spatial_index[spatial_key].append(key)
        
        # Enforce size limit
        while len(self.cache) > self.max_size:
            oldest_key, _ = self.cache.popitem(last=False)
            self._remove_from_spatial_index(oldest_key)
            self._stats['evictions'] += 1
        
        # Periodic cleanup
        if time.time() - self.last_cleanup > self.cleanup_interval:
            asyncio.create_task(self._cleanup_expired())
    
    def get(self, key: str) -> Optional[CachedElement]:
        """Get cached element"""
        if key in self.cache:
            cached = self.cache[key]
            if not cached.is_expired():
                cached.touch()
                # Move to end (LRU)
                self.cache.move_to_end(key)
                self._stats['hits'] += 1
                return cached
            else:
                # Remove expired element
                del self.cache[key]
                self._remove_from_spatial_index(key)
        
        self._stats['misses'] += 1
        return None
    
    def _remove_from_spatial_index(self, key: str):
        """Remove element from spatial index"""
        for spatial_key, keys in self.spatial_index.items():
            if key in keys:
                keys.remove(key)
                if not keys:  # Remove empty spatial buckets
                    del self.spatial_index[spatial_key]
                break
    
    async def _cleanup_expired(self):
        """Clean up expired cache entries"""
        expired_keys = []
        current_time = datetime.now()
        
        for key, cached in self.cache.items():
            if cached.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            self._remove_from_spatial_index(key)
        
        self.last_cleanup = time.time()
        self._stats['cleanups'] += 1
        
        logger.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'spatial_buckets': len(self.spatial_index),
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            **self._stats
        }


class QueryOptimizer:
    """Optimizes DOM queries and reduces redundant operations"""
    
    def __init__(self):
        self.query_cache = {}
        self.selector_patterns = {
            'landmark_text': '*:has-text("{text}")',
            'aria_elements': '[aria-describedby]',
            'creation_time': 'span:contains("Creation Time")',
            'general_spans': 'span',
            'divs_with_content': 'div:not(:empty)'
        }
        self.batch_size = 50  # Process elements in batches
    
    def build_batch_query(self, selectors: List[str]) -> str:
        """Build optimized batch query for multiple selectors"""
        # Combine selectors with OR logic for single query
        return ', '.join(selectors)
    
    async def execute_parallel_queries(self, page, queries: Dict[str, str]) -> Dict[str, List]:
        """Execute multiple queries in parallel"""
        tasks = {}
        
        for query_name, selector in queries.items():
            tasks[query_name] = asyncio.create_task(
                page.query_selector_all(selector)
            )
        
        results = {}
        for query_name, task in tasks.items():
            try:
                results[query_name] = await task
            except Exception as e:
                logger.warning(f"Query '{query_name}' failed: {e}")
                results[query_name] = []
        
        return results
    
    def optimize_selector(self, selector: str, context: Dict[str, Any] = None) -> str:
        """Optimize CSS selector for better performance"""
        optimized = selector
        
        # Add performance optimizations
        if context and context.get('content_area'):
            # Restrict search to content area if available
            bounds = context['content_area']
            # This would require custom CSS or JavaScript to implement properly
            # For now, return original selector
            pass
        
        # Remove redundant descendant selectors
        optimized = re.sub(r'\s+>\s+', ' > ', optimized)
        optimized = re.sub(r'\s+', ' ', optimized).strip()
        
        return optimized


class PerformanceOptimizedExtractor:
    """High-performance metadata extractor with advanced optimizations"""
    
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        
        # Performance components
        self.cache = SpatialCache(max_size=2000, cleanup_interval=120)
        self.query_optimizer = QueryOptimizer()
        self.metrics = PerformanceMetrics()
        
        # Configuration
        self.enable_caching = getattr(config, 'enable_performance_caching', True)
        self.enable_parallel_queries = getattr(config, 'enable_parallel_queries', True)
        self.enable_batch_processing = getattr(config, 'enable_batch_processing', True)
        self.memory_limit_mb = getattr(config, 'memory_limit_mb', 100)
        
        # Object pools for memory efficiency
        self._element_pool = []
        self._result_pool = []
        
        # Performance monitoring
        self._start_time = None
        self._peak_memory = 0
        
        logger.info("Performance-optimized extractor initialized")
    
    async def extract_metadata_optimized(self, page) -> Dict[str, Any]:
        """Optimized metadata extraction with performance monitoring"""
        extraction_start = time.time()
        self._start_time = extraction_start
        
        try:
            # Monitor memory usage
            self._monitor_memory_usage()
            
            # Phase 1: Parallel element discovery
            elements_data = await self._parallel_element_discovery(page)
            
            # Phase 2: Cached spatial analysis
            spatial_context = await self._build_spatial_context(elements_data)
            
            # Phase 3: Optimized metadata extraction
            metadata = await self._extract_with_optimization(page, spatial_context)
            
            # Phase 4: Performance metrics update
            extraction_time = time.time() - extraction_start
            self._update_performance_metrics(extraction_time, True)
            
            # Add performance information to metadata
            metadata['performance_metrics'] = {
                'extraction_time': extraction_time,
                'cache_hit_rate': self.cache.get_stats()['hit_rate'],
                'memory_usage_mb': self._get_memory_usage(),
                'optimization_enabled': True
            }
            
            return metadata
            
        except Exception as e:
            extraction_time = time.time() - extraction_start
            self._update_performance_metrics(extraction_time, False)
            
            logger.error(f"Optimized extraction failed: {e}")
            return await self._fallback_extraction(page)
    
    async def _parallel_element_discovery(self, page) -> Dict[str, List]:
        """Discover elements in parallel with caching"""
        cache_key = f"page_elements_{hash(page.url) if hasattr(page, 'url') else 'unknown'}"
        
        # Check cache first
        if self.enable_caching:
            cached_elements = self.cache.get(cache_key)
            if cached_elements:
                logger.debug("Using cached element discovery")
                return json.loads(cached_elements.text_content)
        
        # Build parallel query batch
        queries = {
            'landmarks': self.query_optimizer.selector_patterns['landmark_text'].format(
                text=self.config.image_to_video_text
            ),
            'creation_time': self.query_optimizer.selector_patterns['landmark_text'].format(
                text=self.config.creation_time_text
            ),
            'aria_elements': self.query_optimizer.selector_patterns['aria_elements'],
            'spans': self.query_optimizer.selector_patterns['general_spans'],
            'content_divs': self.query_optimizer.selector_patterns['divs_with_content']
        }
        
        # Execute queries in parallel
        if self.enable_parallel_queries:
            results = await self.query_optimizer.execute_parallel_queries(page, queries)
        else:
            # Sequential fallback
            results = {}
            for name, query in queries.items():
                results[name] = await page.query_selector_all(query)
        
        # Process and cache results
        processed_results = {}
        for name, elements in results.items():
            processed_results[name] = await self._process_element_batch(elements[:50])  # Limit batch size
        
        # Cache the results
        if self.enable_caching:
            self.cache.put(
                cache_key, 
                processed_results,
                ttl_seconds=600  # Cache for 10 minutes
            )
        
        return processed_results
    
    async def _process_element_batch(self, elements: List) -> List[Dict[str, Any]]:
        """Process elements in optimized batches"""
        processed = []
        
        # Use thread pool for CPU-intensive operations
        if self.enable_batch_processing and len(elements) > 10:
            with ThreadPoolExecutor(max_workers=4) as executor:
                tasks = []
                
                for i in range(0, len(elements), self.query_optimizer.batch_size):
                    batch = elements[i:i + self.query_optimizer.batch_size]
                    task = asyncio.get_event_loop().run_in_executor(
                        executor, 
                        self._process_batch_sync, 
                        batch
                    )
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for batch_result in batch_results:
                    if not isinstance(batch_result, Exception):
                        processed.extend(batch_result)
        else:
            # Sequential processing for small batches
            for element in elements:
                try:
                    element_data = await self._get_element_data_optimized(element)
                    processed.append(element_data)
                except Exception as e:
                    logger.debug(f"Error processing element: {e}")
                    continue
        
        return processed
    
    def _process_batch_sync(self, batch: List) -> List[Dict[str, Any]]:
        """Synchronous batch processing for thread pool"""
        # This would contain synchronous element processing logic
        # For now, return placeholder data
        return [{'type': 'batch_processed', 'count': len(batch)}]
    
    async def _get_element_data_optimized(self, element) -> Dict[str, Any]:
        """Get element data with memory optimization"""
        # Reuse objects from pool when possible
        if self._element_pool:
            element_data = self._element_pool.pop()
            element_data.clear()
        else:
            element_data = {}
        
        try:
            # Get basic element information
            element_data['text'] = await element.text_content() or ""
            element_data['visible'] = await element.is_visible()
            
            # Only get bounds if element is visible (performance optimization)
            if element_data['visible']:
                element_data['bounds'] = await element.bounding_box()
            else:
                element_data['bounds'] = None
            
            # Cache commonly accessed attributes
            element_data['tag'] = await element.evaluate("el => el.tagName.toLowerCase()")
            
        except Exception as e:
            logger.debug(f"Error getting element data: {e}")
            # Return minimal data on error
            element_data = {'text': '', 'visible': False, 'bounds': None, 'tag': 'unknown'}
        
        return element_data
    
    async def _build_spatial_context(self, elements_data: Dict[str, List]) -> Dict[str, Any]:
        """Build spatial context with caching"""
        context = {
            'landmark_positions': [],
            'content_regions': [],
            'high_density_areas': []
        }
        
        # Process landmark positions
        for element_data in elements_data.get('landmarks', []):
            if element_data.get('bounds'):
                context['landmark_positions'].append(element_data['bounds'])
        
        # Identify high-density content areas
        all_bounds = []
        for elements in elements_data.values():
            for element_data in elements:
                if element_data.get('bounds') and element_data.get('visible'):
                    all_bounds.append(element_data['bounds'])
        
        # Simple clustering algorithm to find dense areas
        if len(all_bounds) > 10:
            context['high_density_areas'] = self._find_dense_regions(all_bounds)
        
        return context
    
    def _find_dense_regions(self, bounds_list: List[Dict[str, float]], 
                           grid_size: int = 100) -> List[Dict[str, Any]]:
        """Find regions with high element density"""
        density_map = defaultdict(int)
        
        for bounds in bounds_list:
            grid_x = int(bounds['x'] // grid_size)
            grid_y = int(bounds['y'] // grid_size)
            density_map[(grid_x, grid_y)] += 1
        
        # Find regions with density above threshold
        threshold = max(2, len(bounds_list) // 20)  # At least 5% of elements
        dense_regions = []
        
        for (grid_x, grid_y), density in density_map.items():
            if density >= threshold:
                dense_regions.append({
                    'x': grid_x * grid_size,
                    'y': grid_y * grid_size,
                    'width': grid_size,
                    'height': grid_size,
                    'density': density
                })
        
        return dense_regions
    
    async def _extract_with_optimization(self, page, spatial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata using optimized strategies"""
        metadata = {
            'generation_date': 'Unknown Date',
            'prompt': 'Unknown Prompt',
            'extraction_method': 'performance_optimized',
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        # Strategy 1: Use spatial context for targeted extraction
        if spatial_context['landmark_positions']:
            # Focus on areas near landmarks
            target_regions = spatial_context['landmark_positions'][:3]  # Top 3 landmarks
            
            for region in target_regions:
                # Extract from cached nearby elements
                nearby_elements = await self.cache.get_elements_in_region(region, radius=300)
                
                if nearby_elements:
                    # Fast extraction using cached elements
                    date_result = await self._fast_date_extraction(nearby_elements)
                    if date_result and metadata['generation_date'] == 'Unknown Date':
                        metadata['generation_date'] = date_result
                    
                    prompt_result = await self._fast_prompt_extraction(nearby_elements)
                    if prompt_result and metadata['prompt'] == 'Unknown Prompt':
                        metadata['prompt'] = prompt_result
                
                # Break early if we found both fields
                if (metadata['generation_date'] != 'Unknown Date' and 
                    metadata['prompt'] != 'Unknown Prompt'):
                    break
        
        # Strategy 2: High-density area scanning
        if (metadata['generation_date'] == 'Unknown Date' or 
            metadata['prompt'] == 'Unknown Prompt'):
            
            for dense_area in spatial_context['high_density_areas'][:2]:  # Top 2 dense areas
                area_elements = await self.cache.get_elements_in_region(dense_area, radius=150)
                
                if area_elements and metadata['generation_date'] == 'Unknown Date':
                    metadata['generation_date'] = await self._fast_date_extraction(area_elements) or metadata['generation_date']
                
                if area_elements and metadata['prompt'] == 'Unknown Prompt':
                    metadata['prompt'] = await self._fast_prompt_extraction(area_elements) or metadata['prompt']
        
        return metadata
    
    async def _fast_date_extraction(self, cached_elements: List) -> Optional[str]:
        """Fast date extraction using cached element data"""
        for element_data in cached_elements:
            if hasattr(element_data, 'text_content') and element_data.text_content:
                text = element_data.text_content
                
                # Quick date pattern matching
                date_patterns = [
                    r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}',  # "24 Aug 2025 01:37:01"
                    r'\d{4}-\d{1,2}-\d{1,2}',  # "2025-08-24"
                    r'\d{1,2}/\d{1,2}/\d{4}',  # "24/08/2025"
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text)
                    if match:
                        return match.group(0).strip()
        
        return None
    
    async def _fast_prompt_extraction(self, cached_elements: List) -> Optional[str]:
        """Fast prompt extraction using cached element data"""
        for element_data in cached_elements:
            if (hasattr(element_data, 'text_content') and 
                element_data.text_content and 
                len(element_data.text_content) > 20):
                
                text = element_data.text_content.strip()
                
                # Quick quality check
                if (len(text) > 30 and 
                    not text.lower().startswith(('image to video', 'creation time', 'download')) and
                    '...' not in text):
                    return text
        
        return None
    
    async def _fallback_extraction(self, page) -> Dict[str, Any]:
        """Fallback extraction when optimization fails"""
        logger.warning("Using fallback extraction due to optimization failure")
        
        # Import and use the original extractor
        try:
            from .enhanced_metadata_extractor import EnhancedMetadataExtractor
            fallback_extractor = EnhancedMetadataExtractor(self.config, self.debug_logger)
            return await fallback_extractor.extract_metadata_from_page(page)
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {e}")
            return {
                'generation_date': 'Unknown Date',
                'prompt': 'Unknown Prompt',
                'extraction_method': 'fallback_failed',
                'error': str(e)
            }
    
    def _monitor_memory_usage(self):
        """Monitor memory usage during extraction"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self._peak_memory:
                self._peak_memory = memory_mb
                
            # Trigger cleanup if memory usage is high
            if memory_mb > self.memory_limit_mb:
                self._cleanup_memory()
                
        except ImportError:
            # psutil not available, skip memory monitoring
            pass
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _cleanup_memory(self):
        """Perform memory cleanup"""
        # Return objects to pools
        self._element_pool.clear()
        self._result_pool.clear()
        
        # Force garbage collection
        gc.collect()
        
        # Clear old cache entries
        asyncio.create_task(self.cache._cleanup_expired())
        
        logger.debug("Memory cleanup performed")
    
    def _update_performance_metrics(self, extraction_time: float, success: bool):
        """Update performance metrics"""
        self.metrics.extraction_count += 1
        self.metrics.total_time += extraction_time
        self.metrics.average_time = self.metrics.total_time / self.metrics.extraction_count
        
        if not success:
            self.metrics.error_count += 1
        
        self.metrics.success_rate = (
            (self.metrics.extraction_count - self.metrics.error_count) / 
            self.metrics.extraction_count * 100
        )
        
        if self._peak_memory > self.metrics.memory_peak:
            self.metrics.memory_peak = self._peak_memory
        
        self.metrics.last_updated = datetime.now()
        
        # Update cache stats
        cache_stats = self.cache.get_stats()
        self.metrics.cache_hits = cache_stats['hits']
        self.metrics.cache_misses = cache_stats['misses']
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        cache_stats = self.cache.get_stats()
        
        return {
            'extraction_metrics': {
                'total_extractions': self.metrics.extraction_count,
                'average_time_ms': round(self.metrics.average_time * 1000, 2),
                'success_rate': round(self.metrics.success_rate, 2),
                'total_time_seconds': round(self.metrics.total_time, 2)
            },
            'cache_performance': cache_stats,
            'memory_usage': {
                'peak_mb': round(self.metrics.memory_peak, 2),
                'current_mb': round(self._get_memory_usage(), 2),
                'limit_mb': self.memory_limit_mb
            },
            'optimization_status': {
                'caching_enabled': self.enable_caching,
                'parallel_queries_enabled': self.enable_parallel_queries,
                'batch_processing_enabled': self.enable_batch_processing
            },
            'last_updated': self.metrics.last_updated.isoformat()
        }
    
    def reset_performance_metrics(self):
        """Reset all performance metrics"""
        self.metrics = PerformanceMetrics()
        self.cache = SpatialCache(max_size=2000, cleanup_interval=120)
        self._peak_memory = 0
        logger.info("Performance metrics reset")