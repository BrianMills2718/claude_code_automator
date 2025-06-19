# CC_AUTOMATOR4 V4 - Intelligent Meta-Agent Architecture Specification

## Overview

CC_AUTOMATOR4 V4 is an **intelligent, adaptive code generation system** that builds on V3's stable foundation by adding meta-agent orchestration capabilities. It maintains the core anti-cheating philosophy while introducing contextual intelligence, failure pattern learning, and adaptive strategy selection to overcome V3's rigid pipeline limitations.

## V4 Architecture (2025) - Intelligent Meta-Agent

- **Execution Engine**: Pure Claude Code SDK with async streaming (inherited from V3)
- **Meta-Agent Layer**: Intelligent orchestration that adapts strategies based on context
- **Strategy System**: Multiple orchestration approaches selected dynamically
- **Failure Learning**: Pattern recognition and adaptive recovery from failures
- **Evidence Preservation**: All V3 anti-cheating validation maintained and enhanced
- **Multi-Strategy Support**: Parallel exploration of approaches when beneficial

## Core Philosophy (Enhanced from V3)

1. **Complete Autonomy**: After initial setup, zero human intervention required
2. **Evidence-Based Validation**: Every claim must be proven with actual output (unchanged)
3. **Vertical Slice Milestones**: Each milestone produces a working, testable program
4. **Isolated Phases**: Each phase runs in a separate Claude Code instance for clean context
5. **Real Testing**: E2E tests must use actual implementations, no mocking
6. **Adaptive Intelligence**: Meta-agent learns from failures and adapts strategies
7. **Context Awareness**: Different approaches for different project types

## Architecture

### System Components

```
cc_automator4/
├── CC_AUTOMATOR_SPECIFICATION.md    # This file
├── CLAUDE_TEMPLATE.md               # Template filled for each project
├── CLAUDE_TEMPLATE_QA.md            # Interactive template filling guide
├── phase_orchestrator.py            # V3 orchestration engine (preserved)
├── preflight_validator.py           # Pre-execution validation
├── dependency_analyzer.py           # Build dependency graphs
├── progress_tracker.py              # Track and visualize progress
├── docker/
│   ├── Dockerfile                   # Isolated execution environment
│   └── docker-compose.yml           # Service configuration
├── architecture_validator.py        # Architectural quality validation
├── templates/
│   └── phase_prompts/               # Per-phase prompt templates
└── v4_components/                   # New V4 intelligent components
    ├── v4_meta_orchestrator.py      # Main V4 entry point
    ├── v4_strategy_manager.py       # Strategy selection and coordination
    ├── v4_failure_analyzer.py       # Failure pattern recognition
    ├── v4_multi_executor.py         # Parallel strategy execution
    ├── v4_context_analyzer.py       # Project context analysis
    └── strategies/                  # Individual strategy implementations
        ├── v3_pipeline_strategy.py  # Wrap existing V3 pipeline
        ├── iterative_strategy.py    # Iterative refinement approach
        └── parallel_strategy.py     # Parallel exploration approach
```

### Execution Flow

1. **Initial Setup** (One-time human interaction)
   - Run template Q&A to fill in project details
   - Validate all dependencies available
   - Create project structure

2. **Context Analysis** (New in V4)
   - Analyze project type, complexity, and requirements
   - Review codebase structure and technology stack
   - Create context profile for strategy selection

3. **Intelligent Orchestration** (Enhanced in V4)
   - For each milestone:
     - Analyze context and select optimal strategy
     - Execute strategy with failure monitoring
     - Learn from failures and adapt approach
     - Validate with V3's evidence-based system
     - Save enhanced checkpoints with learning data

### V4 Meta-Agent Components

#### 1. Strategy Manager
Coordinates different orchestration strategies based on project context and failure patterns.

```python
class V4StrategyManager:
    def select_strategy(self, context: ProjectContext, history: FailureHistory) -> Strategy:
        """Select optimal strategy based on context and past failures."""
        # Analyze project characteristics
        if context.is_simple_cli and not history.has_architecture_loops:
            return V3PipelineStrategy()  # Use proven V3 for simple cases
        
        # Complex projects with architecture issues
        if history.architecture_failure_count > 3:
            return IterativeRefinementStrategy(
                focus_phases=["research", "planning", "architecture"]
            )
        
        # Projects requiring exploration
        if context.has_ambiguous_requirements:
            return ParallelExplorationStrategy(
                exploration_budget=3
            )
```

#### 2. Failure Pattern Analyzer
Learns from V3 validation failures to improve future executions.

