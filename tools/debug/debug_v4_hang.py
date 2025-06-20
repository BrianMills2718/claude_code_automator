#!/usr/bin/env python3
"""
Debug script to trace where V4 execution hangs
"""

import os
import sys
import time
import traceback
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Enable verbose logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set environment for debugging
os.environ['FORCE_SONNET'] = 'true'
os.environ['PYTHONUNBUFFERED'] = '1'

def trace_execution():
    """Trace V4 execution step by step."""
    print("🔍 Starting V4 hang debug trace...\n")
    
    try:
        print("1️⃣ Importing V4 Meta Orchestrator...")
        from src.v4_meta_orchestrator import V4MetaOrchestrator
        print("   ✅ Import successful\n")
        
        print("2️⃣ Setting up project path...")
        project_path = Path("example_projects/ml_portfolio_analyzer")
        print(f"   ✅ Project: {project_path}\n")
        
        print("3️⃣ Creating V4 config...")
        v4_config = {
            'learning_enabled': True,
            'parallel_strategies': False,
            'explain_decisions': True,
            'adaptive_parameters': True,
            'intelligent_stepback': True
        }
        print("   ✅ Config created\n")
        
        print("4️⃣ Initializing V4 Meta Orchestrator...")
        start_time = time.time()
        orchestrator = V4MetaOrchestrator(project_path, v4_config)
        print(f"   ✅ Initialized in {time.time() - start_time:.2f}s\n")
        
        print("5️⃣ Running V4 orchestrator (with asyncio)...")
        
        # Define async wrapper with timeout
        async def run_with_timeout():
            try:
                print("   🔄 Starting asyncio.run()...")
                result = await asyncio.wait_for(orchestrator.run(), timeout=30)
                return result
            except asyncio.TimeoutError:
                print("   ⏱️ Timed out after 30s during orchestrator.run()")
                return False
        
        # Run with detailed monitoring
        print("   🔄 Calling orchestrator.run()...")
        result = asyncio.run(run_with_timeout())
        
        print(f"\n6️⃣ Result: {'✅ Success' if result else '❌ Failed'}")
        
    except Exception as e:
        print(f"\n❌ Exception during execution:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print(f"\n📋 Full traceback:")
        traceback.print_exc()
        
        # Additional debug info
        print(f"\n🔍 Debug info:")
        print(f"   Python version: {sys.version}")
        print(f"   Working directory: {os.getcwd()}")
        print(f"   PYTHONPATH: {sys.path}")

if __name__ == "__main__":
    trace_execution()