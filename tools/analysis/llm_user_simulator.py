#!/usr/bin/env python3
"""
LLM User Simulator - Uses OpenAI to act as a human user during project discovery
"""

import openai
import json
import subprocess
import sys
from pathlib import Path
import time
import threading
import queue
import select

class LLMUserSimulator:
    """Uses OpenAI to simulate a human user interacting with CC_AUTOMATOR4"""
    
    def __init__(self, api_key: str, project_intent: str):
        self.api_key = api_key
        self.project_intent = project_intent
        openai.api_key = api_key
        
        # System prompt for the LLM acting as user
        self.system_prompt = f"""You are a software developer interacting with CC_AUTOMATOR4, an intelligent project setup system.

Your goal: Build "{self.project_intent}"

Instructions:
1. When asked "What would you like to build?", respond with exactly: "{self.project_intent}"
2. When shown technology choices (numbered options), pick the option that:
   - Uses OpenAI/GPT if available (you prefer OpenAI since you have the API key)
   - Is marked as "recommended" if no OpenAI option exists
   - Is the simplest/fastest to get started
3. When asked about milestones, respond with "N" (no changes needed)
4. Be concise - give short, direct answers
5. If asked yes/no questions, respond "y" or "n"
6. If you see "Choose approach [1-X]", respond with just the number

Example responses:
- For "What would you like to build?": "{self.project_intent}"
- For technology choices: Just the number like "3"
- For milestone questions: "N"
- For confirmations: "y"

Stay in character as a developer who wants to build this project quickly using OpenAI.
"""

    def get_llm_response(self, prompt: str) -> str:
        """Get response from OpenAI acting as the user"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"The system is asking: {prompt}\n\nWhat should I respond?"}
                ],
                max_tokens=100,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content.strip()
            print(f"🤖 LLM User Response: {answer}")
            return answer
            
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            # Fallback responses
            if "what would you like to build" in prompt.lower():
                return self.project_intent
            elif "choose approach" in prompt.lower():
                return "1"  # Default to first option
            elif "modify" in prompt.lower():
                return "N"
            else:
                return "y"

    def simulate_interaction(self, project_name: str):
        """Run CC_AUTOMATOR4 with LLM acting as user"""
        
        print(f"\n{'='*60}")
        print(f"🤖 LLM USER SIMULATION")
        print(f"📝 Project: {project_name}")
        print(f"🎯 Intent: {self.project_intent}")
        print(f"{'='*60}")
        
        # Clean up any existing test project
        project_dir = Path(f"llm_test_{project_name}")
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
        
        try:
            # Start the CC_AUTOMATOR4 process
            cmd = [
                "python", "project_setup_cli.py",
                "--project", f"llm_test_{project_name}",
                "--openai-api-key", self.api_key
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Interactive communication with the process
            output_buffer = ""
            
            while True:
                # Read available output
                ready, _, _ = select.select([process.stdout], [], [], 0.1)
                if ready:
                    char = process.stdout.read(1)
                    if char:
                        output_buffer += char
                        print(char, end='', flush=True)
                        
                        # Check if we need to respond
                        if self._should_respond(output_buffer):
                            response = self._get_response_for_prompt(output_buffer)
                            print(f"\n🤖 Sending: {response}")
                            process.stdin.write(response + "\n")
                            process.stdin.flush()
                            output_buffer = ""  # Clear buffer after response
                    else:
                        break
                
                # Check if process finished
                if process.poll() is not None:
                    break
                    
                time.sleep(0.1)
            
            # Get any remaining output
            remaining_output, error_output = process.communicate()
            if remaining_output:
                print(remaining_output)
            if error_output:
                print(f"STDERR: {error_output}")
            
            return_code = process.returncode
            
            if return_code == 0:
                print("✅ LLM USER SIMULATION SUCCESSFUL!")
                
                # Check what was created
                project_claude_md = project_dir / "CLAUDE.md"
                discovery_json = project_dir / ".cc_automator" / "project_discovery.json"
                
                if project_claude_md.exists():
                    print(f"✅ Generated: {project_claude_md}")
                if discovery_json.exists():
                    print(f"✅ Generated: {discovery_json}")
                    
            else:
                print(f"❌ Process failed with return code: {return_code}")
                
        except Exception as e:
            print(f"❌ Simulation error: {e}")

    def _should_respond(self, output: str) -> bool:
        """Check if the output contains a prompt we should respond to"""
        prompts = [
            "Your project idea:",
            "Choose approach [",
            "Would you like to modify",
            "(y/N):",
            "(Y/n):"
        ]
        return any(prompt in output for prompt in prompts)

    def _get_response_for_prompt(self, output: str) -> str:
        """Get appropriate response based on the prompt in output"""
        
        if "Your project idea:" in output:
            return self.project_intent
            
        elif "Choose approach [" in output:
            # Extract options and use LLM to choose
            return self.get_llm_response(output)
            
        elif "Would you like to modify" in output:
            return "N"
            
        elif "(y/N):" in output or "(Y/n):" in output:
            return "y"
            
        else:
            # Use LLM for any other prompts
            return self.get_llm_response(output)


def main():
    """Test LLM user simulation with different project types"""
    
    API_KEY = "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"
    
    test_cases = [
        ("learning_rec", "learning recommendation system that adapts to student progress"),
        ("doc_chatbot", "chatbot that answers questions about technical documentation"),
        ("research_graphrag", "graphrag system for analyzing research papers"),
    ]
    
    for project_name, project_intent in test_cases:
        simulator = LLMUserSimulator(API_KEY, project_intent)
        simulator.simulate_interaction(project_name)
        
        print(f"\n{'='*60}")
        time.sleep(3)  # Brief pause between tests


if __name__ == "__main__":
    main()