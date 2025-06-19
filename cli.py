#!/usr/bin/env python3
"""
CLI entry point for CC_AUTOMATOR3
Handles command-line parsing and launches the orchestrator
"""

import sys
import os
import argparse
from pathlib import Path

from src.orchestrator import CCAutomatorOrchestrator


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CC_AUTOMATOR3 - Autonomous Code Generation System",
        epilog="""
Model Selection Examples:
  python cli.py --project myapp                    # Default: Opus for complex, Sonnet for lint/typecheck
  python cli.py --project myapp --force-sonnet    # Use Sonnet for ALL phases (cost-effective)
  python cli.py --project myapp --model claude-3-5-sonnet-20241022  # Force specific model for ALL phases
  
Environment Variables:
  FORCE_SONNET=true     # Use Sonnet for all phases
  CLAUDE_MODEL=<model>  # Override model for all phases
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
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
    parser.add_argument("--infinite", action="store_true",
                       help="Run forever until success (no step-back limits)")
    
    # Model selection options
    parser.add_argument("--force-sonnet", action="store_true",
                       help="Use Sonnet model for ALL phases (cost-effective)")
    parser.add_argument("--model", type=str,
                       help="Override model for all phases (e.g., claude-3-5-sonnet-20241022)")
    
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
    
    # Set model selection environment variables
    if args.force_sonnet:
        os.environ['FORCE_SONNET'] = 'true'
    if args.model:
        os.environ['CLAUDE_MODEL'] = args.model
        
    # Create and run orchestrator
    orchestrator = CCAutomatorOrchestrator(
        project_dir=project_dir,
        resume=args.resume,
        use_parallel=use_parallel,
        use_docker=args.docker,
        use_visual=use_visual,
        specific_milestone=args.milestone,
        verbose=args.verbose,
        use_file_parallel=use_file_parallel,
        infinite_mode=args.infinite
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