import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE_FILE = ROOT / "AI_TRACE.md"
EXTENSIONS = {".py", ".html", ".js", ".css", ".sql"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "media", "staticfiles", "logs"}
SKIP_FILES = {Path(__file__).resolve()}
LOCK_TEXT = "CẤM XÓA CHÚ THÍCH NÀY"

MARKER = re.compile(
    r"AI-TRACE#(?P<id>\d{3,})\s*\|\s*(?P<model>[^|]+?)\s*\|\s*(?P<purpose>[^|]+?)\s*\|\s*"
    + re.escape(LOCK_TEXT)
    + r"(?:\s*\|\s*(?P<note>[^|]+?))?\s*(?:#\}|\*/|-->)?\s*$"
)
ANY_MARKER = re.compile(r"AI-TRACE#")
PY_DEF = re.compile(r"^(?P<indent>\s*)(?:async\s+def|def|class)\s+(?P<name>\w+)")
HTML_BLOCK = re.compile(r"\{%\s*block\s+(?P<name>\w+)")
JS_FUNC = re.compile(r"(?:function\s+(?P<a>\w+)|(?:const|let|var)\s+(?P<b>\w+)\s*=)")
SQL_OBJ = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:DEFINER\s*=\s*\S+\s+)?(?:SQL\s+SECURITY\s+\w+\s+)?"
    r"(?P<kind>PROCEDURE|FUNCTION|VIEW|TRIGGER|TABLE)\s+`?(?P<name>\w+)",
    re.IGNORECASE,
)
ROW = re.compile(r"^\|\s*(?P<id>\d{3,})\s*\|")
HEADER = (
    "| ID | Model | Người dùng | File | Class / Hàm | Dòng | Làm gì | Đã duyệt |\n"
    "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
)
INTRO = (
    "# AI_TRACE – code do AI viết\n\n"
    "File tạm, sinh bằng `python scripts/ai_trace.py`. Không sửa tay các cột Model, File, "
    "Class / Hàm, Dòng, Làm gì. Chỉ điền tay cột **Người dùng** và **Đã duyệt** (`[x]`). "
    "Quy định: `docs/ai-trace.md`.\n\n"
)


def iter_source_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if path.suffix in EXTENSIONS and path.resolve() not in SKIP_FILES:
                yield path


def python_owner(lines, index):
    marker_indent = len(lines[index]) - len(lines[index].lstrip())
    target = None
    for line in lines[index + 1:]:
        text = line.strip()
        if not text or text.startswith("@"):
            continue
        target = PY_DEF.match(line)
        break
    if target is None:
        return "(không đứng trên def/class)"
    names = [target.group("name")]
    level = marker_indent
    for line in reversed(lines[:index]):
        found = PY_DEF.match(line)
        if found and len(found.group("indent")) < level:
            names.insert(0, found.group("name"))
            level = len(found.group("indent"))
            if level == 0:
                break
    return ".".join(names)


def generic_owner(path, lines, index):
    for line in lines[index + 1:]:
        text = line.strip()
        if not text:
            continue
        if path.suffix == ".html":
            found = HTML_BLOCK.search(text)
            if found:
                return "block " + found.group("name")
        elif path.suffix == ".js":
            found = JS_FUNC.search(text)
            if found:
                return found.group("a") or found.group("b")
        elif path.suffix == ".sql":
            found = SQL_OBJ.search(text)
            if found:
                return found.group("kind").upper() + " " + found.group("name")
        elif path.suffix == ".css":
            return text.rstrip("{").strip()[:60]
        return text[:60]
    return "(cuối file)"


def scan():
    entries = {}
    errors = []
    for path in iter_source_files():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for index, line in enumerate(lines):
            if not ANY_MARKER.search(line):
                continue
            found = MARKER.search(line)
            if not found:
                errors.append(f"{rel}:{index + 1}: sai định dạng chú thích AI-TRACE")
                continue
            trace_id = found.group("id")
            if trace_id in entries:
                first = entries[trace_id]
                errors.append(
                    f"{rel}:{index + 1}: trùng ID {trace_id} với {first['file']}:{first['line']}"
                )
                continue
            purpose = found.group("purpose")
            if len(purpose.split()) < 4:
                errors.append(f"{rel}:{index + 1}: mục 'làm gì' của ID {trace_id} quá ngắn")
            owner = python_owner(lines, index) if path.suffix == ".py" else generic_owner(path, lines, index)
            note = found.group("note")
            entries[trace_id] = {
                "model": found.group("model"),
                "file": rel,
                "owner": owner,
                "line": index + 1,
                "purpose": purpose + (f" ({note})" if note else ""),
            }
    return entries, errors


def read_table():
    manual = {}
    if not TABLE_FILE.exists():
        return manual
    for line in TABLE_FILE.read_text(encoding="utf-8").splitlines():
        found = ROW.match(line)
        if not found:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 8:
            continue
        manual[found.group("id")] = {
            "model": cells[1],
            "user": cells[2],
            "file": cells[3].strip("`"),
            "owner": cells[4].strip("`"),
            "line": cells[5],
            "purpose": cells[6],
            "reviewed": cells[7],
        }
    return manual


def render(entries, manual):
    rows = []
    for trace_id in sorted(set(entries) | set(manual), key=int):
        old = manual.get(trace_id, {})
        user = old.get("user", "")
        reviewed = old.get("reviewed") or "[ ]"
        if trace_id in entries:
            item = entries[trace_id]
            line = str(item["line"])
            model, file, owner, purpose = item["model"], item["file"], item["owner"], item["purpose"]
        else:
            model, file, owner, purpose = old["model"], old["file"], old["owner"], old["purpose"]
            line = "**MẤT CHÚ THÍCH**"
        rows.append(
            f"| {trace_id} | {model} | {user} | `{file}` | `{owner}` | {line} | {purpose} | {reviewed} |\n"
        )
    return INTRO + HEADER + "".join(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    entries, errors = scan()
    manual = read_table()
    missing = sorted(set(manual) - set(entries), key=int)
    for trace_id in missing:
        errors.append(f"ID {trace_id}: chú thích trong code đã bị xóa ({manual[trace_id]['file']})")
    content = render(entries, manual)

    if args.check:
        current = TABLE_FILE.read_text(encoding="utf-8") if TABLE_FILE.exists() else ""
        if current != content:
            errors.append("AI_TRACE.md chưa cập nhật: chạy python scripts/ai_trace.py rồi commit")
    else:
        TABLE_FILE.write_text(content, encoding="utf-8")
        print(f"Đã ghi {TABLE_FILE.name}: {len(entries)} mục")

    for message in errors:
        print("LỖI:", message, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
