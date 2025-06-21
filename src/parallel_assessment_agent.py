#!/usr/bin/env python3
"""
Parallel Assessment Agent for CC_AUTOMATOR3
Monitors phase execution in parallel and provides intelligent intervention
"""

import subprocess
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from .phase_orchestrator import PhaseStatus


@dataclass
class AssessmentResult:
    """Result of parallel assessment"""
    is_stuck: bool
    specific_issue: Optional[str]
    suggested_fix: Optional[str]
    should_intervene: bool
    confidence: float


class ParallelAssessmentAgent:
    """Monitors phase execution in parallel without interrupting"""
    
    def __init__(self, project_dir: Path, verbose: bool = False):
        self.project_dir = Path(project_dir)
        self.verbose = verbose
        self.assessment_threads = {}
        self.assessment_results = {}
        
    def start_monitoring(self, phase_name: str, phase_type: str, 
                        check_interval: int = 60, 
                        start_after: int = 90) -> threading.Thread:
        """Start monitoring a phase execution in parallel"""
        
        thread = threading.Thread(
            target=self._monitor_phase,
            args=(phase_name, phase_type, check_interval, start_after),
            daemon=True
        )
        
        self.assessment_threads[phase_name] = thread
        thread.start()
        
        if self.verbose:
            print(f"  🔍 Started assessment monitor for {phase_name}")
            
        return thread
    
    def _monitor_phase(self, phase_name: str, phase_type: str,
                      check_interval: int, start_after: int):
        """Monitor phase execution in background"""
        
        # Wait before starting assessment
        time.sleep(start_after)
        
        assessment_count = 0
        while assessment_count < 5:  # Max 5 assessments
            # Check if phase is still running
            if not self._is_phase_running(phase_name):
                break
                
            # Perform assessment
            result = self._assess_phase_progress(phase_name, phase_type)
            
            # Store result
            self.assessment_results[f"{phase_name}_{assessment_count}"] = result
            
            # Log assessment
            if self.verbose or result.should_intervene:
                self._log_assessment(phase_name, result, assessment_count)
                
            # If intervention needed, save guidance
            if result.should_intervene:
                self._save_intervention_guidance(phase_name, result)
                break
                
            assessment_count += 1
            time.sleep(check_interval)
    
    def _is_phase_running(self, phase_name: str) -> bool:
        """Check if phase is still running"""
        # Check for completion marker
        completion_marker = self.project_dir / ".cc_automator" / f"phase_{phase_name}_complete"
        return not completion_marker.exists()
    
    def _get_recent_outputs(self, phase_name: str, num_outputs: int = 5) -> List[str]:
        """Get recent outputs from phase execution"""
        outputs = []
        
        # Check phase output file
        output_file = self.project_dir / ".cc_automator" / "phase_outputs" / f"current_{phase_name}.log"
        if output_file.exists():
            lines = output_file.read_text().split('\n')
            outputs = lines[-num_outputs:] if len(lines) > num_outputs else lines
            
        # Check for any created files
        recent_files = []
        for ext in ['*.py', '*.md', '*.txt']:
            for file_path in self.project_dir.rglob(ext):
                if file_path.stat().st_mtime > time.time() - 300:  # Last 5 minutes
                    recent_files.append(str(file_path.relative_to(self.project_dir)))
                    
        if recent_files:
            outputs.append(f"Recently created/modified files: {', '.join(recent_files[:5])}")
            
        return outputs
    
    def _assess_phase_progress(self, phase_name: str, phase_type: str) -> AssessmentResult:
        """Use Claude to assess if phase is making progress"""
        
        recent_outputs = self._get_recent_outputs(phase_name)
        
        # Get any previous attempts
        previous_assessments = [
            v for k, v in self.assessment_results.items() 
            if k.startswith(phase_name)
        ]
        
        assessment_prompt = f"""
You are monitoring another Claude agent executing the {phase_type} phase of a coding project.

Phase type: {phase_type}
Phase name: {phase_name}
Time elapsed: Check started after 90+ seconds

Recent activity:
{chr(10).join(recent_outputs) if recent_outputs else "No recent outputs detected"}

Previous assessments: {len(previous_assessments)}

Analyze the situation and determine:

1. Is the agent making real progress or stuck in a loop?
2. What specific issue is the agent facing (if any)?
3. What would help the agent succeed?
4. Should we intervene or let it continue?

Respond in JSON format:
{{
    "is_stuck": true/false,
    "specific_issue": "exact problem identified or null",
    "suggested_fix": "specific guidance to help or null",
    "should_intervene": true/false,
    "confidence": 0.0-1.0
}}

Be specific about issues like:
- Import errors that keep recurring
- File not found errors
- Trying to test non-existent functions
- Creating tests that don't match implementation
- Infinite loops of similar attempts
"""
        
        try:
            # Run assessment
            result = subprocess.run(
                ["claude", "-p", assessment_prompt, "--output-format", "json", "--max-turns", "1"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                assessment_data = json.loads(result.stdout)
                return AssessmentResult(
                    is_stuck=assessment_data.get("is_stuck", False),
                    specific_issue=assessment_data.get("specific_issue"),
                    suggested_fix=assessment_data.get("suggested_fix"),
                    should_intervene=assessment_data.get("should_intervene", False),
                    confidence=assessment_data.get("confidence", 0.5)
                )
                
        except Exception as e:
            if self.verbose:
                print(f"  ⚠️  Assessment failed: {e}")
                
        # Default to not intervening
        return AssessmentResult(
            is_stuck=False,
            specific_issue=None,
            suggested_fix=None,
            should_intervene=False,
            confidence=0.0
        )
    
    def _log_assessment(self, phase_name: str, result: AssessmentResult, count: int):
        """Log assessment result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if result.should_intervene:
            print(f"\n  🚨 [{timestamp}] Assessment #{count} for {phase_name}:")
            print(f"     Stuck: {result.is_stuck} (confidence: {result.confidence:.2f})")
            if result.specific_issue:
                print(f"     Issue: {result.specific_issue}")
            if result.suggested_fix:
                print(f"     Suggestion: {result.suggested_fix}")
            print(f"     Intervention recommended: {result.should_intervene}")
        elif self.verbose:
            print(f"  ✅ [{timestamp}] {phase_name} making progress (assessment #{count})")
    
    def _save_intervention_guidance(self, phase_name: str, result: AssessmentResult):
        """Save intervention guidance for retry"""
        guidance_file = self.project_dir / ".cc_automator" / "assessment_guidance" / f"{phase_name}_guidance.json"
        guidance_file.parent.mkdir(parents=True, exist_ok=True)
        
        guidance = {
            "phase_name": phase_name,
            "timestamp": datetime.now().isoformat(),
            "is_stuck": result.is_stuck,
            "specific_issue": result.specific_issue,
            "suggested_fix": result.suggested_fix,
            "confidence": result.confidence
        }
        
        with open(guidance_file, 'w') as f:
            json.dump(guidance, f, indent=2)
            
        if self.verbose:
            print(f"  💾 Saved intervention guidance to: {guidance_file}")
    
    def get_retry_context(self, phase_name: str) -> Optional[str]:
        """Get retry context based on assessment"""
        guidance_file = self.project_dir / ".cc_automator" / "assessment_guidance" / f"{phase_name}_guidance.json"
        
        if not guidance_file.exists():
            return None
            
        try:
            with open(guidance_file) as f:
                guidance = json.load(f)
                
            if guidance.get("suggested_fix"):
                return f"""
## Previous Attempt Assessment

The previous attempt encountered issues:
- Issue: {guidance.get('specific_issue', 'Unknown')}
- Suggestion: {guidance.get('suggested_fix')}

Please address this specific issue in your approach.
"""
        except Exception:
            pass
            
        return None
    
    def stop_monitoring(self, phase_name: str):
        """Stop monitoring a specific phase"""
        if phase_name in self.assessment_threads:
            # Thread will stop on next check when phase is complete
            self.assessment_threads.pop(phase_name, None)