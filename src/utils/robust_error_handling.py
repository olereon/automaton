#!/usr/bin/env python3
"""
Robust Error Handling and Recovery System

This module provides comprehensive error handling, recovery mechanisms, and
resilience features for the landmark-based metadata extraction system.
"""

import asyncio
import logging
import traceback
import time
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import sys
from functools import wraps
import weakref

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"      # System-breaking errors
    HIGH = "high"             # Feature-breaking errors  
    MEDIUM = "medium"         # Degraded performance
    LOW = "low"               # Minor issues
    WARNING = "warning"       # Potential issues


class RecoveryStrategy(Enum):
    """Error recovery strategies"""
    RETRY = "retry"                    # Retry the operation
    FALLBACK = "fallback"             # Use fallback method
    SKIP = "skip"                     # Skip this operation
    ABORT = "abort"                   # Abort entire process
    DEGRADE = "degrade"               # Continue with degraded functionality
    CIRCUIT_BREAK = "circuit_break"   # Stop trying for a period


@dataclass
class ErrorContext:
    """Comprehensive error context information"""
    error_type: str
    severity: ErrorSeverity
    timestamp: datetime
    operation: str
    details: Dict[str, Any]
    stack_trace: str
    recovery_attempted: bool = False
    recovery_successful: bool = False
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'error_type': self.error_type,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'details': self.details,
            'stack_trace': self.stack_trace,
            'recovery_attempted': self.recovery_attempted,
            'recovery_successful': self.recovery_successful,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }


