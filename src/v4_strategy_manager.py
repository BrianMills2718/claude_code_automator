"""
V4 Strategy Manager
Selects and coordinates different orchestration strategies based on project context and failure patterns.
"""

import logging
from typing import Dict, List, Optional, Any, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .orchestrator import CCAutomatorOrchestrator
from .phase_orchestrator import Phase

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Represents analyzed project characteristics."""
    project_type: str  # 'web_app', 'cli_tool', 'library', 'ml_project', etc.
    complexity_score: float  # 0.0 to 1.0
    technology_stack: List[str]
    requirement_clarity: float  # 0.0 to 1.0
    test_coverage: float  # 0.0 to 1.0
    architectural_quality: float  # 0.0 to 1.0
    similar_projects: List[Dict[str, Any]]
    has_ambiguous_requirements: bool = False
    is_refactoring: bool = False
    is_simple_cli: bool = False


@dataclass
class FailureAnalysis:
    """Results of failure pattern analysis."""
    failure_type: str
    root_cause: str
    pattern_name: str
    suggested_action: str
    confidence: float
    constraints: Optional[Dict[str, Any]] = None
    
    def suggests_strategy_switch(self) -> bool:
        """Determine if failure analysis suggests switching strategies."""
        return (
            self.confidence > 0.7 and 
            self.suggested_action in ['switch_strategy', 'try_alternative_approach']
        )


class Strategy(ABC):
    """Base class for all orchestration strategies."""
    
    def __init__(self, v3_orchestrator: CCAutomatorOrchestrator):
        self.v3_orchestrator = v3_orchestrator
        self.name = self.__class__.__name__
        self.selection_reason = ""
        self.best_for_description = ""
    
    @abstractmethod
    async def execute(
        self, 
        milestone_num: int, 
        milestone: str,
        failure_callback: Optional[Any] = None
    ) -> 'ExecutionResult':
        """Execute the strategy for a milestone."""
        pass
    
    @abstractmethod
    def get_phases(self) -> List[Phase]:
        """Get the phases this strategy will execute."""
        pass
    
    def adapt_for_context(self, context: ProjectContext):
        """Adapt strategy parameters based on project context."""
        pass


class V3PipelineStrategy(Strategy):
    """
    Standard V3 sequential pipeline strategy.
    Best for simple, well-defined projects where the standard pipeline works well.
    """
    
    def __init__(self, v3_orchestrator: CCAutomatorOrchestrator):
        super().__init__(v3_orchestrator)
        self.best_for_description = "Simple, well-defined projects with clear requirements"
    
    async def execute(
        self, 
        milestone_num: int, 
        milestone: str,
        failure_callback: Optional[Any] = None
    ) -> 'ExecutionResult':
        """Execute using standard V3 pipeline."""
        # Use V3 orchestrator directly
        success = await self.v3_orchestrator.process_milestone(
            milestone_num, 
            milestone,
            phase_callback=failure_callback
        )
        
        return ExecutionResult(
            success=success,
            strategy_name=self.name,
            milestone_num=milestone_num,
            evidence_files=self._gather_evidence_files(milestone_num),
            execution_time=self.v3_orchestrator.get_milestone_duration(milestone_num)
        )
    
    def get_phases(self) -> List[Phase]:
        """Return standard V3 phases."""
        return self.v3_orchestrator.phases
    
    def _gather_evidence_files(self, milestone_num: int) -> List[Path]:
        """Gather evidence files from V3 execution."""
        milestone_dir = self.v3_orchestrator.working_dir / '.cc_automator' / 'milestones' / f'milestone_{milestone_num}'
        evidence_files = []
        
        if milestone_dir.exists():
            for pattern in ['*.md', '*.log', '*.json']:
                evidence_files.extend(milestone_dir.glob(pattern))
        
        return evidence_files


class IterativeRefinementStrategy(Strategy):
    """
    Iterative strategy that focuses on problematic phases.
    Best for projects with complex requirements or architecture challenges.
    """
    
    def __init__(self, v3_orchestrator: CCAutomatorOrchestrator, focus_phases: List[str] = None):
        super().__init__(v3_orchestrator)
        self.focus_phases = focus_phases or ['research', 'planning', 'architecture']
        self.iterations = 3
        self.best_for_description = "Complex projects with architecture challenges or unclear requirements"
    
    async def execute(
        self, 
        milestone_num: int, 
        milestone: str,
        failure_callback: Optional[Any] = None
    ) -> 'ExecutionResult':
        """Execute with iterative refinement of key phases."""
        logger.info(f"Starting iterative refinement strategy with focus on: {self.focus_phases}")
        
        best_result = None
        
        for iteration in range(self.iterations):
            logger.info(f"Iteration {iteration + 1}/{self.iterations}")
            
            # Execute focused phases with enhanced prompts
            for phase_name in self.focus_phases:
                phase = self._get_enhanced_phase(phase_name, iteration)
                
                success = await self.v3_orchestrator.execute_single_phase(
                    phase,
                    milestone_num,
                    milestone,
                    callback=failure_callback
                )
                
                if not success:
                    logger.warning(f"Phase {phase_name} failed in iteration {iteration + 1}")
            
            # Validate current iteration
            validation_score = await self._validate_iteration(milestone_num, iteration)
            
            if validation_score > 0.8:
                logger.info(f"Iteration {iteration + 1} achieved good results, continuing to full pipeline")
                break
        
        # Complete remaining phases
        remaining_phases = self._get_remaining_phases()
        for phase in remaining_phases:
            await self.v3_orchestrator.execute_single_phase(
                phase,
                milestone_num,
                milestone,
                callback=failure_callback
            )
        
        return ExecutionResult(
            success=True,
            strategy_name=self.name,
            milestone_num=milestone_num,
            evidence_files=self._gather_evidence_files(milestone_num),
            iterations_used=iteration + 1
        )
    
    def get_phases(self) -> List[Phase]:
        """Get phases including iterations."""
        phases = []
        
        # Add iterative phases
        for i in range(self.iterations):
            for phase_name in self.focus_phases:
                phases.append(self._get_enhanced_phase(phase_name, i))
        
        # Add remaining phases
        phases.extend(self._get_remaining_phases())
        
        return phases
    
    def _get_enhanced_phase(self, phase_name: str, iteration: int) -> Phase:
        """Create enhanced phase with iteration-specific prompts."""
        base_phase = next(p for p in self.v3_orchestrator.phases if p.name == phase_name)
        
        # Create enhanced phase with additional context
        enhanced_prompt = f"""
{base_phase.prompt}

