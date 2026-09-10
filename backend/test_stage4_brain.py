import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("==================================================")
print("  AURA AI — STAGE 4 CONVERSATIONAL BRAIN TESTS    ")
print("==================================================")

from app.assistant.brain import get_brain
from app.assistant.context import get_context
from app.actions import execute_safe_action
from app.db import init_db, add_action_history, get_action_history

brain = get_brain()

# 1. Normal Greetings (Conversation)
print("\n--- 1. Testing Normal Greetings (Type: conversation) ---")
greetings = [
    ("Hi AURA", "en"),
    ("How are you?", "en"),
    ("কেমন আছো?", "bn"),
    ("नमस्ते AURA", "hi")
]
for g, lang in greetings:
    res = brain.process(g, lang, session_id="test_session_1")
    print(f"User: '{g}' -> Type: {res['type']}, Response: '{res['response']}', Executable: {res['executable']}")
    assert res["type"] == "conversation"
    assert res["executable"] is False
print("✓ Normal Greetings Verified!")

# 2. Informational Questions
print("\n--- 2. Testing Informational Questions (Type: question) ---")
questions = [
    ("What is Python?", "en", "Python"),
    ("Explain recursion simply", "en", "Recursion"),
    ("What is machine learning?", "en", "Machine Learning"),
    ("What is the difference between TCP and UDP?", "en", "Networking")
]
for q, lang, expected_topic in questions:
    res = brain.process(q, lang, session_id="test_session_1")
    print(f"Question: '{q}' -> Type: {res['type']}, Response preview: '{res['response'][:60]}...'")
    assert res["type"] == "question"
    assert res["executable"] is False
print("✓ Informational Questions Answered Naturally!")

# 3. Follow-up Context
print("\n--- 3. Testing Follow-up Context ---")
# First ask about Python
brain.process("What is Python?", "en", session_id="test_session_followup")
# Then ask follow-up
res_followup = brain.process("Is it easy to learn?", "en", session_id="test_session_followup")
print(f"Follow-up: 'Is it easy to learn?' -> Response: '{res_followup['response']}'")
assert res_followup["type"] == "question"
assert "Python" in res_followup["response"]
print("✓ Short-term Context Follow-up Verified!")

# 4. Clarification Flow
print("\n--- 4. Testing Clarification Flow ---")
res_clarify = brain.process("Send a message", "en", session_id="test_session_clarify")
print(f"Input: 'Send a message' -> Type: {res_clarify['type']}, Response: '{res_clarify['response']}'")
assert res_clarify["type"] == "clarification"
assert res_clarify["executable"] is False
assert "WhatsApp" in res_clarify["response"]
print("✓ Clarification Flow Verified!")

# 5. Computer Action Routing
print("\n--- 5. Testing Computer Action Routing ---")
res_action = brain.process("Open YouTube", "en", session_id="test_session_action")
print(f"Action: 'Open YouTube' -> Type: {res_action['type']}, Intent: {res_action['intent']}, Executable: {res_action['executable']}")
assert res_action["type"] == "action"
assert res_action["intent"] == "open_website"
assert res_action["executable"] is True
print("✓ Computer Action Routing Verified!")

# 6. Multi-Platform Communication Routing
print("\n--- 6. Testing Multi-Platform Communication Routing ---")
comm_tests = [
    ("Call Riya from my phone", "en", "call_contact", "phone", "Riya"),
    ("WhatsApp-এ Riya-কে message পাঠাও: আমি ১০ মিনিট পরে আসছি", "bn", "send_text_message", "whatsapp", "Riya"),
    ("Send a Messenger message to Riya: I am on my way", "en", "send_text_message", "messenger", "Riya"),
    ("Instagram-এ Riya-কে message পাঠাও: Hi Riya", "bn", "send_text_message", "instagram", "Riya")
]
for c_text, c_lang, exp_intent, exp_plat, exp_contact in comm_tests:
    res_c = brain.process(c_text, c_lang, session_id="test_session_comm")
    print(f"Comm: '{c_text}' -> Intent: {res_c['intent']}, Plat: {res_c['platform']}, Contact: {res_c['params'].get('contact_name')}")
    assert res_c["type"] == "communication"
    assert res_c["intent"] == exp_intent
    assert res_c["platform"] == exp_plat
    assert res_c["requires_confirmation"] is True
    assert res_c["executable"] is True
print("✓ Multi-Platform Communication Routing Verified!")

# 7. Stale Confirmation Safety Guard
print("\n--- 7. Testing Stale Confirmation & Expiration Guard ---")
ctx = get_context("test_session_ttl")
ctx.ttl_seconds = 1  # 1 second TTL for test
ctx.set_pending_action({"action": "open_website", "params": {"url": "https://www.youtube.com"}})
assert ctx.get_valid_pending_action() is not None
time.sleep(1.1)
assert ctx.get_valid_pending_action() is None, "Stale action should expire after TTL"
print("✓ Stale / Expired Confirmation Guard Verified!")

# 8. Unconfigured Provider Truthful Response (No Fake Success)
print("\n--- 8. Testing Provider Not Configured (Zero Fake Success) ---")
res_exec_wa = execute_safe_action("send_text_message", {"contact_name": "Riya", "message": "Hi", "platform": "whatsapp"})
assert res_exec_wa["success"] is False
assert "not configured" in res_exec_wa["error"]
print("✓ Provider-not-configured truthful error verified!")

print("\n==================================================")
print("  🎉 ALL STAGE 4 CONVERSATIONAL BRAIN TESTS PASS! ")
print("==================================================")
