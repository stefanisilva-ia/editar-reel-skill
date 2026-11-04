"""Leitura, validação e linha do tempo do plano.json.

O plano.json é o único arquivo de trabalho da skill. Ele guarda:
  - os vídeos de origem, na ordem da edição
  - os trechos da fala (vídeo, início, fim, se ficam, transição de entrada)
  - os textos na tela, os prints e os efeitos sonoros, todos ancorados
    em trechos (não em segundos), para continuarem no lugar se os cortes mudarem
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

TIPOS = {"capa", "bloco", "lista", "chamada"}
POSICOES = {"alto", "centro", "baixo"}
TRANSICOES = {"corte", "fade", "flash", "zoom"}


def carregar(pasta):
    caminho = Path(pasta) / "plano.json"
    if not caminho.exists():
        raise SystemExit(f"Não achei {caminho}. Rode o comando 'segmentar' antes.")
    plano = json.loads(caminho.read_text(encoding="utf-8"))
    if "video" in plano and "videos" not in plano:
        plano["videos"] = [plano.pop("video")]
    plano.setdefault("velocidade", 1.0)
    plano.setdefault("zoom", {"ativo": True, "fator": 1.12, "altura_rosto": 0.35})
    for chave in ("trechos", "textos", "imagens", "sons"):
        plano.setdefault(chave, [])
    for t in plano["trechos"]:
        t.setdefault("video", 1)
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


def _checar_ancora(item, rotulo, ids, ids_mantidos, problemas):
    trecho = item.get("trecho")
    if trecho not in ids:
        problemas.append(f"{rotulo}: trecho {trecho} não existe.")
    elif trecho not in ids_mantidos:
        problemas.append(f"{rotulo}: está no trecho {trecho}, que foi cortado.")
    ate = item.get("ate_trecho")
    if ate is not None and ate not in ids_mantidos:
        problemas.append(f"{rotulo}: ate_trecho {ate} não existe ou foi cortado.")


def validar(plano, pasta=None):
    """Devolve a lista de problemas. Lista vazia significa plano pronto."""
    problemas = []
    base = Path(pasta) if pasta else Path(".")

    for n, v in enumerate(plano["videos"], 1):
        if not Path(v).expanduser().exists():
            problemas.append(f"Vídeo {n} não encontrado: {v}")

    ids = {t["id"] for t in plano["trechos"]}
    mantidos = [t for t in plano["trechos"] if t.get("manter", True)]
    if not mantidos:
        problemas.append("Nenhum trecho marcado para ficar.")
    ids_mantidos = {t["id"] for t in mantidos}
    for t in plano["trechos"]:
        if not 1 <= t["video"] <= len(plano["videos"]):
            problemas.append(f"Trecho {t['id']}: vídeo {t['video']} não existe.")
        if t.get("transicao", "corte") not in TRANSICOES:
            problemas.append(f"Trecho {t['id']}: transição deve ser uma de {sorted(TRANSICOES)}.")
    ordem = plano.get("ordem")
    if ordem:
        faltando = [i for i in ordem if i not in ids]
        if faltando:
            problemas.append(f"'ordem' cita trechos que não existem: {faltando}.")

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
        if tx.get("tipo") != "chamada":
            _checar_ancora(tx, rotulo, ids, ids_mantidos, problemas)

    for i, im in enumerate(plano["imagens"], 1):
        rotulo = f"Imagem {i} ({im.get('arquivo')})"
        if not im.get("arquivo") or not Path(im["arquivo"]).expanduser().exists():
            problemas.append(f"{rotulo}: arquivo não encontrado.")
        if im.get("posicao", "centro") not in POSICOES:
            problemas.append(f"{rotulo}: posição deve ser uma de {sorted(POSICOES)}.")
        _checar_ancora(im, rotulo, ids, ids_mantidos, problemas)

    for i, s in enumerate(plano["sons"], 1):
        rotulo = f"Som {i} ({s.get('arquivo')})"
        if not s.get("arquivo") or not Path(s["arquivo"]).expanduser().exists():
            problemas.append(f"{rotulo}: arquivo não encontrado.")
        _checar_ancora(s, rotulo, ids, ids_mantidos, problemas)
    return problemas


def linha_do_tempo(plano):
    """Calcula onde cada trecho mantido cai no vídeo final (já com a velocidade)."""
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
            "video": t.get("video", 1),
            "transicao": t.get("transicao", "corte"),
            "inicio_original": t["inicio"],
            "fim_original": t["fim"],
            "inicio_final": cursor,
            "fim_final": cursor + dur,
        })
        cursor += dur
    return finais, cursor


def _ancorar(itens, por_id, total, dur_padrao_fim=2.5):
    saida = []
    for it in itens:
        if it.get("tipo") == "chamada":
            dur = float(it.get("duracao", dur_padrao_fim))
            ini, fim = max(0.0, total - dur), total
        else:
            a = por_id.get(it.get("trecho"))
            if a is None:
                continue
            b = por_id.get(it.get("ate_trecho"), a)
            ini = a["inicio_final"] + float(it.get("atraso", 0.0))
            fim = max(b["fim_final"], ini + 0.4)
            if it.get("duracao"):
                fim = min(total, ini + float(it["duracao"]))
        saida.append({**it, "inicio_final": round(ini, 3), "fim_final": round(fim, 3)})
    return saida


def tempos(plano):
    """Converte a âncora de textos, imagens e sons em segundos do vídeo final."""
    finais, total = linha_do_tempo(plano)
    por_id = {f["id"]: f for f in finais}
    return {
        "textos": _ancorar(plano["textos"], por_id, total),
        "imagens": _ancorar(plano["imagens"], por_id, total),
        "sons": _ancorar(plano["sons"], por_id, total),
        "total": total,
    }


def tempos_dos_textos(plano):
    t = tempos(plano)
    return t["textos"], t["total"]
