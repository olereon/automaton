#!/usr/bin/env python3
"""
Extraction Validation and Quality Assessment

This module provides comprehensive validation and quality assessment for
landmark-based metadata extraction, including cross-field validation,
format verification, and confidence scoring.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import json

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation process"""
    is_valid: bool
    confidence_score: float
    issues: List[str]
    suggestions: List[str]
    quality_metrics: Dict[str, float]


@dataclass
class CrossFieldValidation:
    """Cross-field validation result"""
    fields_consistent: bool
    consistency_score: float
    inconsistencies: List[str]
    recommendations: List[str]


class MetadataValidator:
    """Comprehensive metadata validation system"""
    
    def __init__(self, config):
        self.config = config
        
        # Validation patterns
        self.date_patterns = [
            (r'\d{4}-\d{1,2}-\d{1,2}', '%Y-%m-%d'),
            (r'\d{1,2}/\d{1,2}/\d{4}', '%m/%d/%Y'),
            (r'\d{1,2}-\d{1,2}-\d{4}', '%m-%d-%Y'),
            (r'\w{3} \d{1,2}, \d{4}', '%b %d, %Y'),
            (r'\d{1,2} \w{3} \d{4}', '%d %b %Y'),
            (r'\d{4}/\d{1,2}/\d{1,2}', '%Y/%m/%d')
        ]
        
        # Quality thresholds
        self.quality_thresholds = {
            'date_format_valid': 0.8,
            'date_recent': 0.6,
            'prompt_length_adequate': 0.7,
            'prompt_content_quality': 0.6,
            'extraction_method_reliability': 0.5
        }
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> ValidationResult:
        """Validate extracted metadata comprehensively"""
        try:
            issues = []
            suggestions = []
            quality_metrics = {}
            
            # Validate generation date
            date_validation = self._validate_generation_date(metadata.get('generation_date'))
            quality_metrics.update(date_validation)
            
            if not date_validation.get('format_valid', False):
                issues.append("Generation date format is invalid")
                suggestions.append("Check date extraction patterns and selectors")
            
            if not date_validation.get('reasonable_date', False):
                issues.append("Generation date seems unreasonable")
                suggestions.append("Verify date extraction is from correct element")
            
            # Validate prompt
            prompt_validation = self._validate_prompt(metadata.get('prompt'))
            quality_metrics.update(prompt_validation)
            
            if not prompt_validation.get('adequate_length', False):
                issues.append("Prompt appears too short or truncated")
                suggestions.append("Try alternative prompt extraction methods")
            
            if not prompt_validation.get('content_quality', False):
                issues.append("Prompt content quality is questionable")
                suggestions.append("Verify prompt extraction from correct element")
            
            # Cross-field validation
            cross_validation = self._validate_cross_fields(metadata)
            quality_metrics.update({f"cross_field_{k}": v for k, v in quality_metrics.items()})
            
            if not cross_validation.fields_consistent:
                issues.extend(cross_validation.inconsistencies)
                suggestions.extend(cross_validation.recommendations)
            
            # Calculate overall confidence score
            confidence_score = self._calculate_overall_confidence(quality_metrics)
            
            return ValidationResult(
                is_valid=len(issues) == 0,
                confidence_score=confidence_score,
                issues=issues,
                suggestions=suggestions,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Error in metadata validation: {e}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                issues=[f"Validation error: {str(e)}"],
                suggestions=["Review validation logic"],
                quality_metrics={}
            )
    
    def _validate_generation_date(self, date_value: Any) -> Dict[str, float]:
        """Validate generation date field"""
        metrics = {
            'date_present': 0.0,
            'format_valid': 0.0,
            'reasonable_date': 0.0,
            'recent_date': 0.0
        }
        
        try:
            if not date_value or date_value in ['Unknown Date', None]:
                return metrics
            
            metrics['date_present'] = 1.0
            
            date_str = str(date_value).strip()
            
            # Check format validity
            parsed_date = None
            for pattern, format_str in self.date_patterns:
                if re.match(pattern, date_str):
                    try:
                        parsed_date = datetime.strptime(date_str, format_str)
                        metrics['format_valid'] = 1.0
                        break
                    except ValueError:
                        continue
            
            if parsed_date:
                now = datetime.now()
                
                # Check if date is reasonable (not too far in future/past)
                if (parsed_date >= now - timedelta(days=365) and 
                    parsed_date <= now + timedelta(days=30)):
                    metrics['reasonable_date'] = 1.0
                
                # Check if date is recent (within last 30 days gets higher score)
                days_ago = (now - parsed_date).days
                if days_ago <= 30:
                    metrics['recent_date'] = 1.0
                elif days_ago <= 90:
                    metrics['recent_date'] = 0.7
                elif days_ago <= 180:
                    metrics['recent_date'] = 0.4
                else:
                    metrics['recent_date'] = 0.2
            
            return metrics
            
        except Exception as e:
            logger.debug(f"Error validating date: {e}")
            return metrics
    
    def _validate_prompt(self, prompt_value: Any) -> Dict[str, float]:
        """Validate prompt field"""
        metrics = {
            'prompt_present': 0.0,
            'adequate_length': 0.0,
            'content_quality': 0.0,
            'no_truncation_indicators': 0.0
        }
        
        try:
            if not prompt_value or prompt_value in ['Unknown Prompt', None]:
                return metrics
            
            metrics['prompt_present'] = 1.0
            
            prompt_str = str(prompt_value).strip()
            
            # Check length adequacy
            if len(prompt_str) >= 20:
                metrics['adequate_length'] = min(len(prompt_str) / 100.0, 1.0)
            
            # Check content quality indicators
            quality_score = 0.0
            
            # Has descriptive words
            descriptive_words = ['camera', 'light', 'scene', 'image', 'video', 'style', 'color']
            found_descriptive = sum(1 for word in descriptive_words if word in prompt_str.lower())
            quality_score += min(found_descriptive / 3.0, 0.3)
            
            # Not mostly punctuation or special characters
            alpha_ratio = len(re.sub(r'[^a-zA-Z]', '', prompt_str)) / len(prompt_str)
            quality_score += min(alpha_ratio, 0.4)
            
            # Has reasonable sentence structure
            if '.' in prompt_str or ',' in prompt_str:
                quality_score += 0.2
            
            # Not obviously an error message
            error_indicators = ['error', 'failed', 'not found', 'undefined', 'null']
            if not any(indicator in prompt_str.lower() for indicator in error_indicators):
                quality_score += 0.1
            
            metrics['content_quality'] = min(quality_score, 1.0)
            
            # Check for truncation indicators
            truncation_indicators = ['...', '…', 'more', 'continued']
            if not any(indicator in prompt_str for indicator in truncation_indicators):
                metrics['no_truncation_indicators'] = 1.0
            else:
                metrics['no_truncation_indicators'] = 0.3  # Might still be valid but truncated
            
            return metrics
            
        except Exception as e:
            logger.debug(f"Error validating prompt: {e}")
            return metrics
    
    def _validate_cross_fields(self, metadata: Dict[str, Any]) -> CrossFieldValidation:
        """Validate consistency across fields"""
        try:
            inconsistencies = []
            recommendations = []
            quality_metrics = {
                'extraction_method_consistency': 0.0,
                'timing_consistency': 0.0,
                'content_correlation': 0.0
            }
            
            # Check extraction method consistency
            extraction_method = metadata.get('extraction_method', '')
            if extraction_method:
                quality_metrics['extraction_method_consistency'] = 0.8
                if extraction_method == 'landmark_based':
                    quality_metrics['extraction_method_consistency'] = 1.0
            
            # Check if extraction timestamp is reasonable
            extraction_timestamp = metadata.get('extraction_timestamp')
            if extraction_timestamp:
                try:
                    extract_time = datetime.fromisoformat(extraction_timestamp.replace('Z', '+00:00'))
                    now = datetime.now()
                    if abs((now - extract_time).total_seconds()) < 300:  # Within 5 minutes
                        quality_metrics['timing_consistency'] = 1.0
                    else:
                        quality_metrics['timing_consistency'] = 0.5
                        inconsistencies.append("Extraction timestamp seems outdated")
                except Exception:
                    quality_metrics['timing_consistency'] = 0.0
                    inconsistencies.append("Invalid extraction timestamp format")
            
            # Basic content correlation checks
            date_present = metadata.get('generation_date') not in [None, 'Unknown Date']
            prompt_present = metadata.get('prompt') not in [None, 'Unknown Prompt']
            
            if date_present and prompt_present:
                quality_metrics['content_correlation'] = 1.0
            elif date_present or prompt_present:
                quality_metrics['content_correlation'] = 0.5
                inconsistencies.append("Only partial metadata extracted")
                recommendations.append("Verify extraction completeness")
            else:
                quality_metrics['content_correlation'] = 0.0
                inconsistencies.append("No valid metadata extracted")
                recommendations.append("Review extraction strategies")
            
            consistency_score = sum(quality_metrics.values()) / len(quality_metrics)
            
            return CrossFieldValidation(
                fields_consistent=len(inconsistencies) == 0,
                consistency_score=consistency_score,
                inconsistencies=inconsistencies,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.debug(f"Error in cross-field validation: {e}")
            return CrossFieldValidation(
                fields_consistent=False,
                consistency_score=0.0,
                inconsistencies=[f"Cross-field validation error: {str(e)}"],
                recommendations=["Review validation logic"],
                quality_metrics={}
            )
    
    def _calculate_overall_confidence(self, quality_metrics: Dict[str, float]) -> float:
        """Calculate overall confidence score based on quality metrics"""
        try:
            if not quality_metrics:
                return 0.0
            
            # Weighted importance of different metrics
            weights = {
                'date_present': 0.15,
                'format_valid': 0.20,
                'reasonable_date': 0.15,
                'prompt_present': 0.15,
                'adequate_length': 0.15,
                'content_quality': 0.10,
                'cross_field_extraction_method_consistency': 0.05,
                'cross_field_content_correlation': 0.05
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for metric, value in quality_metrics.items():
                if metric in weights:
                    weighted_score += value * weights[metric]
                    total_weight += weights[metric]
                else:
                    # Give small weight to other metrics
                    weighted_score += value * 0.01
                    total_weight += 0.01
            
            if total_weight > 0:
                return weighted_score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.debug(f"Error calculating confidence: {e}")
            return 0.0
    
    def get_validation_summary(self, validation_result: ValidationResult) -> str:
        """Get human-readable validation summary"""
        try:
            summary_parts = []
            
            # Overall status
            if validation_result.is_valid:
                summary_parts.append(f"✅ Validation PASSED (confidence: {validation_result.confidence_score:.2f})")
            else:
                summary_parts.append(f"❌ Validation FAILED (confidence: {validation_result.confidence_score:.2f})")
            
            # Issues
            if validation_result.issues:
                summary_parts.append("\nIssues found:")
                for issue in validation_result.issues:
                    summary_parts.append(f"  • {issue}")
            
            # Suggestions
            if validation_result.suggestions:
                summary_parts.append("\nSuggestions:")
                for suggestion in validation_result.suggestions:
                    summary_parts.append(f"  • {suggestion}")
            
            # Quality metrics summary
            if validation_result.quality_metrics:
                summary_parts.append(f"\nQuality metrics:")
                for metric, score in validation_result.quality_metrics.items():
                    status = "✅" if score > 0.7 else "⚠️" if score > 0.4 else "❌"
                    summary_parts.append(f"  {status} {metric}: {score:.2f}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            return f"Error generating validation summary: {e}"


class QualityAssessment:
    """Advanced quality assessment for extraction results"""
    
    def __init__(self, config):
        self.config = config
        self.validator = MetadataValidator(config)
    
    async def assess_extraction_quality(self, extraction_results: Dict[str, Any], 
                                       extraction_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Comprehensive quality assessment of extraction results"""
        try:
            assessment = {
                'overall_quality_score': 0.0,
                'validation_result': None,
                'extraction_reliability': 0.0,
                'data_completeness': 0.0,
                'method_effectiveness': 0.0,
                'recommendations': [],
                'quality_breakdown': {}
            }
            
            # Basic validation
            validation_result = self.validator.validate_metadata(extraction_results)
            assessment['validation_result'] = validation_result
            
            # Extraction reliability assessment
            reliability_score = self._assess_extraction_reliability(
                extraction_results, extraction_context
            )
            assessment['extraction_reliability'] = reliability_score
            
            # Data completeness assessment
            completeness_score = self._assess_data_completeness(extraction_results)
            assessment['data_completeness'] = completeness_score
            
            # Method effectiveness assessment
            effectiveness_score = self._assess_method_effectiveness(
                extraction_results, extraction_context
            )
            assessment['method_effectiveness'] = effectiveness_score
            
            # Calculate overall quality score
            overall_score = (
                validation_result.confidence_score * 0.4 +
                reliability_score * 0.25 +
                completeness_score * 0.20 +
                effectiveness_score * 0.15
            )
            assessment['overall_quality_score'] = overall_score
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(
                validation_result, reliability_score, completeness_score, effectiveness_score
            )
            assessment['recommendations'] = recommendations
            
            # Detailed breakdown
            assessment['quality_breakdown'] = {
                'validation_confidence': validation_result.confidence_score,
                'extraction_reliability': reliability_score,
                'data_completeness': completeness_score,
                'method_effectiveness': effectiveness_score,
                'quality_metrics': validation_result.quality_metrics
            }
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
            return {
                'overall_quality_score': 0.0,
                'error': str(e),
                'recommendations': ['Review quality assessment logic']
            }
    
    def _assess_extraction_reliability(self, results: Dict[str, Any], 
                                     context: Optional[Dict] = None) -> float:
        """Assess reliability of extraction process"""
        try:
            reliability_factors = []
            
            # Method used
            extraction_method = results.get('extraction_method', '')
            if extraction_method == 'landmark_based':
                reliability_factors.append(0.9)
            elif 'css' in extraction_method:
                reliability_factors.append(0.6)
            elif 'heuristic' in extraction_method:
                reliability_factors.append(0.4)
            else:
                reliability_factors.append(0.3)
            
            # Error indicators
            extraction_errors = results.get('extraction_errors', [])
            if not extraction_errors:
                reliability_factors.append(0.9)
            elif len(extraction_errors) == 1:
                reliability_factors.append(0.7)
            else:
                reliability_factors.append(0.4)
            
            # Context availability
            if context and context.get('landmark_elements'):
                reliability_factors.append(0.8)
            else:
                reliability_factors.append(0.5)
            
            return sum(reliability_factors) / len(reliability_factors)
            
        except Exception:
            return 0.3
    
    def _assess_data_completeness(self, results: Dict[str, Any]) -> float:
        """Assess completeness of extracted data"""
        try:
            required_fields = ['generation_date', 'prompt']
            present_fields = 0
            quality_scores = []
            
            for field in required_fields:
                value = results.get(field)
                if value and not str(value).startswith('Unknown'):
                    present_fields += 1
                    
                    # Assess field quality
                    if field == 'generation_date':
                        if len(str(value)) > 5 and any(char.isdigit() for char in str(value)):
                            quality_scores.append(0.9)
                        else:
                            quality_scores.append(0.5)
                    elif field == 'prompt':
                        if len(str(value)) > 20:
                            quality_scores.append(0.9)
                        elif len(str(value)) > 10:
                            quality_scores.append(0.6)
                        else:
                            quality_scores.append(0.3)
            
            completeness = present_fields / len(required_fields)
            quality_avg = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            return (completeness * 0.6) + (quality_avg * 0.4)
            
        except Exception:
            return 0.0
    
    def _assess_method_effectiveness(self, results: Dict[str, Any], 
                                   context: Optional[Dict] = None) -> float:
        """Assess effectiveness of extraction method used"""
        try:
            effectiveness_factors = []
            
            # Check for multiple candidates (indicates thorough search)
            if context and context.get('candidates'):
                candidate_count = len(context['candidates'])
                if candidate_count > 3:
                    effectiveness_factors.append(0.9)
                elif candidate_count > 1:
                    effectiveness_factors.append(0.7)
                else:
                    effectiveness_factors.append(0.5)
            
            # Check validation passed
            if context and context.get('validation_passed'):
                effectiveness_factors.append(0.9)
            else:
                effectiveness_factors.append(0.4)
            
            # Check extraction time (if available)
            extraction_timestamp = results.get('extraction_timestamp')
            if extraction_timestamp:
                try:
                    extract_time = datetime.fromisoformat(extraction_timestamp.replace('Z', '+00:00'))
                    now = datetime.now()
                    seconds_ago = (now - extract_time).total_seconds()
                    if seconds_ago < 60:  # Very recent
                        effectiveness_factors.append(0.9)
                    else:
                        effectiveness_factors.append(0.6)
                except Exception:
                    effectiveness_factors.append(0.5)
            
            return sum(effectiveness_factors) / len(effectiveness_factors) if effectiveness_factors else 0.5
            
        except Exception:
            return 0.3
    
    def _generate_quality_recommendations(self, validation_result: ValidationResult,
                                        reliability_score: float, 
                                        completeness_score: float,
                                        effectiveness_score: float) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        try:
            # Validation-based recommendations
            if validation_result.confidence_score < 0.7:
                recommendations.append("Consider using alternative extraction strategies")
                recommendations.extend(validation_result.suggestions)
            
            # Reliability recommendations
            if reliability_score < 0.6:
                recommendations.append("Review extraction method selection logic")
                recommendations.append("Add more robust landmark detection")
            
            # Completeness recommendations
            if completeness_score < 0.8:
                recommendations.append("Implement additional fallback extraction methods")
                recommendations.append("Improve field-specific extraction patterns")
            
            # Effectiveness recommendations
            if effectiveness_score < 0.6:
                recommendations.append("Optimize extraction strategy performance")
                recommendations.append("Add more comprehensive validation checks")
            
            # Overall recommendations
            overall_score = (validation_result.confidence_score + reliability_score + 
                           completeness_score + effectiveness_score) / 4
            
            if overall_score < 0.5:
                recommendations.append("Consider comprehensive extraction system review")
                recommendations.append("Implement additional debugging and logging")
            
            return list(set(recommendations))  # Remove duplicates
            
        except Exception as e:
            logger.debug(f"Error generating recommendations: {e}")
            return ["Review quality assessment system"]