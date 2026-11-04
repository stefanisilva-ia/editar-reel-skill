"""Divide a transcrição em trechos (uma ideia por trecho) e cria o plano.json.

Um trecho termina quando:
  - há uma pausa maior que PAUSA segundos entre duas palavras, ou
  - a palavra termina com ponto, interrogação ou exclamação.
As pausas entre trechos ficam de fora do vídeo final.
"""
import json
from pathlib import Path

from plano import ESTILO_PADRAO, salvar

PAUSA = 0.45
FOLGA_INICIO = 0.08
FOLGA_FIM = 0.15
FIM_DE_FRASE = (".", "?", "!")


def segmentar(pasta, pausa=PAUSA):
    pasta = Path(pasta)
    dados = json.loads((pasta / "transcricao.json").read_text(encoding="utf-8"))
    palavras = dados["palavras"]
    duracao = dados["duracao"]
    if not palavras:
        raise SystemExit("A transcrição está vazia. O vídeo tem fala audível?")

    grupos, atual = [], [palavras[0]]
    for anterior, p in zip(palavras, palavras[1:]):
        quebra = (p["i"] - anterior["f"]) > pausa or anterior["p"].endswith(FIM_DE_FRASE)
        if quebra:
            grupos.append(atual)
            atual = []
        atual.append(p)
    grupos.append(atual)

    trechos = []
    for n, g in enumerate(grupos, 1):
        ini = max(0.0, g[0]["i"] - FOLGA_INICIO)
        fim = min(duracao, g[-1]["f"] + FOLGA_FIM)
        if trechos and ini < trechos[-1]["fim"]:
            ini = trechos[-1]["fim"]
        trechos.append({
            "id": n,
            "inicio": round(ini, 3),
            "fim": round(fim, 3),
            "fala": " ".join(p["p"] for p in g),
            "manter": True,
        })

    plano = {
        "video": dados["video"],
        "saida": "reel-final.mp4",
        "velocidade": 1.0,
        "zoom": {"ativo": True, "fator": 1.12, "altura_rosto": 0.35},
        "estilo": dict(ESTILO_PADRAO),
        "trechos": trechos,
        "textos": [],
    }
    caminho = salvar(pasta, plano)
    return caminho, trechos
