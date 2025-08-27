#!/usr/bin/env python3
"""
Automation Scheduler Script

Manages multiple automation runs with retry logic, timing controls, and comprehensive reporting.
Supports sequential execution of configuration files with different wait times for success/failure.

Usage:
    python automation_scheduler.py --config scheduler_config.json
    python automation_scheduler.py --configs config1.json config2.json --success-wait 300 --failure-wait 60 --max-retries 3
    python automation_scheduler.py --config scheduler_config.json --start-from 5  # Start from 5th config file
    python automation_scheduler.py --config scheduler_config.json --time 14:30:00  # Start at 2:30 PM today
    python automation_scheduler.py --config scheduler_config.json --date 2024-12-25 --time 09:00:00  # Start at specific date and time

Features:
- Sequential execution of multiple automation configurations
- Configurable wait times for success and failure scenarios
- Retry logic with maximum attempt limits
- Comprehensive logging and reporting
- JSON configuration support
- Real-time progress tracking
- Start from specific config file index (convenient for resuming interrupted runs)
- Schedule automation to start at specific time (HH:mm:ss)
- Schedule automation to start on specific date (YYYY-MM-dd)
"""

import sys
import asyncio
import json
import time
import logging
import argparse
import subprocess
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Add src directory to path for importing automation modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from core.engine import WebAutomationEngine, AutomationSequenceBuilder
    from core.controller import AutomationController, AutomationState, ControlSignal
    from core.keyboard_handler import create_keyboard_handler
except ImportError:
    print("Warning: Could not import automation modules. CLI-only mode activated.")
    WebAutomationEngine = None
    AutomationSequenceBuilder = None
    AutomationController = None
    AutomationState = None
    ControlSignal = None
    create_keyboard_handler = None


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

    def finish(self, result: AutomationResult, tasks_created: int = 0, error_message: Optional[str] = None):
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
    scheduled_time: Optional[str] = None  # Time in HH:mm:ss format
    scheduled_date: Optional[str] = None  # Date in YYYY-MM-dd format


