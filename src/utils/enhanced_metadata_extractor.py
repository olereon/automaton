#!/usr/bin/env python3
"""
Enhanced Metadata Extractor Integration

This module provides the integration layer between the new landmark-based extraction
system and the existing generation download manager, with backward compatibility
and gradual migration support.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

# Import the new landmark extraction system
from .landmark_extractor import LandmarkExtractor, ExtractionContext
from .extraction_strategies import StrategyOrchestrator
from .extraction_validator import MetadataValidator, QualityAssessment

logger = logging.getLogger(__name__)


class EnhancedMetadataExtractor:
    """
    Enhanced metadata extractor that integrates landmark-based extraction
    with existing systems, providing fallback compatibility and quality assessment.
    """
    
    def __init__(self, config, debug_logger=None):
        self.config = config
        self.debug_logger = debug_logger
        
        # Feature flags for gradual rollout
        self.use_landmark_extraction = getattr(config, 'use_landmark_extraction', True)
        self.fallback_to_legacy = getattr(config, 'fallback_to_legacy', True)
        self.quality_threshold = getattr(config, 'quality_threshold', 0.6)
        
        # Initialize components
        self.validator = MetadataValidator(config)
        self.quality_assessor = QualityAssessment(config)
        
        # Legacy extraction stats for comparison
        self.extraction_stats = {
            'landmark_attempts': 0,
            'landmark_successes': 0,
            'legacy_fallbacks': 0,
            'quality_failures': 0
        }
    
    async def extract_metadata_from_page(self, page) -> Optional[Dict[str, str]]:
        """
        Main extraction method that orchestrates landmark-based and legacy extraction
        """
        try:
            extraction_start_time = datetime.now()
            
            # Log extraction attempt
            if self.debug_logger:
                self.debug_logger.log_step(-1, "ENHANCED_EXTRACTION_START", {
                    "use_landmark_extraction": self.use_landmark_extraction,
                    "fallback_to_legacy": self.fallback_to_legacy,
                    "quality_threshold": self.quality_threshold
                })
            
            metadata_result = None
            extraction_method = "unknown"
            quality_assessment = None
            
            # Primary: Landmark-based extraction
            if self.use_landmark_extraction:
                try:
                    self.extraction_stats['landmark_attempts'] += 1
                    
                    landmark_result = await self._extract_with_landmark_system(page)
                    
                    if landmark_result:
                        # Quality assessment
                        quality_assessment = await self.quality_assessor.assess_extraction_quality(
                            landmark_result, 
                            {'extraction_method': 'landmark_based'}
                        )
                        
                        if quality_assessment['overall_quality_score'] >= self.quality_threshold:
                            metadata_result = landmark_result
                            extraction_method = "landmark_based_primary"
                            self.extraction_stats['landmark_successes'] += 1
                            
                            if self.debug_logger:
                                self.debug_logger.log_step(-1, "LANDMARK_EXTRACTION_SUCCESS", {
                                    "quality_score": quality_assessment['overall_quality_score'],
                                    "method": extraction_method,
                                    "validation_passed": quality_assessment['validation_result'].is_valid
                                })
                        else:
                            if self.debug_logger:
                                self.debug_logger.log_step(-1, "LANDMARK_EXTRACTION_LOW_QUALITY", {
                                    "quality_score": quality_assessment['overall_quality_score'],
                                    "threshold": self.quality_threshold,
                                    "issues": quality_assessment['validation_result'].issues
                                })
                            self.extraction_stats['quality_failures'] += 1
                    
                except Exception as e:
                    logger.warning(f"Landmark extraction failed: {e}")
                    if self.debug_logger:
                        self.debug_logger.log_step(-1, "LANDMARK_EXTRACTION_ERROR", {
                            "error": str(e)
                        }, success=False, error=str(e))
            
            # Fallback: Legacy extraction system
            if not metadata_result and self.fallback_to_legacy:
                try:
                    self.extraction_stats['legacy_fallbacks'] += 1
                    
                    legacy_result = await self._extract_with_legacy_system(page)
                    
                    if legacy_result:
                        metadata_result = legacy_result
                        extraction_method = "legacy_fallback"
                        
                        if self.debug_logger:
                            self.debug_logger.log_step(-1, "LEGACY_EXTRACTION_SUCCESS", {
                                "method": extraction_method,
                                "fallback_reason": "landmark_failed_or_low_quality"
                            })
                    
                except Exception as e:
                    logger.warning(f"Legacy extraction also failed: {e}")
                    if self.debug_logger:
                        self.debug_logger.log_step(-1, "LEGACY_EXTRACTION_ERROR", {
                            "error": str(e)
                        }, success=False, error=str(e))
            
            # Final result processing
            if metadata_result:
                # Add extraction metadata
                metadata_result['extraction_method'] = extraction_method
                metadata_result['extraction_timestamp'] = extraction_start_time.isoformat()
                metadata_result['extraction_duration'] = (datetime.now() - extraction_start_time).total_seconds()
                
                if quality_assessment:
                    metadata_result['quality_score'] = quality_assessment['overall_quality_score']
                    metadata_result['validation_passed'] = quality_assessment['validation_result'].is_valid
                
                # Log final success
                if self.debug_logger:
                    self.debug_logger.log_metadata_extraction(
                        thumbnail_index=-1,
                        extraction_method=extraction_method,
                        success=True,
                        extracted_data=metadata_result,
                        quality_score=quality_assessment['overall_quality_score'] if quality_assessment else 0.5
                    )
                
                return metadata_result
            else:
                # Complete failure - return default values
                default_result = {
                    'generation_date': 'Unknown Date',
                    'prompt': 'Unknown Prompt',
                    'extraction_method': 'failed_all_methods',
                    'extraction_timestamp': extraction_start_time.isoformat(),
                    'extraction_duration': (datetime.now() - extraction_start_time).total_seconds(),
                    'quality_score': 0.0,
                    'validation_passed': False
                }
                
                if self.debug_logger:
                    self.debug_logger.log_metadata_extraction(
                        thumbnail_index=-1,
                        extraction_method="failed_all_methods",
                        success=False,
                        extracted_data=default_result,
                        quality_score=0.0
                    )
                
                return default_result
                
        except Exception as e:
            logger.error(f"Critical error in enhanced metadata extraction: {e}")
            if self.debug_logger:
                self.debug_logger.log_step(-1, "ENHANCED_EXTRACTION_CRITICAL_ERROR", {
                    "error": str(e)
                }, success=False, error=str(e))
            
            return {
                'generation_date': 'Unknown Date',
                'prompt': 'Unknown Prompt',
                'extraction_method': 'critical_error',
                'extraction_timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _extract_with_landmark_system(self, page) -> Optional[Dict[str, Any]]:
        """Extract metadata using the new landmark-based system"""
        try:
            # Initialize landmark extractor
            landmark_extractor = LandmarkExtractor(page, self.config)
            
            # Also initialize strategy orchestrator for advanced strategies
            from .landmark_extractor import DOMNavigator
            navigator = DOMNavigator(page)
            orchestrator = StrategyOrchestrator(navigator, self.config)
            
            # Extract metadata
            metadata = await landmark_extractor.extract_metadata()
            
            # If landmark extraction didn't get high confidence, try orchestrator
            if (metadata.get('extraction_errors') or 
                not metadata.get('generation_date') or 
                metadata.get('generation_date') == 'Unknown Date'):
                
                # Build context for orchestrator
                context = ExtractionContext(
                    page=page,
                    thumbnail_index=-1,
                    landmark_elements=[],
                    content_area=None,
                    metadata_panels=[],
                    confidence_threshold=0.6
                )
                
                # Try orchestrated extraction for missing fields
                if not metadata.get('generation_date') or metadata.get('generation_date') == 'Unknown Date':
                    date_result = await orchestrator.extract_with_fallbacks(context, 'generation_date')
                    if date_result.success:
                        metadata['generation_date'] = date_result.extracted_value
                
                if not metadata.get('prompt') or metadata.get('prompt') == 'Unknown Prompt':
                    prompt_result = await orchestrator.extract_with_fallbacks(context, 'prompt')
                    if prompt_result.success:
                        metadata['prompt'] = prompt_result.extracted_value
            
            return metadata
            
        except Exception as e:
            logger.debug(f"Landmark system extraction failed: {e}")
            return None
    
    async def _extract_with_legacy_system(self, page) -> Optional[Dict[str, Any]]:
        """Extract metadata using the legacy system as fallback"""
        try:
            # This mimics the original extraction logic from generation_download_manager.py
            # but simplified for fallback purposes
            
            metadata = {}
            
            # Extract generation date using Creation Time landmark (legacy approach)
            try:
                creation_time_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
                
                if creation_time_elements:
                    for element in creation_time_elements[:3]:  # Try first 3 elements
                        try:
                            parent = await element.evaluate_handle("el => el.parentElement")
                            spans = await parent.query_selector_all("span")
                            
                            if len(spans) >= 2:
                                date_span = spans[1]
                                date_text = await date_span.text_content()
                                if date_text and date_text.strip() != self.config.creation_time_text:
                                    metadata['generation_date'] = date_text.strip()
                                    break
                        except Exception:
                            continue
                
                # Fallback to CSS selector
                if not metadata.get('generation_date'):
                    try:
                        date_element = await page.wait_for_selector(
                            self.config.generation_date_selector, 
                            timeout=3000
                        )
                        if date_element:
                            date_text = await date_element.text_content()
                            metadata['generation_date'] = date_text.strip() if date_text else "Unknown Date"
                    except Exception:
                        metadata['generation_date'] = "Unknown Date"
                        
            except Exception:
                metadata['generation_date'] = "Unknown Date"
            
            # Extract prompt using ellipsis pattern (legacy approach)
            try:
                div_containers = await page.query_selector_all("div")
                
                for container in div_containers[:50]:  # Limit search
                    try:
                        html_content = await container.evaluate("el => el.innerHTML")
                        
                        if (self.config.prompt_ellipsis_pattern in html_content and 
                            "aria-describedby" in html_content):
                            
                            prompt_spans = await container.query_selector_all("span[aria-describedby]")
                            
                            for span in prompt_spans:
                                text_content = await span.text_content()
                                if text_content and len(text_content) > 20:
                                    metadata['prompt'] = text_content.strip()
                                    break
                            
                            if metadata.get('prompt'):
                                break
                                
                    except Exception:
                        continue
                
                # Fallback to CSS selector
                if not metadata.get('prompt'):
                    try:
                        prompt_element = await page.wait_for_selector(
                            self.config.prompt_selector,
                            timeout=3000
                        )
                        if prompt_element:
                            prompt_text = await prompt_element.text_content()
                            metadata['prompt'] = prompt_text.strip() if prompt_text else "Unknown Prompt"
                    except Exception:
                        metadata['prompt'] = "Unknown Prompt"
                        
            except Exception:
                metadata['prompt'] = "Unknown Prompt"
            
            # Only return if we got at least one valid field
            if (metadata.get('generation_date', 'Unknown Date') != 'Unknown Date' or
                metadata.get('prompt', 'Unknown Prompt') != 'Unknown Prompt'):
                return metadata
            
            return None
            
        except Exception as e:
            logger.debug(f"Legacy extraction failed: {e}")
            return None
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about extraction performance"""
        total_attempts = self.extraction_stats['landmark_attempts']
        
        stats = dict(self.extraction_stats)
        
        if total_attempts > 0:
            stats['landmark_success_rate'] = self.extraction_stats['landmark_successes'] / total_attempts
            stats['fallback_rate'] = self.extraction_stats['legacy_fallbacks'] / total_attempts
            stats['quality_failure_rate'] = self.extraction_stats['quality_failures'] / total_attempts
        else:
            stats['landmark_success_rate'] = 0.0
            stats['fallback_rate'] = 0.0
            stats['quality_failure_rate'] = 0.0
        
        return stats
    
    def reset_extraction_stats(self):
        """Reset extraction statistics"""
        self.extraction_stats = {
            'landmark_attempts': 0,
            'landmark_successes': 0,
            'legacy_fallbacks': 0,
            'quality_failures': 0
        }
    
    async def validate_extraction_result(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extraction result and provide quality metrics"""
        try:
            validation_result = self.validator.validate_metadata(metadata)
            
            return {
                'is_valid': validation_result.is_valid,
                'confidence_score': validation_result.confidence_score,
                'issues': validation_result.issues,
                'suggestions': validation_result.suggestions,
                'quality_metrics': validation_result.quality_metrics,
                'summary': self.validator.get_validation_summary(validation_result)
            }
            
        except Exception as e:
            logger.error(f"Error validating extraction result: {e}")
            return {
                'is_valid': False,
                'confidence_score': 0.0,
                'issues': [f"Validation error: {str(e)}"],
                'suggestions': ["Review validation system"],
                'quality_metrics': {},
                'summary': f"Validation failed: {str(e)}"
            }


class LegacyCompatibilityWrapper:
    """
    Wrapper to maintain compatibility with existing code while enabling
    gradual migration to the enhanced extraction system.
    """
    
    def __init__(self, config, debug_logger=None):
        self.enhanced_extractor = EnhancedMetadataExtractor(config, debug_logger)
        self.config = config
    
    async def extract_metadata_from_page(self, page) -> Optional[Dict[str, str]]:
        """
        Legacy-compatible extraction method that returns the same format
        as the original system but uses enhanced extraction internally.
        """
        try:
            result = await self.enhanced_extractor.extract_metadata_from_page(page)
            
            if result:
                # Return only the fields expected by legacy code
                return {
                    'generation_date': result.get('generation_date', 'Unknown Date'),
                    'prompt': result.get('prompt', 'Unknown Prompt')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in legacy compatibility wrapper: {e}")
            return {
                'generation_date': 'Unknown Date',
                'prompt': 'Unknown Prompt'
            }
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics for monitoring"""
        return self.enhanced_extractor.get_extraction_stats()
    
    def reset_stats(self):
        """Reset extraction statistics"""
        self.enhanced_extractor.reset_extraction_stats()


# Configuration helper for enabling enhanced extraction
def configure_enhanced_extraction(config, 
                                enable_landmark=True, 
                                enable_fallback=True, 
                                quality_threshold=0.6):
    """Configure enhanced extraction settings on existing config object"""
    config.use_landmark_extraction = enable_landmark
    config.fallback_to_legacy = enable_fallback
    config.quality_threshold = quality_threshold
    return config


# Factory function for creating extraction instances
def create_metadata_extractor(config, debug_logger=None, legacy_compatible=False):
    """
    Factory function to create appropriate metadata extractor instance
    
    Args:
        config: Configuration object
        debug_logger: Optional debug logger
        legacy_compatible: If True, returns wrapper with legacy interface
    
    Returns:
        Metadata extractor instance
    """
    if legacy_compatible:
        return LegacyCompatibilityWrapper(config, debug_logger)
    else:
        return EnhancedMetadataExtractor(config, debug_logger)