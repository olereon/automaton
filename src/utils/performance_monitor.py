#!/usr/bin/env python3
"""
Performance monitoring utilities for Automaton
Tracks execution times, resource usage, and optimization opportunities
"""

import time
import asyncio
import psutil
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    action_type: str
    execution_time: float
    memory_usage_mb: float
    cpu_percent: float
    success: bool
    timestamp: float
    details: Optional[str] = None

class PerformanceMonitor:
    """Monitor and track automation performance"""
    
    def __init__(self, enable_monitoring: bool = True):
        self.enable_monitoring = enable_monitoring
        self.metrics: List[PerformanceMetrics] = []
        self.session_start = time.time()
        
    @asynccontextmanager
    async def track_action(self, action_type: str, details: str = None):
        """Context manager to track action performance"""
        if not self.enable_monitoring:
            yield
            return
            
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        success = True
        try:
            yield
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent()
            
            metrics = PerformanceMetrics(
                action_type=action_type,
                execution_time=execution_time,
                memory_usage_mb=end_memory - start_memory,
                cpu_percent=(start_cpu + end_cpu) / 2,
                success=success,
                timestamp=end_time,
                details=details
            )
            
            self.metrics.append(metrics)
            
            # Log performance info
            if execution_time > 5.0:  # Warn for slow operations
                logger.warning(f"⚠️ Slow operation detected: {action_type} took {execution_time:.2f}s")
            else:
                logger.info(f"⚡ {action_type}: {execution_time:.2f}s")
    
    def get_summary(self) -> Dict:
        """Get performance summary statistics"""
        if not self.metrics:
            return {"status": "No metrics collected"}
        
        total_time = sum(m.execution_time for m in self.metrics)
        avg_time = total_time / len(self.metrics)
        max_time = max(m.execution_time for m in self.metrics)
        min_time = min(m.execution_time for m in self.metrics)
        
        success_rate = sum(1 for m in self.metrics if m.success) / len(self.metrics) * 100
        
        # Group by action type
        by_action = {}
        for metric in self.metrics:
            if metric.action_type not in by_action:
                by_action[metric.action_type] = []
            by_action[metric.action_type].append(metric)
        
        action_stats = {}
        for action_type, action_metrics in by_action.items():
            action_stats[action_type] = {
                "count": len(action_metrics),
                "avg_time": sum(m.execution_time for m in action_metrics) / len(action_metrics),
                "total_time": sum(m.execution_time for m in action_metrics),
                "success_rate": sum(1 for m in action_metrics if m.success) / len(action_metrics) * 100
            }
        
        return {
            "session_duration": time.time() - self.session_start,
            "total_actions": len(self.metrics),
            "total_execution_time": total_time,
            "average_time_per_action": avg_time,
            "max_action_time": max_time,
            "min_action_time": min_time,
            "success_rate": success_rate,
            "action_breakdown": action_stats,
            "slowest_actions": [
                {
                    "type": m.action_type,
                    "time": m.execution_time,
                    "details": m.details
                }
                for m in sorted(self.metrics, key=lambda x: x.execution_time, reverse=True)[:5]
            ]
        }
    
    def save_report(self, filepath: str):
        """Save performance report to file"""
        summary = self.get_summary()
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📊 Performance report saved to: {filepath}")
    
    def log_summary(self):
        """Log performance summary"""
        summary = self.get_summary()
        
        logger.info("📊 PERFORMANCE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Session Duration: {summary.get('session_duration', 0):.2f}s")
        logger.info(f"Total Actions: {summary.get('total_actions', 0)}")
        logger.info(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        logger.info(f"Average Time per Action: {summary.get('average_time_per_action', 0):.2f}s")
        logger.info(f"Total Execution Time: {summary.get('total_execution_time', 0):.2f}s")
        
        if 'slowest_actions' in summary:
            logger.info("\n🐌 Slowest Actions:")
            for i, action in enumerate(summary['slowest_actions'][:3], 1):
                logger.info(f"  {i}. {action['type']}: {action['time']:.2f}s")
        
        if 'action_breakdown' in summary:
            logger.info("\n📋 Action Breakdown:")
            for action_type, stats in summary['action_breakdown'].items():
                logger.info(f"  {action_type}: {stats['count']} actions, {stats['avg_time']:.2f}s avg")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def enable_monitoring():
    """Enable performance monitoring"""
    global performance_monitor
    performance_monitor.enable_monitoring = True

def disable_monitoring():
    """Disable performance monitoring"""
    global performance_monitor
    performance_monitor.enable_monitoring = False

def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor

@asynccontextmanager
async def track_performance(action_type: str, details: str = None):
    """Convenience function for tracking performance"""
    async with performance_monitor.track_action(action_type, details):
        yield