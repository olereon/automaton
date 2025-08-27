#!/usr/bin/env python3
"""
Date Extraction Fix Testing Tool
Specifically tests and debugs date extraction issues with comprehensive analysis
"""

import asyncio
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from playwright.async_api import async_playwright
from utils.generation_download_manager import GenerationDownloadConfig
from utils.generation_debug_logger import GenerationDebugLogger
from utils.metadata_extraction_debugger import MetadataExtractionDebugger
from utils.element_selection_visualizer import ElementSelectionVisualizer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DateExtractionFixTester:
    """Specialized tool for testing and fixing date extraction issues"""
    
    def __init__(self, config):
        self.config = config
        self.debug_logger = GenerationDebugLogger()
        self.extraction_debugger = MetadataExtractionDebugger()
        self.visualizer = ElementSelectionVisualizer()
        
        self.test_results = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "tests": [],
            "issues_found": [],
            "recommendations": []
        }
    
    async def run_comprehensive_date_fix_test(self, page):
        """Run comprehensive date extraction fix testing"""
        print("\n🔧 COMPREHENSIVE DATE EXTRACTION FIX TESTING")
        print("="*70)
        
        try:
            # Test 1: Baseline element discovery
            print("\n1️⃣ BASELINE ELEMENT DISCOVERY")
            print("-"*50)
            await self._test_baseline_element_discovery(page)
            
            # Test 2: Creation Time element analysis
            print("\n2️⃣ CREATION TIME ELEMENT ANALYSIS")  
            print("-"*50)
            await self._test_creation_time_elements(page)
            
            # Test 3: Date pattern matching
            print("\n3️⃣ DATE PATTERN MATCHING ANALYSIS")
            print("-"*50)
            await self._test_date_pattern_matching(page)
            
            # Test 4: Element selection strategy testing
            print("\n4️⃣ ELEMENT SELECTION STRATEGY TESTING")
            print("-"*50)
            await self._test_selection_strategies(page)
            
            # Test 5: Visual element mapping
            print("\n5️⃣ VISUAL ELEMENT MAPPING")
            print("-"*50)
            await self._create_visual_element_map(page)
            
            # Test 6: Multi-thumbnail comparison
            print("\n6️⃣ MULTI-THUMBNAIL COMPARISON TEST")
            print("-"*50)
            await self._test_multi_thumbnail_date_extraction(page)
            
            # Generate comprehensive report
            await self._generate_comprehensive_report()
            
        except Exception as e:
            logger.error(f"Error in comprehensive test: {e}")
            import traceback
            traceback.print_exc()
    
    async def _test_baseline_element_discovery(self, page):
        """Test basic element discovery capabilities"""
        print("🔍 Discovering all relevant elements on the page...")
        
        try:
            # Use the debug logger to discover elements
            search_patterns = ["Creation Time", "2025", "Aug", "..."]
            elements_info, date_candidates = await self.debug_logger.log_page_elements(
                page, -1, search_patterns
            )
            
            print(f"   📊 Total elements discovered: {len(elements_info)}")
            print(f"   📅 Date candidates found: {len(date_candidates)}")
            
            # Show top candidates
            if date_candidates:
                print("   🏆 Top 5 Date Candidates:")
                for i, candidate in enumerate(date_candidates[:5]):
                    print(f"      {i+1}. Confidence: {candidate['confidence']:.2f}")
                    print(f"         Pattern: {candidate['pattern_matched']}")
                    print(f"         Text: '{candidate['full_text'][:50]}...'")
                    print(f"         Visible: {candidate['is_visible']}")
                    print()
            
            self.test_results["tests"].append({
                "test_name": "baseline_discovery",
                "elements_found": len(elements_info),
                "date_candidates": len(date_candidates),
                "top_candidate": date_candidates[0] if date_candidates else None
            })
            
        except Exception as e:
            print(f"   ❌ Error in baseline discovery: {e}")
            self.test_results["issues_found"].append({
                "test": "baseline_discovery",
                "error": str(e)
            })
    
    async def _test_creation_time_elements(self, page):
        """Test Creation Time element detection and analysis"""
        print("🕐 Analyzing Creation Time elements...")
        
        try:
            # Find all Creation Time elements
            creation_time_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
            print(f"   📋 Found {len(creation_time_elements)} Creation Time elements")
            
            if not creation_time_elements:
                issue = "No Creation Time elements found - check landmark text"
                print(f"   ❌ CRITICAL ISSUE: {issue}")
                self.test_results["issues_found"].append({
                    "test": "creation_time_elements",
                    "severity": "critical",
                    "issue": issue,
                    "recommendation": f"Verify that '{self.config.creation_time_text}' is the correct landmark text"
                })
                return
            
            # Analyze each Creation Time element
            element_analysis = []
            for i, element in enumerate(creation_time_elements):
                print(f"\n   🔍 Analyzing Creation Time Element {i+1}:")
                
                # Check visibility
                is_visible = await element.is_visible()
                print(f"      Visible: {is_visible}")
                
                # Get parent and find spans
                parent = await element.evaluate_handle("el => el.parentElement")
                spans = await parent.query_selector_all("span")
                print(f"      Parent spans: {len(spans)}")
                
                # Analyze each span
                span_data = []
                for j, span in enumerate(spans):
                    span_text = await span.text_content()
                    span_visible = await span.is_visible()
                    span_data.append({
                        "index": j,
                        "text": span_text.strip() if span_text else "",
                        "visible": span_visible,
                        "length": len(span_text) if span_text else 0
                    })
                    print(f"         Span {j}: '{span_text[:30]}...' (visible: {span_visible})")
                
                # Check for date in span[1] (typical pattern)
                potential_date = ""
                if len(spans) >= 2:
                    potential_date = await spans[1].text_content()
                    date_quality = self._analyze_date_quality(potential_date)
                    print(f"      📅 Potential Date (span[1]): '{potential_date}'")
                    print(f"         Date Quality: {date_quality}")
                
                element_analysis.append({
                    "element_index": i,
                    "visible": is_visible,
                    "span_count": len(spans),
                    "spans": span_data,
                    "potential_date": potential_date,
                    "date_quality": self._analyze_date_quality(potential_date) if potential_date else "no_date"
                })
            
            # Identify issues
            visible_count = sum(1 for e in element_analysis if e["visible"])
            if visible_count == 0:
                self.test_results["issues_found"].append({
                    "test": "creation_time_elements",
                    "severity": "high",
                    "issue": "No visible Creation Time elements",
                    "recommendation": "Check if elements are hidden by CSS or page structure"
                })
            elif visible_count > 1:
                self.test_results["issues_found"].append({
                    "test": "creation_time_elements",
                    "severity": "medium",
                    "issue": f"Multiple visible Creation Time elements ({visible_count})",
                    "recommendation": "Need logic to select the correct element based on active thumbnail"
                })
            
            # Check for date extraction issues
            dates_found = [e["potential_date"] for e in element_analysis if e["potential_date"]]
            unique_dates = list(set(dates_found))
            
            if len(dates_found) > 1 and len(unique_dates) == 1:
                self.test_results["issues_found"].append({
                    "test": "creation_time_elements",
                    "severity": "high",
                    "issue": f"All Creation Time elements have identical dates: {unique_dates[0]}",
                    "recommendation": "Likely selecting wrong element - need thumbnail-specific selection"
                })
            
            self.test_results["tests"].append({
                "test_name": "creation_time_elements",
                "total_elements": len(creation_time_elements),
                "visible_elements": visible_count,
                "unique_dates": len(unique_dates),
                "element_analysis": element_analysis
            })
            
        except Exception as e:
            print(f"   ❌ Error in Creation Time analysis: {e}")
            self.test_results["issues_found"].append({
                "test": "creation_time_elements",
                "error": str(e)
            })
    
    def _analyze_date_quality(self, date_text: str) -> str:
        """Analyze the quality of a potential date string"""
        if not date_text:
            return "no_date"
        
        date_text = date_text.strip()
        
        # Check for various date patterns
        patterns = {
            "full_datetime": r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}',  # "24 Aug 2025 01:37:01"
            "iso_datetime": r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}',        # "2025-08-24 01:37:01"
            "date_only": r'\d{1,2}\s+\w{3}\s+\d{4}',                           # "24 Aug 2025"
            "year_only": r'20\d{2}',                                           # "2025"
            "time_only": r'\d{1,2}:\d{2}:\d{2}',                               # "01:37:01"
        }
        
        for pattern_name, pattern in patterns.items():
            if re.match(pattern, date_text):
                return pattern_name
        
        # Check for common non-date patterns
        if "creation time" in date_text.lower():
            return "landmark_text"
        elif date_text.lower() in ["unknown", "unknown date", ""]:
            return "unknown_placeholder"
        elif len(date_text) < 5:
            return "too_short"
        elif len(date_text) > 50:
            return "too_long"
        else:
            return "unrecognized_format"
    
    async def _test_date_pattern_matching(self, page):
        """Test comprehensive date pattern matching across the page"""
        print("🔍 Testing date pattern matching across entire page...")
        
        try:
            # Get all page text
            page_text = await page.evaluate("() => document.body.textContent")
            
            # Define comprehensive date patterns
            date_patterns = {
                "full_datetime": r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}',  # "24 Aug 2025 01:37:01"
                "iso_datetime": r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}',        # "2025-08-24 01:37:01"
                "us_datetime": r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}',      # "24/08/2025 01:37:01"
                "date_only": r'\d{1,2}\s+\w{3}\s+\d{4}',                           # "24 Aug 2025"
                "iso_date": r'\d{4}-\d{2}-\d{2}',                                  # "2025-08-24"
                "us_date": r'\d{1,2}/\d{1,2}/\d{4}',                               # "24/08/2025"
                "year_only": r'20\d{2}',                                          # "2025"
                "time_only": r'\d{1,2}:\d{2}:\d{2}',                               # "01:37:01"
            }
            
            pattern_results = {}
            total_matches = 0
            
            print("   📊 Pattern Analysis Results:")
            for pattern_name, pattern in date_patterns.items():
                matches = re.findall(pattern, page_text)
                unique_matches = list(set(matches))
                pattern_results[pattern_name] = {
                    "matches": matches,
                    "unique_matches": unique_matches,
                    "count": len(matches),
                    "unique_count": len(unique_matches)
                }
                
                if matches:
                    print(f"      {pattern_name}: {len(matches)} matches ({len(unique_matches)} unique)")
                    for match in unique_matches[:3]:  # Show first 3 unique matches
                        print(f"         • '{match}'")
                    if len(unique_matches) > 3:
                        print(f"         ... and {len(unique_matches) - 3} more")
                    
                total_matches += len(matches)
            
            print(f"   📈 Total matches found: {total_matches}")
            
            # Find elements containing the best date patterns
            await self._locate_date_pattern_elements(page, pattern_results)
            
            self.test_results["tests"].append({
                "test_name": "date_pattern_matching",
                "total_matches": total_matches,
                "pattern_results": pattern_results
            })
            
        except Exception as e:
            print(f"   ❌ Error in date pattern matching: {e}")
            self.test_results["issues_found"].append({
                "test": "date_pattern_matching",
                "error": str(e)
            })
    
    async def _locate_date_pattern_elements(self, page, pattern_results: Dict):
        """Find elements containing the discovered date patterns"""
        print("\n   🎯 Locating elements containing date patterns...")
        
        # Focus on the best patterns first
        priority_patterns = ["full_datetime", "iso_datetime", "date_only"]
        
        for pattern_name in priority_patterns:
            results = pattern_results.get(pattern_name, {})
            unique_matches = results.get("unique_matches", [])
            
            if not unique_matches:
                continue
                
            print(f"      🔍 Locating elements for pattern '{pattern_name}':")
            
            for match in unique_matches[:3]:  # Check first 3 matches
                try:
                    # Find elements containing this exact match
                    elements = await page.query_selector_all(f"*:has-text('{match}')")
                    print(f"         '{match}': {len(elements)} elements")
                    
                    # Analyze first few elements
                    for i, element in enumerate(elements[:2]):
                        is_visible = await element.is_visible()
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        class_name = await element.evaluate("el => el.className")
                        
                        print(f"            Element {i+1}: <{tag_name}> (visible: {is_visible})")
                        if class_name:
                            print(f"                     class: {class_name[:50]}")
                        
                        # Check if this is associated with a Creation Time element
                        associated = await self._check_creation_time_association(element, match)
                        if associated:
                            print(f"                     ✅ Associated with Creation Time element!")
                        
                except Exception as e:
                    print(f"         ❌ Error locating elements for '{match}': {e}")
    
    async def _check_creation_time_association(self, element, date_text: str) -> bool:
        """Check if an element is associated with a Creation Time element"""
        try:
            # Check if this element or its parent/siblings contain "Creation Time"
            result = await element.evaluate(f"""
                (element) => {{
                    // Check current element
                    if (element.textContent.includes('Creation Time')) {{
                        return true;
                    }}
                    
                    // Check parent
                    const parent = element.parentElement;
                    if (parent && parent.textContent.includes('Creation Time')) {{
                        return true;
                    }}
                    
                    // Check siblings
                    if (parent) {{
                        const siblings = Array.from(parent.children);
                        for (const sibling of siblings) {{
                            if (sibling.textContent.includes('Creation Time')) {{
                                return true;
                            }}
                        }}
                    }}
                    
                    return false;
                }}
            """)
            
            return result
            
        except Exception as e:
            return False
    
    async def _test_selection_strategies(self, page):
        """Test different element selection strategies"""
        print("🎯 Testing element selection strategies...")
        
        strategies = [
            ("first_creation_time", "Select first Creation Time element found"),
            ("first_visible_creation_time", "Select first visible Creation Time element"),
            ("last_visible_creation_time", "Select last visible Creation Time element"),
            ("center_screen_creation_time", "Select Creation Time element closest to screen center"),
            ("most_recent_date", "Select element with most recent date pattern"),
            ("longest_date_text", "Select element with longest date text")
        ]
        
        strategy_results = []
        
        for strategy_name, description in strategies:
            print(f"\n   🧪 Testing: {strategy_name}")
            print(f"      Description: {description}")
            
            try:
                result = await self._apply_date_selection_strategy(page, strategy_name)
                if result:
                    print(f"      ✅ Result: '{result['date']}'")
                    print(f"      📍 Source: {result['source']}")
                    print(f"      🎯 Confidence: {result.get('confidence', 'N/A')}")
                    
                    strategy_results.append({
                        "strategy": strategy_name,
                        "success": True,
                        "date": result['date'],
                        "confidence": result.get('confidence', 0)
                    })
                else:
                    print("      ❌ No result")
                    strategy_results.append({
                        "strategy": strategy_name,
                        "success": False,
                        "error": "No result returned"
                    })
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
                strategy_results.append({
                    "strategy": strategy_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Analyze strategy results
        successful_strategies = [s for s in strategy_results if s["success"]]
        if successful_strategies:
            # Check for consistency
            unique_dates = list(set(s["date"] for s in successful_strategies))
            
            if len(unique_dates) == 1:
                print(f"\n   ⚠️  All strategies returned the same date: {unique_dates[0]}")
                print("      This suggests the wrong element might be selected consistently")
                
                self.test_results["issues_found"].append({
                    "test": "selection_strategies",
                    "severity": "high",
                    "issue": "All selection strategies return identical dates",
                    "recommendation": "Problem likely in element selection logic, not strategy"
                })
            else:
                print(f"\n   ✅ Strategies returned different dates: {unique_dates}")
                print("      This suggests the selection strategy matters")
        
        self.test_results["tests"].append({
            "test_name": "selection_strategies",
            "strategies_tested": len(strategies),
            "successful_strategies": len(successful_strategies),
            "strategy_results": strategy_results
        })
    
    async def _apply_date_selection_strategy(self, page, strategy: str) -> Dict[str, Any]:
        """Apply a specific date selection strategy"""
        try:
            creation_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
            
            if not creation_elements:
                return None
            
            selected_element = None
            source_info = ""
            
            if strategy == "first_creation_time":
                selected_element = creation_elements[0]
                source_info = "first_element"
                
            elif strategy == "first_visible_creation_time":
                for i, element in enumerate(creation_elements):
                    if await element.is_visible():
                        selected_element = element
                        source_info = f"first_visible_{i}"
                        break
                        
            elif strategy == "last_visible_creation_time":
                visible_elements = []
                for i, element in enumerate(creation_elements):
                    if await element.is_visible():
                        visible_elements.append((i, element))
                if visible_elements:
                    selected_element = visible_elements[-1][1]
                    source_info = f"last_visible_{visible_elements[-1][0]}"
                    
            elif strategy == "center_screen_creation_time":
                viewport = await page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})")
                center_x, center_y = viewport["width"] / 2, viewport["height"] / 2
                
                closest_element = None
                min_distance = float('inf')
                
                for i, element in enumerate(creation_elements):
                    if await element.is_visible():
                        box = await element.bounding_box()
                        if box:
                            element_x = box["x"] + box["width"] / 2
                            element_y = box["y"] + box["height"] / 2
                            distance = ((element_x - center_x) ** 2 + (element_y - center_y) ** 2) ** 0.5
                            
                            if distance < min_distance:
                                min_distance = distance
                                closest_element = element
                                source_info = f"center_screen_{i}_dist_{int(min_distance)}"
                
                selected_element = closest_element
                
            elif strategy in ["most_recent_date", "longest_date_text"]:
                # These require analysis of the actual dates
                best_element = None
                best_value = 0 if strategy == "longest_date_text" else None
                
                for i, element in enumerate(creation_elements):
                    if await element.is_visible():
                        date_result = await self._extract_date_from_creation_element(element)
                        if date_result:
                            if strategy == "longest_date_text":
                                if len(date_result["date"]) > best_value:
                                    best_value = len(date_result["date"])
                                    best_element = element
                                    source_info = f"longest_date_{i}_len_{best_value}"
                            elif strategy == "most_recent_date":
                                # Simplified - just take first valid date
                                if best_element is None:
                                    best_element = element
                                    source_info = f"most_recent_{i}"
                
                selected_element = best_element
            
            # Extract date from selected element
            if selected_element:
                date_result = await self._extract_date_from_creation_element(selected_element)
                if date_result:
                    date_result["source"] = source_info
                    return date_result
            
            return None
            
        except Exception as e:
            logger.debug(f"Error in strategy {strategy}: {e}")
            return None
    
    async def _extract_date_from_creation_element(self, element) -> Dict[str, Any]:
        """Extract date from a Creation Time element"""
        try:
            parent = await element.evaluate_handle("el => el.parentElement")
            spans = await parent.query_selector_all("span")
            
            if len(spans) >= 2:
                date_text = await spans[1].text_content()
                is_visible = await spans[1].is_visible()
                
                # Analyze date quality
                quality = self._analyze_date_quality(date_text)
                confidence = 0.8 if is_visible and quality in ["full_datetime", "date_only"] else 0.3
                
                return {
                    "date": date_text.strip() if date_text else "Unknown",
                    "visible": is_visible,
                    "confidence": confidence,
                    "quality": quality,
                    "span_count": len(spans)
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting date: {e}")
            return None
    
    async def _create_visual_element_map(self, page):
        """Create visual element mapping for debugging"""
        print("🎨 Creating visual element map...")
        
        try:
            # Create visual map using the visualizer
            html_report = await self.visualizer.create_element_highlight_map(page, self.config)
            
            if html_report:
                print(f"   📋 Visual map created: {html_report}")
                print(f"   🌐 Open the HTML file in a browser to see highlighted elements")
                
                self.test_results["tests"].append({
                    "test_name": "visual_element_map",
                    "html_report": html_report,
                    "success": True
                })
            else:
                print("   ❌ Failed to create visual map")
                self.test_results["issues_found"].append({
                    "test": "visual_element_map",
                    "severity": "low",
                    "issue": "Could not create visual element map",
                    "recommendation": "Check visualizer implementation"
                })
                
        except Exception as e:
            print(f"   ❌ Error creating visual map: {e}")
            self.test_results["issues_found"].append({
                "test": "visual_element_map",
                "error": str(e)
            })
    
    async def _test_multi_thumbnail_date_extraction(self, page):
        """Test date extraction across multiple thumbnails"""
        print("🔄 Testing multi-thumbnail date extraction...")
        
        try:
            print("   📋 Instructions for multi-thumbnail testing:")
            print("      1. This test requires manual thumbnail clicking")
            print("      2. Click on 3-5 different thumbnails")
            print("      3. For each thumbnail, we'll analyze the date extraction")
            print("      4. Press Enter after clicking each thumbnail")
            
            thumbnail_results = []
            
            for thumbnail_num in range(1, 4):  # Test 3 thumbnails
                input(f"\n   Click on thumbnail {thumbnail_num} and press Enter...")
                
                print(f"   🔍 Analyzing thumbnail {thumbnail_num}:")
                
                # Extract current date using the standard method
                current_date = await self._extract_current_date_standard_method(page)
                print(f"      📅 Current date extracted: '{current_date}'")
                
                # Take state snapshot
                state_name = f"thumbnail_{thumbnail_num}"
                await self.visualizer.compare_element_states(page, self.config, state_name)
                
                thumbnail_results.append({
                    "thumbnail_number": thumbnail_num,
                    "extracted_date": current_date,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Brief analysis
                if len(thumbnail_results) > 1:
                    previous_date = thumbnail_results[-2]["extracted_date"]
                    if current_date == previous_date:
                        print(f"      ⚠️  Same date as previous thumbnail: {current_date}")
                    else:
                        print(f"      ✅ Different date from previous: {previous_date} → {current_date}")
            
            # Analyze results
            unique_dates = list(set(r["extracted_date"] for r in thumbnail_results))
            
            print(f"\n   📊 Multi-thumbnail analysis results:")
            print(f"      Thumbnails tested: {len(thumbnail_results)}")
            print(f"      Unique dates found: {len(unique_dates)}")
            print(f"      Dates: {unique_dates}")
            
            if len(unique_dates) == 1:
                print("      ❌ ISSUE: All thumbnails returned the same date")
                print("         This suggests the wrong element is being selected")
                
                self.test_results["issues_found"].append({
                    "test": "multi_thumbnail_extraction",
                    "severity": "critical",
                    "issue": "All thumbnails return identical dates",
                    "recommendation": "Fix element selection logic to use thumbnail-specific elements"
                })
            else:
                print("      ✅ SUCCESS: Different dates extracted for different thumbnails")
            
            self.test_results["tests"].append({
                "test_name": "multi_thumbnail_extraction",
                "thumbnails_tested": len(thumbnail_results),
                "unique_dates": len(unique_dates),
                "thumbnail_results": thumbnail_results
            })
            
        except Exception as e:
            print(f"   ❌ Error in multi-thumbnail test: {e}")
            self.test_results["issues_found"].append({
                "test": "multi_thumbnail_extraction",
                "error": str(e)
            })
    
    async def _extract_current_date_standard_method(self, page) -> str:
        """Extract date using the current standard method"""
        try:
            # This mimics the current logic in the generation download manager
            creation_time_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
            
            if not creation_time_elements:
                return "No Creation Time elements"
            
            # Use first element (current logic)
            element = creation_time_elements[0]
            parent = await element.evaluate_handle("el => el.parentElement")
            spans = await parent.query_selector_all("span")
            
            if len(spans) >= 2:
                date_text = await spans[1].text_content()
                return date_text.strip() if date_text else "No date text"
            else:
                return "Insufficient spans"
                
        except Exception as e:
            return f"Error: {e}"
    
    async def _generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n📋 GENERATING COMPREHENSIVE REPORT")
        print("="*50)
        
        try:
            # Save test results
            results_file = Path(__file__).parent.parent / "logs" / f"date_fix_test_results_{self.test_results['session_id']}.json"
            results_file.parent.mkdir(exist_ok=True)
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Detailed results saved to: {results_file}")
            
            # Generate summary report
            print("\n📊 TEST SUMMARY:")
            print(f"   Tests run: {len(self.test_results['tests'])}")
            print(f"   Issues found: {len(self.test_results['issues_found'])}")
            
            # Show critical issues
            critical_issues = [i for i in self.test_results["issues_found"] if i.get("severity") == "critical"]
            if critical_issues:
                print("\n🚨 CRITICAL ISSUES FOUND:")
                for issue in critical_issues:
                    print(f"   • {issue['issue']}")
                    print(f"     Recommendation: {issue['recommendation']}")
            
            # Generate recommendations
            self._generate_fix_recommendations()
            
            print("\n✅ Comprehensive testing completed!")
            print(f"📁 All debug files saved to: {Path(results_file).parent}")
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    
    def _generate_fix_recommendations(self):
        """Generate actionable fix recommendations"""
        recommendations = []
        
        # Analyze test results and generate recommendations
        tests = {test["test_name"]: test for test in self.test_results["tests"]}
        
        # Check Creation Time element issues
        if "creation_time_elements" in tests:
            ct_test = tests["creation_time_elements"]
            
            if ct_test.get("visible_elements", 0) == 0:
                recommendations.append({
                    "priority": "high",
                    "title": "Fix invisible Creation Time elements",
                    "description": "All Creation Time elements are hidden",
                    "implementation": "Update selectors or check CSS visibility rules"
                })
            elif ct_test.get("visible_elements", 0) > 1:
                recommendations.append({
                    "priority": "high", 
                    "title": "Implement thumbnail-specific element selection",
                    "description": f"Multiple visible Creation Time elements ({ct_test['visible_elements']})",
                    "implementation": "Add logic to identify which element belongs to active thumbnail"
                })
        
        # Check multi-thumbnail issues
        if "multi_thumbnail_extraction" in tests:
            mt_test = tests["multi_thumbnail_extraction"]
            
            if mt_test.get("unique_dates", 0) <= 1:
                recommendations.append({
                    "priority": "critical",
                    "title": "Fix identical date extraction",
                    "description": "All thumbnails return the same date",
                    "implementation": "Revise element selection to use thumbnail context or improve selectors"
                })
        
        # Check pattern matching results
        if "date_pattern_matching" in tests:
            dp_test = tests["date_pattern_matching"]
            
            if dp_test.get("total_matches", 0) == 0:
                recommendations.append({
                    "priority": "medium",
                    "title": "No date patterns found on page",
                    "description": "Page may have changed structure",
                    "implementation": "Update date patterns or check page structure"
                })
        
        self.test_results["recommendations"] = recommendations
        
        if recommendations:
            print("\n💡 FIX RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
                print(f"      Problem: {rec['description']}")
                print(f"      Solution: {rec['implementation']}")
                print()


async def run_date_fix_testing():
    """Main function to run date extraction fix testing"""
    config = GenerationDownloadConfig(
        creation_time_text="Creation Time",
        prompt_ellipsis_pattern="</span>...",
        completed_task_selector="div[id$='__9']",
        thumbnail_selector=".thumsItem, .thumbnail-item"
    )
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
        context = await browser.new_context(viewport={'width': 2560, 'height': 1440})
        page = await context.new_page()
        
        try:
            print("🔧 DATE EXTRACTION FIX TESTING TOOL")
            print("="*60)
            print("📋 Instructions:")
            print("1. Navigate to the generation page")
            print("2. Log in if needed")
            print("3. Go to completed tasks section")
            print("4. Click on any thumbnail to show details")
            print("5. Press Enter to start comprehensive testing")
            
            input("\nPress Enter when ready to begin testing...")
            
            # Initialize and run tester
            tester = DateExtractionFixTester(config)
            await tester.run_comprehensive_date_fix_test(page)
            
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            logger.error(f"Critical error in testing: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    print("🚀 Starting Date Extraction Fix Testing Tool...")
    try:
        asyncio.run(run_date_fix_testing())
    except KeyboardInterrupt:
        print("\n👋 Testing interrupted by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()