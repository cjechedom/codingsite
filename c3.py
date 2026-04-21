# c3.py
# ---------------------------------------------------------------------------
# Sourcerers Engine Module: Text Processing & Line Utilities (Professional Grade)
# ---------------------------------------------------------------------------
# Provides:
#   • Line splitting / joining
#   • Safe line access
#   • Indentation utilities
#   • Whitespace analysis
#   • Text block extraction
#
# No UI. No Tk. No window logic.
# Pure backend logic for the Sourcerers system.
# ---------------------------------------------------------------------------

import re


# ===========================================================================
# Line Splitting & Joining
# ===========================================================================

def split_lines(text: str) -> list:
    """
    Split text into a list of lines.

    Parameters
    ----------
    text : str

    Returns
    -------
    list[str]
    """
    if not isinstance(text, str):
        return []
    return text.splitlines()


def join_lines(lines: list) -> str:
    """
    Join a list of lines into a single text block.

    Parameters
    ----------
    lines : list[str]

    Returns
    -------
    str
    """
    if not isinstance(lines, list):
        return ""
    return "\n".join(lines)


# ===========================================================================
# Safe Line Access
# ===========================================================================

def get_line(lines: list, index: int) -> str:
    """
    Safely retrieve a line by index.

    Parameters
    ----------
    lines : list[str]
    index : int

    Returns
    -------
    str
        Line content or empty string.
    """
    try:
        return lines[index]
    except Exception:
        return ""


def set_line(lines: list, index: int, value: str) -> list:
    """
    Safely set a line by index.

    Returns
    -------
    list[str]
        Updated list.
    """
    try:
        lines[index] = value
    except Exception:
        pass
    return lines


# ===========================================================================
# Indentation Utilities
# ===========================================================================

def get_indent(line: str) -> str:
    """
    Extract leading whitespace (indentation).

    Returns
    -------
    str
    """
    if not isinstance(line, str):
        return ""
    return re.match(r"\s*", line).group(0)


def indent_line(line: str, amount: int = 4) -> str:
    """
    Add indentation to a line.

    Parameters
    ----------
    amount : int
        Number of spaces.

    Returns
    -------
    str
    """
    return (" " * amount) + line


def dedent_line(line: str, amount: int = 4) -> str:
    """
    Remove indentation from a line.

    Returns
    -------
    str
    """
    if not isinstance(line, str):
        return ""
    return line[amount:] if line.startswith(" " * amount) else line


# ===========================================================================
# Whitespace Analysis
# ===========================================================================

def is_blank(line: str) -> bool:
    """
    Check if a line is blank or whitespace-only.

    Returns
    -------
    bool
    """
    return not line.strip()


def count_leading_spaces(line: str) -> int:
    """
    Count leading spaces.

    Returns
    -------
    int
    """
    return len(line) - len(line.lstrip(" "))


# ===========================================================================
# Text Block Extraction
# ===========================================================================

def extract_block(lines: list, start: int, end: int) -> list:
    """
    Extract a block of lines safely.

    Parameters
    ----------
    start : int
    end : int

    Returns
    -------
    list[str]
    """
    try:
        return lines[start:end]
    except Exception:
        return []


# ===========================================================================
# Engine Integration
# ===========================================================================

def initialize_text_tools() -> dict:
    """
    Initialize the text processing subsystem.

    Returns
    -------
    dict
        Dictionary of text utilities.
    """
    return {
        "split": split_lines,
        "join": join_lines,
        "get": get_line,
        "set": set_line,
        "indent": indent_line,
        "dedent": dedent_line,
        "indent_of": get_indent,
        "blank": is_blank,
        "leading_spaces": count_leading_spaces,
        "block": extract_block
    }
