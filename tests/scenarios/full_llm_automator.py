#!/usr/bin/env python3
"""
Full LLM Automator - Runs complete CC_AUTOMATOR4 with LLM acting as user
Handles project discovery + full orchestrator execution with API key provision
"""

import openai
import pexpect
import time
import os
import json
from pathlib import Path

# Your OpenAI API key
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"

class LLMAutomator:
    """LLM that acts as user for complete CC_AUTOMATOR4 execution"""
    
    def __init__(self, project_intent: str):
        self.project_intent = project_intent
        self.openai_api_key = OPENAI_API_KEY
        openai.api_key = OPENAI_API_KEY
        
        # System prompt for LLM acting as developer
        self.system_prompt = f"""You are a software developer using CC_AUTOMATOR4 to build: "{project_intent}"

Your goal: Complete the full automated development process.

Key behaviors:
1. For project discovery:
   - When asked "What would you like to build?": "{project_intent}"
   - Choose OpenAI/GPT options when available (you have the API key)
   - For milestone questions: respond "N" (accept the generated milestones)

2. For orchestrator execution:
   - When asked for API keys: provide "YOUR_OPENAI_API_KEY_HERE"
   - For confirmations: "y" (proceed with execution)
   - For continue questions: "y" (keep going)

Responses should be brief and direct:
- API key questions: provide the full key
- Choice questions: pick the number for OpenAI options
- Y/N questions: "y" or "N" as appropriate
- Project idea: exact project intent

You're experienced and want to build this quickly using OpenAI.
"""

    def get_llm_response(self, prompt: str, context: str = "") -> str:
        """Get LLM response for any prompt during the process"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Context: {context}\n\nThe system is asking: {prompt}\n\nWhat should I respond?"}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Clean up response - extract just the key part
            if "OPENAI_API_KEY" in prompt.upper() or "api" in prompt.lower():
                return self.openai_api_key
            elif any(word in answer.lower() for word in ['respond with', 'answer', 'say']):
                # Extract quoted response
                import re
                quoted = re.search(r'"([^"]*)"', answer)
                if quoted:
                    return quoted.group(1)
            
            return answer
            
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            # Smart fallbacks
            if "what would you like to build" in prompt.lower():
                return self.project_intent
            elif "api" in prompt.lower() and "key" in prompt.lower():
                return self.openai_api_key
            elif "choose" in prompt.lower() or "[1-" in prompt:
                return "1"
            elif "modify" in prompt.lower() or "milestone" in prompt.lower():
                return "N"
            elif "continue" in prompt.lower() or "proceed" in prompt.lower():
                return "y"
            else:
                return "y"

    def run_full_automation(self, project_name: str):
        """Run complete CC_AUTOMATOR4: discovery + orchestrator"""
        
        print(f"\n{'='*80}")
        print(f"🤖 FULL LLM AUTOMATION TEST")
        print(f"📝 Project: {project_name}")
        print(f"🎯 Intent: {self.project_intent}")
        print(f"🔑 API Key: {self.openai_api_key[:20]}...")
        print(f"{'='*80}")
        
        # Clean up existing project
        project_dir = Path(f"auto_{project_name}")
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
        
        # Phase 1: Project Discovery
        print("\n🔍 PHASE 1: PROJECT DISCOVERY")
        print("-" * 50)
        
        if not self._run_project_discovery(f"auto_{project_name}"):
            print("❌ Project discovery failed")
            return False
        
        # Phase 2: Full Orchestrator Execution
        print("\n🚀 PHASE 2: FULL ORCHESTRATOR EXECUTION")
        print("-" * 50)
        
        if not self._run_orchestrator(f"auto_{project_name}"):
            print("❌ Orchestrator execution failed")
            return False
        
        # Phase 3: Validation
        print("\n✅ PHASE 3: VALIDATION")
        print("-" * 50)
        
        return self._validate_results(project_dir)

    def _run_project_discovery(self, project_name: str) -> bool:
        """Run project discovery with LLM user"""
        try:
            cmd = f"python project_setup_cli.py --project {project_name} --openai-api-key {self.openai_api_key} --auto-openai"
            child = pexpect.spawn(cmd, timeout=120)
            
            # Handle project discovery prompts
            while True:
                try:
                    index = child.expect([
                        r"Your project idea:",
                        r"Choose approach \[1-\d+\]",
                        r"Would you like to modify.*\(y/N\)",
                        pexpect.EOF,
                        pexpect.TIMEOUT
                    ], timeout=30)
                    
                    if index == 0:  # Project idea
                        response = self.project_intent
                        print(f"🤖 Project idea: {response}")
                        child.sendline(response)
                        
                    elif index == 1:  # Choose approach
                        response = self.get_llm_response("Choose approach", str(child.before))
                        print(f"🤖 Approach choice: {response}")
                        child.sendline(response)
                        
                    elif index == 2:  # Modify milestones
                        response = "N"
                        print(f"🤖 Milestone modification: {response}")
                        child.sendline(response)
                        
                    elif index == 3:  # EOF
                        break
                        
                    elif index == 4:  # TIMEOUT
                        print("⏰ Discovery timeout - checking status")
                        break
                        
                except pexpect.EOF:
                    break
                except pexpect.TIMEOUT:
                    print("⏰ Timeout in discovery")
                    break
            
            child.close()
            
            if child.exitstatus == 0:
                print("✅ Project discovery completed successfully")
                return True
            else:
                print(f"❌ Discovery failed with exit code: {child.exitstatus}")
                return False
                
        except Exception as e:
            print(f"❌ Discovery error: {e}")
            return False

    def _run_orchestrator(self, project_name: str) -> bool:
        """Run full orchestrator with LLM handling user interactions"""
        try:
            # Set up environment
            os.environ['OPENAI_API_KEY'] = self.openai_api_key
            
            cmd = f"USE_CLAUDE_SDK=false python cli.py --project {project_name} --force-sonnet"
            child = pexpect.spawn(cmd, timeout=3600)  # 1 hour timeout for full execution
            
            interaction_count = 0
            
            while True:
                try:
                    index = child.expect([
                        r"Missing required API keys: ([^\r\n]+)",
                        r"Please set these environment variables",
                        r"Continue with execution\? \(y/N\)",
                        r"Proceed with milestone \d+\? \(y/N\)",
                        r"API key.*:",
                        r"Enter.*:",
                        r"\(y/N\)",
                        r"\(Y/n\)",
                        pexpect.EOF,
                        pexpect.TIMEOUT
                    ], timeout=300)  # 5 minute timeout per interaction
                    
                    interaction_count += 1
                    
                    if index == 0:  # Missing API keys
                        # Extract which keys are missing
                        missing_keys = child.match.group(1).decode()
                        print(f"🔑 System needs API keys: {missing_keys}")
                        if "OPENAI_API_KEY" in missing_keys:
                            print(f"🤖 Providing OpenAI API key")
                            # The key should already be in environment, but let's continue
                        
                    elif index == 1:  # Environment variable instruction
                        print("📝 System showing environment setup instructions")
                        
                    elif index == 2 or index == 3:  # Continue/Proceed questions
                        response = "y"
                        print(f"🤖 Continuing execution: {response}")
                        child.sendline(response)
                        
                    elif index == 4 or index == 5:  # API key or other input
                        prompt = str(child.before)
                        if "api" in prompt.lower():
                            response = self.openai_api_key
                            print(f"🤖 Providing API key")
                        else:
                            response = self.get_llm_response(prompt, "orchestrator execution")
                            print(f"🤖 LLM response: {response}")
                        child.sendline(response)
                        
                    elif index == 6 or index == 7:  # Y/N questions
                        response = "y"
                        print(f"🤖 Confirming: {response}")
                        child.sendline(response)
                        
                    elif index == 8:  # EOF
                        print("✅ Orchestrator execution completed")
                        break
                        
                    elif index == 9:  # TIMEOUT
                        print(f"⏰ Timeout after {interaction_count} interactions")
                        print(f"Last output: {child.before}")
                        break
                        
                    # Progress indicator
                    if interaction_count % 10 == 0:
                        print(f"📊 Interactions handled: {interaction_count}")
                        
                except pexpect.EOF:
                    print("✅ Process completed")
                    break
                except pexpect.TIMEOUT:
                    print(f"⏰ Timeout during orchestrator execution (interaction {interaction_count})")
                    break
            
            child.close()
            
            success = child.exitstatus == 0
            if success:
                print(f"✅ Orchestrator completed successfully after {interaction_count} interactions")
            else:
                print(f"❌ Orchestrator failed with exit code: {child.exitstatus}")
            
            return success
            
        except Exception as e:
            print(f"❌ Orchestrator error: {e}")
            return False

    def _validate_results(self, project_dir: Path) -> bool:
        """Validate the final results"""
        print(f"🔍 Validating results in {project_dir}")
        
        checks = {
            "CLAUDE.md exists": (project_dir / "CLAUDE.md").exists(),
            "main.py exists": (project_dir / "main.py").exists(),
            "Discovery JSON exists": (project_dir / ".cc_automator" / "project_discovery.json").exists(),
            "Progress tracked": (project_dir / ".cc_automator" / "progress.json").exists(),
            "Final report exists": (project_dir / ".cc_automator" / "final_report.md").exists(),
        }
        
        print("\n📋 VALIDATION RESULTS:")
        all_passed = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
            if not passed:
                all_passed = False
        
        # Try to run main.py
        if checks["main.py exists"]:
            print("\n🧪 Testing main.py execution...")
            try:
                import subprocess
                result = subprocess.run(
                    ["python", "main.py"], 
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env={**os.environ, "OPENAI_API_KEY": self.openai_api_key}
                )
                
                if result.returncode == 0:
                    print("✅ main.py runs successfully")
                    print(f"Output: {result.stdout[:200]}...")
                else:
                    print(f"❌ main.py failed: {result.stderr[:200]}...")
                    
            except subprocess.TimeoutExpired:
                print("⏰ main.py test timed out (may be interactive)")
            except Exception as e:
                print(f"❌ Error testing main.py: {e}")
        
        return all_passed


def main():
    """Run full automation tests for different project types"""
    
    test_projects = [
        ("learning_system", "learning recommendation system that adapts to student progress"),
        ("doc_chatbot", "chatbot that answers questions about technical documentation"),
        ("research_graphrag", "graphrag system for analyzing research papers"),
    ]
    
    results = {}
    
    for project_name, project_intent in test_projects:
        print(f"\n{'='*100}")
        print(f"🚀 STARTING FULL AUTOMATION: {project_name.upper()}")
        print(f"{'='*100}")
        
        automator = LLMAutomator(project_intent)
        success = automator.run_full_automation(project_name)
        results[project_name] = success
        
        print(f"\n🏁 RESULT: {project_name} = {'SUCCESS' if success else 'FAILED'}")
        
        # Brief pause between tests
        time.sleep(5)
    
    # Final summary
    print(f"\n{'='*100}")
    print("🎯 FULL AUTOMATION TEST SUMMARY")
    print(f"{'='*100}")
    
    for project_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {status} {project_name}")
    
    total_success = sum(results.values())
    total_tests = len(results)
    print(f"\n📊 Overall: {total_success}/{total_tests} tests passed")
    
    if total_success == total_tests:
        print("🎉 ALL AUTOMATION TESTS SUCCESSFUL!")
    else:
        print(f"⚠️  {total_tests - total_success} tests failed")


if __name__ == "__main__":
    main()