# c1.py – Sourcerers Engine Core (fixed for localtextkeys root)

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALTEXT_DIR = os.path.join(BASE_DIR, "localtextkeys")  # <-- root, no /keywords


_LANGUAGE_MAP = {
    ".py": "python",
    ".c": "c",
    ".cs": "cs",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".js": "js"
}


def detect_language(path: str) -> str:
    if not path:
        return "text"
    ext = os.path.splitext(path)[1].lower()
    return _LANGUAGE_MAP.get(ext, "text")


def load_keyword_pack(lang: str):
    """
    Reads from: localtextkeys/python.txt
    """
    file_path = os.path.join(LOCALTEXT_DIR, f"python.txt")

    if not os.path.isfile(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception:
        return []


def read_file_safe(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write_file_safe(path: str, data: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        return True
    except Exception:
        return False


_SUPPORTED_LANGUAGES = ["python", "c", "cs", "cpp", "html", "css", "js"]


def initialize_core() -> dict:
    packs = {lang: load_keyword_pack(lang) for lang in _SUPPORTED_LANGUAGES}
    return {
        "keywords": packs,
        "detect_language": detect_language,
        "read_file": read_file_safe,
        "write_file": write_file_safe
    }
