"""
V4 Context Analyzer
Analyzes project characteristics to inform strategy selection.
"""

import re
import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import ast
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TechnologyProfile:
    """Profile of technologies used in the project."""
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    libraries: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)


class V4ContextAnalyzer:
    """
    Analyzes project context to understand its characteristics.
    
    This analysis informs intelligent strategy selection by understanding:
    - Project type and structure
    - Technology stack
    - Complexity metrics
    - Requirement clarity
    - Test coverage expectations
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.claude_md_path = self.project_path / 'CLAUDE.md'
        self.similarity_db_path = self.project_path / '.cc_automator' / 'v4_project_similarity.json'
        
        # Known patterns for project type detection
        self.project_type_indicators = {
            'web_app': ['flask', 'django', 'fastapi', 'express', 'react', 'vue', 'html', 'css'],
            'cli_tool': ['click', 'argparse', 'typer', 'fire', 'console', 'terminal'],
            'library': ['setup.py', 'pyproject.toml', '__init__.py', 'package.json'],
            'ml_project': ['tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'model'],
            'api_service': ['rest', 'graphql', 'grpc', 'swagger', 'openapi', 'endpoints'],
            'data_pipeline': ['etl', 'pipeline', 'airflow', 'spark', 'dataflow', 'streaming']
        }
        
        logger.info(f"Context Analyzer initialized for {project_path}")
    
    async def analyze_project(self) -> 'ProjectContext':
        """
        Perform comprehensive project analysis.
        """
        from .v4_strategy_manager import ProjectContext
        
        logger.info("Starting project context analysis...")
        
        # Read CLAUDE.md for requirements
        requirements = self._read_requirements()
        
        # Analyze project structure
        project_type = self._detect_project_type(requirements)
        
        # Calculate complexity metrics
        complexity_score = self._calculate_complexity(requirements)
        
        # Detect technology stack
        tech_profile = self._analyze_technology_stack(requirements)
        
        # Assess requirement clarity
        requirement_clarity = self._assess_requirement_clarity(requirements)
        
        # Estimate test coverage expectations
        test_coverage = self._estimate_test_coverage(requirements)
        
        # Assess architectural quality requirements
        architectural_quality = self._assess_architectural_requirements(requirements)
        
        # Find similar past projects
        similar_projects = self._find_similar_projects(project_type, tech_profile)
        
        # Determine special characteristics
        has_ambiguous_requirements = requirement_clarity < 0.3
        is_refactoring = self._is_refactoring_task(requirements)
        is_simple_cli = project_type == 'cli_tool' and complexity_score < 0.3
        
        context = ProjectContext(
            project_type=project_type,
            complexity_score=complexity_score,
            technology_stack=tech_profile.languages + tech_profile.frameworks,
            requirement_clarity=requirement_clarity,
            test_coverage=test_coverage,
            architectural_quality=architectural_quality,
            similar_projects=similar_projects,
            has_ambiguous_requirements=has_ambiguous_requirements,
            is_refactoring=is_refactoring,
            is_simple_cli=is_simple_cli
        )
        
        logger.info(f"Context analysis complete: {project_type} project with "
                   f"complexity {complexity_score:.2f}")
        
        return context
    
    def _read_requirements(self) -> str:
        """Read project requirements from CLAUDE.md."""
        if self.claude_md_path.exists():
            return self.claude_md_path.read_text()
        
        # Fallback to README or other docs
        for filename in ['README.md', 'requirements.txt', 'project.md']:
            path = self.project_path / filename
            if path.exists():
                return path.read_text()
        
        return ""
    
    def _detect_project_type(self, requirements: str) -> str:
        """
        Detect the type of project based on requirements and structure.
        """
        requirements_lower = requirements.lower()
        
        # Count indicators for each type
        type_scores = {}
        
        for project_type, indicators in self.project_type_indicators.items():
            score = sum(1 for indicator in indicators if indicator in requirements_lower)
            type_scores[project_type] = score
        
        # Check file structure for additional hints
        project_files = list(self.project_path.glob('**/*'))[:100]  # Limit for performance
        file_names = [f.name.lower() for f in project_files if f.is_file()]
        
        # Additional scoring based on files
        if any('app.py' in f or 'main.py' in f for f in file_names):
            type_scores['web_app'] += 2
        
        if any('cli.py' in f or 'command' in f for f in file_names):
            type_scores['cli_tool'] += 2
        
        if any('setup.py' in f or 'pyproject.toml' in f for f in file_names):
            type_scores['library'] += 1
        
        if any('model' in f or 'train' in f for f in file_names):
            type_scores['ml_project'] += 2
        
        # Explicit mentions in requirements
        if 'web application' in requirements_lower or 'web app' in requirements_lower:
            type_scores['web_app'] += 5
        
        if 'command line' in requirements_lower or 'cli' in requirements_lower:
            type_scores['cli_tool'] += 5
        
        if 'library' in requirements_lower or 'package' in requirements_lower:
            type_scores['library'] += 5
        
        if 'machine learning' in requirements_lower or ' ml ' in requirements_lower:
            type_scores['ml_project'] += 5
        
        # Return highest scoring type
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return 'general'  # Default fallback
    
    def _calculate_complexity(self, requirements: str) -> float:
        """
        Calculate project complexity score (0.0 to 1.0).
        """
        complexity_factors = []
        
        # Requirement length (normalized)
        req_length = len(requirements.split())
        length_score = min(req_length / 1000, 1.0)  # Normalize to 1000 words
        complexity_factors.append(length_score * 0.2)  # 20% weight
        
        # Number of milestones
        milestone_count = requirements.count('### Milestone')
        milestone_score = min(milestone_count / 10, 1.0)  # Normalize to 10 milestones
        complexity_factors.append(milestone_score * 0.2)  # 20% weight
        
        # Technical indicators
        tech_indicators = [
            'distributed', 'concurrent', 'async', 'parallel', 'microservice',
            'authentication', 'authorization', 'security', 'encryption',
            'real-time', 'streaming', 'websocket', 'performance',
            'scalable', 'high availability', 'fault tolerant'
        ]
        
        tech_count = sum(1 for ind in tech_indicators if ind in requirements.lower())
        tech_score = min(tech_count / 5, 1.0)  # Normalize to 5 technical features
        complexity_factors.append(tech_score * 0.3)  # 30% weight
        
        # Integration requirements
        integration_indicators = [
            'api', 'database', 'third-party', 'integration', 'service',
            'oauth', 'webhook', 'queue', 'cache', 'external'
        ]
        
        integration_count = sum(1 for ind in integration_indicators if ind in requirements.lower())
        integration_score = min(integration_count / 5, 1.0)
        complexity_factors.append(integration_score * 0.2)  # 20% weight
        
        # File structure complexity
        if self.project_path.exists():
            file_count = len(list(self.project_path.glob('**/*.py')))
            file_score = min(file_count / 50, 1.0)  # Normalize to 50 files
            complexity_factors.append(file_score * 0.1)  # 10% weight
        
        return sum(complexity_factors)
    
    def _analyze_technology_stack(self, requirements: str) -> TechnologyProfile:
        """
        Analyze the technology stack mentioned or implied.
        """
        profile = TechnologyProfile()
        requirements_lower = requirements.lower()
        
        # Language detection
        languages = {
            'python': ['python', 'py', 'pip', 'conda'],
            'javascript': ['javascript', 'js', 'node', 'npm'],
            'typescript': ['typescript', 'ts', 'tsx'],
            'java': ['java', 'maven', 'gradle'],
            'go': ['golang', 'go ', 'go.mod'],
            'rust': ['rust', 'cargo']
        }
        
        for lang, indicators in languages.items():
            if any(ind in requirements_lower for ind in indicators):
                profile.languages.append(lang)
        
        # Framework detection
        frameworks = {
            'flask': ['flask'],
            'django': ['django'],
            'fastapi': ['fastapi'],
            'react': ['react'],
            'vue': ['vue'],
            'angular': ['angular'],
            'express': ['express'],
            'spring': ['spring'],
            'rails': ['rails', 'ruby on rails']
        }
        
        for framework, indicators in frameworks.items():
            if any(ind in requirements_lower for ind in indicators):
                profile.frameworks.append(framework)
        
        # Library detection
        libraries = {
            'pytest': ['pytest', 'test'],
            'requests': ['http', 'api calls'],
            'pandas': ['data analysis', 'dataframe'],
            'numpy': ['numerical', 'array'],
            'sqlalchemy': ['database', 'orm'],
            'celery': ['task queue', 'background jobs'],
            'redis': ['cache', 'redis'],
            'docker': ['container', 'docker']
        }
        
        for library, indicators in libraries.items():
            if any(ind in requirements_lower for ind in indicators):
                profile.libraries.append(library)
        
        # Pattern detection
        patterns = {
            'mvc': ['model', 'view', 'controller'],
            'rest': ['rest', 'restful', 'api'],
            'microservices': ['microservice'],
            'event_driven': ['event', 'message', 'queue'],
            'serverless': ['serverless', 'lambda', 'function']
        }
        
        for pattern, indicators in patterns.items():
            if any(ind in requirements_lower for ind in indicators):
                profile.patterns.append(pattern)
        
        # Check existing project files for additional tech
        if self.project_path.exists():
            self._detect_tech_from_files(profile)
        
        return profile
    
    def _detect_tech_from_files(self, profile: TechnologyProfile):
        """Detect technology from existing project files."""
        # Check requirements.txt
        req_file = self.project_path / 'requirements.txt'
        if req_file.exists():
            requirements = req_file.read_text().lower()
            
            # Common libraries
            if 'flask' in requirements and 'flask' not in profile.frameworks:
                profile.frameworks.append('flask')
            if 'django' in requirements and 'django' not in profile.frameworks:
                profile.frameworks.append('django')
            if 'fastapi' in requirements and 'fastapi' not in profile.frameworks:
                profile.frameworks.append('fastapi')
            if 'pytest' in requirements and 'pytest' not in profile.libraries:
                profile.libraries.append('pytest')
        
        # Check package.json
        package_file = self.project_path / 'package.json'
        if package_file.exists():
            if 'javascript' not in profile.languages:
                profile.languages.append('javascript')
    
    def _assess_requirement_clarity(self, requirements: str) -> float:
        """
        Assess how clear and specific the requirements are (0.0 to 1.0).
        """
        if not requirements:
            return 0.0
        
        clarity_scores = []
        
        # Check for specific success criteria
        success_criteria = [
            'must', 'should', 'shall', 'requirement', 'criteria',
            'acceptance', 'definition of done', 'expected'
        ]
        
        criteria_count = sum(1 for crit in success_criteria if crit in requirements.lower())
        clarity_scores.append(min(criteria_count / 5, 1.0) * 0.3)
        
        # Check for concrete examples
        example_indicators = [
            'example', 'e.g.', 'for instance', 'such as',
            'input:', 'output:', 'scenario:', 'use case:'
        ]
        
        example_count = sum(1 for ex in example_indicators if ex in requirements.lower())
        clarity_scores.append(min(example_count / 3, 1.0) * 0.3)
        
        # Check for quantifiable metrics
        metric_patterns = [
            r'\d+%', r'\d+ seconds', r'\d+ ms', r'\d+ users',
            r'performance', r'threshold', r'limit', r'maximum'
        ]
        
        metric_count = sum(1 for pattern in metric_patterns 
                          if re.search(pattern, requirements.lower()))
        clarity_scores.append(min(metric_count / 3, 1.0) * 0.2)
        
        # Check for ambiguous language (negative indicator)
        ambiguous_terms = [
            'maybe', 'possibly', 'might', 'could', 'sometimes',
            'various', 'etc', 'and so on', 'stuff', 'things'
        ]
        
        ambiguous_count = sum(1 for term in ambiguous_terms if term in requirements.lower())
        ambiguity_penalty = min(ambiguous_count / 5, 1.0) * 0.2
        clarity_scores.append(1.0 - ambiguity_penalty)
        
        return sum(clarity_scores) / len(clarity_scores)
    
    def _estimate_test_coverage(self, requirements: str) -> float:
        """
        Estimate expected test coverage based on requirements (0.0 to 1.0).
        """
        requirements_lower = requirements.lower()
        
        # Look for explicit test requirements
        if 'test coverage' in requirements_lower:
            # Try to extract percentage
            match = re.search(r'(\d+)%?\s*(?:test\s*)?coverage', requirements_lower)
            if match:
                return float(match.group(1)) / 100
        
        # Look for testing emphasis
        test_indicators = [
            'comprehensive test', 'thorough test', 'unit test',
            'integration test', 'e2e test', 'test-driven',
            'tdd', 'test first', 'well-tested'
        ]
        
        test_emphasis = sum(1 for ind in test_indicators if ind in requirements_lower)
        
        if test_emphasis >= 3:
            return 0.8  # High test coverage expected
        elif test_emphasis >= 1:
            return 0.6  # Moderate test coverage
        else:
            return 0.4  # Basic test coverage
    
    def _assess_architectural_requirements(self, requirements: str) -> float:
        """
        Assess architectural quality requirements (0.0 to 1.0).
        """
        requirements_lower = requirements.lower()
        
        arch_indicators = [
            'scalable', 'maintainable', 'modular', 'extensible',
            'clean code', 'solid principles', 'design pattern',
            'architecture', 'separation of concerns', 'loosely coupled',
            'high cohesion', 'dependency injection', 'interface'
        ]
        
        arch_count = sum(1 for ind in arch_indicators if ind in requirements_lower)
        
        # Normalize to 0-1 scale
        return min(arch_count / 5, 1.0)
    
    def _find_similar_projects(
        self,
        project_type: str,
        tech_profile: TechnologyProfile
    ) -> List[Dict[str, Any]]:
        """
        Find similar past projects from history.
        """
        similar_projects = []
        
        # Load similarity database
        if self.similarity_db_path.exists():
            try:
                with open(self.similarity_db_path) as f:
                    similarity_db = json.load(f)
                
                for project in similarity_db.get('projects', []):
                    similarity_score = self._calculate_similarity(
                        project_type,
                        tech_profile,
                        project
                    )
                    
                    if similarity_score > 0.5:
                        similar_projects.append({
                            'name': project['name'],
                            'type': project['type'],
                            'similarity': similarity_score,
                            'successful_strategy': project.get('successful_strategy', 'unknown')
                        })
                
                # Sort by similarity
                similar_projects.sort(key=lambda x: x['similarity'], reverse=True)
                
            except Exception as e:
                logger.warning(f"Failed to load similarity database: {e}")
        
        return similar_projects[:5]  # Return top 5
    
    def _calculate_similarity(
        self,
        project_type: str,
        tech_profile: TechnologyProfile,
        other_project: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity score between projects.
        """
        similarity = 0.0
        
        # Project type match (40% weight)
        if project_type == other_project.get('type'):
            similarity += 0.4
        
        # Technology overlap (40% weight)
        other_tech = other_project.get('technologies', [])
        our_tech = tech_profile.languages + tech_profile.frameworks
        
        if our_tech and other_tech:
            overlap = len(set(our_tech) & set(other_tech))
            total = len(set(our_tech) | set(other_tech))
            if total > 0:
                similarity += 0.4 * (overlap / total)
        
        # Complexity similarity (20% weight)
        if 'complexity' in other_project:
            # Assume our complexity is calculated elsewhere
            complexity_diff = abs(0.5 - other_project['complexity'])  # Placeholder
            similarity += 0.2 * (1 - complexity_diff)
        
        return similarity
    
    def _is_refactoring_task(self, requirements: str) -> bool:
        """
        Determine if this is primarily a refactoring task.
        """
        refactoring_indicators = [
            'refactor', 'cleanup', 'reorganize', 'restructure',
            'improve code quality', 'technical debt', 'modernize',
            'migrate', 'upgrade', 'optimize existing'
        ]
        
        requirements_lower = requirements.lower()
        indicator_count = sum(1 for ind in refactoring_indicators if ind in requirements_lower)
        
        return indicator_count >= 2