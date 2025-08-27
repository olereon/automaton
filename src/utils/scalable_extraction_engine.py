#!/usr/bin/env python3
"""
Scalable Extraction Engine for High-Volume Processing

This module provides enterprise-grade scalability features including concurrent
processing, load balancing, distributed coordination, and resource management
for large-scale metadata extraction operations.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from pathlib import Path
import weakref
import queue
from functools import partial

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Processing modes for different scales"""
    SINGLE_THREADED = "single_threaded"      # Basic sequential processing
    MULTI_THREADED = "multi_threaded"       # Thread-based concurrency
    MULTI_PROCESS = "multi_process"         # Process-based parallelism
    DISTRIBUTED = "distributed"             # Distributed across multiple nodes
    HYBRID = "hybrid"                       # Adaptive hybrid approach


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    WEIGHTED = "weighted"
    LOCALITY_AWARE = "locality_aware"
    ADAPTIVE = "adaptive"


class ResourceType(Enum):
    """Types of system resources to monitor"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DISK_IO = "disk_io"
    BROWSER_CONTEXTS = "browser_contexts"


@dataclass
class ProcessingNode:
    """Represents a processing node in the scalable system"""
    node_id: str
    capacity: int
    current_load: int = 0
    active_tasks: Set[str] = field(default_factory=set)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    resource_usage: Dict[ResourceType, float] = field(default_factory=dict)
    
    def get_load_percentage(self) -> float:
        """Get current load as percentage of capacity"""
        return (self.current_load / self.capacity) * 100 if self.capacity > 0 else 100
    
    def can_accept_task(self, task_weight: int = 1) -> bool:
        """Check if node can accept a new task"""
        return self.current_load + task_weight <= self.capacity
    
    def add_task(self, task_id: str, weight: int = 1) -> bool:
        """Add a task to this node"""
        if self.can_accept_task(weight):
            self.active_tasks.add(task_id)
            self.current_load += weight
            return True
        return False
    
    def remove_task(self, task_id: str, weight: int = 1) -> bool:
        """Remove a task from this node"""
        if task_id in self.active_tasks:
            self.active_tasks.remove(task_id)
            self.current_load = max(0, self.current_load - weight)
            return True
        return False


@dataclass
class ExtractionTask:
    """Represents a metadata extraction task"""
    task_id: str
    page_url: str
    extraction_config: Dict[str, Any]
    priority: int = 5  # 1-10, 10 being highest
    weight: int = 1    # Resource weight
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    assigned_node: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'task_id': self.task_id,
            'page_url': self.page_url,
            'extraction_config': self.extraction_config,
            'priority': self.priority,
            'weight': self.weight,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'assigned_node': self.assigned_node,
            'status': self.status,
            'result': self.result,
            'error': self.error
        }


class ResourceMonitor:
    """Monitors system resources and provides usage metrics"""
    
    def __init__(self, monitor_interval: int = 10):
        self.monitor_interval = monitor_interval
        self.resource_history: Dict[ResourceType, List[Tuple[datetime, float]]] = {
            resource: [] for resource in ResourceType
        }
        self.monitoring_active = False
        self.alert_thresholds = {
            ResourceType.CPU: 80.0,
            ResourceType.MEMORY: 85.0,
            ResourceType.NETWORK: 90.0,
            ResourceType.DISK_IO: 75.0,
            ResourceType.BROWSER_CONTEXTS: 90.0
        }
        self.alert_callbacks = []
    
    async def start_monitoring(self):
        """Start resource monitoring loop"""
        self.monitoring_active = True
        while self.monitoring_active:
            await self._collect_metrics()
            await asyncio.sleep(self.monitor_interval)
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
    
    async def _collect_metrics(self):
        """Collect current resource metrics"""
        try:
            metrics = await self._get_system_metrics()
            current_time = datetime.now()
            
            for resource_type, value in metrics.items():
                # Store in history
                history = self.resource_history[resource_type]
                history.append((current_time, value))
                
                # Limit history size (keep last 1000 entries)
                if len(history) > 1000:
                    self.resource_history[resource_type] = history[-500:]
                
                # Check alert thresholds
                threshold = self.alert_thresholds.get(resource_type, 90.0)
                if value > threshold:
                    await self._trigger_alert(resource_type, value, threshold)
                    
        except Exception as e:
            logger.warning(f"Error collecting resource metrics: {e}")
    
    async def _get_system_metrics(self) -> Dict[ResourceType, float]:
        """Get current system resource usage"""
        metrics = {}
        
        try:
            import psutil
            
            # CPU usage
            metrics[ResourceType.CPU] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics[ResourceType.MEMORY] = memory.percent
            
            # Network usage (simplified)
            net_io = psutil.net_io_counters()
            metrics[ResourceType.NETWORK] = min(100.0, (net_io.bytes_sent + net_io.bytes_recv) / (1024**3))  # GB
            
            # Disk I/O usage (simplified)
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics[ResourceType.DISK_IO] = min(100.0, (disk_io.read_bytes + disk_io.write_bytes) / (1024**3))  # GB
            else:
                metrics[ResourceType.DISK_IO] = 0.0
                
        except ImportError:
            # Fallback metrics without psutil
            logger.warning("psutil not available, using simplified metrics")
            metrics = {
                ResourceType.CPU: 50.0,
                ResourceType.MEMORY: 60.0,
                ResourceType.NETWORK: 30.0,
                ResourceType.DISK_IO: 40.0
            }
        
        # Browser contexts (would be provided by browser manager)
        metrics[ResourceType.BROWSER_CONTEXTS] = 0.0
        
        return metrics
    
    async def _trigger_alert(self, resource_type: ResourceType, current_value: float, threshold: float):
        """Trigger resource usage alert"""
        alert = {
            'type': 'resource_alert',
            'resource': resource_type.value,
            'current_value': current_value,
            'threshold': threshold,
            'timestamp': datetime.now().isoformat(),
            'severity': 'high' if current_value > threshold * 1.2 else 'medium'
        }
        
        logger.warning(f"Resource alert: {resource_type.value} at {current_value:.1f}% (threshold: {threshold:.1f}%)")
        
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def get_current_usage(self, resource_type: ResourceType) -> Optional[float]:
        """Get current resource usage"""
        history = self.resource_history.get(resource_type, [])
        return history[-1][1] if history else None
    
    def get_average_usage(self, resource_type: ResourceType, 
                         duration_minutes: int = 30) -> Optional[float]:
        """Get average resource usage over specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        history = self.resource_history.get(resource_type, [])
        
        recent_values = [value for timestamp, value in history if timestamp > cutoff_time]
        return sum(recent_values) / len(recent_values) if recent_values else None


