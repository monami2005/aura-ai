from datetime import datetime
from typing import Optional
from .models import ScreenAnalyzeResponse
from .capture import capture_primary_screen
from .vision import get_vision_provider

class ScreenAwarenessService:
    @staticmethod
    def is_screen_query(query: str) -> bool:
        q_lower = query.lower()
        screen_keywords = [
            "on my screen", "this screen", "my screen", "visible on screen", "screen error",
            "look at screen", "analyze screen", "see on screen", "understand what i'm looking at",
            # Bengali triggers
            "আমার স্ক্রিন", "স্ক্রিনে কী", "স্ক্রিনে কি", "স্ক্রিনটা", "স্ক্রিনে যে error", "স্ক্রিন দেখ",
            # Hindi triggers
            "मेरी स्क्रीन", "स्क्रीन पर क्या", "स्क्रीन पर कौन", "स्क्रीन को समझाओ", "स्क्रीन देखो"
        ]
        return any(k in q_lower or k in query for k in screen_keywords)

    def analyze_current_screen(self, question: Optional[str] = None, language: str = "en") -> ScreenAnalyzeResponse:
        ts = datetime.utcnow().isoformat() + "Z"
        
        # 1. Capture primary display explicitly in memory
        image_bytes, metadata, err = capture_primary_screen()
        if err or not image_bytes:
            return ScreenAnalyzeResponse(
                success=False,
                language=language,
                summary=f"Could not capture screen: {err or 'Unknown error'}",
                details=None,
                provider="CaptureDevice",
                timestamp=ts
            )

        # 2. Analyze using configured vision provider
        provider = get_vision_provider()
        return provider.analyze_screen(image_bytes, question, language)


# Global Service Singleton
_screen_service = ScreenAwarenessService()

def get_screen_service() -> ScreenAwarenessService:
    return _screen_service
