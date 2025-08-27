#!/usr/bin/env python3.11

"""
Test for analyzing landmark containers in generation download workflow.

This test logs into the webpage, navigates to the generation gallery, 
selects the first thumbnail, and analyzes containers containing landmark texts.
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
log_file = log_dir / f"landmark_container_analysis_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LandmarkContainerAnalyzer:
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
        self.landmarks = ["Wan2.2 Plus", "Creation Time", "Inspiration Mode"]
        self.analysis_results = {
            'session_info': {
                'start_time': datetime.now().isoformat(),
                'url': self.config['url'],
                'landmarks': self.landmarks
            },
            'container_analysis': {},
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
        """Navigate to the generation gallery"""
        logger.info("🖼️ Navigating to generation gallery")
        
        # Wait for page to load and look for thumbnails
        await page.wait_for_timeout(4000)
        
        # Check if we're already in the gallery or need to navigate
        thumbnails = await page.query_selector_all(self.config['thumbnail_selector'])
        
        if not thumbnails:
            # Try to navigate to the gallery - look for completed tasks or gallery link
            try:
                # Look for common gallery navigation patterns
                gallery_selectors = [
                    "div[id$='__9']",  # Completed task selector from config
                    "text=Completed",
                    "text=Gallery",
                    "text=My Creations",
                    ".thumsInner"
                ]
                
                for selector in gallery_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=2000)
                        if element:
                            await element.click()
                            await page.wait_for_timeout(3000)
                            thumbnails = await page.query_selector_all(self.config['thumbnail_selector'])
                            if thumbnails:
                                logger.info(f"✅ Found gallery via selector: {selector}")
                                break
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not find specific gallery navigation: {e}")
        
        thumbnails = await page.query_selector_all(self.config['thumbnail_selector'])
        logger.info(f"📊 Found {len(thumbnails)} thumbnails in gallery")
        
        if not thumbnails:
            raise Exception("No thumbnails found in gallery")
            
        return thumbnails

    async def select_first_thumbnail(self, page, thumbnails):
        """Select the first (topmost) thumbnail"""
        logger.info("🎯 Selecting first thumbnail")
        
        if not thumbnails:
            raise Exception("No thumbnails available to select")
            
        first_thumbnail = thumbnails[0]
        
        # Click the first thumbnail
        await first_thumbnail.click()
        await page.wait_for_timeout(3000)  # Wait for detail panel to load
        
        logger.info("✅ First thumbnail selected and detail panel loaded")
        
        # Verify that content has changed/loaded
        await page.wait_for_timeout(2000)

    async def analyze_landmark_containers(self, page):
        """Analyze containers containing landmark texts"""
        logger.info("🔍 Starting landmark container analysis")
        
        results = {}
        
        for landmark in self.landmarks:
            logger.info(f"🔍 Analyzing containers for landmark: '{landmark}'")
            
            # Find all containers that contain this landmark text
            try:
                # Use text-based search to find elements containing the landmark
                containers = await page.query_selector_all(f"div:has-text('{landmark}')")
                
                landmark_analysis = {
                    'landmark': landmark,
                    'container_count': len(containers),
                    'containers': []
                }
                
                logger.info(f"📦 Found {len(containers)} containers containing '{landmark}'")
                
                for i, container in enumerate(containers):
                    try:
                        # Get container properties
                        is_visible = await container.is_visible()
                        container_text = await container.text_content() or ""
                        container_class = await container.get_attribute('class') or 'no-class'
                        container_id = await container.get_attribute('id') or 'no-id'
                        
                        # Get container position info
                        bounding_box = None
                        try:
                            bounding_box = await container.bounding_box()
                        except:
                            pass
                        
                        # Check which other landmarks this container contains
                        other_landmarks = []
                        for other_landmark in self.landmarks:
                            if other_landmark != landmark and other_landmark in container_text:
                                other_landmarks.append(other_landmark)
                        
                        container_info = {
                            'index': i,
                            'visible': is_visible,
                            'class': container_class,
                            'id': container_id,
                            'text_length': len(container_text),
                            'text_sample': container_text[:200] + "..." if len(container_text) > 200 else container_text,
                            'other_landmarks_present': other_landmarks,
                            'total_landmarks_count': len(other_landmarks) + 1,  # +1 for the current landmark
                            'bounding_box': bounding_box
                        }
                        
                        landmark_analysis['containers'].append(container_info)
                        
                        logger.info(f"  📋 Container {i}: class='{container_class[:50]}...' visible={is_visible} text_len={len(container_text)} other_landmarks={other_landmarks}")
                        
                    except Exception as e:
                        logger.error(f"Error analyzing container {i} for '{landmark}': {e}")
                        continue
                
                results[landmark] = landmark_analysis
                
            except Exception as e:
                logger.error(f"Error finding containers for landmark '{landmark}': {e}")
                results[landmark] = {
                    'landmark': landmark,
                    'container_count': 0,
                    'containers': [],
                    'error': str(e)
                }
        
        return results

    def generate_summary(self, analysis_results):
        """Generate summary statistics"""
        logger.info("📊 Generating summary statistics")
        
        summary = {
            'total_landmarks_analyzed': len(self.landmarks),
            'landmark_summaries': {},
            'multi_landmark_containers': []
        }
        
        # Per-landmark summaries
        for landmark, data in analysis_results.items():
            if 'error' not in data:
                visible_count = sum(1 for c in data['containers'] if c['visible'])
                multi_landmark_count = sum(1 for c in data['containers'] if c['total_landmarks_count'] > 1)
                
                summary['landmark_summaries'][landmark] = {
                    'total_containers': data['container_count'],
                    'visible_containers': visible_count,
                    'containers_with_multiple_landmarks': multi_landmark_count
                }
                
                logger.info(f"📈 {landmark}: {data['container_count']} total, {visible_count} visible, {multi_landmark_count} multi-landmark")
        
        # Find containers with all landmarks
        all_landmarks_containers = []
        if analysis_results:
            # Get the first landmark's containers as base
            first_landmark = list(analysis_results.keys())[0]
            if 'containers' in analysis_results[first_landmark]:
                for container in analysis_results[first_landmark]['containers']:
                    if container['total_landmarks_count'] == len(self.landmarks):
                        all_landmarks_containers.append({
                            'class': container['class'],
                            'text_sample': container['text_sample'],
                            'text_length': container['text_length'],
                            'visible': container['visible']
                        })
        
        summary['containers_with_all_landmarks'] = {
            'count': len(all_landmarks_containers),
            'containers': all_landmarks_containers
        }
        
        logger.info(f"🎯 Containers with ALL landmarks: {len(all_landmarks_containers)}")
        
        return summary

    async def save_results(self):
        """Save analysis results to JSON file"""
        results_file = log_dir / f"landmark_analysis_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Results saved to: {results_file}")
        return results_file

    async def run_analysis(self):
        """Run the complete landmark container analysis"""
        logger.info("🚀 Starting Landmark Container Analysis Test")
        logger.info(f"📝 Log file: {log_file}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                page.set_default_timeout(30000)
                
                try:
                    # Step 1: Login
                    await self.login(page)
                    
                    # Step 2: Navigate to gallery
                    thumbnails = await self.navigate_to_gallery(page)
                    
                    # Step 3: Select first thumbnail
                    await self.select_first_thumbnail(page, thumbnails)
                    
                    # Step 4: Analyze containers
                    analysis_results = await self.analyze_landmark_containers(page)
                    self.analysis_results['container_analysis'] = analysis_results
                    
                    # Step 5: Generate summary
                    summary = self.generate_summary(analysis_results)
                    self.analysis_results['summary'] = summary
                    
                    # Step 6: Save results
                    results_file = await self.save_results()
                    
                    logger.info("✅ Analysis completed successfully")
                    logger.info(f"📊 Summary: {summary['total_landmarks_analyzed']} landmarks analyzed")
                    logger.info(f"🎯 Found {summary['containers_with_all_landmarks']['count']} containers with all landmarks")
                    
                    # Keep browser open for inspection
                    logger.info("🔍 Browser kept open for manual inspection")
                    await page.wait_for_timeout(5000)
                    
                except Exception as e:
                    logger.error(f"Error during analysis: {e}")
                    self.analysis_results['error'] = str(e)
                    await self.save_results()
                    raise
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Critical error: {e}")
            raise

async def main():
    """Main test function"""
    analyzer = LandmarkContainerAnalyzer()
    await analyzer.run_analysis()

if __name__ == "__main__":
    print("🧪 Landmark Container Analysis Test")
    print("=" * 50)
    asyncio.run(main())
    print("✅ Test completed!")