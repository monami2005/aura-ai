import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("==================================================")
print("  AURA AI — STAGE 7 SAFE UI INTERACTION TESTS     ")
print("==================================================")

from app.assistant.brain import get_brain
from app.screen.interaction import (
    is_ui_interaction_query,
    extract_click_params,
    extract_type_params,
    extract_key_params,
    extract_scroll_params,
    plan_ui_action,
    SAFE_KEYS,
    DANGEROUS_KEYS
)
from app.actions import execute_safe_action, SAFE_ACTIONS

brain = get_brain()

# 1. Test Multilingual UI Query Detection
print("\n--- 1. Testing Multilingual UI Interaction Intent Detection ---")
test_queries = [
    # English
    ("Click the submit button", True),
    ("Click at (350, 420)", True),
    ("Press Enter", True),
    ("Type 'Hello World'", True),
    ("Scroll down", True),
    # Bengali
    ("Submit বাটনে ক্লিক করো", True),
    ("Enter চাপো", True),
    ("নিচে স্ক্রোল করো", True),
    ("এখানে টাইপ করো 'AURA'", True),
    # Hindi
    ("Submit बटन पर क्लिक करो", True),
    ("Enter दबाओ", True),
    ("नीचे स्क्रॉल करो", True),
    # Non-UI Queries
    ("What is Python?", False),
    ("What is on my screen?", False),
    ("Open YouTube", False),
    ("Call Riya", False),
]

for query, expected in test_queries:
    detected = is_ui_interaction_query(query)
    print(f"Query: '{query}' -> Detected: {detected} (Expected: {expected})")
    assert detected == expected, f"Query '{query}' expected {expected} but got {detected}"
print("✓ Multilingual UI Interaction Detection Verified!")

# 2. Test Parameter Extraction
print("\n--- 2. Testing Parameter Extraction (Coordinates, Keys, Text, Scroll) ---")
# Coordinates click
click_p1 = extract_click_params("Click at (450, 300)")
assert click_p1["mode"] == "coordinates"
assert click_p1["x"] == 450
assert click_p1["y"] == 300

# Element click
click_p2 = extract_click_params("Click the Login button")
assert click_p2["mode"] == "element"
assert "Login button" in click_p2["target"]

# Key params (Valid & Dangerous)
ok, key, _ = extract_key_params("Press Enter")
assert ok is True and key == "enter"

ok_tab, key_tab, _ = extract_key_params("Press Tab")
assert ok_tab is True and key_tab == "tab"

ok_esc, key_esc, _ = extract_key_params("Press Escape")
assert ok_esc is True and key_esc == "escape"

# Dangerous key rejection
bad_ok, bad_key, err = extract_key_params("Press ctrl+alt+del")
assert bad_ok is False
assert "blocked" in err.lower()

# Type text params
type_p = extract_type_params("Type 'Testing AURA AI'")
assert type_p["text"] == "Testing AURA AI"

# Scroll params
scroll_p1 = extract_scroll_params("Scroll down 5 steps")
assert scroll_p1["direction"] == "down"
assert scroll_p1["steps"] == 5

scroll_p2 = extract_scroll_params("উপরে স্ক্রোল করো")
assert scroll_p2["direction"] == "up"
print("✓ Parameter Extraction & Sanitization Verified!")

# 3. Test Brain Routing & Mandatory Confirmation Gate
print("\n--- 3. Testing Brain Routing & Mandatory Confirmation Gate ---")
ui_commands = [
    ("Click the submit button", "en", "click_screen"),
    ("Press Enter", "en", "press_key"),
    ("Type 'Hello AURA'", "en", "type_text"),
    ("Scroll down", "en", "scroll_screen"),
    ("Submit বাটনে ক্লিক করো", "bn", "click_screen"),
    ("Enter চাপো", "bn", "press_key"),
    ("Submit बटन पर क्लिक करो", "hi", "click_screen"),
]

