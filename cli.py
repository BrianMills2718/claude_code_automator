#!/usr/bin/env python3
"""
CLI entry point for CC_AUTOMATOR4
Handles command-line parsing and launches the orchestrator
Supports both V3 and V4 execution modes
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

from src.orchestrator import CCAutomatorOrchestrator
from src.v4_meta_orchestrator import V4MetaOrchestrator


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CC_AUTOMATOR4 - Intelligent Autonomous Code Generation System",
        epilog="""
Execution Modes:
  python cli.py --project myapp                    # V3 mode (default)
  python cli.py --project myapp --v4               # V4 intelligent meta-agent mode
  python cli.py --project myapp --v4 --explain    # V4 with decision explanations

Model Selection Examples:
  python cli.py --project myapp                    # Default: Opus for complex, Sonnet for lint/typecheck
  python cli.py --project myapp --force-sonnet    # Use Sonnet for ALL phases (cost-effective)
  python cli.py --project myapp --model claude-opus-4-20250514  # Force specific model
  
V4 Features:
  --v4                    # Enable V4 intelligent orchestration
  --v4-learning          # Enable failure pattern learning (default: on)
  --v4-parallel          # Enable parallel strategy exploration
  --explain              # Explain V4 decisions during execution

Environment Variables:
  FORCE_SONNET=true      # Use Sonnet for all phases
  CLAUDE_MODEL=<model>   # Override model for all phases
  V4_MODE=true           # Enable V4 by default
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
                       help="Override model for all phases (e.g., claude-opus-4-20250514)")
    
    # V4 options
    parser.add_argument("--v4", action="store_true",
                       help="Enable V4 intelligent meta-agent orchestration")
    parser.add_argument("--v4-learning", action="store_true", default=None,
                       help="Enable V4 failure pattern learning (default: on with --v4)")
    parser.add_argument("--v4-parallel", action="store_true",
                       help="Enable V4 parallel strategy exploration")
    parser.add_argument("--explain", action="store_true",
                       help="Explain V4 decisions during execution")
    
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
    
    # Check for V4 mode from environment or args
    use_v4 = args.v4 or os.environ.get('V4_MODE', '').lower() == 'true'
    
    if use_v4:
        # V4 intelligent orchestration
        print("🚀 Starting CC_AUTOMATOR4 with V4 Intelligent Meta-Agent")
        
        # Configure V4 options
        v4_config = {
            'learning_enabled': args.v4_learning if args.v4_learning is not None else True,
            'parallel_strategies': args.v4_parallel,
            'explain_decisions': args.explain,
            'adaptive_parameters': True,
            'intelligent_stepback': True
        }
        
        # Create V4 orchestrator
        orchestrator = V4MetaOrchestrator(project_dir, v4_config)
        
        try:
            # V4 uses async execution
            return asyncio.run(orchestrator.run())
        except KeyboardInterrupt:
            print("\n\nExecution interrupted by user.")
            print("You can resume with: python cli.py --v4 --resume")
            return 1
        except Exception as e:
            print(f"\nV4 orchestration error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    else:
        # V3 standard orchestration
        print("Starting CC_AUTOMATOR4 in V3 compatibility mode")
        
        # Create and run V3 orchestrator
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