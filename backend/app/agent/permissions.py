from typing import Tuple, Dict, Any
from .models import ActionRiskLevel, AgentIntent

class PermissionManager:
    """
    Centralized Permission Manager for AURA AI Agent.
    Categorizes actions into SAFE, CONFIRM, and HIGH_RISK tiers.
    Enforces mandatory approval for state-mutating and sensitive computer operations.
    """

    SAFE_ACTIONS = {
        "chat",
        "web_search",
        "take_screenshot",
        "analyze_screen",
        "analyze_error",
        "explain_code",
        "read_file",
        "summarize_file",
        "list_files",
        "find_file",
    }

    CONFIRM_ACTIONS = {
        "click_screen",
        "type_text",
        "press_key",
        "scroll_screen",
        "open_application",
        "open_website",
        "create_folder",
        "rename_file",
        "move_file",
        "organize_files",
    }

    HIGH_RISK_ACTIONS = {
        "delete_file",
        "send_text_message",
        "send_voice_message",
        "call_contact",
        "change_system_setting",
        "install_software",
        "execute_payment",
        "unknown_action",
    }

    @classmethod
    def evaluate(cls, action_name: str, params: Dict[str, Any] = None) -> Tuple[ActionRiskLevel, bool, str]:
        """
        Evaluate an action and return (risk_level, requires_confirmation, reason).
        """
        params = params or {}
        act = action_name.lower().strip()

        # Check HIGH_RISK tier first
        if act in cls.HIGH_RISK_ACTIONS or act.startswith("delete_") or act.startswith("remove_"):
            if "delete" in act or "remove" in act:
                reason = "Irreversible file deletion can cause data loss. Explicit user confirmation is strictly mandatory."
            elif "message" in act or "call" in act:
                reason = "Outbound communication will send real messages or initiate real calls."
            else:
                reason = "This action has high risk or system-wide impact and must never execute automatically."
            return ActionRiskLevel.HIGH_RISK, True, reason

        # Check CONFIRM tier
        if act in cls.CONFIRM_ACTIONS:
            if act == "click_screen":
                reason = "Simulating mouse input on the active display requires confirmation."
            elif act == "type_text":
                reason = "Simulating keyboard input into the active application requires confirmation."
            elif act == "press_key":
                reason = "Simulating keystrokes on the system requires confirmation."
            elif act == "scroll_screen":
                reason = "Scrolling the active window requires confirmation."
            elif act == "open_application":
                reason = f"Launching external application '{params.get('app_name', 'application')}' requires confirmation."
            elif act == "open_website":
                reason = f"Navigating browser to '{params.get('url', 'website')}' requires confirmation."
            elif act in ("create_folder", "rename_file", "move_file"):
                reason = "Modifying local file system items requires confirmation."
            else:
                reason = "Action mutates system state and requires confirmation."
            return ActionRiskLevel.CONFIRM, True, reason

        # Check SAFE tier
        if act in cls.SAFE_ACTIONS:
            reason = "Read-only or passive operation. Safe to perform."
            return ActionRiskLevel.SAFE, False, reason

        # Unknown actions default to HIGH_RISK
        return ActionRiskLevel.HIGH_RISK, True, f"Unknown action '{action_name}' is not classified and cannot run automatically."

permission_manager = PermissionManager()

def get_permission_manager() -> PermissionManager:
    return permission_manager
