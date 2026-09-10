from fastapi import APIRouter, HTTPException
import ast
import json
from typing import List
from ..models import (
    CodeAnalyzeRequest,
    CodeAnalyzeResponse,
    ChatRequest,
    ChatResponse,
    ExecuteRequest,
    ExecuteResponse,
    HistoryItem,
    LanguageDetectRequest,
    LanguageDetectResponse,
    SpeakRequest,
    SpeakResponse
)
from ..screen.models import ScreenAnalyzeRequest, ScreenAnalyzeResponse
from ..screen import get_screen_service
from ..assistant.brain import get_brain
from ..actions import execute_safe_action
from ..db import add_action_history, get_action_history
from ..assistant.language_service import detect_language, speak_text, get_supported_languages

from ..agent import get_agent_pipeline

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "service": "aura-ai", "version": "0.8.0", "stage": "Stage 8 - AURA AI Agent Core"}

@router.post("/api/screen/analyze", response_model=ScreenAnalyzeResponse)
def screen_analyze_endpoint(req: ScreenAnalyzeRequest):
    try:
        service = get_screen_service()
        return service.analyze_current_screen(question=req.question, language=req.language or "en")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screen analysis failed: {str(e)}")

@router.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        brain = get_brain()
        data = brain.process(req.message, req.language or "en", req.session_id or "default")
        
        reply_text = data.get("response") or data.get("explanation", "Processed request.")
        
        return ChatResponse(
            type=data.get("type", "conversation"),
            intent=data.get("intent", "chat"),
            action=data.get("action"),
            platform=data.get("platform"),
            params=data.get("params", {}),
            explanation=reply_text,
            response=reply_text,
            sources=data.get("sources", []),
            requires_confirmation=bool(data.get("requires_confirmation", False)),
            executable=bool(data.get("executable", False)),
            risk_level=data.get("risk_level", "SAFE"),
            target=data.get("target"),
            reason=data.get("reason")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

@router.post("/api/execute", response_model=ExecuteResponse)
def execute_endpoint(req: ExecuteRequest):
    try:
        pipeline = get_agent_pipeline()
        res = pipeline.execute_confirmed_action(
            original_command=req.original_command,
            action=req.action,
            params=req.params,
            language=req.language or "en"
        )
        return ExecuteResponse(
            success=res.get("success", False),
            result=res.get("result"),
            error=res.get("error"),
            verified=res.get("verified", True),
            evidence=res.get("evidence")
        )
    except Exception as e:
        return ExecuteResponse(
            success=False,
            error=f"Execution failed: {str(e)}",
            verified=False,
            evidence="Exception raised during action dispatch."
        )

@router.get("/api/history", response_model=List[HistoryItem])
def history_endpoint():
    try:
        return get_action_history(limit=50)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

@router.post("/api/language/detect", response_model=LanguageDetectResponse)
def detect_language_endpoint(req: LanguageDetectRequest):
    try:
        res = detect_language(req.text)
        return LanguageDetectResponse(
            language=res["language"],
            name=res["name"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection error: {str(e)}")

@router.post("/api/speak", response_model=SpeakResponse)
def speak_endpoint(req: SpeakRequest):
    try:
        res = speak_text(req.text, req.language or "en")
        return SpeakResponse(
            success=res["success"],
            message=res["message"],
            voice_used=res.get("voice_used")
        )
    except Exception as e:
        return SpeakResponse(
            success=False,
            message=f"TTS error: {str(e)}",
            voice_used=None
        )

@router.post("/api/code/analyze", response_model=CodeAnalyzeResponse)
def analyze_code(req: CodeAnalyzeRequest):
    lang = req.language.lower().strip()
    code = req.source_code

    if lang == "python":
        try:
            ast.parse(code)
            return CodeAnalyzeResponse(
                detected=False,
                error_type=None,
                line_number=None,
                explanation="No syntax errors found. Python code parsed successfully into AST.",
                suggested_fix=None,
                corrected_code=code
            )
        except SyntaxError as e:
            line_no = e.lineno or 1
            explanation = f"Syntax error on line {line_no}: {e.msg}"
            
            corrected = code
            suggested_fix = f"Fix syntax error: {e.msg}"
            
            if "(" in code and not code.strip().endswith(")"):
                corrected = code + ")"
                suggested_fix = "Add the missing closing parenthesis ')' at the end of the statement."
            elif ":" not in code and ("def " in code or "if " in code or "for " in code or "while " in code):
                suggested_fix = "Add a colon ':' at the end of the header line."
                
            return CodeAnalyzeResponse(
                detected=True,
                error_type="SyntaxError",
                line_number=line_no,
                explanation=explanation,
                suggested_fix=suggested_fix,
                corrected_code=corrected
            )
            
    elif lang == "json":
        try:
            json.loads(code)
            return CodeAnalyzeResponse(
                detected=False,
                error_type=None,
                line_number=None,
                explanation="Valid JSON structure.",
                suggested_fix=None,
                corrected_code=code
            )
        except json.JSONDecodeError as e:
            return CodeAnalyzeResponse(
                detected=True,
                error_type="JSONDecodeError",
                line_number=e.lineno,
                explanation=f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}",
                suggested_fix="Ensure all keys and strings are enclosed in double quotes and commas are placed correctly.",
                corrected_code=code
            )
            
    elif lang in ("javascript", "typescript"):
        pairs = {'(': ')', '{': '}', '[': ']'}
        stack = []
        for i, ch in enumerate(code):
            if ch in pairs:
                stack.append((ch, i))
            elif ch in pairs.values():
                if not stack or pairs[stack.pop()[0]] != ch:
                    return CodeAnalyzeResponse(
                        detected=True,
                        error_type="SyntaxError",
                        line_number=1,
                        explanation=f"Unmatched closing delimiter '{ch}'.",
                        suggested_fix="Check that all braces, brackets, and parentheses are properly paired.",
                        corrected_code=code
                    )
        if stack:
            unclosed, _ = stack[-1]
            return CodeAnalyzeResponse(
                detected=True,
                error_type="SyntaxError",
                line_number=1,
                explanation=f"Unclosed opening delimiter '{unclosed}'.",
                suggested_fix=f"Add closing delimiter '{pairs[unclosed]}'.",
                corrected_code=code + pairs[unclosed]
            )
            
        return CodeAnalyzeResponse(
            detected=False,
            error_type=None,
            line_number=None,
            explanation=f"Basic syntax and delimiter checks passed for {req.language}.",
            suggested_fix=None,
            corrected_code=code
        )
        
    else:
        return CodeAnalyzeResponse(
            detected=False,
            error_type=None,
            line_number=None,
            explanation=f"Analysis completed for {req.language}.",
            suggested_fix=None,
            corrected_code=code
        )
