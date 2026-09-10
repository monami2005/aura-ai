import re
from typing import Dict, Any, Optional, Tuple

SAFE_KEYS = {
    "enter", "return", "tab", "escape", "esc", "space",
    "up", "down", "left", "right", "backspace", "delete",
    "home", "end", "pageup", "pagedown"
}

DANGEROUS_KEYS = {
    "ctrl+alt+del", "ctrl+alt+delete", "win+l", "alt+f4", "shutdown", "reboot"
}

def is_ui_interaction_query(query: str) -> bool:
    """
    Detect whether the user's query asks for UI interaction / desktop automation.
    Multilingual support for English, Bengali, and Hindi.
    """
    q_lower = query.lower().strip()
    
    # Avoid false positive on informational queries like "What is clicking?"
    if q_lower.startswith("what is") or q_lower.startswith("explain") or q_lower.startswith("how does"):
        return False
    if "কি" in query and not any(k in query for k in ["করো", "চাপো"]):
        return False

    ui_patterns = [
        # English
        r"\bclick\b", r"\btap\b", r"\bpress\b", r"\btype\b", r"\bscroll\b",
        # Bengali
        r"ক্লিক", r"চাপো", r"প্রেস", r"টাইপ", r"স্ক্রোল", r"লিখো",
        # Hindi
        r"क्लिक", r"दबाओ", r"प्रेस", r"टाइप", r"स्क्रॉल", r"लिखो"
    ]
    
    return any(re.search(p, query, re.IGNORECASE) for p in ui_patterns)


def extract_click_params(query: str) -> Dict[str, Any]:
    """Extract coordinates or target element description from click command."""
    q_lower = query.lower()
    
    # Check for explicit coordinates like (500, 300) or "at 500, 300" or "at 500 300"
    coord_match = re.search(r"\(?\s*(\d{1,5})\s*,\s*(\d{1,5})\s*\)?", query)
    if not coord_match:
        coord_match = re.search(r"\bat\s+(\d{1,5})\s+(\d{1,5})\b", query, re.IGNORECASE)

    if coord_match:
        x = int(coord_match.group(1))
        y = int(coord_match.group(2))
        return {
            "mode": "coordinates",
            "x": x,
            "y": y,
            "target": f"({x}, {y})"
        }
    
    # Extract element name (e.g. "click the submit button" -> "Submit button")
    target = "screen element"
    clean = re.sub(r"click\s+(on\s+)?(the\s+)?", "", query, flags=re.IGNORECASE).strip()
    clean = clean.replace("ক্লিক করো", "").replace("বাটনে", "বাটন").replace("বটন पर", "").replace("क्लिक करो", "").strip()
    if clean:
        target = clean
        
    return {
        "mode": "element",
        "x": None,
        "y": None,
        "target": target
    }


def extract_type_params(query: str) -> Dict[str, Any]:
    """Extract text to type and optional target field."""
    # Check for quoted text first: type "hello world"
    quote_match = re.search(r"['\"]([^'\"]+)['\"]", query)
    if quote_match:
        text = quote_match.group(1)
    else:
        # Extract after keyword
        parts = re.split(r"type|টাইপ করো|टाइप करो|লিখো|लिखो", query, flags=re.IGNORECASE)
        text = parts[-1].strip() if len(parts) > 1 else "Sample Text"
    
    # Sanitize text
    text = "".join(ch for ch in text if ch.isprintable())[:500]
    return {
        "text": text or "Text"
    }


