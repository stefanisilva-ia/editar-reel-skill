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
MODOS_TEXTO = {"resumo", "transcricao"}
LEGENDA_PADRAO = {"palavras_por_bloco": 4, "posicao": "baixo", "destaques": []}
TIPOS_CARTAO = {"numero", "lista", "palavra"}
PASTA_SKILL = Path(__file__).resolve().parent.parent
FIM_DE_FRASE = (".", "?", "!", ",", ";", ":")


def estilo_padrao():
    """Estilo base: o do código, coberto pelo estilo-padrao.json da skill (se existir)."""
    estilo = dict(ESTILO_PADRAO)
    arq = PASTA_SKILL / "estilo-padrao.json"
    if arq.exists():
        try:
            estilo.update({k: v for k, v in json.loads(arq.read_text(encoding="utf-8")).items() if not k.startswith("_")})
        except json.JSONDecodeError:
            print(f"Aviso: {arq} tem erro de formatação e foi ignorado.")
    return estilo
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
    plano.setdefault("modo_texto", "resumo")
    legenda = dict(LEGENDA_PADRAO)
    legenda.update(plano.get("legenda") or {})
    plano["legenda"] = legenda
    plano.setdefault("correcoes", {})
    plano.setdefault("zoom", {"ativo": True, "fator": 1.12, "altura_rosto": 0.35})
    for chave in ("trechos", "textos", "imagens", "cartoes", "sons"):
        plano.setdefault(chave, [])
    for t in plano["trechos"]:
        t.setdefault("video", 1)
    estilo = estilo_padrao()
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
    if plano.get("modo_texto", "resumo") not in MODOS_TEXTO:
        problemas.append(f"modo_texto deve ser um de {sorted(MODOS_TEXTO)}.")
    if plano.get("modo_texto") == "transcricao" and pasta and not (Path(pasta) / "transcricao.json").exists():
        problemas.append("Modo transcrição precisa do transcricao.json na pasta de trabalho.")

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

    for i, c in enumerate(plano["cartoes"], 1):
        rotulo = f"Cartão {i} ({c.get('tipo')})"
        if c.get("tipo") not in TIPOS_CARTAO:
            problemas.append(f"{rotulo}: tipo deve ser um de {sorted(TIPOS_CARTAO)}.")
        elif c["tipo"] == "numero" and not c.get("valor"):
            problemas.append(f"{rotulo}: falta 'valor'.")
        elif c["tipo"] == "lista" and not (1 <= len(c.get("itens") or []) <= 4):
            problemas.append(f"{rotulo}: 'itens' precisa ter de 1 a 4 itens.")
        elif c["tipo"] == "palavra" and not c.get("texto"):
            problemas.append(f"{rotulo}: falta 'texto'.")
        _checar_ancora(c, rotulo, ids, ids_mantidos, problemas)

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


def _normal(palavra):
    return palavra.strip(".,;:!?\"'*()").lower()


def palavras_finais(plano, pasta, finais):
    """Cada palavra dos trechos mantidos com o seu tempo no vídeo final."""
    if not pasta or not (Path(pasta) / "transcricao.json").exists():
        return []
    dados = json.loads((Path(pasta) / "transcricao.json").read_text(encoding="utf-8"))
    videos = dados.get("videos") or [dados]
    vel = float(plano.get("velocidade") or 1.0)
    saida = []
    for f in finais:
        for p in videos[f["video"] - 1]["palavras"]:
            if f["inicio_original"] <= p["i"] < f["fim_original"]:
                ini = f["inicio_final"] + (p["i"] - f["inicio_original"]) / vel
                fim = f["inicio_final"] + (min(p["f"], f["fim_original"]) - f["inicio_original"]) / vel
                saida.append({"p": p["p"], "ini": round(ini, 3), "fim": round(fim, 3), "trecho": f["id"]})
    return saida


def achar_palavra(palavra, falas, desde=0.0, ate=None, trecho=None):
    """Tempo da primeira vez que a palavra (ou expressão) é dita a partir de 'desde'."""
    alvo = [_normal(w) for w in str(palavra).split()]
    for i in range(len(falas) - len(alvo) + 1):
        f = falas[i]
        if f["ini"] < desde - 0.01 or (ate is not None and f["ini"] > ate):
            continue
        if trecho is not None and f["trecho"] != trecho:
            continue
        if [_normal(x["p"]) for x in falas[i:i + len(alvo)]] == alvo:
            return f["ini"]
    return None


