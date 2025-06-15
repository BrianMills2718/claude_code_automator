#!/usr/bin/env python3
"""
CLI entry point for CC_AUTOMATOR3
Handles command-line parsing and launches the orchestrator
"""

import sys
import argparse
from pathlib import Path

from orchestrator import CCAutomatorOrchestrator


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CC_AUTOMATOR3 - Autonomous Code Generation System"
    )
    
    # Project options
    parser.add_argument("--project", type=str, help="Project directory (default: current)")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--milestone", type=int, help="Run specific milestone only")
    
    # Parallelization options
    parser.add_argument("--parallel", action="store_true", default=True,
                       help="Enable parallel execution (default: enabled)")
    parser.add_argument("--no-parallel", action="store_true", 
                       help="Disable parallel execution")
    parser.add_argument("--file-parallel", action="store_true", default=True,
                       help="Enable file-level parallelization for lint/typecheck (default: enabled)")
    parser.add_argument("--no-file-parallel", action="store_true",
                       help="Disable file-level parallelization")
    
    # Advanced options (Phase 4)
    parser.add_argument("--docker", action="store_true",
                       help="Run mechanical phases in Docker containers")
    parser.add_argument("--visual", action="store_true", default=True,
                       help="Enable visual progress display (default: enabled)")
    parser.add_argument("--no-visual", action="store_true",
                       help="Disable visual progress display")
    
    # Debug options
    parser.add_argument("--verbose", action="store_true",
                       help="Show verbose output including all phase details")
    
    args = parser.parse_args()
    
    # Determine project directory
    project_dir = Path(args.project) if args.project else Path.cwd()
    
    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        return 1
        
    # Determine feature flags
    use_parallel = not args.no_parallel
    use_visual = not args.no_visual
    use_file_parallel = not args.no_file_parallel
        
    # Create and run orchestrator
    orchestrator = CCAutomatorOrchestrator(
        project_dir=project_dir,
        resume=args.resume,
        use_parallel=use_parallel,
        use_docker=args.docker,
        use_visual=use_visual,
        specific_milestone=args.milestone,
        verbose=args.verbose,
        use_file_parallel=use_file_parallel
    )
    
    try:
        return orchestrator.run()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
        print("You can resume with: python cli.py --resume")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())