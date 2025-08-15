#!/usr/bin/env python3
"""
Secure Credential Management for Automaton
Provides encryption and safe storage of sensitive login credentials
"""

import os
import base64
import json
import getpass
from cryptography.fernet import Fernet
from pathlib import Path
from typing import Dict, Optional

class CredentialManager:
    """Secure credential storage and retrieval"""
    
    def __init__(self, config_dir: str = ".automaton"):
        self.config_dir = Path.home() / config_dir
        self.config_dir.mkdir(exist_ok=True)
        self.key_file = self.config_dir / "master.key"
        self.creds_file = self.config_dir / "credentials.enc"
        
        # Initialize encryption key
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize or load encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            # Generate new key
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
            # Secure the key file
            os.chmod(self.key_file, 0o600)
        
        self.cipher = Fernet(self.key)
    
    def store_credential(self, credential_id: str, username: str, password: str):
        """Store encrypted credentials"""
        # Load existing credentials
        credentials = self._load_credentials()
        
        # Add new credential
        credentials[credential_id] = {
            'username': username,
            'password': password
        }
        
        # Encrypt and save
        self._save_credentials(credentials)
        print(f"✅ Credential '{credential_id}' stored securely")
    
    def get_credential(self, credential_id: str) -> Optional[Dict[str, str]]:
        """Retrieve decrypted credentials"""
        credentials = self._load_credentials()
        return credentials.get(credential_id)
    
    def prompt_and_store(self, credential_id: str):
        """Interactive credential storage"""
        print(f"Setting up credentials for: {credential_id}")
        username = input("Username/Email: ")
        password = getpass.getpass("Password: ")
        self.store_credential(credential_id, username, password)
    
    def list_credentials(self) -> list:
        """List stored credential IDs"""
        credentials = self._load_credentials()
        return list(credentials.keys())
    
    def delete_credential(self, credential_id: str):
        """Delete stored credentials"""
        credentials = self._load_credentials()
        if credential_id in credentials:
            del credentials[credential_id]
            self._save_credentials(credentials)
            print(f"✅ Credential '{credential_id}' deleted")
        else:
            print(f"❌ Credential '{credential_id}' not found")
    
    def _load_credentials(self) -> dict:
        """Load and decrypt credentials"""
        if not self.creds_file.exists():
            return {}
        
        try:
            with open(self.creds_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"⚠️ Warning: Could not load credentials: {e}")
            return {}
    
    def _save_credentials(self, credentials: dict):
        """Encrypt and save credentials"""
        try:
            json_data = json.dumps(credentials).encode()
            encrypted_data = self.cipher.encrypt(json_data)
            
            with open(self.creds_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Secure the credentials file
            os.chmod(self.creds_file, 0o600)
        except Exception as e:
            print(f"❌ Error saving credentials: {e}")
            raise

def migrate_plaintext_config(config_path: str) -> str:
    """
    Migrate plaintext configuration to use secure credentials
    Returns the updated configuration with credential references
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    cm = CredentialManager()
    
    # Find and replace plaintext credentials
    for action in config.get('actions', []):
        if action.get('type') == 'login' and isinstance(action.get('value'), dict):
            login_data = action['value']
            if 'username' in login_data and 'password' in login_data:
                # Generate credential ID
                cred_id = f"{config['name']}_login".lower().replace(' ', '_')
                
                # Store credentials securely
                cm.store_credential(
                    cred_id,
                    login_data['username'],
                    login_data['password']
                )
                
                # Replace with credential reference
                login_data['credential_id'] = cred_id
                login_data['username'] = f"${{{cred_id}.username}}"
                login_data['password'] = f"${{{cred_id}.password}}"
        
        elif action.get('type') == 'input_text':
            # Check for password fields
            if 'password' in str(action.get('selector', '')).lower():
                if action.get('value') and len(action['value']) > 3:
                    print(f"⚠️ Warning: Possible plaintext password in action: {action.get('description', 'Unknown')}")
    
    # Save updated config
    backup_path = config_path + '.backup'
    os.rename(config_path, backup_path)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration migrated. Backup saved to: {backup_path}")
    return config_path

if __name__ == "__main__":
    # CLI interface for credential management
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python credential_manager.py <command> [args]")
        print("Commands:")
        print("  store <id> - Store new credential")
        print("  get <id> - Retrieve credential")
        print("  list - List all credential IDs")
        print("  delete <id> - Delete credential")
        print("  migrate <config_file> - Migrate plaintext config")
        sys.exit(1)
    
    cm = CredentialManager()
    command = sys.argv[1]
    
    if command == "store" and len(sys.argv) == 3:
        cm.prompt_and_store(sys.argv[2])
    elif command == "get" and len(sys.argv) == 3:
        cred = cm.get_credential(sys.argv[2])
        if cred:
            print(f"Username: {cred['username']}")
            print("Password: [HIDDEN]")
        else:
            print("Credential not found")
    elif command == "list":
        creds = cm.list_credentials()
        print("Stored credentials:", creds)
    elif command == "delete" and len(sys.argv) == 3:
        cm.delete_credential(sys.argv[2])
    elif command == "migrate" and len(sys.argv) == 3:
        migrate_plaintext_config(sys.argv[2])
    else:
        print("Invalid command or arguments")