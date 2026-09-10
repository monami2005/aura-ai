from typing import Dict, Any, Optional
from ..provider import CommunicationProvider

class MessengerProvider(CommunicationProvider):
    def __init__(self, is_configured: bool = False):
        self.is_configured = is_configured

    def call_contact(self, contact_name: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"Messenger Audio/Video Calling API is not configured for '{contact_name}'."
            }
        return {"success": True, "result": f"Started Messenger call with {contact_name}."}

    def send_text_message(self, contact_name: str, message: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"Facebook Messenger Send API is not configured for '{contact_name}'."
            }
        return {"success": True, "result": f"Sent Messenger message to {contact_name}."}

    def send_voice_message(self, contact_name: str, message: str, audio_path: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"Messenger Audio Attachment API is not configured for '{contact_name}'."
            }
        return {"success": True, "result": f"Sent Messenger voice clip to {contact_name}."}
