"""
V4 Failure Analyzer
Analyzes failure patterns to learn and adapt strategies.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class PhaseFailure:
    """Record of a phase failure."""
    phase_name: str
    error: Exception
    context: Dict[str, Any]
    timestamp: datetime
    milestone_num: int
    attempt_num: int
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    
    def __post_init__(self):
        if isinstance(self.error, Exception):
            self.error_type = type(self.error).__name__
            self.error_message = str(self.error)
            # Extract key parts of stack trace if available
            if hasattr(self.error, '__traceback__'):
                import traceback
                self.stack_trace = ''.join(traceback.format_tb(self.error.__traceback__)[-3:])


@dataclass 
class FailurePattern:
    """Identified pattern in failures."""
    pattern_name: str
    description: str
    frequency: int
    phases_affected: List[str]
    common_errors: List[str]
    suggested_remediation: str
    confidence: float = 0.0


@dataclass
class LoopBreakingConstraints:
    """Constraints to break infinite loops."""
    max_attempts: int
    required_changes: List[str]
    forbidden_patterns: List[str]
    additional_context: str
    force_different_approach: bool = False


class V4FailureAnalyzer:
    """
    Analyzes failure patterns to identify root causes and suggest adaptations.
    
    Key capabilities:
    - Detect infinite loop patterns
    - Identify common failure modes
    - Suggest remediation strategies
    - Generate constraints to break loops
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.failure_db_path = self.project_path / '.cc_automator' / 'v4_failure_db.json'
        self.failure_history: List[PhaseFailure] = []
        self.pattern_database = self._initialize_pattern_database()
        self.loop_detection_window = 5  # Look at last N attempts
        
        # Load historical failures
        self._load_failure_history()
        
        logger.info(f"Failure Analyzer initialized with {len(self.failure_history)} historical failures")
    
    def _initialize_pattern_database(self) -> Dict[str, FailurePattern]:
        """Initialize known failure patterns."""
        return {
            'architecture_infinite_loop': FailurePattern(
                pattern_name='architecture_infinite_loop',
                description='Architecture phase fails repeatedly with same issues',
                frequency=0,
                phases_affected=['architecture'],
                common_errors=['function too long', 'circular imports', 'complexity too high'],
                suggested_remediation='Step back to planning with stricter architectural guidelines',
                confidence=0.0
            ),
            'test_cascade_failure': FailurePattern(
                pattern_name='test_cascade_failure',
                description='Test failures cascade from poor implementation',
                frequency=0,
                phases_affected=['test', 'integration'],
                common_errors=['ImportError', 'AttributeError', 'AssertionError'],
                suggested_remediation='Step back to implementation with test-driven approach',
                confidence=0.0
            ),
            'missing_requirements': FailurePattern(
                pattern_name='missing_requirements',
                description='Implementation fails due to incomplete research',
                frequency=0,
                phases_affected=['implement', 'planning'],
                common_errors=['unclear requirements', 'missing context', 'ambiguous spec'],
                suggested_remediation='Return to research with specific questions',
                confidence=0.0
            ),
            'complexity_overwhelm': FailurePattern(
                pattern_name='complexity_overwhelm',
                description='Project too complex for single-pass implementation',
                frequency=0,
                phases_affected=['implement', 'architecture', 'test'],
                common_errors=['timeout', 'max turns exceeded', 'too many files'],
                suggested_remediation='Switch to iterative refinement strategy',
                confidence=0.0
            ),
            'import_resolution_hell': FailurePattern(
                pattern_name='import_resolution_hell',
                description='Persistent import and module resolution issues',
                frequency=0,
                phases_affected=['typecheck', 'test', 'integration'],
                common_errors=['ModuleNotFoundError', 'ImportError', 'circular import'],
                suggested_remediation='Restructure project layout and fix __init__.py files',
                confidence=0.0
            )
        }
    
    def record_phase_failure(
        self,
        phase_name: str,
        error: Exception,
        context: Dict[str, Any]
    ):
        """Record a phase failure for analysis."""
        failure = PhaseFailure(
            phase_name=phase_name,
            error=error,
            context=context,
            timestamp=datetime.now(),
            milestone_num=context.get('milestone_num', 0),
            attempt_num=len([f for f in self.failure_history 
                            if f.phase_name == phase_name and 
                            f.milestone_num == context.get('milestone_num', 0)]) + 1
        )
        
        self.failure_history.append(failure)
        
        # Update pattern detection
        self._update_pattern_detection(failure)
        
        # Save to persistent storage
        self._save_failure_history()
        
        logger.info(f"Recorded failure: {phase_name} attempt {failure.attempt_num} - {failure.error_type}")
    
    async def analyze_failure(
        self,
        strategy: Any,
        error: Exception,
        context: Dict[str, Any]
    ) -> 'FailureAnalysis':
        """
        Analyze a failure and suggest remediation.
        """
        from .v4_strategy_manager import FailureAnalysis
        
        # Get recent failures for context
        phase_name = context.get('current_phase', 'unknown')
        recent_failures = self._get_recent_failures(phase_name, context.get('milestone_num', 0))
        
        # Detect patterns
        detected_patterns = self._detect_patterns(recent_failures, error)
        
        # Determine root cause
        root_cause = self._analyze_root_cause(recent_failures, error, context)
        
        # Generate suggested action
        suggested_action = self._determine_suggested_action(
            detected_patterns,
            root_cause,
            strategy,
            context
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(detected_patterns, recent_failures)
        
        # Generate constraints if needed
        constraints = None
        if suggested_action in ['step_back_with_constraints', 'retry_with_constraints']:
            constraints = self.generate_loop_breaking_constraints(phase_name, context)
        
        analysis = FailureAnalysis(
            failure_type=self._categorize_failure(error),
            root_cause=root_cause,
            pattern_name=detected_patterns[0].pattern_name if detected_patterns else 'unknown',
            suggested_action=suggested_action,
            confidence=confidence,
            constraints=constraints
        )
        
        logger.info(f"Failure analysis: {analysis.pattern_name} - {analysis.suggested_action} "
                   f"(confidence: {analysis.confidence:.2f})")
        
        return analysis
    
    def detect_infinite_loop(self, phase_name: str, context: Dict[str, Any]) -> bool:
        """
        Detect if we're in an infinite loop pattern.
        """
        milestone_num = context.get('milestone_num', 0)
        recent_failures = self._get_recent_failures(phase_name, milestone_num)
        
        if len(recent_failures) < 3:
            return False
        
        # Check for repeated error patterns
        error_messages = [f.error_message for f in recent_failures[-self.loop_detection_window:]]
        
        # If same error repeats 3+ times, it's likely a loop
        error_counts = Counter(error_messages)
        max_repetition = max(error_counts.values()) if error_counts else 0
        
        if max_repetition >= 3:
            logger.warning(f"Infinite loop detected in {phase_name}: "
                          f"same error repeated {max_repetition} times")
            return True
        
        # Check for cycling through same set of errors
        if len(recent_failures) >= 6:
            # Look for ABAB or ABCABC patterns
            pattern_length = min(3, len(recent_failures) // 2)
            for plen in range(2, pattern_length + 1):
                if self._has_repeating_pattern(error_messages[-plen*2:], plen):
                    logger.warning(f"Infinite loop detected in {phase_name}: "
                                  f"cycling error pattern of length {plen}")
                    return True
        
        return False
    
    def generate_loop_breaking_constraints(
        self,
        phase_name: str,
        context: Dict[str, Any]
    ) -> LoopBreakingConstraints:
        """
        Generate constraints to break infinite loops.
        """
        recent_failures = self._get_recent_failures(
            phase_name, 
            context.get('milestone_num', 0)
        )
        
        # Analyze what's causing the loop
        common_issues = self._extract_common_issues(recent_failures)
        
        constraints = LoopBreakingConstraints(
            max_attempts=1,  # Only one attempt with these constraints
            required_changes=[],
            forbidden_patterns=[],
            additional_context=""
        )
        
        # Phase-specific constraints
        if phase_name == 'architecture':
            constraints.required_changes = [
                "Break large functions into smaller ones BEFORE validation",
                "Ensure all imports are at top of files",
                "Create __init__.py files for all packages"
            ]
            constraints.forbidden_patterns = [
                "Functions longer than 40 lines",
                "Classes with more than 15 methods",
                "Circular imports"
            ]
            constraints.additional_context = """
CRITICAL: The architecture validator is VERY strict. You must:
1. Split ANY function over 40 lines into smaller functions
2. Split ANY class over 15 methods into smaller classes  
3. Fix ALL import issues before proceeding
4. Ensure proper package structure with __init__.py files
"""
        
        elif phase_name == 'test':
            constraints.required_changes = [
                "Ensure all imports can be resolved",
                "Mock external dependencies in unit tests",
                "Test behavior, not implementation"
            ]
            constraints.forbidden_patterns = [
                "Testing private methods directly",
                "Tests that depend on specific implementation details",
                "Missing test fixtures"
            ]
            constraints.additional_context = """
Focus on making tests PASS, not perfect. Common issues:
1. Import errors - ensure test files can import the modules
2. Missing fixtures - create necessary test data
3. Over-specific assertions - test behavior, not implementation
"""
        
        elif phase_name == 'implement':
            constraints.required_changes = [
                "Start with minimal working implementation",
                "Add features incrementally",
                "Ensure each component is testable"
            ]
            constraints.forbidden_patterns = [
                "Implementing everything at once",
                "Complex inheritance hierarchies",
                "Tight coupling between components"
            ]
            constraints.force_different_approach = len(recent_failures) > 5
        
        # Add failure-specific constraints
        for issue in common_issues[:3]:  # Top 3 issues
            constraints.additional_context += f"\nKNOWN ISSUE: {issue} - ensure this is addressed"
        
        return constraints
    
    def trace_failure_root_cause(
        self,
        failed_phase: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trace failure back to root cause phase.
        """
        milestone_num = context.get('milestone_num', 0)
        all_failures = [
            f for f in self.failure_history 
            if f.milestone_num == milestone_num
        ]
        
        # Build failure chain
        failure_chain = self._build_failure_chain(all_failures)
        
        # Identify patterns in the chain
        if self._is_cascade_failure(failure_chain):
            # Find the originating phase
            root_phase = failure_chain[0].phase_name if failure_chain else failed_phase
            return {
                'pattern': self._get_cascade_pattern(root_phase, failed_phase),
                'root_phase': root_phase,
                'confidence': 0.8
            }
        
        # Check for specific root cause patterns
        if failed_phase == 'test' and self._has_implementation_issues(all_failures):
            return {
                'pattern': 'test_failures',
                'root_phase': 'implement',
                'confidence': 0.7
            }
        
        if failed_phase == 'architecture' and len(all_failures) > 10:
            return {
                'pattern': 'architecture_loops',
                'root_phase': 'planning',
                'confidence': 0.9
            }
        
        return {
            'pattern': 'unknown',
            'root_phase': failed_phase,
            'confidence': 0.3
        }
    
    def _get_recent_failures(self, phase_name: str, milestone_num: int) -> List[PhaseFailure]:
        """Get recent failures for a specific phase and milestone."""
        return [
            f for f in self.failure_history
            if f.phase_name == phase_name and f.milestone_num == milestone_num
        ][-self.loop_detection_window:]
    
    def _detect_patterns(
        self,
        recent_failures: List[PhaseFailure],
        current_error: Exception
    ) -> List[FailurePattern]:
        """Detect failure patterns from recent history."""
        detected = []
        
        for pattern_name, pattern in self.pattern_database.items():
            confidence = self._match_pattern(pattern, recent_failures, current_error)
            if confidence > 0.5:
                pattern.confidence = confidence
                pattern.frequency = len([
                    f for f in recent_failures 
                    if any(err in f.error_message.lower() for err in pattern.common_errors)
                ])
                detected.append(pattern)
        
        # Sort by confidence
        detected.sort(key=lambda p: p.confidence, reverse=True)
        return detected
    
    def _match_pattern(
        self,
        pattern: FailurePattern,
        failures: List[PhaseFailure],
        current_error: Exception
    ) -> float:
        """Calculate confidence that failures match a pattern."""
        if not failures:
            return 0.0
        
        confidence = 0.0
        
        # Check if phases match
        failure_phases = {f.phase_name for f in failures}
        if failure_phases.intersection(pattern.phases_affected):
            confidence += 0.3
        
        # Check for common errors
        error_messages = [f.error_message.lower() for f in failures]
        error_messages.append(str(current_error).lower())
        
        matches = sum(
            1 for msg in error_messages
            for err in pattern.common_errors
            if err in msg
        )
        
        if matches > 0:
            confidence += min(0.5, matches * 0.1)
        
        # Special cases
        if pattern.pattern_name == 'architecture_infinite_loop' and len(failures) > 5:
            confidence += 0.2
        
        if pattern.pattern_name == 'complexity_overwhelm':
            if any('timeout' in f.error_message.lower() or 'max turns' in f.error_message.lower() 
                   for f in failures):
                confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _analyze_root_cause(
        self,
        recent_failures: List[PhaseFailure],
        error: Exception,
        context: Dict[str, Any]
    ) -> str:
        """Analyze and describe the root cause."""
        if not recent_failures:
            return f"First occurrence of {type(error).__name__}"
        
        # Look for progression of errors
        error_progression = [f.error_type for f in recent_failures]
        
        if len(set(error_progression)) == 1:
            # Same error repeating
            return f"Persistent {error_progression[0]} not being resolved"
        
        # Check for cascade patterns
        if 'ImportError' in error_progression and 'AttributeError' in error_progression:
            return "Import structure issues cascading to attribute errors"
        
        if 'timeout' in str(error).lower():
            return "Complexity overwhelming available resources"
        
        # Phase-specific root causes
        phase = context.get('current_phase', '')
        if phase == 'architecture' and len(recent_failures) > 3:
            return "Implementation violating architectural constraints repeatedly"
        
        if phase == 'test' and 'AssertionError' in error_progression:
            return "Implementation not meeting test expectations"
        
        return f"Multiple issues: {', '.join(set(error_progression))}"
    
    def _determine_suggested_action(
        self,
        patterns: List[FailurePattern],
        root_cause: str,
        strategy: Any,
        context: Dict[str, Any]
    ) -> str:
        """Determine the best action based on analysis."""
        if patterns and patterns[0].confidence > 0.7:
            # High confidence pattern detected
            pattern = patterns[0]
            
            if pattern.pattern_name == 'architecture_infinite_loop':
                return 'step_back_with_constraints'
            
            if pattern.pattern_name == 'complexity_overwhelm':
                return 'switch_strategy'
            
            if pattern.pattern_name == 'missing_requirements':
                return 'step_back_with_constraints'
        
        # Check for simple retry vs strategy switch
        phase_failures = len(self._get_recent_failures(
            context.get('current_phase', ''),
            context.get('milestone_num', 0)
        ))
        
        if phase_failures < 2:
            return 'retry_with_feedback'
        elif phase_failures < 4:
            return 'retry_with_constraints'
        else:
            return 'switch_strategy'
    
    def _calculate_confidence(
        self,
        patterns: List[FailurePattern],
        failures: List[PhaseFailure]
    ) -> float:
        """Calculate overall confidence in the analysis."""
        if not patterns:
            return 0.3
        
        # Base confidence on best pattern
        confidence = patterns[0].confidence if patterns else 0.0
        
        # Adjust based on failure history
        if len(failures) > 5:
            confidence *= 1.2  # More data = more confidence
        elif len(failures) < 2:
            confidence *= 0.7  # Less data = less confidence
        
        return min(confidence, 1.0)
    
    def _categorize_failure(self, error: Exception) -> str:
        """Categorize the type of failure."""
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        if 'timeout' in error_msg:
            return 'timeout'
        elif 'import' in error_msg or error_type in ['ImportError', 'ModuleNotFoundError']:
            return 'import_error'
        elif 'syntax' in error_msg or error_type == 'SyntaxError':
            return 'syntax_error'
        elif 'assert' in error_msg or error_type == 'AssertionError':
            return 'assertion_error'
        elif 'validation' in error_msg:
            return 'validation_error'
        elif 'attribute' in error_msg or error_type == 'AttributeError':
            return 'attribute_error'
        else:
            return 'general_error'
    
    def _has_repeating_pattern(self, messages: List[str], pattern_length: int) -> bool:
        """Check if messages contain a repeating pattern of given length."""
        if len(messages) < pattern_length * 2:
            return False
        
        for i in range(pattern_length):
            if messages[i] != messages[i + pattern_length]:
                return False
        
        return True
    
    def _extract_common_issues(self, failures: List[PhaseFailure]) -> List[str]:
        """Extract common issues from failures."""
        issues = []
        
        # Extract key phrases from error messages
        for failure in failures:
            msg = failure.error_message.lower()
            
            # Extract specific issues
            if 'line' in msg and 'too long' in msg:
                # Extract function name and line count
                match = re.search(r'function (\w+).*?(\d+) lines', msg)
                if match:
                    issues.append(f"Function {match.group(1)} is {match.group(2)} lines")
            
            if 'import' in msg:
                # Extract import issues
                match = re.search(r'cannot import name [\'"](\w+)[\'"]', msg)
                if match:
                    issues.append(f"Cannot import {match.group(1)}")
            
            if 'missing' in msg:
                # Extract missing items
                match = re.search(r'missing (\w+)', msg)
                if match:
                    issues.append(f"Missing {match.group(1)}")
        
        # Return unique issues, most common first
        issue_counts = Counter(issues)
        return [issue for issue, _ in issue_counts.most_common()]
    
    def _build_failure_chain(self, failures: List[PhaseFailure]) -> List[PhaseFailure]:
        """Build a chain of related failures."""
        if not failures:
            return []
        
        # Sort by timestamp
        sorted_failures = sorted(failures, key=lambda f: f.timestamp)
        
        # Group sequential failures
        chain = []
        last_time = None
        
        for failure in sorted_failures:
            if last_time is None or (failure.timestamp - last_time).seconds < 3600:  # Within 1 hour
                chain.append(failure)
                last_time = failure.timestamp
            else:
                # Gap too large, start new chain
                chain = [failure]
                last_time = failure.timestamp
        
        return chain
    
    def _is_cascade_failure(self, chain: List[PhaseFailure]) -> bool:
        """Check if failures form a cascade pattern."""
        if len(chain) < 2:
            return False
        
        # Check if phases follow dependency order
        phase_order = [
            'research', 'planning', 'implement', 'architecture',
            'lint', 'typecheck', 'test', 'integration', 'e2e'
        ]
        
        phase_indices = []
        for failure in chain:
            if failure.phase_name in phase_order:
                phase_indices.append(phase_order.index(failure.phase_name))
        
        # Check if indices are generally increasing (cascade)
        if len(phase_indices) >= 2:
            return all(phase_indices[i] <= phase_indices[i+1] + 1 
                      for i in range(len(phase_indices)-1))
        
        return False
    
    def _get_cascade_pattern(self, root_phase: str, failed_phase: str) -> str:
        """Get pattern name for cascade failure."""
        patterns = {
            ('research', 'implement'): 'missing_requirements',
            ('planning', 'architecture'): 'architecture_loops',
            ('implement', 'test'): 'test_failures',
            ('architecture', 'integration'): 'integration_issues'
        }
        
        return patterns.get((root_phase, failed_phase), 'cascade_failure')
    
    def _has_implementation_issues(self, failures: List[PhaseFailure]) -> bool:
        """Check if test failures are due to implementation issues."""
        impl_failures = [f for f in failures if f.phase_name == 'implement']
        test_failures = [f for f in failures if f.phase_name == 'test']
        
        if impl_failures and test_failures:
            # Check if test failures mention implementation issues
            for tf in test_failures:
                if any(keyword in tf.error_message.lower() 
                      for keyword in ['import', 'attribute', 'not found', 'undefined']):
                    return True
        
        return False
    
    def _update_pattern_detection(self, failure: PhaseFailure):
        """Update pattern database with new failure."""
        # This could be enhanced with ML in the future
        for pattern in self.pattern_database.values():
            if failure.phase_name in pattern.phases_affected:
                # Simple frequency update
                pattern.frequency += 1
    
    def _load_failure_history(self):
        """Load failure history from disk."""
        if self.failure_db_path.exists():
            try:
                with open(self.failure_db_path) as f:
                    data = json.load(f)
                    # Convert back to PhaseFailure objects
                    self.failure_history = [
                        PhaseFailure(
                            phase_name=f['phase_name'],
                            error=Exception(f['error_message']),  # Simplified
                            context=f['context'],
                            timestamp=datetime.fromisoformat(f['timestamp']),
                            milestone_num=f['milestone_num'],
                            attempt_num=f['attempt_num'],
                            error_type=f['error_type'],
                            error_message=f['error_message']
                        )
                        for f in data.get('failures', [])
                    ]
            except Exception as e:
                logger.warning(f"Failed to load failure history: {e}")
                self.failure_history = []
    
    def _save_failure_history(self):
        """Save failure history to disk."""
        self.failure_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to serializable format
        data = {
            'failures': [
                {
                    'phase_name': f.phase_name,
                    'error_type': f.error_type,
                    'error_message': f.error_message,
                    'context': f.context,
                    'timestamp': f.timestamp.isoformat(),
                    'milestone_num': f.milestone_num,
                    'attempt_num': f.attempt_num
                }
                for f in self.failure_history[-100:]  # Keep last 100 failures
            ]
        }
        
        try:
            with open(self.failure_db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save failure history: {e}")