#!/usr/bin/env python3
"""
Progress Tracker for CC_AUTOMATOR3
Tracks execution progress and provides visual feedback
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class MilestoneProgress:
    """Progress for a single milestone"""
    name: str
    total_phases: int
    completed_phases: int = 0
    current_phase: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_cost: float = 0.0
    errors_fixed: int = 0
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.total_phases == 0:
            return 0.0
        return (self.completed_phases / self.total_phases) * 100
        
    @property
    def is_complete(self) -> bool:
        """Check if milestone is complete"""
        return self.completed_phases == self.total_phases
        
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None


class ProgressTracker:
    """Tracks and displays progress for cc_automator execution"""
    
    def __init__(self, project_dir: Path, project_name: str):
        self.project_dir = Path(project_dir)
        self.project_name = project_name
        self.progress_file = self.project_dir / ".cc_automator" / "progress.json"
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.milestones: Dict[str, MilestoneProgress] = {}
        self.current_milestone: Optional[str] = None
        self.start_time = datetime.now()
        self.total_cost = 0.0
        
        # Phase status symbols
        self.status_symbols = {
            "completed": "✓",
            "running": "⚡",
            "failed": "✗",
            "pending": "○",
            "timeout": "⏱"
        }
        
    def add_milestone(self, name: str, phase_names: List[str]):
        """Add a milestone to track"""
        self.milestones[name] = MilestoneProgress(
            name=name,
            total_phases=len(phase_names)
        )
        
    def start_milestone(self, name: str):
        """Mark a milestone as started"""
        if name in self.milestones:
            self.current_milestone = name
            self.milestones[name].start_time = datetime.now()
            self.save_progress()
            
    def update_phase(self, milestone_name: str, phase_name: str, 
                     status: str, cost: float = 0.0, errors_fixed: int = 0):
        """Update progress for a phase"""
        if milestone_name not in self.milestones:
            return
            
        milestone = self.milestones[milestone_name]
        milestone.current_phase = phase_name if status == "running" else None
        
        if status == "completed":
            milestone.completed_phases += 1
            milestone.total_cost += cost
            milestone.errors_fixed += errors_fixed
            self.total_cost += cost
            
        if milestone.is_complete:
            milestone.end_time = datetime.now()
            
        self.save_progress()
        
    def display_progress(self):
        """Display current progress with visual representation"""
        print(f"\n{'='*60}")
        print(f"Project: {self.project_name}")
        print(f"{'='*60}")
        
        for milestone_name, milestone in self.milestones.items():
            self._display_milestone_progress(milestone)
            
        # Overall summary
        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"\nTotal: {self._format_duration(duration)} | ${self.total_cost:.2f}")
        
    def _display_milestone_progress(self, milestone: MilestoneProgress):
        """Display progress for a single milestone"""
        # Progress bar
        progress = milestone.progress_percent
        bar_width = 10
        filled = int(bar_width * progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        print(f"\nMilestone: {milestone.name} [{bar}] {progress:.0f}%")
        
        # Phase details (simplified view)
        if milestone.current_phase:
            print(f"  {self.status_symbols['running']} {milestone.current_phase} (running...)")
        
        # Stats
        if milestone.duration_seconds:
            print(f"  Time: {self._format_duration(milestone.duration_seconds)}")
        if milestone.total_cost > 0:
            print(f"  Cost: ${milestone.total_cost:.4f}")
        if milestone.errors_fixed > 0:
            print(f"  Errors Fixed: {milestone.errors_fixed}")
            
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
            
    def save_progress(self):
        """Save current progress to disk"""
        progress_data = {
            "project_name": self.project_name,
            "start_time": self.start_time.isoformat(),
            "total_cost": self.total_cost,
            "current_milestone": self.current_milestone,
            "milestones": {}
        }
        
        for name, milestone in self.milestones.items():
            milestone_dict = asdict(milestone)
            # Convert datetime objects to strings
            for key in ["start_time", "end_time"]:
                if milestone_dict[key]:
                    milestone_dict[key] = milestone_dict[key].isoformat()
            progress_data["milestones"][name] = milestone_dict
            
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
            
    def load_progress(self) -> bool:
        """Load progress from disk"""
        if not self.progress_file.exists():
            return False
            
        try:
            with open(self.progress_file) as f:
                data = json.load(f)
                
            self.project_name = data["project_name"]
            self.start_time = datetime.fromisoformat(data["start_time"])
            self.total_cost = data["total_cost"]
            self.current_milestone = data["current_milestone"]
            
            # Reconstruct milestones
            self.milestones = {}
            for name, milestone_data in data["milestones"].items():
                milestone = MilestoneProgress(**milestone_data)
                # Convert strings back to datetime
                for key in ["start_time", "end_time"]:
                    if milestone_data[key]:
                        setattr(milestone, key, datetime.fromisoformat(milestone_data[key]))
                self.milestones[name] = milestone
                
            return True
            
        except Exception as e:
            print(f"Error loading progress: {e}")
            return False
            
    def get_resume_point(self) -> Optional[Dict[str, Any]]:
        """Get the point to resume from"""
        for milestone_name, milestone in self.milestones.items():
            if not milestone.is_complete:
                # Extract milestone number from name like "Milestone 1"
                milestone_number = int(milestone_name.split()[-1])
                return {
                    "milestone": milestone_number,
                    "milestone_name": milestone_name,
                    "completed_phases": milestone.completed_phases,
                    "next_phase_index": milestone.completed_phases
                }
        return None
        
    def create_summary_report(self) -> str:
        """Create a summary report of the execution"""
        report = []
        report.append(f"# CC_AUTOMATOR Execution Report")
        report.append(f"\n**Project**: {self.project_name}")
        report.append(f"**Start Time**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_duration = (datetime.now() - self.start_time).total_seconds()
        report.append(f"**Total Duration**: {self._format_duration(total_duration)}")
        report.append(f"**Total Cost**: ${self.total_cost:.4f}")
        
        report.append(f"\n## Milestones")
        
        for milestone in self.milestones.values():
            status = "✓ Complete" if milestone.is_complete else "⚡ In Progress"
            report.append(f"\n### {milestone.name} - {status}")
            report.append(f"- Progress: {milestone.completed_phases}/{milestone.total_phases} phases")
            report.append(f"- Cost: ${milestone.total_cost:.4f}")
            
            if milestone.duration_seconds:
                report.append(f"- Duration: {self._format_duration(milestone.duration_seconds)}")
            if milestone.errors_fixed > 0:
                report.append(f"- Errors Fixed: {milestone.errors_fixed}")
                
        return "\n".join(report)


if __name__ == "__main__":
    # Example usage
    tracker = ProgressTracker(Path("."), "Test Project")
    
    # Add a milestone
    tracker.add_milestone("Basic Features", ["research", "planning", "implement", "test"])
    
    # Simulate progress
    tracker.start_milestone("Basic Features")
    tracker.update_phase("Basic Features", "research", "running")
    time.sleep(1)
    tracker.update_phase("Basic Features", "research", "completed", cost=0.15)
    
    tracker.update_phase("Basic Features", "planning", "running")
    
    # Display progress
    tracker.display_progress()
    
    # Save report
    print("\n" + tracker.create_summary_report())