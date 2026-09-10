import json
import re
from typing import Dict, Any, Optional
from .context import get_context
from ..ai import get_openai_client, detect_platform
from ..web import get_web_service
from ..screen import get_screen_service
from ..screen.interaction import is_ui_interaction_query, plan_ui_action

def natural_offline_brain(message: str, language: str = "en", session_id: str = "default") -> Dict[str, Any]:
    context = get_context(session_id)
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()
    
    recent_topic = context.last_topic or ""
    web_service = get_web_service()
    screen_service = get_screen_service()

    # 1. UI Interaction & Desktop Automation (Stage 7 - Safe, Guarded Input)
    if is_ui_interaction_query(msg_clean) and not any(k in msg_lower for k in ["folder", "screenshot", "youtube", "calculator"]):
        action_plan = plan_ui_action(msg_clean, language)
        if action_plan.get("executable"):
            context.set_pending_action(action_plan)
        return action_plan

    # 2. Screen Understanding & Passive Awareness (Type: screen_analysis)
    if screen_service.is_screen_query(msg_clean) and not any(k in msg_lower for k in ["folder", "screenshot", "youtube", "calculator"]):
        screen_res = screen_service.analyze_current_screen(question=msg_clean, language=language)
        context.add_turn(msg_clean, screen_res.summary, topic="screen_analysis")
        return {
            "type": "screen_analysis",
            "intent": "analyze_screen",
            "platform": None,
            "params": {"question": msg_clean},
            "sources": [],
            "requires_confirmation": False,
            "response": screen_res.summary,
            "executable": False
        }

    # 2. Real-time / Current Information Detection (Type: web_search)
    if web_service.is_realtime_query(msg_clean) and not any(k in msg_lower for k in ["call", "message", "folder", "screenshot", "youtube", "calculator"]):
        web_res = web_service.query(msg_clean, language)
        sources_data = [s.model_dump() for s in web_res.sources]
        context.add_turn(msg_clean, web_res.answer, topic="web_news")
        return {
            "type": "web_search",
            "intent": "web_intelligence",
            "platform": None,
            "params": {"query": msg_clean},
            "sources": sources_data,
            "requires_confirmation": False,
            "response": web_res.answer,
            "executable": False
        }

    # 3. Greetings & Small Talk (Type: conversation)
    greetings_en = ["hi aura", "hello aura", "hey aura", "hi", "hello", "hey", "good morning", "good evening", "how are you", "who are you"]
    greetings_bn = ["নমস্কার", "হ্যালো", "কেমন আছো", "তুমি কেমন আছো", "কেমন আছেন", "কেমন আছিস"]
    greetings_hi = ["नमस्ते", "हेलो", "कैसे हो", "आप कैसे हैं", "कैसी हो"]

    if any(g == msg_lower for g in greetings_en) or any(g in msg_clean for g in greetings_bn) or any(g in msg_clean for g in greetings_hi):
        if "how are you" in msg_lower or "কেমন আছো" in msg_clean or "कैसे हो" in msg_clean:
            if language == "bn":
                ans = "আমি ভালো আছি! আমি আপনাকে কীভাবে সাহায্য করতে পারি?"
            elif language == "hi":
                ans = "मैं ठीक हूँ! मैं आपकी क्या मदद कर सकता हूँ?"
            else:
                ans = "I'm doing well! What can I help you with today?"
        elif "who are you" in msg_lower:
            ans = "I am AURA AI, your multilingual voice & personal desktop assistant."
        else:
            if language == "bn":
                ans = "নমস্কার! আমি অরা এআই (AURA AI)। আমি কীভাবে সাহায্য করতে পারি?"
            elif language == "hi":
                ans = "नमस्ते! मैं AURA AI हूँ। मैं आपकी क्या सहायता कर सकता हूँ?"
            else:
                ans = "Hi! How can I help you today?"
                
        context.add_turn(msg_clean, ans, topic="greeting")
        return {
            "type": "conversation",
            "intent": "chat",
            "platform": None,
            "params": {},
            "sources": [],
            "requires_confirmation": False,
            "response": ans,
            "executable": False
        }

    # 4. Informational Questions & Knowledge (Type: question / follow_up)
    if (
        msg_lower.startswith("what is") or msg_lower.startswith("explain") or msg_lower.startswith("how does")
        or msg_lower.startswith("why does") or msg_lower.startswith("tell me about") or msg_lower.startswith("is it")
        or "কি" in msg_clean or "কী" in msg_clean or "কেন" in msg_clean or "কীভাবে" in msg_clean
        or "क्या है" in msg_clean or "कैसे" in msg_clean or "बताओ" in msg_clean
    ):
        topic = recent_topic
        if "python" in msg_lower:
            topic = "Python"
            ans = "Python is a high-level, interpreted programming language known for its clean syntax, readability, and versatile libraries in AI, web development, and data science."
        elif "japan" in msg_lower and "capital" in msg_lower:
            topic = "Geography"
            ans = "The capital of Japan is Tokyo."
        elif "recursion" in msg_lower:
            topic = "Recursion"
            ans = "Recursion is a programming concept where a function calls itself to solve a smaller subproblem until reaching a base condition that stops the calls."
        elif "machine learning" in msg_lower:
            topic = "Machine Learning"
            ans = "Machine Learning is a subset of AI where algorithms learn patterns from data and improve their performance over time without being explicitly programmed."
        elif "tcp" in msg_lower and "udp" in msg_lower:
            topic = "Networking"
            ans = "TCP is a connection-oriented, reliable protocol that guarantees packet delivery in order. UDP is a connectionless, lightweight protocol optimized for speed (like video streaming) without delivery guarantees."
        elif "binary search" in msg_lower:
            topic = "Algorithms"
            ans = "Binary search is an efficient search algorithm on sorted arrays that repeatedly divides the search interval in half with O(log n) time complexity."
        elif ("is it easy" in msg_lower or "is it hard" in msg_lower or "is it good" in msg_lower) and recent_topic:
            ans = f"Yes, {recent_topic} is generally considered very beginner-friendly and has a large, supportive community."
        elif ("which one" in msg_lower or "explain the second" in msg_lower) and recent_topic:
            ans = f"Based on the previously retrieved updates about {recent_topic}, the most significant breakthrough focuses on multimodal reasoning efficiency."
        else:
            if language == "bn":
                ans = f"আমি আপনার প্রশ্ন বুঝতে পেরেছি: '{msg_clean}'। কোড বা প্রযুক্তিগত বিষয় সম্পর্কে আপনি আমাকে জিজ্ঞাসা করতে পারেন।"
            elif language == "hi":
                ans = f"मुझे आपका प्रश्न समझ आया: '{msg_clean}'। आप मुझसे कोडिंग या तकनीकी विषयों के बारे में पूछ सकते हैं।"
            else:
                ans = f"That's an interesting question about '{msg_clean}'. I can help explain programming, architecture, algorithms, and system operations."

        context.add_turn(msg_clean, ans, topic=topic)
        return {
            "type": "question",
            "intent": "question_answering",
            "platform": None,
            "params": {"topic": topic},
            "sources": [],
            "requires_confirmation": False,
            "response": ans,
            "executable": False
        }

    # 5. Clarification Flow
    if msg_lower in ["send message", "send a message", "message pathao", "মেসেজ পাঠাও", "संदेश भेजो"]:
        ans = "Sure. Which platform should I use — WhatsApp, Messenger, or Instagram?"
        return {
            "type": "clarification",
            "intent": "clarify_platform",
            "platform": None,
            "params": {},
            "sources": [],
            "requires_confirmation": False,
            "response": ans,
            "executable": False
        }

    # 6. Action & Communication Routing
    platform = detect_platform(msg_clean)
    plat_display = platform.capitalize()

    # Call Intent
    if ("call" in msg_lower and "code" not in msg_lower) or "কল করো" in msg_clean or "कॉल करो" in msg_clean:
        contact_name = "Contact"
        parts = re.split(r"call|from my phone|via whatsapp|via messenger|via instagram|on whatsapp|on messenger|on instagram|to|করো|को", msg_clean, flags=re.IGNORECASE)
        for part in parts:
            candidate = part.replace("-কে", "").replace("কে", "").replace("को", "").replace("phone", "").replace("whatsapp", "").replace("messenger", "").replace("instagram", "").strip()
            if candidate and candidate.lower() not in ["please", "now", "a", "the", "my"]:
                contact_name = candidate.capitalize()
                break
                
        if language == "bn" or "করো" in msg_clean:
            exp = f"AURA {plat_display}-এর মাধ্যমে {contact_name}-কে কল করতে প্রস্তুত।"
        elif language == "hi" or "करो" in msg_clean:
            exp = f"AURA {plat_display} के माध्यम से {contact_name} को कॉल करने के लिए तैयार है।"
        else:
            exp = f"AURA wants to call {contact_name} via {plat_display}."

        action_dict = {
            "type": "communication",
            "intent": "call_contact",
            "platform": platform,
            "params": {"contact_name": contact_name, "platform": platform},
            "sources": [],
            "requires_confirmation": True,
            "response": exp,
            "executable": True
        }
        context.set_pending_action(action_dict)
        return action_dict

    # Text / Voice Message Intent
    elif "voice message" in msg_lower or "ভয়েস মেসেজ" in msg_clean or "वॉइस মেসেজ" in msg_clean:
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

        action_dict = {
            "type": "communication",
            "intent": "send_voice_message",
            "platform": platform,
            "params": {"contact_name": contact_name, "message": content_text, "platform": platform},
            "sources": [],
            "requires_confirmation": True,
            "response": exp,
            "executable": True
        }
        context.set_pending_action(action_dict)
        return action_dict

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

        action_dict = {
            "type": "communication",
            "intent": "send_text_message",
            "platform": platform,
            "params": {"contact_name": contact_name, "message": content_text, "platform": platform},
            "sources": [],
            "requires_confirmation": True,
            "response": exp,
            "executable": True
        }
        context.set_pending_action(action_dict)
        return action_dict

    # Safe System Computer Actions
    elif "youtube" in msg_lower or "ইউটিউব" in msg_lower or "यूट्यूब" in msg_lower:
        exp = "Sure, I'll open YouTube in your browser." if language == "en" else "AURA আপনার ব্রাউজারে YouTube খুলবে।" if language == "bn" else "AURA आपके ब्राउज़र में YouTube खोलेगा।"
        action_dict = {
            "type": "action",
            "intent": "open_website",
            "platform": None,
            "params": {"url": "https://www.youtube.com"},
            "sources": [],
            "requires_confirmation": True,
            "response": exp,
            "executable": True
        }
        context.set_pending_action(action_dict)
        return action_dict

    elif "screenshot" in msg_lower or "স্ক্রিনশট" in msg_lower or "स्क्रीनशॉट" in msg_lower:
        exp = "I'm ready to capture your screen and save it to Pictures." if language == "en" else "AURA আপনার স্ক্রিনের একটি স্ক্রিনশট গ্রহণ করবে।"
        action_dict = {
            "type": "action",
            "intent": "take_screenshot",
            "platform": None,
            "params": {},
            "sources": [],
            "requires_confirmation": True,
            "response": exp,
            "executable": True
        }
        context.set_pending_action(action_dict)
        return action_dict

    elif any(k in msg_lower for k in ["create folder", "create a folder", "make directory", "ফোল্ডার তৈরি", "फ़ोल्डर बना"]):
        parts = re.split(r"create folder named|create a folder named|create folder|create a folder|make directory|ফোল্ডার|फ़োल्डर", msg_lower, flags=re.IGNORECASE)
        folder_name = parts[-1].strip().strip('"\'').strip("named").strip() if len(parts) > 1 else "New_Aura_Folder"
        exp = f"I'll create a new folder named '{folder_name}' in your Documents."
        action_dict = {
            "type": "action",
            "intent": "create_folder",
            "platform": None,
            "params": {"folder_name": folder_name or "New_Aura_Folder"},
            "sources": [],
            "requires_confirmation": True,
            "response": exp,
            "executable": True
        }
        context.set_pending_action(action_dict)
        return action_dict

    elif any(k in msg_lower for k in ["find file", "search file", "find", "খুঁজে বের", "फ़ाइल खोज"]):
        parts = re.split(r"find file|search file|find|খুঁজে বের|खोज", msg_lower, flags=re.IGNORECASE)
        filename = parts[-1].strip().strip('"\'') if len(parts) > 1 else "main.py"
        exp = f"I will search the project workspace for '{filename or 'main.py'}'."
        action_dict = {
            "type": "action",
            "intent": "find_file",
            "platform": None,
            "params": {"filename": filename or "main.py"},
            "sources": [],
            "requires_confirmation": True,
            "response": exp,
            "executable": True
        }
        context.set_pending_action(action_dict)
        return action_dict

    elif "calculator" in msg_lower:
        exp = "I will launch the Windows Calculator."
        action_dict = {
            "type": "action",
            "intent": "open_application",
            "platform": None,
            "params": {"app_name": "calculator"},
            "sources": [],
            "requires_confirmation": True,
            "response": exp,
            "executable": True
        }
        context.set_pending_action(action_dict)
        return action_dict

    # Default Conversational
    else:
        ans = f"I understood: \"{msg_clean}\". You can ask about current news, inspect your screen, or command me to open apps and message contacts."
        context.add_turn(msg_clean, ans)
        return {
            "type": "conversation",
            "intent": "unknown",
            "platform": None,
            "params": {},
            "sources": [],
            "requires_confirmation": False,
            "response": ans,
            "executable": False
        }


class AuraBrain:
    def process(self, message: str, language: str = "en", session_id: str = "default") -> Dict[str, Any]:
        from ..agent import get_agent_pipeline
        pipeline = get_agent_pipeline()
        return pipeline.process(message, language, session_id)


_brain = AuraBrain()

def get_brain() -> AuraBrain:
    return _brain