def _ancorar(itens, por_id, total, falas=(), dur_padrao_fim=2.5, avisos=None):
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
            if it.get("palavra"):
                achado = achar_palavra(it["palavra"], falas, a["inicio_final"], b["fim_final"])
                if achado is not None:
                    ini = achado + float(it.get("atraso", 0.0))
                elif avisos is not None:
                    avisos.append(f"Palavra '{it['palavra']}' não encontrada no trecho {it.get('trecho')}; usei o início do trecho.")
            fim = max(b["fim_final"], ini + 0.4)
            if it.get("duracao"):
                fim = min(total, ini + float(it["duracao"]))
        novo = {**it, "inicio_final": round(ini, 3), "fim_final": round(fim, 3)}
        if it.get("tipo") == "lista" and it.get("itens"):
            novo["itens_tempo"] = _tempos_dos_itens(it, novo, falas, avisos)
        saida.append(novo)
    return saida


def _tempos_dos_itens(cfg, ancorado, falas, avisos):
    """Quando cada item de uma lista acende: na palavra dita ou em passos regulares."""
    ini, fim = ancorado["inicio_final"], ancorado["fim_final"]
    n = len(cfg["itens"])
    passo = max(0.4, min(1.2, (fim - ini) * 0.7 / max(n, 1)))
    tempos_itens = []
    palavras = cfg.get("palavras") or []
    for k in range(n):
        t = ini + 0.35 + k * passo
        if k < len(palavras) and palavras[k]:
            achado = achar_palavra(palavras[k], falas, (tempos_itens[-1] if tempos_itens else ini) - 0.05, fim)
            if achado is not None:
                t = achado
            elif avisos is not None:
                avisos.append(f"Palavra '{palavras[k]}' da lista não encontrada; usei um tempo regular.")
        if tempos_itens:
            t = max(t, tempos_itens[-1] + 0.15)
        tempos_itens.append(round(min(t, fim - 0.2), 3))
    return tempos_itens


def _corrigir(palavra, correcoes):
    nucleo = palavra.strip(".,;:!?\"'")
    for errado, certo in correcoes.items():
        if nucleo.lower() == errado.lower():
            return palavra.replace(nucleo, certo)
    return palavra


def legendas_da_fala(plano, falas):
    """Modo transcrição: blocos de legenda com o tempo de cada palavra (para a palavra ativa)."""
    n_max = max(1, int(plano["legenda"].get("palavras_por_bloco", 4)))
    correcoes = plano.get("correcoes") or {}
    destaques = {d.lower() for d in plano["legenda"].get("destaques") or []}

    grupos, atual = [], []
    for k, p in enumerate(falas):
        if atual and p["trecho"] != atual[-1]["trecho"]:
            grupos.append(atual)
            atual = []
        atual.append(p)
        if len(atual) >= n_max or p["p"].endswith(FIM_DE_FRASE):
            grupos.append(atual)
            atual = []
    if atual:
        grupos.append(atual)

    saida = []
    for n, grupo in enumerate(grupos):
        ini = grupo[0]["ini"]
        if n + 1 < len(grupos) and grupos[n + 1][0]["trecho"] == grupo[0]["trecho"]:
            fim = grupos[n + 1][0]["ini"]
        else:
            fim = max(grupo[-1]["fim"] + 0.15, ini + 0.25)
        palavras = []
        for p in grupo:
            w = _corrigir(p["p"], correcoes)
            nucleo = w.rstrip(".,;:!?")
            if nucleo.strip("\"'").lower() in destaques:
                w = f"*{nucleo}*{w[len(nucleo):]}"
            palavras.append(w)
        palavras[-1] = palavras[-1].rstrip(".,;:")
        inicios, cont = [], 0
        for w in palavras:
            inicios.append(cont)
            cont += len(w.split())
        saida.append({
            "indices": inicios,
            "texto": " ".join(palavras), "tipo": "legenda", "posicao": plano["legenda"].get("posicao", "baixo"),
            "inicio_final": round(ini, 3), "fim_final": round(fim, 3),
            "palavras_ini": [p["ini"] for p in grupo],
        })
    for a, b in zip(saida, saida[1:]):
        a["fim_final"] = min(a["fim_final"], b["inicio_final"])
    return saida


def tempos(plano, pasta=None):
    """Converte a âncora de textos, imagens, cartões e sons em segundos do vídeo final."""
    finais, total = linha_do_tempo(plano)
    por_id = {f["id"]: f for f in finais}
    falas = palavras_finais(plano, pasta, finais)
    avisos = []
    textos = _ancorar(plano["textos"], por_id, total, falas, avisos=avisos)
    legendas = []
    if plano.get("modo_texto") == "transcricao" and falas:
        legendas = legendas_da_fala(plano, falas)
    return {
        "textos": textos,
        "legendas": legendas,
        "imagens": _ancorar(plano["imagens"], por_id, total, falas, avisos=avisos),
        "cartoes": _ancorar(plano["cartoes"], por_id, total, falas, avisos=avisos),
        "sons": _ancorar(plano["sons"], por_id, total, falas, avisos=avisos),
        "total": total,
        "avisos": avisos,
    }


def tempos_dos_textos(plano, pasta=None):
    t = tempos(plano, pasta)
    return t["legendas"] + t["textos"], t["total"]
