#!/usr/bin/env python3
"""
Session Manager for CC_AUTOMATOR3
Tracks and manages Claude Code session IDs for precise phase management
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


class SessionManager:
    """Manages Claude Code session IDs and their metadata"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.sessions_file = self.project_dir / ".cc_automator" / "sessions.json"
        self.sessions_file.parent.mkdir(parents=True, exist_ok=True)
        self.sessions = self._load_sessions()
        
    def _load_sessions(self) -> Dict[str, Dict]:
        """Load sessions from disk"""
        if self.sessions_file.exists():
            with open(self.sessions_file) as f:
                return json.load(f)
        return {}
        
    def _save_sessions(self):
        """Save sessions to disk"""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)
            
    def add_session(self, phase_name: str, session_id: str, metadata: Optional[Dict] = None):
        """Add or update a session entry"""
        self.sessions[phase_name] = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self._save_sessions()
        
    def get_session(self, phase_name: str) -> Optional[str]:
        """Get session ID for a phase"""
        session_data = self.sessions.get(phase_name)
        return session_data["session_id"] if session_data else None
        
    def get_all_sessions(self) -> Dict[str, str]:
        """Get all phase -> session_id mappings"""
        return {
            phase: data["session_id"] 
            for phase, data in self.sessions.items()
        }
        
    def clear_phase(self, phase_name: str):
        """Clear session for a specific phase"""
        if phase_name in self.sessions:
            del self.sessions[phase_name]
            self._save_sessions()
            
    def clear_all(self):
        """Clear all sessions"""
        self.sessions = {}
        self._save_sessions()
        
    def get_resume_command(self, phase_name: str) -> Optional[List[str]]:
        """Get the Claude command to resume a specific phase"""
        session_id = self.get_session(phase_name)
        if session_id:
            return ["claude", "--resume", session_id]
        return None
        
    def get_phase_history(self, phase_name: str) -> Optional[Dict]:
        """Get full history for a phase including metadata"""
        return self.sessions.get(phase_name)