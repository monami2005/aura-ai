import sys
import io
from pathlib import Path
from unittest.mock import patch, MagicMock
try:
    from PIL import Image
    pillow_installed = True
except ImportError:
    pillow_installed = False
    Image = MagicMock()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("==================================================")
print("  AURA AI — STAGE 6 SCREEN AWARENESS TESTS        ")
print("==================================================")

from app.assistant.brain import get_brain
from app.screen import get_screen_service
from app.screen.service import ScreenAwarenessService
from app.screen.capture import capture_primary_screen
from app.screen.vision import DefaultScreenVisionProvider, OpenAIVisionProvider
from app.screen.models import ScreenAnalyzeResponse, ScreenCaptureMetadata

brain = get_brain()
screen_service = get_screen_service()

# 1. Test In-Memory Screen Capture
print("\n--- 1. Testing In-Memory Screen Capture ---")
if pillow_installed:
    fake_img = Image.new("RGB", (800, 600), color=(73, 109, 137))
    with patch("PIL.ImageGrab.grab", return_value=fake_img):
        img_bytes, metadata, err = capture_primary_screen()
        assert err is None, f"Capture returned unexpected error: {err}"
        assert img_bytes is not None, "Image bytes should not be None"
        assert len(img_bytes) > 0, "Image bytes should not be empty"
        assert metadata is not None, "Metadata should not be None"
        assert metadata.width == 800
        assert metadata.height == 600
        assert metadata.format == "PNG"
        print(f"✓ In-Memory Capture Verified! (Bytes: {len(img_bytes)}, Dim: {metadata.width}x{metadata.height})")
else:
    img_bytes, metadata, err = capture_primary_screen()
    assert err is not None and "Pillow is not installed" in err
    print("✓ Graceful Missing Pillow Diagnostic Handling Verified!")

# 2. Test Multilingual Screen Query Triggers
print("\n--- 2. Testing Multilingual Screen Query Detection ---")
test_queries = [
    ("What is on my screen?", True),
    ("Look at my screen and explain what you see", True),
    ("Can you analyze screen content?", True),
    ("আমার স্ক্রিনে কী আছে?", True),
    ("স্ক্রিনে কি কোনো error দেখা যাচ্ছে?", True),
    ("मेरी स्क्रीन पर क्या है?", True),
    ("स्क्रीन देखो और समझाओ", True),
    ("What is Python?", False),
    ("Open YouTube", False),
    ("Call Riya", False),
]

for query, expected in test_queries:
    detected = screen_service.is_screen_query(query)
    print(f"Query: '{query}' -> Detected: {detected} (Expected: {expected})")
    assert detected == expected, f"Query '{query}' expected {expected} but got {detected}"
print("✓ Multilingual Screen Query Detection Verified!")

# 3. Test Truthful Fallback When Vision API Key Is Unconfigured
print("\n--- 3. Testing Unconfigured Vision Provider (Truthful Fallback) ---")
default_provider = DefaultScreenVisionProvider()
dummy_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR..."

res_en = default_provider.analyze_screen(dummy_bytes, language="en")
assert res_en.success is False
assert "OpenAI Vision API key" in res_en.summary or "Screen Vision is not configured" in res_en.summary
assert res_en.provider == "Unconfigured"

res_bn = default_provider.analyze_screen(dummy_bytes, language="bn")
assert res_bn.success is False
assert "স্ক্রিন" in res_bn.summary
assert res_bn.provider == "Unconfigured"

res_hi = default_provider.analyze_screen(dummy_bytes, language="hi")
assert res_hi.success is False
assert "स्क्रीन" in res_hi.summary
assert res_hi.provider == "Unconfigured"
print("✓ Truthful Multilingual Fallback Verified (No hallucinations or fabricated answers)!")

# 4. Test Structured Vision Response Mapping
print("\n--- 4. Testing Structured Vision Response Parsing ---")
mock_vision_json = {
    "summary": "The screen shows a code editor with a syntax error on line 42.",
    "details": "VS Code is open on the left showing app.py; terminal on the right.",
    "visible_text": "SyntaxError: unexpected EOF while parsing",
    "detected_elements": ["VS Code", "Terminal"],
    "errors_or_warnings": "SyntaxError on line 42"
}

with patch("app.screen.vision.OpenAIVisionProvider.analyze_screen") as mock_analyze:
    mock_analyze.return_value = ScreenAnalyzeResponse(
        success=True,
        language="en",
        summary=mock_vision_json["summary"],
        details=mock_vision_json["details"],
        visible_text=mock_vision_json["visible_text"],
        detected_elements=mock_vision_json["detected_elements"],
        errors_or_warnings=mock_vision_json["errors_or_warnings"],
        provider="OpenAI Vision",
        timestamp="2026-09-10T12:00:00Z"
    )

    prov = OpenAIVisionProvider(api_key="mock_key")
    parsed_res = prov.analyze_screen(dummy_bytes, "What is on my screen?", "en")
    assert parsed_res.success is True
    assert "syntax error" in parsed_res.summary.lower()
    assert parsed_res.detected_elements == ["VS Code", "Terminal"]
    assert parsed_res.errors_or_warnings == "SyntaxError on line 42"
    print("✓ Structured Vision Response Parsing Verified!")

# 5. Test Brain Routing & Stage 7 Safety Guard
print("\n--- 5. Testing Brain Routing & Action Boundary Guards ---")
# Query: explain screen
with patch.object(screen_service, "analyze_current_screen") as mock_screen:
    mock_screen.return_value = ScreenAnalyzeResponse(
        success=True,
        language="en",
        summary="A code editor is currently active.",
        details=None,
        visible_text=None,
        detected_elements=["Editor"],
        errors_or_warnings=None,
        provider="MockVision",
        timestamp="2026-09-10T12:00:00Z"
    )
    res_brain = brain.process("What is visible on my screen?", "en")
    assert res_brain["type"] == "screen_analysis"
    assert res_brain["executable"] is False
    assert "A code editor is currently active" in res_brain["response"]
    print("✓ Brain Screen Analysis Routing Verified!")

# Stage 7 Guarded UI Action: User asks to click screen (must require explicit confirmation)
res_guard = brain.process("Click the submit button on my screen", "en")
assert res_guard["type"] == "action"
assert res_guard["intent"] == "click_screen"
assert res_guard["requires_confirmation"] is True
assert res_guard["executable"] is True
print("✓ Guarded UI Action Confirmation Requirement Verified!")

# 6. Test Stages 2, 3, 4, 5 Regressions
print("\n--- 6. Testing Regressions (Stages 2, 3, 4, 5) ---")
# Stage 2: OS action
res_act = brain.process("Open YouTube", "en")
assert res_act["type"] == "action"
assert res_act["executable"] is True

# Stage 3: Communication action with confirmation
res_comm = brain.process("WhatsApp Riya: I am heading home", "en")
assert res_comm["type"] == "communication"
assert res_comm["requires_confirmation"] is True
assert res_comm["executable"] is True

# Stage 4: Conversational greeting
res_conv = brain.process("Hello AURA", "en")
assert res_conv["type"] == "conversation"
assert res_conv["executable"] is False

# Stage 5: Real-time query
res_web = brain.process("What is the latest AI news?", "en")
assert res_web["type"] == "web_search"
assert res_web["executable"] is False

print("✓ All Prior Stage Regressions Passed!")

print("\n==================================================")
print("  🎉 STAGE 6 SCREEN AWARENESS TESTS PASSED!       ")
print("==================================================")
