"""
Secure credential management system for the Automaton framework.

This module provides secure loading and handling of credentials and API keys
from separate configuration files in the /Private directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages secure loading of credentials and API keys from private files."""
    
    def __init__(self, base_path: Optional[str] = None):
        """Initialize the credential manager.
        
        Args:
            base_path: Base path to the project root. If None, auto-detects.
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # Auto-detect base path by looking for key files
            current_path = Path(__file__).parent
            while current_path.parent != current_path:
                if (current_path / "Private").exists() or (current_path / "src").exists():
                    self.base_path = current_path
                    break
                current_path = current_path.parent
            else:
                # Default to current working directory
                self.base_path = Path.cwd()
        
        self.private_path = self.base_path / "Private"
        self.credentials_cache = {}
        self.api_keys_cache = {}
    
    def load_credentials(self, reload: bool = False) -> Dict[str, Any]:
        """Load login credentials from Private/credentials.json.
        
        Args:
            reload: If True, reload from file even if cached.
            
        Returns:
            Dictionary of credential configurations.
            
        Raises:
            FileNotFoundError: If credentials file doesn't exist.
            json.JSONDecodeError: If credentials file is invalid JSON.
        """
        if not reload and self.credentials_cache:
            return self.credentials_cache
        
        credentials_file = self.private_path / "credentials.json"
        
        if not credentials_file.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_file}\n"
                f"Please create {credentials_file} using the template in Private/credentials_template.json"
            )
        
        try:
            with open(credentials_file, 'r', encoding='utf-8') as f:
                credentials = json.load(f)
                
            # Remove comments if present
            if '_comment' in credentials:
                del credentials['_comment']
                
            self.credentials_cache = credentials
            logger.info(f"Loaded credentials for {len(credentials)} services")
            return credentials
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in credentials file {credentials_file}: {e.msg}",
                e.doc, e.pos
            )
    
    def load_api_keys(self, reload: bool = False) -> Dict[str, Any]:
        """Load API keys from Private/api_keys.json.
        
        Args:
            reload: If True, reload from file even if cached.
            
        Returns:
            Dictionary of API key configurations.
            
        Raises:
            FileNotFoundError: If API keys file doesn't exist.
            json.JSONDecodeError: If API keys file is invalid JSON.
        """
        if not reload and self.api_keys_cache:
            return self.api_keys_cache
        
        api_keys_file = self.private_path / "api_keys.json"
        
        if not api_keys_file.exists():
            raise FileNotFoundError(
                f"API keys file not found: {api_keys_file}\n"
                f"Please create {api_keys_file} using the template in Private/api_keys_template.json"
            )
        
        try:
            with open(api_keys_file, 'r', encoding='utf-8') as f:
                api_keys = json.load(f)
                
            # Remove comments if present
            if '_comment' in api_keys:
                del api_keys['_comment']
                
            self.api_keys_cache = api_keys
            logger.info(f"Loaded API keys for {len(api_keys)} services")
            return api_keys
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in API keys file {api_keys_file}: {e.msg}",
                e.doc, e.pos
            )
    
    def get_login_credentials(self, service_name: str) -> Dict[str, str]:
        """Get login credentials for a specific service.
        
        Args:
            service_name: Name of the service (e.g., 'wan_video_login').
            
        Returns:
            Dictionary containing username, password, and selectors.
            
        Raises:
            KeyError: If service not found in credentials.
        """
        credentials = self.load_credentials()
        
        if service_name not in credentials:
            available_services = list(credentials.keys())
            raise KeyError(
                f"Service '{service_name}' not found in credentials. "
                f"Available services: {available_services}"
            )
        
        return credentials[service_name]
    
    def get_api_key(self, service_name: str, key_name: str = 'api_key') -> str:
        """Get an API key for a specific service.
        
        Args:
            service_name: Name of the service (e.g., 'openai_api').
            key_name: Name of the key field (default: 'api_key').
            
        Returns:
            The API key string.
            
        Raises:
            KeyError: If service or key not found.
        """
        api_keys = self.load_api_keys()
        
        if service_name not in api_keys:
            available_services = list(api_keys.keys())
            raise KeyError(
                f"Service '{service_name}' not found in API keys. "
                f"Available services: {available_services}"
            )
        
        service_keys = api_keys[service_name]
        if key_name not in service_keys:
            available_keys = list(service_keys.keys())
            raise KeyError(
                f"Key '{key_name}' not found for service '{service_name}'. "
                f"Available keys: {available_keys}"
            )
        
        return service_keys[key_name]
    
    def load_credential_file(self, relative_path: str) -> Dict[str, Any]:
        """Load credentials from a custom file path relative to Private folder.
        
        Args:
            relative_path: Path relative to Private folder (e.g., 'custom_creds.json').
            
        Returns:
            Dictionary containing the credential data.
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            json.JSONDecodeError: If file is invalid JSON.
        """
        file_path = self.private_path / relative_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"Credential file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Remove comments if present
            if '_comment' in data:
                del data['_comment']
                
            return data
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in credential file {file_path}: {e.msg}",
                e.doc, e.pos
            )
    
    def validate_private_directory(self) -> Dict[str, bool]:
        """Validate the Private directory and required files.
        
        Returns:
            Dictionary with validation results.
        """
        results = {
            'private_dir_exists': self.private_path.exists(),
            'credentials_file_exists': (self.private_path / "credentials.json").exists(),
            'api_keys_file_exists': (self.private_path / "api_keys.json").exists(),
            'templates_exist': (
                (self.private_path / "credentials_template.json").exists() and
                (self.private_path / "api_keys_template.json").exists()
            )
        }
        
        results['all_valid'] = all([
            results['private_dir_exists'],
            results['credentials_file_exists'] or results['templates_exist'],
            results['api_keys_file_exists'] or results['templates_exist']
        ])
        
        return results
    
    def setup_private_directory(self) -> bool:
        """Set up the Private directory with templates if it doesn't exist.
        
        Returns:
            True if setup was successful, False otherwise.
        """
        try:
            # Create Private directory if it doesn't exist
            self.private_path.mkdir(exist_ok=True)
            
            # Set restrictive permissions (Unix/Linux only)
            if hasattr(os, 'chmod'):
                os.chmod(self.private_path, 0o700)
            
            logger.info(f"Private directory set up at: {self.private_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up Private directory: {e}")
            return False


# Global credential manager instance
_credential_manager = None

def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance."""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager


