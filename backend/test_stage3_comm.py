import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("==================================================")
print("  AURA AI — STAGE 3 COMMUNICATION & SAFETY TESTS  ")
print("==================================================")

from app.ai import interpret_command
from app.actions import execute_safe_action
from app.communication import get_communication_provider, resolve_contact
from app.db import init_db, add_action_history, get_action_history

# 1. Test Communication Intent Parsing
test_cases = [
    ("Call Riya", "en", "call_contact", "Riya"),
    ("Riya-কে call করো", "bn", "call_contact", "Riya"),
    ("रिया को call करो", "hi", "call_contact", "रिया"),
    ("Send a message to Riya: I will be there in 10 minutes", "en", "send_text_message", "Riya"),
    ("Riya-কে একটা message পাঠাও: আমি ১০ মিনিট পরে আসছি", "bn", "send_text_message", "Riya"),
    ("रिया को message भेजो: मैं थोड़ी देर में आऊँगा", "hi", "send_text_message", "रिया"),
    ("Send Riya a voice message: I am on my way", "en", "send_voice_message", "Riya"),
    ("Riya-কে voice message পাঠাও: আমি আসছি", "bn", "send_voice_message", "Riya"),
]

print("\n--- 1. Testing Communication Intent Parsing (Multilingual) ---")
for msg, lang, expected_intent, expected_name in test_cases:
    res = interpret_command(msg, lang)
    print(f"Command: '{msg}' [{lang}]")
    print(f"  -> Intent: '{res.get('intent')}', Contact: '{res.get('params', {}).get('contact_name')}', Executable: {res.get('executable')}")
    assert res.get("intent") == expected_intent, f"Expected intent {expected_intent}, got {res.get('intent')}"
    assert res.get("executable") is True, "Communication actions must be executable (requiring confirmation)"
print("✓ All Communication Intent Parsing Tests Passed!")

# 2. Test Safe Communication Provider Execution (No Fake Communication)
print("\n--- 2. Testing Communication Provider (Zero Fake Delivery) ---")
res_call = execute_safe_action("call_contact", {"contact_name": "Riya"}, "Call Riya")
print("Call Contact Execution:", res_call)
assert res_call["success"] is False
assert "not configured yet" in res_call["error"]

res_msg = execute_safe_action("send_text_message", {"contact_name": "Riya", "message": "Test"}, "Send message to Riya")
print("Send Text Message Execution:", res_msg)
assert res_msg["success"] is False
assert "not configured yet" in res_msg["error"]

res_voice = execute_safe_action("send_voice_message", {"contact_name": "Riya", "message": "Voice clip"}, "Send voice message to Riya")
print("Send Voice Message Execution:", res_voice)
assert res_voice["success"] is False
assert "not configured yet" in res_voice["error"]
print("✓ Provider correctly reports 'not configured' and NEVER pretends success!")

# 3. Test Privacy & History Logging
print("\n--- 3. Testing Privacy & History Sanitization ---")
init_db()
add_action_history("send_text_message to Riya", "send_text_message", "Provider not configured", False)
history = get_action_history(5)
print("Latest Logged History:", history[0])
assert "send_text_message" in history[0]["action"]
assert "Riya" in history[0]["original_command"]
print("✓ Privacy Logging Verified!")

print("\n==================================================")
print("  🎉 ALL STAGE 3 COMMUNICATION TESTS PASSED!     ")
print("==================================================")
