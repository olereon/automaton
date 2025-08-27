#!/usr/bin/env python3
"""
Optimized Integration Layer

This module provides a unified integration layer that combines all performance
optimizations, caching strategies, error handling, and scalability features
into a seamless, production-ready metadata extraction system.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

# Import all optimization components
from .performance_optimized_extractor import PerformanceOptimizedExtractor, SpatialCache
from .optimized_selector_chains import SelectorChainOptimizer, FallbackChainManager, SelectorStrategy
from .robust_error_handling import RobustErrorHandler, ErrorSeverity, RecoveryStrategy, with_error_handling
from .scalable_extraction_engine import ScalableExtractionEngine, ProcessingMode, create_scalable_engine
from .enhanced_metadata_extractor import EnhancedMetadataExtractor, LegacyCompatibilityWrapper

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Optimization levels for different use cases"""
    BASIC = "basic"                    # Essential optimizations only
    STANDARD = "standard"              # Balanced optimization and compatibility
    PERFORMANCE = "performance"        # Maximum performance optimizations
    ENTERPRISE = "enterprise"          # Full enterprise features
    CUSTOM = "custom"                  # User-defined configuration


@dataclass
class OptimizationConfig:
    """Configuration for the optimization system"""
    level: OptimizationLevel = OptimizationLevel.STANDARD
    
    # Performance settings
    enable_caching: bool = True
    cache_size: int = 2000
    cache_ttl_seconds: int = 300
    enable_parallel_queries: bool = True
    enable_batch_processing: bool = True
    memory_limit_mb: int = 100
    
    # Error handling settings
    enable_error_recovery: bool = True
    max_retries: int = 3
    enable_circuit_breaker: bool = True
    enable_pattern_analysis: bool = True
    
    # Scalability settings
    processing_mode: ProcessingMode = ProcessingMode.MULTI_THREADED
    max_workers: int = 8
    concurrent_workers: int = 4
    max_queue_size: int = 5000
    
    # Selector optimization settings
    selector_strategy: SelectorStrategy = SelectorStrategy.ADAPTIVE
    enable_selector_optimization: bool = True
    enable_fallback_chains: bool = True
    
    # Backward compatibility
    legacy_compatible: bool = True
    fallback_to_legacy: bool = True
    quality_threshold: float = 0.6
    
    @classmethod
    def for_level(cls, level: OptimizationLevel) -> 'OptimizationConfig':
        """Create configuration for specific optimization level"""
        if level == OptimizationLevel.BASIC:
            return cls(
                level=level,
                enable_caching=True,
                enable_parallel_queries=False,
                enable_batch_processing=False,
                enable_error_recovery=True,
                max_retries=2,
                enable_circuit_breaker=False,
                processing_mode=ProcessingMode.SINGLE_THREADED,
                max_workers=2,
                concurrent_workers=1
            )
        
        elif level == OptimizationLevel.STANDARD:
            return cls(level=level)  # Use defaults
        
        elif level == OptimizationLevel.PERFORMANCE:
            return cls(
                level=level,
                cache_size=5000,
                cache_ttl_seconds=600,
                enable_batch_processing=True,
                memory_limit_mb=200,
                max_retries=2,  # Fast fail for performance
                processing_mode=ProcessingMode.MULTI_THREADED,
                max_workers=16,
                concurrent_workers=8,
                selector_strategy=SelectorStrategy.PRECISE
            )
        
        elif level == OptimizationLevel.ENTERPRISE:
            return cls(
                level=level,
                cache_size=10000,
                cache_ttl_seconds=1200,
                memory_limit_mb=500,
                enable_pattern_analysis=True,
                processing_mode=ProcessingMode.HYBRID,
                max_workers=32,
                concurrent_workers=12,
                max_queue_size=20000,
                selector_strategy=SelectorStrategy.ADAPTIVE
            )
        
        else:
            return cls(level=level)


