import os
from datetime import datetime

PROJECT_ROOT = os.getcwd()
OUTPUT_FILE = "prosolution_full_dump.txt"

INCLUDE_EXTENSIONS = {".py", ".txt", ".md", ".env", ".example"}
EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".idea",
    ".vscode",
}

def should_include_file(filename):
    return any(filename.endswith(ext) for ext in INCLUDE_EXTENSIONS)

def is_excluded_dir(path):
    return any(part in EXCLUDE_DIRS for part in path.split(os.sep))

def write_header(f):
    f.write("=" * 80 + "\n")
    f.write("PROSOLUTION IA — FULL PROJECT DUMP\n")
    f.write(f"Generated at: {datetime.now()}\n")
    f.write(f"Project root: {PROJECT_ROOT}\n")
    f.write("=" * 80 + "\n\n")

def dump_tree(f):
    f.write("PROJECT STRUCTURE\n")
    f.write("-" * 80 + "\n")
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if is_excluded_dir(root):
            continue
        level = root.replace(PROJECT_ROOT, "").count(os.sep)
        indent = "  " * level
        f.write(f"{indent}{os.path.basename(root)}/\n")
        for file in files:
            if should_include_file(file):
                f.write(f"{indent}  {file}\n")
    f.write("\n")

def dump_files(f):
    f.write("FILE CONTENTS\n")
    f.write("-" * 80 + "\n")
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if is_excluded_dir(root):
            continue
        for file in files:
            if should_include_file(file):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"FILE: {rel_path}\n")
                f.write("=" * 80 + "\n")
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as rf:
                        f.write(rf.read())
                except Exception as e:
                    f.write(f"\n[ERROR READING FILE: {e}]\n")

def dump_summary(f):
    file_count = 0
    line_count = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if is_excluded_dir(root):
            continue
        for file in files:
            if should_include_file(file):
                file_count += 1
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as rf:
                        line_count += sum(1 for _ in rf)
                except:
                    pass

    f.write("\n" + "=" * 80 + "\n")
    f.write("PROJECT SUMMARY\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total files included: {file_count}\n")
    f.write(f"Total lines of code/text: {line_count}\n")

if __name__ == "__main__":
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        write_header(f)
        dump_tree(f)
        dump_files(f)
        dump_summary(f)

    print(f"\n✅ Dump gerado com sucesso: {OUTPUT_FILE}\n")
