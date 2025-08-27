#!/usr/bin/env python3
"""
Metadata Extraction Debugger
Visual debugging tool for metadata extraction issues.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class MetadataExtractionDebugger:
    """Interactive debugger for metadata extraction issues"""
    
    def __init__(self, debug_output_folder: str = "/home/olereon/workspace/github.com/olereon/automaton/logs/debug"):
        self.debug_folder = Path(debug_output_folder)
        self.debug_folder.mkdir(parents=True, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug_file = self.debug_folder / f"metadata_debug_{self.session_id}.json"
        
        self.debug_results = {
            "session_info": {
                "start_time": datetime.now().isoformat(),
                "session_id": self.session_id
            },
            "page_analysis": {},
            "date_analysis": {},
            "prompt_analysis": {},
            "element_comparisons": {},
            "recommendations": []
        }
        
        logger.info(f"🔬 Metadata extraction debugger initialized: {self.debug_file}")
    
    async def analyze_page_for_metadata(self, page, config) -> Dict[str, Any]:
        """Comprehensive analysis of page elements for metadata extraction"""
        try:
            logger.info("🔍 Starting comprehensive page analysis for metadata extraction")
            
            # Get page info
            page_info = {
                "url": page.url,
                "title": await page.title(),
                "timestamp": datetime.now().isoformat()
            }
            
            self.debug_results["page_analysis"]["page_info"] = page_info
            
            # Analyze date/time elements
            date_analysis = await self._analyze_date_elements(page, config)
            self.debug_results["date_analysis"] = date_analysis
            
            # Analyze prompt elements
            prompt_analysis = await self._analyze_prompt_elements(page, config)
            self.debug_results["prompt_analysis"] = prompt_analysis
            
            # Compare what's selected vs what should be selected
            comparison_analysis = await self._compare_element_selections(page, config, date_analysis, prompt_analysis)
            self.debug_results["element_comparisons"] = comparison_analysis
            
            # Generate recommendations
            recommendations = self._generate_recommendations(date_analysis, prompt_analysis, comparison_analysis)
            self.debug_results["recommendations"] = recommendations
            
            # Save debug results
            self._save_debug_results()
            
            logger.info("✅ Page analysis completed successfully")
            return self.debug_results
            
        except Exception as e:
            logger.error(f"Error in page analysis: {e}")
            return {"error": str(e)}
    
    async def _analyze_date_elements(self, page, config) -> Dict[str, Any]:
        """Comprehensive analysis of date/time elements on the page"""
        logger.info("📅 Analyzing date/time elements...")
        
        analysis = {
            "landmark_analysis": {},
            "all_date_elements": [],
            "pattern_matches": {},
            "visibility_analysis": {},
            "selection_issues": []
        }
        
        try:
            # 1. Analyze "Creation Time" landmark elements
            creation_time_text = getattr(config, 'creation_time_text', 'Creation Time')
            landmark_elements = await page.query_selector_all(f"span:has-text('{creation_time_text}')")
            
            landmark_analysis = {
                "landmark_text": creation_time_text,
                "elements_found": len(landmark_elements),
                "elements_data": []
            }
            
            for i, element in enumerate(landmark_elements):
                try:
                    # Get comprehensive element data
                    element_data = await self._extract_comprehensive_element_data(element, f"landmark_{i}")
                    
                    # Try to find the associated date
                    associated_date = await self._find_associated_date(element)
                    element_data["associated_date"] = associated_date
                    
                    landmark_analysis["elements_data"].append(element_data)
                    
                except Exception as e:
                    logger.debug(f"Error analyzing landmark element {i}: {e}")
                    continue
            
            analysis["landmark_analysis"] = landmark_analysis
            
            # 2. Find ALL elements that contain date-like patterns
            all_date_elements = await self._find_all_date_elements(page)
            analysis["all_date_elements"] = all_date_elements
            
            # 3. Pattern matching analysis
            pattern_analysis = self._analyze_date_patterns(all_date_elements)
            analysis["pattern_matches"] = pattern_analysis
            
            # 4. Visibility and accessibility analysis
            visibility_analysis = await self._analyze_element_visibility(page, all_date_elements)
            analysis["visibility_analysis"] = visibility_analysis
            
            # 5. Identify selection issues
            selection_issues = self._identify_date_selection_issues(landmark_analysis, all_date_elements, pattern_analysis)
            analysis["selection_issues"] = selection_issues
            
            logger.info(f"📅 Date analysis complete: {len(landmark_elements)} landmarks, {len(all_date_elements)} date elements")
            
        except Exception as e:
            logger.error(f"Error in date analysis: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    async def _analyze_prompt_elements(self, page, config) -> Dict[str, Any]:
        """Comprehensive analysis of prompt elements on the page"""
        logger.info("💬 Analyzing prompt elements...")
        
        analysis = {
            "pattern_analysis": {},
            "all_prompt_elements": [],
            "extraction_methods": {},
            "truncation_analysis": {},
            "selection_issues": []
        }
        
        try:
            # 1. Analyze ellipsis pattern elements
            pattern = getattr(config, 'prompt_ellipsis_pattern', '</span>...')
            pattern_elements = await self._find_pattern_elements(page, pattern)
            
            pattern_analysis = {
                "pattern": pattern,
                "elements_found": len(pattern_elements),
                "elements_data": []
            }
            
            for i, element_info in enumerate(pattern_elements):
                try:
                    element_data = await self._extract_comprehensive_element_data(element_info["element"], f"pattern_{i}")
                    element_data["pattern_context"] = element_info["context"]
                    element_data["extracted_prompt"] = await self._extract_prompt_from_element(element_info["element"])
                    
                    pattern_analysis["elements_data"].append(element_data)
                    
                except Exception as e:
                    logger.debug(f"Error analyzing pattern element {i}: {e}")
                    continue
            
            analysis["pattern_analysis"] = pattern_analysis
            
            # 2. Find all elements with aria-describedby
            aria_elements = await page.query_selector_all("span[aria-describedby]")
            all_prompt_elements = []
            
            for i, element in enumerate(aria_elements):
                try:
                    element_data = await self._extract_comprehensive_element_data(element, f"aria_{i}")
                    element_data["extraction_attempts"] = await self._test_extraction_methods(element)
                    all_prompt_elements.append(element_data)
                    
                except Exception as e:
                    logger.debug(f"Error analyzing aria element {i}: {e}")
                    continue
            
            analysis["all_prompt_elements"] = all_prompt_elements
            
            # 3. Test different extraction methods
            extraction_methods = await self._test_prompt_extraction_methods(page, config)
            analysis["extraction_methods"] = extraction_methods
            
            # 4. Analyze truncation patterns
            truncation_analysis = self._analyze_prompt_truncation(all_prompt_elements)
            analysis["truncation_analysis"] = truncation_analysis
            
            # 5. Identify selection issues
            selection_issues = self._identify_prompt_selection_issues(pattern_analysis, all_prompt_elements)
            analysis["selection_issues"] = selection_issues
            
            logger.info(f"💬 Prompt analysis complete: {len(pattern_elements)} pattern matches, {len(all_prompt_elements)} aria elements")
            
        except Exception as e:
            logger.error(f"Error in prompt analysis: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    async def _extract_comprehensive_element_data(self, element, element_id: str) -> Dict[str, Any]:
        """Extract comprehensive data about an element"""
        try:
            data = {
                "element_id": element_id,
                "tag_name": await element.evaluate("el => el.tagName.toLowerCase()"),
                "text_content": (await element.text_content() or "")[:300],
                "inner_text": "",
                "inner_html": "",
                "attributes": {},
                "computed_styles": {},
                "bounding_box": {},
                "is_visible": False,
                "is_enabled": False,
                "parent_chain": [],
                "children_info": {}
            }
            
            # Try inner text
            try:
                data["inner_text"] = (await element.evaluate("el => el.innerText") or "")[:300]
            except:
                data["inner_text"] = data["text_content"]
            
            # Try inner HTML
            try:
                inner_html = await element.inner_html() or ""
                data["inner_html"] = inner_html[:500] if len(inner_html) < 1000 else inner_html[:500] + "..."
            except:
                pass
            
            # Get attributes
            try:
                data["attributes"] = await element.evaluate("""el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }""")
            except:
                pass
            
            # Get relevant computed styles
            try:
                data["computed_styles"] = await element.evaluate("""el => {
                    const style = window.getComputedStyle(el);
                    return {
                        display: style.display,
                        visibility: style.visibility,
                        opacity: style.opacity,
                        overflow: style.overflow,
                        textOverflow: style.textOverflow,
                        whiteSpace: style.whiteSpace,
                        maxWidth: style.maxWidth,
                        width: style.width,
                        height: style.height,
                        position: style.position,
                        zIndex: style.zIndex
                    };
                }""")
            except:
                pass
            
            # Get bounding box
            try:
                box = await element.bounding_box()
                if box:
                    data["bounding_box"] = box
            except:
                pass
            
            # Check visibility and enabled state
            try:
                data["is_visible"] = await element.is_visible()
                data["is_enabled"] = await element.is_enabled()
            except:
                pass
            
            # Get parent chain
            try:
                data["parent_chain"] = await element.evaluate("""el => {
                    const parents = [];
                    let current = el.parentElement;
                    let level = 0;
                    while (current && level < 5) {  // Limit to 5 levels
                        parents.push({
                            tag_name: current.tagName.toLowerCase(),
                            class_name: current.className,
                            id: current.id,
                            text_content: current.textContent ? current.textContent.substring(0, 50) : ''
                        });
                        current = current.parentElement;
                        level++;
                    }
                    return parents;
                }""")
            except:
                pass
            
            # Get children info
            try:
                data["children_info"] = await element.evaluate("""el => {
                    return {
                        children_count: el.children.length,
                        text_nodes: Array.from(el.childNodes)
                            .filter(node => node.nodeType === 3)
                            .map(node => node.textContent.trim())
                            .filter(text => text.length > 0)
                    };
                }""")
            except:
                pass
            
            return data
            
        except Exception as e:
            logger.debug(f"Error extracting element data: {e}")
            return {"element_id": element_id, "error": str(e)}
    
    async def _find_associated_date(self, creation_time_element) -> Dict[str, Any]:
        """Find the date associated with a Creation Time element"""
        try:
            # Method 1: Check sibling spans
            parent = await creation_time_element.evaluate_handle("el => el.parentElement")
            spans = await parent.query_selector_all("span")
            
            span_texts = []
            for span in spans:
                text = await span.text_content()
                span_texts.append(text.strip() if text else "EMPTY")
            
            # Look for date patterns in spans
            date_patterns = [
                r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}',  # "24 Aug 2025 01:37:01"
                r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}',        # "2025-08-24 01:37:01"
                r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}',    # "24/08/2025 01:37:01"
            ]
            
            found_dates = []
            for i, span_text in enumerate(span_texts):
                for pattern in date_patterns:
                    matches = re.findall(pattern, span_text)
                    if matches:
                        found_dates.append({
                            "span_index": i,
                            "span_text": span_text,
                            "pattern": pattern,
                            "matches": matches
                        })
            
            return {
                "all_spans": span_texts,
                "found_dates": found_dates,
                "method": "sibling_spans"
            }
            
        except Exception as e:
            return {"error": str(e), "method": "sibling_spans"}
    
    async def _find_all_date_elements(self, page) -> List[Dict[str, Any]]:
        """Find all elements on the page that might contain dates"""
        date_elements = []
        
        # Comprehensive selectors for finding date elements
        selectors = [
            "*:has-text('Creation Time')",
            "*:has-text('2025')", "*:has-text('2024')", "*:has-text('2026')",
            "*:has-text('Aug')", "*:has-text('August')",
            "*:has-text('Jan')", "*:has-text('Feb')", "*:has-text('Mar')",
            "*:has-text('Apr')", "*:has-text('May')", "*:has-text('Jun')",
            "*:has-text('Jul')", "*:has-text('Sep')", "*:has-text('Oct')",
            "*:has-text('Nov')", "*:has-text('Dec')",
            "span:contains(':')",  # Time patterns
            "*[title*='date']", "*[title*='time']", "*[title*='created']",
            "*[class*='date']", "*[class*='time']", "*[class*='created']",
            ".sc-cSMkSB", ".hUjUPD", ".gjlyBM"  # Known classes
        ]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    try:
                        element_data = await self._extract_comprehensive_element_data(element, f"{selector}")
                        element_data["selector_used"] = selector
                        date_elements.append(element_data)
                    except:
                        continue
            except:
                continue
        
        return date_elements
    
    def _analyze_date_patterns(self, date_elements: List[Dict]) -> Dict[str, Any]:
        """Analyze date patterns in found elements"""
        analysis = {
            "pattern_matches": {},
            "date_formats": {},
            "confidence_scores": []
        }
        
        date_patterns = {
            "full_datetime": r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}',
            "iso_datetime": r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}',
            "us_datetime": r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}',
            "date_only": r'\d{1,2}\s+\w{3}\s+\d{4}',
            "year_only": r'20\d{2}',
            "time_only": r'\d{1,2}:\d{2}:\d{2}'
        }
        
        for element in date_elements:
            text_content = element.get("text_content", "") + " " + element.get("inner_text", "")
            
            for pattern_name, pattern in date_patterns.items():
                matches = re.findall(pattern, text_content)
                if matches:
                    if pattern_name not in analysis["pattern_matches"]:
                        analysis["pattern_matches"][pattern_name] = []
                    
                    analysis["pattern_matches"][pattern_name].append({
                        "element_id": element.get("element_id"),
                        "matches": matches,
                        "is_visible": element.get("is_visible", False),
                        "selector": element.get("selector_used", "unknown")
                    })
        
        return analysis
    
    async def _analyze_element_visibility(self, page, elements: List[Dict]) -> Dict[str, Any]:
        """Analyze visibility and accessibility of elements"""
        visibility_stats = {
            "total_elements": len(elements),
            "visible_elements": 0,
            "hidden_elements": 0,
            "invisible_reasons": {},
            "layout_analysis": {}
        }
        
        for element in elements:
            if element.get("is_visible", False):
                visibility_stats["visible_elements"] += 1
            else:
                visibility_stats["hidden_elements"] += 1
                
                # Analyze why element is not visible
                styles = element.get("computed_styles", {})
                reasons = []
                
                if styles.get("display") == "none":
                    reasons.append("display_none")
                if styles.get("visibility") == "hidden":
                    reasons.append("visibility_hidden")
                if styles.get("opacity") == "0":
                    reasons.append("opacity_zero")
                
                reason_key = "_".join(reasons) if reasons else "unknown"
                if reason_key not in visibility_stats["invisible_reasons"]:
                    visibility_stats["invisible_reasons"][reason_key] = 0
                visibility_stats["invisible_reasons"][reason_key] += 1
        
        return visibility_stats
    
    def _identify_date_selection_issues(self, landmark_analysis: Dict, all_elements: List, pattern_analysis: Dict) -> List[Dict]:
        """Identify potential issues with date selection"""
        issues = []
        
        # Issue 1: Multiple Creation Time elements
        if landmark_analysis.get("elements_found", 0) > 1:
            issues.append({
                "type": "multiple_landmarks",
                "severity": "high",
                "description": f"Found {landmark_analysis['elements_found']} 'Creation Time' elements",
                "recommendation": "Need logic to select the correct one based on active thumbnail"
            })
        
        # Issue 2: No Creation Time elements found
        if landmark_analysis.get("elements_found", 0) == 0:
            issues.append({
                "type": "no_landmarks",
                "severity": "critical",
                "description": "No 'Creation Time' landmark elements found",
                "recommendation": "Check if landmark text is correct or page structure changed"
            })
        
        # Issue 3: Creation Time elements with no associated dates
        landmark_elements = landmark_analysis.get("elements_data", [])
        for i, element in enumerate(landmark_elements):
            associated_date = element.get("associated_date", {})
            if not associated_date.get("found_dates"):
                issues.append({
                    "type": "landmark_no_date",
                    "severity": "high",
                    "description": f"Creation Time element {i} has no associated date",
                    "element_id": element.get("element_id"),
                    "recommendation": "Check parent/sibling structure for date elements"
                })
        
        # Issue 4: All dates are the same (likely wrong selection)
        all_dates = []
        for element in landmark_elements:
            associated_date = element.get("associated_date", {})
            for found_date in associated_date.get("found_dates", []):
                all_dates.extend(found_date.get("matches", []))
        
        if len(set(all_dates)) == 1 and len(all_dates) > 1:
            issues.append({
                "type": "identical_dates",
                "severity": "high",
                "description": f"All found dates are identical: {all_dates[0]}",
                "recommendation": "Likely selecting wrong element - need thumbnail-specific selection"
            })
        
        return issues
    
    async def _find_pattern_elements(self, page, pattern: str) -> List[Dict]:
        """Find elements that contain a specific pattern"""
        elements_with_pattern = []
        
        try:
            # Get all div elements and check their HTML content
            divs = await page.query_selector_all("div")
            
            for i, div in enumerate(divs):
                try:
                    html_content = await div.evaluate("el => el.innerHTML")
                    if pattern in html_content:
                        elements_with_pattern.append({
                            "element": div,
                            "index": i,
                            "context": html_content[:200]
                        })
                except:
                    continue
        except Exception as e:
            logger.debug(f"Error finding pattern elements: {e}")
        
        return elements_with_pattern
    
    async def _extract_prompt_from_element(self, element) -> Dict[str, Any]:
        """Test different methods to extract prompt from an element"""
        extraction_results = {}
        
        # Method 1: text_content
        try:
            text_content = await element.text_content()
            extraction_results["text_content"] = {
                "result": text_content[:200] if text_content else "",
                "length": len(text_content) if text_content else 0
            }
        except Exception as e:
            extraction_results["text_content"] = {"error": str(e)}
        
        # Method 2: inner_text
        try:
            inner_text = await element.evaluate("el => el.innerText")
            extraction_results["inner_text"] = {
                "result": inner_text[:200] if inner_text else "",
                "length": len(inner_text) if inner_text else 0
            }
        except Exception as e:
            extraction_results["inner_text"] = {"error": str(e)}
        
        # Method 3: innerHTML with HTML removal
        try:
            inner_html = await element.inner_html()
            html_text = re.sub(r'<[^>]+>', '', inner_html) if inner_html else ""
            extraction_results["html_text"] = {
                "result": html_text[:200] if html_text else "",
                "length": len(html_text) if html_text else 0
            }
        except Exception as e:
            extraction_results["html_text"] = {"error": str(e)}
        
        # Method 4: Check for title attribute
        try:
            title = await element.get_attribute("title")
            extraction_results["title_attribute"] = {
                "result": title[:200] if title else "",
                "length": len(title) if title else 0
            }
        except Exception as e:
            extraction_results["title_attribute"] = {"error": str(e)}
        
        return extraction_results
    
    async def _test_extraction_methods(self, element) -> Dict[str, Any]:
        """Test different extraction methods on an element"""
        return await self._extract_prompt_from_element(element)
    
    async def _test_prompt_extraction_methods(self, page, config) -> Dict[str, Any]:
        """Test different prompt extraction methods"""
        methods = {}
        
        # Method 1: Current ellipsis pattern method
        pattern = getattr(config, 'prompt_ellipsis_pattern', '</span>...')
        try:
            pattern_results = await self._find_pattern_elements(page, pattern)
            methods["ellipsis_pattern"] = {
                "pattern": pattern,
                "elements_found": len(pattern_results),
                "success": len(pattern_results) > 0
            }
        except Exception as e:
            methods["ellipsis_pattern"] = {"error": str(e)}
        
        # Method 2: CSS selector method
        selector = getattr(config, 'prompt_selector', '.sc-jJRqov.cxtNJi span[aria-describedby]')
        try:
            elements = await page.query_selector_all(selector)
            methods["css_selector"] = {
                "selector": selector,
                "elements_found": len(elements),
                "success": len(elements) > 0
            }
        except Exception as e:
            methods["css_selector"] = {"error": str(e)}
        
        # Method 3: Generic aria-describedby
        try:
            elements = await page.query_selector_all("span[aria-describedby]")
            methods["aria_describedby"] = {
                "elements_found": len(elements),
                "success": len(elements) > 0
            }
        except Exception as e:
            methods["aria_describedby"] = {"error": str(e)}
        
        return methods
    
    def _analyze_prompt_truncation(self, prompt_elements: List[Dict]) -> Dict[str, Any]:
        """Analyze prompt truncation patterns"""
        analysis = {
            "truncation_indicators": [],
            "length_distribution": {},
            "truncation_patterns": {}
        }
        
        truncation_indicators = ["...", "…", "</span>...", "truncated", "ellipsis"]
        
        for element in prompt_elements:
            text_content = element.get("text_content", "")
            inner_html = element.get("inner_html", "")
            
            # Check for truncation indicators
            for indicator in truncation_indicators:
                if indicator in text_content or indicator in inner_html:
                    analysis["truncation_indicators"].append({
                        "element_id": element.get("element_id"),
                        "indicator": indicator,
                        "text_length": len(text_content),
                        "html_length": len(inner_html)
                    })
            
            # Length distribution
            length_bucket = f"{len(text_content)//20*20}-{len(text_content)//20*20+19}"
            if length_bucket not in analysis["length_distribution"]:
                analysis["length_distribution"][length_bucket] = 0
            analysis["length_distribution"][length_bucket] += 1
        
        return analysis
    
    def _identify_prompt_selection_issues(self, pattern_analysis: Dict, all_elements: List) -> List[Dict]:
        """Identify potential issues with prompt selection"""
        issues = []
        
        # Issue 1: No pattern elements found
        if pattern_analysis.get("elements_found", 0) == 0:
            issues.append({
                "type": "no_pattern_elements",
                "severity": "critical",
                "description": "No elements found with ellipsis pattern",
                "recommendation": "Check if pattern is correct or page structure changed"
            })
        
        # Issue 2: Multiple pattern elements
        if pattern_analysis.get("elements_found", 0) > 1:
            issues.append({
                "type": "multiple_pattern_elements",
                "severity": "medium",
                "description": f"Found {pattern_analysis['elements_found']} elements with pattern",
                "recommendation": "Need logic to select the correct element based on active thumbnail"
            })
        
        # Issue 3: All prompts appear truncated
        truncated_count = 0
        for element in all_elements:
            extraction_attempts = element.get("extraction_attempts", {})
            for method, result in extraction_attempts.items():
                if isinstance(result, dict) and result.get("result", ""):
                    if "..." in result["result"] or len(result["result"]) < 50:
                        truncated_count += 1
                        break
        
        if truncated_count > 0:
            issues.append({
                "type": "truncated_prompts",
                "severity": "high",
                "description": f"{truncated_count} elements appear to have truncated prompts",
                "recommendation": "Try CSS manipulation to reveal full text or find alternative sources"
            })
        
        return issues
    
    async def _compare_element_selections(self, page, config, date_analysis: Dict, prompt_analysis: Dict) -> Dict[str, Any]:
        """Compare what elements are being selected vs what should be selected"""
        comparison = {
            "current_selection": {},
            "should_select": {},
            "discrepancies": []
        }
        
        try:
            # Simulate current date extraction logic
            creation_time_elements = await page.query_selector_all(f"span:has-text('{getattr(config, 'creation_time_text', 'Creation Time')}')")
            current_date_selection = None
            
            if creation_time_elements:
                # This mimics the current logic - taking first element found
                first_element = creation_time_elements[0]
                parent = await first_element.evaluate_handle("el => el.parentElement")
                spans = await parent.query_selector_all("span")
                if len(spans) >= 2:
                    date_text = await spans[1].text_content()
                    current_date_selection = date_text.strip() if date_text else "Unknown"
            
            comparison["current_selection"]["date"] = current_date_selection
            
            # Simulate current prompt extraction logic
            prompt_elements = await page.query_selector_all("span[aria-describedby]")
            current_prompt_selection = None
            
            if prompt_elements:
                # This mimics taking the first element
                first_prompt_element = prompt_elements[0]
                prompt_text = await first_prompt_element.text_content()
                current_prompt_selection = prompt_text.strip() if prompt_text else "Unknown"
            
            comparison["current_selection"]["prompt"] = current_prompt_selection[:100] + "..." if current_prompt_selection and len(current_prompt_selection) > 100 else current_prompt_selection
            
            # Analyze what should be selected based on debug analysis
            should_select = self._determine_best_selections(date_analysis, prompt_analysis)
            comparison["should_select"] = should_select
            
            # Find discrepancies
            discrepancies = []
            
            if current_date_selection != should_select.get("date"):
                discrepancies.append({
                    "type": "date_selection",
                    "current": current_date_selection,
                    "should_be": should_select.get("date"),
                    "reason": should_select.get("date_reason")
                })
            
            if current_prompt_selection and should_select.get("prompt") and current_prompt_selection[:50] != should_select.get("prompt")[:50]:
                discrepancies.append({
                    "type": "prompt_selection",
                    "current": current_prompt_selection[:100] if current_prompt_selection else None,
                    "should_be": should_select.get("prompt", "")[:100],
                    "reason": should_select.get("prompt_reason")
                })
            
            comparison["discrepancies"] = discrepancies
            
        except Exception as e:
            comparison["error"] = str(e)
        
        return comparison
    
    def _determine_best_selections(self, date_analysis: Dict, prompt_analysis: Dict) -> Dict[str, Any]:
        """Determine what the best selections should be based on analysis"""
        best_selections = {}
        
        # Best date selection
        landmark_analysis = date_analysis.get("landmark_analysis", {})
        if landmark_analysis.get("elements_data"):
            # Find element with highest confidence
            best_date_element = None
            best_date_score = -1
            
            for element in landmark_analysis["elements_data"]:
                associated_date = element.get("associated_date", {})
                found_dates = associated_date.get("found_dates", [])
                
                if found_dates and element.get("is_visible", False):
                    score = 1.0 if element.get("is_visible") else 0.5
                    if score > best_date_score:
                        best_date_score = score
                        best_date_element = element
                        best_selections["date"] = found_dates[0]["matches"][0] if found_dates[0]["matches"] else "Unknown"
                        best_selections["date_reason"] = f"Visible Creation Time element with associated date"
        
        if "date" not in best_selections:
            best_selections["date"] = "Unknown"
            best_selections["date_reason"] = "No suitable date element found"
        
        # Best prompt selection
        pattern_analysis = prompt_analysis.get("pattern_analysis", {})
        all_prompt_elements = prompt_analysis.get("all_prompt_elements", [])
        
        best_prompt = None
        best_prompt_score = -1
        
        # Look for longest visible prompt
        for element in all_prompt_elements:
            if element.get("is_visible", False):
                extraction_attempts = element.get("extraction_attempts", {})
                for method, result in extraction_attempts.items():
                    if isinstance(result, dict) and result.get("length", 0) > best_prompt_score:
                        best_prompt_score = result["length"]
                        best_prompt = result.get("result", "Unknown")
                        best_selections["prompt"] = best_prompt
                        best_selections["prompt_reason"] = f"Longest visible prompt via {method}"
        
        if not best_prompt:
            best_selections["prompt"] = "Unknown"
            best_selections["prompt_reason"] = "No suitable prompt element found"
        
        return best_selections
    
    def _generate_recommendations(self, date_analysis: Dict, prompt_analysis: Dict, comparison_analysis: Dict) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Date extraction recommendations
        date_issues = date_analysis.get("selection_issues", [])
        for issue in date_issues:
            if issue["type"] == "multiple_landmarks":
                recommendations.append({
                    "category": "date_extraction",
                    "priority": "high",
                    "title": "Implement thumbnail-specific date selection",
                    "description": "Multiple 'Creation Time' elements found. Need logic to identify which belongs to the active thumbnail.",
                    "implementation": "Add visual indicators or DOM hierarchy analysis to find the active thumbnail's date."
                })
            elif issue["type"] == "no_landmarks":
                recommendations.append({
                    "category": "date_extraction",
                    "priority": "critical",
                    "title": "Fix landmark text or add fallback selectors",
                    "description": "No 'Creation Time' elements found. Page structure may have changed.",
                    "implementation": "Update landmark text or add CSS selector fallbacks."
                })
        
        # Prompt extraction recommendations
        prompt_issues = prompt_analysis.get("selection_issues", [])
        for issue in prompt_issues:
            if issue["type"] == "truncated_prompts":
                recommendations.append({
                    "category": "prompt_extraction",
                    "priority": "high",
                    "title": "Implement full prompt extraction",
                    "description": "Prompts appear truncated. Need methods to get full text.",
                    "implementation": "Try CSS manipulation, title attributes, or parent element traversal."
                })
        
        # Discrepancy recommendations
        discrepancies = comparison_analysis.get("discrepancies", [])
        for discrepancy in discrepancies:
            if discrepancy["type"] == "date_selection":
                recommendations.append({
                    "category": "date_selection_fix",
                    "priority": "high",
                    "title": "Fix date selection logic",
                    "description": f"Current selection '{discrepancy['current']}' should be '{discrepancy['should_be']}'",
                    "implementation": discrepancy.get("reason", "Update selection logic")
                })
        
        return recommendations
    
    def _save_debug_results(self):
        """Save debug results to file"""
        try:
            with open(self.debug_file, 'w', encoding='utf-8') as f:
                json.dump(self.debug_results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Debug results saved to: {self.debug_file}")
        except Exception as e:
            logger.error(f"Error saving debug results: {e}")
    
    def create_visual_report(self) -> str:
        """Create a human-readable visual report"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("METADATA EXTRACTION DEBUG REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Session info
        session_info = self.debug_results.get("session_info", {})
        report_lines.append(f"Session ID: {session_info.get('session_id', 'Unknown')}")
        report_lines.append(f"Start Time: {session_info.get('start_time', 'Unknown')}")
        report_lines.append("")
        
        # Page analysis summary
        page_analysis = self.debug_results.get("page_analysis", {})
        page_info = page_analysis.get("page_info", {})
        report_lines.append("PAGE ANALYSIS:")
        report_lines.append(f"  URL: {page_info.get('url', 'Unknown')}")
        report_lines.append(f"  Title: {page_info.get('title', 'Unknown')}")
        report_lines.append("")
        
        # Date analysis summary
        date_analysis = self.debug_results.get("date_analysis", {})
        landmark_analysis = date_analysis.get("landmark_analysis", {})
        report_lines.append("DATE EXTRACTION ANALYSIS:")
        report_lines.append(f"  Creation Time elements found: {landmark_analysis.get('elements_found', 0)}")
        
        all_date_elements = date_analysis.get("all_date_elements", [])
        report_lines.append(f"  Total date-like elements: {len(all_date_elements)}")
        
        selection_issues = date_analysis.get("selection_issues", [])
        report_lines.append(f"  Issues identified: {len(selection_issues)}")
        for issue in selection_issues[:3]:  # Show first 3 issues
            report_lines.append(f"    - {issue.get('type', 'unknown')}: {issue.get('description', 'No description')}")
        report_lines.append("")
        
        # Prompt analysis summary
        prompt_analysis = self.debug_results.get("prompt_analysis", {})
        pattern_analysis = prompt_analysis.get("pattern_analysis", {})
        report_lines.append("PROMPT EXTRACTION ANALYSIS:")
        report_lines.append(f"  Pattern elements found: {pattern_analysis.get('elements_found', 0)}")
        
        all_prompt_elements = prompt_analysis.get("all_prompt_elements", [])
        report_lines.append(f"  Total prompt elements: {len(all_prompt_elements)}")
        
        prompt_issues = prompt_analysis.get("selection_issues", [])
        report_lines.append(f"  Issues identified: {len(prompt_issues)}")
        for issue in prompt_issues[:3]:
            report_lines.append(f"    - {issue.get('type', 'unknown')}: {issue.get('description', 'No description')}")
        report_lines.append("")
        
        # Recommendations
        recommendations = self.debug_results.get("recommendations", [])
        report_lines.append("RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:5], 1):  # Show first 5
            report_lines.append(f"  {i}. {rec.get('title', 'No title')} [{rec.get('priority', 'medium')}]")
            report_lines.append(f"     {rec.get('description', 'No description')}")
            report_lines.append("")
        
        report_lines.append(f"Full debug data saved to: {self.debug_file}")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


# Convenience function for quick debugging
async def debug_metadata_extraction(page, config):
    """Quick function to debug metadata extraction"""
    debugger = MetadataExtractionDebugger()
    results = await debugger.analyze_page_for_metadata(page, config)
    
    report = debugger.create_visual_report()
    print(report)
    
    return results, report