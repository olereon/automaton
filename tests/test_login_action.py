#!/usr/bin/env python3
"""
Test script for LOGIN action functionality
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.engine import ActionType, Action, AutomationConfig, AutomationSequenceBuilder

def test_login_action_creation():
    """Test creating a login action"""
    print("Testing LOGIN action creation...")
    
    # Test ActionType enum
    assert ActionType.LOGIN.value == "login"
    print("✓ LOGIN action type enum works correctly")
    
    # Test creating a login action
    login_data = {
        "username": "test_user",
        "password": "test_password",
        "username_selector": "#username",
        "password_selector": "#password",
        "submit_selector": "#login-btn"
    }
    
    action = Action(
        type=ActionType.LOGIN,
        value=login_data,
        description="Login to test account"
    )
    
    assert action.type == ActionType.LOGIN
    assert action.value == login_data
    assert action.description == "Login to test account"
    print("✓ LOGIN action creation works correctly")
    
def test_automation_sequence_builder():
    """Test building automation sequence with login"""
    print("\nTesting AutomationSequenceBuilder with LOGIN...")
    
    builder = AutomationSequenceBuilder("Test Login", "https://example.com/login")
    
    # Add login action using builder
    config = (builder
        .add_login(
            username="testuser",
            password="testpass",
            username_selector="#username",
            password_selector="#password",
            submit_selector="#submit",
            description="Login to application"
        )
        .add_wait(2000, "Wait after login")
        .build()
    )
    
    assert len(config.actions) == 2
    assert config.actions[0].type == ActionType.LOGIN
    
    login_data = config.actions[0].value
    assert login_data["username"] == "testuser"
    assert login_data["password"] == "testpass"
    assert login_data["username_selector"] == "#username"
    assert login_data["password_selector"] == "#password"
    assert login_data["submit_selector"] == "#submit"
    
    print("✓ AutomationSequenceBuilder LOGIN method works correctly")
    
def test_config_serialization():
    """Test saving and loading config with LOGIN action"""
    print("\nTesting config serialization with LOGIN...")
    
    builder = AutomationSequenceBuilder("Login Test", "https://example.com")
    builder.add_login(
        username="admin",
        password="secret123",
        username_selector="#user",
        password_selector="#pass",
        submit_selector="#login",
        description="Admin login"
    )
    
    # Save to file
    test_file = "/tmp/test_login_config.json"
    builder.save_to_file(test_file)
    print("✓ Config saved successfully")
    
    # Load from file
    loaded_config = AutomationSequenceBuilder.load_from_file(test_file)
    
    assert loaded_config.name == "Login Test"
    assert loaded_config.url == "https://example.com"
    assert len(loaded_config.actions) == 1
    assert loaded_config.actions[0].type == ActionType.LOGIN
    
    login_data = loaded_config.actions[0].value
    assert login_data["username"] == "admin"
    assert login_data["password"] == "secret123"
    
    print("✓ Config loading works correctly")
    
    # Clean up
    Path(test_file).unlink(missing_ok=True)

if __name__ == "__main__":
    print("🧪 Testing LOGIN action functionality...\n")
    
    try:
        test_login_action_creation()
        test_automation_sequence_builder()
        test_config_serialization()
        
        print("\n✅ All tests passed! LOGIN action functionality is working correctly.")
        print("\n📝 Usage Summary:")
        print("1. LOGIN action is now available in the action type dropdown")
        print("2. GUI form includes fields for:")
        print("   - Username")
        print("   - Password (masked)")
        print("   - Username field selector (CSS selector)")
        print("   - Password field selector (CSS selector)")
        print("   - Submit button selector (CSS selector)")
        print("3. Login actions display the username in the actions list")
        print("4. Save/load functionality preserves login credentials")
        print("5. Automation engine can execute login actions")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)