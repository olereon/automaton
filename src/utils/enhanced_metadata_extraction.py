#!/usr/bin/env python3.11
"""
Enhanced metadata extraction for boundary detection after scrolling.
"""

import re
import logging
from typing import Dict, Optional, Any
from playwright.async_api import ElementHandle

logger = logging.getLogger(__name__)


async def extract_container_metadata_enhanced(container: ElementHandle, text_content: str, retry_count: int = 0) -> Optional[Dict[str, str]]:
    """
    Enhanced metadata extraction with retry logic and multiple strategies.
    Specifically designed to handle containers loaded after scrolling.
    """
    
    if retry_count > 0:
        logger.debug(f"   🔄 Enhanced extraction attempt #{retry_count + 1}")
    
    try:
        # Strategy 1: Direct text pattern matching (fastest)
        creation_time = await _extract_creation_time_from_text(text_content)
        prompt_text = await _extract_prompt_from_text(text_content, creation_time)
        
        if creation_time and prompt_text:
            logger.debug(f"   ✅ Strategy 1 success: Time={creation_time}, Prompt={prompt_text[:30]}...")
            return {'creation_time': creation_time, 'prompt': prompt_text}
        
        # Strategy 2: DOM element extraction (more reliable for dynamic content)
        if hasattr(container, 'query_selector_all'):
            creation_time, prompt_text = await _extract_from_dom_elements(container)
            
            if creation_time and prompt_text:
                logger.debug(f"   ✅ Strategy 2 success: Time={creation_time}, Prompt={prompt_text[:30]}...")
                return {'creation_time': creation_time, 'prompt': prompt_text}
        
        # Strategy 3: Comprehensive text scanning (fallback)
        if not creation_time:
            creation_time = await _extract_creation_time_comprehensive(text_content)
        
        if creation_time and not prompt_text:
            prompt_text = await _extract_prompt_comprehensive(text_content, creation_time)
        
        # Strategy 4: Wait and retry for dynamically loading content
        if not creation_time and hasattr(container, 'wait_for'):
            logger.debug(f"   ⏳ Strategy 4: Waiting for dynamic content...")
            try:
                # Wait for any text content to appear
                await container.wait_for(state="visible", timeout=2000)
                # Re-get text content after wait
                fresh_text = await container.text_content() or ""
                if fresh_text != text_content:
                    logger.debug(f"   🔄 Fresh content detected, re-extracting...")
                    return await extract_container_metadata_enhanced(container, fresh_text, retry_count + 1)
            except:
                pass  # Timeout is expected
        
        # Final validation
        if creation_time:
            if not prompt_text:
                prompt_text = ""  # Allow empty prompt if we have time
            
            logger.debug(f"   📊 Final result: Time={creation_time}, Prompt={'[EMPTY]' if not prompt_text else prompt_text[:30] + '...'}")
            return {'creation_time': creation_time, 'prompt': prompt_text}
        
        # Complete failure
        logger.debug(f"   ❌ All extraction strategies failed")
        return None
        
    except Exception as e:
        logger.debug(f"   ❌ Enhanced extraction error: {e}")
        return None