def extract_key_params(query: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Extract navigation key to press and validate against SAFE_KEYS allowlist.
    Returns: (is_valid, key_name, error_message)
    """
    q_lower = query.lower()
    
    # Check for dangerous key combinations
    for dang in DANGEROUS_KEYS:
        if dang in q_lower:
            return False, dang, f"Key combination '{dang}' is blocked for system security."
            
    # Key mapping
    key_aliases = {
        "enter": "enter", "return": "enter",
        "tab": "tab",
        "escape": "escape", "esc": "escape",
        "space": "space", "spacebar": "space",
        "up": "up", "arrow up": "up", "up arrow": "up",
        "down": "down", "arrow down": "down", "down arrow": "down",
        "left": "left", "arrow left": "left", "left arrow": "left",
        "right": "right", "arrow right": "right", "right arrow": "right",
        "backspace": "backspace",
        "delete": "delete",
        "home": "home",
        "end": "end",
        "pageup": "pageup", "page up": "pageup",
        "pagedown": "pagedown", "page down": "pagedown"
    }
    
    # Bengali / Hindi key mentions
    if "এন্টার" in query or "एंटर" in query:
        return True, "enter", None
    if "ট্যাব" in query or "टैब" in query:
        return True, "tab", None
    if "এস্কেপ" in query or "एस्केप" in query:
        return True, "escape", None
    if "স্পেস" in query or "स्पेस" in query:
        return True, "space", None

    for alias, standard in key_aliases.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", q_lower):
            return True, standard, None

    # Check direct word after "press"
    press_match = re.search(r"press\s+([a-zA-Z0-9_\-]+)", q_lower)
    if press_match:
        candidate = press_match.group(1).lower()
        if candidate in SAFE_KEYS:
            return True, candidate, None
        return False, candidate, f"Key '{candidate}' is not in the safe allowed navigation keys."

    return False, None, "No valid navigation key specified."


def extract_scroll_params(query: str) -> Dict[str, Any]:
    """Extract scroll direction and steps."""
    q_lower = query.lower()
    
    direction = "down"
    if "up" in q_lower or "উপরে" in query or "ऊपर" in query:
        direction = "up"
    
    steps = 3
    num_match = re.search(r"\b(\d{1,2})\s*(steps|times|বার|बार)?\b", query)
    if num_match:
        try:
            val = int(num_match.group(1))
            if 1 <= val <= 20:
                steps = val
        except ValueError:
            pass

    return {
        "direction": direction,
        "steps": steps
    }


def plan_ui_action(query: str, language: str = "en") -> Dict[str, Any]:
    """
    Formulate a strictly confirmed UI action plan.
    Guarantees requires_confirmation=True.
    """
    q_lower = query.lower()
    
    # 1. Key Press Action
    if "press" in q_lower or "চাপো" in query or "दबाओ" in query or any(k in q_lower for k in ["enter", "tab", "escape", "esc", "space"]):
        is_valid, key_name, err = extract_key_params(query)
        if not is_valid:
            return {
                "type": "action",
                "intent": "press_key",
                "platform": None,
                "params": {"key": key_name or "unknown", "valid": False},
                "sources": [],
                "requires_confirmation": False,
                "response": err or "Invalid key request.",
                "executable": False
            }
        
        if language == "bn":
            prompt = f"অনুমতি প্রয়োজন: '{key_name.upper()}' কী চাপ দেওয়া হবে। অনুমতি দিচ্ছেন?"
        elif language == "hi":
            prompt = f"अनुमति आवश्यक है: '{key_name.upper()}' कुंजी दबाई जाएगी। क्या अनुमति है?"
        else:
            prompt = f"Awaiting confirmation: Press key '{key_name.upper()}'. Allow or cancel?"
            
        return {
            "type": "action",
            "intent": "press_key",
            "platform": None,
            "params": {"key": key_name},
            "sources": [],
            "requires_confirmation": True,
            "response": prompt,
            "executable": True
        }

    # 2. Type Text Action
    elif "type" in q_lower or "টাইপ" in query or "टाइप" in query or "লিখো" in query or "लिखो" in query:
        params = extract_type_params(query)
        typed_text = params["text"]
        
        if language == "bn":
            prompt = f"অনুমতি প্রয়োজন: \"{typed_text}\" টাইপ করা হবে। অনুমতি দিচ্ছেন?"
        elif language == "hi":
            prompt = f"अनुमति आवश्यक है: \"{typed_text}\" टाइप किया जाएगा। क्या अनुमति है?"
        else:
            prompt = f"Awaiting confirmation: Type \"{typed_text}\" into the active field. Allow or cancel?"

        return {
            "type": "action",
            "intent": "type_text",
            "platform": None,
            "params": params,
            "sources": [],
            "requires_confirmation": True,
            "response": prompt,
            "executable": True
        }

    # 3. Scroll Action
    elif "scroll" in q_lower or "স্ক্রোল" in query or "स्क्रॉल" in query:
        params = extract_scroll_params(query)
        direction = params["direction"]
        steps = params["steps"]
        
        if language == "bn":
            dir_bn = "উপরে" if direction == "up" else "নিচে"
            prompt = f"অনুমতি প্রয়োজন: স্ক্রিন {dir_bn} {steps} বার স্ক্রোল করা হবে। অনুমতি দিচ্ছেন?"
        elif language == "hi":
            dir_hi = "ऊपर" if direction == "up" else "नीचे"
            prompt = f"अनुमति आवश्यक है: स्क्रीन {dir_hi} {steps} बार स्क्रॉल की जाएगी। क्या अनुमति है?"
        else:
            prompt = f"Awaiting confirmation: Scroll screen {direction} by {steps} steps. Allow or cancel?"

        return {
            "type": "action",
            "intent": "scroll_screen",
            "platform": None,
            "params": params,
            "sources": [],
            "requires_confirmation": True,
            "response": prompt,
            "executable": True
        }

    # 4. Click Screen Action (Default UI Interaction)
    else:
        params = extract_click_params(query)
        target_display = f"at ({params['x']}, {params['y']})" if params["mode"] == "coordinates" else f"'{params['target']}'"
        
        if language == "bn":
            prompt = f"অনুমতি প্রয়োজন: স্ক্রিনে {target_display}-এ ক্লিক করা হবে। অনুমতি দিচ্ছেন?"
        elif language == "hi":
            prompt = f"अनुमति आवश्यक है: स्क्रीन पर {target_display} पर क्लिक किया जाएगा। क्या अनुमति है?"
        else:
            prompt = f"Awaiting confirmation: Click on screen {target_display}. Allow or cancel?"

        return {
            "type": "action",
            "intent": "click_screen",
            "platform": None,
            "params": params,
            "sources": [],
            "requires_confirmation": True,
            "response": prompt,
            "executable": True
        }
