#!/usr/bin/env python3
"""
Output Filter for CC_AUTOMATOR3
Filters Claude's output to show only human-relevant information
"""

import re
from typing import Optional, List, Tuple


class OutputFilter:
    """Filters and formats output for human consumption"""
    
    # Patterns to filter out (agent instructions)
    FILTER_PATTERNS = [
        r"## Evidence Requirements.*?Show, don't tell.*?claims\.\*\*",
        r"You MUST provide clear evidence.*?claims\.\*\*", 
        r"Remember: \"Show, don't tell\".*?not just claims\.\*\*",
        r"When done, create file:.*?PHASE_COMPLETE",
        r"Write to it: PHASE_COMPLETE.*?--allowedTools.*",
    ]
    
    # Patterns that indicate progress
    PROGRESS_PATTERNS = [
        (r"Creating\s+([\w/\.]+)", "📝 Creating {0}"),
        (r"Writing\s+([\w/\.]+)", "✏️  Writing {0}"),
        (r"Running:\s*(.+)", "🏃 Running: {0}"),
        (r"Found\s+(\d+)\s+errors?\s+in\s+([\w/\.]+)", "🔍 Found {0} errors in {1}"),
        (r"Fixing\s+(.*)", "🔧 Fixing {0}"),
        (r"All tests pass", "✅ All tests pass"),
        (r"Success: no issues found", "✅ No issues found"),
        (r"Created\s+([\w/\.]+)", "✅ Created {0}"),
        (r"Fixed\s+(\d+)\s+issues?", "✅ Fixed {0} issues"),
        (r"Implemented\s+(.*)", "✅ Implemented {0}"),
    ]
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.compiled_filters = [
            re.compile(pattern, re.DOTALL | re.MULTILINE) 
            for pattern in self.FILTER_PATTERNS
        ]
        self.compiled_progress = [
            (re.compile(pattern), template) 
            for pattern, template in self.PROGRESS_PATTERNS
        ]
    
    def filter_output(self, text: str) -> str:
        """Filter output for human consumption"""
        if self.verbose:
            return text
            
        # Remove agent instructions
        filtered = text
        for pattern in self.compiled_filters:
            filtered = pattern.sub("", filtered)
        
        # Clean up extra whitespace
        filtered = re.sub(r'\n{3,}', '\n\n', filtered)
        
        return filtered.strip()
    
    def extract_progress(self, text: str) -> List[str]:
        """Extract progress indicators from output"""
        progress_items = []
        
        for pattern, template in self.compiled_progress:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    progress_items.append(template.format(*match))
                else:
                    progress_items.append(template.format(match))
        
        return progress_items
    
    def format_phase_output(self, phase_name: str, output: str) -> str:
        """Format output for a specific phase"""
        filtered = self.filter_output(output)
        progress = self.extract_progress(output)
        
        if progress and not self.verbose:
            # Show progress items instead of full output
            return "\n".join(progress)
        else:
            return filtered
    
    def should_show_line(self, line: str) -> bool:
        """Check if a line should be shown in streaming output"""
        # Skip empty lines
        if not line.strip():
            return False
            
        # Skip known verbose patterns
        verbose_starts = [
            "Phase ", "Starting async execution",
            "Completion marker:", "Command: claude -p",
            "Allowed Tools:", "Max Turns:", "Timeout:",
            "Think Mode:", "Description:"
        ]
        
        for start in verbose_starts:
            if line.strip().startswith(start):
                return self.verbose
                
        return True