#!/usr/bin/env python3
"""
File-Level Parallel Executor for CC_AUTOMATOR3
Executes mechanical fixes (lint, typecheck) on individual files in parallel
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from phase_orchestrator import Phase, PhaseStatus, create_phase


@dataclass
class FileError:
    """Represents an error in a specific file"""
    file_path: str
    line: int
    column: int
    error_code: str
    message: str
    

class FileParallelExecutor:
    """Executes mechanical fixes on individual files in parallel"""
    
    def __init__(self, project_dir: Path, max_workers: int = 4):
        self.project_dir = Path(project_dir)
        self.max_workers = max_workers
        
    def parse_flake8_output(self, output: str) -> Dict[str, List[FileError]]:
        """Parse flake8 output and group errors by file"""
        errors_by_file = {}
        
        for line in output.strip().split('\n'):
            if not line or line.startswith('flake8:'):
                continue
                
            # Format: path/to/file.py:line:col: CODE message
            try:
                parts = line.split(':', 4)
                if len(parts) >= 4:
                    file_path = parts[0]
                    line_num = int(parts[1])
                    col_num = int(parts[2])
                    
                    # Extract error code and message
                    error_part = parts[3].strip()
                    code_parts = error_part.split(' ', 1)
                    error_code = code_parts[0]
                    message = code_parts[1] if len(code_parts) > 1 else ""
                    
                    # Only include F-errors
                    if error_code.startswith('F'):
                        error = FileError(
                            file_path=file_path,
                            line=line_num,
                            column=col_num,
                            error_code=error_code,
                            message=message
                        )
                        
                        if file_path not in errors_by_file:
                            errors_by_file[file_path] = []
                        errors_by_file[file_path].append(error)
            except (ValueError, IndexError):
                continue
                
        return errors_by_file
        
    def parse_mypy_output(self, output: str) -> Dict[str, List[FileError]]:
        """Parse mypy output and group errors by file"""
        errors_by_file = {}
        
        for line in output.strip().split('\n'):
            if not line or line.startswith('Success:') or line.startswith('Found'):
                continue
                
            # Format: path/to/file.py:line: error: message
            try:
                if ': error:' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 2:
                        file_path = parts[0]
                        line_num = int(parts[1])
                        
                        # Extract error message
                        error_part = parts[2].strip()
                        if error_part.startswith('error:'):
                            message = error_part[6:].strip()
                        else:
                            message = error_part
                        
                        error = FileError(
                            file_path=file_path,
                            line=line_num,
                            column=0,
                            error_code="TYPE",
                            message=message
                        )
                        
                        if file_path not in errors_by_file:
                            errors_by_file[file_path] = []
                        errors_by_file[file_path].append(error)
            except (ValueError, IndexError):
                continue
                
        return errors_by_file
    
    def create_file_fix_prompt(self, file_path: str, errors: List[FileError], 
                              fix_type: str) -> str:
        """Create a prompt for fixing errors in a specific file"""
        
        # Read the file content
        full_path = self.project_dir / file_path
        if not full_path.exists():
            return None
            
        with open(full_path) as f:
            file_content = f.read()
        
        # Format errors
        error_list = []
        for error in errors:
            if fix_type == "lint":
                error_list.append(f"Line {error.line}:{error.column} - {error.error_code}: {error.message}")
            else:  # mypy
                error_list.append(f"Line {error.line} - {error.message}")
        
        prompt = f"""## Fix {fix_type} errors in {file_path}

### File Content:
```python
{file_content}
```

### Errors to Fix:
{chr(10).join(error_list)}

### Instructions:
1. Fix ONLY the errors listed above
2. Do NOT change any other code
3. Maintain exact formatting and style
4. Use type hints properly (for mypy errors)
5. Remove unused imports (for F401 errors)

Fix the errors and save the file.

