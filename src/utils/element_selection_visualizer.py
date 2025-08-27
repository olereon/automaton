#!/usr/bin/env python3
"""
Element Selection Visualizer
Tool for visually debugging element selection in generation downloads.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class ElementSelectionVisualizer:
    """Visual debugging tool for element selection issues"""
    
    def __init__(self, debug_folder: str = "/home/olereon/workspace/github.com/olereon/automaton/logs/visual_debug"):
        self.debug_folder = Path(debug_folder)
        self.debug_folder.mkdir(parents=True, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_folder = self.debug_folder / f"visual_debug_{self.session_id}"
        self.output_folder.mkdir(exist_ok=True)
        
        logger.info(f"🎨 Visual debugger initialized: {self.output_folder}")
    
    async def create_element_highlight_map(self, page, config, thumbnail_index: int = -1) -> str:
        """Create a visual map highlighting all relevant elements"""
        try:
            # Take base screenshot
            screenshot_path = self.output_folder / f"base_screenshot_{thumbnail_index}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            # Inject highlighting CSS and JavaScript
            highlight_script = """
            () => {
                // Remove any existing highlights
                const existingHighlights = document.querySelectorAll('.debug-highlight');
                existingHighlights.forEach(el => el.remove());
                
                // Add CSS for highlights
                const style = document.createElement('style');
                style.textContent = `
                    .debug-highlight {
                        position: absolute;
                        border: 3px solid red;
                        background: rgba(255, 0, 0, 0.1);
                        pointer-events: none;
                        z-index: 9999;
                        font-family: monospace;
                        font-size: 12px;
                        font-weight: bold;
                        color: white;
                        text-shadow: 1px 1px 2px black;
                        padding: 2px 4px;
                    }
                    
                    .debug-highlight.creation-time { border-color: #ff0000; background: rgba(255, 0, 0, 0.2); }
                    .debug-highlight.date-element { border-color: #00ff00; background: rgba(0, 255, 0, 0.2); }
                    .debug-highlight.prompt-element { border-color: #0000ff; background: rgba(0, 0, 255, 0.2); }
                    .debug-highlight.thumbnail { border-color: #ff00ff; background: rgba(255, 0, 255, 0.2); }
                    .debug-highlight.invisible { border-style: dashed; opacity: 0.5; }
                `;
                document.head.appendChild(style);
                
                return 'Highlighting CSS injected';
            }
            """
            
            await page.evaluate(highlight_script)
            
            # Highlight Creation Time elements
            await self._highlight_creation_time_elements(page, config)
            
            # Highlight date-like elements
            await self._highlight_date_elements(page)
            
            # Highlight prompt elements
            await self._highlight_prompt_elements(page, config)
            
            # Highlight thumbnails
            await self._highlight_thumbnail_elements(page, config)
            
            # Take highlighted screenshot
            highlighted_path = self.output_folder / f"highlighted_elements_{thumbnail_index}.png"
            await page.screenshot(path=str(highlighted_path), full_page=True)
            
            # Generate element map data
            element_map = await self._generate_element_map_data(page, config)
            
            # Save element map as JSON
            map_data_path = self.output_folder / f"element_map_{thumbnail_index}.json"
            with open(map_data_path, 'w', encoding='utf-8') as f:
                json.dump(element_map, f, indent=2, ensure_ascii=False)
            
            # Generate HTML report
            html_report_path = await self._generate_html_report(
                thumbnail_index, 
                str(highlighted_path), 
                element_map
            )
            
            logger.info(f"🎨 Visual debug map created: {html_report_path}")
            return str(html_report_path)
            
        except Exception as e:
            logger.error(f"Error creating visual map: {e}")
            return ""
    
    async def _highlight_creation_time_elements(self, page, config):
        """Highlight all Creation Time elements"""
        highlight_script = f"""
        () => {{
            const elements = document.querySelectorAll("span:has-text('{config.creation_time_text}')");
            let count = 0;
            
            elements.forEach((element, index) => {{
                const rect = element.getBoundingClientRect();
                const isVisible = element.offsetParent !== null && rect.width > 0 && rect.height > 0;
                
                const highlight = document.createElement('div');
                highlight.className = 'debug-highlight creation-time' + (isVisible ? '' : ' invisible');
                highlight.style.left = (rect.left + window.scrollX - 3) + 'px';
                highlight.style.top = (rect.top + window.scrollY - 3) + 'px';
                highlight.style.width = (rect.width + 6) + 'px';
                highlight.style.height = (rect.height + 6) + 'px';
                highlight.textContent = `CT${{index + 1}}${{isVisible ? '' : ' (hidden)'}}`;
                
                document.body.appendChild(highlight);
                count++;
            }});
            
            return count;
        }}
        """
        
        count = await page.evaluate(highlight_script)
        logger.debug(f"Highlighted {count} Creation Time elements")
    
    async def _highlight_date_elements(self, page):
        """Highlight elements that might contain dates"""
        highlight_script = """
        () => {
            // Date patterns to look for
            const datePatterns = [
                /\\d{1,2}\\s+\\w{3}\\s+\\d{4}\\s+\\d{1,2}:\\d{2}:\\d{2}/g,  // "24 Aug 2025 01:37:01"
                /\\d{4}-\\d{2}-\\d{2}\\s+\\d{1,2}:\\d{2}:\\d{2}/g,           // "2025-08-24 01:37:01"
                /\\d{1,2}\\s+\\w{3}\\s+\\d{4}/g,                            // "24 Aug 2025"
                /20\\d{2}/g                                                  // Any year 2000+
            ];
            
            let count = 0;
            const textWalker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            const processedElements = new Set();
            
            let node;
            while (node = textWalker.nextNode()) {
                const text = node.textContent;
                const parent = node.parentElement;
                
                if (!parent || processedElements.has(parent)) continue;
                
                // Check if text matches any date pattern
                let hasDatePattern = false;
                for (const pattern of datePatterns) {
                    if (pattern.test(text)) {
                        hasDatePattern = true;
                        break;
                    }
                }
                
                if (hasDatePattern) {
                    const rect = parent.getBoundingClientRect();
                    const isVisible = parent.offsetParent !== null && rect.width > 0 && rect.height > 0;
                    
                    const highlight = document.createElement('div');
                    highlight.className = 'debug-highlight date-element' + (isVisible ? '' : ' invisible');
                    highlight.style.left = (rect.left + window.scrollX - 3) + 'px';
                    highlight.style.top = (rect.top + window.scrollY - 3) + 'px';
                    highlight.style.width = (rect.width + 6) + 'px';
                    highlight.style.height = (rect.height + 6) + 'px';
                    highlight.textContent = `DATE${count + 1}${isVisible ? '' : ' (hidden)'}`;
                    
                    document.body.appendChild(highlight);
                    processedElements.add(parent);
                    count++;
                    
                    if (count >= 20) break; // Limit to prevent too many highlights
                }
            }
            
            return count;
        }
        """
        
        count = await page.evaluate(highlight_script)
        logger.debug(f"Highlighted {count} potential date elements")
    
    async def _highlight_prompt_elements(self, page, config):
        """Highlight elements that might contain prompts"""
        highlight_script = f"""
        () => {{
            let count = 0;
            
            // Method 1: aria-describedby elements
            const ariaElements = document.querySelectorAll('span[aria-describedby]');
            ariaElements.forEach((element, index) => {{
                const rect = element.getBoundingClientRect();
                const isVisible = element.offsetParent !== null && rect.width > 0 && rect.height > 0;
                
                const highlight = document.createElement('div');
                highlight.className = 'debug-highlight prompt-element' + (isVisible ? '' : ' invisible');
                highlight.style.left = (rect.left + window.scrollX - 3) + 'px';
                highlight.style.top = (rect.top + window.scrollY - 3) + 'px';
                highlight.style.width = (rect.width + 6) + 'px';
                highlight.style.height = (rect.height + 6) + 'px';
                highlight.textContent = `PROMPT${{index + 1}}${{isVisible ? '' : ' (hidden)'}}`;
                
                document.body.appendChild(highlight);
                count++;
            }});
            
            // Method 2: Elements with ellipsis pattern
            const divs = document.querySelectorAll('div');
            let patternCount = 0;
            
            for (const div of divs) {{
                if (patternCount >= 10) break; // Limit pattern highlights
                
                const innerHTML = div.innerHTML;
                if (innerHTML.includes('{config.prompt_ellipsis_pattern}') && innerHTML.includes('aria-describedby')) {{
                    const spans = div.querySelectorAll('span[aria-describedby]');
                    
                    spans.forEach((span, spanIndex) => {{
                        const rect = span.getBoundingClientRect();
                        const isVisible = span.offsetParent !== null && rect.width > 0 && rect.height > 0;
                        
                        const highlight = document.createElement('div');
                        highlight.className = 'debug-highlight prompt-element' + (isVisible ? '' : ' invisible');
                        highlight.style.left = (rect.left + window.scrollX - 3) + 'px';
                        highlight.style.top = (rect.top + window.scrollY - 3) + 'px';
                        highlight.style.width = (rect.width + 6) + 'px';
                        highlight.style.height = (rect.height + 6) + 'px';
                        highlight.textContent = `PATTERN${{patternCount + 1}}-${{spanIndex + 1}}${{isVisible ? '' : ' (hidden)'}}`;
                        
                        document.body.appendChild(highlight);
                    }});
                    
                    patternCount++;
                    count += spans.length;
                }}
            }}
            
            return count;
        }}
        """
        
        count = await page.evaluate(highlight_script)
        logger.debug(f"Highlighted {count} potential prompt elements")
    
    async def _highlight_thumbnail_elements(self, page, config):
        """Highlight thumbnail elements"""
        highlight_script = f"""
        () => {{
            const selectors = ['{config.thumbnail_selector}', '{config.thumbnail_container_selector}'];
            let count = 0;
            
            selectors.forEach((selector, selectorIndex) => {{
                if (!selector) return;
                
                const elements = document.querySelectorAll(selector);
                elements.forEach((element, index) => {{
                    const rect = element.getBoundingClientRect();
                    const isVisible = element.offsetParent !== null && rect.width > 0 && rect.height > 0;
                    
                    const highlight = document.createElement('div');
                    highlight.className = 'debug-highlight thumbnail' + (isVisible ? '' : ' invisible');
                    highlight.style.left = (rect.left + window.scrollX - 3) + 'px';
                    highlight.style.top = (rect.top + window.scrollY - 3) + 'px';
                    highlight.style.width = (rect.width + 6) + 'px';
                    highlight.style.height = (rect.height + 6) + 'px';
                    highlight.textContent = `THUMB${{count + 1}}${{isVisible ? '' : ' (hidden)'}}`;
                    
                    document.body.appendChild(highlight);
                    count++;
                }});
            }});
            
            return count;
        }}
        """
        
        count = await page.evaluate(highlight_script)
        logger.debug(f"Highlighted {count} thumbnail elements")
    
    async def _generate_element_map_data(self, page, config) -> Dict[str, Any]:
        """Generate comprehensive element map data"""
        try:
            # Get all Creation Time elements
            creation_elements = await self._get_creation_time_element_data(page, config)
            
            # Get all date elements
            date_elements = await self._get_date_element_data(page)
            
            # Get all prompt elements
            prompt_elements = await self._get_prompt_element_data(page, config)
            
            # Get all thumbnail elements
            thumbnail_elements = await self._get_thumbnail_element_data(page, config)
            
            # Get page metadata
            page_metadata = await self._get_page_metadata(page)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "page_metadata": page_metadata,
                "creation_time_elements": creation_elements,
                "date_elements": date_elements,
                "prompt_elements": prompt_elements,
                "thumbnail_elements": thumbnail_elements,
                "summary": {
                    "total_creation_time": len(creation_elements),
                    "total_date_elements": len(date_elements),
                    "total_prompt_elements": len(prompt_elements),
                    "total_thumbnails": len(thumbnail_elements),
                    "visible_creation_time": sum(1 for e in creation_elements if e["is_visible"]),
                    "visible_date_elements": sum(1 for e in date_elements if e["is_visible"]),
                    "visible_prompt_elements": sum(1 for e in prompt_elements if e["is_visible"]),
                    "visible_thumbnails": sum(1 for e in thumbnail_elements if e["is_visible"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating element map data: {e}")
            return {"error": str(e)}
    
    async def _get_creation_time_element_data(self, page, config) -> List[Dict]:
        """Get detailed data about Creation Time elements"""
        script = f"""
        () => {{
            const elements = document.querySelectorAll("span:has-text('{config.creation_time_text}')");
            const results = [];
            
            elements.forEach((element, index) => {{
                const rect = element.getBoundingClientRect();
                const isVisible = element.offsetParent !== null && rect.width > 0 && rect.height > 0;
                
                // Get parent spans
                const parent = element.parentElement;
                const parentSpans = parent ? parent.querySelectorAll('span') : [];
                
                const spanData = Array.from(parentSpans).map((span, spanIndex) => ({{
                    index: spanIndex,
                    text: span.textContent || '',
                    is_visible: span.offsetParent !== null,
                    class_name: span.className,
                    tag_name: span.tagName.toLowerCase()
                }}));
                
                results.push({{
                    index: index,
                    text_content: element.textContent || '',
                    is_visible: isVisible,
                    bounding_box: {{
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }},
                    class_name: element.className,
                    parent_spans: spanData,
                    associated_date: spanData.length >= 2 ? spanData[1].text : 'No associated date'
                }});
            }});
            
            return results;
        }}
        """
        
        return await page.evaluate(script)
    
    async def _get_date_element_data(self, page) -> List[Dict]:
        """Get detailed data about potential date elements"""
        script = """
        () => {
            const datePatterns = [
                {name: 'full_datetime', pattern: /\\d{1,2}\\s+\\w{3}\\s+\\d{4}\\s+\\d{1,2}:\\d{2}:\\d{2}/g},
                {name: 'iso_datetime', pattern: /\\d{4}-\\d{2}-\\d{2}\\s+\\d{1,2}:\\d{2}:\\d{2}/g},
                {name: 'date_only', pattern: /\\d{1,2}\\s+\\w{3}\\s+\\d{4}/g},
                {name: 'year_only', pattern: /20\\d{2}/g}
            ];
            
            const results = [];
            const textWalker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            const processedElements = new Set();
            let elementIndex = 0;
            
            let node;
            while (node = textWalker.nextNode() && elementIndex < 50) {
                const text = node.textContent;
                const parent = node.parentElement;
                
                if (!parent || processedElements.has(parent)) continue;
                
                // Check each pattern
                for (const patternInfo of datePatterns) {
                    const matches = text.match(patternInfo.pattern);
                    if (matches && matches.length > 0) {
                        const rect = parent.getBoundingClientRect();
                        const isVisible = parent.offsetParent !== null && rect.width > 0 && rect.height > 0;
                        
                        results.push({
                            index: elementIndex++,
                            text_content: text.substring(0, 100),
                            pattern_type: patternInfo.name,
                            matches: matches.slice(0, 5), // Limit matches
                            is_visible: isVisible,
                            bounding_box: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            },
                            tag_name: parent.tagName.toLowerCase(),
                            class_name: parent.className
                        });
                        
                        processedElements.add(parent);
                        break; // Only add once per element
                    }
                }
            }
            
            return results;
        }
        """
        
        return await page.evaluate(script)
    
    async def _get_prompt_element_data(self, page, config) -> List[Dict]:
        """Get detailed data about potential prompt elements"""
        script = f"""
        () => {{
            const results = [];
            
            // Method 1: aria-describedby elements
            const ariaElements = document.querySelectorAll('span[aria-describedby]');
            ariaElements.forEach((element, index) => {{
                const rect = element.getBoundingClientRect();
                const isVisible = element.offsetParent !== null && rect.width > 0 && rect.height > 0;
                
                results.push({{
                    index: results.length,
                    method: 'aria_describedby',
                    text_content: element.textContent || '',
                    inner_text: element.innerText || '',
                    is_visible: isVisible,
                    bounding_box: {{
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }},
                    aria_describedby: element.getAttribute('aria-describedby'),
                    class_name: element.className,
                    char_count: (element.textContent || '').length
                }});
            }});
            
            // Method 2: Ellipsis pattern elements
            const divs = document.querySelectorAll('div');
            let patternCount = 0;
            
            for (const div of divs) {{
                if (patternCount >= 10) break;
                
                const innerHTML = div.innerHTML;
                if (innerHTML.includes('{config.prompt_ellipsis_pattern}') && innerHTML.includes('aria-describedby')) {{
                    const spans = div.querySelectorAll('span[aria-describedby]');
                    
                    spans.forEach((span) => {{
                        const rect = span.getBoundingClientRect();
                        const isVisible = span.offsetParent !== null && rect.width > 0 && rect.height > 0;
                        
                        results.push({{
                            index: results.length,
                            method: 'ellipsis_pattern',
                            text_content: span.textContent || '',
                            inner_text: span.innerText || '',
                            is_visible: isVisible,
                            bounding_box: {{
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }},
                            aria_describedby: span.getAttribute('aria-describedby'),
                            class_name: span.className,
                            char_count: (span.textContent || '').length,
                            pattern_container: true
                        }});
                    }});
                    
                    patternCount++;
                }}
            }}
            
            return results;
        }}
        """
        
        return await page.evaluate(script)
    
    async def _get_thumbnail_element_data(self, page, config) -> List[Dict]:
        """Get detailed data about thumbnail elements"""
        script = f"""
        () => {{
            const selectors = ['{config.thumbnail_selector}', '{config.thumbnail_container_selector}'];
            const results = [];
            
            selectors.forEach((selector, selectorIndex) => {{
                if (!selector) return;
                
                const elements = document.querySelectorAll(selector);
                elements.forEach((element, index) => {{
                    const rect = element.getBoundingClientRect();
                    const isVisible = element.offsetParent !== null && rect.width > 0 && rect.height > 0;
                    
                    results.push({{
                        index: results.length,
                        selector_used: selector,
                        selector_index: selectorIndex,
                        element_index: index,
                        is_visible: isVisible,
                        bounding_box: {{
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        }},
                        tag_name: element.tagName.toLowerCase(),
                        class_name: element.className,
                        id: element.id || ''
                    }});
                }});
            }});
            
            return results;
        }}
        """
        
        return await page.evaluate(script)
    
    async def _get_page_metadata(self, page) -> Dict[str, Any]:
        """Get general page metadata"""
        metadata = {
            "url": page.url,
            "title": await page.title(),
            "viewport": await page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})"),
            "scroll_position": await page.evaluate("() => ({x: window.scrollX, y: window.scrollY})"),
            "total_elements": await page.evaluate("() => document.querySelectorAll('*').length"),
            "timestamp": datetime.now().isoformat()
        }
        
        return metadata
    
    async def _generate_html_report(self, thumbnail_index: int, screenshot_path: str, element_map: Dict) -> str:
        """Generate an HTML report for visual debugging"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Visual Element Debug Report - Thumbnail {thumbnail_index}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .summary {{ background: #f9f9f9; }}
                .element-list {{ max-height: 300px; overflow-y: auto; }}
                .element {{ padding: 8px; margin: 5px 0; border: 1px solid #eee; background: #fafafa; }}
                .visible {{ border-left: 4px solid green; }}
                .hidden {{ border-left: 4px solid red; opacity: 0.7; }}
                .screenshot {{ text-align: center; margin: 20px 0; }}
                .screenshot img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
                .legend {{ display: flex; gap: 20px; margin: 10px 0; }}
                .legend-item {{ padding: 5px 10px; border-radius: 3px; font-size: 12px; font-weight: bold; }}
                .creation-time {{ background: rgba(255, 0, 0, 0.2); border: 2px solid red; }}
                .date-element {{ background: rgba(0, 255, 0, 0.2); border: 2px solid green; }}
                .prompt-element {{ background: rgba(0, 0, 255, 0.2); border: 2px solid blue; }}
                .thumbnail {{ background: rgba(255, 0, 255, 0.2); border: 2px solid magenta; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Visual Element Debug Report</h1>
                <p><strong>Session:</strong> {self.session_id}</p>
                <p><strong>Thumbnail Index:</strong> {thumbnail_index}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>URL:</strong> {element_map.get('page_metadata', {}).get('url', 'Unknown')}</p>
            </div>
            
            <div class="legend">
                <div class="legend-item creation-time">Creation Time Elements</div>
                <div class="legend-item date-element">Date Elements</div>
                <div class="legend-item prompt-element">Prompt Elements</div>
                <div class="legend-item thumbnail">Thumbnail Elements</div>
            </div>
            
            <div class="screenshot">
                <h2>Page with Highlighted Elements</h2>
                <img src="{Path(screenshot_path).name}" alt="Page screenshot with highlighted elements">
            </div>
            
            <div class="section summary">
                <h2>Summary</h2>
                <p><strong>Total Creation Time Elements:</strong> {element_map.get('summary', {}).get('total_creation_time', 0)} 
                   (Visible: {element_map.get('summary', {}).get('visible_creation_time', 0)})</p>
                <p><strong>Total Date Elements:</strong> {element_map.get('summary', {}).get('total_date_elements', 0)} 
                   (Visible: {element_map.get('summary', {}).get('visible_date_elements', 0)})</p>
                <p><strong>Total Prompt Elements:</strong> {element_map.get('summary', {}).get('total_prompt_elements', 0)} 
                   (Visible: {element_map.get('summary', {}).get('visible_prompt_elements', 0)})</p>
                <p><strong>Total Thumbnails:</strong> {element_map.get('summary', {}).get('total_thumbnails', 0)} 
                   (Visible: {element_map.get('summary', {}).get('visible_thumbnails', 0)})</p>
            </div>
            
            <div class="section">
                <h2>Creation Time Elements</h2>
                <div class="element-list">
                    {self._format_creation_time_elements_html(element_map.get('creation_time_elements', []))}
                </div>
            </div>
            
            <div class="section">
                <h2>Date Elements</h2>
                <div class="element-list">
                    {self._format_date_elements_html(element_map.get('date_elements', []))}
                </div>
            </div>
            
            <div class="section">
                <h2>Prompt Elements</h2>
                <div class="element-list">
                    {self._format_prompt_elements_html(element_map.get('prompt_elements', []))}
                </div>
            </div>
            
            <div class="section">
                <h2>Thumbnail Elements</h2>
                <div class="element-list">
                    {self._format_thumbnail_elements_html(element_map.get('thumbnail_elements', []))}
                </div>
            </div>
            
            <script>
                // Add click handlers to show/hide elements
                document.querySelectorAll('.element').forEach(element => {{
                    element.addEventListener('click', function() {{
                        const details = this.querySelector('.element-details');
                        if (details) {{
                            details.style.display = details.style.display === 'none' ? 'block' : 'none';
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        html_path = self.output_folder / f"visual_debug_report_{thumbnail_index}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(html_path)
    
    def _format_creation_time_elements_html(self, elements: List[Dict]) -> str:
        """Format Creation Time elements for HTML display"""
        if not elements:
            return "<p>No Creation Time elements found</p>"
        
        html = ""
        for element in elements:
            visibility_class = "visible" if element.get("is_visible") else "hidden"
            html += f"""
            <div class="element {visibility_class}">
                <strong>CT{element.get('index', 0) + 1}</strong> - 
                {element.get('text_content', 'No text')[:50]}...
                ({element.get('is_visible', False) and 'Visible' or 'Hidden'})
                <br><small>Associated Date: {element.get('associated_date', 'None')}</small>
                <br><small>Parent Spans: {len(element.get('parent_spans', []))}</small>
            </div>
            """
        return html
    
    def _format_date_elements_html(self, elements: List[Dict]) -> str:
        """Format date elements for HTML display"""
        if not elements:
            return "<p>No date elements found</p>"
        
        html = ""
        for element in elements:
            visibility_class = "visible" if element.get("is_visible") else "hidden"
            html += f"""
            <div class="element {visibility_class}">
                <strong>DATE{element.get('index', 0) + 1}</strong> - 
                Pattern: {element.get('pattern_type', 'Unknown')}
                ({element.get('is_visible', False) and 'Visible' or 'Hidden'})
                <br><small>Matches: {', '.join(element.get('matches', [])[:3])}...</small>
                <br><small>Text: {element.get('text_content', 'No text')[:50]}...</small>
            </div>
            """
        return html
    
    def _format_prompt_elements_html(self, elements: List[Dict]) -> str:
        """Format prompt elements for HTML display"""
        if not elements:
            return "<p>No prompt elements found</p>"
        
        html = ""
        for element in elements:
            visibility_class = "visible" if element.get("is_visible") else "hidden"
            method_badge = element.get('method', 'unknown').replace('_', ' ').title()
            html += f"""
            <div class="element {visibility_class}">
                <strong>PROMPT{element.get('index', 0) + 1}</strong> - 
                Method: {method_badge}
                ({element.get('is_visible', False) and 'Visible' or 'Hidden'})
                <br><small>Length: {element.get('char_count', 0)} chars</small>
                <br><small>Text: {element.get('text_content', 'No text')[:50]}...</small>
            </div>
            """
        return html
    
    def _format_thumbnail_elements_html(self, elements: List[Dict]) -> str:
        """Format thumbnail elements for HTML display"""
        if not elements:
            return "<p>No thumbnail elements found</p>"
        
        html = ""
        for element in elements:
            visibility_class = "visible" if element.get("is_visible") else "hidden"
            html += f"""
            <div class="element {visibility_class}">
                <strong>THUMB{element.get('index', 0) + 1}</strong> - 
                Selector: {element.get('selector_used', 'Unknown')[:30]}...
                ({element.get('is_visible', False) and 'Visible' or 'Hidden'})
                <br><small>Tag: &lt;{element.get('tag_name', 'unknown')}&gt;</small>
                <br><small>Class: {element.get('class_name', 'None')[:50]}</small>
            </div>
            """
        return html
    
    async def compare_element_states(self, page, config, state_name: str = "current") -> str:
        """Compare current element state with previous states"""
        try:
            current_map = await self._generate_element_map_data(page, config)
            
            # Save current state
            state_file = self.output_folder / f"element_state_{state_name}.json"
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(current_map, f, indent=2, ensure_ascii=False)
            
            # Look for previous states to compare
            state_files = list(self.output_folder.glob("element_state_*.json"))
            
            if len(state_files) < 2:
                logger.info(f"State '{state_name}' saved. Need at least 2 states for comparison.")
                return str(state_file)
            
            # Generate comparison report
            comparison_html = await self._generate_comparison_report(state_files)
            
            return comparison_html
            
        except Exception as e:
            logger.error(f"Error in element state comparison: {e}")
            return ""
    
    async def _generate_comparison_report(self, state_files: List[Path]) -> str:
        """Generate HTML comparison report between element states"""
        # Implementation for comparison report
        # This would compare different states and highlight changes
        comparison_html = self.output_folder / "element_comparison_report.html"
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Element State Comparison</title></head>
        <body>
        <h1>Element State Comparison Report</h1>
        <p>Comparison functionality would be implemented here...</p>
        </body>
        </html>
        """
        
        with open(comparison_html, 'w') as f:
            f.write(html_content)
        
        return str(comparison_html)


# Convenience function for quick visual debugging
async def create_visual_element_map(page, config, thumbnail_index=-1):
    """Quick function to create visual element map"""
    visualizer = ElementSelectionVisualizer()
    return await visualizer.create_element_highlight_map(page, config, thumbnail_index)