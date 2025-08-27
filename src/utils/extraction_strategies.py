#!/usr/bin/env python3
"""
Advanced Extraction Strategies for Landmark-Based Metadata Extraction

This module provides multiple extraction strategies with comprehensive fallback mechanisms
and intelligent strategy selection for maximum reliability.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import re
from datetime import datetime
from .landmark_extractor import LandmarkStrategy, ExtractionContext, ExtractionResult, ElementInfo

logger = logging.getLogger(__name__)


class CreationTimeLandmarkStrategy:
    """Strategy using Creation Time text as primary landmark"""
    
    def __init__(self, navigator, config):
        self.navigator = navigator
        self.config = config
    
    async def extract(self, context: ExtractionContext, field_name: str) -> ExtractionResult:
        """Extract metadata using Creation Time landmark"""
        try:
            # Find Creation Time landmarks
            creation_landmarks = await self.navigator.find_elements_by_landmark(
                self.config.creation_time_text
            )
            
            if not creation_landmarks:
                return self._create_failure_result(field_name, "No Creation Time landmarks found")
            
            candidates = []
            
            for i, landmark in enumerate(creation_landmarks):
                if field_name == "generation_date":
                    result = await self._extract_date_from_creation_time(landmark)
                    if result:
                        candidates.append(result)
                elif field_name == "prompt":
                    # For prompt, navigate to nearby elements
                    result = await self._extract_prompt_near_creation_time(landmark)
                    if result:
                        candidates.append(result)
            
            return self._select_best_candidate(field_name, candidates, "creation_time_landmark")
            
        except Exception as e:
            return self._create_failure_result(field_name, str(e))
    
    async def _extract_date_from_creation_time(self, landmark_info: ElementInfo) -> Optional[Dict[str, Any]]:
        """Extract date directly associated with Creation Time landmark"""
        try:
            # Strategy 1: Check next sibling elements
            siblings = await self.navigator.navigate_from_landmark(landmark_info, "siblings")
            
            for sibling in siblings:
                if (sibling.text_content and 
                    sibling.text_content.strip() != self.config.creation_time_text and
                    self._looks_like_date(sibling.text_content)):
                    
                    confidence = self._calculate_date_confidence(sibling.text_content, sibling)
                    return {
                        'value': sibling.text_content.strip(),
                        'confidence': confidence,
                        'validation_passed': self._validate_date_format(sibling.text_content),
                        'method': 'creation_time_sibling'
                    }
            
            # Strategy 2: Check parent container for date spans
            parent_elements = await self.navigator.navigate_from_landmark(landmark_info, "parent")
            for parent in parent_elements:
                children = await self.navigator.navigate_from_landmark(parent, "children")
                for child in children:
                    if (child.text_content and 
                        child.text_content.strip() != self.config.creation_time_text and
                        self._looks_like_date(child.text_content)):
                        
                        confidence = self._calculate_date_confidence(child.text_content, child)
                        return {
                            'value': child.text_content.strip(),
                            'confidence': confidence,
                            'validation_passed': self._validate_date_format(child.text_content),
                            'method': 'creation_time_parent_child'
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting date from creation time: {e}")
            return None
    
    async def _extract_prompt_near_creation_time(self, landmark_info: ElementInfo) -> Optional[Dict[str, Any]]:
        """Extract prompt from elements near Creation Time landmark"""
        try:
            # Find elements within reasonable distance
            nearby_elements = await self.navigator.find_nearest_elements(landmark_info, 500)
            
            for element in nearby_elements:
                if element.attributes.get('aria-describedby'):
                    prompt_text = await self._extract_full_prompt_text(element)
                    if prompt_text and len(prompt_text) > 20:
                        confidence = self._calculate_prompt_confidence(prompt_text, element)
                        return {
                            'value': prompt_text,
                            'confidence': confidence,
                            'validation_passed': len(prompt_text) > 20,
                            'method': 'creation_time_spatial'
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting prompt near creation time: {e}")
            return None
    
    def get_confidence(self, context: ExtractionContext) -> float:
        """Get confidence for this strategy"""
        return 0.85  # High confidence for direct Creation Time landmarks
    
    def get_supported_fields(self) -> List[str]:
        return ["generation_date", "prompt"]
    
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        if not text:
            return False
        
        text = text.strip()
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\w{3} \d{1,2}, \d{4}',
            r'\d{1,2} \w{3} \d{4}',
            r'\d{4}/\d{1,2}/\d{1,2}'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _validate_date_format(self, date_text: str) -> bool:
        """Validate date format"""
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%b %d, %Y', '%d %b %Y', '%Y/%m/%d']
        
        for fmt in formats:
            try:
                datetime.strptime(date_text.strip(), fmt)
                return True
            except ValueError:
                continue
        return False
    
    def _calculate_date_confidence(self, date_text: str, element_info: ElementInfo) -> float:
        """Calculate confidence for date candidate"""
        confidence = 0.6
        
        if self._validate_date_format(date_text):
            confidence += 0.3
        if element_info.visible:
            confidence += 0.1
        if element_info.bounds:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _extract_full_prompt_text(self, element_info: ElementInfo) -> Optional[str]:
        """Extract full prompt text from element"""
        try:
            methods = [
                ('text_content', element_info.text_content),
                ('title', element_info.attributes.get('title')),
                ('aria_label', element_info.attributes.get('aria-label'))
            ]
            
            # Try innerText
            try:
                inner_text = await element_info.element.evaluate("el => el.innerText")
                methods.append(('inner_text', inner_text))
            except:
                pass
            
            # Find longest valid text
            best_text = None
            max_length = 0
            
            for method_name, text in methods:
                if text and len(text.strip()) > max_length and len(text.strip()) > 20:
                    max_length = len(text.strip())
                    best_text = text.strip()
            
            return best_text
            
        except Exception as e:
            logger.debug(f"Error extracting full prompt text: {e}")
            return None
    
    def _calculate_prompt_confidence(self, prompt_text: str, element_info: ElementInfo) -> float:
        """Calculate confidence for prompt candidate"""
        confidence = 0.5
        
        if len(prompt_text) > 100:
            confidence += 0.2
        elif len(prompt_text) > 50:
            confidence += 0.1
        
        if element_info.attributes.get('aria-describedby'):
            confidence += 0.15
        if element_info.visible:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _select_best_candidate(self, field_name: str, candidates: List[Dict], method: str) -> ExtractionResult:
        """Select best candidate from list"""
        if not candidates:
            return self._create_failure_result(field_name, "No candidates found")
        
        best_candidate = max(candidates, key=lambda x: x['confidence'])
        
        return ExtractionResult(
            success=True,
            field_name=field_name,
            extracted_value=best_candidate['value'],
            confidence=best_candidate['confidence'],
            method_used=method,
            validation_passed=best_candidate['validation_passed'],
            candidates=candidates
        )
    
    def _create_failure_result(self, field_name: str, error: str) -> ExtractionResult:
        """Create failure result"""
        return ExtractionResult(
            success=False,
            field_name=field_name,
            extracted_value=None,
            confidence=0.0,
            method_used="creation_time_landmark",
            validation_passed=False,
            candidates=[],
            error=error
        )


class CSSFallbackStrategy:
    """Fallback strategy using traditional CSS selectors"""
    
    def __init__(self, navigator, config):
        self.navigator = navigator
        self.config = config
    
    async def extract(self, context: ExtractionContext, field_name: str) -> ExtractionResult:
        """Extract using CSS selectors as fallback"""
        try:
            if field_name == "generation_date":
                return await self._extract_date_css()
            elif field_name == "prompt":
                return await self._extract_prompt_css()
            else:
                return self._create_failure_result(field_name, "Unsupported field")
                
        except Exception as e:
            return self._create_failure_result(field_name, str(e))
    
    async def _extract_date_css(self) -> ExtractionResult:
        """Extract date using CSS selector"""
        try:
            element = await context.page.wait_for_selector(
                self.config.generation_date_selector, 
                timeout=3000
            )
            
            if element:
                date_text = await element.text_content()
                if date_text:
                    confidence = 0.6 if self._validate_date_format(date_text) else 0.4
                    
                    return ExtractionResult(
                        success=True,
                        field_name="generation_date",
                        extracted_value=date_text.strip(),
                        confidence=confidence,
                        method_used="css_selector_fallback",
                        validation_passed=self._validate_date_format(date_text),
                        candidates=[{
                            'value': date_text.strip(),
                            'confidence': confidence,
                            'method': 'css_selector'
                        }]
                    )
            
            return self._create_failure_result("generation_date", "No element found with CSS selector")
            
        except Exception as e:
            return self._create_failure_result("generation_date", str(e))
    
    async def _extract_prompt_css(self) -> ExtractionResult:
        """Extract prompt using CSS selector"""
        try:
            element = await context.page.wait_for_selector(
                self.config.prompt_selector,
                timeout=3000
            )
            
            if element:
                prompt_text = await element.text_content()
                if prompt_text and len(prompt_text) > 20:
                    confidence = min(0.6 + (len(prompt_text) / 1000), 0.8)
                    
                    return ExtractionResult(
                        success=True,
                        field_name="prompt",
                        extracted_value=prompt_text.strip(),
                        confidence=confidence,
                        method_used="css_selector_fallback",
                        validation_passed=len(prompt_text) > 20,
                        candidates=[{
                            'value': prompt_text.strip(),
                            'confidence': confidence,
                            'method': 'css_selector'
                        }]
                    )
            
            return self._create_failure_result("prompt", "No element found with CSS selector")
            
        except Exception as e:
            return self._create_failure_result("prompt", str(e))
    
    def get_confidence(self, context: ExtractionContext) -> float:
        """Get confidence for CSS fallback strategy"""
        return 0.4  # Lower confidence as fallback
    
    def get_supported_fields(self) -> List[str]:
        return ["generation_date", "prompt"]
    
    def _validate_date_format(self, date_text: str) -> bool:
        """Validate date format"""
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%b %d, %Y', '%d %b %Y']
        
        for fmt in formats:
            try:
                datetime.strptime(date_text.strip(), fmt)
                return True
            except ValueError:
                continue
        return False
    
    def _create_failure_result(self, field_name: str, error: str) -> ExtractionResult:
        """Create failure result"""
        return ExtractionResult(
            success=False,
            field_name=field_name,
            extracted_value=None,
            confidence=0.0,
            method_used="css_selector_fallback",
            validation_passed=False,
            candidates=[],
            error=error
        )


class HeuristicExtractionStrategy:
    """Strategy using heuristic pattern matching as last resort"""
    
    def __init__(self, navigator, config):
        self.navigator = navigator
        self.config = config
    
    async def extract(self, context: ExtractionContext, field_name: str) -> ExtractionResult:
        """Extract using heuristic pattern matching"""
        try:
            if field_name == "generation_date":
                return await self._extract_date_heuristic(context)
            elif field_name == "prompt":
                return await self._extract_prompt_heuristic(context)
            else:
                return self._create_failure_result(field_name, "Unsupported field")
                
        except Exception as e:
            return self._create_failure_result(field_name, str(e))
    
    async def _extract_date_heuristic(self, context: ExtractionContext) -> ExtractionResult:
        """Extract date using heuristic patterns"""
        try:
            # Get all text elements on page
            all_elements = await context.page.query_selector_all("span, div, p")
            date_candidates = []
            
            for element in all_elements:
                try:
                    element_info = await self.navigator.get_element_info(element)
                    if (element_info.text_content and 
                        element_info.visible and
                        self._looks_like_date(element_info.text_content)):
                        
                        confidence = self._calculate_heuristic_date_confidence(
                            element_info.text_content, element_info
                        )
                        
                        date_candidates.append({
                            'value': element_info.text_content.strip(),
                            'confidence': confidence,
                            'validation_passed': self._validate_date_format(element_info.text_content),
                            'method': 'heuristic_pattern'
                        })
                        
                except Exception:
                    continue
            
            if date_candidates:
                best_candidate = max(date_candidates, key=lambda x: x['confidence'])
                return ExtractionResult(
                    success=True,
                    field_name="generation_date",
                    extracted_value=best_candidate['value'],
                    confidence=best_candidate['confidence'],
                    method_used="heuristic_extraction",
                    validation_passed=best_candidate['validation_passed'],
                    candidates=date_candidates
                )
            
            return self._create_failure_result("generation_date", "No date candidates found")
            
        except Exception as e:
            return self._create_failure_result("generation_date", str(e))
    
    async def _extract_prompt_heuristic(self, context: ExtractionContext) -> ExtractionResult:
        """Extract prompt using heuristic patterns"""
        try:
            # Look for long text elements that could be prompts
            elements_with_aria = await context.page.query_selector_all("[aria-describedby]")
            long_text_elements = await context.page.query_selector_all("span, div, p")
            
            prompt_candidates = []
            
            # Check aria-describedby elements first
            for element in elements_with_aria:
                try:
                    element_info = await self.navigator.get_element_info(element)
                    prompt_text = await self._extract_full_prompt_text(element_info)
                    
                    if prompt_text and len(prompt_text) > 30:
                        confidence = 0.4 + min(len(prompt_text) / 500, 0.3)
                        prompt_candidates.append({
                            'value': prompt_text,
                            'confidence': confidence,
                            'validation_passed': len(prompt_text) > 20,
                            'method': 'heuristic_aria'
                        })
                        
                except Exception:
                    continue
            
            # Check long text elements
            for element in long_text_elements:
                try:
                    element_info = await self.navigator.get_element_info(element)
                    if (element_info.text_content and 
                        len(element_info.text_content) > 50 and
                        element_info.visible):
                        
                        confidence = 0.3 + min(len(element_info.text_content) / 1000, 0.2)
                        prompt_candidates.append({
                            'value': element_info.text_content.strip(),
                            'confidence': confidence,
                            'validation_passed': len(element_info.text_content) > 20,
                            'method': 'heuristic_long_text'
                        })
                        
                except Exception:
                    continue
            
            if prompt_candidates:
                best_candidate = max(prompt_candidates, key=lambda x: x['confidence'])
                return ExtractionResult(
                    success=True,
                    field_name="prompt",
                    extracted_value=best_candidate['value'],
                    confidence=best_candidate['confidence'],
                    method_used="heuristic_extraction",
                    validation_passed=best_candidate['validation_passed'],
                    candidates=prompt_candidates[:5]  # Limit candidates
                )
            
            return self._create_failure_result("prompt", "No prompt candidates found")
            
        except Exception as e:
            return self._create_failure_result("prompt", str(e))
    
    def get_confidence(self, context: ExtractionContext) -> float:
        """Get confidence for heuristic strategy"""
        return 0.3  # Lowest confidence as last resort
    
    def get_supported_fields(self) -> List[str]:
        return ["generation_date", "prompt"]
    
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        if not text:
            return False
        
        text = text.strip()
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\w{3} \d{1,2}, \d{4}'
        ]
        
        return any(re.search(pattern, text) for pattern in date_patterns)
    
    def _validate_date_format(self, date_text: str) -> bool:
        """Validate date format"""
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%b %d, %Y']
        
        for fmt in formats:
            try:
                datetime.strptime(date_text.strip(), fmt)
                return True
            except ValueError:
                continue
        return False
    
    def _calculate_heuristic_date_confidence(self, date_text: str, element_info: ElementInfo) -> float:
        """Calculate confidence for heuristic date extraction"""
        confidence = 0.2  # Base for heuristic
        
        if self._validate_date_format(date_text):
            confidence += 0.2
        if element_info.visible:
            confidence += 0.1
        
        return min(confidence, 0.6)  # Cap heuristic confidence
    
    async def _extract_full_prompt_text(self, element_info: ElementInfo) -> Optional[str]:
        """Extract full prompt text"""
        try:
            if element_info.text_content and len(element_info.text_content) > 30:
                return element_info.text_content.strip()
            
            # Try innerText
            try:
                inner_text = await element_info.element.evaluate("el => el.innerText")
                if inner_text and len(inner_text) > 30:
                    return inner_text.strip()
            except:
                pass
            
            return None
            
        except Exception:
            return None
    
    def _create_failure_result(self, field_name: str, error: str) -> ExtractionResult:
        """Create failure result"""
        return ExtractionResult(
            success=False,
            field_name=field_name,
            extracted_value=None,
            confidence=0.0,
            method_used="heuristic_extraction",
            validation_passed=False,
            candidates=[],
            error=error
        )


class StrategyOrchestrator:
    """Orchestrates multiple extraction strategies for maximum reliability"""
    
    def __init__(self, navigator, config):
        self.navigator = navigator
        self.config = config
        self.strategies = []
        
        # Initialize strategies in priority order
        from .landmark_extractor import ImageToVideoLandmarkStrategy
        self.strategies.extend([
            ImageToVideoLandmarkStrategy(navigator, config),
            CreationTimeLandmarkStrategy(navigator, config),
            CSSFallbackStrategy(navigator, config),
            HeuristicExtractionStrategy(navigator, config)
        ])
    
    async def extract_with_fallbacks(self, context: ExtractionContext, field_name: str) -> ExtractionResult:
        """Extract field using multiple strategies with intelligent fallbacks"""
        try:
            best_result = None
            best_confidence = 0.0
            all_attempts = []
            
            for strategy in self.strategies:
                if field_name not in strategy.get_supported_fields():
                    continue
                
                try:
                    # Check if strategy is suitable for this context
                    strategy_confidence = strategy.get_confidence(context)
                    
                    if strategy_confidence > 0.2:  # Minimum threshold
                        result = await strategy.extract(context, field_name)
                        all_attempts.append({
                            'strategy': strategy.__class__.__name__,
                            'result': result,
                            'strategy_confidence': strategy_confidence
                        })
                        
                        if result.success and result.confidence > best_confidence:
                            best_confidence = result.confidence
                            best_result = result
                            
                            # If we have high confidence, we can stop
                            if result.confidence > 0.8:
                                logger.debug(f"High confidence result found for {field_name}, stopping search")
                                break
                        
                except Exception as e:
                    logger.debug(f"Strategy {strategy.__class__.__name__} failed for {field_name}: {e}")
                    continue
            
            if best_result:
                # Add metadata about all attempts
                best_result.candidates.extend([
                    {
                        'strategy': attempt['strategy'],
                        'success': attempt['result'].success,
                        'confidence': attempt['result'].confidence,
                        'value': attempt['result'].extracted_value
                    }
                    for attempt in all_attempts
                ])
                return best_result
            
            # No successful extraction
            return ExtractionResult(
                success=False,
                field_name=field_name,
                extracted_value=None,
                confidence=0.0,
                method_used="all_strategies_failed",
                validation_passed=False,
                candidates=[
                    {
                        'strategy': attempt['strategy'],
                        'success': False,
                        'error': attempt['result'].error
                    }
                    for attempt in all_attempts
                ],
                error="All extraction strategies failed"
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                field_name=field_name,
                extracted_value=None,
                confidence=0.0,
                method_used="orchestrator_error",
                validation_passed=False,
                candidates=[],
                error=str(e)
            )