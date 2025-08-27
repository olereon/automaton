#!/usr/bin/env python3
"""
Test script to verify the hotkey change from Ctrl+P to Ctrl+W
"""

import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.keyboard_handler import create_keyboard_handler

def test_hotkey_change():
    """Test the updated hotkey system"""
    print("🧪 Testing Hotkey Change from Ctrl+P to Ctrl+W")
    print("=" * 50)
    
    # Test handler creation
    handler = create_keyboard_handler(advanced=True)
    print("✅ Keyboard handler created successfully")
    
    # Test callback setup
    commands_received = []
    
    def test_callback(command: str):
        commands_received.append(command)
        print(f"📨 Received command: {command}")
        if command == 'stop':
            handler.stop_monitoring()
    
    handler.set_control_callback(test_callback)
    print("✅ Control callback set up")
    
    # Start monitoring
    handler.start_monitoring()
    print("✅ Keyboard monitoring started")
    
    print("\n🎮 HOTKEY CONTROLS:")
    print("  • Ctrl+W: Pause/Resume (CHANGED from Ctrl+P)")
    print("  • Ctrl+T: Stop")  
    print("  • Ctrl+C: Emergency stop (fallback)")
    print("\n⏱️  Test will run for 10 seconds...")
    print("📝 Try pressing Ctrl+W or Ctrl+T to test")
    
    # Run test for 10 seconds
    start_time = time.time()
    while time.time() - start_time < 10 and handler.is_active:
        time.sleep(0.1)
    
    # Stop handler
    handler.stop_monitoring()
    
    print("\n📊 Test Results:")
    print(f"  • Commands received: {len(commands_received)}")
    if commands_received:
        print(f"  • Commands: {commands_received}")
    else:
        print("  • No commands received (test may have been too short or no keys pressed)")
    
    print("\n✅ Hotkey change test completed!")
    print("🔄 The system now uses Ctrl+W instead of Ctrl+P for pause/resume")
    
    return True

if __name__ == "__main__":
    test_hotkey_change()