#!/usr/bin/env python3
"""
Automation Scheduler Script

Manages multiple automation runs with retry logic, timing controls, and comprehensive reporting.
Supports sequential execution of configuration files with different wait times for success/failure.

Usage:
    python automation_scheduler.py --config scheduler_config.json
    python automation_scheduler.py --configs config1.json config2.json --success-wait 300 --failure-wait 60 --max-retries 3

Features:
- Sequential execution of multiple automation configurations
- Configurable wait times for success and failure scenarios
- Retry logic with maximum attempt limits
- Comprehensive logging and reporting
- JSON configuration support
- Real-time progress tracking
"""

import sys
import asyncio
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Add src directory to path for importing automation modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from core.engine import WebAutomationEngine, AutomationSequenceBuilder
except ImportError:
    print("Warning: Could not import automation modules. CLI-only mode activated.")
    WebAutomationEngine = None


class AutomationResult(Enum):
    """Automation execution results"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class AutomationRun:
    """Single automation run record"""
    config_file: str
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[AutomationResult] = None
    tasks_created: int = 0
    error_message: Optional[str] = None
    attempt_number: int = 1
    total_duration: Optional[float] = None

    def finish(self, result: AutomationResult, tasks_created: int = 0, error_message: str = None):
        """Mark run as finished with results"""
        self.end_time = datetime.now()
        self.result = result
        self.tasks_created = tasks_created
        self.error_message = error_message
        self.total_duration = (self.end_time - self.start_time).total_seconds()


@dataclass
class SchedulerConfig:
    """Scheduler configuration"""
    config_files: List[str]
    success_wait_time: int = 300  # 5 minutes default
    failure_wait_time: int = 60   # 1 minute default
    max_retries: int = 3
    timeout_seconds: int = 1800   # 30 minutes default
    log_file: str = "logs/automation_scheduler.log"
    use_cli: bool = True
    verbose: bool = True


class AutomationScheduler:
    """Main automation scheduler class"""

    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.runs: List[AutomationRun] = []
        self.current_config_index = 0
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_path = Path(self.config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO if self.config.verbose else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    async def run_automation_cli(self, config_file: str, timeout: int) -> tuple[AutomationResult, int, str]:
        """Run automation using CLI interface"""
        try:
            # Prepare CLI command
            cli_script = Path(__file__).parent.parent / "automaton-cli.py"
            cmd = [
                sys.executable,
                str(cli_script),
                "run",
                "-c", config_file,
                "--show-browser"  # For debugging
            ]

            self.logger.info(f"Executing CLI command: {' '.join(cmd)}")

            # Run automation with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path(__file__).parent.parent
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return AutomationResult.TIMEOUT, 0, "Process timed out"

            # Parse output for results
            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""

            self.logger.info(f"CLI stdout: {stdout_text}")
            if stderr_text:
                self.logger.warning(f"CLI stderr: {stderr_text}")

            # Extract task count from output (look for success indicators)
            tasks_created = self._extract_task_count(stdout_text)
            
            # Determine result based on return code and output
            if process.returncode == 0:
                if "success" in stdout_text.lower() or "completed" in stdout_text.lower():
                    return AutomationResult.SUCCESS, tasks_created, "Automation completed successfully"
                else:
                    return AutomationResult.FAILURE, tasks_created, "Automation completed with issues"
            else:
                error_msg = stderr_text or f"Process exited with code {process.returncode}"
                return AutomationResult.FAILURE, tasks_created, error_msg

        except Exception as e:
            self.logger.error(f"Error running CLI automation: {e}")
            return AutomationResult.ERROR, 0, str(e)

    async def run_automation_direct(self, config_file: str, timeout: int) -> tuple[AutomationResult, int, str]:
        """Run automation using direct engine interface"""
        try:
            if WebAutomationEngine is None:
                return AutomationResult.ERROR, 0, "Direct automation not available - missing dependencies"

            # Load configuration
            config_path = Path(config_file)
            if not config_path.exists():
                return AutomationResult.ERROR, 0, f"Configuration file not found: {config_file}"

            with open(config_path, 'r') as f:
                config_data = json.load(f)

            # Build automation sequence
            builder = AutomationSequenceBuilder.from_dict(config_data)
            automation_config = builder.build()

            # Run automation
            engine = WebAutomationEngine(automation_config)
            
            # Run with timeout
            try:
                results = await asyncio.wait_for(
                    engine.run_automation(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                await engine.cleanup()
                return AutomationResult.TIMEOUT, 0, "Automation timed out"

            # Extract results
            success = results.get('success', False)
            tasks_created = self._extract_task_count_from_results(results)
            error_msg = None

            if not success and results.get('errors'):
                error_msg = '; '.join([err.get('error', 'Unknown error') for err in results['errors'][:3]])

            result = AutomationResult.SUCCESS if success else AutomationResult.FAILURE
            message = "Automation completed successfully" if success else (error_msg or "Automation failed")

            return result, tasks_created, message

        except Exception as e:
            self.logger.error(f"Error running direct automation: {e}")
            return AutomationResult.ERROR, 0, str(e)

    def _extract_task_count(self, output_text: str) -> int:
        """Extract task count from CLI output"""
        try:
            # Look for patterns like "Total tasks created: 3" or "tasks created: 3"
            import re
            patterns = [
                r'Total tasks created:\s*(\d+)',
                r'tasks created:\s*(\d+)',
                r'Created task #(\d+)',
                r'Successfully created task #(\d+)',
                r'task #(\d+)'
            ]
            
            max_count = 0
            for pattern in patterns:
                matches = re.findall(pattern, output_text, re.IGNORECASE)
                if matches:
                    # Get the highest number found
                    numbers = [int(m) for m in matches]
                    max_count = max(max_count, max(numbers))
            
            return max_count
        except Exception as e:
            self.logger.warning(f"Could not extract task count: {e}")
            return 0

    def _extract_task_count_from_results(self, results: Dict[str, Any]) -> int:
        """Extract task count from direct automation results"""
        try:
            # Look in outputs for task-related information
            outputs = results.get('outputs', {})
            task_count = 0
            
            # Look for increment_variable results
            for key, value in outputs.items():
                if 'task_count' in key.lower() and isinstance(value, (int, str)):
                    try:
                        task_count = max(task_count, int(value))
                    except (ValueError, TypeError):
                        pass
            
            # Alternative: count successful actions that might be task creations
            action_results = results.get('action_results', [])
            creation_actions = [r for r in action_results if 'submit' in r.get('description', '').lower()]
            if creation_actions:
                task_count = max(task_count, len(creation_actions))
            
            return task_count
        except Exception as e:
            self.logger.warning(f"Could not extract task count from results: {e}")
            return 0

    async def run_single_automation(self, config_file: str, attempt: int = 1) -> AutomationRun:
        """Run a single automation with the specified configuration"""
        run = AutomationRun(
            config_file=config_file,
            start_time=datetime.now(),
            attempt_number=attempt
        )

        self.logger.info(f"🚀 Starting automation: {config_file} (attempt {attempt})")

        try:
            # Choose execution method
            if self.config.use_cli:
                result, tasks_created, message = await self.run_automation_cli(
                    config_file, self.config.timeout_seconds
                )
            else:
                result, tasks_created, message = await self.run_automation_direct(
                    config_file, self.config.timeout_seconds
                )

            # Record results
            run.finish(result, tasks_created, message)
            
            # Log results
            if result == AutomationResult.SUCCESS:
                self.logger.info(f"✅ SUCCESS: {config_file} - {tasks_created} tasks created")
            else:
                self.logger.warning(f"❌ {result.value.upper()}: {config_file} - {message}")

        except Exception as e:
            run.finish(AutomationResult.ERROR, 0, str(e))
            self.logger.error(f"💥 ERROR: {config_file} - {e}")

        self.runs.append(run)
        return run

    async def wait_with_countdown(self, wait_seconds: int, reason: str):
        """Wait with countdown display"""
        self.logger.info(f"⏳ Waiting {wait_seconds} seconds ({reason})...")
        
        if wait_seconds <= 0:
            return

        # Show countdown for waits longer than 10 seconds
        if wait_seconds > 10:
            for remaining in range(wait_seconds, 0, -1):
                if remaining % 60 == 0 or remaining <= 10:
                    mins, secs = divmod(remaining, 60)
                    if mins > 0:
                        self.logger.info(f"⏳ {mins}m {secs}s remaining...")
                    else:
                        self.logger.info(f"⏳ {secs}s remaining...")
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(wait_seconds)

    async def process_config_file(self, config_file: str) -> bool:
        """Process a single config file with retry logic"""
        self.logger.info(f"📁 Processing configuration: {config_file}")
        
        for attempt in range(1, self.config.max_retries + 1):
            run = await self.run_single_automation(config_file, attempt)
            
            if run.result == AutomationResult.SUCCESS:
                self.logger.info(f"🎉 Configuration completed successfully: {config_file}")
                return True
            
            elif attempt < self.config.max_retries:
                self.logger.warning(f"🔄 Retrying {config_file} (attempt {attempt + 1}/{self.config.max_retries})")
                await self.wait_with_countdown(
                    self.config.failure_wait_time,
                    f"before retry {attempt + 1}"
                )
            else:
                self.logger.error(f"💀 Configuration failed after {self.config.max_retries} attempts: {config_file}")
                return False

        return False

    async def run_scheduler(self):
        """Main scheduler execution loop"""
        self.logger.info("🎬 Starting Automation Scheduler")
        self.logger.info(f"📋 Configurations to process: {len(self.config.config_files)}")
        self.logger.info(f"⏱️  Success wait time: {self.config.success_wait_time}s")
        self.logger.info(f"🔄 Failure wait time: {self.config.failure_wait_time}s")
        self.logger.info(f"🎯 Max retries per config: {self.config.max_retries}")

        start_time = datetime.now()
        successful_configs = 0

        for i, config_file in enumerate(self.config.config_files):
            self.current_config_index = i
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📄 Processing {i+1}/{len(self.config.config_files)}: {config_file}")
            self.logger.info(f"{'='*60}")

            # Check if config file exists
            if not Path(config_file).exists():
                self.logger.error(f"❌ Configuration file not found: {config_file}")
                continue

            # Process configuration
            success = await self.process_config_file(config_file)
            
            if success:
                successful_configs += 1
                
                # Wait before next config (if not the last one)
                if i < len(self.config.config_files) - 1:
                    await self.wait_with_countdown(
                        self.config.success_wait_time,
                        "before next configuration"
                    )
            else:
                self.logger.error(f"💀 Skipping to next configuration after failures: {config_file}")

        # Generate final report
        end_time = datetime.now()
        total_duration = end_time - start_time
        
        self.logger.info(f"\n{'='*80}")
        if successful_configs == len(self.config.config_files):
            self.logger.info("🎉 ALL jobs are done. The job summary:")
        else:
            self.logger.info(f"⚠️  Scheduler completed with {successful_configs}/{len(self.config.config_files)} successful configurations:")

        self.generate_summary_report(total_duration)

    def generate_summary_report(self, total_duration: timedelta):
        """Generate comprehensive summary report"""
        self.logger.info(f"\n📊 AUTOMATION SCHEDULER SUMMARY")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"⏱️  Total execution time: {self._format_duration(total_duration.total_seconds())}")
        self.logger.info(f"📁 Total configurations: {len(self.config.config_files)}")
        
        # Group runs by configuration
        config_stats = {}
        for run in self.runs:
            if run.config_file not in config_stats:
                config_stats[run.config_file] = {
                    'attempts': [],
                    'final_result': None,
                    'total_tasks': 0
                }
            
            config_stats[run.config_file]['attempts'].append(run)
            if run.result == AutomationResult.SUCCESS:
                config_stats[run.config_file]['final_result'] = 'SUCCESS'
                config_stats[run.config_file]['total_tasks'] = run.tasks_created

        # Report per configuration
        successful_configs = 0
        total_tasks_created = 0
        
        for config_file in self.config.config_files:
            stats = config_stats.get(config_file, {'attempts': [], 'final_result': 'NOT_PROCESSED', 'total_tasks': 0})
            attempts = stats['attempts']
            final_result = stats['final_result']
            
            if final_result == 'SUCCESS':
                successful_configs += 1
                total_tasks_created += stats['total_tasks']
                
                success_run = next(r for r in attempts if r.result == AutomationResult.SUCCESS)
                self.logger.info(f"✅ {config_file}")
                self.logger.info(f"   └─ Tasks created: {success_run.tasks_created}")
                self.logger.info(f"   └─ Duration: {self._format_duration(success_run.total_duration)}")
                self.logger.info(f"   └─ Attempts: {len(attempts)}")
                self.logger.info(f"   └─ Completed: {success_run.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                self.logger.info(f"❌ {config_file}")
                self.logger.info(f"   └─ Result: FAILED after {len(attempts)} attempts")
                if attempts:
                    last_run = attempts[-1]
                    self.logger.info(f"   └─ Last error: {last_run.error_message}")
                    self.logger.info(f"   └─ Last attempt: {last_run.end_time.strftime('%Y-%m-%d %H:%M:%S') if last_run.end_time else 'N/A'}")

        # Overall statistics
        self.logger.info(f"\n📈 OVERALL STATISTICS")
        self.logger.info(f"{'='*40}")
        self.logger.info(f"✅ Successful configurations: {successful_configs}/{len(self.config.config_files)}")
        self.logger.info(f"🎯 Total tasks created: {total_tasks_created}")
        self.logger.info(f"🔄 Total automation runs: {len(self.runs)}")
        self.logger.info(f"⏱️  Average run duration: {self._format_duration(sum(r.total_duration for r in self.runs if r.total_duration) / len(self.runs) if self.runs else 0)}")
        
        # Success rate
        success_rate = (successful_configs / len(self.config.config_files)) * 100 if self.config.config_files else 0
        self.logger.info(f"📊 Success rate: {success_rate:.1f}%")

        # Export detailed report to JSON
        self.export_detailed_report()

    def export_detailed_report(self):
        """Export detailed report to JSON file"""
        try:
            report_file = Path(self.config.log_file).parent / "automation_report.json"
            
            report_data = {
                "scheduler_config": asdict(self.config),
                "execution_summary": {
                    "total_configs": len(self.config.config_files),
                    "successful_configs": sum(1 for run in self.runs if run.result == AutomationResult.SUCCESS),
                    "total_runs": len(self.runs),
                    "total_tasks_created": sum(run.tasks_created for run in self.runs),
                    "start_time": self.runs[0].start_time.isoformat() if self.runs else None,
                    "end_time": self.runs[-1].end_time.isoformat() if self.runs and self.runs[-1].end_time else None
                },
                "runs": [
                    {
                        "config_file": run.config_file,
                        "attempt_number": run.attempt_number,
                        "start_time": run.start_time.isoformat(),
                        "end_time": run.end_time.isoformat() if run.end_time else None,
                        "result": run.result.value if run.result else None,
                        "tasks_created": run.tasks_created,
                        "duration_seconds": run.total_duration,
                        "error_message": run.error_message
                    }
                    for run in self.runs
                ]
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.logger.info(f"📄 Detailed report exported to: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export detailed report: {e}")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            mins, secs = divmod(seconds, 60)
            return f"{int(mins)}m {int(secs)}s"
        else:
            hours, remainder = divmod(seconds, 3600)
            mins, secs = divmod(remainder, 60)
            return f"{int(hours)}h {int(mins)}m {int(secs)}s"


def load_scheduler_config(config_file: str) -> SchedulerConfig:
    """Load scheduler configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        return SchedulerConfig(
            config_files=config_data.get('config_files', []),
            success_wait_time=config_data.get('success_wait_time', 300),
            failure_wait_time=config_data.get('failure_wait_time', 60),
            max_retries=config_data.get('max_retries', 3),
            timeout_seconds=config_data.get('timeout_seconds', 1800),
            log_file=config_data.get('log_file', 'logs/automation_scheduler.log'),
            use_cli=config_data.get('use_cli', True),
            verbose=config_data.get('verbose', True)
        )
    except Exception as e:
        raise ValueError(f"Failed to load scheduler configuration: {e}")


