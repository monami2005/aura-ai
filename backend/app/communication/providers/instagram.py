from typing import Dict, Any, Optional
from ..provider import CommunicationProvider

class InstagramProvider(CommunicationProvider):
    def __init__(self, is_configured: bool = False):
        self.is_configured = is_configured

    def call_contact(self, contact_name: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        return {
            "success": False,
            "error": f"Instagram Direct Calling is not supported via external API for '{contact_name}'."
        }

    def send_text_message(self, contact_name: str, message: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"Instagram Direct Messaging API is not configured for '{contact_name}'."
            }
        return {"success": True, "result": f"Sent Instagram direct message to {contact_name}."}

    def send_voice_message(self, contact_name: str, message: str, audio_path: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"Instagram Voice Note API is not configured for '{contact_name}'."
            }
        return {"success": True, "result": f"Sent Instagram voice message to {contact_name}."}