def resolve_credential_path(config_value: Any) -> Any:
    """Resolve credential paths in configuration values.
    
    This function looks for special credential path patterns and replaces them
    with actual credential data loaded from the Private directory.
    
    Args:
        config_value: Configuration value that may contain credential paths.
        
    Returns:
        Resolved configuration value with credentials loaded.
    """
    if isinstance(config_value, dict):
        # Check if this looks like a credential file reference
        if 'credential_file' in config_value and 'credential_key' in config_value:
            credential_manager = get_credential_manager()
            try:
                credential_data = credential_manager.load_credential_file(
                    config_value['credential_file']
                )
                
                key_path = config_value['credential_key'].split('.')
                result = credential_data
                for key in key_path:
                    result = result[key]
                
                return result
                
            except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
                logger.error(f"Failed to resolve credential path: {e}")
                raise
        
        # Recursively process dictionary values
        return {key: resolve_credential_path(value) for key, value in config_value.items()}
    
    elif isinstance(config_value, list):
        # Recursively process list items
        return [resolve_credential_path(item) for item in config_value]
    
    else:
        # Return as-is for non-dict/list values
        return config_value


if __name__ == "__main__":
    # CLI interface for credential management
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python credential_manager.py <command> [args]")
        print("Commands:")
        print("  validate - Validate Private directory setup")
        print("  setup - Set up Private directory with templates")
        print("  load-creds [service] - Load and display credentials")
        print("  load-keys [service] - Load and display API keys")
        sys.exit(1)
    
    cm = CredentialManager()
    command = sys.argv[1]
    
    try:
        if command == "validate":
            results = cm.validate_private_directory()
            print("Validation Results:")
            for key, value in results.items():
                print(f"  {key}: {'✅' if value else '❌'}")
        
        elif command == "setup":
            success = cm.setup_private_directory()
            print("✅ Private directory setup completed" if success else "❌ Setup failed")
        
        elif command == "load-creds":
            credentials = cm.load_credentials()
            if len(sys.argv) > 2:
                service = sys.argv[2]
                if service in credentials:
                    cred = credentials[service]
                    print(f"Credentials for {service}:")
                    print(f"  Username: {cred.get('username', 'N/A')}")
                    print(f"  Password: {'*' * len(cred.get('password', ''))}")
                    print(f"  Selectors: {len([k for k in cred.keys() if k.endswith('_selector')])} configured")
                else:
                    print(f"Service '{service}' not found")
            else:
                print(f"Available credential services: {list(credentials.keys())}")
        
        elif command == "load-keys":
            api_keys = cm.load_api_keys()
            if len(sys.argv) > 2:
                service = sys.argv[2]
                if service in api_keys:
                    keys = api_keys[service]
                    print(f"API keys for {service}:")
                    for key_name in keys:
                        print(f"  {key_name}: {'*' * 20}")
                else:
                    print(f"Service '{service}' not found")
            else:
                print(f"Available API key services: {list(api_keys.keys())}")
        
        else:
            print("Unknown command. Use --help for usage information")
    
    except Exception as e:
        print(f"Error: {e}")