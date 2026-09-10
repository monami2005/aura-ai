from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class CommunicationProvider(ABC):
    @abstractmethod
    def call_contact(self, contact_name: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """Initiate a voice phone call to contact."""
        pass

    @abstractmethod
    def send_text_message(self, contact_name: str, message: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """Send an SMS or chat message to contact."""
        pass

    @abstractmethod
    def send_voice_message(self, contact_name: str, message: str, audio_path: Optional[str] = None) -> Dict[str, Any]:
        """Send a synthesized voice message to contact."""
        pass


class MultiPlatformCommunicationRouter(CommunicationProvider):
    """
    Routes requests to specific communication platform providers
    (Phone, WhatsApp, Messenger, Instagram).
    """
    def __init__(self):
        from .providers.phone import PhoneProvider
        from .providers.whatsapp import WhatsAppProvider
        from .providers.messenger import MessengerProvider
        from .providers.instagram import InstagramProvider

        self.providers: Dict[str, CommunicationProvider] = {
            "phone": PhoneProvider(is_configured=False),
            "whatsapp": WhatsAppProvider(is_configured=False),
            "messenger": MessengerProvider(is_configured=False),
            "instagram": InstagramProvider(is_configured=False),
        }

    def get_provider(self, platform: Optional[str] = "phone") -> CommunicationProvider:
        plat_key = (platform or "phone").lower().strip()
        return self.providers.get(plat_key, self.providers["phone"])

    def call_contact(self, contact_name: str, phone_number: Optional[str] = None, platform: str = "phone") -> Dict[str, Any]:
        provider = self.get_provider(platform)
        return provider.call_contact(contact_name, phone_number)

    def send_text_message(self, contact_name: str, message: str, phone_number: Optional[str] = None, platform: str = "phone") -> Dict[str, Any]:
        provider = self.get_provider(platform)
        return provider.send_text_message(contact_name, message, phone_number)

    def send_voice_message(self, contact_name: str, message: str, audio_path: Optional[str] = None, platform: str = "phone") -> Dict[str, Any]:
        provider = self.get_provider(platform)
        return provider.send_voice_message(contact_name, message, audio_path)


# Global multi-platform router instance
_active_router = MultiPlatformCommunicationRouter()

DefaultCommunicationProvider = MultiPlatformCommunicationRouter

def get_communication_provider() -> MultiPlatformCommunicationRouter:
    return _active_router

def set_communication_provider(provider: CommunicationProvider):
    global _active_router
    _active_router = provider