ITERATION {iteration + 1} ENHANCEMENTS:
- Learn from any previous attempts
- Focus on clarity and completeness
- Address any ambiguities explicitly
- Provide detailed reasoning for decisions
"""
        
        return Phase(
            name=f"{phase_name}_iter{iteration}",
            prompt=enhanced_prompt,
            validator=base_phase.validator,
            allowed_tools=base_phase.allowed_tools,
            temperature=base_phase.temperature,
            max_turns=int(base_phase.max_turns * 1.2)  # Give more turns for refinement
        )
    
    def _get_remaining_phases(self) -> List[Phase]:
        """Get phases not included in iterative refinement."""
        return [
            p for p in self.v3_orchestrator.phases 
            if p.name not in self.focus_phases
        ]
    
    async def _validate_iteration(self, milestone_num: int, iteration: int) -> float:
        """Validate quality of current iteration."""
        # Check if key artifacts exist and are substantial
        milestone_dir = self.v3_orchestrator.working_dir / '.cc_automator' / 'milestones' / f'milestone_{milestone_num}'
        
        score = 0.0
        weights = {
            'research.md': 0.3,
            'plan.md': 0.3,
            'architecture_review.md': 0.4
        }
        
        for filename, weight in weights.items():
            file_path = milestone_dir / filename
            if file_path.exists():
                content = file_path.read_text()
                if len(content) > 500:  # Substantial content
                    score += weight
        
        return score
    
    def _gather_evidence_files(self, milestone_num: int) -> List[Path]:
        """Gather evidence files including iteration artifacts."""
        milestone_dir = self.v3_orchestrator.working_dir / '.cc_automator' / 'milestones' / f'milestone_{milestone_num}'
        return list(milestone_dir.glob('*')) if milestone_dir.exists() else []


class ParallelExplorationStrategy(Strategy):
    """
    Explores multiple implementation approaches in parallel.
    Best for projects with ambiguous requirements or multiple valid solutions.
    """
    
    def __init__(self, v3_orchestrator: CCAutomatorOrchestrator, exploration_budget: int = 3):
        super().__init__(v3_orchestrator)
        self.exploration_budget = exploration_budget
        self.best_for_description = "Projects with ambiguous requirements or multiple valid approaches"
    
    async def execute(
        self, 
        milestone_num: int, 
        milestone: str,
        failure_callback: Optional[Any] = None
    ) -> 'ExecutionResult':
        """Execute parallel exploration of approaches."""
        logger.info(f"Starting parallel exploration with budget: {self.exploration_budget}")
        
        # Create exploration variants
        exploration_results = []
        
        for i in range(self.exploration_budget):
            logger.info(f"Exploring approach {i + 1}/{self.exploration_budget}")
            
            # Execute research and planning with different prompts
            variant_phases = self._create_exploration_variant(i)
            
            variant_success = True
            for phase in variant_phases:
                success = await self.v3_orchestrator.execute_single_phase(
                    phase,
                    milestone_num,
                    milestone,
                    callback=failure_callback
                )
                
                if not success:
                    variant_success = False
                    break
            
            if variant_success:
                # Evaluate this exploration
                evaluation = await self._evaluate_exploration(milestone_num, i)
                exploration_results.append((i, evaluation))
        
        # Select best exploration
        if not exploration_results:
            raise ValueError("All exploration variants failed")
        
        best_variant, best_score = max(exploration_results, key=lambda x: x[1])
        logger.info(f"Selected variant {best_variant + 1} with score {best_score}")
        
        # Continue with best variant through remaining phases
        remaining_phases = self.v3_orchestrator.phases[3:]  # After implement
        for phase in remaining_phases:
            await self.v3_orchestrator.execute_single_phase(
                phase,
                milestone_num,
                milestone,
                callback=failure_callback
            )
        
        return ExecutionResult(
            success=True,
            strategy_name=self.name,
            milestone_num=milestone_num,
            evidence_files=self._gather_evidence_files(milestone_num),
            exploration_variant=best_variant,
            exploration_score=best_score
        )
    
    def get_phases(self) -> List[Phase]:
        """Get phases for parallel exploration."""
        phases = []
        
        # Add exploration phases
        for i in range(self.exploration_budget):
            phases.extend(self._create_exploration_variant(i))
        
        # Add standard phases after exploration
        phases.extend(self.v3_orchestrator.phases[3:])
        
        return phases
    
    def _create_exploration_variant(self, variant_num: int) -> List[Phase]:
        """Create exploration variant phases."""
        approaches = [
            "Focus on simplicity and minimal viable implementation",
            "Focus on robustness and comprehensive error handling",
            "Focus on performance and scalability"
        ]
        
        approach = approaches[variant_num % len(approaches)]
        
        # Create variant research phase
        research_phase = Phase(
            name=f"research_variant_{variant_num}",
            prompt=f"""
{self.v3_orchestrator.phases[0].prompt}

