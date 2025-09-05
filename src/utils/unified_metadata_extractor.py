"""
Unified Metadata Extractor - Phase 2 Optimization
Consolidates 8+ extraction files into single intelligent system

Performance Target: 3-5 seconds saved per extraction
Code Reduction: 4,000+ lines consolidated from multiple files:
- enhanced_metadata_extraction.py (245 lines)
- enhanced_metadata_extractor.py (458 lines) 
- performance_optimized_extractor.py (702 lines)
- scalable_extraction_engine.py (897 lines)
- extraction_strategies.py
- landmark_extractor.py
- metadata_extraction_debugger.py
- relative_prompt_extractor.py (keep separate for specialized use)
"""

import asyncio
import time
import re
import json
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ExtractionStrategy(Enum):
    """Unified extraction strategies ordered by performance"""
    RELATIVE_POSITIONING = "relative_positioning"      # Fastest - structure-based
    LONGEST_DIV = "longest_div"                       # Fast - content-length based  
    ENHANCED_SELECTORS = "enhanced_selectors"         # Medium - multiple CSS selectors
    FALLBACK_PATTERNS = "fallback_patterns"          # Slow - regex pattern matching
    COMPREHENSIVE_SCAN = "comprehensive_scan"         # Slowest - full DOM traversal


class ExtractionType(Enum):
    """Types of metadata to extract"""
    PROMPT = "prompt"
    CREATION_DATE = "creation_date"
    GENERATION_ID = "generation_id"
    MEDIA_TYPE = "media_type"
    QUALITY_SETTING = "quality_setting"
    ALL_METADATA = "all_metadata"


@dataclass
class ExtractionResult:
    """Standardized extraction result"""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    strategy_used: Optional[ExtractionStrategy] = None
    extraction_time: float = 0.0
    confidence_score: float = 0.0
    error_message: Optional[str] = None
    debug_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyPerformanceMetrics:
    """Track strategy performance for intelligent selection"""
    strategy: ExtractionStrategy
    success_rate: float = 0.0
    average_time: float = 0.0
    average_confidence: float = 0.0
    total_attempts: int = 0
    successful_extractions: int = 0
    last_used: float = 0.0


