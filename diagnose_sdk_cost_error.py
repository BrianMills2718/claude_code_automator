#!/usr/bin/env python3
"""
Diagnose Claude Code SDK cost_usd parsing error
Capture and analyze the exact message structure causing the KeyError
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from claude_code_sdk import query, ClaudeCodeOptions, Message

async def diagnose_sdk_error():
    """Run a simple query and capture all messages to identify cost_usd error"""
    
    print("=" * 80)
    print("Claude Code SDK Cost Error Diagnosis")
    print("=" * 80)
    print()
    
    # Simple test prompt
    test_prompt = """Create a simple hello.txt file with the content 'Hello World'.
Then read it back to confirm it was created."""
    
    # Minimal options
    options = ClaudeCodeOptions(
        max_turns=5,
        allowed_tools=["Write", "Read"],
        permission_mode="bypassPermissions",
        cwd=str(Path.cwd())
    )
    
    messages_log = []
    error_details = None
    
    print("Starting SDK query...")
    print(f"Working directory: {Path.cwd()}")
    print()
    
    try:
        message_count = 0
        async for message in query(prompt=test_prompt, options=options):
            message_count += 1
            
            # Create detailed log entry
            log_entry = {
                "index": message_count,
                "timestamp": datetime.now().isoformat(),
                "type": type(message).__name__,
                "has_dict": hasattr(message, '__dict__'),
            }
            
            # Safely extract all attributes
            if hasattr(message, '__dict__'):
                try:
                    log_entry["attributes"] = list(message.__dict__.keys())
                    log_entry["raw_dict"] = {}
                    
                    # Safely extract each attribute
                    for key in message.__dict__.keys():
                        try:
                            value = getattr(message, key)
                            # Convert to JSON-serializable format
                            if hasattr(value, '__dict__'):
                                log_entry["raw_dict"][key] = {
                                    "type": type(value).__name__,
                                    "attrs": list(value.__dict__.keys()) if hasattr(value, '__dict__') else "no_dict"
                                }
                            elif isinstance(value, (str, int, float, bool, type(None))):
                                log_entry["raw_dict"][key] = value
                            elif isinstance(value, (list, tuple)):
                                log_entry["raw_dict"][key] = f"[{type(value).__name__} with {len(value)} items]"
                            elif isinstance(value, dict):
                                log_entry["raw_dict"][key] = {k: type(v).__name__ for k, v in value.items()}
                            else:
                                log_entry["raw_dict"][key] = f"<{type(value).__name__}>"
                        except Exception as e:
                            log_entry["raw_dict"][key] = f"ERROR: {str(e)}"
                except Exception as e:
                    log_entry["dict_error"] = str(e)
            
            # Try converting to dict
            try:
                if isinstance(message, dict):
                    log_entry["as_dict"] = message
                elif hasattr(message, '__dict__'):
                    log_entry["as_dict"] = message.__dict__
                else:
                    log_entry["as_dict"] = "no_dict_conversion"
            except Exception as e:
                log_entry["dict_conversion_error"] = str(e)
            
            # Check for specific fields
            for field in ['type', 'subtype', 'cost_usd', 'total_cost_usd', 'is_error', 'result']:
                try:
                    if hasattr(message, field):
                        log_entry[f"has_{field}"] = True
                        log_entry[f"{field}_value"] = getattr(message, field)
                    elif isinstance(message, dict) and field in message:
                        log_entry[f"has_{field}_in_dict"] = True
                        log_entry[f"{field}_value"] = message[field]
                except Exception as e:
                    log_entry[f"{field}_access_error"] = str(e)
            
            messages_log.append(log_entry)
            
            # Print summary
            print(f"Message {message_count}: {log_entry.get('type', 'unknown')}")
            if 'attributes' in log_entry:
                print(f"  Attributes: {', '.join(log_entry['attributes'])}")
            if any(key.startswith('has_') for key in log_entry):
                found_fields = [key[4:] for key in log_entry if key.startswith('has_') and log_entry[key]]
                if found_fields:
                    print(f"  Found fields: {', '.join(found_fields)}")
            
    except Exception as e:
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
            "messages_received": len(messages_log)
        }
        
        print(f"\n❌ Error occurred: {type(e).__name__}: {str(e)}")
        print(f"Messages received before error: {len(messages_log)}")
        
        # Check if it's the cost_usd error
        if "cost_usd" in str(e) or "KeyError" in str(e):
            print("\n🎯 Found cost_usd error!")
            print("Analyzing last message before error...")
            
            if messages_log:
                last_msg = messages_log[-1]
                print(f"\nLast message type: {last_msg.get('type', 'unknown')}")
                print(f"Last message attributes: {last_msg.get('attributes', [])}")
                print(f"Last message raw_dict keys: {list(last_msg.get('raw_dict', {}).keys())}")
    
    # Save detailed log
    log_file = Path("sdk_cost_error_diagnosis.json")
    diagnosis = {
        "test_prompt": test_prompt,
        "options": {
            "max_turns": options.max_turns,
            "allowed_tools": options.allowed_tools,
            "permission_mode": options.permission_mode,
            "cwd": options.cwd
        },
        "messages": messages_log,
        "error": error_details,
        "summary": {
            "total_messages": len(messages_log),
            "message_types": list(set(msg.get('type', 'unknown') for msg in messages_log)),
            "fields_found": list(set(
                key[4:] for msg in messages_log 
                for key in msg 
                if key.startswith('has_') and msg[key]
            ))
        }
    }
    
    with open(log_file, 'w') as f:
        json.dump(diagnosis, f, indent=2)
    
    print(f"\n📝 Detailed diagnosis saved to: {log_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("DIAGNOSIS SUMMARY")
    print("=" * 80)
    print(f"Total messages processed: {len(messages_log)}")
    print(f"Message types seen: {', '.join(diagnosis['summary']['message_types'])}")
    print(f"Fields found: {', '.join(diagnosis['summary']['fields_found'])}")
    
    if error_details:
        print(f"\nError type: {error_details['error_type']}")
        print(f"Error message: {error_details['error_message']}")
        
        if "cost_usd" in error_details['error_message']:
            print("\n⚠️  This is the cost_usd parsing error!")
            print("The SDK is trying to access a 'cost_usd' field that doesn't exist.")
            print("This appears to be a bug in the SDK's message parsing logic.")

if __name__ == "__main__":
    asyncio.run(diagnose_sdk_error())