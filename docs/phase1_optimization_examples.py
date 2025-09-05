"""
Phase 1 Optimization Examples for Generation Download Manager

This file shows how to replace common patterns with optimized versions.
"""

import asyncio
from src.utils.adaptive_timeout_manager import adaptive_timeout_manager
from src.utils.scroll_optimizer import scroll_optimizer

# EXAMPLE 1: Replace Fixed Timeouts with Adaptive Timeouts

# OLD CODE (inefficient):
async def old_wait_for_element(page, selector):
    await page.wait_for_timeout(2000)  # Always waits full 2 seconds
    element = await page.query_selector(selector)
    return element

# NEW CODE (optimized):
async def new_wait_for_element(page, selector):
    result = await adaptive_timeout_manager.wait_for_element(page, selector, 2.0)
    return result.result if result.success else None
    # Saves 1-1.8 seconds on average when element appears quickly


# EXAMPLE 2: Replace Multiple Scroll Methods with Unified System

# OLD CODE (redundant):
async def old_scroll_operations(page):
    # Try multiple scroll strategies sequentially
    success = False
    
    try:
        success = await try_enhanced_infinite_scroll_triggers(page)
    except:
        pass
    
    if not success:
        try:
            success = await try_network_idle_scroll(page)  
        except:
            pass
    
    if not success:
        try:
            success = await try_manual_element_scroll(page)
        except:
            pass
    
    return success

# NEW CODE (optimized):
async def new_scroll_operations(page):
    result = await scroll_optimizer.scroll_to_load_content(
        page, 
        container_selector='.gallery',
        max_distance=2500,
        expected_content_increase=3
    )
    return result.success
    # Saves 2-5 seconds by using optimal strategy first


# EXAMPLE 3: Replace Network Idle Waits

# OLD CODE:
async def old_wait_for_network_idle(page):
    await page.wait_for_timeout(3000)  # Fixed 3s wait
    await page.wait_for_load_state("networkidle", timeout=2000)

# NEW CODE: 
async def new_wait_for_network_idle(page):
    result = await adaptive_timeout_manager.wait_for_network_idle(
        page, idle_time=0.5, timeout=3.0
    )
    # Completes as soon as network is idle, saves 1-2.5 seconds


# EXAMPLE 4: Replace Metadata Waiting

# OLD CODE:
async def old_wait_for_metadata(page, selectors):
    await page.wait_for_timeout(2000)  # Fixed wait
    
    for selector in selectors:
        element = await page.query_selector(selector)
        if element:
            text = await element.text_content()
            if not text:
                await page.wait_for_timeout(1000)  # Another fixed wait
    
    return True

# NEW CODE:
async def new_wait_for_metadata(page, selectors):
    result = await adaptive_timeout_manager.wait_for_metadata_loaded(
        page, selectors, timeout=5.0
    )
    return result.success
    # Saves 2-3 seconds when metadata loads quickly


# EXAMPLE 5: Replace Download Completion Waiting

# OLD CODE:
async def old_wait_for_download(page, download_selector):
    await page.wait_for_timeout(5000)  # Always wait 5 seconds
    button = await page.query_selector(download_selector)
    return button is not None

# NEW CODE:
async def new_wait_for_download(page, download_selector):
    result = await adaptive_timeout_manager.wait_for_download_complete(
        page, download_selector, timeout=5.0
    )
    return result.success
    # Saves 3-4 seconds when download completes quickly