EXPLORATION VARIANT {variant_num + 1}:
Approach this research with the following focus: {approach}
Consider alternative interpretations of the requirements.
""",
            validator=self.v3_orchestrator.phases[0].validator,
            allowed_tools=self.v3_orchestrator.phases[0].allowed_tools
        )
        
        # Create variant planning phase
        planning_phase = Phase(
            name=f"planning_variant_{variant_num}",
            prompt=f"""
{self.v3_orchestrator.phases[1].prompt}

EXPLORATION VARIANT {variant_num + 1}:
Create a plan based on the research variant with focus: {approach}
""",
            validator=self.v3_orchestrator.phases[1].validator,
            allowed_tools=self.v3_orchestrator.phases[1].allowed_tools
        )
        
        # Create variant implementation phase
        implement_phase = Phase(
            name=f"implement_variant_{variant_num}",
            prompt=f"""
{self.v3_orchestrator.phases[2].prompt}

EXPLORATION VARIANT {variant_num + 1}:
Implement based on the variant plan with focus: {approach}
""",
            validator=self.v3_orchestrator.phases[2].validator,
            allowed_tools=self.v3_orchestrator.phases[2].allowed_tools
        )
        
        return [research_phase, planning_phase, implement_phase]
    
    async def _evaluate_exploration(self, milestone_num: int, variant_num: int) -> float:
        """Evaluate quality of an exploration variant."""
        # Run architecture validation on the variant
        architecture_phase = self.v3_orchestrator.phases[3]  # architecture phase
        
        try:
            success = await self.v3_orchestrator.execute_single_phase(
                architecture_phase,
                milestone_num,
                f"variant_{variant_num}",
                quiet=True  # Don't log failures during evaluation
            )
            
            if success:
                # Check architecture review results
                review_file = (
                    self.v3_orchestrator.working_dir / 
                    '.cc_automator' / 'milestones' / 
                    f'milestone_{milestone_num}' / 'architecture_review.md'
                )
                
                if review_file.exists():
                    content = review_file.read_text()
                    # Simple scoring based on review content
                    if "zero violations" in content.lower():
                        return 1.0
                    elif "minor issues" in content.lower():
                        return 0.7
                    else:
                        return 0.4
            
            return 0.2  # Failed architecture validation
            
        except Exception as e:
            logger.warning(f"Variant {variant_num} evaluation failed: {str(e)}")
            return 0.0
    
    def _gather_evidence_files(self, milestone_num: int) -> List[Path]:
        """Gather evidence files including exploration artifacts."""
        milestone_dir = self.v3_orchestrator.working_dir / '.cc_automator' / 'milestones' / f'milestone_{milestone_num}'
        return list(milestone_dir.glob('*')) if milestone_dir.exists() else []


@dataclass
class ExecutionResult:
    """Result of strategy execution."""
    success: bool
    strategy_name: str
    milestone_num: int
    evidence_files: List[Path]
    execution_time: float = 0.0
    resource_usage: Dict[str, Any] = None
    learning_data: Dict[str, Any] = None
    iterations_used: int = 1
    exploration_variant: int = -1
    exploration_score: float = 0.0
    
    def __post_init__(self):
        if self.resource_usage is None:
            self.resource_usage = {}
        if self.learning_data is None:
            self.learning_data = {}


class V4StrategyManager:
    """
    Manages strategy selection and coordination based on project context and failure patterns.
    """
    
    def __init__(self, v3_orchestrator: CCAutomatorOrchestrator):
        self.v3_orchestrator = v3_orchestrator
        self.available_strategies = self._initialize_strategies()
        
        logger.info(f"Strategy Manager initialized with {len(self.available_strategies)} strategies")
    
    def _initialize_strategies(self) -> Dict[str, Type[Strategy]]:
        """Initialize available strategy classes."""
        return {
            'v3_pipeline': V3PipelineStrategy,
            'iterative_refinement': IterativeRefinementStrategy,
            'parallel_exploration': ParallelExplorationStrategy
        }
    
    def select_strategy(
        self,
        project_context: ProjectContext,
        failure_history: 'FailureHistory',
        milestone: str
    ) -> Strategy:
        """
        Select optimal strategy based on context and history.
        
        This is the core intelligence of V4 - choosing the right approach
        based on project characteristics and past failures.
        """
        logger.info(f"Selecting strategy for {project_context.project_type} project "
                   f"with complexity {project_context.complexity_score:.2f}")
        
        # Simple projects use V3 pipeline
        if project_context.is_simple_cli and project_context.complexity_score < 0.3:
            strategy = self._create_strategy('v3_pipeline')
            strategy.selection_reason = "Simple CLI project with low complexity"
            return strategy
        
        # Projects with architecture issues use iterative refinement
        architecture_failures = failure_history.get_phase_failures('architecture')
        if len(architecture_failures) > 2:
            strategy = self._create_strategy('iterative_refinement', 
                                           focus_phases=['research', 'planning', 'architecture'])
            strategy.selection_reason = f"History of {len(architecture_failures)} architecture failures"
            return strategy
        
        # Ambiguous requirements use parallel exploration
        if project_context.has_ambiguous_requirements or project_context.requirement_clarity < 0.3:
            strategy = self._create_strategy('parallel_exploration', exploration_budget=3)
            strategy.selection_reason = "Ambiguous requirements requiring exploration"
            return strategy
        
        # Complex projects with clear requirements use iterative refinement
        if project_context.complexity_score > 0.7:
            strategy = self._create_strategy('iterative_refinement')
            strategy.selection_reason = "High complexity requiring iterative refinement"
            return strategy
        
        # Default to V3 pipeline
        strategy = self._create_strategy('v3_pipeline')
        strategy.selection_reason = "Default strategy for standard projects"
        return strategy
    
    def select_alternative_strategy(
        self,
        current_strategy: Strategy,
        failure_analysis: FailureAnalysis,
        project_context: ProjectContext
    ) -> Strategy:
        """
        Select an alternative strategy based on failure analysis.
        """
        logger.info(f"Selecting alternative to {current_strategy.name} due to {failure_analysis.failure_type}")
        
        # If V3 pipeline failed with complexity issues, try iterative
        if isinstance(current_strategy, V3PipelineStrategy):
            if failure_analysis.pattern_name in ['complexity_overwhelm', 'architecture_loops']:
                strategy = self._create_strategy('iterative_refinement')
                strategy.selection_reason = f"V3 pipeline failed with {failure_analysis.pattern_name}"
                return strategy
        
        # If iterative failed, try parallel exploration
        if isinstance(current_strategy, IterativeRefinementStrategy):
            strategy = self._create_strategy('parallel_exploration')
            strategy.selection_reason = "Iterative refinement failed, trying exploration"
            return strategy
        
        # If parallel exploration failed, fall back to V3 with constraints
        if isinstance(current_strategy, ParallelExplorationStrategy):
            strategy = self._create_strategy('v3_pipeline')
            strategy.selection_reason = "Falling back to V3 pipeline with lessons learned"
            # Could add constraints here based on failure analysis
            return strategy
        
        # Default: return same strategy (no switch)
        return current_strategy
    
    def generate_exploration_strategies(
        self,
        primary_strategy: Strategy,
        project_context: ProjectContext,
        max_strategies: int = 3
    ) -> List[Strategy]:
        """
        Generate multiple strategies for parallel exploration.
        """
        strategies = [primary_strategy]
        
        # Add complementary strategies
        if not isinstance(primary_strategy, IterativeRefinementStrategy):
            strategies.append(self._create_strategy('iterative_refinement'))
        
        if not isinstance(primary_strategy, ParallelExplorationStrategy) and max_strategies > 2:
            strategies.append(self._create_strategy('parallel_exploration', exploration_budget=2))
        
        # Ensure we have at least max_strategies
        while len(strategies) < max_strategies:
            # Add V3 pipeline as fallback
            strategies.append(self._create_strategy('v3_pipeline'))
        
        return strategies[:max_strategies]
    
    def _create_strategy(self, strategy_name: str, **kwargs) -> Strategy:
        """Create a strategy instance with given parameters."""
        strategy_class = self.available_strategies.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy_class(self.v3_orchestrator, **kwargs)