class OptimizedMetadataExtractor:
    """
    Unified optimized metadata extractor that integrates all performance
    enhancements and provides a simple interface for various use cases.
    """
    
    def __init__(self, config, optimization_config: OptimizationConfig = None, debug_logger=None):
        self.config = config
        self.optimization_config = optimization_config or OptimizationConfig.for_level(OptimizationLevel.STANDARD)
        self.debug_logger = debug_logger
        
        # Initialize core components based on optimization level
        self._initialize_components()
        
        # Performance tracking
        self.performance_metrics = {
            'extractions_performed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors_handled': 0,
            'fallbacks_used': 0,
            'average_extraction_time': 0.0,
            'total_extraction_time': 0.0
        }
        
        logger.info(f"Optimized extractor initialized with {self.optimization_config.level.value} optimization level")
    
    def _initialize_components(self):
        """Initialize optimization components based on configuration"""
        opt_config = self.optimization_config
        
        # Performance optimized extractor
        if opt_config.level != OptimizationLevel.BASIC:
            self.performance_extractor = PerformanceOptimizedExtractor(self.config, self.debug_logger)
            # Configure performance settings
            self.performance_extractor.enable_caching = opt_config.enable_caching
            self.performance_extractor.enable_parallel_queries = opt_config.enable_parallel_queries
            self.performance_extractor.enable_batch_processing = opt_config.enable_batch_processing
            self.performance_extractor.memory_limit_mb = opt_config.memory_limit_mb
        else:
            self.performance_extractor = None
        
        # Error handler
        if opt_config.enable_error_recovery:
            error_handler_config = {
                'default_retry_count': opt_config.max_retries,
                'enable_circuit_breaker': opt_config.enable_circuit_breaker,
                'enable_pattern_analysis': opt_config.enable_pattern_analysis
            }
            self.error_handler = RobustErrorHandler(error_handler_config)
        else:
            self.error_handler = None
        
        # Selector chain optimizer
        if opt_config.enable_selector_optimization:
            self.selector_optimizer = SelectorChainOptimizer()
            if opt_config.enable_fallback_chains:
                self.fallback_manager = FallbackChainManager(self.config)
            else:
                self.fallback_manager = None
        else:
            self.selector_optimizer = None
            self.fallback_manager = None
        
        # Scalable engine (for high-volume scenarios)
        if opt_config.level == OptimizationLevel.ENTERPRISE:
            scale_config = {
                'processing_mode': opt_config.processing_mode.value,
                'max_workers': opt_config.max_workers,
                'concurrent_workers': opt_config.concurrent_workers,
                'max_queue_size': opt_config.max_queue_size
            }
            self.scalable_engine = ScalableExtractionEngine(scale_config)
        else:
            self.scalable_engine = None
        
        # Legacy compatibility
        if opt_config.legacy_compatible:
            # Configure enhanced extractor with compatibility settings
            self.config.use_landmark_extraction = True
            self.config.fallback_to_legacy = opt_config.fallback_to_legacy
            self.config.quality_threshold = opt_config.quality_threshold
            
            self.legacy_extractor = EnhancedMetadataExtractor(self.config, self.debug_logger)
        else:
            self.legacy_extractor = None
    
    async def extract_metadata(self, page) -> Dict[str, Any]:
        """
        Main extraction method with full optimization pipeline
        """
        extraction_start = time.time()
        
        try:
            # Choose extraction method based on optimization level
            if self.optimization_config.level == OptimizationLevel.BASIC:
                result = await self._basic_extraction(page)
            
            elif self.optimization_config.level in [OptimizationLevel.STANDARD, OptimizationLevel.PERFORMANCE]:
                result = await self._optimized_extraction(page)
            
            elif self.optimization_config.level == OptimizationLevel.ENTERPRISE:
                result = await self._enterprise_extraction(page)
            
            else:
                result = await self._custom_extraction(page)
            
            # Update performance metrics
            extraction_time = time.time() - extraction_start
            self._update_performance_metrics(extraction_time, True, result)
            
            # Add optimization metadata
            result['optimization_info'] = {
                'level': self.optimization_config.level.value,
                'extraction_time_ms': round(extraction_time * 1000, 2),
                'optimizations_used': self._get_active_optimizations(),
                'performance_score': self._calculate_performance_score(extraction_time, result)
            }
            
            return result
            
        except Exception as e:
            extraction_time = time.time() - extraction_start
            self._update_performance_metrics(extraction_time, False, None)
            
            # Handle with error recovery if available
            if self.error_handler:
                logger.warning(f"Extraction failed, attempting recovery: {e}")
                return await self._handle_extraction_error(page, e, extraction_start)
            else:
                logger.error(f"Extraction failed without recovery: {e}")
                return self._create_error_result(str(e), extraction_start)
    
    async def _basic_extraction(self, page) -> Dict[str, Any]:
        """Basic extraction with minimal optimizations"""
        if self.legacy_extractor:
            return await self.legacy_extractor.extract_metadata_from_page(page)
        else:
            # Fallback to very basic extraction
            return {
                'generation_date': 'Unknown Date',
                'prompt': 'Unknown Prompt',
                'extraction_method': 'basic_fallback',
                'extraction_timestamp': datetime.now().isoformat()
            }
    
    async def _optimized_extraction(self, page) -> Dict[str, Any]:
        """Standard/Performance optimized extraction"""
        if self.performance_extractor:
            # Try performance-optimized extraction first
            try:
                result = await self.performance_extractor.extract_metadata_optimized(page)
                
                # Check quality and fallback if needed
                quality_score = result.get('performance_metrics', {}).get('cache_hit_rate', 0) / 100
                
                if (quality_score < self.optimization_config.quality_threshold and 
                    self.optimization_config.fallback_to_legacy and 
                    self.legacy_extractor):
                    
                    logger.info(f"Quality score {quality_score:.2f} below threshold, using legacy fallback")
                    fallback_result = await self.legacy_extractor.extract_metadata_from_page(page)
                    
                    # Merge results, preferring non-unknown values
                    merged_result = self._merge_extraction_results(result, fallback_result)
                    merged_result['extraction_method'] = 'optimized_with_legacy_fallback'
                    return merged_result
                
                return result
                
            except Exception as e:
                logger.warning(f"Performance extraction failed: {e}")
                
                if self.legacy_extractor and self.optimization_config.fallback_to_legacy:
                    return await self.legacy_extractor.extract_metadata_from_page(page)
                else:
                    raise
        
        # Fallback to legacy extractor
        if self.legacy_extractor:
            return await self.legacy_extractor.extract_metadata_from_page(page)
        else:
            raise ValueError("No extraction method available")
    
    async def _enterprise_extraction(self, page) -> Dict[str, Any]:
        """Enterprise-level extraction with full optimization stack"""
        # For enterprise, we can use the scalable engine for batch processing
        # or direct optimized extraction for single page
        
        if hasattr(page, 'url'):
            page_url = page.url
        else:
            page_url = "unknown_page"
        
        # Create extraction task for enterprise processing
        if self.scalable_engine and not self.scalable_engine.is_running:
            # For single extraction, use direct optimized method
            return await self._optimized_extraction(page)
        
        # Use performance-optimized extraction with full error handling
        if self.performance_extractor and self.error_handler:
            
            @with_error_handling("enterprise_extraction", max_retries=2)
            async def extract_with_recovery():
                return await self.performance_extractor.extract_metadata_optimized(page)
            
            result = await extract_with_recovery()
            
            if result:
                return result
            else:
                # Final fallback
                if self.legacy_extractor:
                    return await self.legacy_extractor.extract_metadata_from_page(page)
                else:
                    return self._create_error_result("All extraction methods failed", time.time())
        
        # Fallback chain
        return await self._optimized_extraction(page)
    
    async def _custom_extraction(self, page) -> Dict[str, Any]:
        """Custom extraction based on specific configuration"""
        # This would implement custom extraction logic based on user configuration
        return await self._optimized_extraction(page)
    
    async def _handle_extraction_error(self, page, error: Exception, start_time: float) -> Dict[str, Any]:
        """Handle extraction error with recovery mechanisms"""
        if not self.error_handler:
            return self._create_error_result(str(error), start_time)
        
        async def recovery_extraction():
            # Try different extraction approaches
            if self.legacy_extractor:
                return await self.legacy_extractor.extract_metadata_from_page(page)
            else:
                return self._create_error_result("No fallback available", start_time)
        
        result, error_context = await self.error_handler.execute_with_recovery(
            recovery_extraction,
            "extraction_recovery",
            max_retries=1
        )
        
        if result:
            result['recovery_info'] = {
                'original_error': str(error),
                'recovery_successful': True,
                'error_context': error_context.to_dict() if error_context else None
            }
            return result
        else:
            return self._create_error_result(str(error), start_time, error_context)
    
    def _merge_extraction_results(self, primary: Dict[str, Any], 
                                 secondary: Dict[str, Any]) -> Dict[str, Any]:
        """Merge extraction results, preferring non-unknown values from primary"""
        merged = primary.copy()
        
        # Merge key fields, preferring known values
        key_fields = ['generation_date', 'prompt']
        
        for field in key_fields:
            primary_value = primary.get(field, '')
            secondary_value = secondary.get(field, '')
            
            # If primary has unknown value but secondary has known value, use secondary
            if (primary_value in ['Unknown Date', 'Unknown Prompt', ''] and 
                secondary_value not in ['Unknown Date', 'Unknown Prompt', '']):
                merged[field] = secondary_value
        
        # Add merge metadata
        merged['merge_info'] = {
            'primary_method': primary.get('extraction_method', 'unknown'),
            'secondary_method': secondary.get('extraction_method', 'unknown'),
            'fields_from_secondary': [
                field for field in key_fields 
                if merged.get(field) == secondary.get(field)
            ]
        }
        
        return merged
    
    def _create_error_result(self, error_message: str, start_time: float, 
                           error_context=None) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            'generation_date': 'Unknown Date',
            'prompt': 'Unknown Prompt',
            'extraction_method': 'error_fallback',
            'extraction_timestamp': datetime.now().isoformat(),
            'extraction_time_ms': round((time.time() - start_time) * 1000, 2),
            'error': error_message,
            'error_context': error_context.to_dict() if error_context else None,
            'optimization_info': {
                'level': self.optimization_config.level.value,
                'extraction_failed': True
            }
        }
    
    def _update_performance_metrics(self, extraction_time: float, success: bool, result: Dict[str, Any]):
        """Update performance tracking metrics"""
        self.performance_metrics['extractions_performed'] += 1
        self.performance_metrics['total_extraction_time'] += extraction_time
        
        if self.performance_metrics['extractions_performed'] > 0:
            self.performance_metrics['average_extraction_time'] = (
                self.performance_metrics['total_extraction_time'] / 
                self.performance_metrics['extractions_performed']
            )
        
        if not success:
            self.performance_metrics['errors_handled'] += 1
        
        # Update cache metrics if available
        if result and 'performance_metrics' in result:
            perf_data = result['performance_metrics']
            if 'cache_hit_rate' in perf_data:
                # This is simplified - real implementation would track hits/misses
                self.performance_metrics['cache_hits'] += 1
        
        # Check if fallback was used
        if result and 'fallback' in result.get('extraction_method', ''):
            self.performance_metrics['fallbacks_used'] += 1
    
    def _get_active_optimizations(self) -> List[str]:
        """Get list of active optimization features"""
        optimizations = []
        
        if self.optimization_config.enable_caching:
            optimizations.append('spatial_caching')
        
        if self.optimization_config.enable_parallel_queries:
            optimizations.append('parallel_queries')
        
        if self.optimization_config.enable_batch_processing:
            optimizations.append('batch_processing')
        
        if self.optimization_config.enable_error_recovery:
            optimizations.append('error_recovery')
        
        if self.optimization_config.enable_circuit_breaker:
            optimizations.append('circuit_breaker')
        
        if self.optimization_config.enable_selector_optimization:
            optimizations.append('selector_optimization')
        
        if self.optimization_config.enable_fallback_chains:
            optimizations.append('fallback_chains')
        
        if self.scalable_engine:
            optimizations.append('scalable_processing')
        
        return optimizations
    
    def _calculate_performance_score(self, extraction_time: float, result: Dict[str, Any]) -> float:
        """Calculate performance score (0.0 to 1.0)"""
        # Base score from extraction time (lower is better)
        time_score = max(0.0, 1.0 - (extraction_time / 5.0))  # 5 seconds = 0 score
        
        # Quality score from result
        quality_score = 0.5  # Default
        
        if result:
            # Check if we got meaningful data
            if (result.get('generation_date', 'Unknown Date') != 'Unknown Date' and
                result.get('prompt', 'Unknown Prompt') != 'Unknown Prompt'):
                quality_score = 0.8
            
            # Bonus for cache hit
            if 'cache_hit_rate' in result.get('performance_metrics', {}):
                cache_hit_rate = result['performance_metrics']['cache_hit_rate'] / 100
                quality_score = min(1.0, quality_score + (cache_hit_rate * 0.2))
        
        # Combined score
        return (time_score * 0.6 + quality_score * 0.4)
    
    async def extract_batch(self, pages: List[Any], 
                           batch_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Extract metadata from multiple pages efficiently"""
        if self.scalable_engine and len(pages) > 5:
            # Use scalable engine for large batches
            return await self._extract_batch_scalable(pages, batch_config or {})
        else:
            # Use concurrent processing for smaller batches
            return await self._extract_batch_concurrent(pages, batch_config or {})
    
    async def _extract_batch_scalable(self, pages: List[Any], 
                                    config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract batch using scalable engine"""
        if not self.scalable_engine.is_running:
            await self.scalable_engine.start()
        
        # Submit tasks
        task_ids = []
        for page in pages:
            page_url = getattr(page, 'url', 'unknown')
            task_id = await self.scalable_engine.submit_task(
                page_url=page_url,
                extraction_config=config,
                priority=config.get('priority', 5)
            )
            task_ids.append(task_id)
        
        # Wait for results
        results = []
        max_wait_time = config.get('timeout', 300)  # 5 minutes default
        start_time = time.time()
        
        while len(results) < len(task_ids) and (time.time() - start_time) < max_wait_time:
            for task_id in task_ids:
                if task_id not in [r.get('task_id') for r in results]:
                    result = await self.scalable_engine.get_task_result(task_id)
                    if result:
                        results.append(result)
            
            await asyncio.sleep(0.5)  # Brief pause between checks
        
        return results
    
    async def _extract_batch_concurrent(self, pages: List[Any], 
                                      config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract batch using concurrent processing"""
        max_concurrent = min(len(pages), config.get('max_concurrent', 4))
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_single(page):
            async with semaphore:
                return await self.extract_metadata(page)
        
        tasks = [extract_single(page) for page in pages]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(self._create_error_result(
                    str(result), 
                    time.time(),
                    None
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        report = {
            'optimization_level': self.optimization_config.level.value,
            'performance_metrics': self.performance_metrics.copy(),
            'optimization_config': {
                'caching_enabled': self.optimization_config.enable_caching,
                'parallel_queries_enabled': self.optimization_config.enable_parallel_queries,
                'error_recovery_enabled': self.optimization_config.enable_error_recovery,
                'scalable_processing_available': self.scalable_engine is not None
            }
        }
        
        # Add component-specific reports
        if self.performance_extractor:
            report['performance_extractor'] = self.performance_extractor.get_performance_report()
        
        if self.error_handler:
            report['error_handler'] = self.error_handler.get_error_statistics()
        
        if self.scalable_engine:
            report['scalable_engine'] = self.scalable_engine.get_engine_statistics()
        
        if self.fallback_manager:
            report['fallback_manager'] = self.fallback_manager.get_performance_report()
        
        return report
    
    async def shutdown(self):
        """Shutdown all components gracefully"""
        if self.scalable_engine and self.scalable_engine.is_running:
            await self.scalable_engine.stop()
        
        logger.info("Optimized metadata extractor shutdown complete")


# Factory functions for common use cases
def create_basic_extractor(config, debug_logger=None) -> OptimizedMetadataExtractor:
    """Create basic extractor for simple use cases"""
    opt_config = OptimizationConfig.for_level(OptimizationLevel.BASIC)
    return OptimizedMetadataExtractor(config, opt_config, debug_logger)


def create_standard_extractor(config, debug_logger=None) -> OptimizedMetadataExtractor:
    """Create standard extractor with balanced optimizations"""
    opt_config = OptimizationConfig.for_level(OptimizationLevel.STANDARD)
    return OptimizedMetadataExtractor(config, opt_config, debug_logger)


def create_performance_extractor(config, debug_logger=None) -> OptimizedMetadataExtractor:
    """Create performance-optimized extractor"""
    opt_config = OptimizationConfig.for_level(OptimizationLevel.PERFORMANCE)
    return OptimizedMetadataExtractor(config, opt_config, debug_logger)


def create_enterprise_extractor(config, debug_logger=None) -> OptimizedMetadataExtractor:
    """Create enterprise-grade extractor with all features"""
    opt_config = OptimizationConfig.for_level(OptimizationLevel.ENTERPRISE)
    return OptimizedMetadataExtractor(config, opt_config, debug_logger)


def create_custom_extractor(config, optimization_config: OptimizationConfig, 
                           debug_logger=None) -> OptimizedMetadataExtractor:
    """Create extractor with custom optimization configuration"""
    return OptimizedMetadataExtractor(config, optimization_config, debug_logger)


# Context manager for automatic resource management
class OptimizedExtractionContext:
    """Context manager for optimized extraction with automatic cleanup"""
    
    def __init__(self, config, optimization_level: OptimizationLevel = OptimizationLevel.STANDARD,
                 debug_logger=None):
        self.config = config
        self.optimization_level = optimization_level
        self.debug_logger = debug_logger
        self.extractor = None
    
    async def __aenter__(self):
        opt_config = OptimizationConfig.for_level(self.optimization_level)
        self.extractor = OptimizedMetadataExtractor(self.config, opt_config, self.debug_logger)
        return self.extractor
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.extractor:
            await self.extractor.shutdown()
        return False