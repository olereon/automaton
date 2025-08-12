#!/usr/bin/env python3
"""
Quick setup script for Web Automation Tool
Handles dependency installation and initial configuration
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✓ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        return False

def main():
    print("=== Web Automation Tool Setup ===")
    print("This script will set up the automation tool environment\n")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("✗ Python 3.8 or higher is required")
        print(f"  Current version: {sys.version}")
        sys.exit(1)
    else:
        print(f"✓ Python version: {sys.version.split()[0]}")
    
    # Create virtual environment
    venv_path = Path("venv")
    if not venv_path.exists():
        if run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
            print("  Please activate the virtual environment:")
            if sys.platform == "win32":
                print("  Run: venv\\Scripts\\activate")
            else:
                print("  Run: source venv/bin/activate")
            print("  Then run this script again")
            sys.exit(0)
    else:
        print("✓ Virtual environment exists")
    
    # Check if we're in virtual environment
    if sys.prefix == sys.base_prefix:
        print("\n⚠ Virtual environment is not activated!")
        print("Please activate it first:")
        if sys.platform == "win32":
            print("  Run: venv\\Scripts\\activate")
        else:
            print("  Run: source venv/bin/activate")
        print("Then run this script again")
        sys.exit(1)
    
    # Upgrade pip
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if Path("requirements.txt").exists():
        run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                   "Installing dependencies")
    else:
        print("✗ requirements.txt not found")
        print("  Installing core dependencies manually...")
        run_command(f"{sys.executable} -m pip install playwright pyyaml", 
                   "Installing core packages")
    
    # Install Playwright browsers
    run_command("playwright install chromium", "Installing Chromium browser")
    
    # Create necessary directories
    directories = ["downloads", "configs", "logs"]
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir()
            print(f"✓ Created directory: {dir_name}/")
        else:
            print(f"✓ Directory exists: {dir_name}/")
    
    # Create example config if it doesn't exist
    example_config = Path("configs/example_automation.json")
    if not example_config.exists():
        example_content = """{
  "name": "Example Automation",
  "url": "https://example.com",
  "headless": false,
  "viewport": {"width": 1280, "height": 720},
  "actions": [
    {
      "type": "wait_for_element",
      "selector": "body",
      "timeout": 30000,
      "description": "Wait for page load"
    }
  ]
}"""
        example_config.write_text(example_content)
        print("✓ Created example configuration: configs/example_automation.json")
    
    # Test imports
    print("\nTesting imports...")
    try:
        import playwright
        print("✓ Playwright imported successfully")
        
        # Test if the main modules exist
        modules = ["web_automation.py", "cli_interface.py", "gui_interface.py"]
        missing = [m for m in modules if not Path(m).exists()]
        
        if missing:
            print(f"\n⚠ Missing required files: {', '.join(missing)}")
            print("  Make sure all automation tool files are in the current directory")
        else:
            print("✓ All required files present")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    print("\n=== Setup Complete! ===")
    print("\nTo get started:")
    print("1. GUI Mode: python gui_interface.py")
    print("2. CLI Mode: python cli_interface.py --help")
    print("3. Example: python cli_interface.py run -c configs/example_automation.json")
    
    # Optional: Create desktop shortcuts
    if sys.platform == "win32":
        create_shortcut = input("\nCreate desktop shortcut for GUI? (y/n): ").lower() == 'y'
        if create_shortcut:
            create_windows_shortcut()
    
    return True

def create_windows_shortcut():
    """Create Windows desktop shortcut for GUI"""
    try:
        import win32com.client
        
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "Web Automation Tool.lnk"
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(Path.cwd() / "venv" / "Scripts" / "python.exe")
        shortcut.Arguments = str(Path.cwd() / "gui_interface.py")
        shortcut.WorkingDirectory = str(Path.cwd())
        shortcut.IconLocation = str(Path.cwd() / "venv" / "Scripts" / "python.exe")
        shortcut.Description = "Web Automation Tool GUI"
        shortcut.save()
        
        print(f"✓ Created desktop shortcut: {shortcut_path}")
    except Exception as e:
        print(f"  Could not create shortcut: {e}")
        print("  You can manually create a shortcut to: python gui_interface.py")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed with error: {e}")
        sys.exit(1)
