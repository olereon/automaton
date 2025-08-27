#!/usr/bin/env python3
"""
Generation Debug Logger
Comprehensive debugging system for generation download metadata extraction.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ElementDebugInfo:
    """Debug information for a page element"""
    element_index: int
    selector: str
    tag_name: str
    text_content: str
    inner_text: str
    inner_html: str
    attributes: Dict[str, str]
    computed_styles: Dict[str, str]
    bounding_box: Dict[str, float]
    is_visible: bool
    is_enabled: bool
    parent_info: Optional[Dict[str, Any]] = None
    children_count: int = 0


@dataclass
class DateExtractionDebug:
    """Debug information for date extraction process"""
    timestamp: str
    thumbnail_index: int
    method: str
    landmark_text: str
    elements_found: int
    candidates: List[Dict[str, Any]]
    selected_date: str
    selection_reason: str
    success: bool
    error: Optional[str] = None


@dataclass
class PromptExtractionDebug:
    """Debug information for prompt extraction process"""
    timestamp: str
    thumbnail_index: int
    method: str
    pattern: str
    elements_searched: int
    candidates: List[Dict[str, Any]]
    selected_prompt: str
    selection_reason: str
    success: bool
    error: Optional[str] = None


class GenerationDebugLogger:
    """Enhanced debug logging system for generation downloads"""
    
    def __init__(self, logs_folder: str = "/home/olereon/workspace/github.com/olereon/automaton/logs"):
        self.logs_folder = Path(logs_folder)
        self.logs_folder.mkdir(parents=True, exist_ok=True)
        
        # Create session-specific debug log file
        session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug_log_file = self.logs_folder / f"debug_generation_downloads_{session_timestamp}.json"
        
        # Initialize debug data structure
        self.debug_data = {
            "session_info": {
                "start_time": datetime.now().isoformat(),
                "session_id": session_timestamp,
                "version": "1.0.0"
            },
            "configuration": {},
            "steps": [],
            "element_snapshots": [],
            "date_extractions": [],
            "prompt_extractions": [],
            "thumbnail_clicks": [],
            "file_naming": [],
            "page_states": []
        }
        
        logger.info(f"🔍 Debug logger initialized: {self.debug_log_file}")
    
    def log_configuration(self, config_dict: Dict[str, Any]):
        """Log the configuration used for this session"""
        self.debug_data["configuration"] = config_dict
        logger.debug("Configuration logged to debug file")
    
    def log_step(self, thumbnail_index: int, step_type: str, data: Dict[str, Any], 
                 success: bool = True, error: str = None):
        """Log a general debug step"""
        step_data = {
            "timestamp": datetime.now().isoformat(),
            "thumbnail_index": thumbnail_index,
            "step_type": step_type,
            "data": data,
            "success": success,
            "error": error
        }
        self.debug_data["steps"].append(step_data)
        
        # Also save to file immediately for real-time debugging
        self._save_debug_file()
    
    async def log_page_elements(self, page, thumbnail_index: int, search_patterns: List[str]):
        """Log all elements on the page that match date/time search patterns"""
        try:
            elements_info = []
            
            # Define comprehensive selectors for finding date/time elements
            comprehensive_selectors = [
                # Text-based selectors
                "*:has-text('Creation Time')",
                "*:has-text('creation time')",
                "*:has-text('Created')",
                "*:has-text('Date')",
                "*:has-text('Time')",
                
                # Specific pattern selectors
                "span:contains('20')",  # Year patterns
                "span:contains('Aug')",  # Month patterns
                "span:contains('2025')",  # Current year
                
                # Aria and data attributes
                "span[aria-describedby]",
                "span[data-date]",
                "span[data-time]",
                "[title*='date']",
                "[title*='time']",
                
                # CSS class patterns
                ".date", ".time", ".created", ".timestamp",
                "*[class*='date']", "*[class*='time']", "*[class*='created']",
                
                # Common UI patterns
                ".sc-cSMkSB", ".hUjUPD", ".gjlyBM",  # Known classes from selectors
                ".metadata", ".info", ".details"
            ]
            
            for i, selector in enumerate(comprehensive_selectors):
                try:
                    elements = await page.query_selector_all(selector)
                    
                    for j, element in enumerate(elements):
                        try:
                            # Extract comprehensive element information
                            element_info = await self._extract_element_info(element, f"{selector}[{j}]")
                            element_info.element_index = len(elements_info)
                            elements_info.append(asdict(element_info))
                            
                        except Exception as e:
                            logger.debug(f"Error extracting info for element {j} of selector {selector}: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error with selector '{selector}': {e}")
                    continue
            
            # Save element snapshot
            self.debug_data["element_snapshots"].append({
                "timestamp": datetime.now().isoformat(),
                "thumbnail_index": thumbnail_index,
                "total_elements_found": len(elements_info),
                "search_patterns": search_patterns,
                "elements": elements_info
            })
            
            # Analyze potential date elements
            date_candidates = self._analyze_date_candidates(elements_info)
            
            logger.info(f"🔍 Found {len(elements_info)} elements, {len(date_candidates)} potential date elements")
            
            return elements_info, date_candidates
            
        except Exception as e:
            logger.error(f"Error logging page elements: {e}")
            return [], []
    
    async def _extract_element_info(self, element, selector: str) -> ElementDebugInfo:
        """Extract comprehensive information about a page element"""
        try:
            # Basic element properties
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            text_content = await element.text_content() or ""
            
            # Try different text extraction methods
            inner_text = ""
            try:
                inner_text = await element.evaluate("el => el.innerText") or ""
            except:
                inner_text = text_content
            
            inner_html = ""
            try:
                inner_html = await element.inner_html() or ""
            except:
                pass
            
            # Get all attributes
            attributes = {}
            try:
                attributes = await element.evaluate("""el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }""")
            except:
                pass
            
            # Get computed styles for layout debugging
            computed_styles = {}
            try:
                computed_styles = await element.evaluate("""el => {
                    const style = window.getComputedStyle(el);
                    return {
                        display: style.display,
                        visibility: style.visibility,
                        opacity: style.opacity,
                        position: style.position,
                        width: style.width,
                        height: style.height,
                        overflow: style.overflow,
                        textOverflow: style.textOverflow,
                        whiteSpace: style.whiteSpace,
                        color: style.color,
                        fontSize: style.fontSize,
                        fontWeight: style.fontWeight
                    };
                }""")
            except:
                pass
            
            # Get bounding box
            bounding_box = {}
            try:
                box = await element.bounding_box()
                if box:
                    bounding_box = {
                        "x": box["x"],
                        "y": box["y"],
                        "width": box["width"],
                        "height": box["height"]
                    }
            except:
                pass
            
            # Check visibility and enabled state
            is_visible = False
            is_enabled = False
            try:
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
            except:
                pass
            
            # Get parent information
            parent_info = None
            try:
                parent_info = await element.evaluate("""el => {
                    const parent = el.parentElement;
                    if (parent) {
                        return {
                            tag_name: parent.tagName.toLowerCase(),
                            class_name: parent.className,
                            id: parent.id,
                            text_content: parent.textContent ? parent.textContent.substring(0, 100) : ''
                        };
                    }
                    return null;
                }""")
            except:
                pass
            
            # Count children
            children_count = 0
            try:
                children_count = await element.evaluate("el => el.children.length")
            except:
                pass
            
            return ElementDebugInfo(
                element_index=0,  # Will be set by caller
                selector=selector,
                tag_name=tag_name,
                text_content=text_content[:200],  # Truncate for readability
                inner_text=inner_text[:200],
                inner_html=inner_html[:300] if len(inner_html) < 1000 else inner_html[:300] + "...",
                attributes=attributes,
                computed_styles=computed_styles,
                bounding_box=bounding_box,
                is_visible=is_visible,
                is_enabled=is_enabled,
                parent_info=parent_info,
                children_count=children_count
            )
            
        except Exception as e:
            logger.debug(f"Error extracting element info: {e}")
            # Return minimal info on error
            return ElementDebugInfo(
                element_index=0,
                selector=selector,
                tag_name="unknown",
                text_content="ERROR",
                inner_text="ERROR",
                inner_html="ERROR",
                attributes={},
                computed_styles={},
                bounding_box={},
                is_visible=False,
                is_enabled=False
            )
    
    def _analyze_date_candidates(self, elements_info: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze elements to find potential date candidates"""
        date_candidates = []
        
        # Date patterns to look for
        date_patterns = [
            r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}',  # "24 Aug 2025 01:37:01"
            r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}',        # "2025-08-24 01:37:01"
            r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}',    # "24/08/2025 01:37:01"
            r'\d{4}-\d{2}-\d{2}',                               # "2025-08-24"
            r'\d{1,2}\s+\w{3}\s+\d{4}',                         # "24 Aug 2025"
            r'\w{3}\s+\d{1,2},?\s+\d{4}',                       # "Aug 24, 2025"
            r'\d{1,2}:\d{2}:\d{2}',                             # "01:37:01"
            r'Creation Time',                                   # Landmark text
            r'20\d{2}',                                         # Any year 2000+
        ]
        
        import re
        
        for element in elements_info:
            text_to_check = [
                element.get('text_content', ''),
                element.get('inner_text', ''),
                element.get('inner_html', ''),
                str(element.get('attributes', {}))
            ]
            
            for text in text_to_check:
                if not text:
                    continue
                    
                for pattern in date_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        candidate = {
                            "element_index": element["element_index"],
                            "selector": element["selector"],
                            "pattern_matched": pattern,
                            "matches": matches,
                            "full_text": text[:100],
                            "is_visible": element.get("is_visible", False),
                            "tag_name": element.get("tag_name", "unknown"),
                            "attributes": element.get("attributes", {}),
                            "confidence": self._calculate_date_confidence(pattern, matches, text, element)
                        }
                        date_candidates.append(candidate)
        
        # Sort by confidence score
        date_candidates.sort(key=lambda x: x["confidence"], reverse=True)
        
        return date_candidates
    
    def _calculate_date_confidence(self, pattern: str, matches: List[str], text: str, element: Dict) -> float:
        """Calculate confidence score for a date candidate"""
        confidence = 0.0
        
        # Base confidence based on pattern type
        if 'Creation Time' in pattern:
            confidence += 0.9
        elif r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}' in pattern:
            confidence += 0.8
        elif 'Time' in pattern:
            confidence += 0.6
        elif '20\\d{2}' in pattern:
            confidence += 0.3
        else:
            confidence += 0.5
        
        # Boost if element is visible
        if element.get("is_visible", False):
            confidence += 0.2
        
        # Boost if element has relevant attributes
        attributes = element.get("attributes", {})
        if any(key in str(attributes).lower() for key in ['date', 'time', 'created']):
            confidence += 0.2
        
        # Boost if text contains Creation Time nearby
        if 'creation time' in text.lower():
            confidence += 0.3
        
        # Penalize if text is too short or too long
        if len(text) < 5:
            confidence -= 0.2
        elif len(text) > 200:
            confidence -= 0.1
        
        return min(confidence, 1.0)
    
    def log_date_extraction(self, thumbnail_index: int, method: str, landmark_text: str,
                           elements_found: int, candidates: List[Dict], selected_date: str,
                           selection_reason: str, success: bool = True, error: str = None):
        """Log detailed date extraction process"""
        extraction_debug = DateExtractionDebug(
            timestamp=datetime.now().isoformat(),
            thumbnail_index=thumbnail_index,
            method=method,
            landmark_text=landmark_text,
            elements_found=elements_found,
            candidates=candidates,
            selected_date=selected_date,
            selection_reason=selection_reason,
            success=success,
            error=error
        )
        
        self.debug_data["date_extractions"].append(asdict(extraction_debug))
        logger.debug(f"Date extraction logged: {method} -> {selected_date}")
    
    def log_prompt_extraction(self, thumbnail_index: int, method: str, pattern: str,
                             elements_searched: int, candidates: List[Dict], selected_prompt: str,
                             selection_reason: str, success: bool = True, error: str = None):
        """Log detailed prompt extraction process"""
        extraction_debug = PromptExtractionDebug(
            timestamp=datetime.now().isoformat(),
            thumbnail_index=thumbnail_index,
            method=method,
            pattern=pattern,
            elements_searched=elements_searched,
            candidates=candidates,
            selected_prompt=selected_prompt[:200],  # Truncate for readability
            selection_reason=selection_reason,
            success=success,
            error=error
        )
        
        self.debug_data["prompt_extractions"].append(asdict(extraction_debug))
        logger.debug(f"Prompt extraction logged: {method} -> {selected_prompt[:50]}...")
    
    def log_thumbnail_click(self, thumbnail_index: int, thumbnail_selector: str, click_success: bool):
        """Log thumbnail click attempts"""
        click_data = {
            "timestamp": datetime.now().isoformat(),
            "thumbnail_index": thumbnail_index,
            "selector": thumbnail_selector,
            "success": click_success
        }
        
        self.debug_data["thumbnail_clicks"].append(click_data)
        logger.debug(f"Thumbnail click logged: {thumbnail_selector} -> {click_success}")
    
    def log_metadata_extraction(self, thumbnail_index: int, extraction_method: str, 
                               extracted_data: Dict[str, Any], success: bool = True):
        """Log metadata extraction results"""
        metadata_log = {
            "timestamp": datetime.now().isoformat(),
            "thumbnail_index": thumbnail_index,
            "extraction_method": extraction_method,
            "extracted_data": extracted_data,
            "success": success,
            "data_quality": self._assess_metadata_quality(extracted_data)
        }
        
        self.debug_data["steps"].append({
            "timestamp": datetime.now().isoformat(),
            "thumbnail_index": thumbnail_index,
            "step_type": "METADATA_EXTRACTION",
            "data": metadata_log,
            "success": success
        })
    
    def log_file_naming(self, thumbnail_index: int, original_filename: str, new_filename: str,
                       naming_data: Dict[str, Any], success: bool = True, error: str = None):
        """Log file naming process"""
        naming_log = {
            "timestamp": datetime.now().isoformat(),
            "thumbnail_index": thumbnail_index,
            "original_filename": original_filename,
            "new_filename": new_filename,
            "naming_data": naming_data,
            "success": success,
            "error": error
        }
        
        self.debug_data["file_naming"].append(naming_log)
        logger.debug(f"File naming logged: {original_filename} -> {new_filename}")
    
    def _assess_metadata_quality(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of extracted metadata"""
        quality_score = 0.0
        issues = []
        
        # Check generation date
        gen_date = metadata.get('generation_date', 'Unknown')
        if gen_date == 'Unknown Date' or gen_date == 'Unknown':
            issues.append("Date not extracted")
        elif 'Unknown' in gen_date:
            issues.append("Date partially extracted")
            quality_score += 0.3
        else:
            quality_score += 0.5
        
        # Check prompt
        prompt = metadata.get('prompt', 'Unknown')
        if prompt == 'Unknown Prompt' or prompt == 'Unknown':
            issues.append("Prompt not extracted")
        elif len(prompt) < 20:
            issues.append("Prompt too short")
            quality_score += 0.2
        elif '...' in prompt:
            issues.append("Prompt appears truncated")
            quality_score += 0.3
        else:
            quality_score += 0.5
        
        return {
            "quality_score": quality_score,
            "issues": issues,
            "date_length": len(str(gen_date)),
            "prompt_length": len(str(prompt))
        }
    
    async def create_visual_debug_report(self, page, thumbnail_index: int) -> str:
        """Create a visual debug report with screenshots"""
        try:
            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = self.logs_folder / f"debug_screenshot_{thumbnail_index}_{timestamp}.png"
            
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            # Log page state
            page_state = {
                "timestamp": datetime.now().isoformat(),
                "thumbnail_index": thumbnail_index,
                "url": page.url,
                "title": await page.title(),
                "screenshot_path": str(screenshot_path),
                "viewport": await page.evaluate("() => ({ width: window.innerWidth, height: window.innerHeight })")
            }
            
            self.debug_data["page_states"].append(page_state)
            
            logger.info(f"📸 Debug screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Error creating visual debug report: {e}")
            return ""
    
    def _save_debug_file(self):
        """Save debug data to JSON file"""
        try:
            with open(self.debug_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.debug_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving debug file: {e}")
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """Get a summary of debug information"""
        return {
            "session_id": self.debug_data["session_info"]["session_id"],
            "start_time": self.debug_data["session_info"]["start_time"],
            "total_steps": len(self.debug_data["steps"]),
            "date_extractions": len(self.debug_data["date_extractions"]),
            "prompt_extractions": len(self.debug_data["prompt_extractions"]),
            "thumbnail_clicks": len(self.debug_data["thumbnail_clicks"]),
            "element_snapshots": len(self.debug_data["element_snapshots"]),
            "page_states": len(self.debug_data["page_states"]),
            "debug_log_file": str(self.debug_log_file)
        }
    
    def finalize_debug_session(self):
        """Finalize and save the complete debug session"""
        self.debug_data["session_info"]["end_time"] = datetime.now().isoformat()
        self._save_debug_file()
        
        summary = self.get_debug_summary()
        logger.info(f"🔍 Debug session finalized: {summary}")
        
        return summary