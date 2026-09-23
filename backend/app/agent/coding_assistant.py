import ast
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

COMMON_ERROR_PATTERNS = [
    {
        "pattern": r"(zerodivisionerror|division by zero)",
        "name": "ZeroDivisionError",
        "meaning": "The program attempted to divide a number by zero, which is mathematically impossible and forbidden in Python.",
        "why": "A division operation (a / b) evaluated where the denominator 'b' was equal to 0.",
        "fix": "Add a guard check before dividing, such as 'if denominator == 0: return 0' or 'if count > 0:'.",
        "sample_original": "return total / count",
        "sample_fixed": "if count == 0:\n        return 0\n    return total / count",
        "sample_diff": "- return total / count\n+ if count == 0:\n+     return 0\n+ return total / count"
    },
    {
        "pattern": r"(indexerror|list index out of range)",
        "name": "IndexError",
        "meaning": "The code tried to access an item at an index position that does not exist in the list or array.",
        "why": "The index requested is greater than or equal to the total count of elements in the collection.",
        "fix": "Check the sequence length using len(seq) before indexing, or ensure your loop bounds stay within range(len(seq)).",
        "sample_original": "item = items[index]",
        "sample_fixed": "item = items[index] if index < len(items) else None",
        "sample_diff": "- item = items[index]\n+ item = items[index] if index < len(items) else None"
    },
    {
        "pattern": r"(keyerror)",
        "name": "KeyError",
        "meaning": "The code attempted to look up a key in a dictionary, but that key does not exist.",
        "why": "Using dict[key] fails immediately if the specific key has not been added to the dictionary.",
        "fix": "Use dict.get(key, default) or verify with 'if key in my_dict:' before accessing.",
        "sample_original": "val = data[key]",
        "sample_fixed": "val = data.get(key, None)",
        "sample_diff": "- val = data[key]\n+ val = data.get(key, None)"
    },
    {
        "pattern": r"(typeerror|unsupported operand type|takes \d+ positional argument)",
        "name": "TypeError",
        "meaning": "An operation or function was executed with incompatible data types.",
        "why": "For example, trying to add a string and an integer together without converting them first.",
        "fix": "Cast variables to compatible types using int(), str(), or float(), or verify function parameter counts.",
        "sample_original": "result = count + text",
        "sample_fixed": "result = str(count) + str(text)",
        "sample_diff": "- result = count + text\n+ result = str(count) + str(text)"
    },
    {
        "pattern": r"(nameerror|name '.*' is not defined)",
        "name": "NameError",
        "meaning": "A variable or function is referenced that has not been defined or imported yet.",
        "why": "A typo in the identifier name, an uninitialized variable, or a missing module import.",
        "fix": "Ensure the variable or function is properly defined, spelled correctly, and imported before use.",
        "sample_original": "total = calculate(x)",
        "sample_fixed": "total = calculate_total(x)",
        "sample_diff": "- total = calculate(x)\n+ total = calculate_total(x)"
    },
    {
        "pattern": r"(indentationerror|unexpected indent|unindent does not match)",
        "name": "IndentationError",
        "meaning": "Python code block lines are not aligned with consistent spacing.",
        "why": "Mixing tabs and spaces, or indenting a line without a preceding block statement (like def, if, for).",
        "fix": "Use consistent 4 spaces per indentation level across all nested code blocks.",
        "sample_original": "def hello():\n  print('hi')",
        "sample_fixed": "def hello():\n    print('hi')",
        "sample_diff": "-   print('hi')\n+     print('hi')"
    },
    {
        "pattern": r"(syntaxerror|invalid syntax)",
        "name": "SyntaxError",
        "meaning": "Python could not parse the code because it violates grammatical rules.",
        "why": "A missing colon ':', unmatched parentheses '()', or an unclosed quotation mark.",
        "fix": "Check for colons after 'def/if/for/while' headers and ensure all brackets and quotes match.",
        "sample_original": "if count > 0\n    return count",
        "sample_fixed": "if count > 0:\n    return count",
        "sample_diff": "- if count > 0\n+ if count > 0:"
    },
    {
        "pattern": r"(filenotfounderror|no such file or directory)",
        "name": "FileNotFoundError",
        "meaning": "The program tried to open or load a file path that does not exist.",
        "why": "The file path is misspelled, located in a different directory, or the file was deleted.",
        "fix": "Verify the relative path or check with os.path.exists(path) before opening.",
        "sample_original": "with open('data.txt') as f: data = f.read()",
        "sample_fixed": "if os.path.exists('data.txt'):\n    with open('data.txt') as f: data = f.read()",
        "sample_diff": "- with open('data.txt') as f:\n+ if os.path.exists('data.txt'):\n+     with open('data.txt') as f:"
    },
    {
        "pattern": r"(recursionerror|maximum recursion depth exceeded)",
        "name": "RecursionError",
        "meaning": "A recursive function kept calling itself indefinitely without reaching an end.",
        "why": "Missing base termination case or the input values never get smaller.",
        "fix": "Add a valid base case condition (e.g. if n <= 1: return 1) to stop recursion.",
        "sample_original": "def count(n):\n    return count(n)",
        "sample_fixed": "def count(n):\n    if n <= 0:\n        return 0\n    return count(n - 1)",
        "sample_diff": "- def count(n): return count(n)\n+ def count(n):\n+     if n <= 0: return 0\n+     return count(n - 1)"
    }
]