def create_example_scheduler_config():
    """Create an example scheduler configuration file"""
    example_config = {
        "config_files": [
            "workflows/user_while-loop-1.json",
            "workflows/user_while-loop-2.json",
            "examples/queue_management_example.json"
        ],
        "success_wait_time": 300,  # 5 minutes between successful runs
        "failure_wait_time": 60,   # 1 minute before retry
        "max_retries": 3,          # Maximum retry attempts per config
        "timeout_seconds": 1800,   # 30 minutes timeout per automation
        "log_file": "logs/automation_scheduler.log",
        "use_cli": True,           # Use CLI interface (recommended)
        "verbose": True            # Detailed logging
    }
    
    config_file = Path("configs/scheduler_config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(example_config, f, indent=2)
    
    print(f"Example scheduler configuration created: {config_file}")
    return config_file


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Automation Scheduler")
    parser.add_argument('--config', type=str, help='Scheduler configuration file')
    parser.add_argument('--configs', nargs='+', help='List of automation config files')
    parser.add_argument('--success-wait', type=int, default=300, help='Wait time after success (seconds)')
    parser.add_argument('--failure-wait', type=int, default=60, help='Wait time before retry (seconds)')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts')
    parser.add_argument('--timeout', type=int, default=1800, help='Timeout per automation (seconds)')
    parser.add_argument('--log-file', type=str, default='logs/automation_scheduler.log', help='Log file path')
    parser.add_argument('--use-direct', action='store_true', help='Use direct engine instead of CLI')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode (less logging)')
    parser.add_argument('--create-example', action='store_true', help='Create example configuration')

    args = parser.parse_args()

    # Create example configuration if requested
    if args.create_example:
        create_example_scheduler_config()
        return

    # Load or create configuration
    if args.config:
        if not Path(args.config).exists():
            print(f"Configuration file not found: {args.config}")
            print("Use --create-example to create an example configuration.")
            return
        config = load_scheduler_config(args.config)
    elif args.configs:
        config = SchedulerConfig(
            config_files=args.configs,
            success_wait_time=args.success_wait,
            failure_wait_time=args.failure_wait,
            max_retries=args.max_retries,
            timeout_seconds=args.timeout,
            log_file=args.log_file,
            use_cli=not args.use_direct,
            verbose=not args.quiet
        )
    else:
        print("Error: Must specify either --config or --configs")
        print("Use --help for usage information or --create-example for example configuration.")
        return

    # Validate configuration files exist
    missing_files = [f for f in config.config_files if not Path(f).exists()]
    if missing_files:
        print(f"Error: Configuration files not found: {missing_files}")
        return

    # Create and run scheduler
    scheduler = AutomationScheduler(config)
    
    try:
        await scheduler.run_scheduler()
    except KeyboardInterrupt:
        scheduler.logger.info("\n⚠️  Scheduler interrupted by user")
    except Exception as e:
        scheduler.logger.error(f"💥 Scheduler failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())