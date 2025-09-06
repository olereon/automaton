#!/usr/bin/env python3
"""
Download Interception Test Runner

This script runs all download interception related tests and provides comprehensive reporting.

Usage:
    python3.11 tests/run_download_interception_tests.py
    python3.11 tests/run_download_interception_tests.py --verbose
    python3.11 tests/run_download_interception_tests.py --focus mock
    python3.11 tests/run_download_interception_tests.py --focus config
    python3.11 tests/run_download_interception_tests.py --focus integration
"""

import sys
import os
import unittest
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Import all download interception test modules
try:
    from test_download_interception_fixes import (
        TestDownloadFileDetection,
        TestGenerationDownloadConfigValidation,
        TestDownloadProcessingAndFilenaming,
        TestStatusTrackingAndCounts,
        TestErrorHandlingAndEdgeCases,
        TestRaceConditionsAndTiming,
        TestIntegrationDownloadFlow
    )
    from test_mock_download_scenarios import (
        TestMockDownloadScenarios,
        TestMockFileOperations,
        TestMockNetworkConditions
    )
    from test_configuration_validation_comprehensive import (
        TestGenerationDownloadConfigStructure,
        TestConfigurationValueValidation,
        TestConfigurationInstantiation,
        TestConfigurationSerialization,
        TestConfigurationErrorHandling
    )
    print("✅ All test modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import test modules: {e}")
    sys.exit(1)


class DownloadInterceptionTestRunner:
    """Comprehensive test runner for download interception functionality"""
    
    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.suite_results = {}
    
    def run_test_suite(self, suite_class, suite_name):
        """Run a single test suite and collect results"""
        print(f"\n{'='*60}")
        print(f"🧪 Running {suite_name}")
        print(f"   Test Suite: {suite_class.__name__}")
        print('='*60)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(suite_class)
        runner = unittest.TextTestRunner(verbosity=self.verbosity, stream=sys.stdout)
        result = runner.run(suite)
        
        # Collect statistics
        tests_run = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        
        self.total_tests += tests_run
        self.total_failures += failures
        self.total_errors += errors
        
        # Store results
        success_rate = ((tests_run - failures - errors) / tests_run * 100) if tests_run > 0 else 0
        self.suite_results[suite_name] = {
            'class': suite_class.__name__,
            'tests': tests_run,
            'failures': failures,
            'errors': errors,
            'success_rate': success_rate,
            'passed': result.wasSuccessful()
        }
        
        # Print summary
        if result.wasSuccessful():
            print(f"✅ {suite_name} - ALL TESTS PASSED ({tests_run} tests)")
        else:
            print(f"❌ {suite_name} - {failures} failures, {errors} errors ({tests_run} tests)")
        
        return result.wasSuccessful()
    
    def run_core_functionality_tests(self):
        """Run core download interception functionality tests"""
        print("\n" + "🎯 CORE FUNCTIONALITY TESTS".center(80, "="))
        
        core_suites = [
            (TestDownloadFileDetection, "File Detection"),
            (TestGenerationDownloadConfigValidation, "Config Validation"),
            (TestDownloadProcessingAndFilenaming, "File Processing"),
            (TestStatusTrackingAndCounts, "Status Tracking"),
            (TestErrorHandlingAndEdgeCases, "Error Handling"),
            (TestRaceConditionsAndTiming, "Race Conditions"),
            (TestIntegrationDownloadFlow, "Integration Flow")
        ]
        
        all_passed = True
        for suite_class, suite_name in core_suites:
            passed = self.run_test_suite(suite_class, suite_name)
            if not passed:
                all_passed = False
        
        return all_passed
    
    def run_mock_scenario_tests(self):
        """Run mock download scenario tests"""
        print("\n" + "🎭 MOCK SCENARIO TESTS".center(80, "="))
        
        mock_suites = [
            (TestMockDownloadScenarios, "Mock Downloads"),
            (TestMockFileOperations, "Mock File Operations"),
            (TestMockNetworkConditions, "Mock Network Conditions")
        ]
        
        all_passed = True
        for suite_class, suite_name in mock_suites:
            passed = self.run_test_suite(suite_class, suite_name)
            if not passed:
                all_passed = False
        
        return all_passed
    
    def run_configuration_tests(self):
        """Run comprehensive configuration tests"""
        print("\n" + "⚙️ CONFIGURATION TESTS".center(80, "="))
        
        config_suites = [
            (TestGenerationDownloadConfigStructure, "Config Structure"),
            (TestConfigurationValueValidation, "Value Validation"),
            (TestConfigurationInstantiation, "Instantiation"),
            (TestConfigurationSerialization, "Serialization"),
            (TestConfigurationErrorHandling, "Error Handling")
        ]
        
        all_passed = True
        for suite_class, suite_name in config_suites:
            passed = self.run_test_suite(suite_class, suite_name)
            if not passed:
                all_passed = False
        
        return all_passed
    
    def run_all_tests(self):
        """Run all download interception tests"""
        print("🚀 STARTING COMPREHENSIVE DOWNLOAD INTERCEPTION TESTS")
        print("="*80)
        
        # Run all test categories
        core_passed = self.run_core_functionality_tests()
        mock_passed = self.run_mock_scenario_tests()
        config_passed = self.run_configuration_tests()
        
        # Final summary
        self.print_final_summary(core_passed and mock_passed and config_passed)
        
        return self.total_failures == 0 and self.total_errors == 0
    
    def print_final_summary(self, all_passed):
        """Print comprehensive final test summary"""
        print("\n" + "📊 FINAL TEST SUMMARY".center(80, "="))
        
        print(f"📈 Total Statistics:")
        print(f"   • Tests Run: {self.total_tests}")
        print(f"   • Failures: {self.total_failures}")
        print(f"   • Errors: {self.total_errors}")
        
        if self.total_tests > 0:
            success_rate = ((self.total_tests - self.total_failures - self.total_errors) / self.total_tests) * 100
            print(f"   • Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Suite-by-Suite Results:")
        for suite_name, results in self.suite_results.items():
            status = "✅ PASS" if results['passed'] else "❌ FAIL"
            print(f"   • {suite_name}: {status} ({results['tests']} tests, {results['success_rate']:.1f}%)")
        
        print(f"\n{'='*80}")
        if all_passed:
            print("🎉 ALL DOWNLOAD INTERCEPTION TESTS PASSED!")
            print("✅ System ready for download file interception and processing")
        else:
            print("⚠️  SOME TESTS FAILED - Review failures above")
            print("❌ System may have issues with download interception")
        
        print("="*80)
        
        # Detailed recommendations
        if not all_passed:
            print("\n🔧 RECOMMENDED ACTIONS:")
            failed_suites = [name for name, result in self.suite_results.items() if not result['passed']]
            for suite in failed_suites:
                print(f"   • Fix issues in {suite} test suite")
            print("   • Re-run tests after fixes")
            print("   • Check system configuration and permissions")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Download Interception Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose test output')
    parser.add_argument('--focus', choices=['core', 'mock', 'config', 'all'], 
                       default='all', help='Focus on specific test category')
    
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    runner = DownloadInterceptionTestRunner(verbosity=verbosity)
    
    try:
        if args.focus == 'core':
            success = runner.run_core_functionality_tests()
        elif args.focus == 'mock':
            success = runner.run_mock_scenario_tests()
        elif args.focus == 'config':
            success = runner.run_configuration_tests()
        else:  # 'all'
            success = runner.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test runner error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()