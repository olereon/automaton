#!/usr/bin/env python3
"""
Helper script to run examples with proper module paths
"""

import sys
import os
import importlib.util
import argparse

# Setup Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

def run_example(example_name):
    """Run an example script"""
    example_path = os.path.join(current_dir, 'examples', example_name)
    
    if not os.path.exists(example_path):
        print(f"❌ Example not found: {example_name}")
        print("\nAvailable examples:")
        examples_dir = os.path.join(current_dir, 'examples')
        for file in os.listdir(examples_dir):
            if file.endswith('.py'):
                print(f"  - {file}")
        return
    
    # Load and execute the example
    spec = importlib.util.spec_from_file_location("example", example_path)
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"❌ Error running example: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Automaton examples")
    parser.add_argument("example", help="Name of the example file (e.g., generation_download_demo.py)")
    
    args = parser.parse_args()
    run_example(args.example)