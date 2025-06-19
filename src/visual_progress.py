#!/usr/bin/env python3
"""
Visual Progress Display for CC_AUTOMATOR3
Provides rich terminal UI for execution progress
"""

import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

# Try to import rich for better display, fallback to simple if not available
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class PhaseProgress:
    """Track progress for a single phase"""
    name: str
    status: str = "pending"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cost: float = 0.0
    session_id: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def duration(self) -> timedelta:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return datetime.now() - self.start_time
        return timedelta(0)
    
    @property
    def duration_str(self) -> str:
        total_seconds = int(self.duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"


class VisualProgressDisplay:
    """Rich visual progress display for CC_AUTOMATOR3"""
    
    def __init__(self):
        self.milestones: Dict[str, Dict[str, PhaseProgress]] = defaultdict(dict)
        self.current_milestone = None
        self.current_phase = None
        self.total_cost = 0.0
        self.start_time = datetime.now()
        self._lock = threading.Lock()
        
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
    
    def start_milestone(self, milestone_name: str, milestone_number: int, total_milestones: int):
        """Start tracking a new milestone"""
        with self._lock:
            self.current_milestone = milestone_name
            if RICH_AVAILABLE:
                self.console.print(f"\n[bold blue]{'='*60}[/bold blue]")
                self.console.print(f"[bold]Milestone {milestone_number}/{total_milestones}: {milestone_name}[/bold]")
                self.console.print(f"[bold blue]{'='*60}[/bold blue]\n")
            else:
                print(f"\n{'='*60}")
                print(f"Milestone {milestone_number}/{total_milestones}: {milestone_name}")
                print(f"{'='*60}\n")
    
    def start_phase(self, phase_name: str, phase_type: str, phase_number: int, total_phases: int):
        """Start tracking a phase"""
        with self._lock:
            self.current_phase = phase_name
            progress = PhaseProgress(
                name=phase_type,
                status="running",
                start_time=datetime.now()
            )
            self.milestones[self.current_milestone][phase_name] = progress
            
            if RICH_AVAILABLE:
                self.console.print(f"[yellow]▶ [{phase_number}/{total_phases}] Starting {phase_type} phase...[/yellow]")
            else:
                print(f"▶ [{phase_number}/{total_phases}] Starting {phase_type} phase...")
    
    def update_phase(self, phase_name: str, status: str, cost: float = 0.0, 
                    session_id: Optional[str] = None, error: Optional[str] = None):
        """Update phase progress"""
        with self._lock:
            if self.current_milestone and phase_name in self.milestones[self.current_milestone]:
                progress = self.milestones[self.current_milestone][phase_name]
                progress.status = status
                progress.cost = cost
                progress.session_id = session_id
                progress.error = error
                
                if status in ["completed", "failed", "timeout"]:
                    progress.end_time = datetime.now()
                    self.total_cost += cost
                    
                    if RICH_AVAILABLE:
                        if status == "completed":
                            self.console.print(f"[green]✓ {progress.name} phase completed in {progress.duration_str}[/green]")
                        else:
                            self.console.print(f"[red]✗ {progress.name} phase {status}[/red]")
                            if error:
                                self.console.print(f"  [dim]{error}[/dim]")
                    else:
                        symbol = "✓" if status == "completed" else "✗"
                        print(f"{symbol} {progress.name} phase {status} in {progress.duration_str}")
                        if error:
                            print(f"  Error: {error}")
    
    def display_summary(self):
        """Display execution summary"""
        with self._lock:
            total_duration = datetime.now() - self.start_time
            
            if RICH_AVAILABLE:
                # Create summary table
                table = Table(title="Execution Summary", show_header=True, header_style="bold magenta")
                table.add_column("Milestone", style="cyan", no_wrap=True)
                table.add_column("Phase", style="white")
                table.add_column("Status", justify="center")
                table.add_column("Duration", justify="right")
                table.add_column("Cost", justify="right")
                
                for milestone, phases in self.milestones.items():
                    first_phase = True
                    for phase_name, progress in phases.items():
                        status_style = "green" if progress.status == "completed" else "red"
                        status_icon = "✓" if progress.status == "completed" else "✗"
                        
                        table.add_row(
                            milestone if first_phase else "",
                            progress.name,
                            f"[{status_style}]{status_icon}[/{status_style}]",
                            progress.duration_str,
                            f"${progress.cost:.4f}" if progress.cost > 0 else "-"
                        )
                        first_phase = False
                
                self.console.print("\n")
                self.console.print(table)
                self.console.print(f"\n[bold]Total Duration:[/bold] {self._format_duration(total_duration)}")
                self.console.print(f"[bold]Total Cost:[/bold] ${self.total_cost:.4f}")
            else:
                # Simple text summary
                print("\n" + "="*60)
                print("EXECUTION SUMMARY")
                print("="*60)
                
                for milestone, phases in self.milestones.items():
                    print(f"\n{milestone}:")
                    for phase_name, progress in phases.items():
                        status = "✓" if progress.status == "completed" else "✗"
                        cost_str = f"${progress.cost:.4f}" if progress.cost > 0 else ""
                        print(f"  {status} {progress.name}: {progress.duration_str} {cost_str}")
                
                print(f"\nTotal Duration: {self._format_duration(total_duration)}")
                print(f"Total Cost: ${self.total_cost:.4f}")
    
    def display_live_progress(self, update_interval: float = 0.5):
        """Display live progress (rich only)"""
        if not RICH_AVAILABLE:
            return
            
        def generate_progress_display():
            """Generate the current progress display"""
            layout = Layout()
            
            # Create progress bars for current milestone
            if self.current_milestone and self.current_milestone in self.milestones:
                phases = self.milestones[self.current_milestone]
                completed = sum(1 for p in phases.values() if p.status == "completed")
                total = len(phases)
                
                progress_text = f"Milestone Progress: {completed}/{total} phases"
                return Panel(Text(progress_text, justify="center"), title=self.current_milestone)
            
            return Panel("Waiting to start...", title="CC_AUTOMATOR3")
        
        # This would be used with rich.Live for real-time updates
        # For now, just return the display function
        return generate_progress_display
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration in human-readable form"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)


class SimpleProgressBar:
    """Simple progress bar for non-rich environments"""
    
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
    
    def update(self, current: int, message: str = ""):
        """Update progress bar"""
        self.current = current
        percentage = int((current / self.total) * 100)
        filled = int((current / self.total) * self.width)
        bar = "█" * filled + "░" * (self.width - filled)
        
        sys.stdout.write(f"\r[{bar}] {percentage}% {message}")
        sys.stdout.flush()
        
        if current >= self.total:
            print()  # New line when complete