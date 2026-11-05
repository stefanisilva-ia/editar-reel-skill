#!/usr/bin/env bash
# Teste rápido da editar-reel, sem baixar o modelo de transcrição.
# Gera dois vídeos sintéticos, uma transcrição falsa, um print e roda o fluxo inteiro:
# segmentar, estilo, sons, validar, renderizar e quadros.
# Uso: bash testes/teste-rapido.sh [pasta-de-saida]
set -e

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
M="$RAIZ/editar-reel/motor/cli.py"
PY="${PYTHON:-python3}"
T="${1:-$(mktemp -d)}"
mkdir -p "$T/prints" "$T/estilo" "$T/reel"
cd "$T"

ffmpeg -y -loglevel error -f lavfi -i testsrc2=s=1920x1080:r=30:d=8 -f lavfi -i "sine=f=440:d=8" -c:v libx264 -preset veryfast -c:a aac -shortest parte1.mp4
ffmpeg -y -loglevel error -f lavfi -i "smptebars=s=1080x1920:r=25:d=6" -c:v libx264 -preset veryfast parte2.mp4
"$PY" -c "
from PIL import Image, ImageDraw
im = Image.new('RGB', (1400, 900), '#f4f4f4'); d = ImageDraw.Draw(im)
d.rectangle([0, 0, 1400, 90], fill='#07544a'); d.rectangle([80, 180, 700, 700], fill='#289a8b')
im.save('prints/painel.png')"
printf "destaque: #FF5A1F\nfundo da caixa: #1B1B3A\ntexto: #FFFFFF\n" > estilo/cores.md

cat > reel/transcricao.json <<EOF
{"videos": [
 {"arquivo": "$T/parte1.mp4", "duracao": 8.0, "palavras": [
  {"p":"O","i":0.2,"f":0.3},{"p":"agente","i":0.35,"f":0.8},{"p":"economiza","i":0.85,"f":1.5},{"p":"10","i":1.55,"f":1.8},{"p":"horas.","i":1.85,"f":2.3},
  {"p":"Olha","i":2.8,"f":3.2},{"p":"o","i":3.25,"f":3.35},{"p":"painel.","i":3.4,"f":5.0},
  {"p":"Ele","i":5.6,"f":5.8},{"p":"atende,","i":5.85,"f":6.3},{"p":"agenda","i":6.4,"f":6.8},{"p":"e","i":6.85,"f":6.9},{"p":"confirma.","i":6.95,"f":7.6}]},
 {"arquivo": "$T/parte2.mp4", "duracao": 6.0, "palavras": [
  {"p":"Comenta","i":0.3,"f":0.8},{"p":"AGENTE.","i":0.85,"f":1.8}]}]}
EOF

"$PY" "$M" segmentar reel
"$PY" "$M" sons > /dev/null
SONS="$RAIZ/editar-reel/sons-basicos"
"$PY" - <<EOF
import json
p = json.load(open("reel/plano.json"))
p["modo_texto"] = "transcricao"
p["legenda"] = {"palavras_por_bloco": 3, "destaques": ["agente", "agenda", "confirma"]}
p["trechos"][-1]["transicao"] = "fade"
p["textos"] = [{"texto": "agente que *economiza* tempo", "tipo": "capa", "trecho": 1, "duracao": 1.3},
               {"texto": "comenta AGENTE", "tipo": "chamada", "duracao": 1.5}]
p["cartoes"] = [{"tipo": "numero", "valor": "10h", "rotulo": "economizadas por semana", "trecho": 1, "palavra": "10"},
                {"tipo": "lista", "titulo": "O que o agente faz", "itens": ["1º atende", "2º agenda", "3º confirma"],
                 "palavras": ["atende", "agenda", "confirma"], "som_itens": True, "trecho": 3}]
p["imagens"] = [{"arquivo": "$T/prints/painel.png", "trecho": 2, "palavra": "painel", "credito": "print: teste"}]
p["sons"] = [{"arquivo": "$SONS/pop.wav", "trecho": 1, "palavra": "10", "volume": 0.6}]
json.dump(p, open("reel/plano.json", "w"), ensure_ascii=False, indent=2)
EOF
"$PY" "$M" estilo estilo --aplicar reel > /dev/null
"$PY" "$M" validar reel
"$PY" "$M" renderizar reel
"$PY" "$M" quadros reel > /dev/null
ffmpeg -i reel/reel-final.mp4 -af ebur128=framelog=quiet -f null - 2>&1 | grep -E "^\s+I:" || true
echo
echo "Teste ok. Vídeo: $T/reel/reel-final.mp4"
echo "Quadros para conferir: $T/reel/quadros/"