class LoadBalancer:
    """Intelligent load balancer for processing nodes"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE):
        self.strategy = strategy
        self.nodes: Dict[str, ProcessingNode] = {}
        self.task_history: List[Tuple[str, str, datetime]] = []  # (task_id, node_id, timestamp)
        self.performance_weights: Dict[str, float] = {}
        
    def register_node(self, node: ProcessingNode):
        """Register a processing node"""
        self.nodes[node.node_id] = node
        self.performance_weights[node.node_id] = 1.0
        logger.info(f"Registered processing node: {node.node_id} (capacity: {node.capacity})")
    
    def unregister_node(self, node_id: str):
        """Unregister a processing node"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.performance_weights.pop(node_id, None)
            logger.info(f"Unregistered processing node: {node_id}")
    
    def select_node(self, task: ExtractionTask) -> Optional[ProcessingNode]:
        """Select optimal node for task based on load balancing strategy"""
        available_nodes = [node for node in self.nodes.values() 
                          if node.can_accept_task(task.weight)]
        
        if not available_nodes:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_nodes)
        
        elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._select_least_loaded(available_nodes)
        
        elif self.strategy == LoadBalancingStrategy.WEIGHTED:
            return self._select_weighted(available_nodes)
        
        elif self.strategy == LoadBalancingStrategy.LOCALITY_AWARE:
            return self._select_locality_aware(available_nodes, task)
        
        elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
            return self._select_adaptive(available_nodes, task)
        
        # Fallback to least loaded
        return self._select_least_loaded(available_nodes)
    
    def _select_round_robin(self, nodes: List[ProcessingNode]) -> ProcessingNode:
        """Round-robin node selection"""
        # Simple implementation - use task history length as round-robin counter
        index = len(self.task_history) % len(nodes)
        return nodes[index]
    
    def _select_least_loaded(self, nodes: List[ProcessingNode]) -> ProcessingNode:
        """Select node with lowest current load"""
        return min(nodes, key=lambda n: n.get_load_percentage())
    
    def _select_weighted(self, nodes: List[ProcessingNode]) -> ProcessingNode:
        """Select node based on performance weights"""
        weighted_scores = []
        for node in nodes:
            weight = self.performance_weights.get(node.node_id, 1.0)
            load_factor = 1.0 - (node.get_load_percentage() / 100.0)
            score = weight * load_factor
            weighted_scores.append((node, score))
        
        return max(weighted_scores, key=lambda x: x[1])[0]
    
    def _select_locality_aware(self, nodes: List[ProcessingNode], 
                              task: ExtractionTask) -> ProcessingNode:
        """Select node based on locality (e.g., previous tasks from same domain)"""
        # Check if any node has processed tasks from the same domain recently
        task_domain = self._extract_domain(task.page_url)
        
        domain_experienced_nodes = []
        for node in nodes:
            recent_tasks = [task_id for task_id, node_id, timestamp in self.task_history[-100:]
                          if node_id == node.node_id and 
                          timestamp > datetime.now() - timedelta(hours=1)]
            
            # This would need task URL tracking in real implementation
            if recent_tasks:  # Simplified locality check
                domain_experienced_nodes.append(node)
        
        if domain_experienced_nodes:
            return self._select_least_loaded(domain_experienced_nodes)
        
        return self._select_least_loaded(nodes)
    
    def _select_adaptive(self, nodes: List[ProcessingNode], 
                        task: ExtractionTask) -> ProcessingNode:
        """Adaptive node selection based on multiple factors"""
        node_scores = []
        
        for node in nodes:
            # Base score from load
            load_score = 1.0 - (node.get_load_percentage() / 100.0)
            
            # Performance weight
            perf_weight = self.performance_weights.get(node.node_id, 1.0)
            
            # Recent success rate (simplified)
            recent_tasks = len([1 for _, node_id, timestamp in self.task_history[-50:]
                              if node_id == node.node_id])
            success_factor = min(1.0, recent_tasks / 10.0) if recent_tasks else 0.5
            
            # Resource availability factor
            resource_factor = 1.0
            for resource, usage in node.resource_usage.items():
                if usage > 80:
                    resource_factor *= 0.8
                elif usage > 60:
                    resource_factor *= 0.9
            
            # Priority bonus for high-priority tasks
            priority_bonus = 1.0 + (task.priority / 20.0)  # Up to 50% bonus
            
            combined_score = (load_score * 0.3 + 
                            perf_weight * 0.25 + 
                            success_factor * 0.2 + 
                            resource_factor * 0.15 + 
                            priority_bonus * 0.1)
            
            node_scores.append((node, combined_score))
        
        return max(node_scores, key=lambda x: x[1])[0]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for locality awareness"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return "unknown"
    
    def record_task_assignment(self, task_id: str, node_id: str):
        """Record task assignment for load balancing decisions"""
        self.task_history.append((task_id, node_id, datetime.now()))
        
        # Limit history size
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-500:]
    
    def update_node_performance(self, node_id: str, performance_metrics: Dict[str, float]):
        """Update node performance metrics"""
        if node_id in self.nodes:
            self.nodes[node_id].performance_metrics.update(performance_metrics)
            
            # Update performance weight based on success rate and speed
            success_rate = performance_metrics.get('success_rate', 50.0) / 100.0
            avg_time = performance_metrics.get('avg_execution_time', 5.0)
            
            # Better success rate and faster execution = higher weight
            weight = success_rate * (10.0 / max(1.0, avg_time))
            self.performance_weights[node_id] = max(0.1, min(2.0, weight))


