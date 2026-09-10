from typing import Dict, Any, Optional

SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {"name": "English", "native": "English", "tts_code": "en-US", "locale": "en-US"},
    "bn": {"name": "Bengali", "native": "বাংলা", "tts_code": "bn-IN", "locale": "bn-IN"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "tts_code": "hi-IN", "locale": "hi-IN"},
}

def get_supported_languages() -> Dict[str, Dict[str, str]]:
    return SUPPORTED_LANGUAGES

def detect_language(text: str) -> Dict[str, str]:
    if not text or not text.strip():
        return {"language": "en", "name": "English"}
        
    # Bengali unicode range: \u0980-\u09FF
    if any("\u0980" <= c <= "\u09FF" for c in text):
        return {"language": "bn", "name": "Bengali"}
    # Devanagari (Hindi) unicode range: \u0900-\u097F
    elif any("\u0900" <= c <= "\u097F" for c in text):
        return {"language": "hi", "name": "Hindi"}
        
    return {"language": "en", "name": "English"}

def speak_text(text: str, language: str = "en") -> Dict[str, Any]:
    if not text or not text.strip():
        return {"success": False, "message": "Empty text provided."}

    # Clean text to avoid speaking long code snippets
    clean_text = text[:300]

    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        
        # Try finding language matching voice if available
        voices = engine.getProperty("voices")
        selected_voice_id = None
        lang_code = language.lower()
        
        for voice in voices:
            v_name = voice.name.lower()
            v_id = voice.id.lower()
            if lang_code == "bn" and ("bengali" in v_name or "bangla" in v_name or "bn" in v_id):
                selected_voice_id = voice.id
                break
            elif lang_code == "hi" and ("hindi" in v_name or "kalpana" in v_name or "hi" in v_id):
                selected_voice_id = voice.id
                break
            elif lang_code == "en" and ("english" in v_name or "david" in v_name or "zira" in v_name or "en" in v_id):
                selected_voice_id = voice.id
                break
                
        if selected_voice_id:
            engine.setProperty("voice", selected_voice_id)
            
        engine.say(clean_text)
        engine.runAndWait()
        return {
            "success": True,
            "message": "Spoke text successfully.",
            "voice_used": selected_voice_id or "default"
        }
    except ImportError:
        return {
            "success": False,
            "message": "pyttsx3 library is not installed on backend. Frontend Web Speech Synthesis can be used.",
            "voice_used": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"TTS playback notice: {str(e)}",
            "voice_used": None
        }
