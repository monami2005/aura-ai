import sys
import os
import io
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Configure UTF-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("==================================================")
print("  AURA AI — STAGE 8 AGENT CORE COMPREHENSIVE TESTS ")
print("==================================================")

from app.agent.models import AgentIntent, ActionRiskLevel
from app.agent.permissions import PermissionManager
from app.agent.intents import detect_structured_intent
from app.agent.verifier import verify_action_execution
from app.agent.file_manager import (
    is_safe_path, safe_create_folder, safe_find_file, safe_read_file,
    safe_summarize_file, safe_rename_file, safe_move_file, safe_delete_file
)
from app.agent.browser import sanitize_url, safe_open_url, safe_browser_search
from app.agent.coding_assistant import analyze_code_or_error
from app.agent.pipeline import get_agent_pipeline
from app.assistant.brain import get_brain
from app.db import init_db, get_action_history

brain = get_brain()
pipeline = get_agent_pipeline()

# 1. Test Multilingual & Mixed-Language Intent Recognition (en, bn, hi, Banglish, Hinglish)
print("\n--- 1. Testing Multilingual & Mixed-Language Intent Recognition ---")
intent_cases = [
    # English
    ("Open Chrome", AgentIntent.OPEN_APPLICATION, "app_name", "chrome"),
    ("Search Google for Python FastAPI tutorial", AgentIntent.WEB_SEARCH, "engine", "google"),
    ("What is this error?", AgentIntent.ANALYZE_ERROR, "focus", "error"),
    ("Find my notes.txt file", AgentIntent.FIND_FILE, "filename", "notes.txt"),
    ("Why is this Python code giving an error?", AgentIntent.HELP_WITH_CODE, None, None),
    # Bengali & Banglish
    ("Google e DAA merge sort search koro", AgentIntent.WEB_SEARCH, "engine", "google"),
    ("Chrome kholo", AgentIntent.OPEN_APPLICATION, "app_name", "chrome"),
    ("Ei error ta bujhiye dao", AgentIntent.ANALYZE_ERROR, "focus", "error"),
    ("Ei error ta ki?", AgentIntent.ANALYZE_ERROR, "focus", "error"),
    ("আমার স্ক্রিনে কী আছে?", AgentIntent.ANALYZE_SCREEN, None, None),
    ("একটি ফোল্ডার বানাও Project_Alpha", AgentIntent.CREATE_FOLDER, "folder_name", "Project_Alpha"),
    # Hindi & Hinglish
    ("Chrome खोलो", AgentIntent.OPEN_APPLICATION, "app_name", "chrome"),
    ("यह एरर क्या है?", AgentIntent.ANALYZE_ERROR, "focus", "error"),
    ("कैलकुलेटर खोलो", AgentIntent.OPEN_APPLICATION, "app_name", "calculator"),
]

for cmd, exp_intent, param_key, exp_param in intent_cases:
    intent, params = detect_structured_intent(cmd)
    print(f"Command: '{cmd}' -> Intent: {intent.value}, Params: {params}")
    assert intent == exp_intent, f"Expected {exp_intent.value} for '{cmd}', got {intent.value}"
    if param_key and exp_param:
        assert exp_param.lower() in str(params.get(param_key, "")).lower()
print("✓ Multilingual, Bengali, Hindi, Banglish & Hinglish Intent Recognition Verified!")

# 2. Test Permission System (SAFE, CONFIRM, HIGH_RISK)
print("\n--- 2. Testing Centralized Permission Manager ---")
risk, conf, reason = PermissionManager.evaluate("find_file", {"filename": "test.txt"})
assert risk == ActionRiskLevel.SAFE and conf is False

risk_browse, conf_browse, _ = PermissionManager.evaluate("web_search_browser", {"query": "AI"})
assert risk_browse in (ActionRiskLevel.SAFE, ActionRiskLevel.CONFIRM)

risk_app, conf_app, _ = PermissionManager.evaluate("open_application", {"app_name": "notepad"})
assert risk_app == ActionRiskLevel.CONFIRM and conf_app is True

