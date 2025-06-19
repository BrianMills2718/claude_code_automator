#!/usr/bin/env python3
"""
Memory Manager for CC_AUTOMATOR V3
Provides intelligent memory management for message histories and session data
"""

import gc
import psutil
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MemoryMetrics:
    """Memory usage metrics"""
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    percent: float  # Memory percentage
    available_mb: float  # Available system memory in MB
    timestamp: datetime


class MemoryManager:
    """Manages memory usage for phase execution"""
    
    def __init__(self, max_memory_mb: int = 2000, enable_gc: bool = True):
        self.max_memory_mb = max_memory_mb
        self.enable_gc = enable_gc
        self.process = psutil.Process()
        self.metrics_history: List[MemoryMetrics] = []
        self.message_limits = {
            "research": 100,
            "planning": 100, 
            "implement": 150,
            "architecture": 50,
            "lint": 30,
            "typecheck": 30,
            "test": 100,
            "integration": 80,
            "e2e": 50,
            "validate": 30,
            "commit": 20
        }
        
    def get_current_metrics(self) -> MemoryMetrics:
        """Get current memory usage metrics"""
        memory_info = self.process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return MemoryMetrics(
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            percent=self.process.memory_percent(),
            available_mb=system_memory.available / 1024 / 1024,
            timestamp=datetime.now()
        )
        
    def record_metrics(self, phase_name: str = "unknown") -> MemoryMetrics:
        """Record current memory metrics"""
        metrics = self.get_current_metrics()
        self.metrics_history.append(metrics)
        
        # Keep only last 100 metrics to prevent memory growth
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
            
        return metrics
        
    def is_memory_pressure(self) -> bool:
        """Check if system is under memory pressure"""
        current = self.get_current_metrics()
        
        # Check multiple conditions
        high_rss = current.rss_mb > self.max_memory_mb
        high_percent = current.percent > 80  # 80% of system memory
        low_available = current.available_mb < 500  # Less than 500MB available
        
        return high_rss or high_percent or low_available
        
    def optimize_message_history(self, messages: List[Any], phase_name: str) -> List[Any]:
        """Optimize message history based on memory pressure and phase requirements"""
        if not messages:
            return messages
            
        # Get phase-specific limit
        limit = self.message_limits.get(phase_name, 100)
        
        # If under memory pressure, be more aggressive
        if self.is_memory_pressure():
            limit = min(limit, 50)  # Cap at 50 messages under pressure
            
        # Always keep recent messages
        if len(messages) <= limit:
            return messages
            
        # Keep the first few and last messages for context
        if limit > 20:
            keep_start = min(5, limit // 4)
            keep_end = limit - keep_start
            optimized = messages[:keep_start] + messages[-keep_end:]
        else:
            # Just keep recent messages if limit is very low
            optimized = messages[-limit:]
            
        return optimized
        
    def cleanup_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up session data to reduce memory usage"""
        cleaned = {}
        
        for phase_name, data in session_data.items():
            if isinstance(data, dict):
                cleaned_data = {
                    "session_id": data.get("session_id"),
                    "sdk": data.get("sdk", False)
                }
                
                # Optimize messages if present
                if "messages" in data:
                    messages = data["messages"]
                    cleaned_data["messages"] = self.optimize_message_history(messages, phase_name)
                    
                cleaned[phase_name] = cleaned_data
            else:
                cleaned[phase_name] = data
                
        return cleaned
        
    def force_garbage_collection(self) -> int:
        """Force garbage collection and return collected objects count"""
        if not self.enable_gc:
            return 0
            
        # Run all generation garbage collection
        collected = 0
        for generation in range(3):
            collected += gc.collect(generation)
            
        return collected
        
    def memory_report(self, verbose: bool = False) -> str:
        """Generate memory usage report"""
        current = self.get_current_metrics()
        
        lines = [
            f"# Memory Usage Report",
            f"**Timestamp**: {current.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**RSS Memory**: {current.rss_mb:.1f} MB",
            f"**Virtual Memory**: {current.vms_mb:.1f} MB", 
            f"**Memory Percentage**: {current.percent:.1f}%",
            f"**Available System**: {current.available_mb:.1f} MB",
            f"**Memory Pressure**: {'⚠️ YES' if self.is_memory_pressure() else '✅ NO'}"
        ]
        
        if verbose and len(self.metrics_history) >= 2:
            lines.append(f"\n## Memory Trend")
            recent = self.metrics_history[-10:]  # Last 10 measurements
            
            if len(recent) >= 2:
                start_rss = recent[0].rss_mb
                end_rss = recent[-1].rss_mb
                delta = end_rss - start_rss
                trend = "↗️ Increasing" if delta > 10 else "↘️ Decreasing" if delta < -10 else "➡️ Stable"
                lines.append(f"**Trend**: {trend} ({delta:+.1f} MB)")
                
            lines.append(f"**Peak RSS**: {max(m.rss_mb for m in recent):.1f} MB")
            lines.append(f"**Min RSS**: {min(m.rss_mb for m in recent):.1f} MB")
            
        return "\n".join(lines)
        
    def should_trigger_cleanup(self) -> bool:
        """Determine if cleanup should be triggered"""
        if self.is_memory_pressure():
            return True
            
        # Check growth trend
        if len(self.metrics_history) >= 5:
            recent = self.metrics_history[-5:]
            growth = recent[-1].rss_mb - recent[0].rss_mb
            if growth > 200:  # 200MB growth in recent measurements
                return True
                
        return False
        
    def smart_cleanup(self, session_data: Dict[str, Any], messages: List[Any], phase_name: str) -> tuple[Dict[str, Any], List[Any], int]:
        """Perform intelligent cleanup based on current memory state"""
        collected = 0
        
        # Clean session data
        cleaned_sessions = self.cleanup_session_data(session_data)
        
        # Optimize current messages
        optimized_messages = self.optimize_message_history(messages, phase_name)
        
        # Force garbage collection if needed
        if self.should_trigger_cleanup():
            collected = self.force_garbage_collection()
            
        return cleaned_sessions, optimized_messages, collected
        
    def save_memory_report(self, output_dir: Path):
        """Save memory report to file"""
        report = self.memory_report(verbose=True)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"memory_report_{timestamp}.md"
        
        report_file.write_text(report)
        return report_file


class AdaptiveMemoryManager(MemoryManager):
    """Memory manager that adapts limits based on system resources"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system_memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024
        self._adapt_limits()
        
    def _adapt_limits(self):
        """Adapt memory limits based on available system resources"""
        if self.system_memory_gb < 8:
            # Low memory system - be conservative
            self.max_memory_mb = 1000
            base_limits = {
                "research": 50,
                "planning": 50,
                "implement": 75,
                "architecture": 25,
                "lint": 20,
                "typecheck": 20,
                "test": 50,
                "integration": 40,
                "e2e": 25,
                "validate": 20,
                "commit": 15
            }
        elif self.system_memory_gb < 16:
            # Medium memory system - moderate limits
            self.max_memory_mb = 1500
            base_limits = {
                "research": 75,
                "planning": 75,
                "implement": 100,
                "architecture": 40,
                "lint": 25,
                "typecheck": 25,
                "test": 75,
                "integration": 60,
                "e2e": 40,
                "validate": 25,
                "commit": 20
            }
        else:
            # High memory system - generous limits
            self.max_memory_mb = 3000
            base_limits = {
                "research": 150,
                "planning": 150,
                "implement": 200,
                "architecture": 75,
                "lint": 50,
                "typecheck": 50,
                "test": 150,
                "integration": 100,
                "e2e": 75,
                "validate": 50,
                "commit": 30
            }
            
        self.message_limits = base_limits


def create_memory_manager(adaptive: bool = True, **kwargs) -> MemoryManager:
    """Factory function to create appropriate memory manager"""
    if adaptive:
        return AdaptiveMemoryManager(**kwargs)
    else:
        return MemoryManager(**kwargs)


if __name__ == "__main__":
    # Example usage
    mm = create_memory_manager()
    
    print("System Memory Analysis:")
    print(f"Total RAM: {mm.system_memory_gb:.1f} GB")
    print(f"Max Memory Limit: {mm.max_memory_mb} MB")
    print()
    
    # Show current metrics
    current = mm.record_metrics("test")
    print("Current Memory Usage:")
    print(f"RSS: {current.rss_mb:.1f} MB")
    print(f"Percentage: {current.percent:.1f}%")
    print(f"Available: {current.available_mb:.1f} MB")
    print(f"Memory Pressure: {mm.is_memory_pressure()}")
    
    # Generate report
    print("\n" + mm.memory_report(verbose=True))