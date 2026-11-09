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

from plano import salvar

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
        "modo_texto": "transcricao",
        "estilo": {},
        "trechos": trechos,
        "textos": [],
        "imagens": [],
        "sons": [],
    }
    caminho = salvar(pasta, plano)
    return caminho, trechos


VICIOS = {"é", "éé", "ééé", "eh", "ah", "ãh", "ã", "hum", "hmm", "uhm", "tipo", "né", "então", "assim", "bom", "enfim", "ok"}


def _limpo(texto):
    return [w.strip(".,;:!?\"'").lower() for w in texto.split() if w.strip(".,;:!?\"'")]


def sugerir_cortes(trechos):
    """Aponta trechos que provavelmente saem: vício solto e tomada repetida."""
    from difflib import SequenceMatcher
    sugestoes = []
    for t in trechos:
        palavras = _limpo(t["fala"])
        if palavras and all(p in VICIOS for p in palavras):
            sugestoes.append(f"Trecho {t['id']}: só vício de fala (\"{t['fala']}\").")
    for i, a in enumerate(trechos):
        pa = _limpo(a["fala"])
        if len(pa) < 2:
            continue
        for b in trechos[i + 1:i + 3]:
            if b.get("video") != a.get("video"):
                continue
            pb = _limpo(b["fala"])
            parecido = SequenceMatcher(None, " ".join(pa), " ".join(pb)).ratio()
            mesmo_comeco = len(pb) >= 3 and pa[:3] == pb[:3]
            if parecido > 0.6 or mesmo_comeco:
                sugestoes.append(f"Trecho {a['id']}: parece tomada repetida do trecho {b['id']}; fica o {b['id']}.")
                break
    return sugestoes