risk_del, conf_del, _ = PermissionManager.evaluate("delete_file", {"filepath": "doc.txt"})
assert risk_del == ActionRiskLevel.HIGH_RISK and conf_del is True

risk_msg, conf_msg, _ = PermissionManager.evaluate("send_text_message", {})
assert risk_msg == ActionRiskLevel.HIGH_RISK and conf_msg is True
print("✓ Centralized Permission System (SAFE, CONFIRM, HIGH_RISK) Verified!")

# 3. Test File Operations & Path Traversal Defense
print("\n--- 3. Testing Safe File & Folder Assistant & Path Defense ---")
test_tmp_dir = Path.home() / "Documents" / "AURA_Stage8_Test"
test_tmp_dir.mkdir(parents=True, exist_ok=True)
test_file = test_tmp_dir / "sample_note.txt"
test_file.write_text("AURA AI Stage 8 Agent Core verification file.", encoding="utf-8")

# 3a. Read file
read_res = safe_read_file(str(test_file))
assert read_res["success"] is True
assert "Stage 8" in read_res["content"]

# 3b. Summarize file
sum_res = safe_summarize_file(str(test_file))
assert sum_res["success"] is True
assert sum_res["words"] > 0

# 3c. Find file
find_res = safe_find_file("sample_note.txt", search_root=str(test_tmp_dir))
assert find_res["success"] is True
assert len(find_res["matches"]) >= 1

# 3d. Path traversal defense
bad_safe, _, bad_err = is_safe_path("C:\\Windows\\System32\\cmd.exe")
assert bad_safe is False
assert "forbidden" in bad_err.lower()

bad_safe2, _, bad_err2 = is_safe_path("/etc/passwd")
assert bad_safe2 is False

# Clean up test file safely
del_res = safe_delete_file(str(test_file))
assert del_res["success"] is True
assert not test_file.exists()
shutil.rmtree(test_tmp_dir, ignore_errors=True)
print("✓ Safe File Management & Path Traversal Security Verified!")

# 4. Test Browser Workflows & URL Sanitization
print("\n--- 4. Testing Safe Browser Automation & URL Sanitization ---")
valid_url, clean_url, _ = sanitize_url("https://fastapi.tiangolo.com")
assert valid_url is True and clean_url == "https://fastapi.tiangolo.com"

# Protocol exploit blocking
bad_js, _, err_js = sanitize_url("javascript:alert('exploit')")
assert bad_js is False
assert "Dangerous URL scheme" in err_js

bad_file, _, err_file = sanitize_url("file:///etc/shadow")
assert bad_file is False

# Sensitive banking block
bad_bank, _, err_bank = sanitize_url("https://accounts.google.com/signin")
assert bad_bank is False
assert "blocked" in err_bank.lower()
print("✓ Browser URL Sanitization & Protocol Defense Verified!")

# 5. Test AI Coding Assistant Diagnostics
print("\n--- 5. Testing AI Coding Assistant Diagnostics ---")
code_diag = analyze_code_or_error("Why is this Python code giving an error: IndexError: list index out of range", language="en")
assert "IndexError" in code_diag["problem"]
assert "Why it happens" in code_diag["response"]
assert "Suggested Fix" in code_diag["response"]
assert code_diag["executable"] is False
print("✓ AI Coding Assistant Diagnostics Verified (No auto code execution)!")

# 6. Test Action Verification Engine (Post-execution confirmation)
print("\n--- 6. Testing Action Verification Engine ---")
# 6a. Folder creation verification
verify_folder = verify_action_execution("create_folder", {"folder_name": "Test"}, {"success": True, "path": str(Path.home() / "Documents")})
assert verify_folder.verified is True
assert "Confirmed directory exists" in verify_folder.evidence

# 6b. Fictitious failure detection (never claim success without evidence)
verify_missing_folder = verify_action_execution("create_folder", {"folder_name": "Phantom"}, {"success": True, "path": "Z:\\NonExistent\\Phantom"})
assert verify_missing_folder.verified is False

# 6c. Execution failure
verify_failed = verify_action_execution("open_website", {}, {"success": False, "error": "Browser crashed"})
assert verify_failed.verified is False
print("✓ Action Verification (Never report success without evidence) Verified!")

