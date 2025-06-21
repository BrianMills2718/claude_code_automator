#!/usr/bin/env python3
"""
Architecture Validator for CC_AUTOMATOR4
Catches structural issues before mechanical phases waste cycles
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any
import subprocess


class ArchitectureValidator:
    """Validates code architecture before mechanical phases"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.issues = []
        
    def validate_all(self) -> Tuple[bool, List[str]]:
        """Run all architectural validation checks"""
        self.issues = []
        
        # Core architectural checks
        self._check_code_structure()
        self._check_import_structure() 
        self._check_design_patterns()
        self._check_complexity_metrics()
        self._check_antipatterns()
        
        return len(self.issues) == 0, self.issues
    
    def _check_code_structure(self):
        """Check basic code structure constraints"""
        
        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                lines = content.split('\n')
                
                # File size check
                if len(lines) > 1000:
                    self.issues.append(
                        f"File too large: {py_file.relative_to(self.project_dir)} ({len(lines)} lines > 1000)"
                    )
                
                # Parse AST for function/class analysis
                try:
                    tree = ast.parse(content)
                    self._analyze_ast_structure(tree, py_file)
                except SyntaxError:
                    self.issues.append(
                        f"Syntax error in {py_file.relative_to(self.project_dir)} - cannot analyze structure"
                    )
                    
            except Exception:
                continue
    
    def _analyze_ast_structure(self, tree: ast.AST, file_path: Path):
        """Analyze AST for structural issues"""
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Function length check
                func_lines = node.end_lineno - node.lineno + 1
                if func_lines > 50:
                    self.issues.append(
                        f"Function too long: {node.name} in {file_path.relative_to(self.project_dir)} ({func_lines} lines > 50)"
                    )
                
                # Parameter count check
                if len(node.args.args) > 5:
                    self.issues.append(
                        f"Too many parameters: {node.name} in {file_path.relative_to(self.project_dir)} ({len(node.args.args)} > 5)"
                    )
                
                # Nesting depth check
                self._check_nesting_depth(node, file_path, node.name)
                
            elif isinstance(node, ast.ClassDef):
                # Class size check (approximate by counting methods)
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    self.issues.append(
                        f"Class too large: {node.name} in {file_path.relative_to(self.project_dir)} ({len(methods)} methods > 20)"
                    )
    
    def _check_nesting_depth(self, node: ast.AST, file_path: Path, func_name: str, depth: int = 0):
        """Check for excessive nesting depth"""
        
        if depth > 4:
            self.issues.append(
                f"Excessive nesting: {func_name} in {file_path.relative_to(self.project_dir)} (depth > 4)"
            )
            return
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                self._check_nesting_depth(child, file_path, func_name, depth + 1)
    
    def _check_import_structure(self):
        """Check for import structure issues"""
        
        # Check for missing __init__.py files in src directories
        src_dirs = []
        for py_file in self.project_dir.rglob("*.py"):
            if "src" in py_file.parts:
                src_dirs.append(py_file.parent)
        
        for src_dir in set(src_dirs):
            init_file = src_dir / "__init__.py"
            if not init_file.exists():
                self.issues.append(
                    f"Missing __init__.py in {src_dir.relative_to(self.project_dir)}"
                )
        
        # Check for circular imports (simplified)
        self._detect_circular_imports()
    
    def _detect_circular_imports(self):
        """Detect potential circular import issues"""
        
        import_graph = {}
        
        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                
                # Store relative imports within project
                project_imports = [imp for imp in imports if not imp.startswith('.') and 'src' in imp]
                if project_imports:
                    import_graph[str(py_file.relative_to(self.project_dir))] = project_imports
                    
            except Exception:
                continue
        
        # Simple cycle detection (this is a simplified check)
        for file_path, imports in import_graph.items():
            for imp in imports:
                if file_path.replace('.py', '').replace('/', '.') in str(imports):
                    self.issues.append(
                        f"Potential circular import: {file_path} <-> {imp}"
                    )
    
    def _check_design_patterns(self):
        """Check for design pattern violations"""
        
        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Check for hardcoded values that should be constants
                hardcode_patterns = [
                    'localhost:',
                    'http://',
                    'https://',
                    '127.0.0.1'
                ]
                
                # Check for hardcoded API keys/passwords (but not when using settings)
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    line_strip = line.strip()
                    if ('api_key = ' in line_strip or 'password = ' in line_strip):
                        # Allow if getting from settings, env, or config
                        if not any(safe_pattern in line_strip for safe_pattern in [
                            'settings.', 'os.environ', 'config.', '.env', 'getenv'
                        ]):
                            self.issues.append(
                                f"Hardcoded credential in {py_file.relative_to(self.project_dir)}:{line_num}"
                            )
                
                # Check other hardcoded patterns
                if any(pattern in content for pattern in hardcode_patterns):
                    self.issues.append(
                        f"Hardcoded configuration values in {py_file.relative_to(self.project_dir)}"
                    )
                
                # Check for mixed concerns (UI + business logic)
                has_ui = any(pattern in content for pattern in ['print(', 'input(', 'click.'])
                has_business = any(pattern in content for pattern in ['def calculate', 'def process', 'def validate'])
                
                if has_ui and has_business and 'main.py' not in str(py_file):
                    self.issues.append(
                        f"Mixed UI and business logic in {py_file.relative_to(self.project_dir)}"
                    )
                
            except Exception:
                continue
    
    def _check_complexity_metrics(self):
        """Check for complexity issues"""
        
        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = self._calculate_cyclomatic_complexity(node)
                        if complexity > 10:
                            self.issues.append(
                                f"High cyclomatic complexity: {node.name} in {py_file.relative_to(self.project_dir)} (complexity: {complexity})"
                            )
                            
            except Exception:
                continue
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""
        
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Each decision point adds to complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ExceptHandler,)):
                complexity += 1
        
        return complexity
    
    def _check_antipatterns(self):
        """Check for common antipatterns"""
        
        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # God object detection (class with too many responsibilities)
                lines = content.split('\n')
                in_class = False
                class_methods = 0
                current_class = ""
                
                for line in lines:
                    if line.strip().startswith('class '):
                        if in_class and class_methods > 15:
                            self.issues.append(
                                f"God object detected: {current_class} in {py_file.relative_to(self.project_dir)} ({class_methods} methods)"
                            )
                        in_class = True
                        class_methods = 0
                        current_class = line.strip().split()[1].split('(')[0]
                    elif line.strip().startswith('def ') and in_class:
                        class_methods += 1
                
                # Final check for last class
                if in_class and class_methods > 15:
                    self.issues.append(
                        f"God object detected: {current_class} in {py_file.relative_to(self.project_dir)} ({class_methods} methods)"
                    )
                
                # Long parameter list detection (already covered in structure check)
                # Duplicate code detection (simplified)
                self._check_duplicate_code(py_file, content)
                
            except Exception:
                continue
    
    def _check_duplicate_code(self, file_path: Path, content: str):
        """Simple duplicate code detection"""
        
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        # Look for repeated 3+ line sequences
        for i in range(len(lines) - 2):
            sequence = lines[i:i+3]
            if len(set(sequence)) > 1:  # Not all identical lines
                for j in range(i + 3, len(lines) - 2):
                    if lines[j:j+3] == sequence:
                        self.issues.append(
                            f"Duplicate code detected in {file_path.relative_to(self.project_dir)} (lines around {i+1} and {j+1})"
                        )
                        break


