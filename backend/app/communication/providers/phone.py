from typing import Dict, Any, Optional
from ..provider import CommunicationProvider

class PhoneProvider(CommunicationProvider):
    def __init__(self, is_configured: bool = False):
        self.is_configured = is_configured

    def call_contact(self, contact_name: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"Phone calling service is not configured. Connect GSM modem or Twilio Voice to call '{contact_name}'."
            }
        return {"success": True, "result": f"Placing voice call to {contact_name} via Phone carrier."}

    def send_text_message(self, contact_name: str, message: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"SMS gateway is not configured. Set up SMS credentials to text '{contact_name}'."
            }
        return {"success": True, "result": f"Sent SMS to {contact_name}."}

    def send_voice_message(self, contact_name: str, message: str, audio_path: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "success": False,
                "error": f"MMS/Carrier voice messaging is not configured for '{contact_name}'."
            }
        return {"success": True, "result": f"Delivered carrier voice message to {contact_name}."}
