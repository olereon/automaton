#!/usr/bin/env python3.11
"""
Enhanced metadata extraction for boundary detection after scrolling.
Robust implementation with multiple fallback strategies and comprehensive error handling.
"""

import re
import logging
import asyncio
import time
from typing import Dict, Optional, Any, List, Tuple
from playwright.async_api import ElementHandle, Page, Error as PlaywrightError

logger = logging.getLogger(__name__)


class MetadataExtractionConfig:
    """Configuration for metadata extraction strategies"""
    
    def __init__(self):
        # Timeout configurations
        self.dom_wait_timeout = 3000  # ms
        self.element_visibility_timeout = 2000  # ms
        self.network_idle_timeout = 1000  # ms
        
        # Retry configurations
        self.max_retry_attempts = 4
        self.retry_delay_ms = 1500
        
        # Strategy configurations
        self.enable_dom_analysis = True
        self.enable_text_patterns = True
        self.enable_spatial_analysis = True
        self.enable_dynamic_content_wait = True
        
        # Debugging
        self.debug_mode = False
        self.log_extraction_details = True


async def extract_container_metadata_enhanced(container: ElementHandle, text_content: str, retry_count: int = 0, config: MetadataExtractionConfig = None) -> Optional[Dict[str, str]]:
    """
    Enhanced metadata extraction with comprehensive retry logic and multiple strategies.
    Specifically designed to handle containers loaded after scrolling with robust error recovery.
    
    Args:
        container: The DOM container element
        text_content: Initial text content from container
        retry_count: Current retry attempt number
        config: Configuration for extraction behavior
    
    Returns:
        Dictionary with 'creation_time' and 'prompt' keys, or None if all strategies fail
    """
    
    if config is None:
        config = MetadataExtractionConfig()
    
    extraction_start = time.time()
    attempt_id = f"attempt_{retry_count + 1}"
    
    if retry_count > 0:
        logger.debug(f"   🔄 Enhanced extraction {attempt_id}/{config.max_retry_attempts}")
        # Progressive delay for retries
        await asyncio.sleep((retry_count * config.retry_delay_ms) / 1000)
    
    try:
        # Initialize result tracking
        extraction_results = {
            'creation_time': None,
            'prompt': None,
            'strategies_attempted': [],
            'extraction_time': 0,
            'retry_count': retry_count
        }
        
        # Strategy 1: Fast text pattern matching
        if config.enable_text_patterns:
            extraction_results['strategies_attempted'].append('text_patterns')
            creation_time, prompt_text = await _strategy_text_patterns(text_content, config)
            
            if creation_time:
                extraction_results['creation_time'] = creation_time
                extraction_results['prompt'] = prompt_text or ""
                
                if config.log_extraction_details:
                    logger.debug(f"   ✅ Text patterns success: Time={creation_time}, Prompt={prompt_text[:30] if prompt_text else '[EMPTY]'}...")
                
                extraction_results['extraction_time'] = time.time() - extraction_start
                return _format_extraction_result(extraction_results)
        
        # Strategy 2: DOM element analysis (more reliable for dynamic content)
        if config.enable_dom_analysis and hasattr(container, 'query_selector_all'):
            extraction_results['strategies_attempted'].append('dom_analysis')
            creation_time, prompt_text = await _strategy_dom_analysis(container, config)
            
            if creation_time:
                extraction_results['creation_time'] = creation_time
                extraction_results['prompt'] = prompt_text or ""
                
                if config.log_extraction_details:
                    logger.debug(f"   ✅ DOM analysis success: Time={creation_time}, Prompt={prompt_text[:30] if prompt_text else '[EMPTY]'}...")
                
                extraction_results['extraction_time'] = time.time() - extraction_start
                return _format_extraction_result(extraction_results)
        
        # Strategy 3: Spatial context analysis
        if config.enable_spatial_analysis:
            extraction_results['strategies_attempted'].append('spatial_analysis')
            creation_time, prompt_text = await _strategy_spatial_analysis(container, text_content, config)
            
            if creation_time:
                extraction_results['creation_time'] = creation_time
                extraction_results['prompt'] = prompt_text or ""
                
                if config.log_extraction_details:
                    logger.debug(f"   ✅ Spatial analysis success: Time={creation_time}, Prompt={prompt_text[:30] if prompt_text else '[EMPTY]'}...")
                
                extraction_results['extraction_time'] = time.time() - extraction_start
                return _format_extraction_result(extraction_results)
        
        # Strategy 4: Dynamic content waiting and retry
        if config.enable_dynamic_content_wait and retry_count < config.max_retry_attempts:
            extraction_results['strategies_attempted'].append('dynamic_content_wait')
            
            retry_result = await _strategy_dynamic_content_wait(container, text_content, retry_count, config)
            if retry_result:
                if config.log_extraction_details:
                    logger.debug(f"   ✅ Dynamic content wait success after retry")
                return retry_result
        
        # Strategy 5: Comprehensive fallback extraction
        extraction_results['strategies_attempted'].append('comprehensive_fallback')
        creation_time, prompt_text = await _strategy_comprehensive_fallback(text_content, config)
        
        if creation_time:
            extraction_results['creation_time'] = creation_time
            extraction_results['prompt'] = prompt_text or ""
            
            if config.log_extraction_details:
                logger.debug(f"   ✅ Comprehensive fallback success: Time={creation_time}, Prompt={prompt_text[:30] if prompt_text else '[EMPTY]'}...")
            
            extraction_results['extraction_time'] = time.time() - extraction_start
            return _format_extraction_result(extraction_results)
        
        # All strategies failed
        extraction_results['extraction_time'] = time.time() - extraction_start
        
        if config.log_extraction_details:
            logger.warning(f"   ❌ All extraction strategies failed for {attempt_id}")
            logger.debug(f"   📊 Attempted strategies: {', '.join(extraction_results['strategies_attempted'])}")
            logger.debug(f"   ⏱️ Total extraction time: {extraction_results['extraction_time']:.3f}s")
        
        return None
        
    except Exception as e:
        extraction_time = time.time() - extraction_start
        logger.error(f"   ❌ Critical error in enhanced extraction {attempt_id}: {e}")
        logger.debug(f"   ⏱️ Failed after {extraction_time:.3f}s")
        
        # If we haven't exhausted retries and error might be transient, try once more
        if retry_count < config.max_retry_attempts and _is_transient_error(e):
            logger.debug(f"   🔄 Transient error detected, will retry...")
            return await extract_container_metadata_enhanced(container, text_content, retry_count + 1, config)
        
        return None


