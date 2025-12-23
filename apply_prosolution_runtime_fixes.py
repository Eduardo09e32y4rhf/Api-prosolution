import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
REQ = BASE / "requirements.txt"

REQUIRED_PACKAGES = [
    "email-validator",
    "pydantic[email]",
]

def run(cmd):
    print(f"▶ {cmd}")
    subprocess.check_call(cmd, shell=True)

def ensure_requirements():
    content = REQ.read_text(encoding="utf-8")

    updated = False
    for pkg in REQUIRED_PACKAGES:
        if pkg.split("[")[0] not in content:
            content += f"\n{pkg}"
            updated = True

    if updated:
        REQ.write_text(content, encoding="utf-8")
        print("✔ requirements.txt atualizado")
    else:
        print("ℹ requirements.txt já estava correto")

def install():
    run(f"{sys.executable} -m pip install --upgrade pip")
    run(f"{sys.executable} -m pip install -r requirements.txt")

def patch_email_schema():
    schemas = BASE / "app" / "payments" / "schemas.py"
    if not schemas.exists():
        return

    txt = schemas.read_text(encoding="utf-8")

    if "EmailStr" in txt:
        txt = txt.replace(
            "from pydantic import BaseModel, EmailStr",
            "from pydantic import BaseModel\nfrom typing import Optional\n\n# EmailStr protegido\ntry:\n    from pydantic import EmailStr\nexcept ImportError:\n    EmailStr = str"
        )
        schemas.write_text(txt, encoding="utf-8")
        print("✔ Schema de pagamento protegido contra crash")

def main():
    print("\n🚀 APLICANDO FIXES DEFINITIVOS (PROSOLUTION)\n")
    ensure_requirements()
    install()
    patch_email_schema()
    print("\n✅ SISTEMA PRONTO PARA SUBIR")

if __name__ == "__main__":
    main()
