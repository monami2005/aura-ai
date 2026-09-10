import ast
import re
from typing import Dict, Any, Optional

COMMON_ERROR_PATTERNS = [
    {
        "pattern": r"(indexerror|list index out of range)",
        "name": "IndexError",
        "why": "The code attempted to access an element at an index that doesn't exist in the list or array (e.g. accessing index 5 in a list with only 3 elements).",
        "fix": "Check the sequence length using len(seq) before indexing, or ensure your loop bounds stay within range(len(seq))."
    },
    {
        "pattern": r"(keyerror)",
        "name": "KeyError",
        "why": "The code attempted to access a dictionary key that does not exist.",
        "fix": "Use dict.get(key, default) or check if key in my_dict before accessing."
    },
    {
        "pattern": r"(typeerror|unsupported operand type|takes \d+ positional argument)",
        "name": "TypeError",
        "why": "An operation or function call was performed on incompatible data types (for example, adding a string to an integer).",
        "fix": "Cast variables to compatible types using int(), str(), or float(), or verify function parameter counts."
    },
    {
        "pattern": r"(nameerror|name '.*' is not defined)",
        "name": "NameError",
        "why": "A variable or function is referenced before it has been assigned, or its name is misspelled, or an import is missing.",
        "fix": "Ensure the variable or function is properly defined, spelled correctly, and imported before use."
    },
    {
        "pattern": r"(zerodivisionerror|division by zero)",
        "name": "ZeroDivisionError",
        "why": "A division or modulo operation attempted to divide by zero.",
        "fix": "Add a check (e.g. if denominator != 0:) before performing division."
    },
    {
        "pattern": r"(indentationerror|unexpected indent|unindent does not match)",
        "name": "IndentationError",
        "why": "Python relies on consistent whitespace to define code blocks. Mixing tabs and spaces or misaligning blocks triggers this error.",
        "fix": "Use consistent 4-space indentation across all nested blocks."
    },
    {
        "pattern": r"(recursionerror|maximum recursion depth exceeded)",
        "name": "RecursionError",
        "why": "A recursive function failed to reach its base termination condition, causing a stack overflow.",
        "fix": "Verify that your recursive function has a valid base case and that arguments step closer to the base case on each call."
    }
]

def analyze_code_or_error(query: str, code: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    """
    Dedicated AI Coding Assistant workflow.
    Analyzes code or error descriptions and returns Problem, Why it happens, and Suggested Fix.
    Never modifies or executes code automatically.
    """
    combined_text = f"{query} {code or ''}".strip()
    q_lower = combined_text.lower()

    # 1. Check for common runtime error patterns
    detected_error = None
    for err in COMMON_ERROR_PATTERNS:
        if re.search(err["pattern"], q_lower):
            detected_error = err
            break

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
        why = "Python could not parse this statement because it violates grammar rules (e.g. missing colon, unbalanced parentheses, or unclosed quotes)."
        fix = f"Review line {syntax_error_details['line']}. Ensure colons ':' follow 'def/if/for/while' headers and all brackets/quotes match."
    elif detected_error:
        problem = f"Runtime {detected_error['name']} detected."
        why = detected_error["why"]
        fix = detected_error["fix"]
    else:
        problem = "General logic or structure review requested."
        why = "The code may contain logical edge cases, unhandled exceptions, or unintended variable scope."
        fix = "Add boundary checks, verify input types, and wrap sensitive operations in try/except blocks."

    # Multilingual formatting
    if language == "bn":
        explanation = (
            f"🛠️ **কোড ও ত্রুটি বিশ্লেষণ (Code Analysis)**:\n"
            f"• **সমস্যা (Problem)**: {problem}\n"
            f"• **কারণ (Why it happens)**: {why}\n"
            f"• **সমাধান (Suggested Fix)**: {fix}\n\n"
            f"*(দ্রষ্টব্য: নিরাপত্তার স্বার্থে AURA AI কোনো কোড স্বয়ংক্রিয়ভাবে এক্সিকিউট বা পরিবর্তন করে না।)*"
        )
    elif language == "hi":
        explanation = (
            f"🛠️ **कोड व त्रुटि विश्लेषण (Code Analysis)**:\n"
            f"• **समस्या (Problem)**: {problem}\n"
            f"• **कारण (Why it happens)**: {why}\n"
            f"• **समाधान (Suggested Fix)**: {fix}\n\n"
            f"*(नोट: सुरक्षा कारणों से AURA AI किसी भी कोड को स्वचालित रूप से निष्पादित या संशोधित नहीं करता है।)*"
        )
    else:
        explanation = (
            f"🛠️ **Code & Error Analysis**:\n"
            f"1. **Problem**: {problem}\n"
            f"2. **Why it happens**: {why}\n"
            f"3. **Suggested Fix**: {fix}\n\n"
            f"*(Note: For safety, AURA AI never modifies or executes code automatically.)*"
        )

    return {
        "problem": problem,
        "why": why,
        "fix": fix,
        "response": explanation,
        "executable": False
    }