# 7. Test Scenarios A, B, C, D (Pipeline Integration)
print("\n--- 7. Testing Pipeline Scenarios A, B, C, D ---")
# Test A: "Open Chrome"
res_a = brain.process("Open Chrome", "en")
assert res_a["type"] == "action"
assert res_a["intent"] == "OPEN_APPLICATION"
assert res_a["requires_confirmation"] is True
assert res_a["risk_level"] == "CONFIRM"
assert "chrome" in res_a["target"].lower()
# Simulate user approval execution
exec_a = pipeline.execute_confirmed_action(
    original_command="Open Chrome",
    action=res_a["action"],
    params=res_a["params"],
    language="en"
)
assert exec_a["success"] is True
assert exec_a["verified"] is True
print("✓ Scenario A (Open Chrome Flow) Verified!")

# Test B: "Google e DAA merge sort search koro"
res_b = brain.process("Google e DAA merge sort search koro", "bn")
assert res_b["type"] == "action"
assert res_b["intent"] == "WEB_SEARCH"
assert "merge sort" in str(res_b["params"].get("query", "")).lower()
print("✓ Scenario B (Banglish Web Search Flow) Verified!")

# Test C: "Ei error ta ki?"
with patch("app.screen.service.ScreenAwarenessService.analyze_current_screen") as mock_screen:
    mock_screen.return_value = MagicMock(success=True, summary="Visible terminal shows SyntaxError on line 12.")
    res_c = brain.process("Ei error ta ki?", "bn")
    assert res_c["type"] == "screen_analysis"
    assert res_c["intent"] == "ANALYZE_ERROR"
    assert "appears to be" in res_c["response"] or "Visual Error Diagnostic" in res_c["response"]
    assert res_c["requires_confirmation"] is False
print("✓ Scenario C (Visual Error Diagnostic Flow) Verified!")

# Test D: "Find my notes.txt file"
with patch("app.agent.file_manager.safe_find_file") as mock_find:
    mock_find.return_value = {"success": True, "result": "Found 1 matching file(s): notes.txt", "matches": ["notes.txt"]}
    res_d = brain.process("Find my notes.txt file", "en")
    assert res_d["intent"] == "FIND_FILE"
    assert "notes.txt" in res_d["response"]
print("✓ Scenario D (Safe File Search Flow) Verified!")

# 8. Test Prior Stages Regressions (Stages 2, 3, 4, 5, 6, 7)
print("\n--- 8. Testing Regressions across Stages 2–7 ---")
# Stage 2: OS automation (Screenshot)
res_shot = brain.process("Take screenshot", "en")
assert res_shot["type"] == "action"
assert res_shot["requires_confirmation"] is True

# Stage 3: Communication (Call)
res_call = brain.process("Call Riya from my phone", "en")
assert res_call["type"] == "communication"
assert res_call["requires_confirmation"] is True
assert res_call["risk_level"] == "HIGH_RISK"

# Stage 4: Conversation small talk
res_chat = brain.process("Hello AURA, how are you?", "en")
assert res_chat["type"] == "conversation"
assert res_chat["executable"] is False

# Stage 5: Web real-time query
res_news = brain.process("What is the latest AI news?", "en")
assert res_news["type"] == "web_search"

# Stage 7: Guarded UI Click
res_click = brain.process("Click the submit button", "en")
assert res_click["type"] == "action"
assert res_click["intent"] == "CLICK"
assert res_click["requires_confirmation"] is True

print("✓ Full Regression Test (Stages 2 through 7) Passed!")

# 9. Test SQLite History Extended Schema
print("\n--- 9. Testing Extended SQLite History Logging ---")
hist = get_action_history(limit=5)
assert len(hist) > 0
latest = hist[0]
assert "detected_intent" in latest
assert "execution_status" in latest
assert "language" in latest
print(f"✓ SQLite Audit History Verified! Latest item: {latest['action']} (Status: {latest['execution_status']})")

print("\n==================================================")
print("  🎉 ALL STAGE 8 AGENT CORE TESTS PASSED!         ")
print("==================================================")
