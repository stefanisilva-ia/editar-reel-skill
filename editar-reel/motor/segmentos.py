"""Divide a transcrição em trechos (uma ideia por trecho) e cria o plano.json.

Um trecho termina quando:
  - há uma pausa maior que PAUSA segundos entre duas palavras, ou
  - a palavra termina com ponto, interrogação ou exclamação.
As pausas entre trechos ficam de fora do vídeo final.

Com vários vídeos, os trechos seguem a ordem dos vídeos e cada trecho
guarda de qual vídeo veio (campo "video", começando em 1).
"""
import json
from pathlib import Path

from plano import ESTILO_PADRAO, salvar

PAUSA = 0.45
FOLGA_INICIO = 0.08
FOLGA_FIM = 0.15
FIM_DE_FRASE = (".", "?", "!")


def _agrupar(palavras, pausa):
    grupos, atual = [], [palavras[0]]
    for anterior, p in zip(palavras, palavras[1:]):
        if (p["i"] - anterior["f"]) > pausa or anterior["p"].endswith(FIM_DE_FRASE):
            grupos.append(atual)
            atual = []
        atual.append(p)
    grupos.append(atual)
    return grupos


def segmentar(pasta, pausa=PAUSA):
    pasta = Path(pasta)
    dados = json.loads((pasta / "transcricao.json").read_text(encoding="utf-8"))
    videos = dados["videos"]

    trechos = []
    for nv, v in enumerate(videos, 1):
        if not v["palavras"]:
            print(f"Aviso: o vídeo {nv} não tem fala reconhecida e ficou de fora.")
            continue
        anterior_fim = 0.0
        for g in _agrupar(v["palavras"], pausa):
            ini = max(0.0, g[0]["i"] - FOLGA_INICIO, anterior_fim)
            fim = min(v["duracao"], g[-1]["f"] + FOLGA_FIM)
            anterior_fim = fim
            trechos.append({
                "id": len(trechos) + 1,
                "video": nv,
                "inicio": round(ini, 3),
                "fim": round(fim, 3),
                "fala": " ".join(p["p"] for p in g),
                "manter": True,
            })
    if not trechos:
        raise SystemExit("A transcrição está vazia. Os vídeos têm fala audível?")

    plano = {
        "videos": [v["arquivo"] for v in videos],
        "saida": "reel-final.mp4",
        "velocidade": 1.0,
        "zoom": {"ativo": True, "fator": 1.12, "altura_rosto": 0.35},
        "estilo": dict(ESTILO_PADRAO),
        "trechos": trechos,
        "textos": [],
        "imagens": [],
        "sons": [],
    }
    caminho = salvar(pasta, plano)
    return caminho, trechos
