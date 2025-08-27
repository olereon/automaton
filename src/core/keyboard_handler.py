#!/usr/bin/env python3
"""
Keyboard Input Handler for Control Commands
Provides cross-platform keyboard input handling for Ctrl+W and Ctrl+T
"""

import asyncio
import sys
import os
import threading
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class KeyboardHandler:
    """Cross-platform keyboard input handler for automation control"""
    
    def __init__(self):
        self.is_active = False
        self.control_callback: Optional[Callable] = None
        self.input_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
    def set_control_callback(self, callback: Callable[[str], None]):
        """Set callback for control commands
        
        Args:
            callback: Function that takes control command ('pause', 'resume', 'stop')
        """
        self.control_callback = callback
    
    def start_monitoring(self):
        """Start keyboard monitoring in background thread"""
        if self.is_active:
            return
        
        self.is_active = True
        self.stop_event.clear()
        
        # Start input monitoring in separate thread
        self.input_thread = threading.Thread(
            target=self._monitor_keyboard, 
            daemon=True,
            name="KeyboardHandler"
        )
        self.input_thread.start()
        logger.info("🎮 Keyboard monitoring started - Ctrl+W: Pause/Resume, Ctrl+T: Stop")
    
    def stop_monitoring(self):
        """Stop keyboard monitoring"""
        if not self.is_active:
            return
        
        self.is_active = False
        self.stop_event.set()
        
        if self.input_thread and self.input_thread.is_alive():
            # Give thread time to finish
            self.input_thread.join(timeout=1.0)
        
        logger.info("🛑 Keyboard monitoring stopped")
    
    def _monitor_keyboard(self):
        """Monitor keyboard input in background thread"""
        try:
            if os.name == 'nt':  # Windows
                self._monitor_windows()
            else:  # Unix/Linux/macOS
                self._monitor_unix()
        except Exception as e:
            logger.error(f"Keyboard monitoring error: {e}")
    
    def _monitor_windows(self):
        """Windows keyboard monitoring using msvcrt"""
        try:
            import msvcrt
            
            while self.is_active and not self.stop_event.is_set():
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\x17':  # Ctrl+W
                        self._handle_control_command('toggle_pause')
                    elif key == b'\x14':  # Ctrl+T
                        self._handle_control_command('stop')
                
                # Small delay to prevent high CPU usage
                self.stop_event.wait(0.1)
                
        except ImportError:
            logger.warning("msvcrt not available - keyboard monitoring disabled on Windows")
        except Exception as e:
            logger.error(f"Windows keyboard monitoring error: {e}")
    
    def _monitor_unix(self):
        """Unix/Linux keyboard monitoring using termios"""
        try:
            import termios
            import tty
            import select
            
            # Save original terminal settings
            old_settings = termios.tcgetattr(sys.stdin)
            
            try:
                # Set terminal to raw mode for character-by-character input
                tty.setraw(sys.stdin.fileno())
                
                while self.is_active and not self.stop_event.is_set():
                    # Check if input is available (non-blocking)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        char = sys.stdin.read(1)
                        
                        # Check for Ctrl+W (ASCII 23) and Ctrl+T (ASCII 20)
                        if ord(char) == 23:  # Ctrl+W
                            self._handle_control_command('toggle_pause')
                        elif ord(char) == 20:  # Ctrl+T
                            self._handle_control_command('stop')
                        elif ord(char) == 3:  # Ctrl+C - still handle for compatibility
                            self._handle_control_command('toggle_pause')
                        elif ord(char) == 26:  # Ctrl+Z - treat as stop
                            self._handle_control_command('stop')
                    
                    # Small delay
                    self.stop_event.wait(0.1)
                    
            finally:
                # Restore original terminal settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
        except ImportError:
            logger.warning("termios not available - using fallback input method")
            self._monitor_fallback()
        except Exception as e:
            logger.error(f"Unix keyboard monitoring error: {e}")
    
    def _monitor_fallback(self):
        """Fallback monitoring using input() with instructions"""
        print("\n" + "="*60)
        print("📋 KEYBOARD CONTROLS:")
        print("  • Type 'p' + Enter: Pause/Resume")
        print("  • Type 't' + Enter: Stop")
        print("  • Type 'q' + Enter: Quit")
        print("  • Type 's' + Enter: Status")
        print("="*60)
        
        while self.is_active and not self.stop_event.is_set():
            try:
                # Use input with timeout simulation
                print("\n> ", end="", flush=True)
                
                # Simple input reading
                try:
                    user_input = input().strip().lower()
                    
                    if user_input == 'p':
                        self._handle_control_command('toggle_pause')
                    elif user_input == 't' or user_input == 'q':
                        self._handle_control_command('stop')
                    elif user_input == 's':
                        self._handle_control_command('status')
                    elif user_input == 'help':
                        print("📋 Commands: p=pause/resume, t=stop, q=quit, s=status")
                        
                except EOFError:
                    # Handle Ctrl+D
                    break
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    self._handle_control_command('toggle_pause')
                    
            except Exception as e:
                logger.error(f"Fallback input error: {e}")
                break
    
    def _handle_control_command(self, command: str):
        """Handle control command and notify callback"""
        if self.control_callback:
            try:
                self.control_callback(command)
            except Exception as e:
                logger.error(f"Control callback error: {e}")
        else:
            logger.warning(f"No control callback set for command: {command}")


class SimpleKeyboardHandler:
    """Simplified keyboard handler for environments where advanced monitoring isn't available"""
    
    def __init__(self):
        self.control_callback: Optional[Callable] = None
        self.is_active = False
        
    def set_control_callback(self, callback: Callable[[str], None]):
        """Set callback for control commands"""
        self.control_callback = callback
    
    def start_monitoring(self):
        """Start simple keyboard monitoring"""
        self.is_active = True
        print("\n📋 SIMPLE CONTROLS:")
        print("  • Press Ctrl+C: Pause/Resume")
        print("  • Send SIGTERM: Stop")
        print("  • For advanced controls, use the GUI interface")
    
    def stop_monitoring(self):
        """Stop keyboard monitoring"""
        self.is_active = False
    
    def show_instructions(self):
        """Show control instructions"""
        if self.is_active:
            print("\n🎮 Active Controls:")
            print("  • Ctrl+C: Pause/Resume toggle")
            print("  • SIGTERM: Graceful stop")


# Factory function to create appropriate handler
def create_keyboard_handler(advanced: bool = True) -> KeyboardHandler:
    """Create appropriate keyboard handler based on environment
    
    Args:
        advanced: If True, try to create advanced handler with Ctrl+W/Ctrl+T
                 If False or advanced fails, create simple handler
    
    Returns:
        KeyboardHandler instance
    """
    if advanced:
        try:
            # Test if we can import required modules
            if os.name == 'nt':
                import msvcrt
            else:
                import termios
                import tty
                import select
            
            return KeyboardHandler()
            
        except ImportError:
            logger.info("Advanced keyboard monitoring not available, using simple handler")
            return SimpleKeyboardHandler()
    else:
        return SimpleKeyboardHandler()


if __name__ == "__main__":
    # Test the keyboard handler
    def test_callback(command: str):
        print(f"📨 Received command: {command}")
        if command == 'stop':
            handler.stop_monitoring()
    
    handler = create_keyboard_handler(advanced=True)
    handler.set_control_callback(test_callback)
    
    print("🧪 Testing keyboard handler...")
    handler.start_monitoring()
    
    try:
        # Keep main thread alive
        import time
        while handler.is_active:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        handler.stop_monitoring()
        print("✅ Test completed")