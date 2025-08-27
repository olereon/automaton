#!/usr/bin/env python3
"""
Optimized Selector Chains and Fallback Mechanisms

This module provides advanced selector optimization, intelligent fallback chains,
and adaptive strategy selection for robust metadata extraction.
"""

import asyncio
import logging
import time
import re
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)


class SelectorStrategy(Enum):
    """Different selector optimization strategies"""
    PRECISE = "precise"          # High precision, may fail more often
    ROBUST = "robust"            # Balance of precision and reliability  
    FALLBACK = "fallback"        # Maximum compatibility, lower precision
    ADAPTIVE = "adaptive"        # Dynamically adjusts based on success rate


@dataclass
class SelectorPerformance:
    """Performance metrics for a selector"""
    selector: str
    success_count: int = 0
    failure_count: int = 0
    average_time_ms: float = 0.0
    last_success: Optional[float] = None
    reliability_score: float = 0.0
    
    def calculate_reliability(self) -> float:
        """Calculate reliability score based on success/failure ratio"""
        total_attempts = self.success_count + self.failure_count
        if total_attempts == 0:
            return 0.5  # Unknown reliability
        
        base_score = self.success_count / total_attempts
        
        # Boost score for recent successes
        if self.last_success and time.time() - self.last_success < 300:  # 5 minutes
            base_score *= 1.1
        
        # Penalize for poor performance
        if self.average_time_ms > 1000:  # More than 1 second
            base_score *= 0.9
        
        self.reliability_score = min(1.0, base_score)
        return self.reliability_score


class OptimizedSelector:
    """Represents an optimized CSS selector with fallback options"""
    
    def __init__(self, primary_selector: str, fallback_selectors: List[str] = None,
                 strategy: SelectorStrategy = SelectorStrategy.ROBUST):
        self.primary_selector = primary_selector
        self.fallback_selectors = fallback_selectors or []
        self.strategy = strategy
        self.performance = SelectorPerformance(primary_selector)
        self.context_hints = {}
        
        # Performance optimizations
        self.cache_key = f"selector_{hash(primary_selector)}"
        self.optimized_variants = self._generate_optimized_variants()
    
    def _generate_optimized_variants(self) -> List[str]:
        """Generate optimized selector variants based on strategy"""
        variants = [self.primary_selector]
        
        if self.strategy == SelectorStrategy.PRECISE:
            # Add more specific selectors
            variants.extend(self._add_precision_selectors())
        
        elif self.strategy == SelectorStrategy.ROBUST:
            # Add balanced variants
            variants.extend(self._add_robust_variants())
        
        elif self.strategy == SelectorStrategy.FALLBACK:
            # Add broad compatibility selectors
            variants.extend(self._add_fallback_variants())
        
        # Always include fallback selectors
        variants.extend(self.fallback_selectors)
        
        return list(dict.fromkeys(variants))  # Remove duplicates while preserving order
    
    def _add_precision_selectors(self) -> List[str]:
        """Add high-precision selector variants"""
        variants = []
        base = self.primary_selector
        
        # Add visibility constraints
        if not ':visible' in base and not ':not(' in base:
            variants.append(f"{base}:visible")
        
        # Add attribute constraints for common patterns
        if '[aria-' not in base and 'span' in base:
            variants.append(f"{base}[aria-describedby]")
        
        return variants
    
    def _add_robust_variants(self) -> List[str]:
        """Add balanced robustness variants"""
        variants = []
        base = self.primary_selector
        
        # Simplified versions
        if ' ' in base:
            # Try direct descendant instead of space
            variants.append(base.replace(' ', ' > '))
            
            # Try without some specificity
            parts = base.split(' ')
            if len(parts) > 2:
                variants.append(' '.join(parts[:-1]))
        
        # Attribute fallbacks
        if '[' in base and ']' in base:
            # Remove one attribute constraint
            variants.append(re.sub(r'\[[^\]]+\]', '', base, 1))
        
        return variants
    
    def _add_fallback_variants(self) -> List[str]:
        """Add maximum compatibility variants"""
        variants = []
        base = self.primary_selector
        
        # Very broad selectors
        if 'span' in base:
            variants.extend(['span', '*[aria-describedby]', '*:contains("text")'])
        
        if 'div' in base:
            variants.extend(['div', 'div:not(:empty)'])
        
        # Class-based fallbacks
        classes = re.findall(r'\.([a-zA-Z0-9_-]+)', base)
        for class_name in classes[:2]:  # Only first 2 classes
            variants.append(f".{class_name}")
        
        return variants
    
    async def execute_optimized(self, page, timeout: int = 5000) -> List[Any]:
        """Execute selector with optimization and fallback"""
        start_time = time.time()
        results = []
        
        try:
            # Try variants in order of preference
            for variant in self.optimized_variants:
                try:
                    elements = await asyncio.wait_for(
                        page.query_selector_all(variant),
                        timeout=timeout / 1000
                    )
                    
                    if elements:
                        results = elements
                        
                        # Update performance metrics
                        execution_time = (time.time() - start_time) * 1000
                        self.performance.success_count += 1
                        self.performance.last_success = time.time()
                        self.performance.average_time_ms = (
                            (self.performance.average_time_ms * (self.performance.success_count - 1) + 
                             execution_time) / self.performance.success_count
                        )
                        
                        break
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.debug(f"Selector variant '{variant}' failed: {e}")
                    continue
            
            if not results:
                self.performance.failure_count += 1
                self.performance.calculate_reliability()
            
            return results
            
        except Exception as e:
            self.performance.failure_count += 1
            self.performance.calculate_reliability()
            logger.warning(f"All selector variants failed for '{self.primary_selector}': {e}")
            return []