def _format_extraction_result(extraction_results: Dict[str, Any]) -> Dict[str, str]:
    """Format extraction results into the expected return format"""
    return {
        'creation_time': extraction_results['creation_time'],
        'prompt': extraction_results['prompt']
    }


def _is_transient_error(error: Exception) -> bool:
    """Determine if an error is transient and worth retrying"""
    transient_indicators = [
        'timeout',
        'network',
        'connection',
        'element not found',
        'element is not attached',
        'element is not visible'
    ]
    
    error_message = str(error).lower()
    return any(indicator in error_message for indicator in transient_indicators)


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


# New enhanced strategy functions
async def _strategy_text_patterns(text_content: str, config: MetadataExtractionConfig) -> Tuple[Optional[str], Optional[str]]:
    """Strategy 1: Extract metadata using comprehensive text pattern matching"""
    
    try:
        # Enhanced creation time patterns with more variations
        creation_time_patterns = [
            # Standard formats with prefixes
            r'Creation Time[:\s]*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',
            r'Created[:\s]*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',
            r'Generated[:\s]*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',
            r'Date[:\s]*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',
            
            # Standalone datetime patterns
            r'(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',
            r'(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',  # Full month names
            
            # Alternative separators
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4}\s+\d{2}:\d{2}:\d{2})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{2}:\d{2}:\d{2})',
            
            # Time-first patterns (less common but possible)
            r'(\d{2}:\d{2}:\d{2}\s+\d{1,2}\s+\w{3}\s+\d{4})',
        ]
        
        creation_time = None
        for pattern in creation_time_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                potential_time = match.group(1).strip()
                # Validate the extracted time format
                if _validate_creation_time_format(potential_time):
                    creation_time = potential_time
                    break
        
        if not creation_time:
            return None, None
        
        # Extract prompt using enhanced strategies
        prompt_text = await _extract_prompt_from_text_enhanced(text_content, creation_time)
        
        return creation_time, prompt_text
        
    except Exception as e:
        logger.debug(f"Text pattern strategy error: {e}")
        return None, None


