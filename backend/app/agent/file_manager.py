import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ALLOWED_ROOTS = [
    Path.home().resolve(),
    Path(__file__).resolve().parents[3],  # Workspace root
]

RESTRICTED_DIRECTORIES = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Recovery",
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/root",
    "/var",
]

def is_safe_path(path_str: str) -> Tuple[bool, Optional[Path], Optional[str]]:
    """
    Validate that a given path is within allowed user directories and prevents path traversal.
    Returns: (is_safe, resolved_path, error_message)
    """
    if not path_str or not str(path_str).strip():
        return False, None, "Path cannot be empty."

    raw_path = Path(path_str).expanduser()
    
    # If path is relative, base it on user's Documents or workspace
    if not raw_path.is_absolute():
        resolved = (Path.home() / "Documents" / raw_path).resolve()
    else:
        resolved = raw_path.resolve()

    resolved_str = str(resolved)

    # Check against restricted system directories
    for restricted in RESTRICTED_DIRECTORIES:
        if resolved_str.lower().startswith(restricted.lower()):
            return False, None, f"Access to system-critical directory '{restricted}' is strictly forbidden."

    # Check that the path resides within at least one allowed root
    allowed = any(
        resolved_str.lower() == str(root).lower() or resolved_str.lower().startswith(str(root).lower() + os.sep)
        for root in ALLOWED_ROOTS
    )

    if not allowed:
        return False, None, f"Path '{resolved_str}' is outside allowed user working roots."

    return True, resolved, None


def safe_create_folder(folder_name_or_path: str) -> Dict[str, Any]:
    safe, target_path, err = is_safe_path(folder_name_or_path)
    if not safe or not target_path:
        return {"success": False, "error": err}

    try:
        target_path.mkdir(parents=True, exist_ok=True)
        return {
            "success": True,
            "result": f"Folder created successfully at: {target_path}",
            "path": str(target_path)
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to create folder: {str(e)}"}


def safe_list_files(dir_path: Optional[str] = None, max_items: int = 30) -> Dict[str, Any]:
    query_dir = dir_path or str(Path.home() / "Documents")
    safe, target_path, err = is_safe_path(query_dir)
    if not safe or not target_path:
        return {"success": False, "error": err}

    if not target_path.exists():
        return {"success": False, "error": f"Directory '{target_path}' does not exist."}
    if not target_path.is_dir():
        return {"success": False, "error": f"Path '{target_path}' is not a directory."}

    try:
        items = []
        for item in sorted(target_path.iterdir()):
            if len(items) >= max_items:
                break
            items.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size_bytes": item.stat().st_size if item.is_file() else 0
            })
        return {
            "success": True,
            "result": f"Listed {len(items)} items in {target_path}:",
            "directory": str(target_path),
            "items": items
        }
    except Exception as e:
        return {"success": False, "error": f"Could not list directory: {str(e)}"}


def safe_find_file(filename: str, search_root: Optional[str] = None) -> Dict[str, Any]:
    if not filename or ".." in filename:
        return {"success": False, "error": "Invalid filename for search."}

    root = Path(search_root).resolve() if search_root else Path(__file__).resolve().parents[3]
    safe, target_root, err = is_safe_path(str(root))
    if not safe or not target_root:
        return {"success": False, "error": err}

    matches = []
    clean_name = filename.lower().strip()

    try:
        for cur_root, dirs, files in os.walk(str(target_root)):
            # Skip hidden/cache directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".git")]
            for f in files:
                if clean_name in f.lower():
                    matches.append(os.path.join(cur_root, f))
                    if len(matches) >= 10:
                        break
            if len(matches) >= 10:
                break

        if matches:
            return {
                "success": True,
                "result": f"Found {len(matches)} matching file(s):\n" + "\n".join(matches),
                "matches": matches
            }
        return {
            "success": True,
            "result": f"No files matching '{filename}' were found in '{target_root}'.",
            "matches": []
        }
    except Exception as e:
        return {"success": False, "error": f"Search failed: {str(e)}"}


