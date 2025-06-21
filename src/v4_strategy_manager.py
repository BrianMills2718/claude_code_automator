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
        milestone: Any,  # Actually a Milestone object
        failure_callback: Optional[Any] = None
    ) -> 'ExecutionResult':
        """Execute using standard V3 pipeline."""
        # For now, use synchronous V3 run for the whole project
        # TODO: Implement proper async milestone execution
        success = self.v3_orchestrator.run()
        
        return ExecutionResult(
            success=success == 0,  # V3 returns 0 for success
            strategy_name=self.name,
            milestone_num=milestone_num,
            evidence_files=self._gather_evidence_files(milestone_num),
            execution_time=0.0  # TODO: Track actual time
        )
    
    def get_phases(self) -> List[Phase]:
        """Return standard V3 phases."""
        # V3 orchestrator may not have phases initialized yet
        return []  # TODO: Implement proper phase retrieval
    
    def _gather_evidence_files(self, milestone_num: int) -> List[Path]:
        """Gather evidence files from V3 execution."""
        milestone_dir = self.v3_orchestrator.project_dir / '.cc_automator' / 'milestones' / f'milestone_{milestone_num}'
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
        
        # For now, delegate to V3 orchestrator to get real execution
        # TODO: Implement proper iterative refinement with focused phases
        logger.info("Executing full V3 pipeline (iterative refinement not fully implemented yet)")
        
        try:
            # Run synchronous V3 orchestrator in thread to avoid asyncio conflicts
            import asyncio
            import concurrent.futures
            
            def run_v3_sync():
                return self.v3_orchestrator.run()
            
            # Execute V3 in thread pool to avoid asyncio nesting issues
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = loop.run_in_executor(executor, run_v3_sync)
                success_code = await future
            
            success = (success_code == 0)
            
            return ExecutionResult(
                success=success,
                strategy_name=self.name,
                milestone_num=milestone_num,
                evidence_files=self._gather_evidence_files(milestone_num),
                iterations_used=1,
                execution_time=0.0  # TODO: Track actual time
            )
            
        except Exception as e:
            logger.error(f"Iterative refinement strategy failed: {str(e)}")
            return ExecutionResult(
                success=False,
                strategy_name=self.name,
                milestone_num=milestone_num,
                evidence_files=[],
                iterations_used=1
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
        # TODO: Implement proper phase creation
        from .phase_orchestrator import Phase
        return Phase(
            name=f"{phase_name}_iter_{iteration}", 
            description=f"Iterative refinement of {phase_name} phase",
            prompt="TODO: Implement proper prompt generation"
        )
    
    def _get_remaining_phases(self) -> List[Phase]:
        """Get phases not included in iterative refinement."""
        # TODO: Implement proper phase retrieval
        return []
    
    async def _validate_iteration(self, milestone_num: int, iteration: int) -> float:
        """Validate quality of current iteration."""
        # TODO: Implement proper validation
        return 0.9
    
    def _gather_evidence_files(self, milestone_num: int) -> List[Path]:
        """Gather evidence files including iteration artifacts."""
        milestone_dir = self.v3_orchestrator.project_dir / '.cc_automator' / 'milestones' / f'milestone_{milestone_num}'
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
        
        # For now, delegate to V3 orchestrator to get real execution
        # TODO: Implement proper parallel exploration with multiple approaches
        logger.info("Executing full V3 pipeline (parallel exploration not fully implemented yet)")
        
        try:
            # Run synchronous V3 orchestrator in thread to avoid asyncio conflicts
            import asyncio
            import concurrent.futures
            
            def run_v3_sync():
                return self.v3_orchestrator.run()
            
            # Execute V3 in thread pool to avoid asyncio nesting issues
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = loop.run_in_executor(executor, run_v3_sync)
                success_code = await future
            
            success = (success_code == 0)
            
            return ExecutionResult(
                success=success,
                strategy_name=self.name,
                milestone_num=milestone_num,
                evidence_files=self._gather_evidence_files(milestone_num),
                exploration_variant=0,
                exploration_score=0.8 if success else 0.0,
                execution_time=0.0  # TODO: Track actual time
            )
            
        except Exception as e:
            logger.error(f"Parallel exploration strategy failed: {str(e)}")
            return ExecutionResult(
                success=False,
                strategy_name=self.name,
                milestone_num=milestone_num,
                evidence_files=[],
                exploration_variant=-1,
                exploration_score=0.0
            )
    
    def get_phases(self) -> List[Phase]:
        """Get phases for parallel exploration."""
        # TODO: Implement proper phase retrieval
        return []
    
    def _create_exploration_variant(self, variant_num: int) -> List[Phase]:
        """Create exploration variant phases."""
        # TODO: Implement proper variant creation
        return []
    
    async def _evaluate_exploration(self, milestone_num: int, variant_num: int) -> float:
        """Evaluate quality of an exploration variant."""
        # TODO: Implement proper evaluation
        return 0.8
    
    def _gather_evidence_files(self, milestone_num: int) -> List[Path]:
        """Gather evidence files including exploration artifacts."""
        milestone_dir = self.v3_orchestrator.project_dir / '.cc_automator' / 'milestones' / f'milestone_{milestone_num}'
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