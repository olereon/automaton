#!/usr/bin/env python3
"""
Relative Prompt Extractor
Robust prompt extraction using DOM structure relationships and ellipsis patterns.
"""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RelativePromptExtractor:
    """Extract prompts using structural relationships and patterns"""
    
    def __init__(self):
        self.ellipsis_patterns = ['...', '…', '</span>...', '</span>…']
        self.metadata_patterns = [
            r'\d{1,2}\s+\w{3}\s+\d{4}',  # Date patterns
            r'^(Wan\d+\.\d+|1080P|4K)$',  # Model/quality indicators
            r'^(Creation Time|Inspiration Mode)$',  # Metadata labels
        ]
    
    async def extract_with_creation_time_anchor(self, container) -> Optional[str]:
        """
        Extract prompt using Creation Time as anchor point.
        
        Strategy:
        1. Find "Creation Time" text
        2. Navigate to parent container
        3. Look for preceding sibling containers with prompt content
        """
        try:
            # Find Creation Time text
            creation_elements = await container.query_selector_all('text="Creation Time"')
            if not creation_elements:
                return None
            
            # Get the parent container of Creation Time
            creation_element = creation_elements[0]
            
            # Navigate up to find the metadata container
            metadata_container = await creation_element.evaluate('''
                element => {
                    // Go up to find container with Creation Time
                    let current = element;
                    while (current && current.parentElement) {
                        current = current.parentElement;
                        if (current.textContent.includes("Creation Time") && 
                            current.textContent.includes("Inspiration Mode")) {
                            return current;
                        }
                    }
                    return null;
                }
            ''')
            
            if not metadata_container:
                return None
            
            # Get the parent that contains both prompt and metadata sections
            main_container = await metadata_container.evaluate('''
                element => element.parentElement
            ''')
            
            if not main_container:
                return None
            
            # Look for the first child (should be prompt section)
            prompt_section = await main_container.query_selector(':first-child')
            if prompt_section:
                prompt_text = await prompt_section.text_content()
                if prompt_text and len(prompt_text.strip()) > 20:
                    return self._clean_prompt_text(prompt_text)
            
            return None
            
        except Exception as e:
            logger.debug(f"Creation Time anchor method failed: {e}")
            return None
    
    async def extract_with_ellipsis_pattern(self, container) -> Optional[str]:
        """
        Extract prompt by finding ellipsis pattern.
        
        Strategy:
        1. Find elements containing "..."
        2. Get their parent containers
        3. Extract full text and clean ellipsis
        """
        try:
            best_prompt = None
            best_length = 0
            
            # Try different ellipsis patterns
            for pattern in self.ellipsis_patterns:
                ellipsis_elements = await container.query_selector_all(f'text="{pattern}"')
                
                for ellipsis_el in ellipsis_elements:
                    # Get the container that has the ellipsis
                    prompt_container = await ellipsis_el.evaluate('''
                        element => {
                            // Find the span or div containing meaningful text
                            let current = element;
                            while (current && current.parentElement) {
                                if (current.tagName === 'SPAN' && 
                                    current.hasAttribute('aria-describedby')) {
                                    return current;
                                }
                                current = current.parentElement;
                            }
                            return element.parentElement;
                        }
                    ''')
                    
                    if prompt_container:
                        full_text = await prompt_container.text_content()
                        clean_text = self._clean_prompt_text(full_text)
                        
                        if (clean_text and 
                            len(clean_text) > best_length and 
                            len(clean_text) > 20 and
                            not self._is_metadata_text(clean_text)):
                            
                            best_prompt = clean_text
                            best_length = len(clean_text)
            
            return best_prompt
            
        except Exception as e:
            logger.debug(f"Ellipsis pattern method failed: {e}")
            return None
    
    async def extract_with_aria_describedby_ranking(self, container) -> Optional[str]:
        """
        Extract prompt by ranking aria-describedby elements.
        
        Strategy:
        1. Find all spans with aria-describedby
        2. Rank by text length (longest likely to be prompt)
        3. Filter out metadata content
        """
        try:
            spans = await container.query_selector_all('span[aria-describedby]')
            candidates = []
            
            for span in spans:
                text = await span.text_content()
                clean_text = self._clean_prompt_text(text)
                
                if (clean_text and 
                    len(clean_text) > 20 and 
                    not self._is_metadata_text(clean_text)):
                    
                    candidates.append({
                        'text': clean_text,
                        'length': len(clean_text),
                        'element': span
                    })
            
            # Sort by length (descending) - longest is likely the prompt
            candidates.sort(key=lambda x: x['length'], reverse=True)
            
            if candidates:
                return candidates[0]['text']
            
            return None
            
        except Exception as e:
            logger.debug(f"Aria-describedby ranking method failed: {e}")
            return None
    
    async def extract_prompt_robust(self, container) -> Optional[str]:
        """
        Robust prompt extraction using multiple strategies.
        
        Returns the first successful extraction from:
        1. Creation Time anchor method
        2. Ellipsis pattern method  
        3. Aria-describedby ranking method
        """
        methods = [
            ("Creation Time Anchor", self.extract_with_creation_time_anchor),
            ("Ellipsis Pattern", self.extract_with_ellipsis_pattern),
            ("Aria-describedby Ranking", self.extract_with_aria_describedby_ranking)
        ]
        
        for method_name, method_func in methods:
            try:
                result = await method_func(container)
                if result:
                    logger.debug(f"✅ {method_name} method succeeded: {result[:50]}...")
                    return result
                else:
                    logger.debug(f"❌ {method_name} method returned no result")
            except Exception as e:
                logger.debug(f"❌ {method_name} method failed: {e}")
                continue
        
        logger.warning("🚨 All prompt extraction methods failed")
        return None
    
    def _clean_prompt_text(self, text: str) -> str:
        """Clean and normalize prompt text"""
        if not text:
            return ""
        
        # Remove ellipsis patterns
        for pattern in self.ellipsis_patterns:
            text = text.replace(pattern, '')
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _is_metadata_text(self, text: str) -> bool:
        """Check if text looks like metadata rather than prompt content"""
        if not text:
            return True
        
        # Check against known metadata patterns
        for pattern in self.metadata_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check for short metadata-like strings
        if len(text) < 20:
            return True
        
        # Check for resolution/quality indicators
        if text.strip() in ['1080P', '4K', 'Off', 'On']:
            return True
        
        return False


# Global instance for easy usage
relative_prompt_extractor = RelativePromptExtractor()