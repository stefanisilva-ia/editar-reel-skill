#!/usr/bin/env bash
# Instala a skill editar-reel no Claude Code (Mac e Linux).
set -e

ORIGEM="$(cd "$(dirname "$0")" && pwd)/editar-reel"
DESTINO="$HOME/.claude/skills/editar-reel"

echo "Instalando editar-reel em $DESTINO"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Falta o ffmpeg."
  if [ "$(uname)" = "Darwin" ]; then echo "  Instale com: brew install ffmpeg"; else echo "  Instale com: sudo apt install ffmpeg"; fi
  exit 1
fi

PY=""
for c in python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; assert sys.version_info >= (3,9)' 2>/dev/null; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "Falta Python 3.9 ou mais novo."
  exit 1
fi

mkdir -p "$DESTINO"
# Atualiza os arquivos e mantém a .venv que já existir.
rsync -a --delete --exclude ".venv" "$ORIGEM/" "$DESTINO/" 2>/dev/null || {
  find "$DESTINO" -mindepth 1 -maxdepth 1 ! -name ".venv" -exec rm -rf {} +
  cp -R "$ORIGEM/." "$DESTINO/"
}

if [ ! -x "$DESTINO/.venv/bin/python" ]; then
  "$PY" -m venv "$DESTINO/.venv"
fi
"$DESTINO/.venv/bin/python" -m pip install --quiet --upgrade pip
"$DESTINO/.venv/bin/python" -m pip install --quiet -r "$DESTINO/requirements.txt"

"$DESTINO/.venv/bin/python" "$DESTINO/motor/cli.py" checar || true
echo
echo "Pronto. No Claude Code, chame /editar-reel"