```python
class V4FailureAnalyzer:
    def analyze_failure(self, phase: Phase, error: Exception, context: dict) -> FailureAnalysis:
        """Analyze failure patterns and suggest adaptations."""
        patterns = self.extract_patterns(error, context)
        
        # Detect infinite loop patterns
        if self.is_infinite_loop_pattern(patterns):
            return FailureAnalysis(
                type="infinite_loop",
                root_cause=self.find_loop_trigger(patterns),
                suggested_action="step_back_with_constraints",
                constraints=self.generate_loop_breakers(patterns)
            )
        
        # Detect validation failures
        if self.is_validation_failure(patterns):
            return FailureAnalysis(
                type="validation_failure",
                root_cause=self.trace_validation_source(patterns),
                suggested_action="targeted_fix",
                fix_strategy=self.generate_fix_strategy(patterns)
            )
```

#### 3. Multi-Strategy Executor
Executes multiple strategies in parallel when beneficial, selecting best results.

```python
class V4MultiStrategyExecutor:
    async def execute_parallel_strategies(
        self, 
        strategies: List[Strategy], 
        milestone: Milestone
    ) -> ExecutionResult:
        """Run multiple strategies in parallel, select best outcome."""
        # Execute strategies concurrently
        results = await asyncio.gather(*[
            strategy.execute(milestone) 
            for strategy in strategies
        ])
        
        # Validate all results using V3 evidence system
        validated_results = [
            r for r in results 
            if self.v3_validator.validate_evidence(r.evidence)
        ]
        
        # Select best result based on evidence quality
        return self.select_best_result(validated_results)
```

#### 4. Context Analyzer
Understands project characteristics to inform intelligent decisions.

```python
class V4ContextAnalyzer:
    def analyze_project(self, project_path: Path) -> ProjectContext:
        """Analyze project to create context profile."""
        return ProjectContext(
            project_type=self.detect_project_type(),  # web, cli, library, etc.
            complexity_score=self.calculate_complexity(),
            technology_stack=self.detect_technologies(),
            test_coverage=self.analyze_test_coverage(),
            architectural_quality=self.assess_architecture(),
            requirement_clarity=self.evaluate_requirements(),
            similar_projects=self.find_similar_past_projects()
        )
```

### Phase Structure (Enhanced)

V4 maintains V3's 11-phase pipeline but adds intelligent orchestration:

```python
PHASES = [
    ("research",     "Analyze requirements and explore solutions"),
    ("planning",     "Create detailed implementation plan"),
    ("implement",    "Build the solution"),
    ("architecture", "Review implementation architecture before mechanical phases"),
    ("lint",         "Fix code style issues (flake8)"),
    ("typecheck",    "Fix type errors (mypy --strict)"),
    ("test",         "Fix unit tests (pytest)"),
    ("integration",  "Fix integration tests"),
    ("e2e",          "Verify main.py runs successfully"),
    ("validate",     "Validate all functionality is real, not mocked"),
    ("commit",       "Create git commit with changes")
]

# V4 adds strategy variations
STRATEGY_PHASE_MODIFICATIONS = {
    "iterative_refinement": {
        "phases": ["research", "planning", "mini_implement", "validate_approach"] * 3
    },
    "parallel_exploration": {
        "phases": [
            ("parallel", ["approach_1", "approach_2", "approach_3"]),
            ("merge", "Select and merge best approach"),
            ("continue", PHASES[3:])  # Continue with standard phases
        ]
    }
}
```

## Key Design Decisions (V4 Additions)

### 1. Meta-Agent Intelligence Layer

**Decision**: Add intelligent orchestration while preserving V3's evidence-based validation

**Reasoning**:
- V3's rigid pipeline causes infinite loops in complex scenarios
- Programmatic rules cannot handle all project variations
- Intelligence needed for contextual decision-making
- Evidence-based validation prevents meta-agent from lying

**Implementation**:
```python
class V4MetaOrchestrator:
    def __init__(self):
        self.v3_orchestrator = CCAutomatorOrchestrator()  # Preserve V3
        self.strategy_manager = V4StrategyManager()
        self.failure_analyzer = V4FailureAnalyzer()
        self.context_analyzer = V4ContextAnalyzer()
        
    async def orchestrate_milestone(self, milestone: Milestone):
        # Analyze context
        context = await self.context_analyzer.analyze_project()
        
        # Select strategy based on context and history
        strategy = self.strategy_manager.select_strategy(
            context, 
            self.failure_history
        )
        
        # Execute with intelligent monitoring
        result = await strategy.execute_with_learning(
            milestone,
            failure_callback=self.handle_intelligent_failure
        )
        
        # Validate using V3's evidence system
        if not self.v3_orchestrator.validate_evidence(result):
            raise ValidationError("Meta-agent result failed V3 validation")
```

### 2. Failure Pattern Learning

**Decision**: Learn from repeated failures to break infinite loops

**Reasoning**:
- V3 shows patterns like 66+ architecture phase attempts
- Same failures repeat without learning
- Pattern recognition can suggest breaking strategies
- Maintains evidence-based validation for all adaptations

