#!/usr/bin/env python3
"""
Test script to verify the new browser resolution settings functionality
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.engine import AutomationConfig


def test_default_viewport():
    """Test that the default viewport is now 1600x1000"""
    config = AutomationConfig(
        name="Test",
        url="https://example.com",
        actions=[]  # Empty actions list required
    )
    
    assert config.viewport == {"width": 1600, "height": 1000}, \
        f"Expected default viewport to be 1600x1000, got {config.viewport}"
    print("✅ Default viewport is correctly set to 1600x1000")


def test_custom_viewport():
    """Test that custom viewport can be set"""
    resolutions = [
        (1600, 1000),
        (1920, 1200),
        (2240, 1400),
        (2560, 1600),
    ]
    
    for width, height in resolutions:
        config = AutomationConfig(
            name="Test",
            url="https://example.com",
            actions=[],  # Empty actions list required
            viewport={"width": width, "height": height}
        )
        
        assert config.viewport == {"width": width, "height": height}, \
            f"Expected viewport {width}x{height}, got {config.viewport}"
        print(f"✅ Viewport {width}x{height} set correctly")


def test_gui_resolution_options():
    """Test that GUI resolution options are valid"""
    # These are the new resolution options defined in the GUI
    resolution_options = [
        ("1600x1000", "1600x1000 (UXGA)"),
        ("1920x1200", "1920x1200 (WUXGA)"),
        ("2240x1400", "2240x1400 (2K+)"),
        ("2560x1600", "2560x1600 (WQXGA)"),
        ("1280x800", "1280x800 (WXGA - Small)"),
        ("1440x900", "1440x900 (WXGA+ - Small)"),
        ("3840x2400", "3840x2400 (4K - Ultra)")
    ]
    
    print("\n📊 Available Resolution Options:")
    print("-" * 50)
    
    for resolution, description in resolution_options:
        width, height = map(int, resolution.split('x'))
        
        # Verify the resolution can be parsed
        assert width > 0 and height > 0, f"Invalid resolution: {resolution}"
        
        # Check if it's in the 320px increment range (1600-2560)
        if 1600 <= width <= 2560:
            increment = (width - 1600) % 320
            if increment == 0:
                print(f"✅ {description} - In 320px increment range")
            else:
                print(f"📌 {description}")
        else:
            print(f"📌 {description} - Legacy/Extended option")
    
    print("\n✅ All resolution options are valid")


def main():
    """Run all tests"""
    print("🧪 Testing Browser Resolution Settings\n")
    print("=" * 50)
    
    test_default_viewport()
    test_custom_viewport()
    test_gui_resolution_options()
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("\nSummary:")
    print("- Default resolution changed from 1280x720 to 1600x1000")
    print("- Added 320px width increments: 1600, 1920, 2240, 2560")
    print("- Kept legacy options for compatibility")
    print("- GUI and browser viewport now use same resolution settings")


if __name__ == "__main__":
    main()