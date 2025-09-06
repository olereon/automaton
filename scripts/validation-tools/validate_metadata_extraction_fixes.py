#!/usr/bin/env python3
"""
Validation Script for Enhanced Metadata Extraction Fixes
Tests the robust metadata extraction implementation against real-world scenarios.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from utils.enhanced_metadata_extraction import (
    extract_container_metadata_enhanced,
    MetadataExtractionConfig,
    _validate_creation_time_format,
    _is_valid_prompt_candidate,
    _extract_fuzzy_creation_time,
    _strategy_text_patterns
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetadataExtractionValidator:
    """Validator for metadata extraction fixes"""
    
    def __init__(self):
        self.config = MetadataExtractionConfig()
        self.config.debug_mode = True
        self.config.log_extraction_details = True
        
        # Real-world test scenarios based on actual issues
        self.test_scenarios = [
            {
                'name': 'Gallery Timing Issue',
                'description': 'Container loads but metadata appears after delay',
                'content_sequence': [
                    "",  # Initial empty state
                    "Loading generation...",  # Loading state
                    "Creation Time 24 Aug 2025 01:37:01\nThe camera captures a breathtaking view of snow-covered mountains at sunset."
                ],
                'expected_time': "24 Aug 2025 01:37:01",
                'expected_prompt_keywords': ["camera", "mountains", "sunset"]
            },
            
            {
                'name': 'Mixed Content with Metadata',
                'description': 'Complex content with multiple timestamps and UI elements',
                'content_sequence': [
                    """
                    Generation Details | Status: Complete | Last Modified: 23 Aug 2025 12:00:00
                    Creation Time 24 Aug 2025 01:37:01
                    The camera slowly pans across a bustling marketplace filled with vendors and customers.
                    Download | Share | More Options
                    Processing Time: 15 seconds | Size: 2.1MB
                    """
                ],
                'expected_time': "24 Aug 2025 01:37:01",
                'expected_prompt_keywords': ["camera", "marketplace", "vendors"]
            },
            
            {
                'name': 'Truncated Prompt Recovery',
                'description': 'Prompt is truncated with ellipsis, need full extraction',
                'content_sequence': [
                    """
                    Creation Time 24 Aug 2025 01:37:01
                    A detailed view of an ancient forest with towering oak trees and dappled sunlight filtering through the canopy, creating a mystical atmosphere...
                    """
                ],
                'expected_time': "24 Aug 2025 01:37:01", 
                'expected_prompt_keywords': ["forest", "oak", "trees", "sunlight", "canopy"]
            },
            
            {
                'name': 'Alternative Time Formats',
                'description': 'Non-standard time formatting variations',
                'content_sequence': [
                    """
                    Generated: 2025-08-24 01:37:01
                    Camera shows a panoramic view of a coastal town with colorful buildings cascading down hillsides.
                    """
                ],
                'expected_time': None,  # Will be detected by fuzzy matching
                'expected_prompt_keywords': ["camera", "coastal", "town", "buildings"]
            },
            
            {
                'name': 'Minimal Content Edge Case',
                'description': 'Very sparse content with just essential metadata',
                'content_sequence': [
                    "Time: 24 Aug 2025 01:37:01 | Ocean waves crash against rocky shore"
                ],
                'expected_time': "24 Aug 2025 01:37:01",
                'expected_prompt_keywords': ["ocean", "waves", "shore"]
            },
            
            {
                'name': 'Multiple Timestamps Disambiguation',
                'description': 'Multiple timestamps present, need to pick the right one',
                'content_sequence': [
                    """
                    Upload Date: 23 Aug 2025 10:00:00
                    Creation Time: 24 Aug 2025 01:37:01
                    Modified: 25 Aug 2025 08:30:15
                    A wide-angle shot revealing the grandeur of a cathedral with intricate Gothic architecture.
                    """
                ],
                'expected_time': "24 Aug 2025 01:37:01",  # Should pick Creation Time specifically
                'expected_prompt_keywords': ["wide-angle", "cathedral", "Gothic", "architecture"]
            },
            
            {
                'name': 'Unicode and Special Characters',
                'description': 'Content with international characters and symbols',
                'content_sequence': [
                    """
                    Création Time: 24 Aug 2025 01:37:01
                    The camera captures a serene café scene in Paris with people enjoying coffee ☕ and pastries 🥐 under evening lights.
                    """
                ],
                'expected_time': "24 Aug 2025 01:37:01",
                'expected_prompt_keywords': ["camera", "café", "Paris", "coffee"]
            }
        ]

    async def run_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of metadata extraction fixes"""
        
        logger.info("🔬 Starting Enhanced Metadata Extraction Validation")
        logger.info("=" * 60)
        
        results = {
            'total_scenarios': len(self.test_scenarios),
            'passed': 0,
            'failed': 0,
            'scenarios': [],
            'performance_metrics': {},
            'overall_success_rate': 0.0
        }
        
        start_time = time.time()
        
        for i, scenario in enumerate(self.test_scenarios, 1):
            logger.info(f"\n📋 Scenario {i}/{len(self.test_scenarios)}: {scenario['name']}")
            logger.info(f"   Description: {scenario['description']}")
            
            scenario_result = await self._test_scenario(scenario)
            results['scenarios'].append(scenario_result)
            
            if scenario_result['success']:
                results['passed'] += 1
                logger.info(f"   ✅ PASSED")
            else:
                results['failed'] += 1
                logger.error(f"   ❌ FAILED: {scenario_result['error']}")
            
            # Log extraction details
            if scenario_result.get('metadata'):
                logger.info(f"   ⏰ Extracted Time: {scenario_result['metadata'].get('creation_time', 'None')}")
                logger.info(f"   📝 Extracted Prompt: {scenario_result['metadata'].get('prompt', 'None')[:100]}...")
        
        total_time = time.time() - start_time
        results['performance_metrics'] = {
            'total_validation_time': total_time,
            'average_time_per_scenario': total_time / len(self.test_scenarios)
        }
        results['overall_success_rate'] = (results['passed'] / results['total_scenarios']) * 100
        
        logger.info("=" * 60)
        logger.info(f"🎯 Validation Results Summary:")
        logger.info(f"   Total Scenarios: {results['total_scenarios']}")
        logger.info(f"   Passed: {results['passed']}")
        logger.info(f"   Failed: {results['failed']}")
        logger.info(f"   Success Rate: {results['overall_success_rate']:.1f}%")
        logger.info(f"   Total Time: {total_time:.3f}s")
        
        return results
    
    async def _test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single validation scenario"""
        
        result = {
            'name': scenario['name'],
            'success': False,
            'metadata': None,
            'error': None,
            'extraction_time': 0.0,
            'strategies_used': []
        }
        
        try:
            # Create mock container for the scenario
            mock_container = self._create_mock_container(scenario['content_sequence'])
            
            # Test extraction with different content states
            start_time = time.time()
            
            for attempt, content in enumerate(scenario['content_sequence']):
                logger.debug(f"   Testing content state {attempt + 1}/{len(scenario['content_sequence'])}")
                
                metadata = await extract_container_metadata_enhanced(
                    mock_container,
                    content,
                    attempt,
                    self.config
                )
                
                if metadata:
                    result['metadata'] = metadata
                    result['extraction_time'] = time.time() - start_time
                    break
            
            # Validate results
            if result['metadata']:
                success = self._validate_extraction_result(
                    result['metadata'], 
                    scenario
                )
                result['success'] = success
                
                if not success:
                    result['error'] = "Validation failed - extracted metadata doesn't match expectations"
            else:
                result['error'] = "No metadata extracted from any content state"
                
        except Exception as e:
            result['error'] = f"Exception during extraction: {e}"
            logger.error(f"   Exception in scenario {scenario['name']}: {e}")
        
        return result
    
    def _create_mock_container(self, content_sequence: List[str]) -> AsyncMock:
        """Create mock container that simulates dynamic content loading"""
        
        mock_container = AsyncMock()
        
        call_count = 0
        def mock_text_content():
            nonlocal call_count
            # Return content based on call sequence
            content = content_sequence[min(call_count, len(content_sequence) - 1)]
            call_count += 1
            return content
        
        mock_container.text_content = AsyncMock(side_effect=mock_text_content)
        mock_container.wait_for = AsyncMock()  # Simulate successful wait
        mock_container.query_selector_all = AsyncMock(return_value=[])  # No DOM elements for simplicity
        mock_container.bounding_box = AsyncMock(return_value={'x': 0, 'y': 0, 'width': 100, 'height': 100})
        
        return mock_container
    
    def _validate_extraction_result(self, metadata: Dict[str, str], scenario: Dict[str, Any]) -> bool:
        """Validate extracted metadata against scenario expectations"""
        
        creation_time = metadata.get('creation_time')
        prompt = metadata.get('prompt', '')
        
        # Validate creation time
        if scenario.get('expected_time'):
            if not creation_time or scenario['expected_time'] not in creation_time:
                logger.debug(f"   Time validation failed: expected '{scenario['expected_time']}', got '{creation_time}'")
                return False
        else:
            # For fuzzy time extraction, just check that some valid time was found
            if not creation_time or not _validate_creation_time_format(creation_time):
                logger.debug(f"   Time validation failed: no valid time format found in '{creation_time}'")
                return False
        
        # Validate prompt keywords
        if scenario.get('expected_prompt_keywords'):
            prompt_lower = prompt.lower()
            missing_keywords = []
            
            for keyword in scenario['expected_prompt_keywords']:
                if keyword.lower() not in prompt_lower:
                    missing_keywords.append(keyword)
            
            if missing_keywords:
                logger.debug(f"   Prompt validation failed: missing keywords {missing_keywords} in '{prompt[:100]}...'")
                return False
        
        # Check that prompt is substantial
        if not prompt or len(prompt.strip()) < 10:
            logger.debug(f"   Prompt validation failed: prompt too short or empty: '{prompt}'")
            return False
        
        return True

    async def test_performance_scenarios(self) -> Dict[str, Any]:
        """Test performance with challenging scenarios"""
        
        logger.info("\n🚀 Testing Performance Scenarios")
        
        performance_tests = [
            {
                'name': 'Large Content Block',
                'content': "Filler text. " * 2000 + "\nCreation Time 24 Aug 2025 01:37:01\nCamera shows beautiful landscape.\n" + "More filler. " * 2000,
                'max_time': 3.0  # Should complete within 3 seconds
            },
            {
                'name': 'Multiple Retry Cycles',
                'content_sequence': ["", "", "", "Creation Time 24 Aug 2025 01:37:01\nFinal content here."],
                'max_time': 5.0  # Should complete within 5 seconds even with retries
            },
            {
                'name': 'Complex Nested Content',
                'content': '\n'.join([
                    "Layer 1 | Layer 2 | Layer 3",
                    "\t\tDeep nested content with Creation Time 24 Aug 2025 01:37:01",
                    "More nested: The camera captures intricate details of a mechanical watch with visible gears.",
                    "Even deeper nesting with more content..."
                ] * 100),
                'max_time': 2.0
            }
        ]
        
        results = []
        
        for test in performance_tests:
            logger.info(f"   Testing: {test['name']}")
            
            start_time = time.time()
            
            try:
                if 'content_sequence' in test:
                    mock_container = self._create_mock_container(test['content_sequence'])
                    metadata = await extract_container_metadata_enhanced(
                        mock_container, test['content_sequence'][0], 0, self.config
                    )
                else:
                    mock_container = self._create_mock_container([test['content']])
                    metadata = await extract_container_metadata_enhanced(
                        mock_container, test['content'], 0, self.config
                    )
                
                extraction_time = time.time() - start_time
                
                success = (
                    extraction_time <= test['max_time'] and 
                    metadata is not None and 
                    metadata.get('creation_time') is not None
                )
                
                results.append({
                    'name': test['name'],
                    'extraction_time': extraction_time,
                    'max_time': test['max_time'],
                    'success': success,
                    'metadata_found': metadata is not None
                })
                
                logger.info(f"     Time: {extraction_time:.3f}s / {test['max_time']}s - {'✅' if success else '❌'}")
                
            except Exception as e:
                results.append({
                    'name': test['name'],
                    'extraction_time': time.time() - start_time,
                    'max_time': test['max_time'],
                    'success': False,
                    'error': str(e)
                })
                logger.error(f"     Error: {e}")
        
        return results

    def generate_report(self, results: Dict[str, Any], performance_results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive validation report"""
        
        report = f"""
# Enhanced Metadata Extraction Validation Report

## Summary
- **Total Scenarios Tested**: {results['total_scenarios']}
- **Passed**: {results['passed']}
- **Failed**: {results['failed']}
- **Success Rate**: {results['overall_success_rate']:.1f}%
- **Total Validation Time**: {results['performance_metrics']['total_validation_time']:.3f}s
- **Average Time Per Scenario**: {results['performance_metrics']['average_time_per_scenario']:.3f}s

## Scenario Results

"""
        
        for scenario in results['scenarios']:
            status = "✅ PASSED" if scenario['success'] else "❌ FAILED"
            report += f"### {scenario['name']} - {status}\n"
            
            if scenario['success']:
                report += f"- **Extraction Time**: {scenario['extraction_time']:.3f}s\n"
                if scenario['metadata']:
                    report += f"- **Time Found**: {scenario['metadata'].get('creation_time', 'None')}\n"
                    report += f"- **Prompt Length**: {len(scenario['metadata'].get('prompt', ''))}\n"
            else:
                report += f"- **Error**: {scenario['error']}\n"
            
            report += "\n"
        
        # Performance results
        report += "## Performance Test Results\n\n"
        
        for perf_test in performance_results:
            status = "✅ PASSED" if perf_test['success'] else "❌ FAILED"
            report += f"### {perf_test['name']} - {status}\n"
            report += f"- **Time**: {perf_test['extraction_time']:.3f}s / {perf_test['max_time']}s\n"
            report += f"- **Metadata Found**: {perf_test.get('metadata_found', False)}\n"
            if 'error' in perf_test:
                report += f"- **Error**: {perf_test['error']}\n"
            report += "\n"
        
        # Recommendations
        report += "## Recommendations\n\n"
        
        if results['overall_success_rate'] >= 90:
            report += "✅ **Excellent**: Metadata extraction is working reliably across all scenarios.\n\n"
        elif results['overall_success_rate'] >= 75:
            report += "⚠️ **Good**: Metadata extraction works well but has some edge cases to address.\n\n"
        else:
            report += "❌ **Needs Improvement**: Significant issues found that require attention.\n\n"
        
        failed_scenarios = [s for s in results['scenarios'] if not s['success']]
        if failed_scenarios:
            report += "### Failed Scenarios to Address:\n"
            for scenario in failed_scenarios:
                report += f"- **{scenario['name']}**: {scenario['error']}\n"
            report += "\n"
        
        report += "### Key Improvements Implemented:\n"
        report += "- Multiple extraction strategies with comprehensive fallbacks\n"
        report += "- Enhanced error handling and timeout management\n"
        report += "- Dynamic content loading support with retry mechanisms\n"
        report += "- Performance optimization for large content blocks\n"
        report += "- Robust validation and format checking\n"
        report += "- Spatial analysis and DOM element inspection\n\n"
        
        return report


async def main():
    """Main validation execution"""
    
    logger.info("🔬 Enhanced Metadata Extraction Validation")
    logger.info("Testing robust fixes for 'Could not extract creation time from gallery' errors")
    
    validator = MetadataExtractionValidator()
    
    # Run main validation scenarios
    results = await validator.run_validation()
    
    # Run performance tests  
    performance_results = await validator.test_performance_scenarios()
    
    # Generate comprehensive report
    report = validator.generate_report(results, performance_results)
    
    # Save report
    report_path = Path(__file__).parent.parent / 'logs' / 'metadata_extraction_validation_report.md'
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"\n📊 Validation report saved to: {report_path}")
    
    # Print summary
    if results['overall_success_rate'] >= 90:
        logger.info("🎉 VALIDATION PASSED: Enhanced metadata extraction is working reliably!")
        return 0
    else:
        logger.error("⚠️ VALIDATION ISSUES: Some scenarios failed - review needed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)