def safe_read_file(filepath: str, max_chars: int = 15000) -> Dict[str, Any]:
    safe, target_path, err = is_safe_path(filepath)
    if not safe or not target_path:
        return {"success": False, "error": err}

    if not target_path.exists() or not target_path.is_file():
        return {"success": False, "error": f"File '{target_path}' does not exist."}

    try:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        truncated = len(content) > max_chars
        preview = content[:max_chars]
        
        return {
            "success": True,
            "result": f"Read file: {target_path.name} ({len(content)} characters):",
            "content": preview,
            "truncated": truncated,
            "file_path": str(target_path)
        }
    except Exception as e:
        return {"success": False, "error": f"Could not read file '{target_path}': {str(e)}"}


def safe_summarize_file(filepath: str) -> Dict[str, Any]:
    read_res = safe_read_file(filepath)
    if not read_res["success"]:
        return read_res

    content = read_res.get("content", "")
    lines = content.splitlines()
    num_lines = len(lines)
    num_words = len(content.split())
    
    # Generate structured preview
    sample_lines = [l.strip() for l in lines[:5] if l.strip()]
    summary_text = (
        f"File: '{Path(filepath).name}' has {num_lines} lines and ~{num_words} words.\n"
        f"Opening content preview:\n" + "\n".join(f"> {l}" for l in sample_lines)
    )
    return {
        "success": True,
        "result": summary_text,
        "lines": num_lines,
        "words": num_words
    }


def safe_rename_file(src: str, dst: str) -> Dict[str, Any]:
    safe_src, src_path, err_src = is_safe_path(src)
    if not safe_src or not src_path:
        return {"success": False, "error": f"Source path error: {err_src}"}

    safe_dst, dst_path, err_dst = is_safe_path(dst)
    if not safe_dst or not dst_path:
        return {"success": False, "error": f"Destination path error: {err_dst}"}

    if not src_path.exists():
        return {"success": False, "error": f"Source file '{src_path}' does not exist."}
    if dst_path.exists():
        return {"success": False, "error": f"Destination '{dst_path}' already exists. Overwriting is blocked."}

    try:
        src_path.rename(dst_path)
        return {
            "success": True,
            "result": f"Renamed '{src_path.name}' to '{dst_path.name}' successfully.",
            "source": str(src_path),
            "destination": str(dst_path)
        }
    except Exception as e:
        return {"success": False, "error": f"Could not rename file: {str(e)}"}


def safe_move_file(src: str, dest_dir: str) -> Dict[str, Any]:
    safe_src, src_path, err_src = is_safe_path(src)
    if not safe_src or not src_path:
        return {"success": False, "error": f"Source path error: {err_src}"}

    safe_dest, dest_path, err_dest = is_safe_path(dest_dir)
    if not safe_dest or not dest_path:
        return {"success": False, "error": f"Destination error: {err_dest}"}

    if not src_path.exists():
        return {"success": False, "error": f"Source file '{src_path}' does not exist."}
    if not dest_path.is_dir():
        return {"success": False, "error": f"Destination '{dest_path}' must be an existing directory."}

    target_file = dest_path / src_path.name
    if target_file.exists():
        return {"success": False, "error": f"A file named '{src_path.name}' already exists in '{dest_path}'. Overwrite blocked."}

    try:
        shutil.move(str(src_path), str(target_file))
        return {
            "success": True,
            "result": f"Moved '{src_path.name}' into '{dest_path.name}' successfully.",
            "source": str(src_path),
            "destination": str(target_file)
        }
    except Exception as e:
        return {"success": False, "error": f"Could not move file: {str(e)}"}


def safe_delete_file(filepath: str) -> Dict[str, Any]:
    """
    Delete a single file safely after explicit user confirmation.
    Blocks deletion of directories or non-whitelisted paths.
    """
    safe, target_path, err = is_safe_path(filepath)
    if not safe or not target_path:
        return {"success": False, "error": err}

    if not target_path.exists():
        return {"success": False, "error": f"File '{target_path}' does not exist."}
    if target_path.is_dir():
        return {"success": False, "error": "Recursive directory deletion is blocked for safety. Only individual files can be deleted."}

    try:
        target_path.unlink()
        return {
            "success": True,
            "result": f"File '{target_path.name}' was safely deleted.",
            "path": str(target_path)
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to delete file: {str(e)}"}
