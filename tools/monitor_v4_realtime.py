#!/usr/bin/env python3
"""
Real-time V4 monitoring tool for enhanced visibility during execution.
Shows V4 decisions, strategy changes, failure patterns, and learning in real-time.
"""

import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import curses
from collections import defaultdict
import argparse

class V4Monitor:
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.cc_dir = project_path / '.cc_automator'
        self.failure_history_path = self.cc_dir / 'v4_failure_history.json'
        self.strategy_perf_path = self.cc_dir / 'v4_strategy_performance.json'
        self.logs_dir = self.cc_dir / 'logs'
        # Also monitor automated testing logs
        self.automated_test_dir = Path('logs/automated_v4_testing')
        
        # State tracking
        self.current_phase = "Not started"
        self.current_strategy = "Unknown"
        self.failure_counts = defaultdict(int)
        self.phase_attempts = defaultdict(int)
        self.strategies_used = []
        self.learning_events = []
        
    def load_failure_history(self):
        """Load and analyze failure history."""
        if self.failure_history_path.exists():
            try:
                with open(self.failure_history_path) as f:
                    data = json.load(f)
                    failures = data.get('failures', [])
                    
                    # Update failure counts
                    self.failure_counts.clear()
                    self.phase_attempts.clear()
                    
                    for failure in failures:
                        phase = failure.get('phase_name', 'unknown')
                        self.failure_counts[phase] += 1
                        attempt = failure.get('attempt_num', 0)
                        self.phase_attempts[phase] = max(self.phase_attempts[phase], attempt)
                        
                    return failures
            except:
                pass
        return []
    
    def load_strategy_performance(self):
        """Load strategy performance data."""
        if self.strategy_perf_path.exists():
            try:
                with open(self.strategy_perf_path) as f:
                    data = json.load(f)
                    return data.get('performances', [])
            except:
                pass
        return []
    
    def scan_latest_logs(self):
        """Scan logs for V4-specific events."""
        if not self.logs_dir.exists():
            return []
        
        events = []
        log_files = sorted(self.logs_dir.glob('*.log'), key=lambda p: p.stat().st_mtime)
        
        if log_files:
            latest_log = log_files[-1]
            try:
                with open(latest_log) as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    
                    for line in lines:
                        # Detect V4 events
                        if "Strategy Selection:" in line:
                            self.current_strategy = line.split("Strategy Selection:")[-1].strip()
                            events.append(("STRATEGY", self.current_strategy))
                        
                        elif "Failure Analysis:" in line:
                            events.append(("FAILURE", line.strip()))
                        
                        elif "Infinite loop detected" in line:
                            events.append(("LOOP", line.strip()))
                        
                        elif "Switching from" in line and "to" in line:
                            events.append(("SWITCH", line.strip()))
                        
                        elif "Context Analysis:" in line:
                            events.append(("CONTEXT", line.strip()))
                        
                        elif "Starting phase:" in line:
                            phase = line.split("Starting phase:")[-1].strip()
                            self.current_phase = phase
                            events.append(("PHASE", phase))
            except:
                pass
        
        return events
    
    def draw_dashboard(self, stdscr):
        """Draw the monitoring dashboard."""
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(1)   # Non-blocking input
        
        # Color pairs
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # Header
            header = "🤖 CC_AUTOMATOR4 V4 Real-Time Monitor"
            stdscr.addstr(0, (width - len(header)) // 2, header, curses.A_BOLD)
            stdscr.addstr(1, 0, "=" * width)
            
            row = 3
            
            # Current Status
            stdscr.addstr(row, 0, "📊 Current Status", curses.A_BOLD | curses.color_pair(4))
            row += 1
            stdscr.addstr(row, 2, f"Phase: {self.current_phase}")
            row += 1
            stdscr.addstr(row, 2, f"Strategy: {self.current_strategy}")
            row += 2
            
            # Failure Analysis
            failures = self.load_failure_history()
            stdscr.addstr(row, 0, "❌ Failure Patterns", curses.A_BOLD | curses.color_pair(2))
            row += 1
            
            if self.failure_counts:
                for phase, count in sorted(self.failure_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    attempts = self.phase_attempts.get(phase, 0)
                    color = curses.color_pair(2) if count > 3 else curses.color_pair(3)
                    stdscr.addstr(row, 2, f"{phase}: {count} failures, {attempts} attempts", color)
                    row += 1
            else:
                stdscr.addstr(row, 2, "No failures yet", curses.color_pair(1))
                row += 1
            row += 1
            
            # Strategy Performance
            perfs = self.load_strategy_performance()
            stdscr.addstr(row, 0, "📈 Strategy Performance", curses.A_BOLD | curses.color_pair(5))
            row += 1
            
            if perfs:
                strategy_stats = defaultdict(lambda: {'count': 0, 'quality': []})
                for perf in perfs:
                    strategy = perf.get('strategy', 'unknown')
                    quality = perf.get('evidence_quality', 0)
                    strategy_stats[strategy]['count'] += 1
                    strategy_stats[strategy]['quality'].append(quality)
                
                for strategy, stats in strategy_stats.items():
                    avg_quality = sum(stats['quality']) / len(stats['quality']) if stats['quality'] else 0
                    stdscr.addstr(row, 2, f"{strategy}: {stats['count']} runs, avg quality: {avg_quality:.2f}")
                    row += 1
            else:
                stdscr.addstr(row, 2, "No strategy data yet")
                row += 1
            row += 1
            
            # Recent Events
            events = self.scan_latest_logs()
            stdscr.addstr(row, 0, "📡 Recent V4 Events", curses.A_BOLD | curses.color_pair(4))
            row += 1
            
            event_colors = {
                'STRATEGY': curses.color_pair(5),
                'FAILURE': curses.color_pair(2),
                'LOOP': curses.color_pair(2) | curses.A_BOLD,
                'SWITCH': curses.color_pair(3),
                'CONTEXT': curses.color_pair(4),
                'PHASE': curses.color_pair(1)
            }
            
            for event_type, event_msg in events[-10:]:
                if row < height - 3:
                    color = event_colors.get(event_type, 0)
                    prefix = {
                        'STRATEGY': '🎯',
                        'FAILURE': '❌',
                        'LOOP': '🔄',
                        'SWITCH': '🔀',
                        'CONTEXT': '🔍',
                        'PHASE': '▶️'
                    }.get(event_type, '•')
                    
                    msg = f"{prefix} {event_msg[:width-5]}"
                    stdscr.addstr(row, 2, msg, color)
                    row += 1
            
            # Footer
            footer = "Press 'q' to quit | Updates every 2 seconds"
            stdscr.addstr(height - 1, (width - len(footer)) // 2, footer, curses.A_DIM)
            
            stdscr.refresh()
            
            # Check for quit
            key = stdscr.getch()
            if key == ord('q'):
                break
            
            time.sleep(2)
    
    def run_simple_monitor(self):
        """Run simple text-based monitoring (fallback)."""
        print("🤖 CC_AUTOMATOR4 V4 Monitor (Simple Mode)")
        print("=" * 60)
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("🤖 CC_AUTOMATOR4 V4 Monitor")
                print("=" * 60)
                print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
                print()
                
                # Load data
                failures = self.load_failure_history()
                perfs = self.load_strategy_performance()
                
                # Show current status
                print("📊 Current Status:")
                print(f"  Phase: {self.current_phase}")
                print(f"  Strategy: {self.current_strategy}")
                print()
                
                # Show failures
                print("❌ Failure Summary:")
                if self.failure_counts:
                    for phase, count in sorted(self.failure_counts.items(), 
                                              key=lambda x: x[1], reverse=True)[:5]:
                        print(f"  {phase}: {count} failures")
                else:
                    print("  No failures yet")
                print()
                
                # Show strategy performance
                print("📈 Strategy Usage:")
                if perfs:
                    strategy_counts = defaultdict(int)
                    for perf in perfs:
                        strategy_counts[perf.get('strategy', 'unknown')] += 1
                    
                    for strategy, count in strategy_counts.items():
                        print(f"  {strategy}: {count} executions")
                else:
                    print("  No strategy data yet")
                print()
                
                # Recent events
                events = self.scan_latest_logs()
                if events:
                    print("📡 Recent Events:")
                    for event_type, msg in events[-5:]:
                        print(f"  [{event_type}] {msg[:80]}")
                
                print("\nPress Ctrl+C to quit")
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")


def main():
    parser = argparse.ArgumentParser(description="V4 Real-time Monitor")
    parser.add_argument("--project", type=str, default=".", 
                       help="Project directory to monitor")
    parser.add_argument("--simple", action="store_true",
                       help="Use simple text mode instead of curses")
    
    args = parser.parse_args()
    
    project_path = Path(args.project).resolve()
    monitor = V4Monitor(project_path)
    
    if args.simple:
        monitor.run_simple_monitor()
    else:
        try:
            curses.wrapper(monitor.draw_dashboard)
        except:
            print("Curses mode failed, falling back to simple mode...")
            monitor.run_simple_monitor()


if __name__ == "__main__":
    main()