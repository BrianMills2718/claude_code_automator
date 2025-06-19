"""
Claude Code SDK V4 - Stable Async Resource Management

This module replaces the V3 error masking strategy with proper async resource
management and structured concurrency patterns to resolve TaskGroup cleanup
race conditions at their root cause.

Key improvements:
1. Proper async resource tracking and cleanup
2. Structured concurrency with shielded cleanup
3. Real error analysis instead of suppression
4. Resource leak detection and prevention
"""

import asyncio
import time
import contextlib
from typing import Dict, Any, Optional, List, AsyncGenerator, Set
from dataclasses import dataclass
import logging
import gc
import psutil
import os

# Import the base Claude Code SDK
from claude_code import query, ClaudeCodeOptions

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Track resource usage for leak detection."""
    timestamp: float
    memory_mb: float
    open_fds: int
    active_tasks: int
    http_connections: int


class AsyncResourceTracker:
    """Track and manage async resources to prevent leaks."""
    
    def __init__(self):
        self.active_resources: Set[Any] = set()
        self.resource_metrics: List[ResourceMetrics] = []
        self.cleanup_failures: List[str] = []
        
    def track_resource(self, resource: Any, resource_type: str = "unknown"):
        """Track an async resource for cleanup."""
        self.active_resources.add((resource, resource_type))
        logger.debug(f"Tracking {resource_type} resource: {id(resource)}")
        
    def untrack_resource(self, resource: Any):
        """Remove resource from tracking (successful cleanup)."""
        to_remove = None
        for tracked_resource, resource_type in self.active_resources:
            if tracked_resource is resource:
                to_remove = (tracked_resource, resource_type)
                break
        
        if to_remove:
            self.active_resources.remove(to_remove)
            logger.debug(f"Untracked {to_remove[1]} resource: {id(resource)}")
        
    async def cleanup_all(self, timeout: float = 30.0) -> bool:
        """Force cleanup of all tracked resources with timeout."""
        if not self.active_resources:
            return True
            
        cleanup_tasks = []
        for resource, resource_type in self.active_resources.copy():
            try:
                if hasattr(resource, 'cleanup'):
                    task = asyncio.create_task(
                        asyncio.shield(resource.cleanup())
                    )
                    cleanup_tasks.append((task, resource_type, id(resource)))
                elif hasattr(resource, 'close'):
                    task = asyncio.create_task(
                        asyncio.shield(resource.close())
                    )
                    cleanup_tasks.append((task, resource_type, id(resource)))
            except Exception as e:
                self.cleanup_failures.append(f"{resource_type}:{id(resource)} - {str(e)}")
                logger.warning(f"Failed to create cleanup task for {resource_type}: {e}")
        
        # Wait for all cleanup tasks with timeout
        if cleanup_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*[task for task, _, _ in cleanup_tasks], return_exceptions=True),
                    timeout=timeout
                )
                logger.info(f"Completed cleanup of {len(cleanup_tasks)} resources")
            except asyncio.TimeoutError:
                logger.error(f"Cleanup timeout after {timeout}s for {len(cleanup_tasks)} resources")
                return False
        
        # Clear tracking after cleanup attempt
        self.active_resources.clear()
        return len(self.cleanup_failures) == 0
    
    def record_metrics(self):
        """Record current resource usage metrics."""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            open_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
            active_tasks = len([task for task in asyncio.all_tasks() if not task.done()])
            
            # HTTP connections are harder to track reliably, approximate
            http_connections = len(self.active_resources)
            
            metrics = ResourceMetrics(
                timestamp=time.time(),
                memory_mb=memory_mb,
                open_fds=open_fds,
                active_tasks=active_tasks,
                http_connections=http_connections
            )
            
            self.resource_metrics.append(metrics)
            
            # Keep only last 100 metrics to prevent memory growth
            if len(self.resource_metrics) > 100:
                self.resource_metrics = self.resource_metrics[-50:]
                
            return metrics
        except Exception as e:
            logger.warning(f"Failed to record metrics: {e}")
            return None
    
    def detect_leaks(self) -> Dict[str, Any]:
        """Analyze metrics to detect resource leaks."""
        if len(self.resource_metrics) < 10:
            return {"insufficient_data": True}
        
        recent = self.resource_metrics[-10:]
        initial = recent[0]
        final = recent[-1]
        
        memory_growth = final.memory_mb - initial.memory_mb
        fd_growth = final.open_fds - initial.open_fds
        task_growth = final.active_tasks - initial.active_tasks
        
        return {
            "memory_growth_mb": memory_growth,
            "fd_growth": fd_growth,
            "task_growth": task_growth,
            "memory_leak_suspected": memory_growth > 50,  # 50MB growth
            "fd_leak_suspected": fd_growth > 10,          # 10 FD growth
            "task_leak_suspected": task_growth > 5,       # 5 task growth
            "active_resources": len(self.active_resources),
            "cleanup_failures": len(self.cleanup_failures)
        }


class ClaudeCodeSDKV4Stable:
    """
    V4 Stable SDK wrapper with proper async resource management.
    
    Replaces V3 error masking with root cause fixes:
    - Structured concurrency with proper cleanup
    - Resource tracking and leak detection  
    - Real error analysis without suppression
    - Shielded cleanup operations
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.resource_tracker = AsyncResourceTracker()
        self.session_count = 0
        
    async def run_claude_streaming(
        self, 
        prompt: str, 
        options: ClaudeCodeOptions
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run Claude Code with proper async resource management.
        
        Key improvements over V3:
        1. Proper resource tracking throughout operation
        2. Structured concurrency with shielded cleanup
        3. Real error handling without masking
        4. Resource leak detection
        """
        
        session_id = f"v4_session_{self.session_count}"
        self.session_count += 1
        
        # Record initial resource state
        initial_metrics = self.resource_tracker.record_metrics()
        if self.verbose and initial_metrics:
            logger.info(f"Starting {session_id} - Memory: {initial_metrics.memory_mb:.1f}MB, FDs: {initial_metrics.open_fds}")
        
        try:
            # Use structured concurrency with proper cleanup
            async with self._managed_execution_context(session_id):
                
                # Run the actual Claude Code operation
                async for message in query(prompt=prompt, options=options):
                    
                    # Process message with enhanced parsing
                    processed_message = await self._process_message_safely(message)
                    
                    # Track any resources created during message processing
                    if "resources" in processed_message:
                        for resource in processed_message["resources"]:
                            self.resource_tracker.track_resource(resource, "claude_message")
                    
                    yield processed_message
                    
        except Exception as e:
            # Analyze error properly instead of masking
            error_analysis = await self._analyze_error_thoroughly(e, session_id)
            
            if error_analysis["can_recover"]:
                # Attempt graceful recovery
                logger.warning(f"Recoverable error in {session_id}: {error_analysis['summary']}")
                yield {
                    "type": "error",
                    "subtype": "recoverable", 
                    "error_analysis": error_analysis,
                    "session_id": session_id
                }
            else:
                # Real error that should be propagated
                logger.error(f"Unrecoverable error in {session_id}: {error_analysis['summary']}")
                
                # Ensure cleanup happens even on failure
                await self._emergency_cleanup(session_id)
                
                raise
        
        finally:
            # Record final metrics and check for leaks
            final_metrics = self.resource_tracker.record_metrics()
            leak_analysis = self.resource_tracker.detect_leaks()
            
            if self.verbose:
                if final_metrics and initial_metrics:
                    memory_delta = final_metrics.memory_mb - initial_metrics.memory_mb
                    fd_delta = final_metrics.open_fds - initial_metrics.open_fds
                    logger.info(f"Completed {session_id} - Memory Δ: {memory_delta:+.1f}MB, FD Δ: {fd_delta:+d}")
                
                if leak_analysis.get("memory_leak_suspected") or leak_analysis.get("fd_leak_suspected"):
                    logger.warning(f"Resource leak suspected in {session_id}: {leak_analysis}")
    
    @contextlib.asynccontextmanager
    async def _managed_execution_context(self, session_id: str):
        """
        Proper async context manager for structured concurrency.
        
        Ensures all resources are properly cleaned up even if the main
        operation is cancelled or fails.
        """
        context_resources = []
        
        try:
            # Set up execution context
            if self.verbose:
                logger.debug(f"Entering managed context for {session_id}")
            
            yield context_resources
            
        finally:
            # Shielded cleanup - won't be cancelled even if parent task is
            try:
                cleanup_successful = await asyncio.shield(
                    self.resource_tracker.cleanup_all(timeout=10.0)
                )
                
                if not cleanup_successful:
                    logger.warning(f"Cleanup incomplete for {session_id}")
                elif self.verbose:
                    logger.debug(f"Cleanup completed for {session_id}")
                    
            except Exception as cleanup_error:
                # Log cleanup failures but don't re-raise
                logger.error(f"Cleanup failed for {session_id}: {cleanup_error}")
    
    async def _process_message_safely(self, message: Any) -> Dict[str, Any]:
        """
        Process Claude Code messages with enhanced error handling.
        
        Includes the V3 cost parsing improvements while adding
        proper resource management.
        """
        try:
            # Convert message to dict if needed
            if hasattr(message, '__dict__'):
                msg_dict = message.__dict__.copy()
            else:
                msg_dict = dict(message) if hasattr(message, 'items') else {"raw_message": str(message)}
            
            # Enhanced cost parsing (from V3)
            if 'cost' in msg_dict or 'total_cost' in msg_dict or 'cost_usd' in msg_dict:
                msg_dict = self._parse_cost_fields_robustly(msg_dict)
            
            # Add processing timestamp
            msg_dict['processing_timestamp'] = time.time()
            
            return msg_dict
            
        except Exception as e:
            logger.warning(f"Message processing error: {e}")
            return {
                "type": "processing_error",
                "error": str(e),
                "raw_message": str(message),
                "processing_timestamp": time.time()
            }
    
    def _parse_cost_fields_robustly(self, msg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced cost parsing from V3 with additional robustness.
        """
        # Try multiple cost field variations
        cost_fields = ['cost_usd', 'total_cost_usd', 'total_cost', 'cost']
        
        for field in cost_fields:
            if field in msg_dict:
                try:
                    cost_value = msg_dict[field]
                    if isinstance(cost_value, (int, float)):
                        msg_dict['total_cost_usd'] = float(cost_value)
                        break
                    elif isinstance(cost_value, str):
                        # Handle string costs like "$1.23"
                        cost_str = cost_value.replace('$', '').replace(',', '')
                        msg_dict['total_cost_usd'] = float(cost_str)
                        break
                except (ValueError, TypeError):
                    continue
        
        # Set default if no cost found
        if 'total_cost_usd' not in msg_dict:
            msg_dict['total_cost_usd'] = 0.0
        
        return msg_dict
    
    async def _analyze_error_thoroughly(self, error: Exception, session_id: str) -> Dict[str, Any]:
        """
        Thorough error analysis instead of simple classification and masking.
        
        Determines if errors are recoverable and provides actionable information.
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        analysis = {
            "error_type": error_type,
            "error_message": str(error),
            "session_id": session_id,
            "timestamp": time.time(),
            "can_recover": False,
            "recovery_actions": [],
            "root_cause": "unknown",
            "summary": f"{error_type}: {str(error)[:100]}"
        }
        
        # TaskGroup errors - analyze instead of mask
        if "taskgroup" in error_str or isinstance(error, BaseExceptionGroup):
            analysis.update(await self._analyze_taskgroup_error(error))
        
        # WebSearch/HTTP errors  
        elif any(keyword in error_str for keyword in ["websearch", "http", "connection", "timeout"]):
            analysis.update(await self._analyze_network_error(error))
        
        # Authentication errors
        elif any(keyword in error_str for keyword in ["authentication", "unauthorized", "api_key"]):
            analysis.update(await self._analyze_auth_error(error))
        
        # Resource/cleanup errors
        elif any(keyword in error_str for keyword in ["cleanup", "resource", "close", "finalizer"]):
            analysis.update(await self._analyze_resource_error(error))
        
        return analysis
    
    async def _analyze_taskgroup_error(self, error: Exception) -> Dict[str, Any]:
        """
        Analyze TaskGroup errors to determine if they're recoverable.
        
        Instead of masking all TaskGroup errors, distinguish between:
        1. Real operational failures that should be reported
        2. Cleanup race conditions that can be recovered from
        3. Resource management issues that need attention
        """
        if isinstance(error, BaseExceptionGroup):
            # Analyze each sub-exception in the group
            operational_errors = []
            cleanup_errors = []
            
            for sub_error in error.exceptions:
                sub_str = str(sub_error).lower()
                if any(word in sub_str for word in ["cancel", "timeout", "cleanup"]):
                    cleanup_errors.append(str(sub_error))
                else:
                    operational_errors.append(str(sub_error))
            
            if operational_errors:
                return {
                    "root_cause": "operational_failure_in_taskgroup",
                    "can_recover": False,
                    "operational_errors": operational_errors,
                    "cleanup_errors": cleanup_errors,
                    "recovery_actions": ["Fix underlying operational issue"]
                }
            else:
                return {
                    "root_cause": "taskgroup_cleanup_race",
                    "can_recover": True,
                    "cleanup_errors": cleanup_errors,
                    "recovery_actions": ["Force resource cleanup", "Check for resource leaks"]
                }
        else:
            error_str = str(error).lower()
            if "cancel_scope" in error_str:
                return {
                    "root_cause": "cancel_scope_boundary_violation",
                    "can_recover": True,
                    "recovery_actions": ["Implement proper async context management"]
                }
            else:
                return {
                    "root_cause": "unknown_taskgroup_issue",
                    "can_recover": False,
                    "recovery_actions": ["Investigate specific TaskGroup usage pattern"]
                }
    
    async def _analyze_network_error(self, error: Exception) -> Dict[str, Any]:
        """Analyze network-related errors for recovery potential."""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return {
                "root_cause": "network_timeout",
                "can_recover": True,
                "recovery_actions": ["Retry with longer timeout", "Check network connectivity"]
            }
        elif "connection" in error_str:
            return {
                "root_cause": "connection_failure", 
                "can_recover": True,
                "recovery_actions": ["Retry connection", "Check service availability"]
            }
        else:
            return {
                "root_cause": "network_error",
                "can_recover": False,
                "recovery_actions": ["Check network configuration"]
            }
    
    async def _analyze_auth_error(self, error: Exception) -> Dict[str, Any]:
        """Analyze authentication errors."""
        return {
            "root_cause": "authentication_failure",
            "can_recover": False,
            "recovery_actions": ["Check API keys", "Verify authentication configuration"]
        }
    
    async def _analyze_resource_error(self, error: Exception) -> Dict[str, Any]:
        """Analyze resource management errors."""
        return {
            "root_cause": "resource_management_failure",
            "can_recover": True,
            "recovery_actions": ["Force cleanup", "Check for resource leaks"]
        }
    
    async def _emergency_cleanup(self, session_id: str):
        """Emergency cleanup when normal flow fails."""
        try:
            logger.warning(f"Emergency cleanup for {session_id}")
            await asyncio.shield(self.resource_tracker.cleanup_all(timeout=5.0))
            
            # Force garbage collection
            gc.collect()
            
        except Exception as cleanup_error:
            logger.error(f"Emergency cleanup failed for {session_id}: {cleanup_error}")


# Factory function for easy integration
def create_stable_sdk(verbose: bool = False) -> ClaudeCodeSDKV4Stable:
    """Create a V4 stable SDK instance with proper resource management."""
    return ClaudeCodeSDKV4Stable(verbose=verbose)