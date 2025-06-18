#!/usr/bin/env python3
"""
Project Setup CLI - Dynamic project creation from user intent
"""

import argparse
import sys
from pathlib import Path
from project_discovery import run_project_discovery


def main():
    """Main CLI entry point for dynamic project setup"""
    
    parser = argparse.ArgumentParser(
        description="CC_AUTOMATOR4 - Dynamic Project Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python project_setup_cli.py
  python project_setup_cli.py --project my_new_project
  python project_setup_cli.py --project /path/to/project
        """
    )
    
    parser.add_argument(
        "--project", 
        type=str,
        help="Project directory (default: current directory)"
    )
    
    parser.add_argument(
        "--openai-api-key",
        type=str,
        help="OpenAI API key for auto-selecting OpenAI-based approaches"
    )
    
    parser.add_argument(
        "--auto-openai",
        action="store_true",
        help="Automatically select OpenAI-based approaches when available"
    )
    
    args = parser.parse_args()
    
    # Determine project directory
    if args.project:
        project_dir = Path(args.project).resolve()
        project_dir.mkdir(parents=True, exist_ok=True)
    else:
        project_dir = Path.cwd()
    
    print(f"🚀 Setting up project in: {project_dir}")
    print()
    
    try:
        # Set OpenAI API key if provided
        if args.openai_api_key:
            import os
            os.environ['OPENAI_API_KEY'] = args.openai_api_key
            print(f"🔑 OpenAI API key configured")
            print()
        
        # Run the discovery wizard
        discovery = run_project_discovery(
            project_dir, 
            openai_api_key=args.openai_api_key,
            auto_select_openai=args.auto_openai
        )
        
        print("="*60)
        print("🎉 PROJECT SETUP COMPLETE!")
        print("="*60)
        print(f"Project: {discovery.project_type}")
        print(f"Location: {project_dir}")
        print(f"Milestones: {len(discovery.suggested_milestones)}")
        print(f"Dependencies: {len(discovery.final_dependencies)}")
        print()
        print("Next steps:")
        print(f"1. cd {project_dir}")
        
        # Check if API keys are needed
        api_deps = [dep for dep in discovery.final_dependencies if "api_key_needed" in dep]
        if api_deps:
            print("2. Set required API keys:")
            for dep in api_deps:
                print(f"   export {dep['api_key_needed']}=\"your-key-here\"")
        
        print(f"3. python {Path(__file__).parent / 'cli.py'} --force-sonnet")
        print()
        print("✨ Ready to build your project!")
        
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()