def _validate_creation_time_format(time_string: str) -> bool:
    """Validate that extracted time string matches expected formats"""
    
    validation_patterns = [
        r'^\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}$',  # "24 Aug 2025 01:37:01"
        r'^\d{1,2}\s+\w{3,9}\s+\d{4}\s+\d{2}:\d{2}:\d{2}$',  # Full month names
        r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}\s+\d{2}:\d{2}:\d{2}$',  # Alternative separators
        r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{2}:\d{2}:\d{2}$',  # ISO-like format
        r'^\d{2}:\d{2}:\d{2}\s+\d{1,2}\s+\w{3}\s+\d{4}$',  # Time-first format
    ]
    
    for pattern in validation_patterns:
        if re.match(pattern, time_string.strip()):
            return True
    
    return False


async def _extract_prompt_from_text_enhanced(text_content: str, creation_time: str) -> Optional[str]:
    """Enhanced prompt extraction with multiple strategies and better filtering"""
    
    if not creation_time:
        return None
    
    try:
        # Strategy 1: Extract text that appears after creation time
        lines = text_content.split('\n')
        creation_time_line_index = -1
        
        for i, line in enumerate(lines):
            if creation_time in line:
                creation_time_line_index = i
                break
        
        if creation_time_line_index >= 0:
            # Look for prompt in subsequent lines
            for i in range(creation_time_line_index + 1, len(lines)):
                line = lines[i].strip()
                if line and _is_valid_prompt_candidate(line):
                    return line
        
        # Strategy 2: Enhanced pattern-based extraction
        enhanced_prompt_patterns = [
            # Camera-related prompts (common)
            r'((?:The\s+)?[Cc]amera[^.]*\.(?:[^.]*\.)*)',
            r'([Aa]\s+[^.]*camera[^.]*\.(?:[^.]*\.)*)',
            r'([^.]*\b(?:shot|angle|perspective|view)\b[^.]*\.(?:[^.]*\.)*)',
            
            # Action and scene descriptions
            r'([^.]*\b(?:shows?|depicts?|features?)\b[^.]*\.(?:[^.]*\.)*)',
            r'([^.]*\b(?:scene|image|video)\b[^.]*\.(?:[^.]*\.)*)',
            
            # Descriptive prompts starting with articles
            r'([Aa]n?\s+[^.]{20,}\.(?:[^.]*\.)*)',
            r'([Tt]he\s+[^.]{20,}\.(?:[^.]*\.)*)',
            
            # Any substantial sentence-like content
            r'([A-Z][^.]{30,}\.(?:[^.]*\.)*)',  # Capitalized, substantial content
        ]
        
        for pattern in enhanced_prompt_patterns:
            match = re.search(pattern, text_content, re.DOTALL | re.IGNORECASE)
            if match:
                prompt_candidate = match.group(1).strip()
                if _is_valid_prompt_candidate(prompt_candidate):
                    return prompt_candidate
        
        # Strategy 3: Find the longest substantial text line
        best_candidate = ""
        for line in lines:
            line = line.strip()
            if (_is_valid_prompt_candidate(line) and 
                len(line) > len(best_candidate) and 
                len(line) >= 20):
                best_candidate = line
        
        return best_candidate if best_candidate else None
        
    except Exception as e:
        logger.debug(f"Enhanced prompt extraction error: {e}")
        return None


def _is_valid_prompt_candidate(text: str) -> bool:
    """Validate if text is a good prompt candidate"""
    
    if not text or len(text.strip()) < 10:
        return False
    
    # Filter out metadata and UI elements
    invalid_indicators = [
        'creation time', 'created', 'generated', 'download',
        'image to video', 'video to video', 'uploaded',
        'click', 'button', 'menu', 'option', 'settings',
        'error', 'failed', 'success', 'loading',
        'www.', 'http', '.com', '.net', '.org',
        'copyright', '©', '®', '™'
    ]
    
    text_lower = text.lower()
    for indicator in invalid_indicators:
        if indicator in text_lower:
            return False
    
    # Must contain some descriptive content
    descriptive_indicators = [
        'camera', 'shot', 'scene', 'image', 'video', 'shows', 'depicts',
        'features', 'the', 'a ', 'an ', 'with', 'of', 'in', 'on', 'at',
        'person', 'people', 'man', 'woman', 'child', 'animal', 'object',
        'landscape', 'building', 'room', 'outdoor', 'indoor'
    ]
    
    has_descriptive_content = any(indicator in text_lower for indicator in descriptive_indicators)
    
    # Check for sentence-like structure (contains letters and reasonable punctuation)
    has_letters = any(c.isalpha() for c in text)
    has_reasonable_structure = len(text.split()) >= 3  # At least 3 words
    
    return has_descriptive_content and has_letters and has_reasonable_structure


