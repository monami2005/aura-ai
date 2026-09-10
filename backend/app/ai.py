import os
import json
import re
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        return None

def detect_platform(text: str) -> str:
    text_lower = text.lower()
    if "whatsapp" in text_lower or "হোয়াটসঅ্যাপ" in text or "व्हाट्सएप" in text:
        return "whatsapp"
    elif "messenger" in text_lower or "মেসেঞ্জার" in text or "मैसेंजर" in text:
        return "messenger"
    elif "instagram" in text_lower or "ইন্সটাগ্রাম" in text or "इंस्टाग्राम" in text or "insta" in text_lower:
        return "instagram"
    return "phone"

def rule_based_fallback(message: str, language: str = "en") -> Dict[str, Any]:
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()
    platform = detect_platform(msg_clean)
    plat_display = platform.capitalize()
    
    # 1. Phone Call Intent
    if (
        ("call" in msg_lower and "code" not in msg_lower and "http" not in msg_lower)
        or "কল করো" in msg_clean
        or "कॉल करो" in msg_clean
    ):
        contact_name = "Contact"
        if "call" in msg_lower:
            parts = re.split(r"call|from my phone|via whatsapp|via messenger|via instagram|on whatsapp|on messenger|on instagram|to|করো|को", msg_clean, flags=re.IGNORECASE)
            for part in parts:
                candidate = part.replace("-কে", "").replace("কে", "").replace("को", "").replace("phone", "").replace("whatsapp", "").replace("messenger", "").replace("instagram", "").strip()
                if candidate and candidate.lower() not in ["please", "now", "a", "the", "my"]:
                    contact_name = candidate.capitalize()
                    break
        elif "কল" in msg_clean:
            contact_name = msg_clean.split("কল")[0].replace("-কে", "").replace("কে", "").replace("ফোন", "").strip().capitalize() or "Contact"
        elif "कॉल" in msg_clean:
            contact_name = msg_clean.split("कॉल")[0].replace("को", "").replace("फ़ोन", "").strip().capitalize() or "Contact"

        if language == "bn" or "করো" in msg_clean:
            exp = f"AURA {plat_display}-এর মাধ্যমে {contact_name}-কে কল করতে প্রস্তুত।"
        elif language == "hi" or "करो" in msg_clean:
            exp = f"AURA {plat_display} के माध्यम से {contact_name} को कॉल करने के लिए तैयार है।"
        else:
            exp = f"AURA wants to call {contact_name} via {plat_display}."

        return {
            "intent": "call_contact",
            "params": {
                "contact_name": contact_name,
                "platform": platform
            },
            "explanation": exp,
            "executable": True
        }

    # 2. Voice Message Intent
    elif "voice message" in msg_lower or "ভয়েস মেসেজ" in msg_clean or "वॉइस मैसेज" in msg_clean:
        contact_name = "Contact"
        content_text = "I will reach shortly."
        if ":" in msg_clean:
            header, content_text = msg_clean.split(":", 1)
            content_text = content_text.strip()
        else:
            header = msg_clean

        parts = re.split(r"send|voice message|via whatsapp|via messenger|via instagram|on whatsapp|on messenger|on instagram|to|পাঠাও|ভেজো|भेजें|-কে|কে|को", header, flags=re.IGNORECASE)
        for part in parts:
            c = part.replace("whatsapp", "").replace("messenger", "").replace("instagram", "").strip()
            if c and c.lower() not in ["a", "the", "please", "me"]:
                contact_name = c.capitalize()
                break

        if language == "bn" or "পাঠাও" in msg_clean:
            exp = f"AURA {plat_display}-এ {contact_name}-কে একটি ভয়েস মেসেজ পাঠাতে চায়: \"{content_text}\""
        elif language == "hi" or "भेजो" in msg_clean:
            exp = f"AURA {plat_display} पर {contact_name} को एक वॉइस मैसेज भेजना चाहता है: \"{content_text}\""
        else:
            exp = f"AURA wants to send a {plat_display} voice message to {contact_name}: \"{content_text}\""

        return {
            "intent": "send_voice_message",
            "params": {
                "contact_name": contact_name,
                "message": content_text,
                "platform": platform
            },
            "explanation": exp,
            "executable": True
        }

    # 3. Text Message Intent
    elif "message" in msg_lower or "মেসেজ" in msg_clean or "संदेश" in msg_clean or "मैसेज" in msg_clean:
        contact_name = "Contact"
        content_text = "Hello from AURA AI."
        if ":" in msg_clean:
            header, content_text = msg_clean.split(":", 1)
            content_text = content_text.strip()
        elif "," in msg_clean:
            header, content_text = msg_clean.split(",", 1)
            content_text = content_text.strip()
        else:
            header = msg_clean

        parts = re.split(r"send a message to|send message to|send whatsapp message to|send messenger message to|send instagram message to|message to|message|পাঠাও|ভেজো|भेजें|-কে|কে|को", header, flags=re.IGNORECASE)
        for part in parts:
            c = part.replace("whatsapp-এ", "").replace("messenger-এ", "").replace("instagram-এ", "").replace("whatsapp", "").replace("messenger", "").replace("instagram", "").strip()
            if c and c.lower() not in ["a", "the", "please", "me", "send", "whatsapp", "messenger", "instagram"]:
                contact_name = c.capitalize()
                break

        if language == "bn" or "পাঠাও" in msg_clean:
            exp = f"AURA {plat_display}-এ {contact_name}-কে মেসেজ পাঠাতে চায়: \"{content_text}\""
        elif language == "hi" or "भेजो" in msg_clean:
            exp = f"AURA {plat_display} पर {contact_name} को संदेश भेजना चाहता है: \"{content_text}\""
        else:
            exp = f"AURA wants to send a {plat_display} message to {contact_name}: \"{content_text}\""

        return {
            "intent": "send_text_message",
            "params": {
                "contact_name": contact_name,
                "message": content_text,
                "platform": platform
            },
            "explanation": exp,
            "executable": True
        }

    # 4. Open Website
    elif "youtube" in msg_lower or "ইউটিউব" in msg_lower or "यूट्यूब" in msg_lower:
        if language == "bn" or "ইউটিউব" in msg_lower:
            exp = "AURA আপনার ব্রাউজারে YouTube খুলবে।"
        elif language == "hi" or "यूट्यूब" in msg_lower:
            exp = "AURA आपके ब्राउज़र में YouTube खोलेगा।"
        else:
            exp = "AURA will open YouTube in your web browser."
        return {
            "intent": "open_website",
            "params": {"url": "https://www.youtube.com"},
            "explanation": exp,
            "executable": True
        }
        
    elif "google" in msg_lower or "গুগল" in msg_lower or "गूगल" in msg_lower:
        if language == "bn":
            exp = "AURA আপনার ব্রাউজারে Google Search খুলবে।"
        elif language == "hi":
            exp = "AURA आपके ब्राउज़र में Google Search खोलेगा।"
        else:
            exp = "AURA will open Google Search in your web browser."
        return {
            "intent": "open_website",
            "params": {"url": "https://www.google.com"},
            "explanation": exp,
            "executable": True
        }
        
    elif "github" in msg_lower or "গিটহাব" in msg_lower:
        return {
            "intent": "open_website",
            "params": {"url": "https://www.github.com"},
            "explanation": "AURA will open GitHub in your web browser.",
            "executable": True
        }
        
    elif msg_lower.startswith("open http") or msg_lower.startswith("open www."):
        url = msg_clean.split(maxsplit=1)[1]
        return {
            "intent": "open_website",
            "params": {"url": url},
            "explanation": f"AURA will open {url} in your default browser.",
            "executable": True
        }
    
    # 5. Take Screenshot
    elif "screenshot" in msg_lower or "স্ক্রিনশট" in msg_lower or "स्क्रीनशॉट" in msg_lower or "screen capture" in msg_lower:
        if language == "bn" or "স্ক্রিনশট" in msg_lower:
            exp = "AURA আপনার স্ক্রিনের একটি স্ক্রিনশট গ্রহণ করবে এবং Pictures ফোল্ডারে সেভ করবে।"
        elif language == "hi" or "स्क्रीनशॉट" in msg_lower:
            exp = "AURA स्क्रीनशॉट लेगा और Pictures फ़ोल्डर में सहेजेगा।"
        else:
            exp = "AURA will capture your primary display and save it to your Pictures directory."
        return {
            "intent": "take_screenshot",
            "params": {},
            "explanation": exp,
            "executable": True
        }
        
    # 6. Create Folder
    elif any(k in msg_lower for k in ["create folder", "create a folder", "make directory", "ফোল্ডার তৈরি", "फ़ोल्डर बना"]):
        parts = re.split(r"create folder named|create a folder named|create folder|create a folder|make directory|ফোল্ডার|फ़ोल्डर", msg_lower, flags=re.IGNORECASE)
        folder_name = parts[-1].strip().strip('"\'').strip("named").strip() if len(parts) > 1 else "Test_Aura_Folder"
        if not folder_name:
            folder_name = "Test_Aura_Folder"
            
        if language == "bn" or "ফোল্ডার" in msg_lower:
            exp = f"AURA Documents-এ '{folder_name}' নামে একটি নতুন ফোল্ডার তৈরি করবে।"
        elif language == "hi" or "फ़ोल्डर" in msg_lower:
            exp = f"AURA Documents में '{folder_name}' नाम से एक नया फ़ोल्डर बनाएगा।"
        else:
            exp = f"AURA will create a new folder named '{folder_name}' in your Documents."
            
        return {
            "intent": "create_folder",
            "params": {"folder_name": folder_name},
            "explanation": exp,
            "executable": True
        }
        
    # 7. Find File
    elif any(k in msg_lower for k in ["find file", "search file", "find", "খুঁজে বের", "फ़ाइल खोज"]):
        parts = re.split(r"find file|search file|find|খুঁজে বের|खोज", msg_lower, flags=re.IGNORECASE)
        filename = parts[-1].strip().strip('"\'') if len(parts) > 1 else "main.py"
        if not filename:
            filename = "main.py"
        return {
            "intent": "find_file",
            "params": {"filename": filename},
            "explanation": f"AURA will search the project workspace for files matching '{filename}'.",
            "executable": True
        }
        
    # 8. Open Application
    elif "calculator" in msg_lower or "ক্যালকুলেটর" in msg_lower or "कैलकुलेटर" in msg_lower:
        return {
            "intent": "open_application",
            "params": {"app_name": "calculator"},
            "explanation": "AURA will launch the Windows Calculator.",
            "executable": True
        }
    elif "notepad" in msg_lower or "নোটপ্যাড" in msg_lower or "नोटपैड" in msg_lower:
        return {
            "intent": "open_application",
            "params": {"app_name": "notepad"},
            "explanation": "AURA will launch Notepad.",
            "executable": True
        }
        
    # Unknown / Conversational
    else:
        if language == "bn" or any("\u0980" <= c <= "\u09FF" for c in msg_clean):
            exp = f"আমি আপনার বার্তা পেয়েছি: '{msg_clean}'। আপনি আমাকে কল করা, WhatsApp/Messenger-এ বার্তা পাঠানো, বা কম্পিউটার নিয়ন্ত্রণের আদেশ দিতে পারেন।"
        elif language == "hi" or any("\u0900" <= c <= "\u097F" for c in msg_clean):
            exp = f"मुझे आपका संदेश मिला: '{msg_clean}'। आप मुझे कॉल करने, WhatsApp/Messenger पर संदेश भेजने या कंप्यूटर नियंत्रण के आदेश दे सकते हैं।"
        else:
            exp = f"I understood your message: '{msg_clean}'. Try giving commands like 'Call Riya from my phone', 'Send WhatsApp message to Riya', 'Open YouTube', or use the Code Analyzer."
            
        return {
            "intent": "unknown",
            "params": {},
            "explanation": exp,
            "executable": False
        }

