# Credential Migration Guide

## 🔐 Secure Credential System - September 2025

This guide helps you migrate from hardcoded credentials to the secure Private folder credential system.

## Overview

The new system stores sensitive credentials in a `/Private` folder that is completely excluded from version control, providing better security and easier credential management.

## Quick Migration Steps

### 1. **Set up Private Directory**
```bash
# Validate and set up the Private directory
python3.11 src/utils/credential_manager.py setup
python3.11 src/utils/credential_manager.py validate
```

### 2. **Configure Your Credentials**
Copy the templates and add your actual credentials:

```bash
# Copy templates to actual credential files
cp Private/credentials_template.json Private/credentials.json
cp Private/api_keys_template.json Private/api_keys.json

# Edit the files with your actual credentials
nano Private/credentials.json
nano Private/api_keys.json
```

### 3. **Example Credential Configuration**

**Private/credentials.json:**
```json
{
  "wan_video_login": {
    "username": "your-actual-email@example.com",
    "password": "your-actual-password",
    "username_selector": "input[placeholder=\"Email address\"]",
    "password_selector": "input[type=\"password\"]",
    "submit_selector": "button:has-text(\"Log in\")[type=\"submit\"]"
  }
}
```

**Private/api_keys.json:**
```json
{
  "openai_api": {
    "api_key": "sk-your-actual-openai-key-here",
    "organization": "org-your-org-here"
  }
}
```

### 4. **Update Configuration Files**

The system automatically handles the new credential format. Existing config files have been updated to use:

```json
{
  "type": "login",
  "value": {
    "credential_file": "credentials.json",
    "credential_key": "wan_video_login",
    "username_selector": "input[placeholder=\"Email address\"]",
    "password_selector": "input[type=\"password\"]",
    "submit_selector": "button:has-text(\"Log in\")[type=\"submit\"]"
  }
}
```

## File Security

### Set Proper Permissions
```bash
# Restrict access to credential files (Unix/Linux/macOS)
chmod 600 Private/credentials.json
chmod 600 Private/api_keys.json
chmod 700 Private/
```

### Verify Git Exclusion
The `.gitignore` file has been updated to exclude the entire `/Private` folder:
```
# Private folder with credentials and API keys
Private/
/Private/
Private/*
!Private/.gitkeep
!Private/README.md
```

## Testing the System

### Validate Setup
```bash
# Check if everything is configured correctly
python3.11 src/utils/credential_manager.py validate
```

### List Available Credentials
```bash
# View configured credential services
python3.11 src/utils/credential_manager.py load-creds

# View configured API key services
python3.11 src/utils/credential_manager.py load-keys
```

### Test Automation
```bash
# Test with secure credentials (should show no security warnings)
python3.11 automaton-cli.py run -c scripts/fast_generation_config.json --show-browser
```

## Security Benefits

1. **Version Control Safety**: Credentials never committed to git
2. **Template System**: Easy setup without exposing actual credentials
3. **Backward Compatibility**: Existing systems still work with warnings
4. **File Permissions**: Restricted access to credential files
5. **Separation of Concerns**: Credentials separate from configuration logic

## Troubleshooting

### Common Issues

**FileNotFoundError: credentials.json**
- Run `python3.11 src/utils/credential_manager.py setup`
- Copy templates and configure your actual credentials

**Security Warnings in Logs**
- Old config files still have plaintext credentials
- Update configs to use `credential_file` and `credential_key` format

**Permission Denied Errors**
- Set proper file permissions: `chmod 600 Private/*.json`
- Ensure Private directory exists and is accessible

### Getting Help

1. Check validation: `python3.11 src/utils/credential_manager.py validate`
2. Review logs for detailed error messages
3. Verify file permissions and directory structure
4. Ensure templates are properly configured

## Migration Benefits

- ✅ **Security**: No more credentials in version control
- ✅ **Flexibility**: Easy to update credentials without changing configs
- ✅ **Organization**: All credentials in one secure location
- ✅ **Backward Compatibility**: Existing automations continue to work
- ✅ **Template System**: Easy setup for new environments

*Migration completed: September 2025*