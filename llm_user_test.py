#!/usr/bin/env python3
"""
LLM User Test - Simple test of LLM acting as user in CC_AUTOMATOR4
"""

import openai
import pexpect
import time
from pathlib import Path

API_KEY = "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"

def get_llm_choice(prompt: str, project_intent: str) -> str:
    """Get LLM response for a given prompt"""
    
    openai.api_key = API_KEY
    
    system_prompt = f"""You are a developer using CC_AUTOMATOR4 to build: "{project_intent}"

When the system asks you to choose technology approaches, you should:
1. Prefer OpenAI/GPT options since you have an API key
2. Choose simple/fast options to get started quickly
3. Give concise responses

For questions like "Choose approach [1-3]" respond with just the number.
For "Would you like to modify milestones? (y/N)" respond with just "N".
For the initial question, respond with exactly: "{project_intent}"
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"The system is asking: {prompt}\n\nWhat should I respond? (Be very brief)"}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"🤖 LLM responds: {answer}")
        return answer
        
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        # Fallback
        if "what would you like to build" in prompt.lower():
            return project_intent
        elif "choose approach" in prompt.lower() or "[1-" in prompt:
            return "1"
        elif "modify" in prompt.lower():
            return "N"
        else:
            return "y"

def test_llm_user_interaction():
    """Test LLM acting as user with CC_AUTOMATOR4"""
    
    project_intent = "learning recommendation system that adapts to student progress"
    project_name = "llm_test_learning"
    
    print(f"🤖 Starting LLM User Test")
    print(f"📝 Project Intent: {project_intent}")
    print(f"🔑 Using OpenAI API Key: {API_KEY[:20]}...")
    print("="*60)
    
    # Clean up existing project
    project_dir = Path(project_name)
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)
    
    try:
        # Spawn the CC_AUTOMATOR4 process
        cmd = f"python project_setup_cli.py --project {project_name} --openai-api-key {API_KEY}"
        child = pexpect.spawn(cmd, timeout=60)
        child.logfile_read = open('interaction.log', 'wb')
        
        # Respond to prompts
        responses = [
            (r"Your project idea:", project_intent),
            (r"Choose approach \[1-\d+\]", lambda: get_llm_choice("Choose approach", project_intent)),
            (r"Would you like to modify.*\(y/N\)", "N"),
        ]
        
        while True:
            try:
                # Look for any of our expected prompts
                index = child.expect([pattern for pattern, _ in responses] + [pexpect.EOF, pexpect.TIMEOUT])
                
                if index < len(responses):
                    # We found a matching prompt
                    pattern, response = responses[index]
                    
                    if callable(response):
                        response = response()
                    
                    print(f"📤 Sending: {response}")
                    child.sendline(response)
                    
                elif index == len(responses):  # EOF
                    print("✅ Process completed")
                    break
                    
                elif index == len(responses) + 1:  # TIMEOUT
                    print("⏰ Timeout - process may be waiting for input")
                    # Try to see what's on screen
                    print(f"Current output: {child.before}")
                    break
                    
            except pexpect.EOF:
                print("✅ Process finished")
                break
            except pexpect.TIMEOUT:
                print("⏰ Timeout waiting for prompt")
                print(f"Current output: {child.before}")
                break
        
        child.close()
        
        # Check results
        if child.exitstatus == 0:
            print("✅ LLM USER TEST SUCCESSFUL!")
            
            # Check generated files
            claude_md = project_dir / "CLAUDE.md"
            discovery_json = project_dir / ".cc_automator" / "project_discovery.json"
            
            if claude_md.exists():
                print(f"✅ Generated: {claude_md}")
                # Show first few lines
                with open(claude_md) as f:
                    content = f.read()[:300]
                    print(f"📄 CLAUDE.md preview:\n{content}...")
                    
            if discovery_json.exists():
                print(f"✅ Generated: {discovery_json}")
                
        else:
            print(f"❌ Process failed with exit status: {child.exitstatus}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Show interaction log
        if Path('interaction.log').exists():
            print("\n📋 INTERACTION LOG:")
            with open('interaction.log', 'rb') as f:
                log_content = f.read().decode('utf-8', errors='ignore')
                print(log_content[-500:])  # Last 500 chars

if __name__ == "__main__":
    test_llm_user_interaction()