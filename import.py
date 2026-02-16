from __future__ import annotations

import os
import re
import sys
from pathlib import Path

START_RE = re.compile(r"^---\s*START_FILE:\s*(.+?)\s*---\s*$")
END_RE = re.compile(r"^---\s*END_FILE:\s*(.+?)\s*---\s*$")


def normalize_rel_path(rel: str) -> Path:
    """
    Normaliza o caminho relativo do dump para o SO (Windows/Linux/Mac).
    Bloqueia path traversal (..).
    """
    rel = rel.strip().replace("\\", "/")
    p = Path(rel)

    if p.is_absolute():
        raise ValueError(f"Caminho absoluto não permitido no dump: {rel}")

    # Bloqueia tentativa de escapar da pasta base (..)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"Path traversal detectado (..): {rel}")

    return Path(*p.parts)


def write_file(base_dir: Path, rel_path: str, content: str, overwrite: bool = True) -> None:
    target_rel = normalize_rel_path(rel_path)
    target = base_dir / target_rel

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not overwrite:
        print(f"[SKIP] {target_rel} (já existe)")
        return

    # Garante newline final
    if content and not content.endswith("\n"):
        content += "\n"

    target.write_text(content, encoding="utf-8")
    print(f"[OK]  {target_rel}")


def parse_dump(dump_text: str) -> list[tuple[str, str]]:
    """
    Retorna lista de (rel_path, content) extraídos do dump.
    """
    lines = dump_text.splitlines()
    i = 0
    out: list[tuple[str, str]] = []

    while i < len(lines):
        m = START_RE.match(lines[i])
        if not m:
            i += 1
            continue

        rel_path = m.group(1).strip()
        i += 1
        buf: list[str] = []

        # Lê até encontrar END_FILE (pode vir com nome diferente, a gente aceita qualquer)
        while i < len(lines):
            endm = END_RE.match(lines[i])
            if endm:
                i += 1
                break
            buf.append(lines[i])
            i += 1

        content = "\n".join(buf)
        out.append((rel_path, content))

    if not out:
        raise RuntimeError("Nenhum bloco START_FILE/END_FILE encontrado. Confira se o dump.txt está completo.")
    return out


def main() -> int:
    base_dir = Path.cwd()
    dump_path = base_dir / "dump.txt"

    if not dump_path.exists():
        print("ERRO: dump.txt não encontrado na pasta atual.")
        print(f"Pasta atual: {base_dir}")
        print("Crie o dump.txt e cole o conteúdo do dump dentro dele.")
        return 1

    dump_text = dump_path.read_text(encoding="utf-8", errors="replace")

    try:
        files = parse_dump(dump_text)
    except Exception as e:
        print(f"ERRO ao ler dump: {e}")
        return 1

    # Confirmação rápida: mostra quantos arquivos vai criar
    print(f"Encontrados {len(files)} arquivos no dump.")
    overwrite = True  # se quiser não sobrescrever, troque para False

    # Escreve
    try:
        for rel_path, content in files:
            write_file(base_dir, rel_path, content, overwrite=overwrite)
    except Exception as e:
        print(f"ERRO ao escrever arquivos: {e}")
        return 1

    print("\nConcluído ✅")
    print("Agora rode:  uvicorn app.main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
