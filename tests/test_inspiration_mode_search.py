#!/usr/bin/env python3.11

"""
Test for searching containers using "Inspiration Mode" + "Off" pattern.

This test implements a more targeted approach:
1. Find "Inspiration Mode" + "Off" span pairs
2. Navigate backwards to find "Creation Time" + date pairs
3. Count and analyze these specific metadata containers
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"inspiration_mode_search_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InspirationModeSearcher:
    def __init__(self):
        self.config = {
            'url': 'https://wan.video/generate',
            'username': 'shyraoleg@outlook.com',
            'password': 'Wanv!de025',
            'username_selector': 'input[placeholder="Email address"]',
            'password_selector': 'input[type="password"]',
            'submit_selector': 'button:has-text("Log in")[type="submit"]',
            'thumbnail_selector': '.thumsItem, .thumbnail-item'
        }
        self.results = {
            'session_info': {
                'start_time': datetime.now().isoformat(),
                'url': self.config['url'],
                'search_pattern': 'Inspiration Mode + Off'
            },
            'inspiration_mode_containers': [],
            'creation_time_analysis': [],
            'summary': {}
        }

    async def login(self, page):
        """Login to the generation platform"""
        logger.info("🔐 Starting login process")
        
        await page.goto(self.config['url'])
        await page.wait_for_load_state('networkidle')
        logger.info(f"📍 Navigated to: {self.config['url']}")
        
        # Fill username
        await page.fill(self.config['username_selector'], self.config['username'])
        logger.info("✅ Username filled")
        
        # Fill password
        await page.fill(self.config['password_selector'], self.config['password'])
        logger.info("✅ Password filled")
        
        # Click submit
        await page.click(self.config['submit_selector'])
        await page.wait_for_load_state('networkidle')
        logger.info("✅ Login completed")

    async def navigate_to_gallery(self, page):
        """Navigate to the generation gallery and select first thumbnail"""
        logger.info("🖼️ Navigating to generation gallery")
        
        # Wait for page to load
        await page.wait_for_timeout(4000)
        
        # Look for completed tasks or navigate to gallery
        gallery_selectors = [
            "div[id$='__9']",  # Completed task selector
            "text=Completed",
            ".thumsInner"
        ]
        
        for selector in gallery_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=2000)
                if element:
                    await element.click()
                    await page.wait_for_timeout(3000)
                    break
            except:
                continue
        
        # Find and click first thumbnail
        thumbnails = await page.query_selector_all(self.config['thumbnail_selector'])
        logger.info(f"📊 Found {len(thumbnails)} thumbnails in gallery")
        
        if thumbnails:
            await thumbnails[0].click()
            await page.wait_for_timeout(3000)
            logger.info("✅ First thumbnail selected and detail panel loaded")
        else:
            raise Exception("No thumbnails found in gallery")

    async def search_inspiration_mode_containers(self, page):
        """Search for containers using 'Inspiration Mode' + 'Off' pattern"""
        logger.info("🔍 Starting 'Inspiration Mode' + 'Off' search")
        
        inspiration_containers = []
        
        try:
            # Step 1: Find all spans containing "Inspiration Mode"
            inspiration_spans = await page.query_selector_all("span:has-text('Inspiration Mode')")
            logger.info(f"📦 Found {len(inspiration_spans)} spans containing 'Inspiration Mode'")
            
            for i, inspiration_span in enumerate(inspiration_spans):
                try:
                    container_info = {
                        'index': i,
                        'inspiration_span_info': {},
                        'off_span_info': {},
                        'container_info': {},
                        'has_off_sibling': False,
                        'creation_time_found': False,
                        'creation_date': None
                    }
                    
                    # Get inspiration span details
                    inspiration_text = await inspiration_span.text_content()
                    inspiration_class = await inspiration_span.get_attribute('class') or 'no-class'
                    
                    container_info['inspiration_span_info'] = {
                        'text': inspiration_text.strip(),
                        'class': inspiration_class
                    }
                    
                    logger.info(f"🎯 Processing Inspiration Mode span {i}: class='{inspiration_class}' text='{inspiration_text.strip()}'")
                    
                    # Step 2: Look for "Off" in the next sibling span
                    parent = await inspiration_span.evaluate_handle("el => el.parentElement")
                    if parent:
                        parent_spans = await parent.query_selector_all("span")
                        logger.info(f"   Parent has {len(parent_spans)} spans")
                        
                        # Find the inspiration span index in parent
                        inspiration_index = -1
                        for j, span in enumerate(parent_spans):
                            span_text = await span.text_content()
                            if "Inspiration Mode" in span_text:
                                inspiration_index = j
                                break
                        
                        # Check if next span contains "Off"
                        if inspiration_index >= 0 and inspiration_index + 1 < len(parent_spans):
                            next_span = parent_spans[inspiration_index + 1]
                            next_span_text = await next_span.text_content()
                            next_span_class = await next_span.get_attribute('class') or 'no-class'
                            
                            logger.info(f"   Next span: class='{next_span_class}' text='{next_span_text.strip()}'")
                            
                            if "Off" in next_span_text:
                                container_info['has_off_sibling'] = True
                                container_info['off_span_info'] = {
                                    'text': next_span_text.strip(),
                                    'class': next_span_class
                                }
                                
                                logger.info(f"   ✅ Found 'Inspiration Mode' + 'Off' pair!")
                                
                                # Step 3: Search backwards for "Creation Time" + date
                                await self.search_creation_time_backwards(parent, container_info)
                                
                                # Step 4: Get container information
                                await self.analyze_metadata_container(parent, container_info)
                                
                            else:
                                logger.info(f"   ❌ Next span does not contain 'Off': '{next_span_text.strip()}'")
                        else:
                            logger.info(f"   ❌ No next sibling span found")
                    
                    inspiration_containers.append(container_info)
                    
                except Exception as e:
                    logger.error(f"Error processing inspiration span {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in inspiration mode search: {e}")
        
        return inspiration_containers

    async def search_creation_time_backwards(self, parent_element, container_info):
        """Search backwards from 'Inspiration Mode' to find 'Creation Time' + date"""
        logger.info("   🔍 Searching backwards for 'Creation Time' + date")
        
        try:
            # Get the parent container (likely the metadata container)
            metadata_container = await parent_element.evaluate_handle("el => el.parentElement")
            if not metadata_container:
                logger.info("   ❌ No metadata container found")
                return
            
            # Look for all child divs that might contain Creation Time
            child_divs = await metadata_container.query_selector_all("div")
            logger.info(f"   📦 Found {len(child_divs)} child divs in metadata container")
            
            for i, div in enumerate(child_divs):
                try:
                    div_text = await div.text_content() or ""
                    
                    if "Creation Time" in div_text:
                        logger.info(f"   ✅ Found 'Creation Time' in div {i}: '{div_text[:100]}...'")
                        
                        # Look for spans within this div
                        div_spans = await div.query_selector_all("span")
                        logger.info(f"     Div has {len(div_spans)} spans")
                        
                        # Log all spans in this div
                        creation_time_index = -1
                        for j, span in enumerate(div_spans):
                            span_text = await span.text_content() or ""
                            span_class = await span.get_attribute('class') or 'no-class'
                            logger.info(f"       Span {j}: class='{span_class}' text='{span_text.strip()}'")
                            
                            if "Creation Time" in span_text:
                                creation_time_index = j
                        
                        # Check if next span contains the date
                        if creation_time_index >= 0 and creation_time_index + 1 < len(div_spans):
                            date_span = div_spans[creation_time_index + 1]
                            date_text = await date_span.text_content() or ""
                            date_class = await date_span.get_attribute('class') or 'no-class'
                            
                            # Validate this looks like a date
                            if self.is_valid_date_text(date_text):
                                container_info['creation_time_found'] = True
                                container_info['creation_date'] = date_text.strip()
                                
                                logger.info(f"     ✅ Found Creation Time date: '{date_text.strip()}'")
                                
                                # Store creation time analysis
                                self.results['creation_time_analysis'].append({
                                    'creation_time_span': {
                                        'text': f"Creation Time",
                                        'class': await div_spans[creation_time_index].get_attribute('class')
                                    },
                                    'date_span': {
                                        'text': date_text.strip(),
                                        'class': date_class
                                    },
                                    'container_div_text': div_text[:200]
                                })
                                
                                return
                            else:
                                logger.info(f"     ❌ Next span doesn't look like date: '{date_text.strip()}'")
                
                except Exception as e:
                    logger.debug(f"Error processing div {i}: {e}")
                    continue
            
            logger.info("   ❌ No 'Creation Time' + date pair found")
            
        except Exception as e:
            logger.error(f"Error searching for Creation Time: {e}")

    def is_valid_date_text(self, text):
        """Check if text looks like a valid date"""
        if not text or len(text.strip()) < 10:
            return False
        
        text = text.strip()
        
        # Check for date indicators
        date_indicators = ['Aug', '2025', ':', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Sep', 'Oct', 'Nov', 'Dec']
        matches = sum(1 for indicator in date_indicators if indicator in text)
        
        return matches >= 2  # Should have at least month and year or time

    async def analyze_metadata_container(self, parent_element, container_info):
        """Analyze the metadata container properties"""
        try:
            metadata_container = await parent_element.evaluate_handle("el => el.parentElement")
            if not metadata_container:
                return
            
            container_text = await metadata_container.text_content() or ""
            container_class = await metadata_container.get_attribute('class') or 'no-class'
            container_id = await metadata_container.get_attribute('id') or 'no-id'
            
            # Get bounding box if possible
            bounding_box = None
            try:
                bounding_box = await metadata_container.bounding_box()
            except:
                pass
            
            container_info['container_info'] = {
                'class': container_class,
                'id': container_id,
                'text_length': len(container_text),
                'text_sample': container_text[:300] + "..." if len(container_text) > 300 else container_text,
                'bounding_box': bounding_box
            }
            
            logger.info(f"   📦 Metadata container: class='{container_class}' id='{container_id}' text_length={len(container_text)}")
            
        except Exception as e:
            logger.error(f"Error analyzing metadata container: {e}")

    def generate_summary(self):
        """Generate summary of results"""
        inspiration_containers = self.results['inspiration_mode_containers']
        
        total_inspiration_mode = len(inspiration_containers)
        with_off_sibling = sum(1 for c in inspiration_containers if c['has_off_sibling'])
        with_creation_time = sum(1 for c in inspiration_containers if c['creation_time_found'])
        
        # Find the best candidate (has both Off and Creation Time)
        best_candidates = [c for c in inspiration_containers if c['has_off_sibling'] and c['creation_time_found']]
        
        summary = {
            'total_inspiration_mode_spans': total_inspiration_mode,
            'with_off_sibling': with_off_sibling,
            'with_creation_time_found': with_creation_time,
            'complete_metadata_containers': len(best_candidates),
            'best_candidates': []
        }
        
        # Extract key info from best candidates
        for candidate in best_candidates[:3]:  # Top 3
            summary['best_candidates'].append({
                'container_class': candidate['container_info'].get('class', 'unknown'),
                'container_text_length': candidate['container_info'].get('text_length', 0),
                'creation_date': candidate['creation_date'],
                'inspiration_mode_class': candidate['inspiration_span_info'].get('class', 'unknown'),
                'off_class': candidate['off_span_info'].get('class', 'unknown')
            })
        
        self.results['summary'] = summary
        return summary

    async def save_results(self):
        """Save results to JSON file"""
        results_file = log_dir / f"inspiration_mode_search_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to: {results_file}")
        return results_file

    async def run_search(self):
        """Run the complete inspiration mode search"""
        logger.info("🚀 Starting Inspiration Mode Search Test")
        logger.info(f"📝 Log file: {log_file}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                page.set_default_timeout(30000)
                
                try:
                    # Step 1: Login
                    await self.login(page)
                    
                    # Step 2: Navigate to gallery and select thumbnail
                    await self.navigate_to_gallery(page)
                    
                    # Step 3: Search for Inspiration Mode + Off containers
                    inspiration_containers = await self.search_inspiration_mode_containers(page)
                    self.results['inspiration_mode_containers'] = inspiration_containers
                    
                    # Step 4: Generate summary
                    summary = self.generate_summary()
                    
                    # Step 5: Save results
                    results_file = await self.save_results()
                    
                    # Step 6: Report results
                    logger.info("✅ Search completed successfully")
                    logger.info(f"📊 Found {summary['total_inspiration_mode_spans']} 'Inspiration Mode' spans")
                    logger.info(f"🎯 Found {summary['with_off_sibling']} with 'Off' sibling spans")
                    logger.info(f"📅 Found {summary['with_creation_time_found']} with 'Creation Time' backwards")
                    logger.info(f"🏆 Found {summary['complete_metadata_containers']} complete metadata containers")
                    
                    if summary['best_candidates']:
                        logger.info("🏆 Best metadata container candidates:")
                        for i, candidate in enumerate(summary['best_candidates']):
                            logger.info(f"  {i+1}. Container class: {candidate['container_class']}")
                            logger.info(f"     Text length: {candidate['container_text_length']} chars")
                            logger.info(f"     Creation date: {candidate['creation_date']}")
                    
                    # Keep browser open for inspection
                    logger.info("🔍 Browser kept open for manual inspection")
                    await page.wait_for_timeout(5000)
                    
                except Exception as e:
                    logger.error(f"Error during search: {e}")
                    self.results['error'] = str(e)
                    await self.save_results()
                    raise
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Critical error: {e}")
            raise

async def main():
    """Main test function"""
    searcher = InspirationModeSearcher()
    await searcher.run_search()

if __name__ == "__main__":
    print("🧪 Inspiration Mode + Off Search Test")
    print("=" * 50)
    asyncio.run(main())
    print("✅ Test completed!")