class UnifiedMetadataExtractor:
    """
    Consolidated metadata extraction system that replaces multiple extraction files
    with intelligent, performance-optimized extraction strategies
    
    Replaces and consolidates:
    - enhanced_metadata_extraction.py
    - enhanced_metadata_extractor.py  
    - performance_optimized_extractor.py
    - scalable_extraction_engine.py
    - extraction_strategies.py
    - landmark_extractor.py
    - metadata_extraction_debugger.py
    """
    
    def __init__(self):
        self.strategy_metrics: Dict[ExtractionStrategy, StrategyPerformanceMetrics] = {}
        self.initialize_performance_tracking()
        
        # Configuration
        self.enable_debugging = False
        self.min_prompt_length = 50
        self.max_prompt_length = 2000
        self.confidence_threshold = 0.7
        
        # Selector patterns (consolidated from multiple files)
        self.prompt_selectors = [
            '.sc-eKQYOU.bdGRCs span[aria-describedby]',  # Current primary
            '.sc-jJRqov.cxtNJi span[aria-describedby]',  # Legacy fallback
            '.sc-fileXT.gEIKhI span[aria-describedby]',
            'span[aria-describedby]',
            '[class*="prompt"] span',
            '[class*="text"] span'
        ]
        
        self.date_selectors = [
            '.sc-hAYgFD.fLPdud',  # Primary date selector
            '.sc-fKKGCA.dVzKiI span:last-child',  # Alternative date location
            '[class*="date"]',
            '[class*="time"]'
        ]
        
        self.container_selectors = [
            '.sc-fileXT.gEIKhI',     # Prompt container
            '.sc-fKKGCA.dVzKiI',     # Metadata container
            '[class*="container"]',
            '[class*="info"]',
            '[class*="details"]'
        ]
        
        # Pattern matching (from extraction_strategies.py)
        self.date_patterns = [
            r'\d{2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}',  # "05 Sep 2025 06:41:43"
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',       # "2025-09-05 06:41:43"  
            r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}', # "9/5/2025 6:41:43"
        ]
        
        self.prompt_indicators = [
            'camera', 'scene', 'shot', 'frame', 'view', 'angle', 'light', 
            'shows', 'reveals', 'captures', 'depicts', 'begins', 'moves'
        ]
        
        # Performance optimization
        self.extraction_cache: Dict[str, ExtractionResult] = {}
        self.cache_ttl = 30  # seconds
        
    def initialize_performance_tracking(self):
        """Initialize performance tracking for all strategies"""
        for strategy in ExtractionStrategy:
            self.strategy_metrics[strategy] = StrategyPerformanceMetrics(strategy=strategy)
    
    async def extract_metadata(self, 
                             page,
                             container=None,
                             extraction_type: ExtractionType = ExtractionType.ALL_METADATA,
                             preferred_strategy: Optional[ExtractionStrategy] = None) -> ExtractionResult:
        """
        Unified entry point for all metadata extraction
        
        Args:
            page: Playwright page object or container element
            container: Specific container to extract from (optional)
            extraction_type: What type of metadata to extract
            preferred_strategy: Override automatic strategy selection
            
        Returns:
            ExtractionResult with extracted metadata and performance info
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(page, container, extraction_type)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Select optimal strategy
        strategy = preferred_strategy or self._select_optimal_strategy(extraction_type)
        
        try:
            result = await self._execute_extraction_strategy(
                strategy, page, container, extraction_type
            )
            
            # Update performance metrics
            execution_time = time.time() - start_time
            self._update_strategy_metrics(strategy, result.success, execution_time, result.confidence_score)
            
            result.extraction_time = execution_time
            result.strategy_used = strategy
            
            # Cache successful results
            if result.success and result.confidence_score > self.confidence_threshold:
                self._add_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_strategy_metrics(strategy, False, execution_time, 0.0)
            
            return ExtractionResult(
                success=False,
                strategy_used=strategy,
                extraction_time=execution_time,
                error_message=str(e)
            )
    
    def _select_optimal_strategy(self, extraction_type: ExtractionType) -> ExtractionStrategy:
        """
        Intelligently select extraction strategy based on performance history and context
        
        Args:
            extraction_type: Type of metadata being extracted
            
        Returns:
            Optimal ExtractionStrategy for current context
        """
        # Get strategies sorted by performance
        strategies_by_performance = sorted(
            self.strategy_metrics.items(),
            key=lambda x: (x[1].success_rate * x[1].average_confidence, -x[1].average_time),
            reverse=True
        )
        
        # For prompt extraction, prefer structural approaches
        if extraction_type == ExtractionType.PROMPT:
            structural_strategies = [
                ExtractionStrategy.RELATIVE_POSITIONING,
                ExtractionStrategy.LONGEST_DIV,
                ExtractionStrategy.ENHANCED_SELECTORS
            ]
            
            for strategy in structural_strategies:
                metrics = self.strategy_metrics[strategy]
                if metrics.total_attempts > 0 and metrics.success_rate > 0.5:
                    return strategy
        
        # For date extraction, prefer selector-based approaches
        elif extraction_type == ExtractionType.CREATION_DATE:
            selector_strategies = [
                ExtractionStrategy.ENHANCED_SELECTORS,
                ExtractionStrategy.FALLBACK_PATTERNS,
                ExtractionStrategy.RELATIVE_POSITIONING
            ]
            
            for strategy in selector_strategies:
                metrics = self.strategy_metrics[strategy]
                if metrics.total_attempts > 0 and metrics.success_rate > 0.7:
                    return strategy
        
        # Return best performing strategy overall, fallback to RELATIVE_POSITIONING
        if strategies_by_performance and strategies_by_performance[0][1].total_attempts > 0:
            return strategies_by_performance[0][0]
        
        return ExtractionStrategy.RELATIVE_POSITIONING  # Default fastest strategy
    
    async def _execute_extraction_strategy(self,
                                         strategy: ExtractionStrategy,
                                         page,
                                         container,
                                         extraction_type: ExtractionType) -> ExtractionResult:
        """Execute the selected extraction strategy"""
        
        if strategy == ExtractionStrategy.RELATIVE_POSITIONING:
            return await self._extract_via_relative_positioning(page, container, extraction_type)
        
        elif strategy == ExtractionStrategy.LONGEST_DIV:
            return await self._extract_via_longest_div(page, container, extraction_type)
        
        elif strategy == ExtractionStrategy.ENHANCED_SELECTORS:
            return await self._extract_via_enhanced_selectors(page, container, extraction_type)
        
        elif strategy == ExtractionStrategy.FALLBACK_PATTERNS:
            return await self._extract_via_fallback_patterns(page, container, extraction_type)
        
        elif strategy == ExtractionStrategy.COMPREHENSIVE_SCAN:
            return await self._extract_via_comprehensive_scan(page, container, extraction_type)
        
        else:
            raise ValueError(f"Unknown extraction strategy: {strategy}")
    
    async def _extract_via_relative_positioning(self, page, container, extraction_type: ExtractionType) -> ExtractionResult:
        """Fastest strategy - structure-based extraction using DOM relationships"""
        
        result_data = {}
        confidence = 0.0
        debug_info = {}
        
        try:
            # Use relative positioning approach (based on relative_prompt_extractor.py)
            if extraction_type in [ExtractionType.PROMPT, ExtractionType.ALL_METADATA]:
                prompt = await self._extract_prompt_relative_positioning(page, container)
                if prompt:
                    result_data['prompt'] = prompt
                    confidence += 0.4
                    debug_info['prompt_method'] = 'relative_positioning'
            
            if extraction_type in [ExtractionType.CREATION_DATE, ExtractionType.ALL_METADATA]:
                date = await self._extract_date_relative_positioning(page, container)
                if date:
                    result_data['generation_date'] = date
                    confidence += 0.4
                    debug_info['date_method'] = 'relative_positioning'
            
            # Additional metadata
            if extraction_type == ExtractionType.ALL_METADATA:
                media_type = await self._extract_media_type(page, container)
                if media_type:
                    result_data['media_type'] = media_type
                    confidence += 0.2
            
            success = len(result_data) > 0
            
            return ExtractionResult(
                success=success,
                data=result_data,
                confidence_score=min(confidence, 1.0),
                debug_info=debug_info
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"Relative positioning extraction failed: {str(e)}"
            )
    
    async def _extract_via_longest_div(self, page, container, extraction_type: ExtractionType) -> ExtractionResult:
        """Fast strategy - content-length based extraction"""
        
        result_data = {}
        confidence = 0.0
        debug_info = {}
        
        try:
            # Find divs with substantial text content for prompts
            if extraction_type in [ExtractionType.PROMPT, ExtractionType.ALL_METADATA]:
                prompt_divs = await page.query_selector_all('.sc-eKQYOU.bdGRCs')
                
                if prompt_divs:
                    longest_text = ""
                    for div in prompt_divs[:10]:  # Limit to first 10 for performance
                        try:
                            text = await div.text_content()
                            if text and len(text) > len(longest_text) and len(text) >= self.min_prompt_length:
                                # Validate it looks like a prompt
                                if any(indicator in text.lower() for indicator in self.prompt_indicators):
                                    longest_text = text.strip()
                        except:
                            continue
                    
                    if longest_text:
                        result_data['prompt'] = longest_text
                        confidence += 0.5
                        debug_info['prompt_method'] = 'longest_div'
                        debug_info['prompt_length'] = len(longest_text)
            
            # Date extraction using selectors
            if extraction_type in [ExtractionType.CREATION_DATE, ExtractionType.ALL_METADATA]:
                date = await self._extract_date_via_selectors(page)
                if date:
                    result_data['generation_date'] = date
                    confidence += 0.4
                    debug_info['date_method'] = 'selector_based'
            
            success = len(result_data) > 0
            
            return ExtractionResult(
                success=success,
                data=result_data,
                confidence_score=min(confidence, 1.0),
                debug_info=debug_info
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"Longest div extraction failed: {str(e)}"
            )
    
    async def _extract_via_enhanced_selectors(self, page, container, extraction_type: ExtractionType) -> ExtractionResult:
        """Medium strategy - multiple CSS selectors with fallbacks"""
        
        result_data = {}
        confidence = 0.0
        debug_info = {}
        
        try:
            # Prompt extraction with multiple selectors
            if extraction_type in [ExtractionType.PROMPT, ExtractionType.ALL_METADATA]:
                for i, selector in enumerate(self.prompt_selectors):
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            for element in elements[:3]:  # Check first 3 matches
                                text = await element.text_content()
                                if text and len(text) >= self.min_prompt_length:
                                    result_data['prompt'] = text.strip()
                                    confidence += 0.4
                                    debug_info['prompt_selector'] = selector
                                    debug_info['selector_index'] = i
                                    break
                        
                        if 'prompt' in result_data:
                            break
                    except:
                        continue
            
            # Date extraction with multiple selectors
            if extraction_type in [ExtractionType.CREATION_DATE, ExtractionType.ALL_METADATA]:
                for i, selector in enumerate(self.date_selectors):
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            if text:
                                # Validate date format
                                for pattern in self.date_patterns:
                                    match = re.search(pattern, text)
                                    if match:
                                        result_data['generation_date'] = match.group().strip()
                                        confidence += 0.4
                                        debug_info['date_selector'] = selector
                                        debug_info['date_pattern'] = pattern
                                        break
                        
                        if 'generation_date' in result_data:
                            break
                    except:
                        continue
            
            success = len(result_data) > 0
            
            return ExtractionResult(
                success=success,
                data=result_data,
                confidence_score=min(confidence, 1.0),
                debug_info=debug_info
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"Enhanced selectors extraction failed: {str(e)}"
            )
    
    async def _extract_via_fallback_patterns(self, page, container, extraction_type: ExtractionType) -> ExtractionResult:
        """Slow strategy - regex pattern matching on page content"""
        
        result_data = {}
        confidence = 0.0
        debug_info = {}
        
        try:
            # Get page text content
            page_text = await page.evaluate("() => document.body.textContent")
            
            if extraction_type in [ExtractionType.CREATION_DATE, ExtractionType.ALL_METADATA]:
                # Try date patterns
                for pattern in self.date_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        # Take the most recent/last match
                        result_data['generation_date'] = matches[-1].strip()
                        confidence += 0.3
                        debug_info['date_pattern_used'] = pattern
                        debug_info['total_date_matches'] = len(matches)
                        break
            
            if extraction_type in [ExtractionType.PROMPT, ExtractionType.ALL_METADATA]:
                # Look for prompt-like content using indicators
                sentences = re.split(r'[.!?]\s+', page_text)
                best_prompt = ""
                best_score = 0
                
                for sentence in sentences:
                    if len(sentence) >= self.min_prompt_length:
                        # Score based on prompt indicators
                        score = sum(1 for indicator in self.prompt_indicators 
                                  if indicator in sentence.lower())
                        
                        if score > best_score:
                            best_score = score
                            best_prompt = sentence.strip()
                
                if best_prompt and best_score >= 2:  # Require at least 2 indicators
                    result_data['prompt'] = best_prompt
                    confidence += 0.2
                    debug_info['prompt_indicator_score'] = best_score
            
            success = len(result_data) > 0
            
            return ExtractionResult(
                success=success,
                data=result_data,
                confidence_score=min(confidence, 1.0),
                debug_info=debug_info
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"Fallback patterns extraction failed: {str(e)}"
            )
    
    async def _extract_via_comprehensive_scan(self, page, container, extraction_type: ExtractionType) -> ExtractionResult:
        """Slowest but most thorough - full DOM traversal"""
        
        result_data = {}
        confidence = 0.0
        debug_info = {}
        
        try:
            # Comprehensive DOM scan
            all_elements = await page.query_selector_all('*')
            
            prompt_candidates = []
            date_candidates = []
            
            for element in all_elements[:100]:  # Limit for performance
                try:
                    text = await element.text_content()
                    if not text:
                        continue
                    
                    # Check for date patterns
                    for pattern in self.date_patterns:
                        if re.search(pattern, text):
                            date_candidates.append(text.strip())
                    
                    # Check for prompt-like content
                    if (len(text) >= self.min_prompt_length and 
                        any(indicator in text.lower() for indicator in self.prompt_indicators)):
                        prompt_candidates.append(text.strip())
                
                except:
                    continue
            
            # Select best candidates
            if extraction_type in [ExtractionType.CREATION_DATE, ExtractionType.ALL_METADATA] and date_candidates:
                # Take the most specific/longest date
                best_date = max(date_candidates, key=len)
                result_data['generation_date'] = best_date
                confidence += 0.4
                debug_info['date_candidates_found'] = len(date_candidates)
            
            if extraction_type in [ExtractionType.PROMPT, ExtractionType.ALL_METADATA] and prompt_candidates:
                # Take the longest prompt that's not too long
                valid_prompts = [p for p in prompt_candidates if len(p) <= self.max_prompt_length]
                if valid_prompts:
                    best_prompt = max(valid_prompts, key=len)
                    result_data['prompt'] = best_prompt
                    confidence += 0.3
                    debug_info['prompt_candidates_found'] = len(prompt_candidates)
            
            success = len(result_data) > 0
            
            return ExtractionResult(
                success=success,
                data=result_data,
                confidence_score=min(confidence, 1.0),
                debug_info=debug_info
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                error_message=f"Comprehensive scan extraction failed: {str(e)}"
            )
    
    async def _extract_prompt_relative_positioning(self, page, container) -> Optional[str]:
        """Extract prompt using relative positioning (Creation Time anchor)"""
        try:
            # Find "Creation Time" text as anchor
            creation_time_elements = await page.query_selector_all('span:has-text("Creation Time")')
            
            for ct_element in creation_time_elements:
                try:
                    # Navigate up to find metadata container
                    metadata_container = await ct_element.evaluate_handle(
                        'element => element.closest("div")'
                    )
                    
                    # Get parent container
                    parent_container = await metadata_container.evaluate_handle(
                        'element => element.parentElement'
                    )
                    
                    # Find prompt section (usually first child)
                    prompt_section = await parent_container.query_selector('.sc-fileXT.gEIKhI')
                    if prompt_section:
                        prompt_element = await prompt_section.query_selector('span[aria-describedby]')
                        if prompt_element:
                            text = await prompt_element.text_content()
                            if text and len(text) >= self.min_prompt_length:
                                return text.strip()
                
                except:
                    continue
            
            return None
            
        except:
            return None
    
    async def _extract_date_relative_positioning(self, page, container) -> Optional[str]:
        """Extract date using relative positioning"""
        try:
            # Look for "Creation Time" label and get adjacent date
            creation_time_elements = await page.query_selector_all('span:has-text("Creation Time")')
            
            for ct_element in creation_time_elements:
                try:
                    # Get parent container and look for date span
                    parent = await ct_element.evaluate_handle('element => element.parentElement')
                    date_spans = await parent.query_selector_all('span')
                    
                    for span in date_spans:
                        text = await span.text_content()
                        if text and any(re.search(pattern, text) for pattern in self.date_patterns):
                            return text.strip()
                
                except:
                    continue
            
            return None
            
        except:
            return None
    
    async def _extract_date_via_selectors(self, page) -> Optional[str]:
        """Extract date using selector-based approach"""
        for selector in self.date_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        for pattern in self.date_patterns:
                            match = re.search(pattern, text)
                            if match:
                                return match.group().strip()
            except:
                continue
        
        return None
    
    async def _extract_media_type(self, page, container) -> Optional[str]:
        """Extract media type information"""
        try:
            # Look for media type indicators
            media_indicators = await page.query_selector_all('span:has-text("Image to video")')
            if media_indicators:
                return "video"
            
            # Check for other indicators
            page_text = await page.evaluate("() => document.body.textContent")
            if "image to video" in page_text.lower():
                return "video"
            elif "image" in page_text.lower():
                return "image"
            
            return "unknown"
        except:
            return None
    
    def _get_cache_key(self, page, container, extraction_type: ExtractionType) -> str:
        """Generate cache key for extraction results"""
        try:
            url = page.url if hasattr(page, 'url') else "unknown"
        except:
            url = "unknown"
        
        container_id = str(id(container)) if container else "none"
        return f"{url}#{container_id}#{extraction_type.value}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[ExtractionResult]:
        """Get cached extraction result with TTL validation"""
        if cache_key not in self.extraction_cache:
            return None
        
        cached_result = self.extraction_cache[cache_key]
        current_time = time.time()
        
        # Check TTL
        if current_time - cached_result.extraction_time > self.cache_ttl:
            del self.extraction_cache[cache_key]
            return None
        
        return cached_result
    
    def _add_to_cache(self, cache_key: str, result: ExtractionResult):
        """Add result to cache"""
        self.extraction_cache[cache_key] = result
    
    def _update_strategy_metrics(self, 
                               strategy: ExtractionStrategy,
                               success: bool,
                               execution_time: float,
                               confidence_score: float):
        """Update performance metrics for strategy optimization"""
        
        metrics = self.strategy_metrics[strategy]
        metrics.total_attempts += 1
        
        if success:
            metrics.successful_extractions += 1
        
        # Update success rate
        metrics.success_rate = metrics.successful_extractions / metrics.total_attempts
        
        # Update average time
        if metrics.total_attempts == 1:
            metrics.average_time = execution_time
        else:
            metrics.average_time = (
                (metrics.average_time * (metrics.total_attempts - 1)) + execution_time
            ) / metrics.total_attempts
        
        # Update average confidence
        if metrics.total_attempts == 1:
            metrics.average_confidence = confidence_score
        else:
            metrics.average_confidence = (
                (metrics.average_confidence * (metrics.total_attempts - 1)) + confidence_score
            ) / metrics.total_attempts
        
        metrics.last_used = time.time()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        
        report = {
            'strategies': {},
            'summary': {
                'total_extractions': sum(m.total_attempts for m in self.strategy_metrics.values()),
                'overall_success_rate': 0.0,
                'average_confidence': 0.0,
                'best_strategy': None,
                'cache_statistics': {
                    'cached_results': len(self.extraction_cache),
                    'cache_hit_potential': f"{len(self.extraction_cache) * 100}%"
                }
            }
        }
        
        # Calculate metrics for each strategy
        total_attempts = 0
        total_successful = 0
        total_confidence = 0.0
        strategies_with_data = 0
        
        for strategy, metrics in self.strategy_metrics.items():
            if metrics.total_attempts > 0:
                report['strategies'][strategy.value] = {
                    'success_rate': f"{metrics.success_rate:.2%}",
                    'average_time': f"{metrics.average_time:.3f}s",
                    'average_confidence': f"{metrics.average_confidence:.2f}",
                    'total_attempts': metrics.total_attempts,
                    'successful_extractions': metrics.successful_extractions
                }
                
                total_attempts += metrics.total_attempts
                total_successful += metrics.successful_extractions
                total_confidence += metrics.average_confidence
                strategies_with_data += 1
        
        # Calculate summary metrics
        if total_attempts > 0:
            report['summary']['overall_success_rate'] = f"{(total_successful / total_attempts):.2%}"
        
        if strategies_with_data > 0:
            report['summary']['average_confidence'] = f"{(total_confidence / strategies_with_data):.2f}"
            
            # Find best strategy
            best_strategy = max(
                [(s, m) for s, m in self.strategy_metrics.items() if m.total_attempts > 0],
                key=lambda x: (x[1].success_rate * x[1].average_confidence),
                default=(None, None)
            )[0]
            
            if best_strategy:
                report['summary']['best_strategy'] = best_strategy.value
        
        return report
    
    def clear_cache(self):
        """Clear extraction cache"""
        self.extraction_cache.clear()
    
    def clear_expired_cache(self):
        """Clear only expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, result in self.extraction_cache.items()
            if current_time - result.extraction_time > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.extraction_cache[key]


# Global instance for reuse
unified_extractor = UnifiedMetadataExtractor()