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

from visual import (FORMATOS, PAINEL_GRANDE, PAINEL_PADRAO, RECEITA_BASE, area_da_peca, cor_do_fundo,
                    montar_receita, tema, y_legenda)

MAX_PALAVRAS = 6

ESTILO_PADRAO = {
    "cor_texto": "#FFFFFF",
    "cor_destaque": "#DFAC16",
    "cor_caixa": "#03332CD9",
    "cor_contorno": "#000000",
    "cor_texto_claro": "#111111",
    "cor_destaque_claro": "#07544A",
    "cor_alerta": "#C9473A",
    "cor_apoio": "#289A8B",
    "caixa": True,
    "raio": 24,
    "fonte": None,
    "fonte_destaque": None,
    "fonte_rotulo": None,
    "tamanho": 68,
    "maiusculas": False,
}

TIPOS = {"capa", "bloco", "lista", "chamada", "manchete"}
MODOS_TEXTO = {"resumo", "transcricao"}
LEGENDA_PADRAO = {"palavras_por_bloco": 2, "destaques": [], "alertas": [], "caixa_em": [], "nomes": []}
TIPOS_CARTAO = {"numero", "lista", "palavra", "fluxo", "comparacao"}
TIPOS_ANOTACAO = {"circulo", "caixa", "marca", "sublinhado", "seta"}
SONS_BASICOS = {"pop", "click", "ding", "impacto", "whoosh"}
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
    plano.setdefault("modo_texto", "transcricao")
    try:
        plano["_receita"] = montar_receita(plano.get("receita"))
    except (ValueError, json.JSONDecodeError) as e:
        plano["_receita"] = montar_receita(None)
        plano["_erro_receita"] = str(e)
    legenda = dict(LEGENDA_PADRAO)
    legenda.update(plano["_receita"].get("legenda") or {})
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
    if any(s.get("arquivo") in SONS_BASICOS for s in plano["sons"]):
        from sons import garantir
        basicos = garantir()
        for s in plano["sons"]:
            if s.get("arquivo") in SONS_BASICOS:
                s["arquivo"] = str(basicos[s["arquivo"]][0])
    return plano


def salvar(pasta, plano):
    caminho = Path(pasta) / "plano.json"
    limpo = {k: v for k, v in plano.items() if not k.startswith("_")}
    caminho.write_text(json.dumps(limpo, ensure_ascii=False, indent=2), encoding="utf-8")
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


def _numero_entre(valor, lo, hi):
    try:
        return lo <= float(valor) <= hi
    except (TypeError, ValueError):
        return False


