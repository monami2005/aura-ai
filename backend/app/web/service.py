import re
from typing import Dict, Any, List
from .models import WebSearchResultItem, WebIntelligenceResponse
from .search import perform_safe_web_search

REALTIME_PATTERNS = [
    r"\blatest\b", r"\btoday\b", r"\bcurrent\b", r"\bright now\b", r"\bthis week\b",
    r"\brecent\b", r"\bnews\b", r"\bweather\b", r"\bprice\b", r"\bstock\b",
    r"\bscore\b", r"\bschedule\b", r"\bwhat happened\b", r"\brecent update\b", r"\blive\b",
    # Bengali triggers
    r"আজকের", r"তাজা খবর", r"বর্তমান", r"এখনকার", r"দাম", r"আবহাওয়া", r"খবর",
    # Hindi triggers
    r"आज की", r"ताज़ा खबर", r"वर्तमान", r"अभी", r"मौसम", r"कीमत", r"समाचार", r"खबर"
]

class WebIntelligenceService:
    @staticmethod
    def is_realtime_query(query: str) -> bool:
        q_lower = query.lower()
        for pattern in REALTIME_PATTERNS:
            if re.search(pattern, q_lower, flags=re.IGNORECASE):
                return True
        return False

    def query(self, query: str, language: str = "en") -> WebIntelligenceResponse:
        is_rt = self.is_realtime_query(query)
        sources = perform_safe_web_search(query)

        # If external retrieval returned zero sources or failed
        if not sources:
            if language == "bn":
                ans = "আমি এই মুহূর্তে নির্ভরযোগ্য সাম্প্রতিক তথ্য খুঁজে পাইনি বা ওয়েব পরিষেবা অনুপলব্ধ রয়েছে।"
            elif language == "hi":
                ans = "मुझे इस समय इसके लिए विश्वसनीय ताज़ा जानकारी नहीं मिली या वेब सेवा अनुपलब्ध है।"
            else:
                ans = "I couldn't access live web information or find reliable results for that query right now."

            return WebIntelligenceResponse(
                query=query,
                is_realtime_query=is_rt,
                answer=ans,
                sources=[],
                confidence=0.0
            )

        # Prompt-Injection Defense: sanitize snippet text and treat as untrusted passive data
        primary_snippet = sources[0].snippet
        
        if language == "bn":
            ans = f"আমি ওয়েব থেকে সাম্প্রতিক তথ্য পেয়েছি। {primary_snippet}"
        elif language == "hi":
            ans = f"मुझे वेब से ताज़ा जानकारी मिली है। {primary_snippet}"
        else:
            ans = f"Here is the latest verified web information regarding your query: {primary_snippet}"

        return WebIntelligenceResponse(
            query=query,
            is_realtime_query=is_rt,
            answer=ans,
            sources=sources,
            confidence=0.95
        )


# Global Service Singleton
_web_service = WebIntelligenceService()

def get_web_service() -> WebIntelligenceService:
    return _web_service
