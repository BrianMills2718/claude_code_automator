#!/usr/bin/env python3
"""
Analyze historical session data to identify common failure patterns
and cheating behaviors for V4 learning system.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))


def analyze_session_failures(project_dir: Path) -> Dict[str, List[Dict]]:
    """Analyze all session data for failure patterns."""
    cc_automator_dir = project_dir / ".cc_automator"
    if not cc_automator_dir.exists():
        return {}
    
    # Load session data
    sessions_file = cc_automator_dir / "sessions.json"
    if not sessions_file.exists():
        return {}
        
    with open(sessions_file) as f:
        sessions = json.load(f)
    
    # Load checkpoint data
    checkpoints_dir = cc_automator_dir / "checkpoints"
    failure_patterns = defaultdict(list)
    
    for session_key, session_info in sessions.items():
        milestone, phase = session_key.rsplit('_', 1)
        checkpoint_file = checkpoints_dir / f"{phase}_checkpoint.json"
        
        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                checkpoint = json.load(f)
                
            if checkpoint.get("status") == "failed":
                failure_patterns[phase].append({
                    "milestone": milestone,
                    "error": checkpoint.get("error", "Unknown error"),
                    "duration_ms": checkpoint.get("duration_ms", 0),
                    "cost_usd": checkpoint.get("cost_usd", 0)
                })
    
    return dict(failure_patterns)


def identify_cheating_patterns(project_dir: Path) -> List[Dict]:
    """Identify potential cheating behaviors from evidence files."""
    patterns = []
    milestones_dir = project_dir / ".cc_automator" / "milestones"
    
    if not milestones_dir.exists():
        return patterns
    
    for milestone_dir in milestones_dir.iterdir():
        if not milestone_dir.is_dir():
            continue
            
        # Check for minimal evidence files
        evidence_files = list(milestone_dir.glob("*.md")) + list(milestone_dir.glob("*.log"))
        
        for evidence_file in evidence_files:
            content = evidence_file.read_text()
            file_size = len(content)
            
            # Detect suspiciously small evidence files
            if file_size < 100:
                patterns.append({
                    "type": "minimal_evidence",
                    "file": str(evidence_file.relative_to(project_dir)),
                    "size": file_size,
                    "milestone": milestone_dir.name
                })
            
            # Detect generic/templated content
            generic_phrases = [
                "successfully completed",
                "all tests passed",
                "no errors found",
                "working as expected"
            ]
            
            generic_count = sum(1 for phrase in generic_phrases if phrase in content.lower())
            if generic_count >= 3:
                patterns.append({
                    "type": "generic_evidence",
                    "file": str(evidence_file.relative_to(project_dir)),
                    "generic_phrases": generic_count,
                    "milestone": milestone_dir.name
                })
    
    return patterns


def analyze_integration_failures(project_dir: Path) -> List[Dict]:
    """Analyze E2E evidence for integration failures."""
    failures = []
    e2e_logs = list(project_dir.rglob("**/e2e_evidence.log"))
    
    for log_file in e2e_logs:
        content = log_file.read_text()
        
        # Look for command sequence failures
        if "fetch" in content and "analyze" in content:
            if "No data found" in content or "failed" in content.lower():
                failures.append({
                    "type": "integration_failure",
                    "workflow": "fetch_analyze",
                    "file": str(log_file.relative_to(project_dir))
                })
        
        # Look for missing data persistence
        if "Error:" in content or "Traceback" in content:
            failures.append({
                "type": "execution_error",
                "file": str(log_file.relative_to(project_dir))
            })
    
    return failures


def generate_report(project_dirs: List[Path]):
    """Generate comprehensive failure pattern analysis report."""
    all_failures = defaultdict(list)
    all_cheating = []
    all_integration = []
    
    for project_dir in project_dirs:
        print(f"\nAnalyzing {project_dir.name}...")
        
        # Collect failure patterns
        failures = analyze_session_failures(project_dir)
        for phase, phase_failures in failures.items():
            all_failures[phase].extend(phase_failures)
        
        # Collect cheating patterns
        cheating = identify_cheating_patterns(project_dir)
        all_cheating.extend(cheating)
        
        # Collect integration failures
        integration = analyze_integration_failures(project_dir)
        all_integration.extend(integration)
    
    # Generate summary report
    print("\n" + "="*60)
    print("FAILURE PATTERN ANALYSIS REPORT")
    print("="*60)
    
    print("\n1. PHASE FAILURE PATTERNS:")
    for phase, failures in sorted(all_failures.items()):
        if failures:
            print(f"\n  {phase.upper()} Phase:")
            print(f"    Total failures: {len(failures)}")
            print(f"    Average cost per failure: ${sum(f['cost_usd'] for f in failures)/len(failures):.2f}")
            print(f"    Common errors:")
            error_counts = defaultdict(int)
            for f in failures:
                error_type = f['error'].split('\n')[0][:50]
                error_counts[error_type] += 1
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"      - {error}: {count} times")
    
    print("\n2. CHEATING PATTERN DETECTION:")
    if all_cheating:
        cheating_types = defaultdict(int)
        for c in all_cheating:
            cheating_types[c['type']] += 1
        for ctype, count in cheating_types.items():
            print(f"  - {ctype}: {count} instances")
    else:
        print("  No obvious cheating patterns detected")
    
    print("\n3. INTEGRATION FAILURE PATTERNS:")
    if all_integration:
        integration_types = defaultdict(int)
        for i in all_integration:
            integration_types[i['type']] += 1
        for itype, count in integration_types.items():
            print(f"  - {itype}: {count} instances")
    else:
        print("  No integration failures detected")
    
    # Save detailed data for V4 learning
    output_file = Path("failure_patterns_analysis.json")
    with open(output_file, 'w') as f:
        json.dump({
            "phase_failures": dict(all_failures),
            "cheating_patterns": all_cheating,
            "integration_failures": all_integration
        }, f, indent=2)
    
    print(f"\nDetailed analysis saved to: {output_file}")


if __name__ == "__main__":
    # Analyze all example projects
    example_projects = Path("example_projects").glob("*/")
    project_dirs = [p for p in example_projects if p.is_dir() and (p / ".cc_automator").exists()]
    
    if not project_dirs:
        print("No projects with .cc_automator data found")
        sys.exit(1)
    
    generate_report(project_dirs)