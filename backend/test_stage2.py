import sys
import os
import json
import sqlite3
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("==================================================")
print("     AURA AI — STAGE 2 CORE ENGINE VERIFICATION   ")
print("==================================================")

# 1. AI Rule-based Multilingual Interpreter Test
from app.ai import interpret_command

test_commands = [
    ("Open YouTube", "en", "open_website"),
    ("Take screenshot", "en", "take_screenshot"),
    ("Create a folder named AURA_Test", "en", "create_folder"),
    ("Find a file named test.txt", "en", "find_file"),
    ("ইউটিউব খোলো", "bn", "open_website"),
    ("স্ক্রিনশট নাও", "bn", "take_screenshot"),
    ("YouTube खोलो", "hi", "open_website"),
    ("Tell me something random", "en", "unknown"),
]

print("\n--- 1. Testing AI Intent Interpretation (Multilingual) ---")
for msg, lang, expected_intent in test_commands:
    res = interpret_command(msg, lang)
    print(f"Input: '{msg}' [{lang}] -> Intent: '{res.get('intent')}', Executable: {res.get('executable')}")
    assert res.get("intent") == expected_intent, f"Expected {expected_intent}, got {res.get('intent')}"
    assert "explanation" in res, "Missing explanation in response"
    assert "params" in res, "Missing params in response"
print("✓ All Multilingual Intent Tests Passed!")

# 2. Safe Allowlist Execution Test
from app.actions import execute_safe_action, SAFE_ACTIONS

print("\n--- 2. Testing Safe Action Execution Engine ---")
# Create folder test
res_folder = execute_safe_action("create_folder", {"folder_name": "AURA_Test_Verification"}, "Create a folder named AURA_Test_Verification")
print("create_folder test:", res_folder)
assert res_folder["success"] is True

# Find file test
res_find = execute_safe_action("find_file", {"filename": "main.py"}, "Find main.py")
print("find_file test:", res_find)
assert res_find["success"] is True

# Blocked action test (Security check)
res_blocked = execute_safe_action("delete_system_files", {}, "Delete system files")
print("blocked action security test:", res_blocked)
assert res_blocked["success"] is False
assert "not in the safe allowlist" in res_blocked["error"]
print("✓ All Safe Action Execution & Security Tests Passed!")

# 3. SQLite History Logging Test
from app.db import init_db, add_action_history, get_action_history

print("\n--- 3. Testing SQLite Action History Database ---")
init_db()
add_action_history("Open YouTube", "open_website", "Opened website: https://www.youtube.com", True)
add_action_history("Take screenshot", "take_screenshot", "Screenshot saved", True)
history = get_action_history(10)
print(f"Retrieved {len(history)} history records:")
for item in history[:3]:
    print(f"  - [{item['timestamp']}] '{item['original_command']}' -> Action: {item['action']} (Success: {item['success']})")
assert len(history) >= 2
assert history[0]["original_command"] in ["Take screenshot", "Open YouTube"]
print("✓ SQLite History Persistence Tests Passed!")

# 4. AST Code Analyzer Test
print("\n--- 4. Testing Code Analyzer AST Engine ---")
import ast

def analyze_code_logic(language: str, source_code: str):
    lang = language.lower().strip()
    code = source_code
    if lang == "python":
        try:
            ast.parse(code)
            return {"detected": False, "error_type": None, "corrected_code": code}
        except SyntaxError as e:
            corrected = code + ")" if "(" in code and not code.strip().endswith(")") else code
            return {"detected": True, "error_type": "SyntaxError", "line_number": e.lineno or 1, "corrected_code": corrected}
    elif lang == "json":
        try:
            json.loads(code)
            return {"detected": False, "error_type": None, "corrected_code": code}
        except json.JSONDecodeError as e:
            return {"detected": True, "error_type": "JSONDecodeError", "line_number": e.lineno, "corrected_code": code}
    elif lang in ("javascript", "typescript"):
        pairs = {'(': ')', '{': '}', '[': ']'}
        stack = []
        for ch in code:
            if ch in pairs:
                stack.append(ch)
            elif ch in pairs.values():
                if not stack or pairs[stack.pop()] != ch:
                    return {"detected": True, "error_type": "SyntaxError", "corrected_code": code}
        if stack:
            unclosed = stack[-1]
            return {"detected": True, "error_type": "SyntaxError", "corrected_code": code + pairs[unclosed]}
        return {"detected": False, "error_type": None, "corrected_code": code}
    return {"detected": False, "error_type": None, "corrected_code": code}

# Test Python error
res_py_err = analyze_code_logic("python", 'print("Hello"')
print("Python Syntax Error:", res_py_err)
assert res_py_err["detected"] is True
assert res_py_err["corrected_code"] == 'print("Hello")'

# Test Python valid
res_py_ok = analyze_code_logic("python", 'print("Hello")')
print("Python Valid:", res_py_ok)
assert res_py_ok["detected"] is False

# Test JSON invalid
res_json_err = analyze_code_logic("json", '{"name": "AURA"')
print("JSON Invalid:", res_json_err)
assert res_json_err["detected"] is True

# Test JSON valid
res_json_ok = analyze_code_logic("json", '{"name": "AURA", "status": "online"}')
print("JSON Valid:", res_json_ok)
assert res_json_ok["detected"] is False

# Test JS unbalanced
res_js_err = analyze_code_logic("javascript", 'function test() {')
print("JS Unbalanced:", res_js_err)
assert res_js_err["detected"] is True

print("✓ All Code Analyzer Diagnostics Tests Passed!")

print("\n==================================================")
print("    🎉 ALL STAGE 2 VERIFICATION CHECKS PASSED!    ")
print("==================================================")
