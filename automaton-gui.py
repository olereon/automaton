#!/usr/bin/env python3
"""
Entry point for Automaton GUI interface
"""

import sys
from pathlib import Path

# Check for tkinter availability
try:
    import tkinter as tk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Error: tkinter is not available.")
    print("To fix this issue on Ubuntu/Debian/WSL:")
    print("  sudo apt update")
    print("  sudo apt install python3-tk")
    print("For other distributions, install the appropriate tkinter package.")
    sys.exit(1)

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from interfaces.gui import AutomationGUI
except ImportError as e:
    print(f"Error importing GUI interface: {e}")
    print("Make sure the src/interfaces/gui.py file exists and is properly configured.")
    sys.exit(1)

if __name__ == "__main__":
    if TKINTER_AVAILABLE:
        root = tk.Tk()
        app = AutomationGUI(root)
        root.mainloop()
    else:
        print("GUI interface cannot be started due to missing tkinter module.")