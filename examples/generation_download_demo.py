#!/usr/bin/env python3
"""
Generation Download Demo
Demonstrates how to use the generation download automation system.
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType


async def demo_generation_downloads():
    """Demo the generation download automation"""
    
    print("🚀 Generation Download Automation Demo")
    print("=" * 50)
    
    # Load configuration
    config_path = Path(__file__).parent / "generation_download_config.json"
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return
    
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    # Convert to AutomationConfig
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
    
    config = AutomationConfig(
        name=config_data['name'],
        url=config_data['url'],
        actions=actions,
        headless=config_data.get('headless', False),
        viewport=config_data.get('viewport', {"width": 1600, "height": 1000})
    )
    
    # Create automation engine
    engine = WebAutomationEngine(config)
    
    try:
        print(f"📋 Automation: {config.name}")
        print(f"🌐 URL: {config.url}")
        print(f"🎬 Actions: {len(config.actions)}")
        print()
        
        # Run automation
        print("🔥 Starting automation...")
        results = await engine.run_automation()
        
        print("\n📊 Results:")
        print(f"✅ Success: {results['success']}")
        print(f"⚡ Actions completed: {results['actions_completed']}/{results['total_actions']}")
        
        if results.get('errors'):
            print(f"❌ Errors: {len(results['errors'])}")
            for i, error in enumerate(results['errors'][:3], 1):
                print(f"   {i}. {error}")
        
        # Check for generation-specific results
        generation_results = results.get('outputs', {})
        if generation_results:
            print("\n🎯 Generation Download Results:")
            for key, value in generation_results.items():
                if isinstance(value, dict) and 'downloads_completed' in value:
                    print(f"📥 Downloads completed: {value['downloads_completed']}")
                    if value.get('manager_status'):
                        status = value['manager_status']
                        print(f"📁 Downloads folder: {status.get('downloads_folder', 'Unknown')}")
                        print(f"📝 Log file: {status.get('log_file_path', 'Unknown')}")
        
        print("\n🎉 Demo completed!")
        
    except Exception as e:
        print(f"\n❌ Error during automation: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            await engine.cleanup()
        except:
            pass
    
    return True


def main():
    """Main entry point"""
    try:
        success = asyncio.run(demo_generation_downloads())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()