When done, create file: {self.project_dir}/.cc_automator/phase_{fix_type}_{Path(file_path).stem}_complete
Write to it: PHASE_COMPLETE
"""
        
        return prompt
    
    def execute_file_fix(self, file_path: str, errors: List[FileError], 
                        fix_type: str, orchestrator) -> Dict[str, Any]:
        """Execute fix for a single file"""
        
        print(f"  🔧 Fixing {fix_type} errors in {file_path} ({len(errors)} errors)")
        
        prompt = self.create_file_fix_prompt(file_path, errors, fix_type)
        if not prompt:
            return {"status": "skipped", "file": file_path, "reason": "File not found"}
        
        # Create a phase for this file
        phase = create_phase(
            name=f"{fix_type}_{Path(file_path).stem}",
            description=f"Fix {fix_type} errors in {file_path}",
            prompt=prompt
        )
        
        # Use shorter timeout for file-level fixes
        phase.timeout_seconds = 300  # 5 minutes per file
        phase.max_turns = 10  # Fewer turns needed for focused fixes
        
        # Execute the fix
        result = orchestrator.execute_phase(phase)
        
        return {
            "status": "completed" if phase.status == PhaseStatus.COMPLETED else "failed",
            "file": file_path,
            "errors_fixed": len(errors),
            "cost": phase.cost_usd,
            "duration": phase.duration_ms,
            "error": phase.error
        }
    
    def execute_parallel_lint(self, orchestrator) -> Tuple[bool, List[Dict]]:
        """Execute flake8 and fix errors in parallel by file"""
        
        print("\n🔍 Running flake8 to find errors...")
        
        # Run flake8
        result = subprocess.run(
            ["flake8", "--select=F", "--exclude=venv,__pycache__,.git", "."],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ No flake8 F-errors found")
            return True, []
        
        # Parse errors by file
        errors_by_file = self.parse_flake8_output(result.stdout)
        
        if not errors_by_file:
            print("✅ No F-errors to fix")
            return True, []
        
        print(f"\n📊 Found F-errors in {len(errors_by_file)} files")
        for file_path, errors in errors_by_file.items():
            print(f"  - {file_path}: {len(errors)} errors")
        
        print(f"\n🚀 Fixing errors in parallel (max {self.max_workers} workers)...")
        
        # Execute fixes in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file fixes
            future_to_file = {
                executor.submit(
                    self.execute_file_fix, 
                    file_path, 
                    errors, 
                    "lint", 
                    orchestrator
                ): file_path
                for file_path, errors in errors_by_file.items()
            }
            
            # Process results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result["status"] == "completed":
                        print(f"  ✅ Fixed {file_path}")
                    else:
                        print(f"  ❌ Failed to fix {file_path}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"  ❌ Error fixing {file_path}: {e}")
                    results.append({
                        "status": "failed",
                        "file": file_path,
                        "error": str(e)
                    })
        
        # Verify all errors fixed
        print("\n🔍 Verifying fixes...")
        verify_result = subprocess.run(
            ["flake8", "--select=F", "--exclude=venv,__pycache__,.git", "."],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        success = verify_result.returncode == 0
        if success:
            print("✅ All F-errors fixed successfully")
        else:
            print("❌ Some F-errors remain")
            
        return success, results
    
    def execute_parallel_typecheck(self, orchestrator) -> Tuple[bool, List[Dict]]:
        """Execute mypy and fix errors in parallel by file"""
        
        print("\n🔍 Running mypy --strict to find type errors...")
        
        # Run mypy
        result = subprocess.run(
            ["mypy", "--strict", "."],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ No mypy errors found")
            return True, []
        
        # Parse errors by file
        errors_by_file = self.parse_mypy_output(result.stdout)
        
        if not errors_by_file:
            print("✅ No type errors to fix")
            return True, []
        
        print(f"\n📊 Found type errors in {len(errors_by_file)} files")
        for file_path, errors in errors_by_file.items():
            print(f"  - {file_path}: {len(errors)} errors")
        
        print(f"\n🚀 Fixing errors in parallel (max {self.max_workers} workers)...")
        
        # Execute fixes in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all file fixes
            future_to_file = {
                executor.submit(
                    self.execute_file_fix, 
                    file_path, 
                    errors, 
                    "typecheck", 
                    orchestrator
                ): file_path
                for file_path, errors in errors_by_file.items()
            }
            
            # Process results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result["status"] == "completed":
                        print(f"  ✅ Fixed {file_path}")
                    else:
                        print(f"  ❌ Failed to fix {file_path}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"  ❌ Error fixing {file_path}: {e}")
                    results.append({
                        "status": "failed", 
                        "file": file_path,
                        "error": str(e)
                    })
        
        # Verify all errors fixed
        print("\n🔍 Verifying fixes...")
        verify_result = subprocess.run(
            ["mypy", "--strict", "."],
            cwd=self.project_dir,
            capture_output=True,
            text=True
        )
        
        success = verify_result.returncode == 0
        if success:
            print("✅ All type errors fixed successfully")
        else:
            print("❌ Some type errors remain")
            
        return success, results