**Implementation**:
```python
class FailurePatternDatabase:
    def record_failure(self, failure: PhaseFailure):
        pattern = self.extract_pattern(failure)
        self.patterns[pattern.signature].append(failure)
        
        # Detect emerging patterns
        if len(self.patterns[pattern.signature]) > 3:
            self.trigger_adaptation_strategy(pattern)
    
    def suggest_adaptation(self, current_failure: PhaseFailure) -> Strategy:
        similar_patterns = self.find_similar_patterns(current_failure)
        successful_adaptations = self.get_successful_adaptations(similar_patterns)
        return self.select_best_adaptation(successful_adaptations)
```

### 3. Multi-Strategy Orchestration

**Decision**: Support multiple strategies executing in parallel when beneficial

**Reasoning**:
- Some problems benefit from exploring multiple approaches
- Parallel exploration can find solutions faster
- V3's evidence validation ensures quality of all approaches
- Resource management prevents system overload

**Implementation**:
```python
async def execute_parallel_exploration(self, milestone: Milestone):
    # Determine if parallel exploration is beneficial
    if not self.should_explore_parallel(milestone):
        return await self.v3_strategy.execute(milestone)
    
    # Create exploration strategies
    strategies = [
        self.create_exploration_strategy(i, milestone) 
        for i in range(self.exploration_budget)
    ]
    
    # Execute with resource limits
    async with ResourceLimiter(max_concurrent=3):
        results = await self.multi_executor.execute_parallel(strategies)
    
    # Validate all results
    valid_results = [
        r for r in results 
        if self.evidence_validator.validate(r)
    ]
    
    # Select best or merge approaches
    return self.merge_or_select_best(valid_results)
```

### 4. Context-Aware Strategy Selection

**Decision**: Different strategies for different project types and states

**Reasoning**:
- One-size-fits-all approach causes V3's limitations
- Web apps, CLI tools, and libraries have different patterns
- Context informs optimal approach selection
- Preserves quality through evidence validation

**Strategy Examples**:
```python
CONTEXT_STRATEGY_MAPPING = {
    "simple_cli": V3PipelineStrategy(),  # V3 works well for simple cases
    "complex_web_app": IterativeRefinementStrategy(),  # Handle complexity
    "ambiguous_requirements": ParallelExplorationStrategy(),  # Explore options
    "ml_project": MLSpecificStrategy(),  # Domain-specific approach
    "refactoring_task": RefactoringStrategy(),  # Different phase emphasis
}
```

### 5. Evidence-Based Learning

**Decision**: Meta-agent decisions must be validated through V3's evidence system

**Reasoning**:
- Prevents meta-agent from violating anti-cheating philosophy
- All adaptations must prove effectiveness
- Learning data must be concrete, not claimed
- Maintains trust in system output

**Implementation**:
```python
def validate_meta_agent_decision(self, decision: MetaDecision) -> bool:
    # Meta-agent must provide evidence for decisions
    evidence = decision.generate_evidence()
    
    # Use V3's validation system
    validation_results = {
        "strategy_selection": self.validate_strategy_evidence(evidence.strategy),
        "failure_analysis": self.validate_failure_evidence(evidence.analysis),
        "adaptation_success": self.validate_adaptation_evidence(evidence.result)
    }
    
    # All evidence must be concrete
    return all(validation_results.values())
```

## V4-Specific Features

### 1. Adaptive Phase Parameters

Instead of fixed parameters, V4 adapts based on context and history:

```python
class AdaptivePhaseParameters:
    def get_phase_config(self, phase: str, context: ProjectContext) -> PhaseConfig:
        base_config = self.v3_defaults[phase]
        
        # Adapt based on failure history
        if self.failure_history.has_timeouts(phase):
            base_config.max_turns *= 1.5
            base_config.think_mode = "think harder"
        
        # Adapt based on project complexity
        if context.complexity_score > 0.8:
            base_config.additional_context = self.get_complexity_helpers(context)
        
        return base_config
```

### 2. Intelligent Step-Back

Enhanced from V3's step-back with learning:

```python
async def intelligent_step_back(self, failure: PhaseFailure) -> PhaseResult:
    # Analyze failure pattern
    analysis = self.failure_analyzer.deep_analyze(failure)
    
    # Determine optimal step-back target
    target_phase = self.determine_step_back_target(analysis)
    
    # Create constraints to prevent repetition
    constraints = self.generate_breaking_constraints(analysis)
    
    # Re-execute with learned constraints
    return await self.execute_with_constraints(target_phase, constraints)
```

### 3. Strategy Performance Tracking

Monitor strategy effectiveness for future improvements:

