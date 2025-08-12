#!/usr/bin/env python3
"""
Entry point for Automaton GUI interface
"""

import sys
from pathlib import Path
import tkinter as tk

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from interfaces.gui import AutomationGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationGUI(root)
    root.mainloop()