async def _strategy_dom_analysis(container: ElementHandle, config: MetadataExtractionConfig) -> Tuple[Optional[str], Optional[str]]:
    """Strategy 2: Extract metadata using DOM element analysis with enhanced selectors"""
    
    try:
        creation_time = None
        prompt_text = None
        
        # Enhanced creation time selectors with more comprehensive coverage
        time_selectors = [
            # Specific known classes and patterns
            '.sc-cSMkSB.hUjUPD',  # Known time element class
            '.sc-cSMkSB',          # Broader class match
            '.hUjUPD',             # Alternative class
            
            # Generic time-related selectors
            '[class*="time"]',
            '[class*="date"]',
            '[class*="created"]',
            '[class*="generated"]',
        ]
        
        # Try each time selector with timeout handling
        for selector in time_selectors:
            try:
                elements = await asyncio.wait_for(
                    container.query_selector_all(selector),
                    timeout=config.dom_wait_timeout / 1000
                )
                
                for element in elements:
                    try:
                        element_text = await asyncio.wait_for(
                            element.text_content(),
                            timeout=1.0
                        ) or ""
                        
                        # Validate if this looks like a creation time
                        if _validate_creation_time_format(element_text):
                            creation_time = element_text.strip()
                            logger.debug(f"   🔍 DOM time found with selector '{selector}': {creation_time}")
                            break
                        
                    except asyncio.TimeoutError:
                        logger.debug(f"   ⏱️ Timeout reading element text for selector: {selector}")
                        continue
                    except Exception as elem_e:
                        logger.debug(f"   ⚠️ Element text extraction error: {elem_e}")
                        continue
                
                if creation_time:
                    break
                    
            except asyncio.TimeoutError:
                logger.debug(f"   ⏱️ Timeout for selector: {selector}")
                continue
            except Exception as sel_e:
                logger.debug(f"   ⚠️ Selector error for '{selector}': {sel_e}")
                continue
        
        return creation_time, prompt_text
        
    except Exception as e:
        logger.debug(f"DOM analysis strategy error: {e}")
        return None, None


async def _strategy_spatial_analysis(container: ElementHandle, text_content: str, config: MetadataExtractionConfig) -> Tuple[Optional[str], Optional[str]]:
    """Strategy 3: Extract metadata using spatial context and element positioning"""
    
    try:
        # For now, use text-based approach as fallback
        return await _strategy_text_patterns(text_content, config)
        
    except Exception as e:
        logger.debug(f"Spatial analysis strategy error: {e}")
        return None, None


async def _strategy_dynamic_content_wait(container: ElementHandle, text_content: str, retry_count: int, config: MetadataExtractionConfig) -> Optional[Dict[str, str]]:
    """Strategy 4: Wait for dynamic content and retry extraction"""
    
    try:
        if retry_count >= config.max_retry_attempts:
            return None
        
        logger.debug(f"   ⏳ Waiting for dynamic content to load...")
        
        # Wait for any pending network activity
        try:
            # Wait for the element to be in a stable state
            await container.wait_for(state="visible", timeout=config.element_visibility_timeout)
            
            # Wait for potential network idle (new content loading)
            await asyncio.sleep(config.network_idle_timeout / 1000)
            
        except Exception as wait_e:
            logger.debug(f"   ⚠️ Wait operation failed: {wait_e}")
            # Continue even if wait fails
        
        # Get fresh content after waiting
        try:
            fresh_text = await asyncio.wait_for(
                container.text_content(),
                timeout=2.0
            ) or ""
            
            # Check if content has changed significantly
            if fresh_text and fresh_text != text_content:
                text_diff_ratio = len(fresh_text) / max(len(text_content), 1)
                
                if text_diff_ratio > 1.2 or text_diff_ratio < 0.8:  # Significant change
                    logger.debug(f"   🔄 Significant content change detected, retrying extraction...")
                    # Recursive call with fresh content
                    return await extract_container_metadata_enhanced(
                        container, fresh_text, retry_count + 1, config
                    )
        
        except asyncio.TimeoutError:
            logger.debug(f"   ⏱️ Timeout getting fresh text content")
        except Exception as fresh_e:
            logger.debug(f"   ⚠️ Error getting fresh content: {fresh_e}")
        
        return None
        
    except Exception as e:
        logger.debug(f"Dynamic content wait strategy error: {e}")
        return None


