#!/usr/bin/env python3
"""
Generation Download Fixes Validation Suite

Comprehensive test runner that validates all generation download automation fixes.
This script runs all relevant tests and provides a detailed report on the status
of each fix implemented in swarm task #000006.

Usage:
    python3.11 tests/run_generation_fixes_validation.py
    python3.11 tests/run_generation_fixes_validation.py --quick  # Skip integration tests
    python3.11 tests/run_generation_fixes_validation.py --verbose  # Detailed output
"""

import asyncio
import argparse
import logging
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Setup comprehensive logging
log_dir = Path('/home/olereon/workspace/github.com/olereon/automaton/logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'generation_fixes_validation.log')
    ]
)
logger = logging.getLogger(__name__)


class FixValidationReport:
    """Generate comprehensive validation report for all fixes"""
    
    def __init__(self):
        self.fixes = {
            'fix_1_timing': {
                'name': 'Date extraction timing after thumbnail selection',
                'description': 'Ensures date extraction uses landmark strategy AFTER thumbnail selection',
                'status': 'pending',
                'tests': [],
                'critical': True
            },
            'fix_2_button_sequence': {
                'name': 'Download button sequence (SVG → watermark)',
                'description': 'Proper SVG icon click before watermark option selection',
                'status': 'pending', 
                'tests': [],
                'critical': True
            },
            'fix_3_thumbnail_clicking': {
                'name': 'Enhanced thumbnail clicking for multiple items',
                'description': 'Improved thumbnail selection logic for subsequent downloads',
                'status': 'pending',
                'tests': [],
                'critical': True
            },
            'fix_4_metadata_accuracy': {
                'name': 'File naming and metadata accuracy',
                'description': 'Enhanced metadata extraction and descriptive file naming',
                'status': 'pending',
                'tests': [],
                'critical': True
            },
            'fix_5_workflow_integration': {
                'name': 'Complete workflow integration',
                'description': 'End-to-end workflow with all fixes integrated',
                'status': 'pending',
                'tests': [],
                'critical': True
            }
        }
        self.test_results = {}
        self.start_time = time.time()
    
    def add_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Add test result to the report"""
        self.test_results[test_name] = {
            'passed': passed,
            'details': details,
            'timestamp': time.time()
        }
        
        # Map tests to fixes
        if 'timing' in test_name.lower() or 'sequence' in test_name.lower():
            self.fixes['fix_1_timing']['tests'].append(test_name)
        if 'button' in test_name.lower() or 'download' in test_name.lower() or 'svg' in test_name.lower():
            self.fixes['fix_2_button_sequence']['tests'].append(test_name)
        if 'thumbnail' in test_name.lower() or 'clicking' in test_name.lower():
            self.fixes['fix_3_thumbnail_clicking']['tests'].append(test_name)
        if 'metadata' in test_name.lower() or 'naming' in test_name.lower() or 'file' in test_name.lower():
            self.fixes['fix_4_metadata_accuracy']['tests'].append(test_name)
        if 'workflow' in test_name.lower() or 'integration' in test_name.lower() or 'complete' in test_name.lower():
            self.fixes['fix_5_workflow_integration']['tests'].append(test_name)
    
    def update_fix_status(self):
        """Update fix status based on test results"""
        for fix_key, fix_info in self.fixes.items():
            if not fix_info['tests']:
                fix_info['status'] = 'no_tests'
                continue
            
            all_passed = all(
                self.test_results.get(test_name, {}).get('passed', False) 
                for test_name in fix_info['tests']
            )
            
            if all_passed:
                fix_info['status'] = 'passed'
            else:
                fix_info['status'] = 'failed'
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        self.update_fix_status()
        duration = time.time() - self.start_time
        
        report = []
        report.append("=" * 80)
        report.append("GENERATION DOWNLOAD FIXES VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Duration: {duration:.2f} seconds")
        report.append("")
        
        # Summary
        total_fixes = len(self.fixes)
        passed_fixes = sum(1 for fix in self.fixes.values() if fix['status'] == 'passed')
        critical_fixes = sum(1 for fix in self.fixes.values() if fix['critical'])
        critical_passed = sum(1 for fix in self.fixes.values() if fix['critical'] and fix['status'] == 'passed')
        
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Fixes: {total_fixes}")
        report.append(f"Fixes Passed: {passed_fixes}")
        report.append(f"Critical Fixes: {critical_fixes}")
        report.append(f"Critical Passed: {critical_passed}")
        report.append(f"Overall Success Rate: {(passed_fixes/total_fixes*100):.1f}%")
        report.append("")
        
        # Detailed fix status
        report.append("DETAILED FIX STATUS")
        report.append("-" * 40)
        
        for fix_key, fix_info in self.fixes.items():
            status_icon = {
                'passed': '✅',
                'failed': '❌', 
                'pending': '⏳',
                'no_tests': '⚠️'
            }.get(fix_info['status'], '❓')
            
            critical_marker = " [CRITICAL]" if fix_info['critical'] else ""
            report.append(f"{status_icon} {fix_info['name']}{critical_marker}")
            report.append(f"   {fix_info['description']}")
            
            if fix_info['tests']:
                report.append(f"   Tests: {len(fix_info['tests'])}")
                for test_name in fix_info['tests']:
                    test_result = self.test_results.get(test_name, {})
                    test_icon = '✅' if test_result.get('passed', False) else '❌'
                    report.append(f"     {test_icon} {test_name}")
            else:
                report.append("   ⚠️  No tests found for this fix")
            report.append("")
        
        # Test execution details
        report.append("TEST EXECUTION DETAILS")
        report.append("-" * 40)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
        
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed Tests: {passed_tests}")
        report.append(f"Failed Tests: {total_tests - passed_tests}")
        report.append(f"Test Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        
        failed_critical = [fix for fix in self.fixes.values() 
                          if fix['critical'] and fix['status'] == 'failed']
        
        if failed_critical:
            report.append("🚨 CRITICAL ISSUES FOUND:")
            for fix in failed_critical:
                report.append(f"   • {fix['name']}: {fix['description']}")
            report.append("")
            report.append("   ACTION REQUIRED: Address critical fixes before deployment")
        else:
            report.append("✅ All critical fixes are working correctly")
        
        if passed_fixes == total_fixes:
            report.append("🎉 ALL FIXES VALIDATED SUCCESSFULLY!")
            report.append("   Ready for production deployment")
        else:
            report.append(f"⚠️  {total_fixes - passed_fixes} fixes need attention")
            report.append("   Review failed tests and fix issues before deployment")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


async def run_test_suite(test_module: str, timeout: int = 300) -> Tuple[bool, str]:
    """Run a test suite and return success status and output"""
    logger.info(f"Running {test_module}...")
    
    try:
        # Run the test module
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'pytest', test_module, '-v',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=Path(__file__).parent.parent
        )
        
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
            output = stdout.decode('utf-8')
            success = process.returncode == 0
            
            return success, output
            
        except asyncio.TimeoutError:
            process.kill()
            return False, f"Test suite {test_module} timed out after {timeout} seconds"
    
    except Exception as e:
        return False, f"Failed to run {test_module}: {str(e)}"


async def run_direct_test(test_script: Path) -> Tuple[bool, str]:
    """Run a test script directly"""
    logger.info(f"Running {test_script.name}...")
    
    try:
        # Use subprocess.run instead of asyncio.create_subprocess_exec
        # This avoids creating a nested event loop for async tests
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr
            
        success = result.returncode == 0
        
        return success, output
        
    except Exception as e:
        return False, f"Failed to run {test_script}: {str(e)}"


def parse_test_output(output: str, test_name: str) -> List[Tuple[str, bool, str]]:
    """Parse test output to extract individual test results"""
    results = []
    lines = output.split('\n')
    
    current_test = None
    current_status = None
    
    for line in lines:
        line = line.strip()
        
        # Look for test method names
        if '::' in line and ('PASSED' in line or 'FAILED' in line):
            parts = line.split('::')
            if len(parts) >= 2:
                method_name = parts[-1].split()[0]
                status = 'PASSED' in line
                results.append((f"{test_name}.{method_name}", status, line))
        
        # Look for test class results
        elif line.startswith('test_') and ('... ok' in line or '... FAIL' in line):
            test_method = line.split()[0]
            status = 'ok' in line
            results.append((f"{test_name}.{test_method}", status, line))
    
    return results


async def main():
    """Main validation runner"""
    parser = argparse.ArgumentParser(description='Validate generation download fixes')
    parser.add_argument('--quick', action='store_true', help='Skip integration tests')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Generation Download Fixes Validation")
    logger.info("=" * 60)
    
    # Initialize report
    report = FixValidationReport()
    
    # Define test suites to run
    test_suites = [
        {
            'name': 'Comprehensive Unit Tests',
            'path': 'tests/test_generation_download_fixes_comprehensive.py',
            'critical': True
        },
        {
            'name': 'Integration Tests',
            'path': 'tests/test_generation_demo_integration.py',
            'critical': True,
            'skip': args.quick
        },
        {
            'name': 'Existing Generation Tests',
            'path': 'tests/test_generation_downloads.py',
            'critical': False
        }
    ]
    
    # Run test suites
    for suite in test_suites:
        if suite.get('skip', False):
            logger.info(f"Skipping {suite['name']} (--quick mode)")
            continue
        
        test_path = Path(__file__).parent.parent / suite['path']
        
        if test_path.exists():
            success, output = await run_direct_test(test_path)
            
            # Parse results
            test_results = parse_test_output(output, suite['name'])
            
            for test_name, passed, details in test_results:
                report.add_test_result(test_name, passed, details)
            
            # Add overall suite result
            report.add_test_result(f"{suite['name']}_overall", success, 
                                 f"Exit code: {'0' if success else 'non-zero'}")
            
            if args.verbose:
                logger.debug(f"Output for {suite['name']}:\n{output}")
        else:
            logger.warning(f"Test file not found: {test_path}")
            report.add_test_result(f"{suite['name']}_missing", False, "Test file not found")
    
    # Additional validation checks
    logger.info("Running additional validation checks...")
    
    # Check configuration file
    config_path = Path(__file__).parent.parent / "examples" / "generation_download_config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Validate configuration has fixes
            has_landmark_config = False
            has_enhanced_naming = False
            
            for action in config_data.get('actions', []):
                if action.get('type') == 'start_generation_downloads':
                    value = action.get('value', {})
                    has_landmark_config = value.get('landmark_extraction_enabled', False)
                    has_enhanced_naming = value.get('use_descriptive_naming', False)
                    break
            
            report.add_test_result('config_landmark_extraction', has_landmark_config,
                                 'Landmark extraction enabled in config')
            report.add_test_result('config_enhanced_naming', has_enhanced_naming,
                                 'Enhanced naming enabled in config')
            
        except Exception as e:
            report.add_test_result('config_validation', False, f"Config validation failed: {e}")
    else:
        report.add_test_result('config_exists', False, 'Configuration file not found')
    
    # Check demo script
    demo_path = Path(__file__).parent.parent / "examples" / "generation_download_demo.py"
    demo_exists = demo_path.exists()
    report.add_test_result('demo_script_exists', demo_exists, 'Demo script exists')
    
    # Generate and display report
    final_report = report.generate_report()
    
    print(final_report)
    
    # Save report to file
    report_path = log_dir / 'generation_fixes_validation_report.txt'
    with open(report_path, 'w') as f:
        f.write(final_report)
    
    logger.info(f"Detailed report saved to: {report_path}")
    
    # Determine exit code
    all_critical_passed = all(
        fix['status'] == 'passed' 
        for fix in report.fixes.values() 
        if fix['critical']
    )
    
    if all_critical_passed:
        logger.info("✅ ALL CRITICAL FIXES VALIDATED - READY FOR DEPLOYMENT")
        return 0
    else:
        logger.error("❌ CRITICAL FIXES FAILED - DEPLOYMENT NOT RECOMMENDED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning("🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error in validation: {e}")
        sys.exit(1)