for cmd, lang, expected_intent in ui_commands:
    res = brain.process(cmd, lang)
    print(f"Command: '{cmd}' [{lang}] -> Intent: '{res.get('intent')}', Confirmation: {res.get('requires_confirmation')}")
    assert res["type"] == "action"
    assert res["intent"] == expected_intent
    assert res["requires_confirmation"] is True, "Security Violation: UI interaction must require explicit confirmation!"
    assert res["executable"] is True
    assert len(res["response"]) > 0
print("✓ Mandatory Confirmation Gate Verified across all UI interactions!")

# 4. Test Safe Action Dispatcher & Simulation Mode in actions.py
print("\n--- 4. Testing Safe Action Dispatcher (app/actions.py) ---")
# 4a. Click Action
res_click_coords = execute_safe_action("click_screen", {"x": 200, "y": 150, "target": "(200, 150)", "simulate": True})
assert res_click_coords["success"] is True
assert "Simulated click" in res_click_coords["result"]

# Click bounds validation
res_bad_click = execute_safe_action("click_screen", {"x": -50, "y": 100})
assert res_bad_click["success"] is False
assert "Invalid click coordinates" in res_bad_click["error"]

# 4b. Type Action
res_type = execute_safe_action("type_text", {"text": "AURA automated test", "simulate": True})
assert res_type["success"] is True
assert "AURA automated test" in res_type["result"]

# Text length validation
res_long_type = execute_safe_action("type_text", {"text": "A" * 600})
assert res_long_type["success"] is False
assert "exceeds maximum safe length" in res_long_type["error"]

# 4c. Key Press Action
res_press = execute_safe_action("press_key", {"key": "enter", "simulate": True})
assert res_press["success"] is True
assert "ENTER" in res_press["result"]

# Blocked key rejection in action executor
res_bad_press = execute_safe_action("press_key", {"key": "ctrl+alt+del"})
assert res_bad_press["success"] is False
assert "not allowed" in res_bad_press["error"]

# 4d. Scroll Action
res_scroll = execute_safe_action("scroll_screen", {"direction": "down", "steps": 4, "simulate": True})
assert res_scroll["success"] is True
assert "Scrolled screen down" in res_scroll["result"]

res_bad_scroll = execute_safe_action("scroll_screen", {"direction": "sideways", "steps": 5})
assert res_bad_scroll["success"] is False
print("✓ Action Dispatcher Bounds, Sanitization & Simulation Verified!")

# 5. Prior Stages Regressions (Stages 2, 3, 4, 5, 6)
print("\n--- 5. Testing Prior Stages Regressions ---")
# Stage 2: OS Action
res_s2 = brain.process("Open YouTube", "en")
assert res_s2["type"] == "action"
assert res_s2["intent"] == "open_website"

# Stage 3: Communication
res_s3 = brain.process("Call Riya from my phone", "en")
assert res_s3["type"] == "communication"
assert res_s3["requires_confirmation"] is True

# Stage 4: Conversation
res_s4 = brain.process("Hello AURA", "en")
assert res_s4["type"] == "conversation"
assert res_s4["executable"] is False

# Stage 5: Web Query
res_s5 = brain.process("What is the latest AI news?", "en")
assert res_s5["type"] == "web_search"
assert res_s5["executable"] is False

# Stage 6: Passive Screen Query (Must NOT trigger UI interaction)
with patch("app.screen.service.ScreenAwarenessService.analyze_current_screen") as mock_screen:
    mock_screen.return_value = MagicMock(summary="Screen contains a browser window.")
    res_s6 = brain.process("What is on my screen?", "en")
    assert res_s6["type"] == "screen_analysis"
    assert res_s6["executable"] is False
    assert "Screen contains a browser window" in res_s6["response"]

print("✓ All Stages (2, 3, 4, 5, 6) Regressions Passed Successfully!")

print("\n==================================================")
print("  🎉 STAGE 7 SAFE UI INTERACTION TESTS PASSED!    ")
print("==================================================")
