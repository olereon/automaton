#!/usr/bin/env python3
"""
GUI Tabs Test Runner
Automated test runner for all new GUI tab functionality tests.

This runner orchestrates the complete test suite:
- Comprehensive functionality tests
- Performance benchmarks  
- Integration scenarios
- Error handling validation
- GUI responsiveness tests

Usage:
    python3.11 tests/test_gui_tabs_runner.py
    python3.11 tests/test_gui_tabs_runner.py --performance
    python3.11 tests/test_gui_tabs_runner.py --integration
    python3.11 tests/test_gui_tabs_runner.py --all
"""

import sys
import os
import asyncio
import argparse
import time
from pathlib import Path
import json

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

class GUITabsTestRunner:
    """Orchestrates all GUI tabs testing"""
    
    def __init__(self):
        self.test_results = {
            'comprehensive': None,
            'performance': None,
            'integration': None,
            'overall_success': False,
            'start_time': None,
            'end_time': None,
            'duration': None
        }
    
    async def run_comprehensive_tests(self):
        """Run comprehensive functionality tests"""
        print("📋 Running Comprehensive Functionality Tests...")
        print("=" * 50)
        
        try:
            # Import and run comprehensive tests
            from test_new_gui_tabs_comprehensive import run_comprehensive_test_suite
            
            start_time = time.time()
            success = run_comprehensive_test_suite()
            duration = time.time() - start_time
            
            self.test_results['comprehensive'] = {
                'success': success,
                'duration': duration,
                'test_type': 'comprehensive'
            }
            
            print(f"📊 Comprehensive tests completed in {duration:.2f}s")
            return success
            
        except Exception as e:
            print(f"❌ Comprehensive tests failed: {str(e)}")
            self.test_results['comprehensive'] = {
                'success': False,
                'error': str(e),
                'test_type': 'comprehensive'
            }
            return False
    
    async def run_performance_benchmarks(self):
        """Run performance benchmarks"""
        print("\n⚡ Running Performance Benchmarks...")
        print("=" * 50)
        
        try:
            # Import and run performance tests
            from test_gui_tabs_performance_benchmarks import run_performance_benchmarks
            
            start_time = time.time()
            success = await run_performance_benchmarks()
            duration = time.time() - start_time
            
            self.test_results['performance'] = {
                'success': success,
                'duration': duration,
                'test_type': 'performance'
            }
            
            print(f"📊 Performance benchmarks completed in {duration:.2f}s")
            return success
            
        except Exception as e:
            print(f"❌ Performance benchmarks failed: {str(e)}")
            self.test_results['performance'] = {
                'success': False,
                'error': str(e),
                'test_type': 'performance'
            }
            return False
    
    async def run_integration_scenarios(self):
        """Run integration scenario tests"""
        print("\n🔄 Running Integration Scenarios...")
        print("=" * 50)
        
        try:
            # Import and run integration tests
            from test_gui_tabs_integration_scenarios import run_integration_scenarios
            
            start_time = time.time()
            success = await run_integration_scenarios()
            duration = time.time() - start_time
            
            self.test_results['integration'] = {
                'success': success,
                'duration': duration,
                'test_type': 'integration'
            }
            
            print(f"📊 Integration scenarios completed in {duration:.2f}s")
            return success
            
        except Exception as e:
            print(f"❌ Integration scenarios failed: {str(e)}")
            self.test_results['integration'] = {
                'success': False,
                'error': str(e),
                'test_type': 'integration'
            }
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            'test_suite': 'GUI Tabs - Action Tab & Selector Tab',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_duration': self.test_results.get('duration', 0),
            'results': self.test_results,
            'summary': self._generate_summary()
        }
        
        # Write report to file
        report_path = Path(__file__).parent / "gui_tabs_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Test report written to: {report_path}")
        return report
    
    def _generate_summary(self):
        """Generate test summary"""
        summary = {
            'total_test_suites': 0,
            'passed_suites': 0,
            'failed_suites': 0,
            'overall_success_rate': 0,
            'recommendations': []
        }
        
        for test_type, result in self.test_results.items():
            if test_type in ['comprehensive', 'performance', 'integration'] and result:
                summary['total_test_suites'] += 1
                if result.get('success', False):
                    summary['passed_suites'] += 1
                else:
                    summary['failed_suites'] += 1
        
        if summary['total_test_suites'] > 0:
            summary['overall_success_rate'] = (summary['passed_suites'] / summary['total_test_suites']) * 100
        
        # Generate recommendations
        if summary['overall_success_rate'] >= 90:
            summary['recommendations'].append("✅ All test suites passed. Ready for implementation!")
        elif summary['overall_success_rate'] >= 75:
            summary['recommendations'].append("⚠️ Most tests passed. Review failed tests before implementation.")
        else:
            summary['recommendations'].append("❌ Multiple test failures. Significant issues need resolution.")
        
        # Performance-specific recommendations
        performance_result = self.test_results.get('performance')
        if performance_result and performance_result.get('success', False):
            summary['recommendations'].append("⚡ Performance benchmarks met. GUI should be responsive.")
        elif performance_result is not None:
            summary['recommendations'].append("🐌 Performance issues detected. Optimize before implementation.")
        
        # Integration-specific recommendations  
        integration_result = self.test_results.get('integration')
        if integration_result and integration_result.get('success', False):
            summary['recommendations'].append("🔄 Integration scenarios work. Cross-tab functionality validated.")
        elif integration_result is not None:
            summary['recommendations'].append("🔗 Integration issues found. Fix cross-tab communication.")
        
        return summary
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("🎯 GUI TABS TEST SUITE - FINAL SUMMARY")
        print("=" * 80)
        
        # Test suite results
        for test_type, result in self.test_results.items():
            if test_type in ['comprehensive', 'performance', 'integration'] and result:
                status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
                duration = result.get('duration', 0)
                print(f"{test_type.upper():15} {status:10} ({duration:.2f}s)")
        
        print("-" * 80)
        
        # Overall summary
        summary = self._generate_summary()
        print(f"📊 Test Suites: {summary['passed_suites']}/{summary['total_test_suites']} passed")
        print(f"📈 Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"⏱️ Total Duration: {self.test_results.get('duration', 0):.2f}s")
        
        print("\n🎯 RECOMMENDATIONS:")
        for recommendation in summary['recommendations']:
            print(f"   {recommendation}")
        
        # Implementation readiness
        if summary['overall_success_rate'] >= 80:
            print("\n🚀 IMPLEMENTATION READY: New GUI tabs can be implemented!")
            print("✨ Action Tab and Selector Tab functionality validated")
        else:
            print("\n⚠️ NOT READY: Address test failures before implementation")
            print("🔧 Review failed tests and resolve issues")
        
        return summary['overall_success_rate'] >= 80

async def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description='GUI Tabs Test Runner')
    parser.add_argument('--comprehensive', action='store_true', 
                       help='Run comprehensive functionality tests only')
    parser.add_argument('--performance', action='store_true',
                       help='Run performance benchmarks only') 
    parser.add_argument('--integration', action='store_true',
                       help='Run integration scenarios only')
    parser.add_argument('--all', action='store_true',
                       help='Run all test suites (default)')
    parser.add_argument('--report', type=str, 
                       help='Save detailed report to specified file')
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific suite is selected
    if not (args.comprehensive or args.performance or args.integration):
        args.all = True
    
    print("🚀 GUI TABS TEST RUNNER")
    print("=" * 40)
    print("Testing Action Tab & Selector Tab functionality")
    print("=" * 40)
    
    runner = GUITabsTestRunner()
    runner.test_results['start_time'] = time.time()
    
    overall_success = True
    
    try:
        # Run selected test suites
        if args.all or args.comprehensive:
            success = await runner.run_comprehensive_tests()
            overall_success = overall_success and success
        
        if args.all or args.performance:
            success = await runner.run_performance_benchmarks()
            overall_success = overall_success and success
        
        if args.all or args.integration:
            success = await runner.run_integration_scenarios()
            overall_success = overall_success and success
        
    except KeyboardInterrupt:
        print("\n🛑 Test execution interrupted by user")
        overall_success = False
    except Exception as e:
        print(f"\n❌ Test runner error: {str(e)}")
        overall_success = False
    
    finally:
        runner.test_results['end_time'] = time.time()
        runner.test_results['duration'] = (
            runner.test_results['end_time'] - runner.test_results['start_time']
        )
        runner.test_results['overall_success'] = overall_success
        
        # Generate and print final summary
        implementation_ready = runner.print_final_summary()
        
        # Generate test report
        report = runner.generate_test_report()
        
        # Save custom report if specified
        if args.report:
            custom_report_path = Path(args.report)
            with open(custom_report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Custom report saved to: {custom_report_path}")
        
        # Exit with appropriate code
        sys.exit(0 if implementation_ready else 1)

if __name__ == "__main__":
    asyncio.run(main())