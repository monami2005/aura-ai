import re
from typing import Tuple, Dict, Any, Optional
from .models import AgentIntent
from ..screen.interaction import (
    extract_click_params,
    extract_type_params,
    extract_key_params,
    extract_scroll_params,
    SAFE_KEYS
)

def detect_structured_intent(query: str, language: str = "en") -> Tuple[AgentIntent, Dict[str, Any]]:
    """
    Structured, multilingual intent classifier supporting English, Bengali, Hindi,
    and mixed-language (Banglish / Hinglish) commands.
    """
    q_clean = query.strip()
    q_lower = q_clean.lower()

    # 0. Code Fix & Modification Requests
    # E.g., "Eta fix kore dao", "Fix korar age amake dekhao", "fix this error", "ঠিক করে দাও"
    if any(k in q_lower or k in q_clean for k in [
        "fix kore dao", "eta fix kore dao", "eta fix koro", "fix it", "fix this", "fix code",
        "apply fix", "apply this fix", "please fix it", "fix korar age", "amake dekhao",
        "show me the fix", "show fix", "ঠিক করে দাও", "কোড ঠিক করো", "ফিক্স করে দাও",
        "আগে আমাকে দেখাও", "সংশোধন করো", "इसे ठीक करो", "कोड ठीक करो", "फिक्स करो"
    ]):
        return AgentIntent.FIX_CODE, {"command": q_clean}

    # 1. Screen Error & Code Check Detection
    # E.g., "Ei error ta bujhiye dao", "Ei error ta ki?", "Amar code ta check koro", "Eta keno hocche?", "Easy kore bojhao"
    if any(k in q_lower or k in q_clean for k in [
        "amar code ta check koro", "code ta check koro", "amar code ta dekho", "amar code check",
        "check my code", "check this code", "আমার কোড", "কোডটা চেক করো", "कोड चेक करो",
        "review my code", "review this code"
    ]):
        return AgentIntent.HELP_WITH_CODE, {"question": q_clean, "focus": "code_review"}

    if any(k in q_lower or k in q_clean for k in [
        "ei error", "error ta", "এই এরর", "এই error", "error ta ki", "error ta bujhiye dao",
        "yeh error", "ye error", "यह एरर", "एरर क्या है", "what is this error", "explain visible error",
        "look at this error", "screen error", "eta keno hocche", "keno hocche", "why is this happening",
        "easy kore bojhao", "সহজ করে বোঝাও", "सरल भाषा में समझाओ", "explain simply", "easy kore"
    ]):
        return AgentIntent.ANALYZE_ERROR, {"question": q_clean, "focus": "error"}

    if any(k in q_lower or k in q_clean for k in [
        "on my screen", "this screen", "my screen", "visible on screen",
        "আমার স্ক্রিন", "স্ক্রিনে কী আছে", "স্ক্রিনে কি", "স্ক্রিনটা দেখ",
        "मेरी स्क्रीन", "स्क्रीन पर क्या", "स्क्रीन देखो"
    ]) and not any(k in q_lower for k in ["click", "type", "press", "scroll", "ক্লিক", "টাইপ", "চাপো"]):
        return AgentIntent.ANALYZE_SCREEN, {"question": q_clean}

    # 2. Browser Search Workflows
    # E.g., "Google e DAA merge sort search koro", "Search Google for Python FastAPI tutorial", "Google pe search karo AI"
    search_patterns = [
        r"google\s+(?:e|pe|te|par|me|mein)\s+(.*?)\s+(?:search\s+koro|search\s+karo|khojo|dhoondo)",
        r"(?:search\s+google\s+for|google\s+search\s+for|search\s+for|search)\s+(.*)",
        r"(.*?)\s+(?:search\s+koro|search\s+karo|khojo|সার্চ করো|सर्च करो)",
    ]
    for sp in search_patterns:
        m = re.search(sp, q_clean, re.IGNORECASE)
        if m:
            raw_q = m.group(1).strip()
            # Clean search query prefixes/suffixes
            clean_q = re.sub(r"^(google\s+(?:e|pe|par|for)?|browser\s+e\s+)", "", raw_q, flags=re.IGNORECASE).strip()
            if clean_q and clean_q.lower() not in ["google", "browser", "something"]:
                return AgentIntent.WEB_SEARCH, {"query": clean_q, "engine": "google"}

    # 3. Application Launch
    # E.g., "Chrome kholo", "Chrome open koro", "Launch calculator", "Notepad kholo", "कैलकुलेटर खोलो"
    app_patterns = [
        r"(chrome|google chrome|calculator|notepad|paint|कैलकुलेटर|क्रोम|नोटपैड|ক্যালকুলেটর|নোটপ্যাড)\s+(?:kholo|open koro|khol|chalu koro|khojo|खोलो|खोलें|খোল|খোলো)",
        r"(?:open|launch|start|खोलो|খোল)\s+(chrome|google chrome|calculator|notepad|paint|कैलकुलेटर|क्रोम|नोटपैड|ক্যালকুলেটর|নোটপ্যাড)\b",
        r"(?:application|app)\s+(chrome|calculator|notepad|paint)",
    ]
    for ap in app_patterns:
        m = re.search(ap, q_clean, re.IGNORECASE)
        if m:
            raw_app = m.group(1).lower().strip()
            name_map = {
                "कैलकुलेटर": "calculator",
                "ক্যালকুলেটর": "calculator",
                "क्रोम": "chrome",
                "नोटपैड": "notepad",
                "নোটপ্যাড": "notepad"
            }
            app_name = name_map.get(raw_app, raw_app)
            return AgentIntent.OPEN_APPLICATION, {"app_name": app_name}

    # 4. Website Launch
    # E.g., "Open YouTube", "YouTube kholo", "GitHub open koro"
    if any(k in q_lower for k in ["youtube", "github", "wikipedia", "stackoverflow"]) and any(k in q_lower for k in ["open", "kholo", "খোল", "खोलो", "launch"]):
        for site in ["youtube", "github", "wikipedia", "stackoverflow"]:
            if site in q_lower:
                return AgentIntent.OPEN_WEBSITE, {"url": f"https://www.{site}.com", "site": site}

    # 5. Screenshot
    if any(k in q_lower or k in q_clean for k in ["screenshot", "স্ক্রিনশট", "स्क्रीनशॉट"]):
        return AgentIntent.SCREENSHOT, {}

    # 6. File & Folder Operations
    # 6a. Create folder: "create folder named AURA", "folder banao Test", "একটি ফোল্ডার বানাও Notes"
    if any(k in q_lower or k in q_clean for k in ["create folder", "make folder", "folder banao", "folder banate", "ফোল্ডার বানাও", "ফোল্ডার তৈরি", "फ़ोल्डर बना", "फोल्डर बना"]):
        parts = re.split(r"named|name|banao|banate|বানাও|তৈরি করো|ফোল্ডার|फ़ोल्डर|फोल्डर", q_clean, flags=re.IGNORECASE)
        candidate = parts[-1].strip().strip("'\"").strip() if len(parts) > 1 else "New_Aura_Folder"
        folder_name = candidate or "New_Aura_Folder"
        return AgentIntent.CREATE_FOLDER, {"folder_name": folder_name}

    # 6b. Find file: "find my notes.txt file", "find file app.py", "notes.txt file ta khojo", "Amar notes.txt file ta khuje dao"
    if any(k in q_lower or k in q_clean for k in [
        "find file", "find my", "search file", "file ta khojo", "file khojo",
        "khuje dao", "khuje", "khujo", "dhoondo", "dhoondho", "फ़ाइल खोज", "ফাইল খোঁজো", "খুঁজে দাও", "খুঁজে"
    ]):
        # Extract filename (e.g. word with extension or word after find)
        file_match = re.search(r"([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]{1,5})", q_clean)
        if file_match:
            filename = file_match.group(1)
        else:
            parts = re.split(r"find file|find my|search file|file|khojo|khuje dao|khuje|khujo|dhoondo", q_clean, flags=re.IGNORECASE)
            filename = parts[-1].strip().strip("'\"") if len(parts) > 1 else "document.txt"
        return AgentIntent.FIND_FILE, {"filename": filename or "document.txt"}

    # 6c. Read file: "read file notes.txt", "read notes.txt", "notes.txt file ta poro"
    if any(k in q_lower or k in q_clean for k in ["read file", "read ", "file ta poro", "file poro", "फ़ाइल पढ़ो", "ফাইল পড়"]):
        file_match = re.search(r"([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]{1,5})", q_clean)
        if file_match:
            return AgentIntent.READ_FILE, {"filepath": file_match.group(1)}

    # 6d. Summarize file: "summarize notes.txt", "notes.txt summarize koro"
    if "summarize" in q_lower or "সারাংশ" in q_clean or "सारांश" in q_clean:
        file_match = re.search(r"([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]{1,5})", q_clean)
        if file_match:
            return AgentIntent.SUMMARIZE_FILE, {"filepath": file_match.group(1)}

    # 6e. Rename file: "rename old.txt to new.txt"
    if "rename" in q_lower or "নাম পরিবর্তন" in q_clean or "नाम बदलो" in q_clean:
        files = re.findall(r"([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]{1,5})", q_clean)
        if len(files) >= 2:
            return AgentIntent.RENAME_FILE, {"source": files[0], "destination": files[1]}

    # 6f. Move file: "move file.txt to backup"
    if "move" in q_lower or "স্থানান্তর" in q_clean or "मूव" in q_clean:
        file_match = re.search(r"([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]{1,5})", q_clean)
        dest_match = re.search(r"(?:to|into)\s+([a-zA-Z0-9_\-]+)", q_clean, re.IGNORECASE)
        if file_match:
            dest = dest_match.group(1) if dest_match else "Backup"
            return AgentIntent.MOVE_FILE, {"source": file_match.group(1), "destination": dest}

    # 6g. Delete file: "delete notes.txt", "notes.txt delete koro" (HIGH RISK)
    if any(k in q_lower or k in q_clean for k in ["delete", "মুছে ফেল", "डिलीट", "remove file"]):
        file_match = re.search(r"([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]{1,5})", q_clean)
        if file_match:
            return AgentIntent.DELETE_FILE, {"filepath": file_match.group(1)}

    # 7. Code Help & Error Diagnostics
    # E.g., "Why is this Python code giving an error?", "Help with this code", "Explain this compiler error"
    if any(k in q_lower or k in q_clean for k in [
        "python code", "giving an error", "code giving error", "help with code",
        "syntaxerror", "indexerror", "typeerror", "runtime error", "compiler error",
        "কোডে এরর", "কোড সমস্যা", "कोड में एरर", "कोड में समस्या"
    ]):
        return AgentIntent.HELP_WITH_CODE, {"query": q_clean}

    # 8. UI Automation (Click, Type, Press Key, Scroll)
    if "click" in q_lower or "ক্লিক" in q_clean or "क्लिक" in q_clean:
        params = extract_click_params(q_clean)
        return AgentIntent.CLICK, params

    if "type" in q_lower or "টাইপ" in q_clean or "टाइप" in q_clean:
        params = extract_type_params(q_clean)
        return AgentIntent.TYPE, params

    if "press" in q_lower or "চাপো" in q_clean or "दबाओ" in q_clean or any(k in q_lower for k in ["enter", "tab", "escape", "space"]):
        ok, key, _ = extract_key_params(q_clean)
        if ok and key:
            return AgentIntent.PRESS_KEY, {"key": key}

    if "scroll" in q_lower or "স্ক্রোল" in q_clean or "स्क्रॉल" in q_clean:
        params = extract_scroll_params(q_clean)
        return AgentIntent.SCROLL, params

    # 9. Communication (Call & Message)
    if ("call" in q_lower and "code" not in q_lower) or "কল করো" in q_clean or "कॉल करो" in q_clean:
        return AgentIntent.CALL_CONTACT, {"contact": "Contact", "raw": q_clean}

    if (
        any(k in q_lower for k in ["message", "whatsapp", "messenger", "instagram", "text "])
        or any(k in q_clean for k in ["মেসেজ", "ম্যাসেজ", "संदेश", "मैसेज", "হোয়াটসঅ্যাপ", "व्हाट्सएप"])
    ):
        plat = "phone"
        if "whatsapp" in q_lower or "হোয়াটসঅ্যাপ" in q_clean or "व्हाट्सएप" in q_clean:
            plat = "whatsapp"
        elif "messenger" in q_lower or "মেসেঞ্জার" in q_clean or "मैसेंजर" in q_clean:
            plat = "messenger"
        elif "instagram" in q_lower or "ইন্সটাগ্রাম" in q_clean or "इंस्टाग्राम" in q_clean:
            plat = "instagram"
        return AgentIntent.SEND_MESSAGE, {"contact": "Contact", "platform": plat, "raw": q_clean}

    # 10. Default / Small Talk / Conversational Knowledge
    return AgentIntent.CHAT, {"message": q_clean}