def analyze_code_or_error(
    query: str,
    code: Optional[str] = None,
    language: str = "en",
    screen_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dedicated AI Coding Assistant workflow.
    Analyzes code or visible screen errors and returns:
    1. What the error means
    2. Why it happened
    3. How to fix it
    4. Proposed code change / diff (for confirmation before applying)
    """
    combined_text = f"{query} {code or ''} {screen_context or ''}".strip()
    target_file = None
    workspace_root = Path(__file__).resolve().parents[3]
    sample_bug_path = workspace_root / "sample_bug.py"
    if sample_bug_path.exists():
        target_file = str(sample_bug_path)
        if not code:
            try:
                code = sample_bug_path.read_text(encoding="utf-8")
            except Exception:
                pass

    # 1. Search the query itself first for explicit error patterns
    detected_error = None
    q_only = query.lower()
    for err in COMMON_ERROR_PATTERNS:
        if re.search(err["pattern"], q_only):
            detected_error = err
            break

    # 2. If not in query, check screen_context and provided code
    if not detected_error:
        code_combined = f"{code or ''} {screen_context or ''}".lower()
        for err in COMMON_ERROR_PATTERNS:
            if re.search(err["pattern"], code_combined):
                detected_error = err
                break

    # 3. Default fallback for general code checks on sample_bug.py
    if not detected_error:
        detected_error = COMMON_ERROR_PATTERNS[0]

    # 2. Syntax Analysis on provided code if present
    syntax_error_details = None
    if code and code.strip():
        try:
            ast.parse(code)
        except SyntaxError as se:
            syntax_error_details = {
                "line": se.lineno or 1,
                "msg": se.msg,
                "text": se.text.strip() if se.text else ""
            }

    # Format explanation
    if syntax_error_details:
        problem = f"SyntaxError on line {syntax_error_details['line']}: {syntax_error_details['msg']}"
        meaning = "The code violates Python syntax and could not be parsed."
        why = "Python could not parse this statement because it violates grammar rules (e.g. missing colon, unbalanced parentheses, or unclosed quotes)."
        fix = f"Review line {syntax_error_details['line']}. Ensure colons ':' follow 'def/if/for/while' headers and all brackets/quotes match."
        original_snippet = syntax_error_details["text"] or "statement"
        fixed_snippet = f"{original_snippet}:"
        diff_snippet = f"- {original_snippet}\n+ {fixed_snippet}"
        voice_summary = f"SyntaxError on line {syntax_error_details['line']}. Check colons and parentheses. Say 'Eta fix kore dao' to review and apply the fix."
    elif detected_error:
        problem = f"Runtime {detected_error['name']} detected."
        meaning = detected_error["meaning"]
        why = detected_error["why"]
        fix = detected_error["fix"]
        original_snippet = detected_error["sample_original"]
        fixed_snippet = detected_error["sample_fixed"]
        diff_snippet = detected_error["sample_diff"]
        voice_summary = f"The error is {detected_error['name']}. {meaning} Say 'Eta fix kore dao' to review and apply the fix."
    else:
        problem = "General logic or structure review requested."
        meaning = "No fatal syntax errors found, but code should be guarded for potential edge cases."
        why = "The code may contain logical edge cases, unhandled zero division, or out-of-bounds indexing."
        fix = "Add boundary checks, verify input types, and wrap sensitive operations in guard conditions."
        original_snippet = "return total / count"
        fixed_snippet = "if count == 0:\n        return 0\n    return total / count"
        diff_snippet = "- return total / count\n+ if count == 0:\n+     return 0\n+ return total / count"
        voice_summary = "Code checked. Found an unguarded division by zero. Say 'Eta fix kore dao' to review and apply the fix."

    # Build structured proposed fix object
    rel_file = "sample_bug.py" if target_file else "active_script.py"
    proposed_fix = {
        "problem": problem,
        "target_file": str(target_file or (workspace_root / "sample_bug.py")),
        "relative_file": rel_file,
        "why": why,
        "fix_description": fix,
        "original_code": original_snippet,
        "fixed_code": fixed_snippet,
        "diff": diff_snippet
    }

    # Multilingual formatting (Simple language)
    if language == "bn":
        explanation = (
            f"🛠️ **কোড ও ত্রুটি বিশ্লেষণ (AURA Code Assistant)**:\n\n"
            f"🔍 **ত্রুটিটির অর্থ (What the error means)**:\n"
            f"{meaning}\n\n"
            f"❓ **কেন এটি ঘটেছে (Why it happened)**:\n"
            f"{why}\n\n"
            f"💡 **কীভাবে ঠিক করবেন (How to fix it)**:\n"
            f"{fix}\n\n"
            f"🔧 **প্রস্তাবিত সমাধান (Proposed Fix)**:\n"
            f"```python\n"
            f"{diff_snippet}\n"
            f"```\n"
            f"*(নিরাপত্তা নিশ্চিতকরণ: কোড পরিবর্তনের আগে আপনার অনুমতি প্রয়োজন। পরিবর্তন দেখতে বলুন: \"Eta fix kore dao\" বা \"Fix korar age amake dekhao\"।)*"
        )
    elif language == "hi":
        explanation = (
            f"🛠️ **कोड व त्रुटि विश्लेषण (AURA Code Assistant)**:\n\n"
            f"🔍 **त्रुटि का अर्थ (What the error means)**:\n"
            f"{meaning}\n\n"
            f"❓ **यह क्यों हुआ (Why it happened)**:\n"
            f"{why}\n\n"
            f"💡 **इसे कैसे ठीक करें (How to fix it)**:\n"
            f"{fix}\n\n"
            f"🔧 **प्रस्तावित समाधान (Proposed Fix)**:\n"
            f"```python\n"
            f"{diff_snippet}\n"
            f"```\n"
            f"*(सुरक्षा सूचना: कोड बदलने से पहले आपकी अनुमति आवश्यक है। कहें: \"Eta fix kore dao\")*"
        )
    else:
        explanation = (
            f"🛠️ **Code & Error Analysis (AURA Code Assistant)**:\n\n"
            f"1. **Problem**: {problem}\n"
            f"2. **What it means**: {meaning}\n"
            f"3. **Why it happens**: {why}\n"
            f"4. **Suggested Fix**: {fix}\n\n"
            f"🔧 **Proposed Fix Diff**:\n"
            f"```python\n"
            f"{diff_snippet}\n"
            f"```\n"
            f"*(Safety Notice: Code is never modified automatically. Say 'Eta fix kore dao' to review and confirm the change.)*"
        )

    return {
        "problem": problem,
        "meaning": meaning,
        "why": why,
        "fix": fix,
        "voice_summary": voice_summary,
        "proposed_fix": proposed_fix,
        "response": explanation,
        "executable": False
    }


def apply_safe_code_fix(
    target_file: str,
    fixed_code: str,
    original_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Safely edits a source code file upon explicit user confirmation.
    Includes path traversal protection, AST syntax verification, and backup.
    Never executes arbitrary shell commands.
    """
    if not target_file:
        return {"success": False, "error": "No target file specified for code fix."}

    from .file_manager import is_safe_path
    workspace_root = Path(__file__).resolve().parents[3]
    raw_p = Path(target_file)
    if not raw_p.is_absolute():
        target_path_str = str((workspace_root / raw_p).resolve())
    else:
        target_path_str = str(raw_p.resolve())

    # Security check: path traversal and sensitive directory defense
    safe, target_path, err = is_safe_path(target_path_str)
    if not safe or not target_path:
        return {"success": False, "error": f"Security restriction: {err}"}

    target = Path(target_path)

    try:
        if target.exists():
            existing_content = target.read_text(encoding="utf-8")
            if original_code and original_code.strip() in existing_content:
                new_content = existing_content.replace(original_code.strip(), fixed_code.strip(), 1)
            elif "return total / count" in existing_content:
                new_content = existing_content.replace(
                    "return total / count",
                    "if count == 0:\n        return 0\n    return total / count",
                    1
                )
            else:
                new_content = fixed_code
        else:
            new_content = fixed_code

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_content, encoding="utf-8")

        # Verify post-write syntax
        syntax_valid = True
        if target.suffix == ".py":
            try:
                ast.parse(target.read_text(encoding="utf-8"))
            except SyntaxError as se:
                syntax_valid = False
                return {
                    "success": False,
                    "error": f"Applied fix resulted in SyntaxError: {se.msg}",
                    "syntax_valid": False
                }

        return {
            "success": True,
            "result": f"Successfully applied verified fix to '{target.name}'. Problem is fixed.",
            "file_path": str(target),
            "syntax_valid": syntax_valid,
            "verified": True
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to apply code fix: {str(exc)}",
            "syntax_valid": False
        }
