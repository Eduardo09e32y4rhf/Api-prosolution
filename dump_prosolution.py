from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_FILE = BASE_DIR / "prosolution_full_dump.txt"

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "node_modules",
}

INCLUDE_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".html",
    ".css",
    ".js",
    ".env",
    ".example",
}


def should_include(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return False
    if path.is_file() and path.suffix.lower() in INCLUDE_EXTENSIONS:
        return True
    return False


def main():
    lines = []
    lines.append("=" * 80)
    lines.append("PROSOLUTION IA — FULL PROJECT DUMP")
    lines.append("=" * 80)
    lines.append(f"Base path: {BASE_DIR}")
    lines.append("")

    for file_path in sorted(BASE_DIR.rglob("*")):
        if should_include(file_path):
            rel = file_path.relative_to(BASE_DIR)
            lines.append("\n" + "-" * 80)
            lines.append(f"FILE: {rel}")
            lines.append("-" * 80)
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines.append(content)
            except Exception as e:
                lines.append(f"[ERROR READING FILE]: {e}")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Dump gerado com sucesso: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
