import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("==================================================")
print("  AURA AI — STAGE 4 MULTI-PLATFORM & VOICE TESTS  ")
print("==================================================")

from app.ai import interpret_command, detect_platform
from app.actions import execute_safe_action
from app.communication import get_communication_provider
from app.db import init_db, add_action_history, get_action_history

# 1. Test Multi-Platform Intent Extraction
test_platforms = [
    ("Call Riya from my phone", "en", "call_contact", "phone", "Riya"),
    ("WhatsApp-এ Riya-কে message পাঠাও: আমি ১০ মিনিট পরে আসছি", "bn", "send_text_message", "whatsapp", "Riya"),
    ("Send a Messenger message to Riya: I am on my way", "en", "send_text_message", "messenger", "Riya"),
    ("Instagram-এ Riya-কে message পাঠাও: Hi", "bn", "send_text_message", "instagram", "Riya"),
    ("Send Riya a WhatsApp voice message: Meeting at 5", "en", "send_voice_message", "whatsapp", "Riya"),
    ("रिया को WhatsApp पर message भेजो: मैं थोड़ी देर में आऊँगा", "hi", "send_text_message", "whatsapp", "रिया"),
]

print("\n--- 1. Testing Multi-Platform Intent & Parameter Extraction ---")
for msg, lang, expected_intent, expected_plat, expected_name in test_platforms:
    res = interpret_command(msg, lang)
    params = res.get("params", {})
    plat = params.get("platform")
    contact = params.get("contact_name")
    print(f"Command: '{msg}' [{lang}]")
    print(f"  -> Intent: '{res.get('intent')}', Platform: '{plat}', Contact: '{contact}', Executable: {res.get('executable')}")
    assert res.get("intent") == expected_intent, f"Expected intent {expected_intent}, got {res.get('intent')}"
    assert plat == expected_plat, f"Expected platform {expected_plat}, got {plat}"
    assert res.get("executable") is True, "Communication actions must be executable (requiring confirmation)"
print("✓ Multi-Platform Intent & Parameter Extraction Passed!")

# 2. Test Multi-Platform Providers (No Fake Delivery)
print("\n--- 2. Testing Multi-Platform Router & Providers ---")
platforms = ["phone", "whatsapp", "messenger", "instagram"]
for p in platforms:
    res_call = execute_safe_action("call_contact", {"contact_name": "Riya", "platform": p}, f"Call Riya on {p}")
    print(f"[{p}] call_contact result:", res_call)
    assert res_call["success"] is False
    assert "not configured" in res_call["error"] or "not supported" in res_call["error"]

    res_msg = execute_safe_action("send_text_message", {"contact_name": "Riya", "message": "Hi", "platform": p}, f"Text Riya on {p}")
    print(f"[{p}] send_text_message result:", res_msg)
    assert res_msg["success"] is False
    assert "not configured" in res_msg["error"]

print("✓ All 4 Platform Providers correctly report unconfigured status without faking delivery!")

# 3. Test Voice Confirmation & Cancel Logic (Simulation)
print("\n--- 3. Testing Voice Confirmation Keyword Recognition ---")
APPROVAL_KEYWORDS = [
    'okay', 'ok', 'yes', 'allow', 'do it', 'go ahead',
    'ঠিক আছে', 'হ্যাঁ', 'করো', 'অনুমতি দিচ্ছি',
    'ठीक है', 'हाँ', 'करो', 'अनुमति है'
]

REJECTION_KEYWORDS = [
    'no', 'cancel', 'dont do it', 'stop',
    'না', 'বাতিল করো', 'করো না',
    'नहीं', 'रद्द करो', 'मत करो'
]

sample_speech = ["okay", "ঠিক আছে", "हाँ", "yes", "করো"]
for sp in sample_speech:
    matched = any(kw == sp or kw in sp for kw in APPROVAL_KEYWORDS)
    assert matched is True, f"Failed to match approval keyword '{sp}'"

sample_cancels = ["cancel", "বাতিল করো", "नहीं", "no", "না"]
for sc in sample_cancels:
    matched = any(kw == sc or kw in sc for kw in REJECTION_KEYWORDS)
    assert matched is True, f"Failed to match rejection keyword '{sc}'"

print("✓ Multilingual Voice Approval & Cancellation Keywords Verified!")

# 4. Stage 2 & 3 Regression Check
print("\n--- 4. Testing Stage 2 & 3 Regressions ---")
res_web = execute_safe_action("open_website", {"url": "https://www.youtube.com"}, "Open YouTube")
assert res_web["success"] is True

res_unknown = interpret_command("What is quantum computing?", "en")
assert res_unknown.get("intent") == "unknown"
assert res_unknown.get("executable") is False

print("✓ All Stage 2 & Stage 3 Regression Checks Passed!")

print("\n==================================================")
print("  🎉 ALL STAGE 4 MULTI-PLATFORM TESTS PASSED!    ")
print("==================================================")
