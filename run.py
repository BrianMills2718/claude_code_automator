#!/usr/bin/env python3
"""
Legacy entry point for CC_AUTOMATOR3
Redirects to the new CLI module
"""

import sys
from cli import main

if __name__ == "__main__":
    # Maintain backwards compatibility
    sys.exit(main())