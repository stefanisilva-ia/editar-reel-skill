"""Procura travessão e meia-risca nos arquivos de texto do repositório.

Uso: python3 testes/checar-texto.py   (sai com erro se achar algum)
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROIBIDOS = {chr(0x2014): "travessão", chr(0x2013): "meia-risca"}
EXTENSOES = {".md", ".py", ".sh", ".ps1", ".json", ".txt", ".html", ".js", ".css"}
IGNORAR = {".git", ".venv", "__pycache__", "sons-basicos"}

achados = 0
for arq in sorted(RAIZ.rglob("*")):
    if arq.suffix not in EXTENSOES or any(parte in IGNORAR for parte in arq.parts):
        continue
    for n, linha in enumerate(arq.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        for ch, nome in PROIBIDOS.items():
            if ch in linha:
                print(f"{arq.relative_to(RAIZ)}:{n}: {nome}: {linha.strip()[:90]}")
                achados += 1
print("Nenhum travessão encontrado." if not achados else f"{achados} ocorrência(s).")
sys.exit(1 if achados else 0)
