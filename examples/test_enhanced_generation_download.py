#!/usr/bin/env python3
"""
Test Enhanced Generation Download with Debug Logging
Tests the new selector strategies for generation downloads.
"""

import asyncio
import sys
import os
import json
import logging
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from src directory
try:
    from src.core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType
except ImportError:
    # Alternative import path
    sys.path.insert(0, os.path.join(parent_dir, 'src'))
    from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType

# Set up enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('generation_download_debug.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_enhanced_generation_downloads():
    """Test the enhanced generation download automation with new selectors"""
    
    print("🚀 Enhanced Generation Download Test")
    print("=" * 50)
    print("📝 Debug logging enabled - check generation_download_debug.log for details")
    print("")
    
    # Load configuration
    config_path = Path(__file__).parent / "generation_download_config.json"
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return
    
    # Load and parse configuration
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    print(f"📋 Automation: {config_data['name']}")
    print(f"🌐 URL: {config_data['url']}")
    print(f"🎬 Actions: {len(config_data['actions'])}")
    print("")
    
    # Parse actions
    actions = []
    for action_data in config_data['actions']:
        action = Action(
            type=ActionType(action_data['type']),
            selector=action_data.get('selector'),
            value=action_data.get('value'),
            timeout=action_data.get('timeout', 10000),
            description=action_data.get('description')
        )
        actions.append(action)
    
    # Create automation config
    config = AutomationConfig(
        name=config_data['name'],
        url=config_data['url'],
        actions=actions,
        headless=config_data.get('headless', False),
        viewport=config_data.get('viewport', {"width": 1600, "height": 1000}),
        keep_browser_open=True
    )
    
    # Run automation
    print("🔥 Starting automation with enhanced selectors...")
    print("")
    
    engine = WebAutomationEngine(config)
    results = await engine.run_automation()
    
    # Display results
    print("\n" + "=" * 50)
    print("📊 Results:")
    print(f"✅ Success: {results['success']}")
    print(f"⚡ Actions completed: {results['actions_completed']}/{results['total_actions']}")
    
    if results.get('errors'):
        print(f"❌ Errors: {len(results['errors'])}")
        for i, error in enumerate(results['errors'], 1):
            print(f"   {i}. {error}")
    
    # Display generation download specific results
    if results.get('outputs'):
        for key, value in results['outputs'].items():
            if 'generation_downloads' in str(key):
                print("\n🎯 Generation Download Results:")
                if isinstance(value, dict):
                    print(f"📥 Downloads completed: {value.get('downloads_completed', 0)}")
                    if value.get('errors'):
                        print(f"⚠️  Download errors: {len(value['errors'])}")
                        for err in value['errors'][:3]:  # Show first 3 errors
                            print(f"     - {err}")
    
    print("\n🎉 Test completed!")
    print("📝 Check generation_download_debug.log for detailed debug information")

if __name__ == "__main__":
    asyncio.run(test_enhanced_generation_downloads())