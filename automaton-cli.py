#!/usr/bin/env python3
"""
Entry point for Automaton CLI interface
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from interfaces.cli import main

if __name__ == "__main__":
    main()