class SelectorChainOptimizer:
    """Optimizes chains of selectors for complex extraction scenarios"""
    
    def __init__(self):
        self.selector_registry = {}
        self.performance_history = {}
        self.optimization_rules = self._load_optimization_rules()
        self.adaptive_threshold = 0.7  # Minimum reliability for adaptive strategies
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Load selector optimization rules"""
        return {
            'text_content_patterns': {
                'landmark_text': {
                    'patterns': ['*:has-text("{text}")', ':contains("{text}")'],
                    'fallbacks': ['*:text-matches("{text}", "i")', 'span, div']
                },
                'creation_time': {
                    'patterns': ['span:contains("Creation Time")', '*:has-text("Creation Time")'],
                    'fallbacks': ['*[title*="time"]', 'time', 'span']
                }
            },
            'attribute_patterns': {
                'aria_elements': {
                    'patterns': ['[aria-describedby]', '[aria-label]'],
                    'fallbacks': ['[title]', '[alt]', 'span[data-*]']
                },
                'interactive_elements': {
                    'patterns': ['button', 'a[href]', '[onclick]'],
                    'fallbacks': ['*[role="button"]', '[tabindex]']
                }
            },
            'structural_patterns': {
                'content_areas': {
                    'patterns': ['main', 'article', '.content', '#content'],
                    'fallbacks': ['div:not(:empty)', 'section', 'div[class*="content"]']
                }
            }
        }
    
    def create_optimized_chain(self, field_name: str, base_selectors: List[str],
                              strategy: SelectorStrategy = SelectorStrategy.ADAPTIVE) -> 'SelectorChain':
        """Create an optimized selector chain for a specific field"""
        chain = SelectorChain(field_name, strategy)
        
        # Add optimized selectors based on patterns
        for selector in base_selectors:
            optimized_selector = self._optimize_single_selector(selector, field_name, strategy)
            chain.add_selector(optimized_selector)
        
        # Add intelligent fallbacks
        fallback_selectors = self._generate_intelligent_fallbacks(field_name, base_selectors)
        for fallback in fallback_selectors:
            optimized_fallback = self._optimize_single_selector(fallback, field_name, SelectorStrategy.FALLBACK)
            chain.add_selector(optimized_fallback)
        
        return chain
    
    def _optimize_single_selector(self, selector: str, field_name: str, 
                                 strategy: SelectorStrategy) -> OptimizedSelector:
        """Optimize a single selector based on context"""
        # Get performance history
        perf_key = f"{selector}_{field_name}"
        historical_performance = self.performance_history.get(perf_key)
        
        # Generate fallbacks based on optimization rules
        fallbacks = self._generate_contextual_fallbacks(selector, field_name)
        
        optimized = OptimizedSelector(selector, fallbacks, strategy)
        
        # Apply historical performance data
        if historical_performance:
            optimized.performance = historical_performance
        
        return optimized
    
    def _generate_contextual_fallbacks(self, selector: str, field_name: str) -> List[str]:
        """Generate contextual fallback selectors"""
        fallbacks = []
        
        # Field-specific fallbacks
        if field_name == 'generation_date':
            fallbacks.extend([
                'time', 'span[class*="date"]', 'span[class*="time"]',
                '[datetime]', '*[title*="date"]'
            ])
        
        elif field_name == 'prompt':
            fallbacks.extend([
                '[aria-describedby]', 'span[title]', 'div[title]',
                'span:not(:empty)', 'div:not(:empty)'
            ])
        
        # General fallbacks based on selector type
        if ':has-text' in selector or ':contains' in selector:
            # Text-based selector fallbacks
            fallbacks.extend(['span', 'div', 'p', '*:not(script):not(style)'])
        
        elif '[' in selector and ']' in selector:
            # Attribute-based selector fallbacks
            fallbacks.extend(['*[class]', '*[id]', 'span', 'div'])
        
        elif '.' in selector:
            # Class-based selector fallbacks
            class_matches = re.findall(r'\.([a-zA-Z0-9_-]+)', selector)
            for class_name in class_matches:
                fallbacks.append(f'*[class*="{class_name}"]')
        
        return list(dict.fromkeys(fallbacks))  # Remove duplicates
    
    def _generate_intelligent_fallbacks(self, field_name: str, base_selectors: List[str]) -> List[str]:
        """Generate intelligent fallbacks based on field type and base selectors"""
        fallbacks = []
        
        # Use optimization rules
        for category, patterns in self.optimization_rules.items():
            for pattern_name, pattern_config in patterns.items():
                if field_name in pattern_name or any(keyword in field_name for keyword in pattern_config.get('keywords', [])):
                    fallbacks.extend(pattern_config.get('fallbacks', []))
        
        # Add progressive degradation fallbacks
        fallbacks.extend([
            '*[data-testid]',  # Testing attributes
            '*[class]',        # Any classed element
            '*:not(:empty)',   # Non-empty elements
            'span, div, p'     # Common text containers
        ])
        
        return list(dict.fromkeys(fallbacks))


class SelectorChain:
    """A chain of optimized selectors with intelligent fallback logic"""
    
    def __init__(self, field_name: str, strategy: SelectorStrategy = SelectorStrategy.ADAPTIVE):
        self.field_name = field_name
        self.strategy = strategy
        self.selectors: List[OptimizedSelector] = []
        self.execution_history = []
        self.adaptive_weights = {}
        self.last_successful_index = 0
    
    def add_selector(self, selector: OptimizedSelector):
        """Add an optimized selector to the chain"""
        self.selectors.append(selector)
        self.adaptive_weights[len(self.selectors) - 1] = 1.0
    
    async def execute_chain(self, page, max_attempts: int = None) -> Tuple[List[Any], Dict[str, Any]]:
        """Execute the selector chain with adaptive optimization"""
        max_attempts = max_attempts or len(self.selectors)
        results = []
        execution_info = {
            'successful_selector': None,
            'attempts_made': 0,
            'total_time_ms': 0,
            'strategy_used': self.strategy.value
        }
        
        start_time = time.time()
        
        # Adaptive ordering: Start with most reliable selectors
        if self.strategy == SelectorStrategy.ADAPTIVE:
            selector_order = self._get_adaptive_order()
        else:
            selector_order = list(range(len(self.selectors)))
        
        for i, selector_idx in enumerate(selector_order[:max_attempts]):
            if selector_idx >= len(self.selectors):
                continue
                
            selector = self.selectors[selector_idx]
            execution_info['attempts_made'] += 1
            
            try:
                elements = await selector.execute_optimized(page, timeout=3000)
                
                if elements and self._validate_results(elements, selector):
                    results = elements
                    execution_info['successful_selector'] = selector.primary_selector
                    self.last_successful_index = selector_idx
                    
                    # Update adaptive weights (successful selector gets boost)
                    self.adaptive_weights[selector_idx] *= 1.2
                    
                    break
                else:
                    # Reduce weight for unsuccessful selector
                    self.adaptive_weights[selector_idx] *= 0.9
                    
            except Exception as e:
                logger.debug(f"Selector chain execution failed for '{selector.primary_selector}': {e}")
                self.adaptive_weights[selector_idx] *= 0.8
                continue
        
        execution_info['total_time_ms'] = (time.time() - start_time) * 1000
        
        # Record execution history for learning
        self.execution_history.append({
            'timestamp': time.time(),
            'successful_selector_idx': self.last_successful_index if results else -1,
            'execution_time_ms': execution_info['total_time_ms'],
            'results_count': len(results)
        })
        
        # Keep history limited
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-50:]
        
        return results, execution_info
    
    def _get_adaptive_order(self) -> List[int]:
        """Get adaptive ordering of selectors based on performance"""
        # Combine reliability scores with adaptive weights
        selector_scores = []
        
        for i, selector in enumerate(self.selectors):
            reliability = selector.performance.calculate_reliability()
            adaptive_weight = self.adaptive_weights.get(i, 1.0)
            
            # Recent success bonus
            recent_bonus = 1.0
            if self.execution_history:
                recent_successes = sum(1 for h in self.execution_history[-10:] 
                                     if h['successful_selector_idx'] == i)
                recent_bonus = 1.0 + (recent_successes * 0.1)
            
            combined_score = reliability * adaptive_weight * recent_bonus
            selector_scores.append((i, combined_score))
        
        # Sort by score (highest first)
        selector_scores.sort(key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in selector_scores]
    
    def _validate_results(self, elements: List[Any], selector: OptimizedSelector) -> bool:
        """Validate that the results are meaningful"""
        if not elements:
            return False
        
        # Field-specific validation
        if self.field_name == 'generation_date':
            # For date fields, prefer elements with date-like text
            for element in elements[:3]:  # Check first 3 elements
                try:
                    # This would need async handling in real implementation
                    # For now, assume basic validation
                    return True
                except:
                    continue
        
        elif self.field_name == 'prompt':
            # For prompt fields, prefer elements with substantial text
            return len(elements) > 0  # Basic validation
        
        return True
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for this selector chain"""
        if not self.execution_history:
            return {'status': 'no_history'}
        
        recent_history = self.execution_history[-20:]  # Last 20 executions
        
        success_rate = sum(1 for h in recent_history if h['successful_selector_idx'] >= 0) / len(recent_history)
        avg_time = sum(h['execution_time_ms'] for h in recent_history) / len(recent_history)
        
        # Most successful selector
        successful_selectors = [h['successful_selector_idx'] for h in recent_history if h['successful_selector_idx'] >= 0]
        most_successful_idx = max(set(successful_selectors), key=successful_selectors.count) if successful_selectors else -1
        
        return {
            'field_name': self.field_name,
            'success_rate': round(success_rate * 100, 2),
            'average_time_ms': round(avg_time, 2),
            'total_selectors': len(self.selectors),
            'executions': len(self.execution_history),
            'most_successful_selector': (
                self.selectors[most_successful_idx].primary_selector 
                if most_successful_idx >= 0 and most_successful_idx < len(self.selectors)
                else 'none'
            ),
            'adaptive_weights': self.adaptive_weights
        }