async def _strategy_comprehensive_fallback(text_content: str, config: MetadataExtractionConfig) -> Tuple[Optional[str], Optional[str]]:
    """Strategy 5: Comprehensive fallback extraction using all available methods"""
    
    try:
        # Method 1: Parse by various separators and analyze each segment
        separators = ['\n', '\t', '|', '•', '‣', '●']  # Including bullet points
        
        all_segments = [text_content]  # Start with full text
        
        for separator in separators:
            new_segments = []
            for segment in all_segments:
                new_segments.extend(segment.split(separator))
            all_segments = new_segments
        
        # Clean and filter segments
        clean_segments = [seg.strip() for seg in all_segments if seg.strip()]
        
        # Find creation time in segments
        creation_time = None
        for segment in clean_segments:
            if _validate_creation_time_format(segment):
                creation_time = segment
                break
        
        # Find prompt in segments
        prompt_text = None
        prompt_candidates = []
        
        for segment in clean_segments:
            if _is_valid_prompt_candidate(segment):
                prompt_candidates.append(segment)
        
        # Select best prompt candidate (longest valid one)
        if prompt_candidates:
            prompt_text = max(prompt_candidates, key=len)
        
        # Method 2: If still no creation time, try fuzzy matching
        if not creation_time:
            creation_time = _extract_fuzzy_creation_time(text_content)
        
        # Method 3: If still no prompt, try content-based heuristics
        if not prompt_text and creation_time:
            prompt_text = _extract_context_aware_prompt(text_content, creation_time)
        
        return creation_time, prompt_text
        
    except Exception as e:
        logger.debug(f"Comprehensive fallback strategy error: {e}")
        return None, None


def _extract_fuzzy_creation_time(text_content: str) -> Optional[str]:
    """Extract creation time using fuzzy matching techniques"""
    
    try:
        # Look for any sequence that resembles a timestamp
        fuzzy_patterns = [
            r'\b(\d{1,2})\s*[-/\s]\s*(\w{3,9})\s*[-/\s]\s*(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\b',
            r'\b(\d{4})\s*[-/]\s*(\d{1,2})\s*[-/]\s*(\d{1,2})\s+(\d{1,2}):(\d{2}):(\d{2})\b',
            r'\b(\d{1,2})\s+(\w{3})\s+(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\b',
        ]
        
        for pattern in fuzzy_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                # Reconstruct the timestamp
                if len(match) == 6:  # Format: day, month, year, hour, min, sec
                    day, month, year, hour, min_val, sec = match
                    # Try to format it properly
                    if month.isdigit():
                        # Numeric month, convert to text
                        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        if 1 <= int(month) <= 12:
                            month = month_names[int(month)]
                    
                    reconstructed = f"{day} {month} {year} {hour}:{min_val}:{sec}"
                    if _validate_creation_time_format(reconstructed):
                        return reconstructed
        
        return None
        
    except Exception as e:
        logger.debug(f"Fuzzy creation time extraction error: {e}")
        return None


def _extract_context_aware_prompt(text_content: str, creation_time: str) -> Optional[str]:
    """Extract prompt using context awareness around creation time"""
    
    try:
        # Find the position of creation time
        time_pos = text_content.find(creation_time)
        if time_pos == -1:
            return None
        
        # Look before and after the creation time
        before_time = text_content[:time_pos].strip()
        after_time = text_content[time_pos + len(creation_time):].strip()
        
        # Check after creation time first (more common)
        after_lines = [line.strip() for line in after_time.split('\n') if line.strip()]
        for line in after_lines:
            if _is_valid_prompt_candidate(line):
                return line
        
        # Check before creation time
        before_lines = [line.strip() for line in before_time.split('\n') if line.strip()]
        for line in reversed(before_lines):  # Check most recent lines first
            if _is_valid_prompt_candidate(line):
                return line
        
        return None
        
    except Exception as e:
        logger.debug(f"Context-aware prompt extraction error: {e}")
        return None