def validar(plano, pasta=None):
    """Devolve a lista de problemas. Lista vazia significa plano pronto."""
    problemas = []
    if plano.get("_erro_receita"):
        problemas.append(f"Receita: {plano['_erro_receita']}")
    if plano.get("modo_texto", "transcricao") not in MODOS_TEXTO:
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
        r = f"Trecho {t['id']}"
        if not 1 <= t["video"] <= len(plano["videos"]):
            problemas.append(f"{r}: vídeo {t['video']} não existe.")
        if t.get("transicao", "corte") not in TRANSICOES:
            problemas.append(f"{r}: transição deve ser uma de {sorted(TRANSICOES)}.")
        if str(t.get("formato", "A")).upper() not in FORMATOS:
            problemas.append(f"{r}: formato deve ser A, B ou C.")
        if t.get("fundo") and not cor_do_fundo(t["fundo"], plano["estilo"]):
            problemas.append(f"{r}: fundo '{t['fundo']}' não existe. Use um nome da paleta ou #RRGGBB.")
        if t.get("painel") is not None and not _numero_entre(t["painel"], 0.30, 0.50):
            problemas.append(f"{r}: painel deve ficar entre 0.30 e 0.50.")
        if t.get("zoom") is not None and not _numero_entre(t["zoom"], 1.0, 1.3):
            problemas.append(f"{r}: zoom deve ficar entre 1.0 e 1.3.")
        if t.get("inclinacao") is not None and not _numero_entre(t["inclinacao"], -4, 4):
            problemas.append(f"{r}: inclinacao deve ficar entre -4 e 4 graus.")
    ordem = plano.get("ordem")
    if ordem:
        faltando = [i for i in ordem if i not in ids]
        if faltando:
            problemas.append(f"'ordem' cita trechos que não existem: {faltando}.")

    selo = plano.get("selo")
    if selo is not None and not (isinstance(selo, dict) and selo.get("serie")):
        problemas.append("Selo: precisa de 'serie' (e, se quiser, 'parte' e 'total').")

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
        if im.get("inclinacao") is not None and not _numero_entre(im["inclinacao"], -4, 4):
            problemas.append(f"{rotulo}: inclinacao deve ficar entre -4 e 4 graus.")
        if im.get("pilula") and contar_palavras(im["pilula"]) > MAX_PALAVRAS:
            problemas.append(f"{rotulo}: a pílula passa de {MAX_PALAVRAS} palavras.")
        for k, an in enumerate(im.get("anotacoes") or [], 1):
            if an.get("tipo") not in TIPOS_ANOTACAO:
                problemas.append(f"{rotulo}, anotação {k}: tipo deve ser um de {sorted(TIPOS_ANOTACAO)}.")
            area = an.get("area")
            if not (isinstance(area, list) and len(area) == 4 and all(isinstance(v, (int, float)) for v in area)):
                problemas.append(f"{rotulo}, anotação {k}: 'area' precisa ser [x, y, largura, altura].")
        _checar_ancora(im, rotulo, ids, ids_mantidos, problemas)

    for i, c in enumerate(plano["cartoes"], 1):
        rotulo = f"Cartão {i} ({c.get('tipo')})"
        tipo = c.get("tipo")
        if tipo not in TIPOS_CARTAO:
            problemas.append(f"{rotulo}: tipo deve ser um de {sorted(TIPOS_CARTAO)}.")
        elif tipo == "numero" and not c.get("valor"):
            problemas.append(f"{rotulo}: falta 'valor'.")
        elif tipo == "lista" and not (1 <= len(c.get("itens") or []) <= 4):
            problemas.append(f"{rotulo}: 'itens' precisa ter de 1 a 4 itens.")
        elif tipo == "fluxo" and not (2 <= len(c.get("itens") or []) <= 5):
            problemas.append(f"{rotulo}: 'itens' precisa ter de 2 a 5 etapas.")
        elif tipo == "comparacao" and not (c.get("esquerda") and c.get("direita")):
            problemas.append(f"{rotulo}: precisa de 'esquerda' e 'direita', cada um com 'titulo' e 'itens'.")
        elif tipo == "palavra" and not c.get("texto"):
            problemas.append(f"{rotulo}: falta 'texto'.")
        _checar_ancora(c, rotulo, ids, ids_mantidos, problemas)

    for i, s in enumerate(plano["sons"], 1):
        rotulo = f"Som {i} ({s.get('arquivo')})"
        if not s.get("arquivo") or not Path(s["arquivo"]).expanduser().exists():
            problemas.append(f"{rotulo}: arquivo não encontrado.")
        _checar_ancora(s, rotulo, ids, ids_mantidos, problemas)
    return problemas