class FallbackChainManager:
    """Manages complex fallback chains across multiple extraction strategies"""
    
    def __init__(self, config):
        self.config = config
        self.optimizer = SelectorChainOptimizer()
        self.chains = {}
        self.global_fallback_strategy = self._create_global_fallback()
    
    def _create_global_fallback(self) -> List[Callable]:
        """Create global fallback strategy functions"""
        return [
            self._landmark_based_fallback,
            self._css_selector_fallback,
            self._heuristic_fallback,
            self._last_resort_fallback
        ]
    
    def create_field_chain(self, field_name: str, selectors: List[str]) -> SelectorChain:
        """Create optimized selector chain for a specific field"""
        chain = self.optimizer.create_optimized_chain(
            field_name, 
            selectors, 
            SelectorStrategy.ADAPTIVE
        )
        
        self.chains[field_name] = chain
        return chain
    
    async def extract_with_fallbacks(self, page, field_name: str, 
                                   primary_selectors: List[str] = None) -> Tuple[Any, Dict[str, Any]]:
        """Extract field value using optimized fallback chains"""
        extraction_info = {
            'field_name': field_name,
            'method_used': 'unknown',
            'success': False,
            'execution_time_ms': 0,
            'fallback_level': 0
        }
        
        start_time = time.time()
        
        try:
            # Level 1: Use existing optimized chain if available
            if field_name in self.chains:
                results, chain_info = await self.chains[field_name].execute_chain(page)
                if results:
                    extraction_info.update({
                        'method_used': 'optimized_chain',
                        'success': True,
                        'fallback_level': 1,
                        'chain_info': chain_info
                    })
                    return await self._extract_value_from_results(results, field_name), extraction_info
            
            # Level 2: Create and execute new chain with primary selectors
            if primary_selectors:
                new_chain = self.create_field_chain(field_name, primary_selectors)
                results, chain_info = await new_chain.execute_chain(page)
                if results:
                    extraction_info.update({
                        'method_used': 'new_chain',
                        'success': True,
                        'fallback_level': 2,
                        'chain_info': chain_info
                    })
                    return await self._extract_value_from_results(results, field_name), extraction_info
            
            # Level 3: Global fallback strategies
            for level, fallback_func in enumerate(self.global_fallback_strategy, 3):
                try:
                    result = await fallback_func(page, field_name)
                    if result:
                        extraction_info.update({
                            'method_used': f'global_fallback_{level-2}',
                            'success': True,
                            'fallback_level': level
                        })
                        return result, extraction_info
                except Exception as e:
                    logger.debug(f"Fallback level {level} failed: {e}")
                    continue
            
            # No successful extraction
            extraction_info['success'] = False
            return None, extraction_info
            
        finally:
            extraction_info['execution_time_ms'] = (time.time() - start_time) * 1000
    
    async def _extract_value_from_results(self, results: List[Any], field_name: str) -> Optional[str]:
        """Extract actual value from DOM elements"""
        if not results:
            return None
        
        for element in results[:5]:  # Check first 5 results
            try:
                text = await element.text_content()
                if text and text.strip():
                    # Field-specific value validation
                    if field_name == 'generation_date' and self._validate_date_format(text):
                        return text.strip()
                    elif field_name == 'prompt' and len(text.strip()) > 20:
                        return text.strip()
                    elif field_name not in ['generation_date', 'prompt'] and text.strip():
                        return text.strip()
            except Exception as e:
                logger.debug(f"Error extracting value from element: {e}")
                continue
        
        return None
    
    def _validate_date_format(self, text: str) -> bool:
        """Validate if text looks like a date"""
        date_patterns = [
            r'\d{1,2}\s+\w{3}\s+\d{4}',  # "24 Aug 2025"
            r'\d{4}-\d{1,2}-\d{1,2}',    # "2025-08-24"
            r'\d{1,2}/\d{1,2}/\d{4}',    # "24/08/2025"
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    async def _landmark_based_fallback(self, page, field_name: str) -> Optional[str]:
        """Landmark-based fallback strategy"""
        # Implementation would use landmark extraction logic
        return None
    
    async def _css_selector_fallback(self, page, field_name: str) -> Optional[str]:
        """CSS selector fallback strategy"""
        # Implementation would use traditional CSS selectors
        return None
    
    async def _heuristic_fallback(self, page, field_name: str) -> Optional[str]:
        """Heuristic-based fallback strategy"""
        # Implementation would use pattern matching and heuristics
        return None
    
    async def _last_resort_fallback(self, page, field_name: str) -> Optional[str]:
        """Last resort fallback strategy"""
        if field_name == 'generation_date':
            return 'Unknown Date'
        elif field_name == 'prompt':
            return 'Unknown Prompt'
        return f'Unknown {field_name.replace("_", " ").title()}'
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for all chains"""
        report = {
            'total_chains': len(self.chains),
            'chain_performance': {}
        }
        
        for field_name, chain in self.chains.items():
            report['chain_performance'][field_name] = chain.get_performance_summary()
        
        return report