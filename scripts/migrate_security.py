#!/usr/bin/env python3
"""
Security Migration Script for Automaton
Automatically detects and migrates plaintext credentials to secure storage
"""

import os
import sys
import json
import glob
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from utils.credential_manager import CredentialManager, migrate_plaintext_config
except ImportError:
    print("❌ Error: Could not import credential manager")
    print("Make sure you're in the automaton project directory and have installed dependencies")
    sys.exit(1)

def scan_for_credentials(directory: str = "."):
    """Scan directory for configuration files with potential credentials"""
    dangerous_files = []
    
    # Look for JSON config files
    for json_file in glob.glob(f"{directory}/**/*.json", recursive=True):
        if 'node_modules' in json_file or '.git' in json_file:
            continue
            
        try:
            with open(json_file, 'r') as f:
                content = f.read().lower()
                
            # Check for credential patterns
            if any(pattern in content for pattern in ['password', 'login', 'username', 'credential']):
                with open(json_file, 'r') as f:
                    config = json.load(f)
                
                # Look for automation configs with login actions
                if 'actions' in config:
                    for action in config['actions']:
                        if action.get('type') == 'login':
                            if isinstance(action.get('value'), dict):
                                login_data = action['value']
                                if 'password' in login_data and login_data['password']:
                                    dangerous_files.append(json_file)
                                    break
                        elif action.get('type') == 'input_text':
                            # Check for password input fields
                            selector = str(action.get('selector', '')).lower()
                            if 'password' in selector and action.get('value'):
                                dangerous_files.append(json_file)
                                break
                                
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    
    return dangerous_files

def main():
    print("🔒 Automaton Security Migration Tool")
    print("=" * 50)
    
    # Scan for vulnerable files
    print("🔍 Scanning for configuration files with plaintext credentials...")
    vulnerable_files = scan_for_credentials()
    
    if not vulnerable_files:
        print("✅ No plaintext credentials found in configuration files!")
        print("   Your setup appears to be secure.")
        return
    
    print(f"⚠️ Found {len(vulnerable_files)} files with potential plaintext credentials:")
    for i, file_path in enumerate(vulnerable_files, 1):
        print(f"   {i}. {file_path}")
    
    print("\n🛡️ Security Issues Detected:")
    print("   • Plaintext passwords in configuration files")
    print("   • Credentials exposed in version control")
    print("   • Risk of credential theft")
    
    print(f"\n📋 Migration Plan:")
    print("   1. Create encrypted credential storage")
    print("   2. Migrate plaintext credentials to secure storage")
    print("   3. Update configuration files to use credential references")
    print("   4. Create backup of original files")
    
    # Confirm migration
    response = input("\n❓ Proceed with security migration? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Migration cancelled. Your credentials remain at risk.")
        return
    
    print("\n🚀 Starting migration...")
    
    # Initialize credential manager
    cm = CredentialManager()
    
    # Migrate each file
    for file_path in vulnerable_files:
        print(f"\n📁 Migrating: {file_path}")
        try:
            migrate_plaintext_config(file_path)
            print(f"   ✅ Successfully migrated: {file_path}")
        except Exception as e:
            print(f"   ❌ Failed to migrate {file_path}: {e}")
    
    print(f"\n🎉 Migration Complete!")
    print(f"   • {len(vulnerable_files)} files processed")
    print(f"   • Credentials encrypted and stored securely")
    print(f"   • Original files backed up with .backup extension")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Test your automations to ensure they still work")
    print(f"   2. Delete .backup files once you've verified everything works")
    print(f"   3. Add *.backup to your .gitignore file")
    print(f"   4. Never commit plaintext credentials again!")
    
    print(f"\n🔧 Credential Management:")
    print(f"   • Store new credentials: python scripts/migrate_security.py store <id>")
    print(f"   • List credentials: python scripts/migrate_security.py list")
    print(f"   • Delete credentials: python scripts/migrate_security.py delete <id>")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Handle credential management commands
        cm = CredentialManager()
        command = sys.argv[1]
        
        if command == "store" and len(sys.argv) == 3:
            cm.prompt_and_store(sys.argv[2])
        elif command == "list":
            creds = cm.list_credentials()
            if creds:
                print("Stored credentials:")
                for cred_id in creds:
                    print(f"  • {cred_id}")
            else:
                print("No credentials stored.")
        elif command == "delete" and len(sys.argv) == 3:
            cm.delete_credential(sys.argv[2])
        else:
            print("Usage: python migrate_security.py [store <id> | list | delete <id>]")
    else:
        main()