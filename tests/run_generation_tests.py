#!/usr/bin/env python3.11
"""
Test runner for generation download system tests
Runs comprehensive test suite and provides coverage report
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def main():
    """Run generation download tests with various options"""
    
    parser = argparse.ArgumentParser(description='Run generation download tests')
    parser.add_argument('--fast', action='store_true', help='Run only fast tests (skip slow/performance tests)')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--performance', action='store_true', help='Run only performance tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--specific', type=str, help='Run specific test file or pattern')
    
    args = parser.parse_args()
    
    # Set up test directory
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    
    # Change to project root for running tests
    os.chdir(project_root)
    
    # Build pytest command
    pytest_cmd = ['python3.11', '-m', 'pytest']
    
    if args.specific:
        # Run specific test file or pattern
        pytest_cmd.append(args.specific)
    else:
        # Default test files for generation download system
        test_files = [
            'tests/test_exit_scan_return_strategy.py',
            'tests/test_skip_mode_comprehensive.py', 
            'tests/test_integration_workflow.py',
            'tests/test_edge_cases_and_performance.py'
        ]
        pytest_cmd.extend(test_files)
    
    # Add options based on arguments
    if args.verbose:
        pytest_cmd.append('-v')
    else:
        pytest_cmd.append('-q')
        
    if args.parallel:
        pytest_cmd.extend(['-n', 'auto'])  # Requires pytest-xdist
        
    if args.fast:
        pytest_cmd.extend(['-m', 'not slow and not performance'])
    elif args.integration:
        pytest_cmd.extend(['-m', 'integration'])
    elif args.performance:
        pytest_cmd.extend(['-m', 'performance'])
        pytest_cmd.append('--runslow')
    else:
        # Run all tests except slow ones by default
        pytest_cmd.extend(['-m', 'not slow'])
    
    # Add coverage if requested
    if args.coverage:
        pytest_cmd.extend([
            '--cov=src/utils/generation_download_manager',
            '--cov-report=html:tests/coverage_html',
            '--cov-report=term-missing'
        ])
    
    # Print command being run
    print("Running command:", ' '.join(pytest_cmd))
    print("=" * 80)
    
    # Run tests
    try:
        result = subprocess.run(pytest_cmd, check=False)
        
        if args.coverage:
            print("\n" + "=" * 80)
            print("Coverage report generated in: tests/coverage_html/index.html")
            
        return result.returncode
        
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)