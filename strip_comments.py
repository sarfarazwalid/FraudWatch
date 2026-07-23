"""
Strip unnecessary comments and docstrings from code files.
Keeps: type annotations, TODOs/FIXMEs, license headers, executable code, non-obvious comments.
"""

import re
import os
from pathlib import Path

# Directories to process
DIRS = [
    Path("backend/app"),
    Path("frontend"),
    Path("ml"),
]

# File extensions to process
PY_EXT = ".py"
TS_EXT = (".ts", ".tsx")
ALL_EXT = (".py", ".ts", ".tsx")

# Patterns to skip (keep these comments)
KEEP_PATTERNS = [
    r"TODO",
    r"FIXME",
    r"HACK",
    r"XXX",
    r"Copyright",
    r"License",
    r"MIT",
    r"Apache",
]


def has_keep_pattern(line: str) -> bool:
    """Check if a comment line should be kept."""
    for pat in KEEP_PATTERNS:
        if re.search(pat, line, re.IGNORECASE):
            return True
    return False


def strip_py_file(content: str) -> str:
    """Strip docstrings and obvious comments from a Python file."""
    lines = content.split("\n")
    result = []
    i = 0
    in_docstring = False
    docstring_char = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track multi-line docstrings
        if in_docstring:
            if docstring_char in line:
                # Check if this line ends the docstring
                idx = line.find(docstring_char)
                # Count occurrences
                count = line.count(docstring_char)
                if count >= 3 or (count >= 1 and line.strip().endswith(docstring_char * 3)):
                    in_docstring = False
                    docstring_char = None
                    # If there's code after the closing, keep it
                    remainder = line[line.rfind(docstring_char * 3) + 3:]
                    if remainder.strip():
                        result.append(remainder)
            i += 1
            continue

        # Check for start of docstring
        if stripped.startswith('"""') or stripped.startswith("'''"):
            char = stripped[:3]
            # Check if it's a module-level or function-level docstring
            # Skip if it's a docstring (not an assignment or expression)
            if stripped == char * 3 or (len(stripped) > 3 and stripped.endswith(char * 3) and len(stripped) == 6):
                # Single line docstring - skip it
                i += 1
                continue
            elif stripped == char * 3:
                # Multi-line docstring start
                in_docstring = True
                docstring_char = char
                i += 1
                continue

        # Strip inline comments that are obvious
        if "#" in line:
            # Find the comment position (not inside a string)
            comment_pos = _find_comment_pos(line)
            if comment_pos is not None:
                comment = line[comment_pos + 1:].strip()
                # Keep TODOs, FIXMEs, etc.
                if has_keep_pattern(comment):
                    result.append(line)
                    i += 1
                    continue
                # Check if the comment is "obvious" (just restates the code)
                code_part = line[:comment_pos].strip()
                if _is_obvious_comment(comment, code_part):
                    # Remove the comment, keep the code
                    result.append(line[:comment_pos].rstrip())
                    i += 1
                    continue

        result.append(line)
        i += 1

    return "\n".join(result)


def _find_comment_pos(line: str) -> int | None:
    """Find the position of a # comment that's not inside a string."""
    in_single = False
    in_double = False
    in_triple_single = False
    in_triple_double = False
    i = 0
    while i < len(line):
        ch = line[i]
        # Check for triple quotes
        if line[i:i+3] == '"""':
            in_triple_double = not in_triple_double
            i += 3
            continue
        if line[i:i+3] == "'''":
            in_triple_single = not in_triple_single
            i += 3
            continue
        if ch == '"' and not in_single and not in_triple_single:
            in_double = not in_double
        elif ch == "'" and not in_double and not in_triple_double:
            in_single = not in_single
        elif ch == "#" and not in_single and not in_double and not in_triple_single and not in_triple_double:
            return i
        i += 1
    return None


def _is_obvious_comment(comment: str, code: str) -> bool:
    """Check if a comment is obvious (just restates what the code does)."""
    comment_lower = comment.lower().rstrip(".")
    code_lower = code.lower()

    # Common obvious comment patterns
    obvious_patterns = [
        # Variable assignments
        lambda c, cd: c.startswith("set ") or c.startswith("get "),
        # Simple operations
        lambda c, cd: c in ("check", "validate", "update", "create", "delete", "add", "remove"),
        # Redundant
        lambda c, cd: c == cd.strip().rstrip(":").strip(),
        # Return statements
        lambda c, cd: c.startswith("return the ") or c.startswith("return a "),
        # Type declarations
        lambda c, cd: c.startswith("type for ") or c.startswith("type of "),
    ]

    for pattern in obvious_patterns:
        if pattern(comment_lower, code_lower):
            return True

    return False


def strip_ts_file(content: str) -> str:
    """Strip JSDoc comments and obvious inline comments from TypeScript files."""
    lines = content.split("\n")
    result = []
    i = 0
    in_jsdoc = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Track JSDoc blocks
        if in_jsdoc:
            if stripped.endswith("*/"):
                in_jsdoc = False
            i += 1
            continue

        if stripped.startswith("/**"):
            in_jsdoc = True
            i += 1
            continue

        # Strip single-line comments that are obvious
        if "//" in line:
            comment_pos = _find_ts_comment_pos(line)
            if comment_pos is not None:
                comment = line[comment_pos + 2:].strip()
                if has_keep_pattern(comment):
                    result.append(line)
                    i += 1
                    continue
                code_part = line[:comment_pos].strip()
                if _is_obvious_comment(comment, code_part):
                    result.append(line[:comment_pos].rstrip())
                    i += 1
                    continue

        result.append(line)
        i += 1

    return "\n".join(result)


def _find_ts_comment_pos(line: str) -> int | None:
    """Find the position of a // comment that's not inside a string."""
    in_single = False
    in_double = False
    in_template = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '`':
            in_template = not in_template
        elif ch == '"' and not in_single and not in_template:
            in_double = not in_double
        elif ch == "'" and not in_double and not in_template:
            in_single = not in_single
        elif ch == "/" and i + 1 < len(line) and line[i+1] == "/" and not in_single and not in_double and not in_template:
            return i
        i += 1
    return None


def process_file(filepath: Path) -> bool:
    """Process a single file. Returns True if modified."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        try:
            content = filepath.read_text(encoding="latin-1")
        except Exception:
            return False

    original = content

    if filepath.suffix == ".py":
        content = strip_py_file(content)
    elif filepath.suffix in (".ts", ".tsx"):
        content = strip_ts_file(content)
    else:
        return False

    if content != original:
        filepath.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    total_modified = 0
    total_files = 0

    for base_dir in DIRS:
        if not base_dir.exists():
            print(f"Directory not found: {base_dir}")
            continue

        for root, dirs, files in os.walk(base_dir):
            # Skip __pycache__, node_modules, .next, etc.
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules", ".next", ".git", ".venv", "venv")]

            for fname in files:
                if not fname.endswith(ALL_EXT):
                    continue
                filepath = Path(root) / fname
                if process_file(filepath):
                    try:
                        rel_path = filepath.relative_to(Path.cwd())
                    except ValueError:
                        rel_path = filepath
                    print(f"  Modified: {rel_path}")
                    total_modified += 1
                total_files += 1

    print(f"\nProcessed {total_files} files, modified {total_modified}")


if __name__ == "__main__":
    main()
