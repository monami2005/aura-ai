from typing import Dict, Any, Optional
from ..provider import CommunicationProvider

class WhatsAppProvider(CommunicationProvider):
    def __init__(self, is_configured: bool = False):
        self.is_configured = is_configured

    def call_contact(self, contact_name: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"WhatsApp VoIP calling integration is not configured for '{contact_name}'."
            }
        return {"success": True, "result": f"Initiated WhatsApp call to {contact_name}."}

    def send_text_message(self, contact_name: str, message: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"WhatsApp Business API / Desktop Bridge is not configured. Set up WhatsApp integration to send messages to '{contact_name}'."
            }
        return {"success": True, "result": f"Sent WhatsApp message to {contact_name}."}

    def send_voice_message(self, contact_name: str, message: str, audio_path: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"WhatsApp Voice Note API is not configured for '{contact_name}'."
            }
        return {"success": True, "result": f"Sent WhatsApp voice note to {contact_name}."}
