#!/usr/bin/env python3
"""
Progress display for CC_AUTOMATOR3
Handles all UI and progress visualization
"""

from typing import Optional

# Try to import visual progress display
try:
    from visual_progress import VisualProgressDisplay
    VISUAL_AVAILABLE = True
except ImportError:
    VISUAL_AVAILABLE = False


class ProgressDisplay:
    """Unified progress display handler"""
    
    def __init__(self, use_visual: bool = True):
        self.use_visual = use_visual and VISUAL_AVAILABLE
        self.visual_progress = None
        
        if self.use_visual:
            self.visual_progress = VisualProgressDisplay()
            
    def show_phase_start(self, phase_type: str, current: int, total: int):
        """Display phase start information"""
        if self.visual_progress:
            self.visual_progress.start_phase(phase_type, phase_type, current, total)
        else:
            print(f"\n[{current}/{total}] {phase_type.upper()} Phase")
            
    def show_phase_complete(self, phase_name: str, status: str, 
                          cost: Optional[float] = None,
                          session_id: Optional[str] = None,
                          error: Optional[str] = None):
        """Display phase completion information"""
        if self.visual_progress:
            self.visual_progress.update_phase(phase_name, status, 
                                            cost=cost,
                                            session_id=session_id,
                                            error=error)
        else:
            # Standard output for non-visual mode is handled by PhaseOrchestrator
            pass
            
    def show_progress_bar(self, milestone_name: str, completed: int, total: int,
                         elapsed_time: float, total_cost: float):
        """Display overall progress bar"""
        if self.visual_progress:
            self.visual_progress.update_milestone(milestone_name, completed, total,
                                                elapsed_time, total_cost)
        else:
            # Simple text progress
            percent = int((completed / total) * 100) if total > 0 else 0
            bar_length = 40
            filled = int(bar_length * completed / total) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_length - filled)
            
            print(f"\nProgress: {milestone_name}")
            print(f"[{bar}] {percent}%")
            print(f"Completed: {completed}/{total} phases")
            print(f"Elapsed: {self._format_duration(elapsed_time)}")
            print(f"Cost: ${total_cost:.4f}")
            
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"