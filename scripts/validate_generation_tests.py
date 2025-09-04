#!/usr/bin/env python3.11
"""
Validation script for generation download test suite
Validates test coverage, algorithm compliance, and edge cases
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def check_test_files():
    """Check that all required test files exist"""
    test_dir = Path(__file__).parent.parent / 'tests'
    
    required_files = [
        'test_exit_scan_return_strategy.py',
        'test_skip_mode_comprehensive.py', 
        'test_integration_workflow.py',
        'test_edge_cases_and_performance.py',
        'conftest.py',
        'run_generation_tests.py'
    ]
    
    print("🔍 Checking test files...")
    missing_files = []
    
    for file in required_files:
        file_path = test_dir / file
        if file_path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            missing_files.append(file)
            
    return len(missing_files) == 0

def check_algorithm_coverage():
    """Check that all algorithm steps are covered by tests"""
    
    print("\n🎯 Checking algorithm coverage...")
    
    required_test_patterns = [
        # Exit-Scan-Return Strategy Algorithm Steps
        "test_algorithm_step_11_exit_gallery",
        "test_algorithm_step_12_checkpoint_data", 
        "test_algorithm_step_13_sequential_scan",
        "test_algorithm_step_14_boundary_detection",
        "test_algorithm_step_15_click_boundary_container",
        
        # Duplicate Detection
        "test_duplicate_detection_exact_match",
        "test_duplicate_detection_no_match",
        "test_duplicate_detection_partial_prompt_match",
        
        # SKIP Mode Behavior
        "test_skip_mode_continues_after_duplicate",
        "test_finish_mode_stops_at_duplicate",
        
        # Edge Cases
        "test_empty_gallery_handling",
        "test_malformed_metadata_handling",
        "test_network_timeout_handling",
        
        # Performance
        "test_large_log_file_loading_performance",
        "test_concurrent_operations_performance",
        "test_exit_scan_return_scaling"
    ]
    
    test_dir = Path(__file__).parent.parent / 'tests'
    found_patterns = []
    
    for test_file in test_dir.glob('test_*.py'):
        with open(test_file, 'r') as f:
            content = f.read()
            
        for pattern in required_test_patterns:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"  ✅ {pattern}")
                
    missing_patterns = set(required_test_patterns) - set(found_patterns)
    
    for pattern in missing_patterns:
        print(f"  ❌ {pattern} - MISSING")
        
    coverage_percent = (len(found_patterns) / len(required_test_patterns)) * 100
    print(f"\n  📊 Algorithm Coverage: {coverage_percent:.1f}% ({len(found_patterns)}/{len(required_test_patterns)})")
    
    return len(missing_patterns) == 0

def run_basic_test_validation():
    """Run basic test validation to ensure tests can execute"""
    
    print("\n🧪 Running basic test validation...")
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Run syntax check on test files
    test_files = [
        'tests/test_exit_scan_return_strategy.py',
        'tests/test_skip_mode_comprehensive.py',
        'tests/test_integration_workflow.py', 
        'tests/test_edge_cases_and_performance.py'
    ]
    
    syntax_errors = []
    
    for test_file in test_files:
        try:
            result = subprocess.run(
                ['python3.11', '-m', 'py_compile', test_file], 
                capture_output=True, 
                text=True,
                check=True
            )
            print(f"  ✅ {test_file} - Syntax OK")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ {test_file} - Syntax Error")
            syntax_errors.append((test_file, e.stderr))
            
    if syntax_errors:
        print("\n❌ Syntax Errors Found:")
        for file, error in syntax_errors:
            print(f"  {file}: {error}")
            
    return len(syntax_errors) == 0

def check_test_documentation():
    """Check that tests are properly documented"""
    
    print("\n📝 Checking test documentation...")
    
    test_dir = Path(__file__).parent.parent / 'tests'
    documentation_issues = []
    
    for test_file in test_dir.glob('test_*.py'):
        if test_file.name == 'conftest.py':
            continue
            
        with open(test_file, 'r') as f:
            content = f.read()
            
        # Check for docstrings
        if '"""' not in content or 'test suite for' not in content.lower():
            documentation_issues.append(f"{test_file.name} - Missing module docstring")
            
        # Check for test method documentation
        lines = content.split('\n')
        in_test_method = False
        for i, line in enumerate(lines):
            if line.strip().startswith('def test_'):
                in_test_method = True
                method_name = line.strip().split('(')[0].replace('def ', '')
                
                # Look for docstring in next few lines
                has_docstring = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    if '"""' in lines[j]:
                        has_docstring = True
                        break
                        
                if not has_docstring:
                    documentation_issues.append(f"{test_file.name} - {method_name} missing docstring")
                    
    for issue in documentation_issues[:10]:  # Limit output
        print(f"  ⚠️ {issue}")
        
    if len(documentation_issues) > 10:
        print(f"  ... and {len(documentation_issues) - 10} more documentation issues")
        
    if not documentation_issues:
        print("  ✅ All tests are properly documented")
        
    return len(documentation_issues) == 0

def generate_test_report():
    """Generate comprehensive test validation report"""
    
    print("\n📋 Generating Test Validation Report...")
    
    report = {
        'validation_date': datetime.now().isoformat(),
        'test_suite': 'Generation Download System',
        'validation_results': {}
    }
    
    # Run all validation checks
    report['validation_results']['files_exist'] = check_test_files()
    report['validation_results']['algorithm_coverage'] = check_algorithm_coverage()
    report['validation_results']['syntax_valid'] = run_basic_test_validation()
    report['validation_results']['documentation_complete'] = check_test_documentation()
    
    # Calculate overall score
    passed_checks = sum(1 for result in report['validation_results'].values() if result)
    total_checks = len(report['validation_results'])
    overall_score = (passed_checks / total_checks) * 100
    
    report['overall_score'] = overall_score
    report['status'] = 'PASS' if overall_score >= 80 else 'FAIL'
    
    # Save report
    report_path = Path(__file__).parent.parent / 'tests' / 'validation_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"\n📊 Validation Report Summary:")
    print(f"  Overall Score: {overall_score:.1f}%")
    print(f"  Status: {report['status']}")
    print(f"  Passed Checks: {passed_checks}/{total_checks}")
    print(f"  Report saved: {report_path}")
    
    return report['status'] == 'PASS'

def main():
    """Main validation function"""
    
    print("🔍 Generation Download Test Suite Validation")
    print("=" * 60)
    
    success = generate_test_report()
    
    print("\n" + "=" * 60)
    
    if success:
        print("✅ Test suite validation PASSED")
        print("\nRecommended next steps:")
        print("  1. Run fast tests: python3.11 tests/run_generation_tests.py --fast")
        print("  2. Run integration tests: python3.11 tests/run_generation_tests.py --integration")
        print("  3. Run performance tests: python3.11 tests/run_generation_tests.py --performance")
        print("  4. Generate coverage: python3.11 tests/run_generation_tests.py --coverage")
        return 0
    else:
        print("❌ Test suite validation FAILED")
        print("\nPlease fix the issues above before running tests")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)