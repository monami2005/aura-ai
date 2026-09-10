from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ActionRiskLevel(str, Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    HIGH_RISK = "HIGH_RISK"

class AgentIntent(str, Enum):
    CHAT = "CHAT"
    OPEN_APPLICATION = "OPEN_APPLICATION"
    OPEN_WEBSITE = "OPEN_WEBSITE"
    WEB_SEARCH = "WEB_SEARCH"
    SCREENSHOT = "SCREENSHOT"
    ANALYZE_SCREEN = "ANALYZE_SCREEN"
    ANALYZE_ERROR = "ANALYZE_ERROR"
    CLICK = "CLICK"
    TYPE = "TYPE"
    PRESS_KEY = "PRESS_KEY"
    SCROLL = "SCROLL"
    CREATE_FOLDER = "CREATE_FOLDER"
    LIST_FILES = "LIST_FILES"
    FIND_FILE = "FIND_FILE"
    READ_FILE = "READ_FILE"
    SUMMARIZE_FILE = "SUMMARIZE_FILE"
    RENAME_FILE = "RENAME_FILE"
    MOVE_FILE = "MOVE_FILE"
    DELETE_FILE = "DELETE_FILE"
    EXPLAIN_ERROR = "EXPLAIN_ERROR"
    HELP_WITH_CODE = "HELP_WITH_CODE"
    CALL_CONTACT = "CALL_CONTACT"
    SEND_MESSAGE = "SEND_MESSAGE"
    UNKNOWN = "UNKNOWN"

class PlannedAction(BaseModel):
    intent: AgentIntent
    action_name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    risk_level: ActionRiskLevel = ActionRiskLevel.SAFE
    reason: str
    target: str
    requires_confirmation: bool = False
    executable: bool = True
    response: str
    explanation: Optional[str] = None

class ActionVerificationResult(BaseModel):
    verified: bool
    evidence: str
    error: Optional[str] = None