```python
class StrategyPerformanceTracker:
    def record_strategy_outcome(self, strategy: Strategy, outcome: Outcome):
        self.performance_db.record({
            "strategy_type": strategy.__class__.__name__,
            "project_context": outcome.context,
            "success_rate": outcome.success,
            "execution_time": outcome.duration,
            "resource_usage": outcome.resources,
            "failure_patterns": outcome.failures
        })
    
    def recommend_strategy(self, context: ProjectContext) -> Strategy:
        historical_performance = self.performance_db.query(
            context_similar_to=context
        )
        return self.select_best_performing(historical_performance)
```

## Migration from V3

V4 is designed as a **progressive enhancement** of V3:

1. **V3 Compatibility**: All V3 projects continue to work unchanged
2. **Opt-in Intelligence**: V4 features activated via flags
3. **Gradual Adoption**: Can use V3 strategy within V4 system
4. **Fallback Safety**: Automatic fallback to V3 on V4 failures

### Migration Path

```bash
# Run in V3 mode (default)
python cc_automator4/run.py

# Run with V4 intelligence
python cc_automator4/run.py --v4-meta-agent

# Run with specific V4 features
python cc_automator4/run.py --v4-learning --v4-context-aware

# Debug V4 decisions
python cc_automator4/run.py --v4-meta-agent --explain-decisions
```

## Success Metrics (Enhanced)

A milestone is complete when (V3 requirements maintained):
1. All required phases completed successfully 
2. main.py runs without errors and produces expected output
3. **100% test passage**: Zero failures, zero errors (strict validation)
4. Evidence logs prove real execution with concrete proof
5. Validation phase confirms no mocked implementations
6. Git commit created with proper message format

V4 additions:
7. **Strategy effectiveness**: Chosen strategy completed without infinite loops
8. **Learning validation**: Any adaptations have concrete evidence of improvement
9. **Resource efficiency**: Execution time and cost within acceptable bounds
10. **Context accuracy**: Strategy selection aligned with project characteristics

## V4 Anti-Patterns to Avoid

### ❌ Trusting Meta-Agent Claims Without Evidence
```python
# WRONG: Trust meta-agent's strategy selection
if meta_agent.claims_best_strategy("iterative"):
    use_iterative_strategy()

# CORRECT: Validate strategy selection with evidence
strategy_evidence = meta_agent.get_strategy_selection_evidence()
if validate_evidence(strategy_evidence):
    use_strategy(strategy_evidence.validated_strategy)
```

### ❌ Learning Without Validation
```python
# WRONG: Accept learned patterns without proof
learned_pattern = analyzer.detect_pattern()
apply_pattern_everywhere(learned_pattern)

# CORRECT: Validate learned patterns work
learned_pattern = analyzer.detect_pattern()
test_results = validate_pattern_effectiveness(learned_pattern)
if test_results.success_rate > 0.8:
    apply_pattern_with_monitoring(learned_pattern)
```

### ❌ Parallel Execution Without Resource Management
```python
# WRONG: Unlimited parallel strategies
strategies = create_100_strategies()
await asyncio.gather(*[s.execute() for s in strategies])

# CORRECT: Resource-limited parallel execution
strategies = create_strategies(max=3)
async with ResourceLimiter(max_concurrent=2, memory_limit="2GB"):
    results = await execute_parallel_with_monitoring(strategies)
```

## Implementation Timeline

### Phase 1: Foundation (Week 1)
- [ ] Create V4 meta-orchestrator skeleton
- [ ] Implement basic strategy manager with V3 fallback
- [ ] Add failure pattern tracking
- [ ] Preserve all V3 validation systems

### Phase 2: Intelligence (Week 2)
- [ ] Build context analyzer for project classification
- [ ] Implement multiple orchestration strategies
- [ ] Add failure pattern learning system
- [ ] Create adaptive strategy switching

### Phase 3: Optimization (Week 3)
- [ ] Add parallel strategy execution capability
- [ ] Implement intelligent resource management
- [ ] Build strategy performance tracking
- [ ] Create adaptive parameter tuning

### Phase 4: Validation (Week 4)
- [ ] Comprehensive testing of V4 features
- [ ] Validate evidence-based learning
- [ ] Performance benchmarking vs V3
- [ ] Documentation and migration guides

## Summary

CC_AUTOMATOR4 V4 enhances V3's solid foundation with intelligent orchestration that:
- **Adapts strategies** based on project context and failure patterns
- **Learns from failures** to break infinite loops and improve efficiency
- **Explores multiple approaches** when beneficial for complex problems
- **Maintains evidence-based validation** for all intelligent decisions
- **Preserves V3 compatibility** with progressive enhancement

The system combines V3's proven anti-cheating validation with V4's contextual intelligence to overcome rigid pipeline limitations while maintaining trust through concrete evidence. This creates a more flexible, intelligent system that can handle diverse project types without compromising on quality or reliability.