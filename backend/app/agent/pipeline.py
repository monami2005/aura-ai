import re
from typing import Dict, Any, Optional
from .models import AgentIntent, ActionRiskLevel, PlannedAction
from .permissions import PermissionManager
from .intents import detect_structured_intent
from .verifier import verify_action_execution
from .file_manager import (
    safe_create_folder, safe_find_file, safe_read_file, safe_summarize_file,
    safe_rename_file, safe_move_file, safe_delete_file
)
from .browser import safe_open_url, safe_browser_search, safe_launch_browser
from .coding_assistant import analyze_code_or_error
from ..actions import execute_safe_action, SAFE_ACTIONS
from ..db import add_action_history
from ..assistant.context import get_context
from ..screen import get_screen_service
from ..web import get_web_service

class AuraAgentPipeline:
    """
    Unified Agent Pipeline for AURA AI.
    
    Flow:
    User Input
    → Intent Detection
    → Action Planning
    → Safety Check
    → Permission Check
    → User Confirmation (if required)
    → Action Execution
    → Result Verification
    → Response
    → History Logging
    """

    def process(self, user_input: str, language: str = "en", session_id: str = "default") -> Dict[str, Any]:
        context = get_context(session_id)
        msg_clean = user_input.strip()
        screen_service = get_screen_service()
        web_service = get_web_service()

        # Step 1: Intent Detection
        intent, params = detect_structured_intent(msg_clean, language)

        # Step 2 & 3: Action Planning & Safety Mapping
        # 2a. Screen Error & Visual Analysis
        if intent in (AgentIntent.ANALYZE_ERROR, AgentIntent.ANALYZE_SCREEN):
            screen_res = screen_service.analyze_current_screen(question=msg_clean, language=language)
            context.add_turn(msg_clean, screen_res.summary, topic="screen_analysis")

            # Cautious diagnostic wording for error queries
            if intent == AgentIntent.ANALYZE_ERROR:
                cautious_summary = f"Visual Error Diagnostic: This appears to be related to visible application state. {screen_res.summary}"
            else:
                cautious_summary = screen_res.summary

            # Auto-log read-only operation
            add_action_history(
                original_command=msg_clean,
                action="analyze_screen",
                result=cautious_summary[:100],
                success=screen_res.success,
                detected_intent=intent.value,
                planned_action="analyze_screen",
                confirmation_status="auto_allowed",
                execution_status="completed" if screen_res.success else "failed",
                language=language
            )

            return {
                "type": "screen_analysis",
                "intent": intent.value,
                "platform": None,
                "params": params,
                "risk_level": ActionRiskLevel.SAFE.value,
                "target": "active screen",
                "reason": "Passive visual screen analysis is read-only.",
                "sources": [],
                "requires_confirmation": False,
                "response": cautious_summary,
                "executable": False
            }

        # 2b. Coding Assistant Diagnostics
        if intent == AgentIntent.HELP_WITH_CODE:
            code_res = analyze_code_or_error(msg_clean, None, language)
            context.add_turn(msg_clean, code_res["response"], topic="coding_help")
            return {
                "type": "question",
                "intent": intent.value,
                "platform": None,
                "params": params,
                "risk_level": ActionRiskLevel.SAFE.value,
                "target": "code diagnostics",
                "reason": "Static code diagnostics are read-only and do not execute code.",
                "sources": [],
                "requires_confirmation": False,
                "response": code_res["response"],
                "executable": False
            }

        # 2c. Passive File Operations (Read, Find, Summarize)
        if intent == AgentIntent.FIND_FILE:
            file_res = safe_find_file(params.get("filename", "notes.txt"))
            context.add_turn(msg_clean, file_res.get("result", ""), topic="file_search")
            add_action_history(
                original_command=msg_clean,
                action="find_file",
                result=file_res.get("result", "")[:100],
                success=file_res.get("success", False),
                detected_intent=intent.value,
                planned_action="find_file",
                confirmation_status="auto_allowed",
                execution_status="completed",
                language=language
            )
            return {
                "type": "action",
                "intent": intent.value,
                "platform": None,
                "params": params,
                "risk_level": ActionRiskLevel.SAFE.value,
                "target": params.get("filename", ""),
                "reason": "Searching files is a safe read-only operation.",
                "sources": [],
                "requires_confirmation": False,
                "response": file_res.get("result", ""),
                "executable": False
            }

        if intent in (AgentIntent.READ_FILE, AgentIntent.SUMMARIZE_FILE):
            fp = params.get("filepath", "")
            if intent == AgentIntent.SUMMARIZE_FILE:
                file_res = safe_summarize_file(fp)
            else:
                file_res = safe_read_file(fp)

            resp_text = file_res.get("result") or file_res.get("error", "Could not read file.")
            context.add_turn(msg_clean, resp_text, topic="file_reading")
            return {
                "type": "action",
                "intent": intent.value,
                "platform": None,
                "params": params,
                "risk_level": ActionRiskLevel.SAFE.value,
                "target": fp,
                "reason": "Reading file content within allowed user directories.",
                "sources": [],
                "requires_confirmation": False,
                "response": resp_text,
                "executable": False
            }

        # 2d. State-Mutating Computer & Communication Actions (Permission & Confirmation Required)
        action_mapping = {
            AgentIntent.OPEN_APPLICATION: ("open_application", params.get("app_name", "App")),
            AgentIntent.OPEN_WEBSITE: ("open_website", params.get("url", "https://www.google.com")),
            AgentIntent.WEB_SEARCH: ("web_search_browser", f"Search: {params.get('query', '')}"),
            AgentIntent.SCREENSHOT: ("take_screenshot", "Display screenshot"),
            AgentIntent.CREATE_FOLDER: ("create_folder", params.get("folder_name", "Folder")),
            AgentIntent.RENAME_FILE: ("rename_file", f"{params.get('source')} -> {params.get('destination')}"),
            AgentIntent.MOVE_FILE: ("move_file", f"{params.get('source')} -> {params.get('destination')}"),
            AgentIntent.DELETE_FILE: ("delete_file", params.get("filepath", "File")),
            AgentIntent.CLICK: ("click_screen", params.get("target", "Screen element")),
            AgentIntent.TYPE: ("type_text", params.get("text", "")),
            AgentIntent.PRESS_KEY: ("press_key", params.get("key", "").upper()),
            AgentIntent.SCROLL: ("scroll_screen", f"{params.get('direction', 'down')} ({params.get('steps', 3)} steps)"),
            AgentIntent.CALL_CONTACT: ("call_contact", params.get("contact", "Contact")),
            AgentIntent.SEND_MESSAGE: ("send_text_message", params.get("contact", "Contact")),
        }

        if intent in action_mapping:
            action_name, target_desc = action_mapping[intent]
            
            # Step 4: Permission Check
            risk_level, requires_confirmation, reason = PermissionManager.evaluate(action_name, params)

            # Localized confirmation prompt
            if language == "bn":
                prompt = f"অনুমতি প্রয়োজন [{risk_level.value}]: AURA '{target_desc}' {action_name} করতে প্রস্তুত। অনুমতি দিচ্ছেন?"
            elif language == "hi":
                prompt = f"अनुमति आवश्यक है [{risk_level.value}]: AURA '{target_desc}' {action_name} करने के लिए तैयार है। क्या अनुमति है?"
            else:
                prompt = f"Awaiting Confirmation [{risk_level.value}]: AURA wants to execute {action_name} on '{target_desc}'. Reason: {reason}. Allow or deny?"

            action_dict = {
                "type": "communication" if "message" in action_name or "call" in action_name else "action",
                "intent": intent.value,
                "action": action_name,
                "platform": params.get("platform", "phone") if "message" in action_name or "call" in action_name else None,
                "params": params,
                "risk_level": risk_level.value,
                "target": str(target_desc),
                "reason": reason,
                "sources": [],
                "requires_confirmation": requires_confirmation,
                "response": prompt,
                "explanation": prompt,
                "executable": True
            }
            context.set_pending_action(action_dict)
            return action_dict

        # 2e. Conversational Knowledge & Real-time Web fallback
        from ..assistant.brain import natural_offline_brain
        return natural_offline_brain(msg_clean, language, session_id)


    def execute_confirmed_action(
        self, original_command: str, action: str, params: Dict[str, Any], language: str = "en"
    ) -> Dict[str, Any]:
        """
        Execute an action after explicit confirmation has been granted by the user.
        Includes safety validation, execution, post-execution verification, and SQLite logging.
        """
        # Step 1: Safety & Allowlist Validation
        # Extend SAFE_ACTIONS for Stage 8 primitives
        STAGE8_ALLOWED_ACTIONS = SAFE_ACTIONS | {
            "web_search_browser", "read_file", "summarize_file", "rename_file", "move_file", "delete_file"
        }

        if action not in STAGE8_ALLOWED_ACTIONS:
            add_action_history(
                original_command=original_command,
                action=action,
                result="Blocked: Action not in safe allowlist.",
                success=False,
                detected_intent=action,
                confirmation_status="blocked",
                execution_status="failed",
                error="Action not permitted",
                language=language
            )
            return {
                "success": False,
                "result": None,
                "error": f"Action '{action}' is blocked by security allowlist.",
                "verified": False,
                "evidence": "Action blocked prior to dispatch."
            }

        # Step 2: Action Execution
        exec_res: Dict[str, Any]
        if action == "web_search_browser":
            exec_res = safe_browser_search(params.get("query", ""))
        elif action == "read_file":
            exec_res = safe_read_file(params.get("filepath", ""))
        elif action == "summarize_file":
            exec_res = safe_summarize_file(params.get("filepath", ""))
        elif action == "rename_file":
            exec_res = safe_rename_file(params.get("source", ""), params.get("destination", ""))
        elif action == "move_file":
            exec_res = safe_move_file(params.get("source", ""), params.get("destination", ""))
        elif action == "delete_file":
            exec_res = safe_delete_file(params.get("filepath", ""))
        else:
            exec_res = execute_safe_action(action, params, original_command)

        success = exec_res.get("success", False)
        result_msg = exec_res.get("result") if success else None
        error_msg = exec_res.get("error") if not success else None

        # Step 3: Result Verification
        verification = verify_action_execution(action, params, exec_res)

        # Step 4: History Logging
        add_action_history(
            original_command=original_command,
            action=action,
            result=result_msg or error_msg or "Executed",
            success=success and verification.verified,
            detected_intent=action,
            planned_action=action,
            confirmation_status="allowed",
            execution_status="verified" if (success and verification.verified) else "failed",
            error=error_msg or verification.error,
            language=language
        )

        return {
            "success": success and verification.verified,
            "result": result_msg,
            "error": error_msg or verification.error,
            "verified": verification.verified,
            "evidence": verification.evidence
        }

_agent_pipeline = AuraAgentPipeline()

def get_agent_pipeline() -> AuraAgentPipeline:
    return _agent_pipeline
