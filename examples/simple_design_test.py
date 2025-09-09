#!/usr/bin/env python3.11
"""
Simple Design System Test

Basic test to verify design system components work correctly.
"""

import sys
import os
import tkinter as tk

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from interfaces.design_system import ThemeMode, ComponentSize
from interfaces.modern_components import (
    ModernButton, ModernEntry, ModernFrame, ModernLabel
)

def test_basic_components():
    """Test basic components"""
    
    root = tk.Tk()
    root.title("Design System Test")
    root.geometry("400x300")
    
    # Create main frame
    main_frame = ModernFrame(root, variant='primary', theme_mode=ThemeMode.DARK)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Test label
    title = ModernLabel(
        main_frame,
        text="Design System Test",
        variant='heading1',
        weight='bold',
        theme_mode=ThemeMode.DARK
    )
    title.pack(pady=10)
    
    # Test button
    test_btn = ModernButton(
        main_frame,
        text="Test Button",
        variant='primary',
        size=ComponentSize.MEDIUM,
        theme_mode=ThemeMode.DARK,
        command=lambda: print("Button clicked!")
    )
    test_btn.pack(pady=10)
    
    # Test entry
    test_entry = ModernEntry(
        main_frame,
        placeholder="Enter test text...",
        theme_mode=ThemeMode.DARK
    )
    test_entry.pack(pady=10)
    
    # Test different button variants
    button_frame = tk.Frame(main_frame, bg=main_frame['bg'])
    button_frame.pack(pady=20)
    
    variants = ['secondary', 'outline', 'danger']
    for i, variant in enumerate(variants):
        ModernButton(
            button_frame,
            text=variant.title(),
            variant=variant,
            theme_mode=ThemeMode.DARK,
            command=lambda v=variant: print(f"{v} clicked!")
        ).pack(side=tk.LEFT, padx=5)
    
    root.mainloop()

if __name__ == "__main__":
    test_basic_components()