async def _extract_creation_time_from_text(text_content: str) -> str:
    """Extract creation time using multiple pattern strategies"""
    
    # Pattern 1: Standard format with "Creation Time" prefix
    patterns = [
        r'Creation Time\s*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',
        r'(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',  # No prefix
        r'Creation Time[:\s]*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',  # With colon
        r'Created[:\s]*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',  # "Created" instead
        r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',  # Case insensitive month
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return ""


async def _extract_prompt_from_text(text_content: str, creation_time: str) -> str:
    """Extract prompt text using multiple strategies"""
    
    if not creation_time:
        return ""
    
    # Strategy 1: Text after creation time
    lines = text_content.split('\n')
    for i, line in enumerate(lines):
        if creation_time in line and i + 1 < len(lines):
            potential_prompt = lines[i + 1].strip()
            if potential_prompt and len(potential_prompt) > 10:
                # Skip empty lines and find the actual prompt content
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    potential_prompt = lines[j].strip()
                    if potential_prompt and len(potential_prompt) > 10:
                        return potential_prompt
    
    # Strategy 2: Look for camera-related prompts (common pattern)
    camera_patterns = [
        r'(The camera[^.]+\.(?:[^.]+\.)*)',  # Camera descriptions
        r'(A [^.]*camera[^.]+\.(?:[^.]+\.)*)',  # A [adjective] camera...
        r'([^.]*shot[^.]+\.(?:[^.]+\.)*)',  # Shot descriptions
    ]
    
    for pattern in camera_patterns:
        match = re.search(pattern, text_content, re.DOTALL | re.IGNORECASE)
        if match:
            prompt = match.group(1).strip()
            if len(prompt) > 20:
                return prompt
    
    # Strategy 3: Any substantial text that looks like a prompt
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if (line and len(line) > 30 and 
            'Creation Time' not in line and 
            not re.match(r'\d{1,2}\s+\w{3}\s+\d{4}', line) and
            not line.lower().startswith('image to') and
            not line.lower().startswith('download')):
            return line
    
    return ""


async def _extract_from_dom_elements(container: ElementHandle) -> tuple[str, str]:
    """Extract metadata using DOM element queries"""
    
    creation_time = ""
    prompt_text = ""
    
    try:
        # Look for creation time in specific elements
        time_selectors = [
            '.sc-cSMkSB.hUjUPD',  # Common time element class
            '[class*="time"]',
            '[class*="date"]',
            'span:has-text("Creation Time") + span',
            'div:has-text("Creation Time")'
        ]
        
        for selector in time_selectors:
            try:
                elements = await container.query_selector_all(selector)
                for element in elements:
                    element_text = await element.text_content() or ""
                    # Check if this looks like a creation time
                    if re.match(r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}', element_text):
                        creation_time = element_text
                        break
                if creation_time:
                    break
            except:
                continue
        
        # Look for prompt in specific elements
        prompt_selectors = [
            '.sc-jJRqov.cxtNJi span[aria-describedby]',  # Specific prompt class
            '.sc-dDrhAi.dnESm',  # Truncated prompt divs
            '[aria-describedby]',  # Any aria-describedby elements
            '[class*="prompt"]',
            '[class*="description"]',
            'span[title]'  # Elements with title attribute (often prompts)
        ]
        
        for selector in prompt_selectors:
            try:
                elements = await container.query_selector_all(selector)
                for element in elements:
                    element_text = await element.text_content() or ""
                    # Check if this looks like a prompt (substantial text, not metadata)
                    if (len(element_text) > 20 and 
                        not re.match(r'\d{1,2}\s+\w{3}\s+\d{4}', element_text) and
                        'Creation Time' not in element_text):
                        prompt_text = element_text.replace('...', '').strip()
                        break
                if prompt_text:
                    break
            except:
                continue
                
    except Exception as e:
        logger.debug(f"   DOM extraction error: {e}")
    
    return creation_time, prompt_text


async def _extract_creation_time_comprehensive(text_content: str) -> str:
    """Comprehensive creation time extraction as final fallback"""
    
    # Split by common separators and look in each part
    parts = re.split(r'[|\n\t]+', text_content)
    
    for part in parts:
        part = part.strip()
        # Look for any datetime pattern in this part
        if re.match(r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}', part):
            return part
    
    return ""


async def _extract_prompt_comprehensive(text_content: str, creation_time: str) -> str:
    """Comprehensive prompt extraction as final fallback"""
    
    # Remove creation time and common metadata from text
    clean_text = text_content
    if creation_time:
        clean_text = clean_text.replace(creation_time, '')
    
    # Remove common metadata patterns
    clean_text = re.sub(r'Creation Time.*?\n', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'Image to Video.*?\n', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'Download.*?\n', '', clean_text, flags=re.IGNORECASE)
    
    # Split into lines and find the most substantial one
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    
    # Find the longest line that looks like prompt content
    best_prompt = ""
    for line in lines:
        if len(line) > len(best_prompt) and len(line) > 20:
            best_prompt = line
    
    return best_prompt