class AutomationScheduler:
    """Main automation scheduler class with enhanced control"""

    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.runs: List[AutomationRun] = []
        self.current_config_index = 0
        
        # Control system
        self.controller = AutomationController() if AutomationController else None
        self.is_paused = False
        self.should_stop = False
        self.current_automation_task: Optional[asyncio.Task] = None
        
        # Enhanced keyboard handling
        self.keyboard_handler = create_keyboard_handler(advanced=True) if create_keyboard_handler else None
        self._setup_control_handlers()
        
        self.setup_logging()

    def _setup_control_handlers(self):
        """Setup enhanced control handlers for Ctrl+W and Ctrl+T"""
        def keyboard_control_callback(command: str):
            """Handle keyboard control commands"""
            if command == 'toggle_pause':
                if self.is_paused:
                    print("\n▶️  Resuming scheduler...")
                    self.resume_scheduler()
                else:
                    print("\n⏸️  Pausing scheduler...")
                    self.pause_scheduler()
            elif command == 'stop':
                print("\n🛑 Stopping scheduler...")
                self.stop_scheduler()
            elif command == 'status':
                self._print_status()
        
        # Setup keyboard handler
        if self.keyboard_handler:
            self.keyboard_handler.set_control_callback(keyboard_control_callback)
        
        # Keep basic signal handlers as fallback
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            if signum == signal.SIGINT:  # Ctrl+C - fallback pause
                print(f"\n⏸️  Received {signal_name} - Use Ctrl+W for pause/resume, Ctrl+T for stop")
                if self.is_paused:
                    self.resume_scheduler()
                else:
                    self.pause_scheduler()
            elif signum == signal.SIGTERM:  # Termination
                print(f"\n🛑 Received {signal_name} - Stopping scheduler...")
                self.stop_scheduler()
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except ValueError:
            # Signals not available (e.g., in some threading contexts)
            pass

    def setup_logging(self):
        """Setup minimal logging configuration"""
        # Create logs directory if it doesn't exist
        log_path = Path(self.config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure minimal logging - only errors and final results
        logging.basicConfig(
            level=logging.ERROR,
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

            # Only log errors
            if stderr_text:
                self.logger.error(f"CLI automation error: {stderr_text}")

            # Extract task count from output (look for success indicators)
            tasks_created = self._extract_task_count(stdout_text)
            
            # Check for specific FAILURE indicators (only for actual errors, not successful completion)
            failure_indicators = [
                "stop_automation",
                "STOP_AUTOMATION", 
                "Automation stopped",
                "RuntimeError"
            ]
            
            # Check for queue-related failures (only if no tasks were created)
            queue_failure_indicators = [
                "queue is full - popup detected",
                "Queue is full - popup detected", 
                "reached your video submission limit",
                "You've reached your"
            ]
            
            # Check if any failure indicator is present
            output_lower = stdout_text.lower()
            has_failure_indicator = any(indicator.lower() in output_lower for indicator in failure_indicators)
            
            # Check for queue failures only if no tasks were created
            has_queue_failure = False
            if tasks_created == 0:
                has_queue_failure = any(indicator.lower() in output_lower for indicator in queue_failure_indicators)
            
            # Determine result based on return code and output
            if process.returncode == 0:
                if has_failure_indicator or has_queue_failure:
                    # Only fail if we have actual failure indicators OR queue failure with 0 tasks
                    if has_failure_indicator:
                        return AutomationResult.FAILURE, tasks_created, "Automation stopped due to error condition"
                    else:  # has_queue_failure and tasks_created == 0
                        return AutomationResult.FAILURE, tasks_created, "Automation failed - queue already full (0 tasks created)"
                elif "success" in stdout_text.lower() or "completed" in stdout_text.lower():
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
            if AutomationSequenceBuilder is None:
                return AutomationResult.ERROR, 0, "Automation modules not available"
            
            builder = AutomationSequenceBuilder.from_dict(config_data)
            automation_config = builder.build()

            # Run automation with controller
            engine = WebAutomationEngine(automation_config, self.controller)
            
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

            # Check for STOP_AUTOMATION failures (only if no tasks were created)
            errors = results.get('errors', [])
            stop_automation_failure = False
            if errors:
                error_msg = '; '.join([err.get('error', 'Unknown error') for err in errors[:3]])
                # Check if any error is from STOP_AUTOMATION, but only consider it failure if no tasks created
                for error in errors:
                    error_text = error.get('error', '').lower()
                    if ('stop_automation' in error_text or 'automation stopped' in error_text):
                        # Only consider STOP_AUTOMATION a failure if no tasks were created
                        if tasks_created == 0:
                            stop_automation_failure = True
                        break

            # Force failure if STOP_AUTOMATION was triggered with 0 tasks created
            if stop_automation_failure:
                result = AutomationResult.FAILURE
                message = "Automation failed - queue already full (0 tasks created)"
            else:
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
        except Exception:
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
        except Exception:
            return 0

    async def run_single_automation(self, config_file: str, attempt: int = 1) -> AutomationRun:
        """Run a single automation with enhanced control support"""
        run = AutomationRun(
            config_file=config_file,
            start_time=datetime.now(),
            attempt_number=attempt
        )

        try:
            # Check if scheduler should stop before starting
            if self.should_stop:
                run.finish(AutomationResult.ERROR, 0, "Scheduler stopped")
                return run
            
            # Setup controller if available
            if self.controller:
                self.controller.start_automation()
                self.controller.save_checkpoint(
                    config_name=Path(config_file).stem,
                    action_index=0,
                    variables={},
                    execution_context={"attempt": attempt, "config_file": config_file}
                )
            
            self.logger.info(f"🚀 Starting automation: {config_file} (attempt {attempt})")
            
            # Create automation task
            if self.config.use_cli:
                automation_coro = self.run_automation_cli(
                    config_file, self.config.timeout_seconds
                )
            else:
                automation_coro = self.run_automation_direct(
                    config_file, self.config.timeout_seconds
                )
            
            self.current_automation_task = asyncio.create_task(automation_coro)
            
            # Wait for automation with control support
            result, tasks_created, message = await self._run_with_control(self.current_automation_task)
            
            # Record results
            run.finish(result, tasks_created, message)
            
            # Log results
            if result == AutomationResult.SUCCESS:
                self.logger.info(f"✅ SUCCESS: {config_file} - {tasks_created} tasks created")
            else:
                self.logger.warning(f"❌ {result.value.upper()}: {config_file} - {message}")

        except Exception as e:
            run.finish(AutomationResult.ERROR, 0, str(e))
            self.logger.error(f"💥 Exception in automation {config_file}: {e}")
        finally:
            self.current_automation_task = None
            if self.controller:
                self.controller.cleanup_checkpoints(Path(config_file).stem)

        self.runs.append(run)
        return run

    async def wait_with_countdown(self, wait_seconds: int, reason: str):
        """Wait with countdown display and control support"""
        self.logger.info(f"⏳ Waiting {wait_seconds} seconds ({reason})...")
        
        if wait_seconds <= 0:
            return

        # Show countdown for waits longer than 10 seconds with control support
        if wait_seconds > 10:
            for remaining in range(wait_seconds, 0, -1):
                # Check for stop signal
                if self.should_stop:
                    self.logger.info(f"🛑 Wait interrupted by stop signal")
                    break
                
                # Handle pause
                if self.is_paused:
                    self.logger.info(f"⏸️ Wait paused at {remaining}s remaining")
                    await self._wait_for_resume()
                    self.logger.info(f"▶️ Wait resumed with {remaining}s remaining")
                
                if remaining % 60 == 0 or remaining <= 10:
                    mins, secs = divmod(remaining, 60)
                    if mins > 0:
                        self.logger.info(f"⏳ {mins}m {secs}s remaining...")
                    else:
                        self.logger.info(f"⏳ {secs}s remaining...")
                
                await asyncio.sleep(1)
        else:
            # For shorter waits, just sleep with periodic control checks
            elapsed = 0
            while elapsed < wait_seconds:
                if self.should_stop:
                    break
                
                if self.is_paused:
                    await self._wait_for_resume()
                
                sleep_time = min(1, wait_seconds - elapsed)
                await asyncio.sleep(sleep_time)
                elapsed += sleep_time

    async def process_config_file(self, config_file: str) -> bool:
        """Process a single config file with retry logic and control support"""
        self.logger.info(f"📁 Processing configuration: {config_file}")
        
        for attempt in range(1, self.config.max_retries + 1):
            # Check if scheduler should stop
            if self.should_stop:
                self.logger.info(f"🛑 Stopping processing of {config_file} due to scheduler stop")
                break
            
            # Handle pause state
            await self._handle_pause_state(f"before processing {config_file} (attempt {attempt})")
            
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
        """Main scheduler execution loop with enhanced control"""
        # Wait for scheduled time if specified
        await self._wait_for_scheduled_time()
        
        self.logger.info("🎬 Starting Automation Scheduler")
        self.logger.info(f"📋 Configurations to process: {len(self.config.config_files)}")
        self.logger.info(f"⏱️  Success wait time: {self.config.success_wait_time}s")
        self.logger.info(f"🔄 Failure wait time: {self.config.failure_wait_time}s")
        self.logger.info(f"🎯 Max retries per config: {self.config.max_retries}")
        self.logger.info(f"🎮 Control: Ctrl+W=Pause/Resume, Ctrl+T=Stop")
        
        # Start keyboard monitoring
        if self.keyboard_handler:
            self.keyboard_handler.start_monitoring()

        start_time = datetime.now()
        successful_configs = 0

        try:
            for i, config_file in enumerate(self.config.config_files):
                self.current_config_index = i
                
                # Check if scheduler should stop
                if self.should_stop:
                    self.logger.info(f"🛑 Scheduler stopped at configuration {i+1}/{len(self.config.config_files)}")
                    break
                
                # Handle pause state
                await self._handle_pause_state(f"before configuration {i+1}/{len(self.config.config_files)}")
                
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

        finally:
            # Stop keyboard monitoring
            if self.keyboard_handler:
                self.keyboard_handler.stop_monitoring()

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

    # Control Methods
    
    def pause_scheduler(self):
        """Pause the scheduler"""
        if not self.is_paused:
            self.is_paused = True
            self.logger.info("⏸️ Scheduler paused - press Ctrl+W to resume")
            if self.controller:
                self.controller.pause_automation()
        else:
            self.resume_scheduler()
    
    def resume_scheduler(self):
        """Resume the scheduler"""
        if self.is_paused:
            self.is_paused = False
            self.logger.info("▶️ Scheduler resumed")
            if self.controller:
                self.controller.resume_automation()
    
    def stop_scheduler(self, emergency: bool = False):
        """Stop the scheduler"""
        self.should_stop = True
        if emergency:
            self.logger.warning("🚨 Emergency stop requested")
        else:
            self.logger.info("🛑 Graceful stop requested")
        
        # Cancel current automation task
        if self.current_automation_task and not self.current_automation_task.done():
            self.current_automation_task.cancel()
        
        if self.controller:
            self.controller.stop_automation(emergency=emergency)
        
        # Resume if paused to allow stop processing
        if self.is_paused:
            self.is_paused = False
    
    def _print_status(self):
        """Print current scheduler status"""
        status = self.get_status()
        print("\n" + "="*50)
        print("📊 SCHEDULER STATUS")
        print("="*50)
        print(f"State: {'🟢 Running' if not self.is_paused and not self.should_stop else '⏸️ Paused' if self.is_paused else '🛑 Stopping'}")
        print(f"Config: {self.current_config_index + 1}/{len(self.config.config_files)}")
        print(f"Total Runs: {len(self.runs)}")
        print(f"Success Rate: {sum(1 for run in self.runs if run.result == AutomationResult.SUCCESS)}/{len(self.runs)}")
        if self.controller and status.get('automation'):
            auto_status = status['automation']
            if auto_status['progress']['total'] > 0:
                print(f"Current Progress: {auto_status['progress']['completed']}/{auto_status['progress']['total']} ({auto_status['progress']['percentage']:.1f}%)")
        print("="*50)
    
    async def _handle_pause_state(self, context: str = ""):
        """Handle pause state with context information"""
        if self.is_paused:
            self.logger.info(f"⏸️ Scheduler paused {context}")
            await self._wait_for_resume()
            self.logger.info(f"▶️ Scheduler resumed {context}")
    
    async def _wait_for_resume(self):
        """Wait for scheduler to be resumed"""
        while self.is_paused and not self.should_stop:
            await asyncio.sleep(0.5)
    
    async def _run_with_control(self, automation_task: asyncio.Task):
        """Run automation task with control signal monitoring"""
        try:
            # Wait for either automation completion or control signals
            while not automation_task.done():
                if self.should_stop:
                    automation_task.cancel()
                    try:
                        await automation_task
                    except asyncio.CancelledError:
                        pass
                    return AutomationResult.ERROR, 0, "Stopped by scheduler"
                
                if self.is_paused:
                    # Automation will handle its own pausing through controller
                    await self._wait_for_resume()
                
                # Check every 100ms
                await asyncio.sleep(0.1)
            
            # Get automation result
            return await automation_task
            
        except asyncio.CancelledError:
            return AutomationResult.ERROR, 0, "Cancelled"
        except Exception as e:
            return AutomationResult.ERROR, 0, str(e)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        controller_status = self.controller.get_status() if self.controller else None
        
        return {
            "scheduler": {
                "is_paused": self.is_paused,
                "should_stop": self.should_stop,
                "current_config_index": self.current_config_index,
                "total_configs": len(self.config.config_files),
                "total_runs": len(self.runs)
            },
            "automation": controller_status,
            "config": {
                "success_wait_time": self.config.success_wait_time,
                "failure_wait_time": self.config.failure_wait_time,
                "max_retries": self.config.max_retries,
                "use_cli": self.config.use_cli,
                "scheduled_time": self.config.scheduled_time,
                "scheduled_date": self.config.scheduled_date
            }
        }
    
    async def _wait_for_scheduled_time(self):
        """Wait until the scheduled time to start automation"""
        if not self.config.scheduled_time and not self.config.scheduled_date:
            return
        
        try:
            now = datetime.now()
            
            # Parse scheduled date and time
            if self.config.scheduled_date:
                # Parse date in YYYY-MM-dd format
                scheduled_date = datetime.strptime(self.config.scheduled_date, "%Y-%m-%d").date()
            else:
                # Use today's date if no date specified
                scheduled_date = now.date()
            
            if self.config.scheduled_time:
                # Parse time in HH:mm:ss format
                time_parts = self.config.scheduled_time.split(':')
                if len(time_parts) == 3:
                    hour, minute, second = map(int, time_parts)
                elif len(time_parts) == 2:
                    hour, minute = map(int, time_parts)
                    second = 0
                else:
                    raise ValueError(f"Invalid time format: {self.config.scheduled_time}. Use HH:mm:ss or HH:mm")
                
                # Create scheduled datetime
                scheduled_datetime = datetime.combine(scheduled_date, datetime.min.time())
                scheduled_datetime = scheduled_datetime.replace(hour=hour, minute=minute, second=second)
            else:
                # If only date is specified, start at midnight
                scheduled_datetime = datetime.combine(scheduled_date, datetime.min.time())
            
            # Calculate wait time
            wait_seconds = (scheduled_datetime - now).total_seconds()
            
            if wait_seconds <= 0:
                self.logger.info(f"⚠️  Scheduled time {scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S')} has already passed. Starting immediately.")
                return
            
            self.logger.info(f"⏰ Scheduler will start at: {scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"⏳ Waiting {self._format_duration(wait_seconds)} until scheduled time...")
            
            # Show countdown for long waits
            if wait_seconds > 60:
                # Check every minute and update countdown
                while wait_seconds > 0:
                    # Check for stop signal
                    if self.should_stop:
                        self.logger.info(f"🛑 Scheduled wait interrupted by stop signal")
                        return
                    
                    # Handle pause
                    if self.is_paused:
                        self.logger.info(f"⏸️ Scheduled wait paused")
                        await self._wait_for_resume()
                        self.logger.info(f"▶️ Scheduled wait resumed")
                        # Recalculate wait time after resume
                        now = datetime.now()
                        wait_seconds = (scheduled_datetime - now).total_seconds()
                        if wait_seconds <= 0:
                            break
                    
                    # Display countdown
                    if wait_seconds > 3600:
                        # For waits longer than an hour, check every 5 minutes
                        sleep_time = min(300, wait_seconds)
                    elif wait_seconds > 600:
                        # For waits longer than 10 minutes, check every minute
                        sleep_time = min(60, wait_seconds)
                    else:
                        # For shorter waits, check every 10 seconds
                        sleep_time = min(10, wait_seconds)
                    
                    await asyncio.sleep(sleep_time)
                    
                    # Update remaining time
                    now = datetime.now()
                    wait_seconds = (scheduled_datetime - now).total_seconds()
                    
                    # Show periodic updates
                    if wait_seconds > 0:
                        if int(wait_seconds) % 300 == 0 or wait_seconds <= 60:
                            self.logger.info(f"⏳ {self._format_duration(wait_seconds)} remaining until scheduled start...")
            else:
                # For short waits, just sleep
                await asyncio.sleep(wait_seconds)
            
            self.logger.info(f"✅ Scheduled time reached. Starting automation...")
            
        except ValueError as e:
            self.logger.error(f"❌ Invalid scheduled time or date format: {e}")
            self.logger.error("Use --time HH:mm:ss for time and --date YYYY-MM-dd for date")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error processing scheduled time: {e}")
            raise


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
            verbose=config_data.get('verbose', True),
            scheduled_time=config_data.get('scheduled_time', None),
            scheduled_date=config_data.get('scheduled_date', None)
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
        "verbose": True,           # Detailed logging
        "scheduled_time": None,    # Optional: Time to start (HH:mm:ss)
        "scheduled_date": None     # Optional: Date to start (YYYY-MM-dd)
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
    parser.add_argument('--start-from', type=int, metavar='INDEX', help='Start from specified config file index (1-indexed, e.g., --start-from 3 starts from the 3rd config)')
    parser.add_argument('--time', type=str, metavar='HH:MM:SS', help='Schedule start time (e.g., 14:30:00 for 2:30 PM). Defaults to current day if --date not specified')
    parser.add_argument('--date', type=str, metavar='YYYY-MM-DD', help='Schedule start date (e.g., 2024-12-25). Used with --time for specific datetime')

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
            sys.exit(1)
        config = load_scheduler_config(args.config)
        # Override scheduled time/date from command line if provided
        if args.time:
            config.scheduled_time = args.time
        if args.date:
            config.scheduled_date = args.date
    elif args.configs:
        config = SchedulerConfig(
            config_files=args.configs,
            success_wait_time=args.success_wait,
            failure_wait_time=args.failure_wait,
            max_retries=args.max_retries,
            timeout_seconds=args.timeout,
            log_file=args.log_file,
            use_cli=not args.use_direct,
            verbose=not args.quiet,
            scheduled_time=args.time,
            scheduled_date=args.date
        )
    else:
        print("Error: Must specify either --config or --configs")
        print("Use --help for usage information or --create-example for example configuration.")
        sys.exit(1)
    
    # Validate scheduled time and date formats if provided
    if args.time:
        try:
            # Validate time format
            time_parts = args.time.split(':')
            if len(time_parts) not in [2, 3]:
                raise ValueError("Time must be in HH:MM or HH:MM:SS format")
            hour, minute = int(time_parts[0]), int(time_parts[1])
            if hour < 0 or hour > 23:
                raise ValueError("Hour must be between 0 and 23")
            if minute < 0 or minute > 59:
                raise ValueError("Minute must be between 0 and 59")
            if len(time_parts) == 3:
                second = int(time_parts[2])
                if second < 0 or second > 59:
                    raise ValueError("Second must be between 0 and 59")
        except ValueError as e:
            print(f"Error: Invalid time format '{args.time}': {e}")
            print("Use format HH:MM:SS (e.g., 14:30:00) or HH:MM (e.g., 14:30)")
            sys.exit(1)
    
    if args.date:
        try:
            # Validate date format
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'")
            print("Use format YYYY-MM-DD (e.g., 2024-12-25)")
            sys.exit(1)

    # Apply start-from filtering if specified
    if args.start_from is not None:
        start_index = args.start_from - 1  # Convert from 1-indexed to 0-indexed
        
        # Validate start index bounds
        if start_index < 0:
            print(f"Error: --start-from index must be 1 or greater (got {args.start_from})")
            sys.exit(1)
        elif start_index >= len(config.config_files):
            print(f"Error: --start-from index {args.start_from} is beyond the number of config files ({len(config.config_files)})")
            print(f"Available config files (1-{len(config.config_files)}):")
            for i, cf in enumerate(config.config_files, 1):
                print(f"  {i}. {cf}")
            sys.exit(1)
        
        # Filter config files to start from specified index
        original_count = len(config.config_files)
        config.config_files = config.config_files[start_index:]
        print(f"📍 Starting from config {args.start_from}/{original_count}: {config.config_files[0]}")
        print(f"📋 Processing {len(config.config_files)} config files (skipping first {start_index})")

    # Validate configuration files exist
    missing_files = [f for f in config.config_files if not Path(f).exists()]
    if missing_files:
        print(f"Error: Configuration files not found: {missing_files}")
        sys.exit(1)

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