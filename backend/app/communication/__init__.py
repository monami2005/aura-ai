from .provider import (
    CommunicationProvider,
    DefaultCommunicationProvider,
    get_communication_provider,
    set_communication_provider
)
from .contacts import resolve_contact

__all__ = [
    "CommunicationProvider",
    "DefaultCommunicationProvider",
    "get_communication_provider",
    "set_communication_provider",
    "resolve_contact"
]