class ScalableExtractionEngine:
    """Main scalable extraction engine with enterprise features"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.processing_mode = ProcessingMode(self.config.get('processing_mode', 'multi_threaded'))
        
        # Core components
        self.load_balancer = LoadBalancer(
            LoadBalancingStrategy(self.config.get('load_balancing_strategy', 'adaptive'))
        )
        self.resource_monitor = ResourceMonitor(
            self.config.get('resource_monitor_interval', 10)
        )
        
        # Task management
        self.task_queue = asyncio.Queue(maxsize=self.config.get('max_queue_size', 10000))
        self.completed_tasks: Dict[str, ExtractionTask] = {}
        self.failed_tasks: Dict[str, ExtractionTask] = {}
        
        # Processing pools
        self.max_workers = self.config.get('max_workers', min(32, mp.cpu_count() * 4))
        self.thread_executor = None
        self.process_executor = None
        
        # State management
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.statistics = {
            'tasks_processed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'throughput_per_minute': 0.0,
            'start_time': None
        }
    
    async def start(self):
        """Start the scalable extraction engine"""
        if self.is_running:
            logger.warning("Engine is already running")
            return
        
        self.is_running = True
        self.statistics['start_time'] = datetime.now()
        
        logger.info(f"Starting scalable extraction engine in {self.processing_mode.value} mode")
        
        # Initialize processing pools
        await self._initialize_processing_pools()
        
        # Start resource monitoring
        asyncio.create_task(self.resource_monitor.start_monitoring())
        
        # Start worker tasks
        num_workers = min(self.max_workers, self.config.get('concurrent_workers', 8))
        for i in range(num_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker_{i}"))
            self.worker_tasks.append(worker_task)
        
        # Start statistics updater
        asyncio.create_task(self._update_statistics_loop())
        
        logger.info(f"Engine started with {num_workers} workers")
    
    async def stop(self):
        """Stop the scalable extraction engine"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping scalable extraction engine")
        
        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for workers to finish current tasks
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Shutdown processing pools
        await self._shutdown_processing_pools()
        
        # Log final statistics
        await self._log_final_statistics()
        
        logger.info("Engine stopped")
    
    async def _initialize_processing_pools(self):
        """Initialize processing pools based on mode"""
        if self.processing_mode in [ProcessingMode.MULTI_THREADED, ProcessingMode.HYBRID]:
            self.thread_executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="extraction_thread"
            )
        
        if self.processing_mode in [ProcessingMode.MULTI_PROCESS, ProcessingMode.HYBRID]:
            self.process_executor = ProcessPoolExecutor(
                max_workers=min(self.max_workers, mp.cpu_count()),
                mp_context=mp.get_context('spawn')
            )
    
    async def _shutdown_processing_pools(self):
        """Shutdown processing pools"""
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)
            self.thread_executor = None
        
        if self.process_executor:
            self.process_executor.shutdown(wait=True)
            self.process_executor = None
    
    async def submit_task(self, page_url: str, extraction_config: Dict[str, Any], 
                         priority: int = 5, max_retries: int = 3) -> str:
        """Submit a new extraction task"""
        task = ExtractionTask(
            task_id=str(uuid.uuid4()),
            page_url=page_url,
            extraction_config=extraction_config,
            priority=priority,
            max_retries=max_retries
        )
        
        await self.task_queue.put(task)
        logger.debug(f"Submitted task {task.task_id} for {page_url}")
        return task.task_id
    
    async def submit_batch_tasks(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Submit multiple tasks in batch"""
        task_ids = []
        
        for task_data in tasks:
            task_id = await self.submit_task(
                page_url=task_data['page_url'],
                extraction_config=task_data.get('extraction_config', {}),
                priority=task_data.get('priority', 5),
                max_retries=task_data.get('max_retries', 3)
            )
            task_ids.append(task_id)
        
        logger.info(f"Submitted batch of {len(task_ids)} tasks")
        return task_ids
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result of a completed task"""
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].result
        elif task_id in self.failed_tasks:
            return {
                'error': self.failed_tasks[task_id].error,
                'task_id': task_id,
                'status': 'failed'
            }
        return None
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a task"""
        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                'task_id': task_id,
                'status': 'completed',
                'result': task.result,
                'processing_time': task.result.get('processing_time') if task.result else None
            }
        
        # Check failed tasks
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': task.error,
                'retry_count': task.retry_count
            }
        
        # Task might be in queue or processing
        return {
            'task_id': task_id,
            'status': 'processing_or_queued',
            'message': 'Task is either queued or currently being processed'
        }
    
    async def _worker_loop(self, worker_id: str):
        """Main worker loop for processing tasks"""
        logger.debug(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Process the task
                await self._process_task(task, worker_id)
                
            except asyncio.TimeoutError:
                # No task available, continue loop
                continue
            except asyncio.CancelledError:
                logger.debug(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                continue
        
        logger.debug(f"Worker {worker_id} stopped")
    
    async def _process_task(self, task: ExtractionTask, worker_id: str):
        """Process a single extraction task"""
        start_time = time.time()
        task.status = "processing"
        
        logger.debug(f"Worker {worker_id} processing task {task.task_id}")
        
        try:
            # Select processing method based on mode
            if self.processing_mode == ProcessingMode.SINGLE_THREADED:
                result = await self._process_task_async(task)
            
            elif self.processing_mode == ProcessingMode.MULTI_THREADED:
                result = await self._process_task_threaded(task)
            
            elif self.processing_mode == ProcessingMode.MULTI_PROCESS:
                result = await self._process_task_multiprocess(task)
            
            elif self.processing_mode == ProcessingMode.HYBRID:
                result = await self._process_task_adaptive(task)
            
            else:
                raise ValueError(f"Unsupported processing mode: {self.processing_mode}")
            
            # Task completed successfully
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            result['worker_id'] = worker_id
            result['processing_mode'] = self.processing_mode.value
            
            task.result = result
            task.status = "completed"
            self.completed_tasks[task.task_id] = task
            
            # Update statistics
            self.statistics['tasks_processed'] += 1
            self.statistics['total_processing_time'] += processing_time
            
            logger.debug(f"Task {task.task_id} completed in {processing_time:.2f}s")
            
        except Exception as e:
            # Task failed
            processing_time = time.time() - start_time
            task.error = str(e)
            task.retry_count += 1
            
            logger.warning(f"Task {task.task_id} failed: {e}")
            
            # Retry if possible
            if task.retry_count < task.max_retries:
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count + 1}/{task.max_retries})")
                task.status = "pending"
                await self.task_queue.put(task)
            else:
                task.status = "failed"
                self.failed_tasks[task.task_id] = task
                self.statistics['tasks_failed'] += 1
                
                logger.error(f"Task {task.task_id} failed permanently after {task.retry_count} attempts")
    
    async def _process_task_async(self, task: ExtractionTask) -> Dict[str, Any]:
        """Process task in single-threaded async mode"""
        # This would use the optimized extractor directly
        from .performance_optimized_extractor import PerformanceOptimizedExtractor
        
        # Create a mock page object for demonstration
        # In real implementation, this would create/manage browser page
        mock_page = type('MockPage', (), {
            'url': task.page_url,
            'query_selector_all': lambda self, selector: []
        })()
        
        extractor = PerformanceOptimizedExtractor(task.extraction_config)
        result = await extractor.extract_metadata_optimized(mock_page)
        
        return result
    
    async def _process_task_threaded(self, task: ExtractionTask) -> Dict[str, Any]:
        """Process task using thread executor"""
        loop = asyncio.get_event_loop()
        
        # Run extraction in thread pool
        result = await loop.run_in_executor(
            self.thread_executor,
            self._extract_sync,
            task
        )
        
        return result
    
    async def _process_task_multiprocess(self, task: ExtractionTask) -> Dict[str, Any]:
        """Process task using process executor"""
        loop = asyncio.get_event_loop()
        
        # Run extraction in process pool
        result = await loop.run_in_executor(
            self.process_executor,
            _extract_in_process,  # Global function for pickling
            task.to_dict()
        )
        
        return result
    
    async def _process_task_adaptive(self, task: ExtractionTask) -> Dict[str, Any]:
        """Adaptively choose processing method based on system state"""
        # Check system resources
        cpu_usage = self.resource_monitor.get_current_usage(ResourceType.CPU) or 50
        memory_usage = self.resource_monitor.get_current_usage(ResourceType.MEMORY) or 60
        
        # Decision logic
        if cpu_usage > 80 or memory_usage > 85:
            # High resource usage - use single-threaded
            return await self._process_task_async(task)
        
        elif task.priority >= 8:
            # High priority - use dedicated thread
            return await self._process_task_threaded(task)
        
        elif len(task.page_url) > 100:  # Complex URL indicating complex page
            # Complex task - use process isolation
            return await self._process_task_multiprocess(task)
        
        else:
            # Default to threaded
            return await self._process_task_threaded(task)
    
    def _extract_sync(self, task: ExtractionTask) -> Dict[str, Any]:
        """Synchronous extraction for thread execution"""
        # Simplified synchronous extraction
        return {
            'task_id': task.task_id,
            'extraction_method': 'threaded_sync',
            'generation_date': 'Unknown Date',
            'prompt': 'Unknown Prompt',
            'url': task.page_url
        }
    
    async def _update_statistics_loop(self):
        """Update engine statistics periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Calculate average processing time
                if self.statistics['tasks_processed'] > 0:
                    self.statistics['average_processing_time'] = (
                        self.statistics['total_processing_time'] / 
                        self.statistics['tasks_processed']
                    )
                
                # Calculate throughput
                if self.statistics['start_time']:
                    elapsed_minutes = (datetime.now() - self.statistics['start_time']).total_seconds() / 60
                    if elapsed_minutes > 0:
                        self.statistics['throughput_per_minute'] = (
                            self.statistics['tasks_processed'] / elapsed_minutes
                        )
                
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
    
    async def _log_final_statistics(self):
        """Log final engine statistics"""
        stats = self.get_engine_statistics()
        logger.info("Final engine statistics:")
        logger.info(f"  Tasks processed: {stats['tasks_processed']}")
        logger.info(f"  Tasks failed: {stats['tasks_failed']}")
        logger.info(f"  Average processing time: {stats['average_processing_time']:.2f}s")
        logger.info(f"  Throughput: {stats['throughput_per_minute']:.2f} tasks/minute")
        logger.info(f"  Success rate: {stats.get('success_rate', 0):.1f}%")
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics"""
        total_tasks = self.statistics['tasks_processed'] + self.statistics['tasks_failed']
        success_rate = (
            (self.statistics['tasks_processed'] / total_tasks * 100) 
            if total_tasks > 0 else 0
        )
        
        return {
            **self.statistics,
            'total_tasks': total_tasks,
            'success_rate': success_rate,
            'queue_size': self.task_queue.qsize(),
            'completed_tasks_count': len(self.completed_tasks),
            'failed_tasks_count': len(self.failed_tasks),
            'active_workers': len([t for t in self.worker_tasks if not t.done()]),
            'processing_mode': self.processing_mode.value,
            'resource_usage': {
                resource.value: self.resource_monitor.get_current_usage(resource)
                for resource in ResourceType
            }
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'queue_size': self.task_queue.qsize(),
            'max_queue_size': self.task_queue.maxsize,
            'queue_utilization': (self.task_queue.qsize() / self.task_queue.maxsize) * 100,
            'is_full': self.task_queue.full(),
            'estimated_processing_time_minutes': (
                self.task_queue.qsize() * self.statistics['average_processing_time'] / 60
                if self.statistics['average_processing_time'] > 0 else 0
            )
        }


# Global function for multiprocess execution
def _extract_in_process(task_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata in separate process (for process pool executor)"""
    # This would implement the actual extraction logic
    # For now, return mock result
    return {
        'task_id': task_dict['task_id'],
        'extraction_method': 'multiprocess',
        'generation_date': 'Unknown Date',
        'prompt': 'Unknown Prompt',
        'url': task_dict['page_url'],
        'process_id': mp.current_process().pid
    }


