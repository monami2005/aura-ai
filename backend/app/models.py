from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class CodeAnalyzeRequest(BaseModel):
    language: str = Field(..., description='Programming language of the source code')
    source_code: str = Field(..., description='Source code to analyze')

class CodeAnalyzeResponse(BaseModel):
    detected: bool = Field(..., description='Whether an issue was detected')
    error_type: Optional[str] = Field(None, description='Type of the error, e.g., SyntaxError')
    line_number: Optional[int] = Field(None, description='Line number where the error occurs')
    explanation: Optional[str] = Field(None, description='Explanation of the problem')
    suggested_fix: Optional[str] = Field(None, description='Suggested fix description')
    corrected_code: Optional[str] = Field(None, description='Full corrected source code')

class ChatRequest(BaseModel):
    message: str = Field(..., description='User message or command')
    language: Optional[str] = Field('en', description='Preferred language code')
    session_id: Optional[str] = Field('default', description='Conversation session identifier')

class ChatResponse(BaseModel):
    type: Optional[str] = Field('conversation', description='Interaction type: conversation, question, web_search, clarification, action, communication')
    intent: str = Field(..., description='Detected intent')
    action: Optional[str] = Field(None, description='Allowlisted action name to execute')
    platform: Optional[str] = Field(None, description='Communication platform if applicable')
    params: Dict[str, Any] = Field(default_factory=dict, description='Action parameters')
    explanation: str = Field(..., description='Human-like response or explanation')
    response: Optional[str] = Field(None, description='Natural assistant answer')
    sources: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description='Web Intelligence source citations')
    requires_confirmation: Optional[bool] = Field(False, description='Whether action requires user confirmation')
    executable: bool = Field(False, description='Whether action requires user confirmation/execution')
    risk_level: Optional[str] = Field('SAFE', description='Permission risk level: SAFE, CONFIRM, HIGH_RISK')
    target: Optional[str] = Field(None, description='Action target element, path, or recipient')
    reason: Optional[str] = Field(None, description='Reason why permission or confirmation is required')

class ExecuteRequest(BaseModel):
    original_command: str = Field(..., description='Original user command')
    action: str = Field(..., description='Allowlisted action name')
    params: Dict[str, Any] = Field(default_factory=dict, description='Action parameters')
    detected_intent: Optional[str] = Field(None, description='Detected agent intent')
    language: Optional[str] = Field('en', description='Command language')

class ExecuteResponse(BaseModel):
    success: bool = Field(..., description='Execution status')
    result: Optional[str] = Field(None, description='Execution result message')
    error: Optional[str] = Field(None, description='Error message if execution failed')
    verified: Optional[bool] = Field(True, description='Whether the action was post-verified')
    evidence: Optional[str] = Field(None, description='Verification evidence or observation')

class HistoryItem(BaseModel):
    id: int
    timestamp: str
    original_command: str
    action: str
    result: str
    success: bool
    detected_intent: Optional[str] = None
    planned_action: Optional[str] = None
    confirmation_status: Optional[str] = None
    execution_status: Optional[str] = None
    error: Optional[str] = None
    language: Optional[str] = 'en'

class LanguageDetectRequest(BaseModel):
    text: str = Field(..., description='Text to analyze for language detection')

class LanguageDetectResponse(BaseModel):
    language: str = Field(..., description='Detected ISO language code (en, bn, hi)')
    name: str = Field(..., description='Full language name')

class SpeakRequest(BaseModel):
    text: str = Field(..., description='Text to synthesize to speech')
    language: Optional[str] = Field('en', description='Language code (en, bn, hi)')

class SpeakResponse(BaseModel):
    success: bool = Field(..., description='Whether TTS executed or is available')
    message: str = Field(..., description='Status details or fallback message')
    voice_used: Optional[str] = Field(None, description='Voice identifier used')
