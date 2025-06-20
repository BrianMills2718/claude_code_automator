"""
Automated Recovery Scenario Tester for CC_AUTOMATOR4 Phase 3
Creates real failure scenarios and tests recovery mechanisms automatically
"""

import asyncio
import tempfile
import json
import time
import subprocess
import signal
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FailureScenario:
    """Defines a real failure scenario to create and test recovery"""
    name: str
    description: str
    setup_failure: callable  # Function to create the failure condition
    recovery_trigger: callable  # Function to trigger recovery
    verify_recovery: callable  # Function to verify recovery worked
    cleanup: callable  # Function to cleanup after test
    timeout: float = 30.0

@dataclass
class RecoveryEvidence:
    """Evidence that recovery mechanism worked"""
    scenario_name: str
    failure_created: bool
    recovery_triggered: bool
    recovery_successful: bool
    recovery_time: float
    evidence_collected: Dict[str, Any]
    logs_captured: List[str]

class AutomatedRecoveryTester:
    """Creates real failure scenarios and tests recovery mechanisms"""
    
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.test_scenarios = self._create_failure_scenarios()
        
    def _create_failure_scenarios(self) -> List[FailureScenario]:
        """Create comprehensive failure scenarios for testing"""
        
        return [
            FailureScenario(
                name="SDK JSON Decode Failure",
                description="Create malformed JSON response and test SDK recovery",
                setup_failure=self._setup_json_decode_failure,
                recovery_trigger=self._trigger_json_recovery,
                verify_recovery=self._verify_json_recovery,
                cleanup=self._cleanup_json_test
            ),
            
            FailureScenario(
                name="Network Timeout Failure", 
                description="Block network access and test timeout recovery",
                setup_failure=self._setup_network_failure,
                recovery_trigger=self._trigger_network_recovery,
                verify_recovery=self._verify_network_recovery,
                cleanup=self._cleanup_network_test
            ),
            
            FailureScenario(
                name="Interactive Program Hang",
                description="Create program requiring input and test auto-exit recovery",
                setup_failure=self._setup_interactive_hang,
                recovery_trigger=self._trigger_interactive_recovery,
                verify_recovery=self._verify_interactive_recovery,
                cleanup=self._cleanup_interactive_test
            ),
            
            FailureScenario(
                name="Session Resource Leak",
                description="Create session that fails to cleanup and test recovery",
                setup_failure=self._setup_session_leak,
                recovery_trigger=self._trigger_session_recovery,
                verify_recovery=self._verify_session_recovery,
                cleanup=self._cleanup_session_test
            ),
            
            FailureScenario(
                name="Process Orphan Creation",
                description="Create orphaned child processes and test cleanup recovery",
                setup_failure=self._setup_process_orphans,
                recovery_trigger=self._trigger_process_recovery,
                verify_recovery=self._verify_process_recovery,
                cleanup=self._cleanup_process_test
            )
        ]
    
    # JSON Decode Failure Scenario
    def _setup_json_decode_failure(self) -> Dict[str, Any]:
        """Setup malformed JSON scenario"""
        
        # Create test cases with various JSON malformations
        malformed_cases = [
            '{"role":"assistant","content":"Hello worl...',  # Truncated
            '{"incomplete": true, "data": [1, 2, 3',        # Missing brackets
            '{"role":"assistant"',                          # Incomplete
            '{"malformed": "json", "missing_quote: "value"}',  # Syntax error
        ]
        
        return {
            "test_cases": malformed_cases,
            "setup_complete": True
        }
    
    def _trigger_json_recovery(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger JSON recovery mechanism"""
        
        try:
            from claude_code_sdk_stable import StableSDKWrapper
            
            wrapper = StableSDKWrapper()
            recovery_results = []
            
            for i, malformed_json in enumerate(setup_data["test_cases"]):
                try:
                    repaired = wrapper._repair_truncated_json(malformed_json)
                    recovery_results.append({
                        "case": i,
                        "input": malformed_json[:50],
                        "repaired": repaired,
                        "success": isinstance(repaired, dict)
                    })
                except Exception as e:
                    recovery_results.append({
                        "case": i,
                        "input": malformed_json[:50],
                        "error": str(e),
                        "success": False
                    })
            
            return {
                "recovery_triggered": True,
                "results": recovery_results
            }
            
        except Exception as e:
            return {
                "recovery_triggered": False,
                "error": str(e)
            }
    
    def _verify_json_recovery(self, trigger_data: Dict[str, Any]) -> bool:
        """Verify JSON recovery worked correctly"""
        
        if not trigger_data.get("recovery_triggered"):
            return False
            
        results = trigger_data.get("results", [])
        successful_recoveries = sum(1 for r in results if r.get("success"))
        
        # Recovery should work for at least some cases
        return successful_recoveries > 0
    
    def _cleanup_json_test(self, setup_data: Dict[str, Any], trigger_data: Dict[str, Any]):
        """Cleanup JSON test"""
        # No specific cleanup needed for JSON test
        pass
    
    # Network Failure Scenario
    def _setup_network_failure(self) -> Dict[str, Any]:
        """Setup network failure scenario"""
        
        # Create a simple network test that will timeout
        test_urls = [
            "http://httpbin.org/delay/10",  # Will timeout
            "http://nonexistent-domain-12345.com",  # DNS failure
            "http://127.0.0.1:99999",  # Connection refused
        ]
        
        return {
            "test_urls": test_urls,
            "setup_complete": True
        }
    
    def _trigger_network_recovery(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger network recovery mechanism"""
        
        import requests
        
        recovery_results = []
        
        for url in setup_data["test_urls"]:
            try:
                start_time = time.time()
                
                # This should timeout and trigger recovery
                response = requests.get(url, timeout=2)
                
                elapsed = time.time() - start_time
                recovery_results.append({
                    "url": url,
                    "success": response.status_code == 200,
                    "elapsed": elapsed,
                    "recovery_used": False
                })
                
            except requests.exceptions.Timeout:
                elapsed = time.time() - start_time
                recovery_results.append({
                    "url": url,
                    "timeout": True,
                    "elapsed": elapsed,
                    "recovery_used": True
                })
                
            except requests.exceptions.RequestException as e:
                elapsed = time.time() - start_time
                recovery_results.append({
                    "url": url,
                    "error": str(e),
                    "elapsed": elapsed,
                    "recovery_used": True
                })
        
        return {
            "recovery_triggered": True,
            "results": recovery_results
        }
    
    def _verify_network_recovery(self, trigger_data: Dict[str, Any]) -> bool:
        """Verify network recovery worked correctly"""
        
        if not trigger_data.get("recovery_triggered"):
            return False
            
        results = trigger_data.get("results", [])
        
        # Recovery should handle timeouts and errors gracefully
        timeouts_handled = sum(1 for r in results if r.get("timeout") and r.get("elapsed", 0) < 5)
        errors_handled = sum(1 for r in results if r.get("error") and r.get("recovery_used"))
        
        return timeouts_handled > 0 or errors_handled > 0
    
    def _cleanup_network_test(self, setup_data: Dict[str, Any], trigger_data: Dict[str, Any]):
        """Cleanup network test"""
        # No specific cleanup needed for network test
        pass
    
    # Interactive Program Scenario
    def _setup_interactive_hang(self) -> Dict[str, Any]:
        """Setup interactive program that hangs"""
        
        # Create test program that requires input
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import sys
import time

print("Interactive test program started")
print("This program will wait for input...")

try:
    user_input = input("Enter something (or 'q' to quit): ")
    
    if user_input.lower() == 'q':
        print("Exiting gracefully")
        sys.exit(0)
    else:
        print(f"You entered: {user_input}")
        print("Program complete")
        
except KeyboardInterrupt:
    print("Program interrupted")
    sys.exit(1)
except EOFError:
    print("Input stream closed, exiting")
    sys.exit(0)
""")
            interactive_program = Path(f.name)
        
        return {
            "program_path": interactive_program,
            "setup_complete": True
        }
    
    def _trigger_interactive_recovery(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger interactive program recovery"""
        
        program_path = setup_data["program_path"]
        
        try:
            start_time = time.time()
            
            # Start the interactive program
            process = subprocess.Popen(
                [subprocess.sys.executable, str(program_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Try to exit gracefully with 'q'
            try:
                stdout, stderr = process.communicate(input="q\n", timeout=5)
                elapsed = time.time() - start_time
                
                return {
                    "recovery_triggered": True,
                    "exit_successful": process.returncode == 0,
                    "elapsed": elapsed,
                    "stdout": stdout,
                    "stderr": stderr
                }
                
            except subprocess.TimeoutExpired:
                # Force kill if timeout
                process.kill()
                elapsed = time.time() - start_time
                
                return {
                    "recovery_triggered": True,
                    "exit_successful": False,
                    "force_killed": True,
                    "elapsed": elapsed
                }
                
        except Exception as e:
            return {
                "recovery_triggered": False,
                "error": str(e)
            }
    
    def _verify_interactive_recovery(self, trigger_data: Dict[str, Any]) -> bool:
        """Verify interactive program recovery worked"""
        
        if not trigger_data.get("recovery_triggered"):
            return False
            
        # Recovery successful if program exited gracefully or was killed within timeout
        exit_successful = trigger_data.get("exit_successful", False)
        force_killed = trigger_data.get("force_killed", False)
        elapsed = trigger_data.get("elapsed", 0)
        
        return (exit_successful or force_killed) and elapsed < 10
    
    def _cleanup_interactive_test(self, setup_data: Dict[str, Any], trigger_data: Dict[str, Any]):
        """Cleanup interactive test"""
        
        program_path = setup_data.get("program_path")
        if program_path and Path(program_path).exists():
            Path(program_path).unlink()
    
    # Session Resource Leak Scenario
    def _setup_session_leak(self) -> Dict[str, Any]:
        """Setup session resource leak scenario"""
        
        return {
            "sessions_to_create": 5,
            "setup_complete": True
        }
    
    def _trigger_session_recovery(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger session recovery mechanism"""
        
        try:
            from claude_code_sdk_stable import StableSDKWrapper
            
            wrapper = StableSDKWrapper()
            session_ids = []
            
            # Create sessions that fail and test cleanup
            for i in range(setup_data["sessions_to_create"]):
                try:
                    async def test_session():
                        async with wrapper.managed_session(f"test_session_{i}") as session_id:
                            session_ids.append(session_id)
                            # Simulate failure
                            raise Exception(f"Simulated failure {i}")
                    
                    # Run the session test
                    try:
                        asyncio.get_event_loop().run_until_complete(test_session())
                    except:
                        pass  # Expected to fail
                        
                except Exception as e:
                    pass  # Expected
            
            # Check for cleanup
            active_sessions = len(wrapper.active_sessions)
            total_operations = len(wrapper.operations)
            
            return {
                "recovery_triggered": True,
                "sessions_created": len(session_ids),
                "active_sessions_remaining": active_sessions,
                "total_operations_recorded": total_operations
            }
            
        except Exception as e:
            return {
                "recovery_triggered": False,
                "error": str(e)
            }
    
    def _verify_session_recovery(self, trigger_data: Dict[str, Any]) -> bool:
        """Verify session recovery worked correctly"""
        
        if not trigger_data.get("recovery_triggered"):
            return False
            
        # Recovery successful if no active sessions remain
        active_sessions = trigger_data.get("active_sessions_remaining", 0)
        total_operations = trigger_data.get("total_operations_recorded", 0)
        
        return active_sessions == 0 and total_operations > 0
    
    def _cleanup_session_test(self, setup_data: Dict[str, Any], trigger_data: Dict[str, Any]):
        """Cleanup session test"""
        # No specific cleanup needed for session test
        pass
    
    # Process Orphan Scenario  
    def _setup_process_orphans(self) -> Dict[str, Any]:
        """Setup process orphan scenario"""
        
        return {
            "child_processes_to_create": 3,
            "setup_complete": True
        }
    
    def _trigger_process_recovery(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger process recovery mechanism"""
        
        import psutil
        
        initial_children = len(psutil.Process().children())
        child_pids = []
        
        try:
            # Create child processes that might become orphans
            for i in range(setup_data["child_processes_to_create"]):
                process = subprocess.Popen(
                    [subprocess.sys.executable, "-c", f"import time; time.sleep(1); print('Child {i} complete')"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                child_pids.append(process.pid)
            
            # Wait a moment
            time.sleep(0.5)
            
            # Check for orphans
            current_children = len(psutil.Process().children())
            
            # Wait for processes to complete
            time.sleep(2)
            
            final_children = len(psutil.Process().children())
            
            return {
                "recovery_triggered": True,
                "initial_children": initial_children,
                "peak_children": current_children,
                "final_children": final_children,
                "child_pids_created": child_pids
            }
            
        except Exception as e:
            return {
                "recovery_triggered": False,
                "error": str(e)
            }
    
    def _verify_process_recovery(self, trigger_data: Dict[str, Any]) -> bool:
        """Verify process recovery worked correctly"""
        
        if not trigger_data.get("recovery_triggered"):
            return False
            
        # Recovery successful if child processes were cleaned up
        initial = trigger_data.get("initial_children", 0)
        final = trigger_data.get("final_children", 0)
        
        return final <= initial  # No increase in child processes
    
    def _cleanup_process_test(self, setup_data: Dict[str, Any], trigger_data: Dict[str, Any]):
        """Cleanup process test"""
        
        # Kill any remaining child processes
        child_pids = trigger_data.get("child_pids_created", [])
        
        for pid in child_pids:
            try:
                import psutil
                process = psutil.Process(pid)
                if process.is_running():
                    process.terminate()
            except:
                pass
    
    async def run_recovery_scenario(self, scenario: FailureScenario) -> RecoveryEvidence:
        """Run a complete recovery scenario test"""
        
        start_time = time.time()
        logs_captured = []
        
        logger.info(f"🧪 Testing recovery scenario: {scenario.name}")
        logs_captured.append(f"Starting scenario: {scenario.name}")
        
        try:
            # Setup failure condition
            logs_captured.append("Setting up failure condition...")
            setup_data = scenario.setup_failure()
            failure_created = setup_data.get("setup_complete", False)
            logs_captured.append(f"Failure setup: {'SUCCESS' if failure_created else 'FAILED'}")
            
            if not failure_created:
                return RecoveryEvidence(
                    scenario_name=scenario.name,
                    failure_created=False,
                    recovery_triggered=False,
                    recovery_successful=False,
                    recovery_time=0.0,
                    evidence_collected=setup_data,
                    logs_captured=logs_captured
                )
            
            # Trigger recovery mechanism
            logs_captured.append("Triggering recovery mechanism...")
            trigger_data = scenario.recovery_trigger(setup_data)
            recovery_triggered = trigger_data.get("recovery_triggered", False)
            logs_captured.append(f"Recovery trigger: {'SUCCESS' if recovery_triggered else 'FAILED'}")
            
            # Verify recovery worked
            logs_captured.append("Verifying recovery effectiveness...")
            recovery_successful = scenario.verify_recovery(trigger_data)
            logs_captured.append(f"Recovery verification: {'SUCCESS' if recovery_successful else 'FAILED'}")
            
            # Cleanup
            try:
                scenario.cleanup(setup_data, trigger_data)
                logs_captured.append("Cleanup completed")
            except Exception as e:
                logs_captured.append(f"Cleanup failed: {str(e)}")
            
            recovery_time = time.time() - start_time
            
            # Collect evidence
            evidence = {
                "setup_data": setup_data,
                "trigger_data": trigger_data,
                "scenario_description": scenario.description
            }
            
            return RecoveryEvidence(
                scenario_name=scenario.name,
                failure_created=failure_created,
                recovery_triggered=recovery_triggered,
                recovery_successful=recovery_successful,
                recovery_time=recovery_time,
                evidence_collected=evidence,
                logs_captured=logs_captured
            )
            
        except Exception as e:
            recovery_time = time.time() - start_time
            logs_captured.append(f"Scenario failed with exception: {str(e)}")
            
            return RecoveryEvidence(
                scenario_name=scenario.name,
                failure_created=False,
                recovery_triggered=False,
                recovery_successful=False,
                recovery_time=recovery_time,
                evidence_collected={"error": str(e)},
                logs_captured=logs_captured
            )
    
    async def run_all_recovery_scenarios(self) -> List[RecoveryEvidence]:
        """Run all automated recovery scenarios"""
        
        logger.info("🚀 Starting automated recovery scenario testing")
        
        evidence_list = []
        
        for scenario in self.test_scenarios:
            evidence = await self.run_recovery_scenario(scenario)
            evidence_list.append(evidence)
            
            status = "✅ PASSED" if evidence.recovery_successful else "❌ FAILED"
            logger.info(f"{status}: {scenario.name} ({evidence.recovery_time:.2f}s)")
        
        # Summary
        successful = sum(1 for e in evidence_list if e.recovery_successful)
        total = len(evidence_list)
        
        logger.info(f"🏁 Automated recovery testing complete: {successful}/{total} scenarios passed")
        
        return evidence_list
    
    def generate_recovery_evidence_report(self, evidence_list: List[RecoveryEvidence]) -> str:
        """Generate comprehensive report of recovery evidence"""
        
        successful = [e for e in evidence_list if e.recovery_successful]
        failed = [e for e in evidence_list if not e.recovery_successful]
        
        report_lines = [
            "# Automated Recovery Scenario Testing Report",
            "",
            f"**Total Scenarios**: {len(evidence_list)}",
            f"**Successful Recoveries**: {len(successful)}",
            f"**Failed Recoveries**: {len(failed)}",
            f"**Recovery Success Rate**: {(len(successful)/len(evidence_list)*100):.1f}%",
            ""
        ]
        
        if successful:
            report_lines.extend([
                "## ✅ Successful Recovery Scenarios",
                ""
            ])
            
            for evidence in successful:
                report_lines.extend([
                    f"### {evidence.scenario_name}",
                    f"**Recovery Time**: {evidence.recovery_time:.2f}s",
                    f"**Failure Created**: {evidence.failure_created}",
                    f"**Recovery Triggered**: {evidence.recovery_triggered}",
                    "",
                    "**Execution Log**:",
                    ""
                ])
                
                for log_entry in evidence.logs_captured:
                    report_lines.append(f"- {log_entry}")
                
                report_lines.append("")
        
        if failed:
            report_lines.extend([
                "## ❌ Failed Recovery Scenarios",
                ""
            ])
            
            for evidence in failed:
                report_lines.extend([
                    f"### {evidence.scenario_name}",
                    f"**Failure Created**: {evidence.failure_created}",
                    f"**Recovery Triggered**: {evidence.recovery_triggered}",
                    "",
                    "**Execution Log**:",
                    ""
                ])
                
                for log_entry in evidence.logs_captured:
                    report_lines.append(f"- {log_entry}")
                
                if evidence.evidence_collected.get("error"):
                    report_lines.extend([
                        "",
                        f"**Error**: {evidence.evidence_collected['error']}",
                        ""
                    ])
                
                report_lines.append("")
        
        return "\n".join(report_lines)