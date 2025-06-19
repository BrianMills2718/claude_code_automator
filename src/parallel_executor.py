#!/usr/bin/env python3
"""
Parallel Executor for CC_AUTOMATOR3
Implements git worktree-based parallelization for mechanical phases
"""

import subprocess
import threading
import queue
import time
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future

from .phase_orchestrator import Phase, PhaseOrchestrator, PhaseStatus


@dataclass
class ParallelPhaseGroup:
    """Group of phases that can run in parallel"""
    phases: List[Phase]
    can_parallelize: bool = True
    
    
class ParallelExecutor:
    """Executes phases in parallel using git worktrees"""
    
    # Define which phases can run in parallel
    PARALLEL_GROUPS = {
        "mechanical_fixes": ["lint", "typecheck"],
        "test_suite": ["test", "integration"],
    }
    
    def __init__(self, project_dir: Path, max_workers: int = 3):
        self.project_dir = Path(project_dir)
        self.max_workers = max_workers
        self.worktree_base = self.project_dir.parent / f"{self.project_dir.name}_worktrees"
        self.results_queue = queue.Queue()
        
    def can_parallelize_phases(self, phase_types: List[str]) -> List[ParallelPhaseGroup]:
        """Determine which phases can run in parallel"""
        
        groups = []
        remaining_phases = phase_types.copy()
        
        # Check each parallel group
        for group_name, group_phases in self.PARALLEL_GROUPS.items():
            # Find phases in this group
            parallel_phases = [p for p in remaining_phases if p in group_phases]
            
            if len(parallel_phases) > 1:
                # Can parallelize these
                groups.append(ParallelPhaseGroup(parallel_phases, True))
                for p in parallel_phases:
                    remaining_phases.remove(p)
        
        # Add remaining phases as sequential
        for phase in remaining_phases:
            groups.append(ParallelPhaseGroup([phase], False))
            
        return groups
    
    def setup_worktree(self, branch_name: str) -> Path:
        """Create a git worktree for parallel execution"""
        
        worktree_path = self.worktree_base / branch_name
        
        # Remove if exists
        if worktree_path.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)], 
                         cwd=self.project_dir, capture_output=True)
        
        # Create new worktree
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")
            
        return worktree_path
    
    def cleanup_worktree(self, worktree_path: Path):
        """Remove a git worktree"""
        
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=self.project_dir,
            capture_output=True
        )
    
    def execute_phase_in_worktree(self, phase: Phase, worktree_name: str) -> Dict:
        """Execute a single phase in its own worktree"""
        
        print(f"\n🔀 Starting parallel execution of {phase.name} in worktree")
        
        try:
            # Setup worktree
            worktree_path = self.setup_worktree(worktree_name)
            
            # Copy any necessary files (like .cc_automator directory)
            cc_dir = self.project_dir / ".cc_automator"
            if cc_dir.exists():
                shutil.copytree(cc_dir, worktree_path / ".cc_automator", dirs_exist_ok=True)
            
            # Execute phase in worktree
            orchestrator = PhaseOrchestrator(phase.name, str(worktree_path))
            result = orchestrator.execute_phase(phase)
            
            # If successful, merge changes back
            if phase.status == PhaseStatus.COMPLETED:
                self._merge_worktree_changes(worktree_path, worktree_name)
            
            # Cleanup
            self.cleanup_worktree(worktree_path)
            
            return result
            
        except Exception as e:
            print(f"❌ Error in parallel execution of {phase.name}: {e}")
            phase.status = PhaseStatus.FAILED
            phase.error = str(e)
            return {"status": "failed", "error": str(e)}
    
    def _merge_worktree_changes(self, worktree_path: Path, branch_name: str):
        """Merge changes from worktree back to main branch"""
        
        # First, commit any changes in the worktree
        subprocess.run(["git", "add", "-A"], cwd=worktree_path)
        subprocess.run(
            ["git", "commit", "-m", f"Auto-commit from parallel phase: {branch_name}"],
            cwd=worktree_path
        )
        
        # Switch back to main branch and merge
        current_branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        # Merge the worktree branch
        result = subprocess.run(
            ["git", "merge", branch_name, "--no-ff", "-m", f"Merge parallel phase: {branch_name}"],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"⚠️  Merge conflict for {branch_name}, may need manual resolution")
    
    def execute_parallel_group(self, phases: List[Phase], 
                             orchestrator: PhaseOrchestrator) -> List[Dict]:
        """Execute a group of phases in parallel"""
        
        print(f"\n🚀 Executing {len(phases)} phases in parallel: {[p.name for p in phases]}")
        
        with ThreadPoolExecutor(max_workers=min(len(phases), self.max_workers)) as executor:
            # Submit all phases
            futures = {}
            for i, phase in enumerate(phases):
                worktree_name = f"parallel_{phase.name}_{int(time.time())}"
                future = executor.submit(self.execute_phase_in_worktree, phase, worktree_name)
                futures[future] = phase
            
            # Collect results
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=phases[0].timeout_seconds)
                    results.append(result)
                except Exception as e:
                    phase = futures[future]
                    print(f"❌ Phase {phase.name} failed: {e}")
                    results.append({"status": "failed", "error": str(e)})
        
        return results
    
    def should_parallelize_phase_group(self, phase_types: List[str], 
                                     milestone_name: str) -> bool:
        """Determine if a group of phases should be parallelized"""
        
        # Don't parallelize if git is not clean
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        if status.stdout.strip():
            print("⚠️  Git has uncommitted changes, skipping parallelization")
            return False
        
        # Check if phases are in parallel groups
        for group_phases in self.PARALLEL_GROUPS.values():
            if all(p in group_phases for p in phase_types):
                return True
                
        return False