# Factory function for creating scalable engines
def create_scalable_engine(scale_level: str = "medium", 
                         custom_config: Dict[str, Any] = None) -> ScalableExtractionEngine:
    """
    Factory function to create appropriately configured scalable engines
    
    Scale levels:
    - small: Single-threaded, 4 workers, basic monitoring
    - medium: Multi-threaded, 8 workers, full monitoring  
    - large: Hybrid processing, 16 workers, advanced features
    - enterprise: Multi-process, 32+ workers, all features
    """
    
    base_configs = {
        'small': {
            'processing_mode': 'single_threaded',
            'max_workers': 4,
            'concurrent_workers': 2,
            'max_queue_size': 1000,
            'load_balancing_strategy': 'round_robin',
            'resource_monitor_interval': 30
        },
        'medium': {
            'processing_mode': 'multi_threaded',
            'max_workers': 8,
            'concurrent_workers': 4,
            'max_queue_size': 5000,
            'load_balancing_strategy': 'least_loaded',
            'resource_monitor_interval': 15
        },
        'large': {
            'processing_mode': 'hybrid',
            'max_workers': 16,
            'concurrent_workers': 8,
            'max_queue_size': 10000,
            'load_balancing_strategy': 'adaptive',
            'resource_monitor_interval': 10
        },
        'enterprise': {
            'processing_mode': 'multi_process',
            'max_workers': min(32, mp.cpu_count() * 4),
            'concurrent_workers': 12,
            'max_queue_size': 20000,
            'load_balancing_strategy': 'adaptive',
            'resource_monitor_interval': 5
        }
    }
    
    config = base_configs.get(scale_level, base_configs['medium']).copy()
    
    if custom_config:
        config.update(custom_config)
    
    return ScalableExtractionEngine(config)