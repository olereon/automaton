#!/usr/bin/env python3
"""
Enhanced Landmark-Based Metadata Extraction System

This module provides a robust, multi-strategy approach to extracting metadata
from web pages using spatial and semantic landmarks for improved reliability.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ElementInfo:
    """Information about a DOM element"""
    element: Any  # Playwright element handle
    text_content: Optional[str]
    bounds: Optional[Dict[str, float]]  # x, y, width, height
    visible: bool
    tag_name: str
    attributes: Dict[str, str]
    parent_info: Optional['ElementInfo'] = None
    children_count: int = 0


@dataclass
class ExtractionContext:
    """Context information for metadata extraction"""
    page: Any  # Playwright page
    thumbnail_index: int
    landmark_elements: List[ElementInfo]
    content_area: Optional[Dict[str, float]]  # Bounding box of content area
    metadata_panels: List[ElementInfo]
    confidence_threshold: float = 0.7


@dataclass
class ExtractionResult:
    """Result of metadata extraction"""
    success: bool
    field_name: str
    extracted_value: Optional[str]
    confidence: float
    method_used: str
    validation_passed: bool
    candidates: List[Dict[str, Any]]
    error: Optional[str] = None


class ConfidenceLevel(Enum):
    """Confidence levels for extracted data"""
    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5
    UNCERTAIN = 0.3


class LandmarkStrategy(Protocol):
    """Interface for landmark-based extraction strategies"""
    
    async def extract(self, context: ExtractionContext, field_name: str) -> ExtractionResult:
        """Extract a specific field using this strategy"""
        ...
    
    def get_confidence(self, context: ExtractionContext) -> float:
        """Get confidence score for this strategy in given context"""
        ...
    
    def get_supported_fields(self) -> List[str]:
        """Get list of fields this strategy can extract"""
        ...


class DOMNavigator:
    """Advanced DOM navigation with spatial and semantic awareness"""
    
    def __init__(self, page):
        self.page = page
    
    async def get_element_info(self, element) -> ElementInfo:
        """Get comprehensive information about an element"""
        try:
            text_content = await element.text_content()
            bounds = await element.bounding_box()
            visible = await element.is_visible()
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            
            # Get attributes
            attributes = await element.evaluate("""el => {
                const attrs = {};
                for (let attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }""")
            
            # Get children count
            children_count = await element.evaluate("el => el.children.length")
            
            return ElementInfo(
                element=element,
                text_content=text_content,
                bounds=bounds,
                visible=visible,
                tag_name=tag_name,
                attributes=attributes,
                children_count=children_count
            )
            
        except Exception as e:
            logger.debug(f"Error getting element info: {e}")
            return ElementInfo(
                element=element,
                text_content=None,
                bounds=None,
                visible=False,
                tag_name="unknown",
                attributes={},
                children_count=0
            )
    
    async def find_elements_by_landmark(self, landmark_text: str) -> List[ElementInfo]:
        """Find elements using text landmark"""
        try:
            elements = await self.page.query_selector_all(f"*:has-text('{landmark_text}')")
            element_infos = []
            
            for element in elements:
                info = await self.get_element_info(element)
                element_infos.append(info)
            
            return element_infos
            
        except Exception as e:
            logger.error(f"Error finding elements by landmark '{landmark_text}': {e}")
            return []
    
    async def find_nearest_elements(self, anchor_info: ElementInfo, 
                                   search_radius: float = 200.0) -> List[ElementInfo]:
        """Find elements within a radius of an anchor element"""
        if not anchor_info.bounds:
            return []
        
        try:
            # Get all visible elements on page
            all_elements = await self.page.query_selector_all("*")
            nearby_elements = []
            
            anchor_center = {
                'x': anchor_info.bounds['x'] + anchor_info.bounds['width'] / 2,
                'y': anchor_info.bounds['y'] + anchor_info.bounds['height'] / 2
            }
            
            for element in all_elements:
                try:
                    bounds = await element.bounding_box()
                    if bounds:
                        element_center = {
                            'x': bounds['x'] + bounds['width'] / 2,
                            'y': bounds['y'] + bounds['height'] / 2
                        }
                        
                        distance = ((element_center['x'] - anchor_center['x']) ** 2 + 
                                   (element_center['y'] - anchor_center['y']) ** 2) ** 0.5
                        
                        if distance <= search_radius:
                            element_info = await self.get_element_info(element)
                            if element_info.visible:
                                nearby_elements.append(element_info)
                                
                except Exception:
                    continue
            
            return nearby_elements
            
        except Exception as e:
            logger.error(f"Error finding nearby elements: {e}")
            return []
    
    async def navigate_from_landmark(self, landmark_info: ElementInfo, 
                                    navigation_pattern: str) -> List[ElementInfo]:
        """Navigate from landmark using pattern (parent, sibling, child, etc.)"""
        try:
            results = []
            
            if navigation_pattern == "parent":
                parent = await landmark_info.element.evaluate_handle("el => el.parentElement")
                if parent:
                    parent_info = await self.get_element_info(parent)
                    results.append(parent_info)
                    
            elif navigation_pattern == "siblings":
                siblings = await landmark_info.element.evaluate_handle_all("el => Array.from(el.parentElement.children)")
                for sibling in siblings:
                    if sibling != landmark_info.element:
                        sibling_info = await self.get_element_info(sibling)
                        results.append(sibling_info)
                        
            elif navigation_pattern == "children":
                children = await landmark_info.element.query_selector_all("*")
                for child in children:
                    child_info = await self.get_element_info(child)
                    results.append(child_info)
                    
            elif navigation_pattern.startswith("ancestor_"):
                levels = int(navigation_pattern.split("_")[1])
                current = landmark_info.element
                for _ in range(levels):
                    current = await current.evaluate_handle("el => el.parentElement")
                    if current:
                        ancestor_info = await self.get_element_info(current)
                        results.append(ancestor_info)
                    else:
                        break
            
            return results
            
        except Exception as e:
            logger.debug(f"Error navigating from landmark: {e}")
            return []


class ImageToVideoLandmarkStrategy:
    """Strategy for extracting metadata using 'Image to video' landmark"""
    
    def __init__(self, navigator: DOMNavigator, config):
        self.navigator = navigator
        self.config = config
    
    async def extract(self, context: ExtractionContext, field_name: str) -> ExtractionResult:
        """Extract metadata field using Image to video landmark"""
        try:
            # Find Image to video landmarks
            landmark_elements = await self.navigator.find_elements_by_landmark(
                self.config.image_to_video_text
            )
            
            if not landmark_elements:
                return ExtractionResult(
                    success=False,
                    field_name=field_name,
                    extracted_value=None,
                    confidence=0.0,
                    method_used="image_to_video_landmark",
                    validation_passed=False,
                    candidates=[],
                    error="No Image to video landmarks found"
                )
            
            candidates = []
            
            for i, landmark in enumerate(landmark_elements):
                if field_name == "generation_date":
                    result = await self._extract_date_from_landmark(landmark)
                elif field_name == "prompt":
                    result = await self._extract_prompt_from_landmark(landmark)
                else:
                    continue
                    
                if result:
                    candidates.append(result)
            
            if not candidates:
                return ExtractionResult(
                    success=False,
                    field_name=field_name,
                    extracted_value=None,
                    confidence=0.0,
                    method_used="image_to_video_landmark",
                    validation_passed=False,
                    candidates=[],
                    error=f"No candidates found for field {field_name}"
                )
            
            # Select best candidate
            best_candidate = max(candidates, key=lambda x: x['confidence'])
            
            return ExtractionResult(
                success=True,
                field_name=field_name,
                extracted_value=best_candidate['value'],
                confidence=best_candidate['confidence'],
                method_used="image_to_video_landmark",
                validation_passed=best_candidate['validation_passed'],
                candidates=candidates
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                field_name=field_name,
                extracted_value=None,
                confidence=0.0,
                method_used="image_to_video_landmark",
                validation_passed=False,
                candidates=[],
                error=str(e)
            )
    
    async def _extract_date_from_landmark(self, landmark_info: ElementInfo) -> Optional[Dict[str, Any]]:
        """Extract date using spatial navigation from Image to video landmark"""
        try:
            # Strategy 1: Look for Creation Time elements near the landmark
            nearby_elements = await self.navigator.find_nearest_elements(landmark_info, 300)
            
            for element_info in nearby_elements:
                if (element_info.text_content and 
                    self.config.creation_time_text in element_info.text_content):
                    
                    # Navigate to find associated date
                    date_candidates = await self._find_date_near_element(element_info)
                    if date_candidates:
                        best_date = max(date_candidates, key=lambda x: x['confidence'])
                        return {
                            'value': best_date['value'],
                            'confidence': best_date['confidence'],
                            'validation_passed': self._validate_date_format(best_date['value']),
                            'method': 'spatial_creation_time_navigation'
                        }
            
            # Strategy 2: Navigate through DOM structure
            parent_elements = await self.navigator.navigate_from_landmark(landmark_info, "parent")
            for parent in parent_elements:
                date_result = await self._search_date_in_container(parent)
                if date_result:
                    return date_result
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting date from landmark: {e}")
            return None
    
    async def _extract_prompt_from_landmark(self, landmark_info: ElementInfo) -> Optional[Dict[str, Any]]:
        """Extract prompt using spatial navigation from Image to video landmark"""
        try:
            # Strategy 1: Look for aria-describedby elements near landmark
            nearby_elements = await self.navigator.find_nearest_elements(landmark_info, 400)
            
            prompt_candidates = []
            
            for element_info in nearby_elements:
                if element_info.attributes.get('aria-describedby'):
                    prompt_text = await self._extract_full_prompt_text(element_info)
                    if prompt_text and len(prompt_text) > 20:
                        confidence = self._calculate_prompt_confidence(prompt_text, element_info)
                        prompt_candidates.append({
                            'value': prompt_text,
                            'confidence': confidence,
                            'element_info': element_info
                        })
            
            if prompt_candidates:
                best_prompt = max(prompt_candidates, key=lambda x: x['confidence'])
                return {
                    'value': best_prompt['value'],
                    'confidence': best_prompt['confidence'],
                    'validation_passed': len(best_prompt['value']) > 20,
                    'method': 'spatial_aria_navigation'
                }
            
            # Strategy 2: Search in ancestor containers
            ancestors = await self.navigator.navigate_from_landmark(landmark_info, "ancestor_3")
            for ancestor in ancestors:
                prompt_result = await self._search_prompt_in_container(ancestor)
                if prompt_result:
                    return prompt_result
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting prompt from landmark: {e}")
            return None
    
    async def _find_date_near_element(self, element_info: ElementInfo) -> List[Dict[str, Any]]:
        """Find date candidates near a Creation Time element"""
        candidates = []
        try:
            # Check sibling elements
            siblings = await self.navigator.navigate_from_landmark(element_info, "siblings")
            for sibling in siblings:
                if sibling.text_content and self._looks_like_date(sibling.text_content):
                    confidence = self._calculate_date_confidence(sibling.text_content, sibling)
                    candidates.append({
                        'value': sibling.text_content.strip(),
                        'confidence': confidence,
                        'element_info': sibling
                    })
            
            # Check child elements  
            children = await self.navigator.navigate_from_landmark(element_info, "children")
            for child in children:
                if child.text_content and self._looks_like_date(child.text_content):
                    confidence = self._calculate_date_confidence(child.text_content, child)
                    candidates.append({
                        'value': child.text_content.strip(),
                        'confidence': confidence,
                        'element_info': child
                    })
            
            return candidates
            
        except Exception as e:
            logger.debug(f"Error finding date candidates: {e}")
            return []
    
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        if not text:
            return False
        
        text = text.strip()
        
        # Common date patterns
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',  # 2024-01-15
            r'\d{1,2}/\d{1,2}/\d{4}',  # 1/15/2024
            r'\d{1,2}-\d{1,2}-\d{4}',  # 1-15-2024
            r'\w{3} \d{1,2}, \d{4}',   # Jan 15, 2024
            r'\d{1,2} \w{3} \d{4}',    # 15 Jan 2024
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _calculate_date_confidence(self, date_text: str, element_info: ElementInfo) -> float:
        """Calculate confidence score for a date candidate"""
        confidence = 0.5  # Base confidence
        
        # Format validation
        if self._validate_date_format(date_text):
            confidence += 0.3
        
        # Element visibility
        if element_info.visible:
            confidence += 0.1
        
        # Element position (prefer elements with bounds)
        if element_info.bounds:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _validate_date_format(self, date_text: str) -> bool:
        """Validate date format"""
        if not date_text:
            return False
        
        # Try to parse common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y', 
            '%m-%d-%Y',
            '%b %d, %Y',
            '%d %b %Y'
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(date_text.strip(), fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    async def _extract_full_prompt_text(self, element_info: ElementInfo) -> Optional[str]:
        """Extract full prompt text from element using multiple methods"""
        try:
            # Method 1: Direct text content
            if element_info.text_content and len(element_info.text_content) > 20:
                return element_info.text_content.strip()
            
            # Method 2: Inner text
            try:
                inner_text = await element_info.element.evaluate("el => el.innerText")
                if inner_text and len(inner_text) > 20:
                    return inner_text.strip()
            except:
                pass
            
            # Method 3: Title attribute
            title = element_info.attributes.get('title')
            if title and len(title) > 20:
                return title.strip()
            
            # Method 4: Check parent elements
            parent_elements = await self.navigator.navigate_from_landmark(element_info, "parent")
            for parent in parent_elements:
                if parent.text_content and len(parent.text_content) > 20:
                    return parent.text_content.strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting full prompt text: {e}")
            return None
    
    def _calculate_prompt_confidence(self, prompt_text: str, element_info: ElementInfo) -> float:
        """Calculate confidence score for a prompt candidate"""
        confidence = 0.6  # Base confidence
        
        # Length-based confidence
        if len(prompt_text) > 100:
            confidence += 0.2
        elif len(prompt_text) > 50:
            confidence += 0.1
        
        # Element attributes
        if element_info.attributes.get('aria-describedby'):
            confidence += 0.1
        
        # Element visibility
        if element_info.visible:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _search_date_in_container(self, container_info: ElementInfo) -> Optional[Dict[str, Any]]:
        """Search for date within a container element"""
        try:
            # Implementation for searching dates in container
            # This would search child elements for date patterns
            pass
        except Exception as e:
            logger.debug(f"Error searching date in container: {e}")
            return None
    
    async def _search_prompt_in_container(self, container_info: ElementInfo) -> Optional[Dict[str, Any]]:
        """Search for prompt within a container element"""
        try:
            # Implementation for searching prompts in container
            # This would search child elements for text patterns
            pass
        except Exception as e:
            logger.debug(f"Error searching prompt in container: {e}")
            return None
    
    def get_confidence(self, context: ExtractionContext) -> float:
        """Get confidence score for this strategy"""
        if context.landmark_elements:
            return 0.8  # High confidence when landmarks are available
        return 0.2
    
    def get_supported_fields(self) -> List[str]:
        """Get supported field names"""
        return ["generation_date", "prompt"]


class LandmarkExtractor:
    """Main landmark-based extraction engine"""
    
    def __init__(self, page, config):
        self.page = page
        self.config = config
        self.navigator = DOMNavigator(page)
        self.strategies = []
        
        # Initialize strategies
        try:
            from .extraction_strategies import ImageToVideoLandmarkStrategy as ImageToVideoStrategy
            self.strategies.append(ImageToVideoStrategy(self.navigator, config))
        except ImportError:
            # Handle import issues gracefully
            logger.warning("Could not import ImageToVideoLandmarkStrategy, using basic implementation")
            pass
    
    async def extract_metadata(self) -> Dict[str, Any]:
        """Extract all metadata using landmark-based strategies"""
        try:
            # Build extraction context
            context = await self._build_extraction_context()
            
            results = {}
            errors = []
            
            # Extract each required field
            fields_to_extract = ["generation_date", "prompt"]
            
            for field_name in fields_to_extract:
                try:
                    result = await self._extract_field(context, field_name)
                    if result.success:
                        results[field_name] = result.extracted_value
                        logger.debug(f"Successfully extracted {field_name}: {result.extracted_value[:50]}...")
                    else:
                        logger.warning(f"Failed to extract {field_name}: {result.error}")
                        errors.append(f"{field_name}: {result.error}")
                        results[field_name] = f"Unknown {field_name.replace('_', ' ').title()}"
                        
                except Exception as e:
                    logger.error(f"Error extracting {field_name}: {e}")
                    errors.append(f"{field_name}: {str(e)}")
                    results[field_name] = f"Unknown {field_name.replace('_', ' ').title()}"
            
            # Add extraction metadata
            results['extraction_method'] = 'landmark_based'
            results['extraction_timestamp'] = datetime.now().isoformat()
            results['extraction_errors'] = errors
            
            return results
            
        except Exception as e:
            logger.error(f"Error in landmark-based extraction: {e}")
            return {
                'generation_date': 'Unknown Date',
                'prompt': 'Unknown Prompt',
                'extraction_method': 'landmark_based',
                'extraction_timestamp': datetime.now().isoformat(),
                'extraction_errors': [str(e)]
            }
    
    async def _build_extraction_context(self) -> ExtractionContext:
        """Build context for extraction"""
        try:
            # Find Image to video landmarks
            landmark_elements = await self.navigator.find_elements_by_landmark(
                self.config.image_to_video_text
            )
            
            # Identify content area
            content_area = None
            if landmark_elements:
                # Use first landmark to estimate content area
                first_landmark = landmark_elements[0]
                if first_landmark.bounds:
                    content_area = {
                        'x': first_landmark.bounds['x'] - 200,
                        'y': first_landmark.bounds['y'] - 100,
                        'width': 800,
                        'height': 600
                    }
            
            return ExtractionContext(
                page=self.page,
                thumbnail_index=-1,  # Will be set by caller
                landmark_elements=landmark_elements,
                content_area=content_area,
                metadata_panels=[],  # Will be populated as needed
                confidence_threshold=0.7
            )
            
        except Exception as e:
            logger.error(f"Error building extraction context: {e}")
            return ExtractionContext(
                page=self.page,
                thumbnail_index=-1,
                landmark_elements=[],
                content_area=None,
                metadata_panels=[],
                confidence_threshold=0.7
            )
    
    async def _extract_field(self, context: ExtractionContext, field_name: str) -> ExtractionResult:
        """Extract a specific field using the best available strategy"""
        best_result = None
        best_confidence = 0.0
        
        for strategy in self.strategies:
            if field_name in strategy.get_supported_fields():
                strategy_confidence = strategy.get_confidence(context)
                
                if strategy_confidence > context.confidence_threshold:
                    result = await strategy.extract(context, field_name)
                    
                    if result.success and result.confidence > best_confidence:
                        best_confidence = result.confidence
                        best_result = result
        
        if best_result:
            return best_result
        
        # Return failure result
        return ExtractionResult(
            success=False,
            field_name=field_name,
            extracted_value=None,
            confidence=0.0,
            method_used="no_suitable_strategy",
            validation_passed=False,
            candidates=[],
            error="No suitable extraction strategy found"
        )