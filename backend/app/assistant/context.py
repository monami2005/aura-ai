import time
from typing import Dict, Any, Optional, List

class ConversationContext:
    def __init__(self, session_id: str = "default", ttl_seconds: int = 120):
        self.session_id = session_id
        self.ttl_seconds = ttl_seconds
        self.history: List[Dict[str, str]] = []
        self.last_topic: Optional[str] = None
        self.pending_action: Optional[Dict[str, Any]] = None
        self.pending_action_time: float = 0.0
        self.last_proposed_fix: Optional[Dict[str, Any]] = None
        self.last_error_context: Optional[Dict[str, Any]] = None

    def add_turn(self, user_msg: str, assistant_msg: str, topic: Optional[str] = None):
        self.history.append({"user": user_msg, "assistant": assistant_msg})
        if len(self.history) > 10:
            self.history.pop(0)
        if topic:
            self.last_topic = topic

    def set_proposed_fix(self, fix_dict: Dict[str, Any]):
        self.last_proposed_fix = fix_dict

    def get_proposed_fix(self) -> Optional[Dict[str, Any]]:
        return self.last_proposed_fix

    def clear_proposed_fix(self):
        self.last_proposed_fix = None

    def set_error_context(self, error_dict: Dict[str, Any]):
        self.last_error_context = error_dict

    def get_error_context(self) -> Optional[Dict[str, Any]]:
        return self.last_error_context

    def set_pending_action(self, action_dict: Dict[str, Any]):
        self.pending_action = action_dict
        self.pending_action_time = time.time()

    def get_valid_pending_action(self) -> Optional[Dict[str, Any]]:
        if not self.pending_action:
            return None
        # Check for expiration (stale confirmation guard)
        if time.time() - self.pending_action_time > self.ttl_seconds:
            self.pending_action = None
            return None
        return self.pending_action

    def clear_pending_action(self):
        self.pending_action = None
        self.pending_action_time = 0.0

    def get_recent_context_summary(self) -> str:
        if not self.history:
            return ""
        turns = [f"User: {t['user']}\nAssistant: {t['assistant']}" for t in self.history[-3:]]
        return "\n".join(turns)


# Global in-memory session manager
_sessions: Dict[str, ConversationContext] = {}

def get_context(session_id: str = "default") -> ConversationContext:
    if session_id not in _sessions:
        _sessions[session_id] = ConversationContext(session_id)
    return _sessions[session_id]