@dataclass
class CircuitBreakerState:
    """Circuit breaker state management"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "closed"  # closed, open, half_open
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3  # successes needed to close circuit
    recent_successes: int = 0
    
    def should_allow_request(self) -> bool:
        """Determine if request should be allowed"""
        now = datetime.now()
        
        if self.state == "closed":
            return True
        
        elif self.state == "open":
            if (self.last_failure_time and 
                (now - self.last_failure_time).seconds > self.recovery_timeout):
                self.state = "half_open"
                self.recent_successes = 0
                return True
            return False
        
        elif self.state == "half_open":
            return True
        
        return False
    
    def record_success(self):
        """Record successful operation"""
        if self.state == "half_open":
            self.recent_successes += 1
            if self.recent_successes >= self.success_threshold:
                self.state = "closed"
                self.failure_count = 0
                self.recent_successes = 0
        elif self.state == "closed":
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
        elif self.state == "half_open":
            self.state = "open"
            self.recent_successes = 0


class ErrorPatternAnalyzer:
    """Analyzes error patterns to predict and prevent issues"""
    
    def __init__(self, max_history: int = 1000):
        self.error_history: List[ErrorContext] = []
        self.pattern_cache = {}
        self.max_history = max_history
        self.analysis_interval = 60  # seconds
        self.last_analysis = time.time()
    
    def record_error(self, error_context: ErrorContext):
        """Record error for pattern analysis"""
        self.error_history.append(error_context)
        
        # Maintain history size
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history//2:]
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns and generate insights"""
        now = time.time()
        if now - self.last_analysis < self.analysis_interval:
            return self.pattern_cache.get('last_analysis', {})
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'total_errors': len(self.error_history),
            'error_distribution': self._analyze_error_distribution(),
            'temporal_patterns': self._analyze_temporal_patterns(),
            'severity_trends': self._analyze_severity_trends(),
            'operation_reliability': self._analyze_operation_reliability(),
            'predictive_insights': self._generate_predictive_insights()
        }
        
        self.pattern_cache['last_analysis'] = analysis
        self.last_analysis = now
        
        return analysis
    
    def _analyze_error_distribution(self) -> Dict[str, int]:
        """Analyze distribution of error types"""
        distribution = {}
        for error in self.error_history:
            error_type = error.error_type
            distribution[error_type] = distribution.get(error_type, 0) + 1
        return distribution
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal patterns in errors"""
        if not self.error_history:
            return {}
        
        # Recent errors (last hour)
        recent_threshold = datetime.now() - timedelta(hours=1)
        recent_errors = [e for e in self.error_history if e.timestamp > recent_threshold]
        
        # Error frequency analysis
        hourly_distribution = [0] * 24
        for error in self.error_history[-200:]:  # Last 200 errors
            hour = error.timestamp.hour
            hourly_distribution[hour] += 1
        
        return {
            'recent_errors_count': len(recent_errors),
            'hourly_distribution': hourly_distribution,
            'peak_error_hour': hourly_distribution.index(max(hourly_distribution)) if any(hourly_distribution) else 0
        }
    
    def _analyze_severity_trends(self) -> Dict[str, Any]:
        """Analyze severity level trends"""
        severity_counts = {}
        recent_severity_trend = []
        
        for error in self.error_history:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Recent trend (last 50 errors)
        for error in self.error_history[-50:]:
            recent_severity_trend.append(error.severity.value)
        
        return {
            'severity_distribution': severity_counts,
            'recent_trend': recent_severity_trend,
            'critical_error_rate': severity_counts.get('critical', 0) / len(self.error_history) if self.error_history else 0
        }
    
    def _analyze_operation_reliability(self) -> Dict[str, Dict[str, float]]:
        """Analyze reliability of different operations"""
        operation_stats = {}
        
        for error in self.error_history:
            operation = error.operation
            if operation not in operation_stats:
                operation_stats[operation] = {
                    'error_count': 0,
                    'total_attempts': 0,
                    'success_rate': 0.0,
                    'avg_retry_count': 0.0
                }
            
            stats = operation_stats[operation]
            stats['error_count'] += 1
            stats['total_attempts'] += error.retry_count + 1
            stats['avg_retry_count'] = (stats['avg_retry_count'] * (stats['error_count'] - 1) + error.retry_count) / stats['error_count']
        
        # Calculate success rates (this would need success tracking in real implementation)
        for operation, stats in operation_stats.items():
            # Placeholder calculation - would need actual success data
            estimated_successes = max(0, stats['total_attempts'] - stats['error_count'])
            stats['success_rate'] = estimated_successes / stats['total_attempts'] if stats['total_attempts'] > 0 else 0.0
        
        return operation_stats
    
    def _generate_predictive_insights(self) -> List[Dict[str, str]]:
        """Generate predictive insights based on patterns"""
        insights = []
        
        # High error rate insight
        recent_errors = [e for e in self.error_history if e.timestamp > datetime.now() - timedelta(hours=1)]
        if len(recent_errors) > 10:
            insights.append({
                'type': 'high_error_rate',
                'message': f'High error rate detected: {len(recent_errors)} errors in the last hour',
                'severity': 'high',
                'recommendation': 'Consider enabling circuit breaker or increasing timeouts'
            })
        
        # Repeated failure insight
        operation_failures = {}
        for error in self.error_history[-50:]:
            op = error.operation
            operation_failures[op] = operation_failures.get(op, 0) + 1
        
        for operation, count in operation_failures.items():
            if count > 5:
                insights.append({
                    'type': 'repeated_operation_failure',
                    'message': f'Operation "{operation}" failing repeatedly ({count} times recently)',
                    'severity': 'medium',
                    'recommendation': f'Review and optimize "{operation}" implementation'
                })
        
        return insights
    
    def predict_failure_risk(self, operation: str) -> float:
        """Predict failure risk for an operation (0.0 to 1.0)"""
        operation_errors = [e for e in self.error_history if e.operation == operation]
        
        if not operation_errors:
            return 0.1  # Low risk for unknown operations
        
        # Recent error density
        recent_errors = [e for e in operation_errors if e.timestamp > datetime.now() - timedelta(hours=1)]
        recent_density = len(recent_errors) / max(1, len(operation_errors))
        
        # Severity factor
        critical_errors = [e for e in operation_errors if e.severity == ErrorSeverity.CRITICAL]
        severity_factor = len(critical_errors) / len(operation_errors)
        
        # Retry factor (operations requiring many retries are riskier)
        avg_retries = sum(e.retry_count for e in operation_errors) / len(operation_errors)
        retry_factor = min(1.0, avg_retries / 3.0)  # Normalize to 0-1
        
        # Combine factors
        risk_score = (recent_density * 0.4 + severity_factor * 0.3 + retry_factor * 0.3)
        return min(1.0, risk_score)


class RobustErrorHandler:
    """Comprehensive error handling with recovery strategies"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.pattern_analyzer = ErrorPatternAnalyzer()
        self.circuit_breakers = {}
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.error_callbacks = []
        
        # Configuration
        self.default_retry_count = self.config.get('default_retry_count', 3)
        self.retry_delay_base = self.config.get('retry_delay_base', 1.0)  # seconds
        self.max_retry_delay = self.config.get('max_retry_delay', 30.0)  # seconds
        self.enable_circuit_breaker = self.config.get('enable_circuit_breaker', True)
        self.enable_pattern_analysis = self.config.get('enable_pattern_analysis', True)
    
    def _initialize_recovery_strategies(self) -> Dict[str, Callable]:
        """Initialize recovery strategy functions"""
        return {
            'dom_query_timeout': self._recover_dom_query_timeout,
            'element_not_found': self._recover_element_not_found,
            'page_navigation_error': self._recover_page_navigation_error,
            'memory_pressure': self._recover_memory_pressure,
            'network_error': self._recover_network_error,
            'javascript_error': self._recover_javascript_error,
            'selector_invalid': self._recover_selector_invalid,
            'extraction_timeout': self._recover_extraction_timeout
        }
    
    def add_error_callback(self, callback: Callable[[ErrorContext], None]):
        """Add callback to be notified of errors"""
        self.error_callbacks.append(callback)
    
    async def execute_with_recovery(self, operation_func: Callable, 
                                  operation_name: str,
                                  *args, 
                                  max_retries: Optional[int] = None,
                                  recovery_strategy: Optional[RecoveryStrategy] = None,
                                  **kwargs) -> Tuple[Any, Optional[ErrorContext]]:
        """Execute operation with comprehensive error handling and recovery"""
        max_retries = max_retries or self.default_retry_count
        retry_count = 0
        last_error_context = None
        
        # Check circuit breaker
        if self.enable_circuit_breaker:
            circuit_breaker = self._get_circuit_breaker(operation_name)
            if not circuit_breaker.should_allow_request():
                error_context = ErrorContext(
                    error_type="circuit_breaker_open",
                    severity=ErrorSeverity.HIGH,
                    timestamp=datetime.now(),
                    operation=operation_name,
                    details={'reason': 'Circuit breaker is open'},
                    stack_trace=""
                )
                return None, error_context
        
        while retry_count <= max_retries:
            try:
                # Execute the operation
                result = await operation_func(*args, **kwargs)
                
                # Record success
                if self.enable_circuit_breaker:
                    circuit_breaker = self._get_circuit_breaker(operation_name)
                    circuit_breaker.record_success()
                
                return result, last_error_context
                
            except Exception as e:
                retry_count += 1
                
                # Create error context
                error_context = ErrorContext(
                    error_type=type(e).__name__,
                    severity=self._determine_error_severity(e, operation_name),
                    timestamp=datetime.now(),
                    operation=operation_name,
                    details={
                        'exception_message': str(e),
                        'operation_args': str(args)[:200],  # Limit size
                        'operation_kwargs': str(kwargs)[:200],
                        'retry_count': retry_count,
                        'max_retries': max_retries
                    },
                    stack_trace=traceback.format_exc(),
                    retry_count=retry_count,
                    max_retries=max_retries
                )
                
                last_error_context = error_context
                
                # Record error for pattern analysis
                if self.enable_pattern_analysis:
                    self.pattern_analyzer.record_error(error_context)
                
                # Record circuit breaker failure
                if self.enable_circuit_breaker:
                    circuit_breaker = self._get_circuit_breaker(operation_name)
                    circuit_breaker.record_failure()
                
                # Notify callbacks
                for callback in self.error_callbacks:
                    try:
                        callback(error_context)
                    except Exception as cb_error:
                        logger.warning(f"Error callback failed: {cb_error}")
                
                # Determine if we should continue retrying
                if retry_count > max_retries:
                    break
                
                # Apply recovery strategy
                should_retry, recovery_successful = await self._apply_recovery_strategy(
                    e, error_context, recovery_strategy
                )
                
                error_context.recovery_attempted = True
                error_context.recovery_successful = recovery_successful
                
                if not should_retry:
                    break
                
                # Calculate exponential backoff delay
                delay = min(
                    self.retry_delay_base * (2 ** (retry_count - 1)),
                    self.max_retry_delay
                )
                
                logger.info(f"Retrying {operation_name} after {delay:.1f}s (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.error(f"Operation {operation_name} failed after {retry_count} attempts")
        return None, last_error_context
    
    def _get_circuit_breaker(self, operation_name: str) -> CircuitBreakerState:
        """Get or create circuit breaker for operation"""
        if operation_name not in self.circuit_breakers:
            self.circuit_breakers[operation_name] = CircuitBreakerState()
        return self.circuit_breakers[operation_name]
    
    def _determine_error_severity(self, exception: Exception, operation: str) -> ErrorSeverity:
        """Determine error severity based on exception type and context"""
        error_type = type(exception).__name__
        
        # Critical errors
        if error_type in ['MemoryError', 'SystemExit', 'KeyboardInterrupt']:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if error_type in ['ConnectionError', 'TimeoutError', 'BrokenPipeError']:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if error_type in ['ElementNotFound', 'SelectorError', 'JavaScriptException']:
            return ErrorSeverity.MEDIUM
        
        # Operation-specific severity
        if 'extraction' in operation.lower():
            if error_type in ['AttributeError', 'TypeError']:
                return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    async def _apply_recovery_strategy(self, exception: Exception, 
                                     error_context: ErrorContext,
                                     recovery_strategy: Optional[RecoveryStrategy] = None) -> Tuple[bool, bool]:
        """Apply appropriate recovery strategy"""
        should_retry = True
        recovery_successful = False
        
        # Determine recovery strategy if not provided
        if not recovery_strategy:
            recovery_strategy = self._select_recovery_strategy(exception, error_context)
        
        try:
            if recovery_strategy == RecoveryStrategy.RETRY:
                # Simple retry - no additional recovery action needed
                recovery_successful = True
            
            elif recovery_strategy == RecoveryStrategy.FALLBACK:
                recovery_successful = await self._attempt_fallback_recovery(exception, error_context)
            
            elif recovery_strategy == RecoveryStrategy.SKIP:
                should_retry = False
                recovery_successful = True  # Successfully skipped
            
            elif recovery_strategy == RecoveryStrategy.ABORT:
                should_retry = False
                recovery_successful = False
            
            elif recovery_strategy == RecoveryStrategy.DEGRADE:
                recovery_successful = await self._attempt_degraded_recovery(exception, error_context)
            
            elif recovery_strategy == RecoveryStrategy.CIRCUIT_BREAK:
                # Circuit breaker will handle this automatically
                should_retry = False
                recovery_successful = False
            
        except Exception as recovery_error:
            logger.warning(f"Recovery strategy failed: {recovery_error}")
            recovery_successful = False
        
        return should_retry, recovery_successful
    
    def _select_recovery_strategy(self, exception: Exception, 
                                error_context: ErrorContext) -> RecoveryStrategy:
        """Select appropriate recovery strategy based on error context"""
        error_type = type(exception).__name__
        operation = error_context.operation
        
        # High-frequency errors should trigger circuit breaking
        failure_risk = self.pattern_analyzer.predict_failure_risk(operation)
        if failure_risk > 0.8:
            return RecoveryStrategy.CIRCUIT_BREAK
        
        # Strategy selection based on error type
        if error_type in ['TimeoutError', 'AsyncTimeoutError']:
            return RecoveryStrategy.RETRY
        
        elif error_type in ['ElementNotFound', 'NoSuchElementException']:
            return RecoveryStrategy.FALLBACK
        
        elif error_type in ['MemoryError', 'OutOfMemoryError']:
            return RecoveryStrategy.DEGRADE
        
        elif error_type in ['NetworkError', 'ConnectionError']:
            return RecoveryStrategy.RETRY if error_context.retry_count < 2 else RecoveryStrategy.ABORT
        
        elif error_type in ['InvalidSelectorException']:
            return RecoveryStrategy.FALLBACK
        
        # Default strategy
        return RecoveryStrategy.RETRY
    
    async def _attempt_fallback_recovery(self, exception: Exception, 
                                       error_context: ErrorContext) -> bool:
        """Attempt fallback recovery based on error type"""
        error_type = type(exception).__name__
        recovery_func = self.recovery_strategies.get(error_type.lower())
        
        if recovery_func:
            try:
                return await recovery_func(exception, error_context)
            except Exception as e:
                logger.debug(f"Fallback recovery failed: {e}")
        
        return False
    
    async def _attempt_degraded_recovery(self, exception: Exception, 
                                       error_context: ErrorContext) -> bool:
        """Attempt recovery with degraded functionality"""
        # Implement graceful degradation
        operation = error_context.operation
        
        if 'extraction' in operation.lower():
            # For extraction operations, we can continue with partial data
            logger.info(f"Continuing {operation} with degraded functionality")
            return True
        
        elif 'query' in operation.lower():
            # For query operations, we can try simpler selectors
            logger.info(f"Degrading {operation} to simpler query methods")
            return True
        
        return False
    
    # Recovery strategy implementations
    async def _recover_dom_query_timeout(self, exception: Exception, 
                                       error_context: ErrorContext) -> bool:
        """Recover from DOM query timeout"""
        logger.info("Attempting DOM query timeout recovery")
        # Could implement timeout adjustment or alternative query methods
        return True
    
    async def _recover_element_not_found(self, exception: Exception, 
                                       error_context: ErrorContext) -> bool:
        """Recover from element not found error"""
        logger.info("Attempting element not found recovery")
        # Could implement alternative selector strategies
        return True
    
    async def _recover_page_navigation_error(self, exception: Exception, 
                                           error_context: ErrorContext) -> bool:
        """Recover from page navigation error"""
        logger.info("Attempting page navigation recovery")
        # Could implement page refresh or alternative navigation
        return True
    
    async def _recover_memory_pressure(self, exception: Exception, 
                                     error_context: ErrorContext) -> bool:
        """Recover from memory pressure"""
        logger.info("Attempting memory pressure recovery")
        # Could implement garbage collection or cache clearing
        import gc
        gc.collect()
        return True
    
    async def _recover_network_error(self, exception: Exception, 
                                   error_context: ErrorContext) -> bool:
        """Recover from network error"""
        logger.info("Attempting network error recovery")
        # Could implement connection retry or alternative endpoints
        return True
    
    async def _recover_javascript_error(self, exception: Exception, 
                                      error_context: ErrorContext) -> bool:
        """Recover from JavaScript execution error"""
        logger.info("Attempting JavaScript error recovery")
        # Could implement alternative JavaScript approaches
        return True
    
    async def _recover_selector_invalid(self, exception: Exception, 
                                      error_context: ErrorContext) -> bool:
        """Recover from invalid selector error"""
        logger.info("Attempting invalid selector recovery")
        # Could implement selector simplification or alternatives
        return True
    
    async def _recover_extraction_timeout(self, exception: Exception, 
                                        error_context: ErrorContext) -> bool:
        """Recover from extraction timeout"""
        logger.info("Attempting extraction timeout recovery")
        # Could implement faster extraction methods
        return True
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        circuit_breaker_stats = {}
        for operation, cb in self.circuit_breakers.items():
            circuit_breaker_stats[operation] = {
                'state': cb.state,
                'failure_count': cb.failure_count,
                'recent_successes': cb.recent_successes
            }
        
        return {
            'pattern_analysis': self.pattern_analyzer.analyze_patterns(),
            'circuit_breakers': circuit_breaker_stats,
            'total_operations_monitored': len(self.circuit_breakers),
            'recovery_strategies_available': len(self.recovery_strategies)
        }
    
    def reset_error_state(self, operation_name: Optional[str] = None):
        """Reset error state for specific operation or all operations"""
        if operation_name:
            if operation_name in self.circuit_breakers:
                self.circuit_breakers[operation_name] = CircuitBreakerState()
        else:
            self.circuit_breakers.clear()
            self.pattern_analyzer.error_history.clear()
        
        logger.info(f"Error state reset for {operation_name or 'all operations'}")


# Decorators for easy integration
def with_error_handling(operation_name: str, max_retries: int = 3, 
                       recovery_strategy: Optional[RecoveryStrategy] = None):
    """Decorator for adding error handling to functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need access to a global error handler instance
            # For now, create a basic one
            error_handler = RobustErrorHandler()
            
            result, error_context = await error_handler.execute_with_recovery(
                func, operation_name, *args, 
                max_retries=max_retries,
                recovery_strategy=recovery_strategy,
                **kwargs
            )
            
            if error_context and not error_context.recovery_successful:
                logger.warning(f"Operation {operation_name} completed with errors: {error_context.error_type}")
            
            return result
        
        return wrapper
    return decorator


# Context manager for error handling
class ErrorHandlingContext:
    """Context manager for error handling operations"""
    
    def __init__(self, error_handler: RobustErrorHandler, operation_name: str):
        self.error_handler = error_handler
        self.operation_name = operation_name
        self.start_time = None
        self.error_context = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Handle the exception
            error_context = ErrorContext(
                error_type=exc_type.__name__,
                severity=self.error_handler._determine_error_severity(exc_val, self.operation_name),
                timestamp=datetime.now(),
                operation=self.operation_name,
                details={'exception_message': str(exc_val)},
                stack_trace=traceback.format_exc()
            )
            
            self.error_context = error_context
            
            # Record for pattern analysis
            if self.error_handler.enable_pattern_analysis:
                self.error_handler.pattern_analyzer.record_error(error_context)
            
            # Apply recovery if needed
            recovery_strategy = self.error_handler._select_recovery_strategy(exc_val, error_context)
            should_retry, recovery_successful = await self.error_handler._apply_recovery_strategy(
                exc_val, error_context, recovery_strategy
            )
            
            error_context.recovery_attempted = True
            error_context.recovery_successful = recovery_successful
            
            # Suppress exception if recovery was successful and strategy allows it
            if recovery_successful and recovery_strategy in [RecoveryStrategy.SKIP, RecoveryStrategy.DEGRADE]:
                return True  # Suppress exception
        
        return False  # Let exception propagate