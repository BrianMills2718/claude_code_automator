#!/usr/bin/env python3
"""
Enhanced SDK diagnostics with comprehensive logging and tracing
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('sdk_diagnostics.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Enhanced wrapper with logging
class SDKMessageTracer:
    """Trace all SDK messages for debugging"""
    
    def __init__(self):
        self.messages = []
        self.errors = []
        self.stats = {
            'total_messages': 0,
            'message_types': {},
            'errors': 0,
            'cost_fields_seen': set(),
            'result_messages': []
        }
    
    def trace_message(self, message: Any) -> None:
        """Trace a message with full inspection"""
        self.stats['total_messages'] += 1
        
        msg_info = {
            'index': self.stats['total_messages'],
            'timestamp': datetime.now().isoformat(),
            'type': type(message).__name__,
            'has_dict': hasattr(message, '__dict__')
        }
        
        # Track message type
        msg_type = type(message).__name__
        self.stats['message_types'][msg_type] = self.stats['message_types'].get(msg_type, 0) + 1
        
        # Inspect attributes
        if hasattr(message, '__dict__'):
            attrs = message.__dict__
            msg_info['attributes'] = list(attrs.keys())
            
            # Look for cost-related fields
            for key in attrs.keys():
                if 'cost' in key.lower():
                    self.stats['cost_fields_seen'].add(key)
                    msg_info[f'field_{key}'] = getattr(message, key, None)
            
            # Special handling for result messages
            if hasattr(message, 'subtype'):
                msg_info['subtype'] = message.subtype
                if message.subtype in ['success', 'error_max_turns', 'error_during_execution']:
                    result_info = {
                        'subtype': message.subtype,
                        'has_cost_usd': hasattr(message, 'cost_usd'),
                        'has_total_cost_usd': hasattr(message, 'total_cost_usd'),
                        'cost_usd': getattr(message, 'cost_usd', None),
                        'total_cost_usd': getattr(message, 'total_cost_usd', None),
                        'duration_ms': getattr(message, 'duration_ms', None),
                        'is_error': getattr(message, 'is_error', None)
                    }
                    self.stats['result_messages'].append(result_info)
                    msg_info['result_details'] = result_info
        
        self.messages.append(msg_info)
        logger.debug(f"Message {self.stats['total_messages']}: {json.dumps(msg_info, indent=2)}")
    
    def trace_error(self, error: Exception) -> None:
        """Trace an error with context"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'is_cost_error': 'cost_usd' in str(error),
            'messages_before_error': self.stats['total_messages']
        }
        
        self.errors.append(error_info)
        self.stats['errors'] += 1
        
        logger.error(f"Error traced: {json.dumps(error_info, indent=2)}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of traced data"""
        return {
            'stats': self.stats,
            'errors': self.errors,
            'cost_fields_found': list(self.stats['cost_fields_seen']),
            'message_type_counts': self.stats['message_types'],
            'result_message_count': len(self.stats['result_messages']),
            'first_error': self.errors[0] if self.errors else None,
            'last_message': self.messages[-1] if self.messages else None
        }

# Test with enhanced diagnostics
async def test_with_diagnostics():
    """Run SDK test with comprehensive diagnostics"""
    
    # Use the fixed wrapper
    from claude_code_sdk_fixed import query, ClaudeCodeOptions
    
    tracer = SDKMessageTracer()
    
    logger.info("=" * 80)
    logger.info("ENHANCED SDK DIAGNOSTICS TEST")
    logger.info("=" * 80)
    
    # Simple test prompt
    test_prompt = "Create diagnostics.txt with 'Testing SDK diagnostics' content."
    
    options = ClaudeCodeOptions(
        max_turns=3,
        allowed_tools=["Write", "Read"],
        permission_mode="bypassPermissions",
        cwd=str(Path.cwd())
    )
    
    logger.info(f"Test prompt: {test_prompt}")
    logger.info(f"Options: max_turns={options.max_turns}, tools={options.allowed_tools}")
    
    try:
        async for message in query(prompt=test_prompt, options=options):
            tracer.trace_message(message)
            
            # Extra logging for specific message types
            if hasattr(message, 'content'):
                logger.info(f"Content message: {type(message).__name__}")
            elif hasattr(message, 'subtype'):
                logger.info(f"Subtype message: {message.subtype}")
        
        logger.info("✅ Query completed successfully")
        
    except Exception as e:
        tracer.trace_error(e)
        logger.error(f"❌ Query failed: {type(e).__name__}: {str(e)}")
        
        # Additional error analysis
        if "cost_usd" in str(e):
            logger.error("🎯 This is the cost_usd parsing error!")
            logger.error(f"Error occurred after {tracer.stats['total_messages']} messages")
            
            # Try to identify the problematic message
            if tracer.messages:
                last_msg = tracer.messages[-1]
                logger.error(f"Last message before error: {json.dumps(last_msg, indent=2)}")
    
    # Generate comprehensive report
    summary = tracer.get_summary()
    
    logger.info("\n" + "=" * 80)
    logger.info("DIAGNOSTICS SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total messages: {summary['stats']['total_messages']}")
    logger.info(f"Message types: {summary['message_type_counts']}")
    logger.info(f"Cost fields seen: {summary['cost_fields_found']}")
    logger.info(f"Result messages: {summary['result_message_count']}")
    logger.info(f"Errors: {summary['stats']['errors']}")
    
    if summary['result_message_count'] > 0:
        logger.info("\nResult message details:")
        for i, result in enumerate(summary['stats']['result_messages']):
            logger.info(f"  Result {i+1}: {json.dumps(result, indent=4)}")
    
    # Save full diagnostics
    with open('sdk_diagnostics_report.json', 'w') as f:
        json.dump({
            'test_prompt': test_prompt,
            'options': {
                'max_turns': options.max_turns,
                'allowed_tools': options.allowed_tools
            },
            'summary': summary,
            'all_messages': tracer.messages,
            'all_errors': tracer.errors
        }, f, indent=2)
    
    logger.info(f"\n📝 Full diagnostics saved to: sdk_diagnostics_report.json")
    
    return summary

if __name__ == "__main__":
    # Run the diagnostic test
    summary = asyncio.run(test_with_diagnostics())
    
    # Exit with appropriate code
    sys.exit(0 if summary['stats']['errors'] == 0 else 1)