#!/usr/bin/env python3
"""
Interactive Process Manager
Displays running processes and allows selective killing
"""

import subprocess
import sys
import os
import signal
from typing import List, Tuple, Optional
import re
from datetime import datetime

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.process_filters = [
            "python", "automaton", "chromium", "chrome", "playwright",
            "node", "npm", "npx", "generation", "download"
        ]
    
    def get_processes(self, filter_pattern: Optional[str] = None) -> List[Tuple[int, str, str]]:
        """Get list of running processes with optional filtering"""
        try:
            # Get process list
            cmd = "ps aux"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            processes = []
            for line in lines:
                if line:
                    parts = line.split(None, 10)  # Split into max 11 parts
                    if len(parts) >= 11:
                        pid = int(parts[1])
                        cpu = parts[2]
                        mem = parts[3]
                        start_time = parts[8]
                        time = parts[9]
                        command = parts[10]
                        
                        # Filter if pattern provided
                        if filter_pattern:
                            if not any(f in command.lower() for f in filter_pattern.lower().split()):
                                continue
                        
                        # Skip grep and this script itself
                        if 'grep' in command or 'process_manager.py' in command:
                            continue
                        
                        # Format display string
                        display = f"PID: {pid:8} | CPU: {cpu:5}% | MEM: {mem:5}% | {command[:100]}"
                        processes.append((pid, command, display))
            
            return processes
        except Exception as e:
            print(f"Error getting processes: {e}")
            return []
    
    def display_processes(self, processes: List[Tuple[int, str, str]]) -> None:
        """Display processes with numbering"""
        print("\n" + "="*120)
        print(f"{'No.':<5} {'Process Information':<115}")
        print("="*120)
        
        if not processes:
            print("No matching processes found.")
            return
        
        for i, (pid, cmd, display) in enumerate(processes, 1):
            # Highlight certain process types
            if any(keyword in cmd.lower() for keyword in ["automaton", "generation"]):
                print(f"\033[93m{i:3}.\033[0m  {display}")  # Yellow
            elif "chrome" in cmd.lower() or "chromium" in cmd.lower():
                print(f"\033[96m{i:3}.\033[0m  {display}")  # Cyan
            elif "python" in cmd.lower():
                print(f"\033[92m{i:3}.\033[0m  {display}")  # Green
            else:
                print(f"{i:3}.  {display}")
        
        print("="*120)
        print(f"Total processes: {len(processes)}")
    
    def kill_process(self, pid: int, force: bool = False) -> bool:
        """Kill a process by PID"""
        try:
            if force:
                os.kill(pid, signal.SIGKILL)  # Force kill
                print(f"✅ Force killed process {pid}")
            else:
                os.kill(pid, signal.SIGTERM)  # Gentle termination
                print(f"✅ Terminated process {pid}")
            return True
        except ProcessLookupError:
            print(f"⚠️  Process {pid} not found (may have already terminated)")
            return False
        except PermissionError:
            print(f"❌ Permission denied to kill process {pid}")
            return False
        except Exception as e:
            print(f"❌ Error killing process {pid}: {e}")
            return False
    
    def interactive_mode(self):
        """Run interactive process manager"""
        print("\n🔧 Interactive Process Manager")
        print("-" * 50)
        
        while True:
            # Display menu
            print("\n📋 Options:")
            print("  1. Show all processes")
            print("  2. Show filtered processes (python/automaton/chrome)")
            print("  3. Show processes by custom filter")
            print("  4. Kill process(es)")
            print("  5. Refresh")
            print("  6. Quick kill all automaton processes")
            print("  0. Exit")
            
            try:
                choice = input("\n👉 Enter choice: ").strip()
                
                if choice == '0':
                    print("👋 Exiting...")
                    break
                
                elif choice == '1':
                    self.processes = self.get_processes()
                    self.display_processes(self.processes)
                
                elif choice == '2':
                    filter_str = ' '.join(self.process_filters)
                    print(f"🔍 Filtering for: {filter_str}")
                    filtered = []
                    for pattern in self.process_filters:
                        filtered.extend(self.get_processes(pattern))
                    # Remove duplicates
                    seen = set()
                    self.processes = []
                    for p in filtered:
                        if p[0] not in seen:
                            seen.add(p[0])
                            self.processes.append(p)
                    self.display_processes(self.processes)
                
                elif choice == '3':
                    pattern = input("🔍 Enter filter pattern: ").strip()
                    if pattern:
                        self.processes = self.get_processes(pattern)
                        self.display_processes(self.processes)
                
                elif choice == '4':
                    if not self.processes:
                        print("⚠️  No processes loaded. Please show processes first.")
                        continue
                    
                    print("\n🎯 Kill Options:")
                    print("  - Enter number(s) separated by comma: 1,3,5")
                    print("  - Enter range: 1-5")
                    print("  - Enter 'all' to kill all displayed processes")
                    print("  - Enter '0' to cancel")
                    
                    selection = input("👉 Select processes to kill: ").strip()
                    
                    if selection == '0':
                        print("❌ Kill operation cancelled")
                        continue
                    
                    force = input("💪 Force kill? (y/n, default=n): ").strip().lower() == 'y'
                    
                    pids_to_kill = []
                    
                    if selection.lower() == 'all':
                        pids_to_kill = [p[0] for p in self.processes]
                    elif '-' in selection:
                        # Range
                        try:
                            start, end = map(int, selection.split('-'))
                            for i in range(start, min(end + 1, len(self.processes) + 1)):
                                pids_to_kill.append(self.processes[i-1][0])
                        except:
                            print("❌ Invalid range format")
                            continue
                    else:
                        # Individual numbers
                        try:
                            numbers = [int(x.strip()) for x in selection.split(',')]
                            for num in numbers:
                                if 1 <= num <= len(self.processes):
                                    pids_to_kill.append(self.processes[num-1][0])
                                else:
                                    print(f"⚠️  Number {num} out of range")
                        except:
                            print("❌ Invalid selection format")
                            continue
                    
                    if pids_to_kill:
                        confirm = input(f"⚠️  Kill {len(pids_to_kill)} process(es)? (y/n): ").strip().lower()
                        if confirm == 'y':
                            success = 0
                            for pid in pids_to_kill:
                                if self.kill_process(pid, force):
                                    success += 1
                            print(f"\n✨ Killed {success}/{len(pids_to_kill)} processes")
                        else:
                            print("❌ Operation cancelled")
                
                elif choice == '5':
                    print("🔄 Refreshing...")
                    continue
                
                elif choice == '6':
                    print("🎯 Quick killing all automaton processes...")
                    result = subprocess.run("pkill -f automaton", shell=True, capture_output=True)
                    if result.returncode == 0:
                        print("✅ Killed all automaton processes")
                    else:
                        print("⚠️  No automaton processes found or already terminated")
                
                else:
                    print("❌ Invalid choice")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    manager = ProcessManager()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("Process Manager - Interactive process viewer and killer")
            print("\nUsage:")
            print("  python3 process_manager.py          # Interactive mode")
            print("  python3 process_manager.py --list   # List all processes")
            print("  python3 process_manager.py --filter <pattern>  # Filter processes")
            print("  python3 process_manager.py --kill-automaton    # Kill all automaton processes")
            sys.exit(0)
        elif sys.argv[1] == '--list':
            processes = manager.get_processes()
            manager.display_processes(processes)
            sys.exit(0)
        elif sys.argv[1] == '--filter' and len(sys.argv) > 2:
            pattern = ' '.join(sys.argv[2:])
            processes = manager.get_processes(pattern)
            manager.display_processes(processes)
            sys.exit(0)
        elif sys.argv[1] == '--kill-automaton':
            subprocess.run("pkill -f automaton", shell=True)
            print("✅ Killed all automaton processes")
            sys.exit(0)
    
    # Run interactive mode
    try:
        manager.interactive_mode()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()