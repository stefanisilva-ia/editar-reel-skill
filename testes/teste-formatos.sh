#!/usr/bin/env bash
# Teste dos formatos A, B e C e das peças da direção visual, sem baixar o modelo de transcrição.
# Gera uma "pessoa" sintética, um print de painel, uma transcrição falsa e um plano com
# receita combinada, selo, manchete, print anotado, fluxo, comparação, palavra solta,
# número, destaque em caixa, palavra de alerta e chamada. Roda mapa, validar, renderizar e quadros.
# Uso: bash testes/teste-formatos.sh [pasta-de-saida]
set -e

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
M="$RAIZ/editar-reel/motor/cli.py"
PY="${PYTHON:-python3}"
T="${1:-$(mktemp -d)}"
mkdir -p "$T/imagens" "$T/reel"
cd "$T"

"$PY" - <<'EOF'
from PIL import Image, ImageDraw
im = Image.new("RGB", (1080, 1920), "#C9B8A6"); d = ImageDraw.Draw(im)
d.rectangle([0, 1250, 1080, 1920], fill="#B5A08A")
d.ellipse([390, 470, 690, 830], fill="#E2B497")
d.rounded_rectangle([210, 860, 870, 1920], radius=220, fill="#2B4C7E")
d.ellipse([470, 610, 500, 640], fill="#333"); d.ellipse([580, 610, 610, 640], fill="#333")
im.save("pessoa.png")
p = Image.new("RGB", (1400, 900), "#F4F4F2"); d = ImageDraw.Draw(p)
d.rectangle([0, 0, 1400, 90], fill="#1E1E1E")
for k, y in enumerate((170, 240, 310, 380)):
    d.rounded_rectangle([80, y, 80 + (900 if k % 2 else 640), y + 34], radius=8, fill="#CFCFCB")
d.rounded_rectangle([980, 560, 1300, 650], radius=18, fill="#E8742A")
d.rounded_rectangle([80, 520, 760, 800], radius=18, fill="#DADAD5")
p.save("imagens/painel.png")
EOF
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i pessoa.png -f lavfi -i "sine=f=330:d=20" -t 20 \
  -vf "drawtext=text='%{pts\:hms}':x=40:y=1800:fontsize=40:fontcolor=white" -c:v libx264 -preset veryfast -pix_fmt yuv420p -c:a aac -shortest parte1.mp4
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i pessoa.png -f lavfi -i "sine=f=440:d=4" -t 4 \
  -c:v libx264 -preset veryfast -pix_fmt yuv420p -c:a aac -shortest parte2.mp4

"$PY" - "$T" <<'EOF'
import json, sys
T = sys.argv[1]
def frase(texto, ini, fim):
    ws = texto.split(); passo = (fim - ini) / len(ws)
    return [{"p": w, "i": round(ini + k * passo, 2), "f": round(ini + (k + 0.85) * passo, 2)} for k, w in enumerate(ws)]
v1 = []
for texto, a, b in [("Tu usa o claude code pra tudo?", 0.2, 2.4), ("Olha esse botão no painel.", 2.8, 5.0),
                    ("O fluxo tem quatro etapas.", 5.4, 7.4), ("Isso é proibido no plano grátis.", 7.8, 9.6),
                    ("Economiza 10 horas por semana.", 10.0, 12.0), ("Ele trabalha sozinho.", 12.4, 14.4),
                    ("Eu testei e ficou melhor.", 14.8, 17.0), ("Antes era manual, agora é automático.", 17.4, 19.4)]:
    v1 += frase(texto, a, b)
v2 = frase("Comenta AGENTE que eu te mando.", 0.3, 2.6)
json.dump({"videos": [{"arquivo": f"{T}/parte1.mp4", "duracao": 20.0, "palavras": v1},
                      {"arquivo": f"{T}/parte2.mp4", "duracao": 4.0, "palavras": v2}]},
          open("reel/transcricao.json", "w"), ensure_ascii=False)
EOF

"$PY" "$M" segmentar reel > /dev/null
"$PY" - "$T" <<'EOF'
import json, sys
T = sys.argv[1]
p = json.load(open("reel/plano.json"))
visual = {1: ("B", None), 2: ("B", None), 3: ("C", None), 4: ("C", "alerta"), 5: ("B", "areia"),
          6: ("C", "verde-profundo"), 7: ("A", None), 8: ("B", "off-white"), 9: ("A", None)}
for t in p["trechos"]:
    t["formato"], fundo = visual[t["id"]]
    if fundo:
        t["fundo"] = fundo
p["trechos"][6]["zoom"] = 1.2
p["receita"] = {"base": "escuro-tecnico", "prints": "print-anotado"}
p["selo"] = {"serie": "Claude na prática", "parte": 3, "total": 7}
p["correcoes"] = {"claude code": "Claude Code"}
p["legenda"] = {"destaques": ["Claude Code", "etapas", "automático"], "alertas": ["proibido"], "caixa_em": ["melhor"]}
p["textos"] = [{"texto": "o *Claude* certo pra cada tarefa", "tipo": "manchete", "trecho": 1, "ate_trecho": 2},
               {"texto": "comenta AGENTE que eu te mando", "tipo": "chamada", "duracao": 2.2}]
p["imagens"] = [{"arquivo": f"{T}/imagens/painel.png", "trecho": 2, "palavra": "olha", "pilula": "o botão que resolve",
                 "anotacoes": [{"tipo": "circulo", "area": [0.70, 0.62, 0.23, 0.10], "palavra": "botão"},
                               {"tipo": "marca", "area": [0.057, 0.19, 0.46, 0.04], "palavra": "painel"}],
                 "som_anotacoes": True}]
p["cartoes"] = [{"tipo": "fluxo", "titulo": "Do pedido à entrega", "itens": ["Gatilho", "Planilha", "IA", "E-mail"],
                 "palavras": ["fluxo", "tem", "quatro", "etapas"], "som_itens": True, "trecho": 3},
                {"tipo": "numero", "valor": "10h", "rotulo": "economizadas por semana", "trecho": 5, "palavra": "10"},
                {"tipo": "palavra", "texto": "sozinho", "trecho": 6, "palavra": "trabalha"},
                {"tipo": "comparacao", "esquerda": {"titulo": "Antes", "itens": ["manual", "3 horas"]},
                 "direita": {"titulo": "Agora", "itens": ["automático", "10 minutos"]}, "palavras": ["antes", "agora"], "trecho": 8},
                {"tipo": "lista", "check": True, "titulo": "Checklist", "itens": ["Entrada confiável", "Regra clara"],
                 "trecho": 4}]
p["sons"] = [{"arquivo": "whoosh", "trecho": 3, "volume": 0.5}, {"arquivo": "pop", "trecho": 6, "palavra": "trabalha", "volume": 0.5},
             {"arquivo": "ding", "trecho": 5, "palavra": "10", "volume": 0.5}]
json.dump(p, open("reel/plano.json", "w"), ensure_ascii=False, indent=2)
EOF

"$PY" "$M" mapa reel
"$PY" "$M" validar reel
"$PY" "$M" renderizar reel
"$PY" "$M" quadros reel > /dev/null
echo
echo "Teste ok. Vídeo: $T/reel/reel-final.mp4"
echo "Quadros para conferir: $T/reel/quadros/"
