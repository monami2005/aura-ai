import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict, Any
from .communication import get_communication_provider, resolve_contact

SAFE_ACTIONS = {
    "open_website",
    "take_screenshot",
    "create_folder",
    "find_file",
    "open_application",
    "call_contact",
    "send_text_message",
    "send_voice_message",
    "click_screen",
    "type_text",
    "press_key",
    "scroll_screen",
    "apply_code_fix",
    "safe_code_edit"
}

ALLOWED_APPLICATIONS = {
    "calculator": "calc.exe",
    "notepad": "notepad.exe",
    "paint": "mspaint.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe"
}

def execute_safe_action(action: str, params: Dict[str, Any], original_command: str = "") -> Dict[str, Any]:
    if action not in SAFE_ACTIONS:
        return {
            "success": False,
            "error": f"Action '{action}' is not in the safe allowlist."
        }
    
    try:
        # 1. Open Website
        if action == "open_website":
            url = params.get("url", "").strip()
            if not url:
                return {"success": False, "error": "No URL provided for open_website."}
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
            webbrowser.open(url)
            return {"success": True, "result": f"Opened website: {url}"}
            
        # 2. Take Screenshot
        elif action == "take_screenshot":
            screenshots_dir = Path.home() / "Pictures" / "AURA_Screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            from datetime import datetime
            file_name = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            file_path = screenshots_dir / file_name
            
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                img.save(str(file_path))
                return {"success": True, "result": f"Screenshot saved successfully at {file_path}"}
            except Exception as e:
                return {"success": False, "error": f"Failed to capture screenshot: {str(e)}"}
                
        # 3. Create Folder (Sanitized path)
        elif action == "create_folder":
            raw_folder_name = params.get("folder_name", "").strip()
            clean_name = "".join(c for c in raw_folder_name if c.isalnum() or c in (" ", "_", "-")).strip()
            if not clean_name:
                clean_name = "New_Aura_Folder"
                
            target_path = Path.home() / "Documents" / clean_name
            target_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "result": f"Folder created safely at {target_path}"}
            
        # 4. Find File
        elif action == "find_file":
            filename = params.get("filename", "").strip()
            if not filename or ".." in filename:
                return {"success": False, "error": "Invalid filename parameter."}
            search_root = Path(__file__).resolve().parents[2] # Project root
            matches = []
            for root, _, files in os.walk(search_root):
                for f in files:
                    if filename.lower() in f.lower():
                        matches.append(os.path.join(root, f))
                        if len(matches) >= 5:
                            break
                if len(matches) >= 5:
                    break
            if matches:
                return {"success": True, "result": f"Found matching files:\n" + "\n".join(matches)}
            return {"success": True, "result": f"No files matching '{filename}' were found in project workspace."}
            
        # 5. Open Application (Strict binary lookup without shell)
        elif action == "open_application":
            app_key = params.get("app_name", "").strip().lower()
            if app_key in ALLOWED_APPLICATIONS:
                exe = ALLOWED_APPLICATIONS[app_key]
                if "chrome" in app_key:
                    chrome_candidates = [
                        Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
                        Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
                        Path(os.environ.get("LocalAppData", "")) / "Google" / "Chrome" / "Application" / "chrome.exe"
                    ]
                    for cand in chrome_candidates:
                        if cand.exists():
                            exe = str(cand)
                            break
                try:
                    subprocess.Popen([exe], shell=False)
                    return {"success": True, "result": f"Launched {app_key} ({exe}) safely."}
                except FileNotFoundError:
                    return {"success": False, "error": f"Application binary '{exe}' not found on system."}
            else:
                return {
                    "success": False,
                    "error": f"Application '{app_key}' is not in the allowlist. Allowed: {list(ALLOWED_APPLICATIONS.keys())}"
                }
                
        # 6. Call Contact (Multi-Platform Router)
        elif action == "call_contact":
            contact_name = params.get("contact_name", "").strip()
            platform = params.get("platform", "phone").lower().strip()
            if not contact_name:
                return {"success": False, "error": "Recipient name is required for calls."}
            provider = get_communication_provider()
            return provider.call_contact(contact_name, platform=platform)
            
        # 7. Send Text Message (Multi-Platform Router)
        elif action == "send_text_message":
            contact_name = params.get("contact_name", "").strip()
            message_text = params.get("message", "").strip()
            platform = params.get("platform", "phone").lower().strip()
            if not contact_name:
                return {"success": False, "error": "Recipient name is required to send a message."}
            if not message_text:
                return {"success": False, "error": "Message content cannot be empty."}
            provider = get_communication_provider()
            return provider.send_text_message(contact_name, message_text, platform=platform)
            
        # 8. Send Voice Message (Multi-Platform Router)
        elif action == "send_voice_message":
            contact_name = params.get("contact_name", "").strip()
            message_text = params.get("message", "").strip()
            platform = params.get("platform", "phone").lower().strip()
            if not contact_name:
                return {"success": False, "error": "Recipient name is required to send a voice message."}
            provider = get_communication_provider()
            return provider.send_voice_message(contact_name, message_text, platform=platform)

        # 9. Click Screen (Stage 7 UI Automation)
        elif action == "click_screen":
            x = params.get("x")
            y = params.get("y")
            target = params.get("target", "screen element")
            simulate = params.get("simulate", False)

            if x is not None and y is not None:
                if not (isinstance(x, (int, float)) and isinstance(y, (int, float)) and 0 <= x <= 10000 and 0 <= y <= 10000):
                    return {"success": False, "error": f"Invalid click coordinates: ({x}, {y})"}

            if not simulate:
                try:
                    import pyautogui
                    pyautogui.FAILSAFE = True
                    if x is not None and y is not None:
                        pyautogui.click(x=int(x), y=int(y))
                    return {"success": True, "result": f"Clicked on screen at {target}."}
                except ImportError:
                    pass
                except Exception as e:
                    return {"success": False, "error": f"Failed to execute click: {str(e)}"}

            # Simulation fallback
            return {"success": True, "result": f"Simulated click executed on screen {target}."}

        # 10. Type Text (Stage 7 UI Automation)
        elif action == "type_text":
            text = params.get("text", "")
            simulate = params.get("simulate", False)
            if not text:
                return {"success": False, "error": "No text provided to type."}
            if len(text) > 500:
                return {"success": False, "error": "Text exceeds maximum safe length of 500 characters."}

            if not simulate:
                try:
                    import pyautogui
                    pyautogui.FAILSAFE = True
                    pyautogui.typewrite(text)
                    return {"success": True, "result": f"Typed text into active field: \"{text}\""}
                except ImportError:
                    pass
                except Exception as e:
                    return {"success": False, "error": f"Failed to execute typing: {str(e)}"}

            # Simulation fallback
            return {"success": True, "result": f"Simulated typing executed: \"{text}\""}

        # 11. Press Navigation Key (Stage 7 UI Automation)
        elif action == "press_key":
            from .screen.interaction import SAFE_KEYS
            key = params.get("key", "").lower().strip()
            simulate = params.get("simulate", False)
            if not key:
                return {"success": False, "error": "No key provided to press."}
            if key not in SAFE_KEYS:
                return {"success": False, "error": f"Key '{key}' is not allowed for security reasons."}

            if not simulate:
                try:
                    import pyautogui
                    pyautogui.FAILSAFE = True
                    pyautogui.press(key)
                    return {"success": True, "result": f"Pressed navigation key: {key.upper()}"}
                except ImportError:
                    pass
                except Exception as e:
                    return {"success": False, "error": f"Failed to press key: {str(e)}"}

            # Simulation fallback
            return {"success": True, "result": f"Simulated key press executed: {key.upper()}"}

        # 12. Scroll Screen (Stage 7 UI Automation)
        elif action == "scroll_screen":
            direction = params.get("direction", "down").lower().strip()
            steps = params.get("steps", 3)
            simulate = params.get("simulate", False)
            if direction not in ("up", "down"):
                return {"success": False, "error": f"Invalid scroll direction: '{direction}'"}
            if not (isinstance(steps, int) and 1 <= steps <= 20):
                return {"success": False, "error": "Scroll steps must be an integer between 1 and 20."}

            if not simulate:
                try:
                    import pyautogui
                    pyautogui.FAILSAFE = True
                    scroll_amount = (steps * 100) if direction == "up" else -(steps * 100)
                    pyautogui.scroll(scroll_amount)
                    return {"success": True, "result": f"Scrolled screen {direction} by {steps} steps."}
                except ImportError:
                    pass
                except Exception as e:
                    return {"success": False, "error": f"Failed to execute scroll: {str(e)}"}

            # Simulation fallback
            return {"success": True, "result": f"Scrolled screen {direction} (simulated, {steps} steps)."}

        # 13. Apply Safe Code Fix (AI Screen & Code Assistant)
        elif action in ("apply_code_fix", "safe_code_edit"):
            from .agent.coding_assistant import apply_safe_code_fix
            target_file = params.get("target_file", "")
            fixed_code = params.get("fixed_code", "")
            original_code = params.get("original_code", "")
            return apply_safe_code_fix(target_file, fixed_code, original_code)

        return {"success": False, "error": f"Unhandled action: {action}"}
        
    except Exception as exc:
        return {"success": False, "error": f"Execution error: {str(exc)}"}