def linha_do_tempo(plano):
    """Calcula onde cada trecho mantido cai no vídeo final (já com a velocidade) e o visual dele."""
    v = float(plano.get("velocidade") or 1.0)
    receita = plano.get("_receita") or RECEITA_BASE
    estilo = plano.get("estilo") or {}
    fundo_padrao = receita["fundos"].get("padrao", "verde-profundo")
    grandes = {im.get("trecho") for im in plano.get("imagens", []) if im.get("grande")}
    cursor = 0.0
    finais = []
    ordem = plano.get("ordem") or [t["id"] for t in plano["trechos"]]
    por_id = {t["id"]: t for t in plano["trechos"]}
    for tid in ordem:
        t = por_id[tid]
        if not t.get("manter", True):
            continue
        dur = (t["fim"] - t["inicio"]) / v
        formato = str(t.get("formato", "A")).upper()
        nome_fundo = t.get("fundo") or fundo_padrao
        fundo = cor_do_fundo(nome_fundo, estilo) or cor_do_fundo(fundo_padrao, estilo) or "#03332C"
        painel = float(t["painel"]) if t.get("painel") else (PAINEL_GRANDE if tid in grandes else PAINEL_PADRAO)
        finais.append({
            "id": tid,
            "video": t.get("video", 1),
            "transicao": t.get("transicao", "corte"),
            "inicio_original": t["inicio"],
            "fim_original": t["fim"],
            "inicio_final": cursor,
            "fim_final": cursor + dur,
            "formato": formato,
            "fundo": fundo,
            "fundo_nome": nome_fundo if formato != "A" else "",
            "painel": painel,
            "tema": tema(formato, fundo),
            "zoom": t.get("zoom"),
            "inclinacao": float(t.get("inclinacao") or 0),
            "fala": t.get("fala", ""),
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
        tipo = it.get("tipo")
        if tipo in ("lista", "fluxo") and it.get("itens"):
            novo["itens_tempo"] = _tempos_de_marcos(len(it["itens"]), it.get("palavras") or [], novo, falas, avisos)
        elif tipo == "comparacao":
            novo["itens_tempo"] = _tempos_de_marcos(2, it.get("palavras") or [], novo, falas, avisos)
        if it.get("anotacoes"):
            palavras = [an.get("palavra") for an in it["anotacoes"]]
            novo["anotacoes_tempo"] = _tempos_de_marcos(len(palavras), palavras, novo, falas, avisos, 0.5)
        saida.append(novo)
    return saida


def _tempos_de_marcos(n, palavras, ancorado, falas, avisos, primeiro=0.35):
    """Quando cada item acende (lista, fluxo, anotação): na palavra dita ou em passos regulares."""
    ini, fim = ancorado["inicio_final"], ancorado["fim_final"]
    passo = max(0.4, min(1.2, (fim - ini) * 0.7 / max(n, 1)))
    marcos = []
    for k in range(n):
        t = ini + primeiro + k * passo
        if k < len(palavras) and palavras[k]:
            achado = achar_palavra(palavras[k], falas, (marcos[-1] if marcos else ini) - 0.05, fim)
            if achado is not None:
                t = achado
            elif avisos is not None:
                avisos.append(f"Palavra '{palavras[k]}' não encontrada depois da anterior; usei um tempo regular.")
        if marcos:
            t = max(t, marcos[-1] + 0.15)
        marcos.append(round(min(t, fim - 0.2), 3))
    return marcos


# Legenda da fala

def _frases(lista):
    """Separa expressões de uma palavra e de várias: (set de palavras, [listas de palavras])."""
    simples, compostas = set(), []
    for item in lista or []:
        partes = [_normal(w) for w in str(item).split() if _normal(w)]
        if len(partes) == 1:
            simples.add(partes[0])
        elif partes:
            compostas.append(partes)
    return simples, compostas


def _marcar(palavras, lista):
    """Índices das palavras que fazem parte de algum item da lista (inclui expressões)."""
    simples, compostas = _frases(lista)
    norm = [_normal(p["p"]) for p in palavras]
    marcados = {i for i, w in enumerate(norm) if w in simples}
    for frase in compostas:
        n = len(frase)
        for i in range(len(norm) - n + 1):
            if norm[i:i + n] == frase:
                marcados.update(range(i, i + n))
    return marcados


def _aplicar_correcoes(falas, correcoes):
    """Corrige palavras e expressões escritas errado na transcrição ("claude code": "Claude Code")."""
    if not correcoes:
        return list(falas)
    regras = sorted(((k.split(), v.split()) for k, v in correcoes.items()), key=lambda r: -len(r[0]))
    saida, i = [], 0
    while i < len(falas):
        for errado, certo in regras:
            n = len(errado)
            janela = falas[i:i + n]
            if len(janela) == n and len({p["trecho"] for p in janela}) == 1 and \
                    [_normal(p["p"]) for p in janela] == [_normal(w) for w in errado]:
                fim_pont = janela[-1]["p"][len(janela[-1]["p"].rstrip(".,;:!?")):]
                if len(certo) == n:
                    novas = [{**p, "p": w} for p, w in zip(janela, certo)]
                else:
                    novas = [{**janela[0], "p": " ".join(certo), "fim": janela[-1]["fim"]}]
                novas[-1]["p"] += fim_pont
                saida.extend(novas)
                i += n
                break
        else:
            saida.append(falas[i])
            i += 1
    return saida


def legendas_da_fala(plano, falas):
    """Blocos da legenda com o tempo de cada palavra (para a palavra acender quando é dita)."""
    leg = plano["legenda"]
    n_max = max(1, int(leg.get("palavras_por_bloco", 2)))
    correcoes = plano.get("correcoes") or {}
    falas = _aplicar_correcoes(falas, correcoes)
    nomes = list(leg.get("nomes") or []) + [v for v in correcoes.values() if " " in v]
    destaques, alertas, caixas = _marcar(falas, leg.get("destaques")), _marcar(falas, leg.get("alertas")), _marcar(falas, leg.get("caixa_em"))
    presos = set()
    for frase in _frases(nomes)[1]:
        n = len(frase)
        norm = [_normal(p["p"]) for p in falas]
        for i in range(len(norm) - n + 1):
            if norm[i:i + n] == frase:
                presos.update(range(i, i + n - 1))

    grupos, atual = [], []
    for k, p in enumerate(falas):
        if atual and p["trecho"] != atual[-1][1]["trecho"]:
            grupos.append(atual)
            atual = []
        atual.append((k, p))
        if k in presos:
            continue
        if len(atual) >= n_max or p["p"].endswith(FIM_DE_FRASE):
            grupos.append(atual)
            atual = []
    if atual:
        grupos.append(atual)

    saida = []
    for n, grupo in enumerate(grupos):
        ini = grupo[0][1]["ini"]
        if n + 1 < len(grupos) and grupos[n + 1][0][1]["trecho"] == grupo[0][1]["trecho"]:
            fim = grupos[n + 1][0][1]["ini"]
        else:
            fim = max(grupo[-1][1]["fim"] + 0.15, ini + 0.25)
        palavras = []
        for k, p in grupo:
            t = p["p"].replace("*", "").rstrip(",.;:").strip()
            if not t:
                continue
            nucleo = _normal(t)
            tipo = None
            if k in caixas:
                tipo = "caixa"
            elif k in alertas:
                tipo = "alerta"
            elif k in destaques or re.search(r"\d", nucleo):
                tipo = "destaque"
            palavras.append({"t": t, "tipo": tipo})
        if not palavras:
            continue
        saida.append({
            "palavras": palavras,
            "texto": " ".join(w["t"] for w in palavras),
            "tipo": "legenda",
            "trecho": grupo[0][1]["trecho"],
            "inicio_final": round(ini, 3), "fim_final": round(fim, 3),
            "palavras_ini": [p["ini"] for _, p in grupo if p["p"].replace("*", "").rstrip(",.;:").strip()],
        })
    for a, b in zip(saida, saida[1:]):
        a["fim_final"] = min(a["fim_final"], b["inicio_final"])
    return saida


# Contexto visual de cada peça

def _sobrepoe(a_ini, a_fim, b_ini, b_fim):
    return a_ini < b_fim - 0.01 and b_ini < a_fim - 0.01


def tempos(plano, pasta=None):
    """Converte a âncora de textos, imagens, cartões e sons em segundos e põe cada peça no seu formato."""
    finais, total = linha_do_tempo(plano)
    por_id = {f["id"]: f for f in finais}
    falas = palavras_finais(plano, pasta, finais)
    avisos = []
    textos = _ancorar(plano["textos"], por_id, total, falas, avisos=avisos)
    imagens = _ancorar(plano["imagens"], por_id, total, falas, avisos=avisos)
    cartoes = _ancorar(plano["cartoes"], por_id, total, falas, avisos=avisos)
    sons = _ancorar(plano["sons"], por_id, total, falas, avisos=avisos)
    legendas = []
    if plano.get("modo_texto") == "transcricao" and falas:
        legendas = legendas_da_fala(plano, falas)

    def trecho_de(item):
        if item.get("tipo") == "chamada" or item.get("trecho") not in por_id:
            return finais[-1] if finais else None
        return por_id[item["trecho"]]

    manchetes = [tx for tx in textos if tx.get("tipo") == "manchete"]
    faixas_manchete = []
    for m in manchetes:
        for f in finais:
            if f["formato"] != "A" and _sobrepoe(m["inicio_final"], m["fim_final"], f["inicio_final"], f["fim_final"]):
                faixas_manchete.append((max(m["inicio_final"], f["inicio_final"]), min(m["fim_final"], f["fim_final"])))

    def com_manchete(ini):
        return any(a - 0.01 <= ini < b for a, b in faixas_manchete)

    grandes_c = [(im["inicio_final"], im["fim_final"]) for im in imagens
                 if im.get("grande") and trecho_de(im) and trecho_de(im)["formato"] == "C"]

    for item in textos + imagens + cartoes:
        f = trecho_de(item)
        if not f:
            continue
        item["_formato"], item["_tema"], item["_painel"] = f["formato"], f["tema"], f["painel"]
        item["_fundo"] = f["fundo"] if f["formato"] != "A" else None
        if f["formato"] != "A" and item.get("tipo") not in ("manchete", "chamada"):
            item["_area"] = area_da_peca(f["formato"], f["painel"], com_manchete(item["inicio_final"]), bool(item.get("grande")))
        b = por_id.get(item.get("ate_trecho"))
        if b and b["formato"] != f["formato"] and item.get("tipo") != "manchete":
            avisos.append(f"{item.get('tipo') or Path(item.get('arquivo', '')).name} vai do trecho {f['id']} ({f['formato']}) "
                          f"ao {b['id']} ({b['formato']}); a posição segue o formato do primeiro.")

    chamadas = [tx for tx in textos if tx.get("tipo") == "chamada"]
    if chamadas:
        corte = min(c["inicio_final"] for c in chamadas)
        legendas = [lg for lg in legendas if lg["inicio_final"] < corte - 0.05]
        for lg in legendas:
            lg["fim_final"] = min(lg["fim_final"], corte)
    for lg in legendas:
        f = por_id[lg["trecho"]]
        grande = f["formato"] == "C" and any(_sobrepoe(lg["inicio_final"], lg["fim_final"], a, b) for a, b in grandes_c)
        lg["_formato"], lg["_tema"] = f["formato"], f["tema"]
        lg["_fundo"] = f["fundo"] if f["formato"] != "A" else None
        lg["_y"] = y_legenda(f["formato"], f["painel"], grande)

    return {
        "textos": textos,
        "legendas": legendas,
        "imagens": imagens,
        "cartoes": cartoes,
        "sons": sons,
        "finais": finais,
        "total": total,
        "avisos": avisos + avisos_de_ritmo(finais, total),
    }


def tempos_dos_textos(plano, pasta=None):
    t = tempos(plano, pasta)
    return t["legendas"] + t["textos"], t["total"]


# Ritmo e mapa visual

def _sequencias(finais):
    grupos = []
    for f in finais:
        if grupos and grupos[-1][0]["formato"] == f["formato"]:
            grupos[-1].append(f)
        else:
            grupos.append([f])
    return grupos


def avisos_de_ritmo(finais, total):
    """Confere as regras de ritmo da direção visual. Só vale quando o vídeo usa B ou C."""
    if not finais or all(f["formato"] == "A" for f in finais):
        return []
    avisos = []
    if finais[0]["formato"] != "B":
        avisos.append("Ritmo: a abertura pede B nos primeiros segundos.")
    if finais[-1]["formato"] != "A":
        avisos.append("Ritmo: o fechamento pede A, com a chamada.")
    rosto = sum(f["fim_final"] - f["inicio_final"] for f in finais if f["formato"] != "C")
    if total and rosto / total < 0.5:
        avisos.append(f"Ritmo: o rosto aparece em {rosto / total:.0%} do vídeo; o mínimo é 50%.")
    for grupo in _sequencias(finais):
        dur = grupo[-1]["fim_final"] - grupo[0]["inicio_final"]
        ids = ", ".join(str(f["id"]) for f in grupo)
        if grupo[0]["formato"] == "C" and dur > 6.0:
            avisos.append(f"Ritmo: só gráficos por {dur:.1f} s seguidos (trechos {ids}); o máximo é 6 s.")
        elif len(grupo) >= 3 and dur > 5.0:
            avisos.append(f"Ritmo: formato {grupo[0]['formato']} em {len(grupo)} trechos seguidos ({dur:.1f} s, trechos {ids}).")
    return avisos


def mapa(plano, pasta=None):
    """Linhas do mapa visual: um trecho mantido por linha, com formato, fundo, peças e sons."""
    t = tempos(plano, pasta)
    pecas, sons = {}, {}
    for tx in t["textos"]:
        if tx.get("tipo") != "chamada":
            pecas.setdefault(tx.get("trecho"), []).append(f"{tx.get('tipo', 'bloco')}: {tx['texto']}")
    for im in t["imagens"]:
        extra = f" ({len(im['anotacoes'])} marcações)" if im.get("anotacoes") else ""
        pecas.setdefault(im.get("trecho"), []).append(f"print {Path(im['arquivo']).name}{extra}")
    for c in t["cartoes"]:
        desc = c.get("valor") or c.get("texto") or c.get("titulo") or ", ".join(c.get("itens", [])[:3])
        if c["tipo"] == "comparacao":
            desc = f"{(c.get('esquerda') or {}).get('titulo', '')} x {(c.get('direita') or {}).get('titulo', '')}"
        pecas.setdefault(c.get("trecho"), []).append(f"{c['tipo']}: {desc}")
    for s in t["sons"]:
        sons.setdefault(s.get("trecho"), []).append(Path(s["arquivo"]).stem)
    linhas = []
    for f in t["finais"]:
        linhas.append({
            "id": f["id"], "inicio": f["inicio_final"], "duracao": f["fim_final"] - f["inicio_final"],
            "fala": f["fala"], "formato": f["formato"], "fundo": f["fundo_nome"] or "-",
            "pecas": "; ".join(pecas.get(f["id"], [])) or "-", "sons": ", ".join(sons.get(f["id"], [])) or "-",
        })
    chamada = [(tx["inicio_final"], tx["texto"]) for tx in t["textos"] if tx.get("tipo") == "chamada"]
    return linhas, t, chamada
