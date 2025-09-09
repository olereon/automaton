#!/usr/bin/env python3.11
"""
Simple Color Validation Test
Tests color contrast without GUI instantiation.
"""

def calculate_contrast_ratio(color1_hex, color2_hex):
    """Calculate WCAG contrast ratio between two hex colors."""
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    
    def get_relative_luminance(rgb):
        def linearize(c):
            return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4)
        
        r, g, b = [linearize(c) for c in rgb]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    rgb1 = hex_to_rgb(color1_hex)
    rgb2 = hex_to_rgb(color2_hex)
    
    l1 = get_relative_luminance(rgb1)
    l2 = get_relative_luminance(rgb2)
    
    # Ensure l1 is the lighter color
    if l2 > l1:
        l1, l2 = l2, l1
        
    return (l1 + 0.05) / (l2 + 0.05)

def test_color_accessibility():
    """Test all color combinations for WCAG compliance."""
    print("=" * 60)
    print("AUTOMATON COLOR ACCESSIBILITY VALIDATION")
    print("=" * 60)
    
    # Define color combinations used in the dark theme
    color_combinations = [
        ('#2b2b2b', '#ffffff', 'Background/Text'),      # Main bg/text
        ('#404040', '#ffffff', 'Button/Text'),          # Button bg/text  
        ('#404040', '#ffffff', 'Entry/Text'),           # Entry bg/text
        ('#2b2b2b', '#cccccc', 'Background/Secondary'), # Secondary text
        ('#505050', '#ffffff', 'Hover/Text'),           # Hover states
    ]
    
    all_passed = True
    
    for bg_color, fg_color, description in color_combinations:
        ratio = calculate_contrast_ratio(bg_color, fg_color)
        
        # WCAG 2.1 AA requires 4.5:1 for normal text
        aa_compliant = ratio >= 4.5
        aaa_compliant = ratio >= 7.0
        
        status = "✅ PASSED" if aa_compliant else "❌ FAILED"
        aaa_status = "AAA ✓" if aaa_compliant else "AAA ✗"
        
        print(f"{description:<30} {ratio:>6.2f}:1 {status} ({aaa_status})")
        
        if not aa_compliant:
            all_passed = False
    
    print("-" * 60)
    
    if all_passed:
        print("🎉 ALL COLOR COMBINATIONS MEET WCAG 2.1 AA STANDARDS!")
        print("✅ Colors are accessible and production-ready")
    else:
        print("❌ Some color combinations fail WCAG 2.1 AA standards")
        print("⚠️ Color accessibility improvements needed")
    
    return all_passed

if __name__ == '__main__':
    import sys
    success = test_color_accessibility()
    sys.exit(0 if success else 1)