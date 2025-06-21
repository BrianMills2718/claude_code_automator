#!/usr/bin/env python3
"""Architecture Validator for ML Portfolio Analyzer.

Validates code structure, complexity, imports, and design patterns
to prevent wasted cycles in lint/typecheck/test phases.
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ArchitectureIssue:
    """Represents an architecture issue found during validation."""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'error', 'warning', 'info'


class ArchitectureValidator:
    """Validates architectural quality of the codebase."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[ArchitectureIssue] = []
        self.src_dir = project_root / 'src'
    
    def validate_all(self) -> Tuple[bool, List[ArchitectureIssue]]:
        """Run all architecture validations."""
        self.issues.clear()
        
        # Get all Python files in src/
        python_files = list(self.src_dir.rglob('*.py'))
        
        for file_path in python_files:
            if file_path.name == '__init__.py':
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST
                try:
                    tree = ast.parse(content)
                except SyntaxError as e:
                    self.issues.append(ArchitectureIssue(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=e.lineno or 0,
                        issue_type='syntax_error',
                        description=f'Syntax error: {e.msg}',
                        severity='error'
                    ))
                    continue
                
                # Run validations
                self._validate_file_structure(file_path, content, tree)
                self._validate_function_complexity(file_path, tree)
                self._validate_class_structure(file_path, tree)
                self._validate_imports(file_path, tree)
                self._validate_design_patterns(file_path, content, tree)
                
            except Exception as e:
                self.issues.append(ArchitectureIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=0,
                    issue_type='validation_error',
                    description=f'Validation error: {str(e)}',
                    severity='error'
                ))
        
        # Validate directory structure
        self._validate_directory_structure()
        
        # Check for critical errors
        critical_errors = [i for i in self.issues if i.severity == 'error']
        return len(critical_errors) == 0, self.issues
    
    def _validate_file_structure(self, file_path: Path, content: str, tree: ast.AST):
        """Validate file-level structure issues."""
        lines = content.split('\n')
        
        # Check file length
        if len(lines) > 1000:
            self.issues.append(ArchitectureIssue(
                file_path=str(file_path.relative_to(self.project_root)),
                line_number=1,
                issue_type='file_too_long',
                description=f'File has {len(lines)} lines (max 1000)',
                severity='warning'
            ))
    
    def _validate_function_complexity(self, file_path: Path, tree: ast.AST):
        """Validate function length and complexity."""
        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self, validator, file_path):
                self.validator = validator
                self.file_path = file_path
            
            def visit_FunctionDef(self, node):
                # Check function length
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                    if func_length > 50:
                        self.validator.issues.append(ArchitectureIssue(
                            file_path=str(self.file_path.relative_to(self.validator.project_root)),
                            line_number=node.lineno,
                            issue_type='function_too_long',
                            description=f'Function "{node.name}" is {func_length} lines (max 50)',
                            severity='warning'
                        ))
                
                # Check parameter count
                args_count = len(node.args.args)
                if hasattr(node.args, 'posonlyargs'):
                    args_count += len(node.args.posonlyargs)
                if hasattr(node.args, 'kwonlyargs'):
                    args_count += len(node.args.kwonlyargs)
                
                if args_count > 5:
                    self.validator.issues.append(ArchitectureIssue(
                        file_path=str(self.file_path.relative_to(self.validator.project_root)),
                        line_number=node.lineno,
                        issue_type='too_many_parameters',
                        description=f'Function "{node.name}" has {args_count} parameters (max 5)',
                        severity='warning'
                    ))
                
                # Check cyclomatic complexity (simplified)
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    self.validator.issues.append(ArchitectureIssue(
                        file_path=str(self.file_path.relative_to(self.validator.project_root)),
                        line_number=node.lineno,
                        issue_type='high_complexity',
                        description=f'Function "{node.name}" has complexity {complexity} (max 10)',
                        severity='warning'
                    ))
                
                self.generic_visit(node)
            
            def _calculate_complexity(self, node):
                """Calculate simplified cyclomatic complexity."""
                complexity = 1  # Base complexity
                
                class ComplexityVisitor(ast.NodeVisitor):
                    def __init__(self):
                        self.complexity = 0
                    
                    def visit_If(self, node):
                        self.complexity += 1
                        self.generic_visit(node)
                    
                    def visit_While(self, node):
                        self.complexity += 1
                        self.generic_visit(node)
                    
                    def visit_For(self, node):
                        self.complexity += 1
                        self.generic_visit(node)
                    
                    def visit_Try(self, node):
                        self.complexity += len(node.handlers)
                        self.generic_visit(node)
                    
                    def visit_BoolOp(self, node):
                        if isinstance(node.op, (ast.And, ast.Or)):
                            self.complexity += len(node.values) - 1
                        self.generic_visit(node)
                
                visitor = ComplexityVisitor()
                visitor.visit(node)
                return complexity + visitor.complexity
        
        visitor = FunctionVisitor(self, file_path)
        visitor.visit(tree)
    
    def _validate_class_structure(self, file_path: Path, tree: ast.AST):
        """Validate class structure and method counts."""
        class ClassVisitor(ast.NodeVisitor):
            def __init__(self, validator, file_path):
                self.validator = validator
                self.file_path = file_path
            
            def visit_ClassDef(self, node):
                # Count methods
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    self.validator.issues.append(ArchitectureIssue(
                        file_path=str(self.file_path.relative_to(self.validator.project_root)),
                        line_number=node.lineno,
                        issue_type='too_many_methods',
                        description=f'Class "{node.name}" has {len(methods)} methods (max 20)',
                        severity='warning'
                    ))
                
                self.generic_visit(node)
        
        visitor = ClassVisitor(self, file_path)
        visitor.visit(tree)
    
    def _validate_imports(self, file_path: Path, tree: ast.AST):
        """Validate import structure and organization."""
        class ImportVisitor(ast.NodeVisitor):
            def __init__(self, validator, file_path):
                self.validator = validator
                self.file_path = file_path
                self.imports = []
                self.current_group = None
                self.groups = {'stdlib': [], 'third_party': [], 'local': []}
            
            def visit_Import(self, node):
                for alias in node.names:
                    self.imports.append((node.lineno, 'import', alias.name))
                    self._categorize_import(alias.name, node.lineno)
            
            def visit_ImportFrom(self, node):
                module = node.module or ''
                for alias in node.names:
                    import_name = f"{module}.{alias.name}" if module else alias.name
                    self.imports.append((node.lineno, 'from', import_name))
                    self._categorize_import(module, node.lineno)
            
            def _categorize_import(self, module_name, line_no):
                """Categorize import as stdlib, third-party, or local."""
                if not module_name:
                    return
                
                # Check if it's a relative import or starts with src
                if module_name.startswith('.') or module_name.startswith('src'):
                    self.groups['local'].append((line_no, module_name))
                elif self._is_stdlib_module(module_name):
                    self.groups['stdlib'].append((line_no, module_name))
                else:
                    self.groups['third_party'].append((line_no, module_name))
            
            def _is_stdlib_module(self, module_name):
                """Check if module is part of standard library."""
                stdlib_modules = {
                    'os', 'sys', 'pathlib', 'datetime', 'typing', 'abc', 'asyncio',
                    're', 'json', 'logging', 'collections', 'dataclasses'
                }
                return module_name.split('.')[0] in stdlib_modules
        
        visitor = ImportVisitor(self, file_path)
        visitor.visit(tree)
        
        # Check import organization (simplified check)
        if len(visitor.imports) > 10:
            # Look for mixed import types
            prev_group = None
            for line_no, import_type, module in visitor.imports:
                current_group = self._get_import_group(module)
                if prev_group and current_group != prev_group and prev_group != 'unknown':
                    self.issues.append(ArchitectureIssue(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_no,
                        issue_type='mixed_imports',
                        description='Imports not grouped by type (stdlib, third-party, local)',
                        severity='info'
                    ))
                    break
                prev_group = current_group
    
    def _get_import_group(self, module_name):
        """Get import group for a module."""
        if not module_name:
            return 'unknown'
        
        if module_name.startswith('.') or module_name.startswith('src'):
            return 'local'
        elif self._is_stdlib_module(module_name):
            return 'stdlib'
        else:
            return 'third_party'
    
    def _is_stdlib_module(self, module_name):
        """Check if module is part of standard library."""
        stdlib_modules = {
            'os', 'sys', 'pathlib', 'datetime', 'typing', 'abc', 'asyncio',
            're', 'json', 'logging', 'collections', 'dataclasses'
        }
        return module_name.split('.')[0] in stdlib_modules
    
    def _validate_design_patterns(self, file_path: Path, content: str, tree: ast.AST):
        """Validate design patterns and anti-patterns."""
        lines = content.split('\n')
        
        # Check for hardcoded values
        hardcoded_patterns = [
            r'"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"',  # Email
            r'"https?://[^\s"]+?"',  # URLs
            r'"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"',  # IP addresses
        ]
        
        for line_no, line in enumerate(lines, 1):
            for pattern in hardcoded_patterns:
                if re.search(pattern, line):
                    self.issues.append(ArchitectureIssue(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_no,
                        issue_type='hardcoded_value',
                        description='Hardcoded value found, consider using configuration',
                        severity='info'
                    ))
        
        # Check for God classes/functions (already covered in other methods)
        # Check for duplicate code (simplified)
        self._check_duplicate_code(file_path, lines)
    
    def _check_duplicate_code(self, file_path: Path, lines: List[str]):
        """Check for duplicate code blocks."""
        # Simplified duplicate detection - look for identical function signatures
        func_signatures = {}
        for line_no, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('def ') and not stripped.startswith('def __'):
                signature = stripped.split('(')[0] if '(' in stripped else stripped
                if signature in func_signatures:
                    self.issues.append(ArchitectureIssue(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_no,
                        issue_type='duplicate_function_name',
                        description=f'Function name "{signature}" already used at line {func_signatures[signature]}',
                        severity='warning'
                    ))
                else:
                    func_signatures[signature] = line_no
    
    def _validate_directory_structure(self):
        """Validate overall directory structure."""
        required_init_files = [
            'src/__init__.py',
            'src/api/__init__.py',
            'src/cli/__init__.py',
            'src/config/__init__.py',
            'src/data_sources/__init__.py',
            'src/processing/__init__.py',
            'src/storage/__init__.py',
            'src/web/__init__.py'
        ]
        
        for init_file in required_init_files:
            init_path = self.project_root / init_file
            if not init_path.exists():
                self.issues.append(ArchitectureIssue(
                    file_path=init_file,
                    line_number=0,
                    issue_type='missing_init_file',
                    description=f'Missing __init__.py file: {init_file}',
                    severity='error'
                ))
        
        # Check for duplicate config files
        config_py = self.project_root / 'src' / 'config.py'
        config_init_py = self.project_root / 'src' / 'config' / '__init__.py'
        if config_py.exists() and config_init_py.exists():
            self.issues.append(ArchitectureIssue(
                file_path='src/config.py',
                line_number=0,
                issue_type='duplicate_config',
                description='Duplicate configuration files found: both src/config.py and src/config/__init__.py exist',
                severity='error'
            ))


def main():
    """Run architecture validation."""
    validator = ArchitectureValidator(Path('.'))
    is_valid, issues = validator.validate_all()
    
    print('ARCHITECTURE VALIDATION RESULTS:')
    if is_valid:
        print('✓ All architecture checks passed')
    else:
        print('✗ Architecture issues found:')
        
        # Group by severity
        by_severity = defaultdict(list)
        for issue in issues:
            by_severity[issue.severity].append(issue)
        
        for severity in ['error', 'warning', 'info']:
            if severity in by_severity:
                print(f'\n{severity.upper()}S ({len(by_severity[severity])}):')
                for issue in by_severity[severity]:
                    print(f'  - {issue.file_path}:{issue.line_number} [{issue.issue_type}] {issue.description}')
    
    return is_valid


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)