def create_architecture_phase_prompt(milestone) -> str:
    """Create prompt for architecture review phase"""
    return f"""
## Architecture Review Phase

Review the implementation for {milestone.name} to ensure good architectural quality BEFORE proceeding to mechanical phases.

### CRITICAL MISSION: Prevent Wasted Cycles

Your goal is to catch architectural issues that would cause lint/typecheck/test phases to waste time and API costs. Fix structural problems NOW, not later.

### Architecture Standards to Enforce:

#### 1. **Code Structure**
- Functions ≤ 50 lines (break down larger ones)
- Classes ≤ 20 methods (split responsibilities)  
- Files ≤ 1000 lines (create modules)
- Nesting depth ≤ 4 levels (flatten complex logic)
- Function parameters ≤ 5 (use data classes/configs)

#### 2. **Import Structure**
- Add missing `__init__.py` files in src/ directories
- Fix circular imports (restructure if needed)
- Use relative imports within project modules
- Group imports: stdlib, third-party, local

#### 3. **Design Patterns**
- Separate UI code from business logic (except main.py)
- Extract hardcoded values to constants/config
- Implement proper error handling patterns
- Use dependency injection for testability

#### 4. **Complexity Management**
- Cyclomatic complexity ≤ 10 per function
- Break down complex conditionals
- Extract repeated code into functions
- Use early returns to reduce nesting

#### 5. **Anti-Pattern Prevention**
- No god objects (classes with too many responsibilities)
- No long parameter lists
- No duplicate code blocks
- No mixed concerns (business logic + UI in same module)

### Tools to Use:
```bash
# Run architecture validation
python -c "
from src.architecture_validator import ArchitectureValidator
from pathlib import Path
validator = ArchitectureValidator(Path('.'))
is_valid, issues = validator.validate_all()
print('ARCHITECTURE VALIDATION RESULTS:')
if is_valid:
    print('✓ All architecture checks passed')
else:
    print('✗ Architecture issues found:')
    for issue in issues:
        print(f'  - {{issue}}')
"
```

### SUCCESS CRITERIA:
1. **Zero architecture violations** - All checks must pass
2. **Well-structured code** - Clear separation of concerns
3. **Maintainable complexity** - Functions and classes are manageable
4. **Clean imports** - No circular dependencies
5. **Evidence provided** - Show the validation results

### FAILURE CONSEQUENCES:
If you skip this review, the following phases will waste cycles:
- **Lint phase**: Breaking down monolithic functions
- **Typecheck phase**: Fixing import structure issues  
- **Test phase**: Working around tightly coupled code
- **Integration phase**: Debugging complex interactions

### Output Required:
1. Run architecture validation and show results
2. Fix ALL issues found (no compromises)
3. Re-run validation to confirm zero issues
4. Create `architecture_review.md` with:
   - List of issues found and fixed
   - Final validation showing all checks passed
   - Brief explanation of any major restructuring

REMEMBER: This phase prevents wasted API costs in later phases. Be thorough!
"""


if __name__ == "__main__":
    # Example usage
    validator = ArchitectureValidator(Path("."))
    is_valid, issues = validator.validate_all()
    
    if is_valid:
        print("✓ All architecture checks passed")
    else:
        print("✗ Architecture issues found:")
        for issue in issues:
            print(f"  - {issue}")