def interpret_command(message: str, language: str = "en") -> Dict[str, Any]:
    client = get_openai_client()
    if not client:
        return rule_based_fallback(message, language)
        
    system_prompt = """You are AURA AI's intent parsing engine with strict confirmation policies.
Given a user command, parse it into structured JSON with:
1. "intent": one of [
     "call_contact",
     "send_text_message",
     "send_voice_message",
     "open_website",
     "open_application",
     "take_screenshot",
     "create_folder",
     "find_file",
     "unknown"
   ]
2. "params": dictionary with relevant parameters:
   - call_contact: {"contact_name": "Riya", "platform": "phone"|"whatsapp"|"messenger"|"instagram"}
   - send_text_message: {"contact_name": "Riya", "message": "...", "platform": "phone"|"whatsapp"|"messenger"|"instagram"}
   - send_voice_message: {"contact_name": "Riya", "message": "...", "platform": "phone"|"whatsapp"|"messenger"|"instagram"}
   - open_website: {"url": "https://..."}
   - open_application: {"app_name": "calculator"|"notepad"|"paint"}
   - take_screenshot: {}
   - create_folder: {"folder_name": "..."}
   - find_file: {"filename": "..."}
3. "explanation": friendly string explaining what AURA intends to do, clearly stating the recipient, platform, and content preview.
4. "executable": boolean (true for actionable tasks requiring confirmation, false for chit-chat or unknown).

Respond ONLY with valid JSON. Do not include markdown codeblocks or extra text.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Language: {language}\nUser Command: {message}"}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        if "intent" in data and "explanation" in data:
            if "executable" not in data:
                data["executable"] = data.get("intent") != "unknown"
            if "params" not in data:
                data["params"] = {}
            if "platform" not in data["params"] and data.get("intent") in ("call_contact", "send_text_message", "send_voice_message"):
                data["params"]["platform"] = detect_platform(message)
            return data
        return rule_based_fallback(message, language)
    except Exception:
        return rule_based_fallback(message, language)
