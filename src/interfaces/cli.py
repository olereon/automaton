#!/usr/bin/env python3
# CLI Interface for Web Automation App

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Optional
import yaml

from core.engine import (
    WebAutomationEngine, 
    AutomationSequenceBuilder, 
    AutomationConfig,
    ActionType
)

class AutomationCLI:
    """Command Line Interface for Web Automation"""
    
    def __init__(self):
        self.parser = self._create_parser()
        
    def _create_parser(self):
        """Create argument parser with subcommands"""
        parser = argparse.ArgumentParser(
            description="Web Automation Tool - Automate repetitive web tasks",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run automation from config file
  automation run -c my_automation.json
  
  # Run with browser visible
  automation run -c my_automation.json --show-browser
  
  # Create new automation interactively
  automation create -n "My Task" -u https://example.com
  
  # Add actions to existing config
  automation add-action -c config.json --type click --selector "#button"
  
  # List available actions
  automation list-actions
            """
        )
        
        parser.add_argument('-v', '--verbose', action='store_true', 
                          help='Enable verbose logging')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Run command
        run_parser = subparsers.add_parser('run', help='Run automation from config file')
        run_parser.add_argument('-c', '--config', required=True, 
                              help='Path to automation config file (JSON/YAML)')
        run_parser.add_argument('--show-browser', action='store_true',
                              help='Show browser window (disable headless mode)')
        run_parser.add_argument('--continue-on-error', action='store_true',
                              help='Continue automation even if an action fails')
        
        # Create command
        create_parser = subparsers.add_parser('create', 
                                            help='Create new automation config')
        create_parser.add_argument('-n', '--name', required=True,
                                 help='Name for the automation')
        create_parser.add_argument('-u', '--url', required=True,
                                 help='Target URL')
        create_parser.add_argument('-o', '--output', 
                                 help='Output file path (default: <name>.json)')
        create_parser.add_argument('--interactive', action='store_true',
                                 help='Interactive mode to add actions')
        
        # Add action command
        add_parser = subparsers.add_parser('add-action', 
                                         help='Add action to existing config')
        add_parser.add_argument('-c', '--config', required=True,
                              help='Path to config file to modify')
        add_parser.add_argument('--type', required=True, 
                              choices=[a.value for a in ActionType],
                              help='Type of action to add')
        add_parser.add_argument('--selector', help='CSS selector for the element')
        add_parser.add_argument('--value', help='Value for the action')
        add_parser.add_argument('--description', help='Description of the action')
        add_parser.add_argument('--timeout', type=int, default=30000,
                              help='Timeout in milliseconds')
        
        # List actions command
        list_parser = subparsers.add_parser('list-actions', 
                                          help='List all available action types')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', 
                                              help='Validate config file')
        validate_parser.add_argument('-c', '--config', required=True,
                                   help='Path to config file to validate')
        
        # Convert command
        convert_parser = subparsers.add_parser('convert', 
                                             help='Convert between JSON and YAML')
        convert_parser.add_argument('-i', '--input', required=True,
                                  help='Input file path')
        convert_parser.add_argument('-o', '--output', required=True,
                                  help='Output file path')
        
        return parser
        
    def run(self, args=None):
        """Main entry point for CLI"""
        args = self.parser.parse_args(args)
        
        if args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
            
        if not args.command:
            self.parser.print_help()
            return
            
        # Route to appropriate handler
        handlers = {
            'run': self._handle_run,
            'create': self._handle_create,
            'add-action': self._handle_add_action,
            'list-actions': self._handle_list_actions,
            'validate': self._handle_validate,
            'convert': self._handle_convert
        }
        
        handler = handlers.get(args.command)
        if handler:
            try:
                handler(args)
            except Exception as e:
                print(f"Error: {str(e)}", file=sys.stderr)
                sys.exit(1)
                
    def _handle_run(self, args):
        """Handle run command"""
        config_path = Path(args.config)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        # Load config
        if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            config = self._dict_to_config(data)
        else:
            config = AutomationSequenceBuilder.load_from_file(str(config_path))
            
        # Override headless if requested
        if args.show_browser:
            config.headless = False
            
        # Run automation
        print(f"Starting automation: {config.name}")
        print(f"Target URL: {config.url}")
        print(f"Total actions: {len(config.actions)}")
        print("-" * 50)
        
        engine = WebAutomationEngine(config)
        if args.continue_on_error:
            engine.continue_on_error = True
            
        results = asyncio.run(engine.run_automation())
        
        # Display results
        print("\n" + "-" * 50)
        print(f"Automation {'succeeded' if results['success'] else 'failed'}")
        print(f"Actions completed: {results['actions_completed']}/{results['total_actions']}")
        
        if results['outputs']:
            print("\nOutputs:")
            for key, value in results['outputs'].items():
                print(f"  {key}: {value}")
                
        if results['errors']:
            print("\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")
                
    def _handle_create(self, args):
        """Handle create command"""
        builder = AutomationSequenceBuilder(args.name, args.url)
        
        if args.interactive:
            print(f"Creating automation: {args.name}")
            print(f"Target URL: {args.url}")
            print("\nEnter actions (type 'done' to finish):")
            
            while True:
                print("\nAvailable actions:")
                for i, action_type in enumerate(ActionType, 1):
                    print(f"  {i}. {action_type.value}")
                    
                choice = input("\nSelect action number (or 'done'): ").strip()
                
                if choice.lower() == 'done':
                    break
                    
                try:
                    action_idx = int(choice) - 1
                    action_type = list(ActionType)[action_idx]
                    
                    # Get action parameters
                    params = self._get_action_parameters(action_type)
                    self._add_action_to_builder(builder, action_type, params)
                    
                    print(f"✓ Added {action_type.value} action")
                    
                except (ValueError, IndexError):
                    print("Invalid choice, please try again")
                    
        # Save config
        output_path = args.output or f"{args.name.lower().replace(' ', '_')}.json"
        builder.save_to_file(output_path)
        print(f"\nAutomation config saved to: {output_path}")
        
    def _handle_add_action(self, args):
        """Handle add-action command"""
        config_path = Path(args.config)
        config = AutomationSequenceBuilder.load_from_file(str(config_path))
        
        # Create builder from existing config
        builder = AutomationSequenceBuilder(config.name, config.url)
        builder.config = config
        
        # Add new action
        action_type = ActionType(args.type)
        params = {
            'selector': args.selector,
            'value': args.value,
            'description': args.description,
            'timeout': args.timeout
        }
        
        self._add_action_to_builder(builder, action_type, params)
        
        # Save updated config
        builder.save_to_file(str(config_path))
        print(f"✓ Added {action_type.value} action to {config_path}")
        
    def _handle_list_actions(self, args):
        """Handle list-actions command"""
        print("Available Action Types:")
        print("-" * 50)
        
        action_descriptions = {
            ActionType.EXPAND_DIALOG: "Click to expand a dialog or panel",
            ActionType.INPUT_TEXT: "Enter text into an input field",
            ActionType.UPLOAD_IMAGE: "Upload an image file",
            ActionType.TOGGLE_SETTING: "Toggle a checkbox or switch",
            ActionType.CLICK_BUTTON: "Click a button element",
            ActionType.CHECK_QUEUE: "Check queue status for completion",
            ActionType.DOWNLOAD_FILE: "Download a file",
            ActionType.REFRESH_PAGE: "Refresh the current page",
            ActionType.SWITCH_PANEL: "Switch to a different panel or tab",
            ActionType.WAIT: "Wait for specified milliseconds",
            ActionType.WAIT_FOR_ELEMENT: "Wait for an element to appear"
        }
        
        for action_type, description in action_descriptions.items():
            print(f"\n{action_type.value}:")
            print(f"  {description}")
            
            # Show required parameters
            if action_type in [ActionType.REFRESH_PAGE, ActionType.WAIT]:
                print("  Parameters: None required")
            elif action_type == ActionType.WAIT:
                print("  Parameters: value (milliseconds)")
            else:
                print("  Parameters: selector")
                if action_type in [ActionType.INPUT_TEXT, ActionType.UPLOAD_IMAGE, 
                                 ActionType.TOGGLE_SETTING, ActionType.CHECK_QUEUE]:
                    print("             value")
                    
    def _handle_validate(self, args):
        """Handle validate command"""
        config_path = Path(args.config)
        
        try:
            if config_path.suffix in ['.yaml', '.yml']:
                with open(config_path, 'r') as f:
                    data = yaml.safe_load(f)
                config = self._dict_to_config(data)
            else:
                config = AutomationSequenceBuilder.load_from_file(str(config_path))
                
            # Validate config
            errors = self._validate_config(config)
            
            if errors:
                print(f"❌ Config validation failed with {len(errors)} errors:")
                for error in errors:
                    print(f"  - {error}")
            else:
                print(f"✓ Config is valid")
                print(f"  Name: {config.name}")
                print(f"  URL: {config.url}")
                print(f"  Actions: {len(config.actions)}")
                
        except Exception as e:
            print(f"❌ Failed to load config: {str(e)}")
            
    def _handle_convert(self, args):
        """Handle convert command"""
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        # Load from input format
        if input_path.suffix in ['.yaml', '.yml']:
            with open(input_path, 'r') as f:
                data = yaml.safe_load(f)
        else:
            with open(input_path, 'r') as f:
                data = json.load(f)
                
        # Save to output format
        if output_path.suffix in ['.yaml', '.yml']:
            with open(output_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        print(f"✓ Converted {input_path} to {output_path}")
        
    def _get_action_parameters(self, action_type: ActionType) -> dict:
        """Interactive prompt for action parameters"""
        params = {}
        
        if action_type != ActionType.REFRESH_PAGE:
            if action_type != ActionType.WAIT:
                params['selector'] = input("CSS Selector: ").strip()
                
            if action_type in [ActionType.INPUT_TEXT, ActionType.UPLOAD_IMAGE]:
                params['value'] = input("Value/Path: ").strip()
            elif action_type == ActionType.TOGGLE_SETTING:
                enabled = input("Enable? (y/n): ").strip().lower() == 'y'
                params['value'] = enabled
            elif action_type == ActionType.CHECK_QUEUE:
                params['value'] = input("Completion text (optional): ").strip() or None
            elif action_type == ActionType.WAIT:
                params['value'] = int(input("Wait time (ms): ").strip())
                
        params['description'] = input("Description (optional): ").strip() or None
        
        return params
        
    def _add_action_to_builder(self, builder, action_type: ActionType, params: dict):
        """Add action to builder based on type and parameters"""
        method_map = {
            ActionType.EXPAND_DIALOG: builder.add_expand_dialog,
            ActionType.INPUT_TEXT: builder.add_input_text,
            ActionType.UPLOAD_IMAGE: builder.add_upload_image,
            ActionType.TOGGLE_SETTING: builder.add_toggle_setting,
            ActionType.CLICK_BUTTON: builder.add_click_button,
            ActionType.CHECK_QUEUE: builder.add_check_queue,
            ActionType.DOWNLOAD_FILE: builder.add_download_file,
            ActionType.REFRESH_PAGE: builder.add_refresh_page,
            ActionType.SWITCH_PANEL: builder.add_switch_panel,
            ActionType.WAIT: builder.add_wait,
            ActionType.WAIT_FOR_ELEMENT: builder.add_wait_for_element
        }
        
        method = method_map.get(action_type)
        if method:
            # Filter out None values
            filtered_params = {k: v for k, v in params.items() 
                             if v is not None and k in method.__code__.co_varnames}
            method(**filtered_params)
            
    def _dict_to_config(self, data: dict) -> AutomationConfig:
        """Convert dictionary to AutomationConfig"""
        config = AutomationConfig(
            name=data['name'],
            url=data['url'],
            headless=data.get('headless', True),
            viewport=data.get('viewport'),
            actions=[]
        )
        
        for action_data in data.get('actions', []):
            from web_automation import Action
            config.actions.append(Action(
                type=ActionType(action_data['type']),
                selector=action_data.get('selector'),
                value=action_data.get('value'),
                timeout=action_data.get('timeout', 30000),
                description=action_data.get('description')
            ))
            
        return config
        
    def _validate_config(self, config: AutomationConfig) -> list:
        """Validate automation config"""
        errors = []
        
        if not config.name:
            errors.append("Name is required")
        if not config.url:
            errors.append("URL is required")
        if not config.actions:
            errors.append("At least one action is required")
            
        for i, action in enumerate(config.actions):
            if action.type not in ActionType:
                errors.append(f"Action {i}: Invalid action type")
                
            # Validate required parameters
            if action.type not in [ActionType.REFRESH_PAGE, ActionType.WAIT]:
                if not action.selector:
                    errors.append(f"Action {i} ({action.type.value}): Selector is required")
                    
            if action.type in [ActionType.INPUT_TEXT, ActionType.UPLOAD_IMAGE, ActionType.WAIT]:
                if action.value is None:
                    errors.append(f"Action {i} ({action.type.value}): Value is required")
                    
        return errors

def main():
    """Main entry point"""
    cli = AutomationCLI()
    cli.run()

if __name__ == "__main__":
    main()
