"""Leitura, validação e linha do tempo do plano.json.

O plano.json é o único arquivo de trabalho da skill. Ele guarda:
  - os trechos da fala (com início e fim no vídeo original e se ficam ou saem)
  - os textos na tela (ancorados em trechos, não em segundos)
  - o estilo visual e as opções de exportação
"""
import json
import re
from pathlib import Path

MAX_PALAVRAS = 6

ESTILO_PADRAO = {
    "cor_texto": "#FFFFFF",
    "cor_destaque": "#FFD60A",
    "cor_caixa": "#000000B8",
    "fonte": None,
    "tamanho": 68,
    "maiusculas": False,
}

PADRAO = {
    "velocidade": 1.0,
    "zoom": {"ativo": True, "fator": 1.12, "altura_rosto": 0.35},
    "estilo": ESTILO_PADRAO,
    "trechos": [],
    "textos": [],
}

TIPOS = {"capa", "bloco", "lista", "chamada"}
POSICOES = {"alto", "centro", "baixo"}


def carregar(pasta):
    caminho = Path(pasta) / "plano.json"
    if not caminho.exists():
        raise SystemExit(f"Não achei {caminho}. Rode o comando 'segmentar' antes.")
    plano = json.loads(caminho.read_text(encoding="utf-8"))
    for chave, valor in PADRAO.items():
        plano.setdefault(chave, valor)
    estilo = dict(ESTILO_PADRAO)
    estilo.update(plano.get("estilo") or {})
    plano["estilo"] = estilo
    return plano


def salvar(pasta, plano):
    caminho = Path(pasta) / "plano.json"
    caminho.write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def contar_palavras(texto):
    limpo = texto.replace("*", " ")
    return len([p for p in re.split(r"\s+", limpo) if p])


def validar(plano):
    """Devolve a lista de problemas. Lista vazia significa plano pronto."""
    problemas = []
    ids = {t["id"] for t in plano["trechos"]}
    mantidos = [t for t in plano["trechos"] if t.get("manter", True)]
    if not mantidos:
        problemas.append("Nenhum trecho marcado para ficar.")
    ids_mantidos = {t["id"] for t in mantidos}

    for i, tx in enumerate(plano["textos"], 1):
        rotulo = f"Texto {i} ({tx.get('texto', '')!r})"
        if not tx.get("texto"):
            problemas.append(f"{rotulo}: está vazio.")
            continue
        n = contar_palavras(tx["texto"])
        if n > MAX_PALAVRAS:
            problemas.append(f"{rotulo}: tem {n} palavras, o máximo é {MAX_PALAVRAS}.")
        if tx.get("tipo", "bloco") not in TIPOS:
            problemas.append(f"{rotulo}: tipo deve ser um de {sorted(TIPOS)}.")
        if tx.get("posicao", "baixo") not in POSICOES:
            problemas.append(f"{rotulo}: posição deve ser uma de {sorted(POSICOES)}.")
        if tx.get("tipo") == "chamada":
            continue
        trecho = tx.get("trecho")
        if trecho not in ids:
            problemas.append(f"{rotulo}: trecho {trecho} não existe.")
        elif trecho not in ids_mantidos:
            problemas.append(f"{rotulo}: está no trecho {trecho}, que foi cortado.")
        ate = tx.get("ate_trecho")
        if ate is not None and ate not in ids_mantidos:
            problemas.append(f"{rotulo}: ate_trecho {ate} não existe ou foi cortado.")
    return problemas


def linha_do_tempo(plano):
    """Calcula onde cada trecho mantido cai no vídeo final (já com a velocidade).

    Devolve (trechos_finais, duracao_total). Cada trecho final tem
    id, inicio_original, fim_original, inicio_final, fim_final.
    """
    v = float(plano.get("velocidade") or 1.0)
    cursor = 0.0
    finais = []
    ordem = plano.get("ordem") or [t["id"] for t in plano["trechos"]]
    por_id = {t["id"]: t for t in plano["trechos"]}
    for tid in ordem:
        t = por_id[tid]
        if not t.get("manter", True):
            continue
        dur = (t["fim"] - t["inicio"]) / v
        finais.append({
            "id": tid,
            "inicio_original": t["inicio"],
            "fim_original": t["fim"],
            "inicio_final": cursor,
            "fim_final": cursor + dur,
        })
        cursor += dur
    return finais, cursor


def tempos_dos_textos(plano):
    """Converte a âncora de cada texto (trecho) em segundos do vídeo final."""
    finais, total = linha_do_tempo(plano)
    por_id = {f["id"]: f for f in finais}
    saida = []
    for tx in plano["textos"]:
        if tx.get("tipo") == "chamada":
            dur = float(tx.get("duracao", 2.5))
            ini, fim = max(0.0, total - dur), total
        else:
            a = por_id.get(tx.get("trecho"))
            if a is None:
                continue
            b = por_id.get(tx.get("ate_trecho"), a)
            ini = a["inicio_final"] + float(tx.get("atraso", 0.0))
            fim = max(b["fim_final"], ini + 0.4)
        saida.append({**tx, "inicio_final": round(ini, 3), "fim_final": round(fim, 3)})
    return saida, total
