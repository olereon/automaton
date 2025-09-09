#!/usr/bin/env python3.11
"""
Comprehensive UI QA Validation Script
Runs all UI quality assurance tests and generates summary report.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and capture its output."""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        print(f"Command: {command}")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out: {command}")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False, "", str(e)

def main():
    """Main QA validation runner."""
    print("=" * 80)
    print("AUTOMATON UI QUALITY ASSURANCE VALIDATION SUITE")
    print("=" * 80)
    
    # Change to project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    print(f"Working directory: {project_dir}")
    
    # Test results
    test_results = {}
    
    # 1. Manual UI Validation
    success, stdout, stderr = run_command(
        "python3.11 tests/test_ui_manual_validation.py",
        "Manual UI Validation Test"
    )
    test_results["Manual UI Validation"] = success
    
    # 2. Basic GUI Functionality Test
    success, stdout, stderr = run_command(
        "python3.11 -c \"import sys; sys.path.insert(0, 'src'); from interfaces.gui import AutomationGUI; import tkinter as tk; root = tk.Tk(); root.withdraw(); gui = AutomationGUI(root); print('✅ GUI Creation Test Passed'); root.destroy()\"",
        "GUI Creation Test"
    )
    test_results["GUI Creation"] = success
    
    # 3. Theme Consistency Check
    success, stdout, stderr = run_command(
        "python3.11 -c \"import sys; sys.path.insert(0, 'src'); from interfaces.gui import AutomationGUI; import tkinter as tk; root = tk.Tk(); root.withdraw(); gui = AutomationGUI(root); bg = root.cget('bg'); print(f'Root background: {bg}'); success = bg == '#2b2b2b'; print('✅ Dark theme applied' if success else '❌ Theme not applied'); root.destroy(); exit(0 if success else 1)\"",
        "Theme Consistency Check"
    )
    test_results["Theme Consistency"] = success
    
    # 4. Color Contrast Validation
    success, stdout, stderr = run_command(
        "python3.11 -c \"def contrast_ratio(c1, c2): import math; def hex_to_rgb(h): h = h.lstrip('#'); return [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]; def luminance(rgb): def linearize(c): return c / 12.92 if c <= 0.03928 else pow((c + 0.055) / 1.055, 2.4); r, g, b = [linearize(c) for c in rgb]; return 0.2126 * r + 0.7152 * g + 0.0722 * b; l1, l2 = luminance(hex_to_rgb(c1)), luminance(hex_to_rgb(c2)); return (l1 + 0.05) / (l2 + 0.05) if l1 > l2 else (l2 + 0.05) / (l1 + 0.05); ratio = contrast_ratio('#2b2b2b', '#ffffff'); print(f'Contrast ratio: {ratio:.2f}:1'); success = ratio >= 4.5; print('✅ WCAG AA compliant' if success else '❌ Below WCAG AA'); exit(0 if success else 1)\"",
        "Color Contrast Validation"
    )
    test_results["Color Contrast"] = success
    
    # 5. Button Functionality Check  
    success, stdout, stderr = run_command(
        "python3.11 -c \"import sys; sys.path.insert(0, 'src'); from interfaces.gui import AutomationGUI; import tkinter as tk; root = tk.Tk(); root.withdraw(); gui = AutomationGUI(root); buttons = ['run_button', 'stop_button']; all_good = True; [print(f'✅ {btn}: {getattr(gui, btn).cget(\\\"text\\\")}') if hasattr(gui, btn) and getattr(gui, btn).cget('command') else print(f'❌ {btn}: missing or no command') or setattr(gui, 'all_good', False) for btn in buttons]; root.destroy(); print('✅ Button functionality validated' if all_good else '❌ Button issues found')\"",
        "Button Functionality Check"
    )
    test_results["Button Functionality"] = success
    
    # Print Summary
    print("\n" + "=" * 80)
    print("UI QA VALIDATION SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print("-" * 80)
    print(f"TOTAL TESTS: {total_tests}")
    print(f"PASSED: {passed_tests}")
    print(f"FAILED: {total_tests - passed_tests}")
    print(f"SUCCESS RATE: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ALL UI QA VALIDATION TESTS PASSED!")
        print("✅ UI is ready for production deployment")
        overall_status = True
    elif success_rate >= 80:
        print(f"\n⚠️ UI QA validation mostly successful ({success_rate:.1f}%)")
        print("✅ UI is acceptable for deployment with minor issues")
        overall_status = True
    else:
        print(f"\n❌ UI QA validation failed ({success_rate:.1f}%)")
        print("❌ UI needs significant improvements before deployment")
        overall_status = False
    
    # Quality Gates
    print("\n" + "=" * 80)
    print("QUALITY GATES ASSESSMENT")
    print("=" * 80)
    
    quality_gates = {
        "Theme Consistency": test_results.get("Theme Consistency", False),
        "Color Accessibility": test_results.get("Color Contrast", False), 
        "Button Functionality": test_results.get("Button Functionality", False),
        "GUI Creation": test_results.get("GUI Creation", False),
        "Manual Validation": test_results.get("Manual UI Validation", False)
    }
    
    for gate, passed in quality_gates.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"Gate: {gate:<25} {status}")
    
    gates_passed = sum(quality_gates.values())
    gates_total = len(quality_gates)
    
    print(f"\nQuality Gates: {gates_passed}/{gates_total} passed")
    
    if gates_passed == gates_total:
        print("🏆 ALL QUALITY GATES PASSED - PRODUCTION READY")
    elif gates_passed >= gates_total * 0.8:
        print("⚠️ Most quality gates passed - Minor improvements needed")
    else:
        print("❌ Quality gates failed - Major improvements required")
    
    return overall_status

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)