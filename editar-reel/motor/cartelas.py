"""Desenha textos e cartões como imagens transparentes 1080x1920.

Fontes: as da pasta fontes/ da skill vêm primeiro (Montserrat para o texto,
Playfair Display Italic para destaques, DM Sans para rótulos). O estilo pode
trocar cada uma: "fonte", "fonte_destaque", "fonte_rotulo".

Cada peça recebe do plano o formato do trecho (_formato: A, B ou C) e o tema
(_tema: video, escuro ou claro), que decidem posição, tamanho e cores.

Destaque automático nos textos de resumo (capa, bloco, lista):
  - palavras entre asteriscos: "pronto em *10 minutos*"
  - números e ordinais: 10, 24H, 3x, 1º, 2º
"""
import platform
import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from visual import ALTURA, LARGURA, PAINEL_PADRAO, area_da_peca, cores_do_tema
from visual import cor as _cor

LARGURA_MAX_TEXTO = 900
PASTA_FONTES = Path(__file__).resolve().parent.parent / "fontes"
FONTE_TEXTO, FONTE_DESTAQUE, FONTE_ROTULO = "Montserrat", "Playfair Display", "DM Sans"
OURO = ("#DFAC16", "#AB8208")
APAGADA = 0.45

# Centro vertical de cada posição (fração da altura), usado no formato A.
POSICAO_Y = {"alto": 0.22, "centro": 0.50, "baixo": 0.70}
POSICAO_PADRAO = {"capa": "alto", "bloco": "baixo", "lista": "baixo", "chamada": "centro", "legenda": "baixo"}
ESCALA = {"capa": 1.45, "bloco": 1.0, "lista": 1.0, "chamada": 1.2, "legenda": 0.9}
# Legenda da fala por formato: (tamanho, peso)
LEGENDA_FORMATO = {"A": (64, 600), "B": (56, 600), "C": (76, 700)}

PASTAS_DE_FONTES = [
    "~/Library/Fonts", "/Library/Fonts", "/System/Library/Fonts", "/System/Library/Fonts/Supplemental",
    "C:/Windows/Fonts", "~/AppData/Local/Microsoft/Windows/Fonts",
    "~/.local/share/fonts", "~/.fonts", "/usr/share/fonts", "/usr/local/share/fonts",
]
PESOS = ["extrabold", "black", "bold", "semibold", "medium", "regular", ""]
FONTES_SISTEMA = {
    "Darwin": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf"],
    "Windows": ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"],
    "Linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
}

NUMERO = re.compile(r"\d")
ORDINAL = re.compile(r"^\d+[ºª°]$")


# Fontes

def _normal(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _da_skill(nome):
    alvo = _normal(nome)
    for arq in sorted(PASTA_FONTES.glob("*")):
        if arq.suffix.lower() in (".ttf", ".otf") and alvo in _normal(arq.stem):
            return str(arq)
    return None


def _por_nome(nome):
    """Procura uma fonte instalada pelo nome da família, preferindo pesos fortes."""
    alvo = _normal(nome)
    achadas = []
    for pasta in PASTAS_DE_FONTES:
        raiz = Path(pasta).expanduser()
        if not raiz.is_dir():
            continue
        for arq in raiz.rglob("*"):
            if arq.suffix.lower() in (".ttf", ".otf") and alvo in _normal(arq.stem):
                achadas.append(arq)
    if not achadas:
        return None

    def nota(arq):
        nome_arq = arq.stem.lower()
        italico = "italic" in nome_arq
        for i, peso in enumerate(PESOS):
            if peso and peso in nome_arq:
                return (italico, i)
        return (italico, len(PESOS))
    return str(sorted(achadas, key=nota)[0])


@lru_cache(maxsize=64)
def achar_fonte(preferida=None):
    if preferida:
        caminho = Path(preferida).expanduser()
        if caminho.is_file():
            return str(caminho)
        if caminho.suffix.lower() not in (".ttf", ".otf"):
            achada = _da_skill(preferida) or _por_nome(preferida)
            if achada:
                return achada
        print(f"Aviso: não achei a fonte '{preferida}', usando a padrão da skill.")
    padrao = _da_skill(FONTE_TEXTO)
    if padrao:
        return padrao
    for c in FONTES_SISTEMA.get(platform.system(), []) + sum(FONTES_SISTEMA.values(), []):
        if Path(c).expanduser().exists():
            return str(Path(c).expanduser())
    return None


@lru_cache(maxsize=512)
def _fonte(caminho, tamanho, peso=700):
    """Fonte no tamanho pedido. Em fonte variável, aplica o peso (e o tamanho óptico)."""
    tamanho = max(8, int(tamanho))
    if not caminho:
        return ImageFont.load_default(size=tamanho)
    f = ImageFont.truetype(caminho, tamanho)
    try:
        eixos = f.get_variation_axes()
    except Exception:
        return f
    valores = []
    for e in eixos:
        nome = e.get("name", b"")
        nome = nome.decode("utf-8", "ignore") if isinstance(nome, bytes) else str(nome)
        lo, hi = e["minimum"], e["maximum"]
        if "eight" in nome:
            v = peso
        elif "ptical" in nome:
            v = tamanho * 0.5
        else:
            v = e.get("default", lo)
        valores.append(max(lo, min(hi, v)))
    try:
        f.set_variation_by_axes(valores)
    except Exception:
        pass
    return f


def f_texto(estilo, tamanho, peso=700):
    return _fonte(achar_fonte(estilo.get("fonte") or FONTE_TEXTO), int(tamanho), peso)


def f_destaque(estilo, tamanho, peso=500):
    return _fonte(achar_fonte(estilo.get("fonte_destaque") or FONTE_DESTAQUE), int(tamanho), peso)


def f_rotulo(estilo, tamanho, peso=500):
    return _fonte(achar_fonte(estilo.get("fonte_rotulo") or FONTE_ROTULO), int(tamanho), peso)


def _escala(estilo):
    return float(estilo.get("tamanho") or 68) / 68


def _ouro(estilo, tema):
    """Gradiente dourado quando o destaque é o dourado padrão e o fundo não é claro."""
    if tema != "claro" and str(estilo.get("cor_destaque", "")).upper().startswith(OURO[0]):
        return {"gradiente": OURO}
    return {}


def _apagar(c, fator=APAGADA):
    return c[:3] + (int(c[3] * fator),)


# Texto em linhas com fontes misturadas

def _peca(t, fonte, cor, **extra):
    return {"t": t, "f": fonte, "cor": cor, **extra}


def _linhas(pecas, largura_max):
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    linhas, atual, w = [], [], 0.0
    for p in pecas:
        pad = p.get("pad", 0)
        pw = d.textlength(p["t"], font=p["f"]) + 2 * pad
        esp = d.textlength(" ", font=p["f"]) + (8 if pad else 0)
        if atual and w + esp + pw > largura_max:
            linhas.append((atual, w))
            atual, w = [], 0.0
        if not atual:
            esp = 0
        atual.append({**p, "w": pw, "esp": esp})
        w += esp + pw
    if atual:
        linhas.append((atual, w))
    return linhas


def _gradiente(w, h, c1, c2):
    g = Image.linear_gradient("L").resize((max(1, w), max(1, h)))
    return Image.composite(Image.new("RGBA", (w, h), _cor(c2)), Image.new("RGBA", (w, h), _cor(c1)), g)


def _desenhar_linhas(img, linhas, cy, sombra=False, entrelinha=1.08):
    """Desenha as linhas centradas na horizontal, com o bloco centrado em cy."""
    camada = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    metricas = [(max(p["f"].getmetrics()[0] for p in ln), max(p["f"].getmetrics()[1] for p in ln)) for ln, _ in linhas]
    alturas = [(a + b) * entrelinha for a, b in metricas]
    y = cy - sum(alturas) / 2
    for (linha, w), (asc, desc), h in zip(linhas, metricas, alturas):
        base = y + asc + (h - asc - desc) / 2
        x = (LARGURA - w) / 2
        for p in linha:
            x += p["esp"]
            pad = p.get("pad", 0)
            if p.get("caixa"):
                bx = d.textbbox((x + pad, base), p["t"], font=p["f"], anchor="ls")
                d.rounded_rectangle([x, bx[1] - 12, x + p["w"], bx[3] + 14], radius=16, fill=p["caixa"])
            if p.get("gradiente"):
                mascara = Image.new("L", (LARGURA, ALTURA), 0)
                ImageDraw.Draw(mascara).text((x + pad, base), p["t"], font=p["f"], fill=255, anchor="ls")
                bx = mascara.getbbox()
                if bx:
                    g = _gradiente(bx[2] - bx[0], bx[3] - bx[1], *p["gradiente"])
                    camada.paste(g, bx[:2], mascara.crop(bx))
            else:
                d.text((x + pad, base), p["t"], font=p["f"], fill=p["cor"], anchor="ls")
            x += p["w"]
        y += h
    if sombra:
        alfa = camada.getchannel("A").filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.65))
        s = Image.new("RGBA", camada.size, (0, 0, 0, 255))
        s.putalpha(alfa)
        img.alpha_composite(s, (0, 4))
    img.alpha_composite(camada)
    return img


def _marcadas(texto):
    """[(palavra, destaque)] com *marcação* e números em destaque."""
    saida, marcando = [], False
    for bruta in texto.split():
        limpa = bruta.replace("*", "")
        if not limpa:
            continue
        abre = bruta.startswith("*")
        fecha = bruta.rstrip(".,;:!?").endswith("*")
        destaque = marcando or abre or bool(NUMERO.search(limpa))
        if abre and not fecha:
            marcando = True
        if fecha:
            marcando = False
        saida.append((limpa, destaque))
    return saida


def _juntar(marcadas):
    """Agrupa palavras vizinhas com o mesmo destaque: [(texto, destaque)]."""
    grupos = []
    for p, dest in marcadas:
        if grupos and grupos[-1][1] == dest:
            grupos[-1] = (grupos[-1][0] + " " + p, dest)
        else:
            grupos.append((p, dest))
    return grupos


# Legenda da fala

def desenhar_legenda(bloco, estilo, destino, ativa=None):
    """Bloco da legenda. Palavras depois da ativa ficam apagadas (acendem ao serem ditas)."""
    formato = bloco.get("_formato", "A")
    c = cores_do_tema(bloco.get("_tema", "video"), estilo, bloco.get("_fundo"))
    tam, peso = LEGENDA_FORMATO.get(formato, LEGENDA_FORMATO["A"])
    tam = int(tam * _escala(estilo))
    fonte = f_texto(estilo, tam, peso)
    fonte_dest = f_destaque(estilo, int(tam * 1.15), 500)
    claro = bloco.get("_tema") == "claro"
    pecas = []
    for k, w in enumerate(bloco["palavras"]):
        t, tipo = w["t"], w.get("tipo")
        futura = ativa is not None and k > ativa
        extra = {}
        if tipo in ("destaque", "caixa", "alerta"):
            f, cor = fonte_dest, (c["alerta"] if tipo == "alerta" else c["destaque"])
            if tipo == "caixa":
                extra = {"caixa": _apagar(c["destaque"], APAGADA if futura else 1), "pad": 14}
                cor = _cor("#FFFFFF") if claro else _cor("#03332C")
        else:
            f, cor = fonte, c["texto"]
            if formato == "C":
                t = t.upper()
        if futura:
            cor = _apagar(cor)
        pecas.append(_peca(t, f, cor, **extra))
    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    _desenhar_linhas(img, _linhas(pecas, 920), bloco.get("_y", 1300), sombra=c["sombra"])
    img.save(destino)
    return destino


# Manchete, chamada, selo e palavra solta

def desenhar_manchete(cfg, estilo, destino, tema, modelo="solta", cy=280):
    """Resumo da seção no topo da área das peças. *palavra* sai em Playfair (ou em etiqueta)."""
    c = cores_do_tema(tema, estilo, cfg.get("_fundo"))
    esc = _escala(estilo)
    fonte = f_texto(estilo, 62 * esc, 800)
    fonte_dest = f_destaque(estilo, 72 * esc, 600)
    pecas = []
    for t, dest in _juntar(_marcadas(cfg["texto"])):
        if not dest:
            pecas.append(_peca(t.upper(), fonte, c["texto"]))
        elif modelo == "etiqueta":
            pecas.append(_peca(t, fonte_dest, _cor("#FFFFFF"), caixa=_cor(estilo["cor_destaque_claro"]), pad=18))
        else:
            pecas.append(_peca(t, fonte_dest, c["destaque"], **_ouro(estilo, tema)))
    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    _desenhar_linhas(img, _linhas(pecas, 960), cy)
    img.save(destino)
    return destino


def desenhar_chamada(cfg, estilo, destino, tema="video"):
    """Chamada final em três linhas: COMENTA, a palavra grande em Playfair, o complemento."""
    c = cores_do_tema(tema, estilo)
    palavras = cfg["texto"].split()
    chave = [i for i, p in enumerate(palavras) if p.startswith("*") or p.endswith("*")
             or (p.strip(".,!?\"'").isupper() and len(p.strip(".,!?\"'")) > 1)]
    if not chave:
        chave = [len(palavras) - 1]
    ini, fim = chave[0], chave[-1]
    antes = " ".join(palavras[:ini]).upper()
    meio = " ".join(palavras[ini:fim + 1]).replace("*", "")
    depois = " ".join(palavras[fim + 1:])
    esc = _escala(estilo)
    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    if antes:
        _desenhar_linhas(img, _linhas([_peca(antes, f_texto(estilo, 60 * esc, 800), c["texto"])], 960), 1340, c["sombra"])
    tam = 160 * esc
    d = ImageDraw.Draw(img)
    while tam > 70 and d.textlength(meio, font=f_destaque(estilo, tam, 600)) > 980:
        tam -= 8
    _desenhar_linhas(img, _linhas([_peca(meio, f_destaque(estilo, tam, 600), c["destaque"], **_ouro(estilo, tema))], 2000), 1470, c["sombra"])
    if depois:
        _desenhar_linhas(img, _linhas([_peca(depois, f_texto(estilo, 44 * esc, 600), c["texto"])], 960), 1590, c["sombra"])
    img.save(destino)
    return destino


def desenhar_selo(selo, estilo, destino):
    """Selo de série no topo: nome da série e 'parte X/Y' com barra de progresso."""
    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fonte = f_rotulo(estilo, 30, 500)
    fundo, borda = (3, 51, 44, 214), _cor(estilo["cor_apoio"])[:3] + (120,)
    texto = (236, 246, 242, 255)
    nome = str(selo.get("serie", "")).strip()
    parte, total = selo.get("parte"), selo.get("total")
    rotulo2 = f"parte {parte}/{total}" if parte and total else ""
    barra = 96 if rotulo2 else 0
    w1 = d.textlength(nome, font=fonte) + 48 if nome else 0
    w2 = d.textlength(rotulo2, font=fonte) + 48 + (barra + 16 if barra else 0) if rotulo2 else 0
    total_w = w1 + w2 + (14 if w1 and w2 else 0)
    x, y0, y1 = (LARGURA - total_w) / 2, 92, 148
    if w1:
        d.rounded_rectangle([x, y0, x + w1, y1], radius=28, fill=fundo, outline=borda, width=2)
        d.text((x + w1 / 2, (y0 + y1) / 2), nome, font=fonte, fill=texto, anchor="mm")
        x += w1 + 14
    if w2:
        d.rounded_rectangle([x, y0, x + w2, y1], radius=28, fill=fundo, outline=borda, width=2)
        tx = x + 24
        d.text((tx, (y0 + y1) / 2), rotulo2, font=fonte, fill=texto, anchor="lm")
        bx = tx + d.textlength(rotulo2, font=fonte) + 16
        by = (y0 + y1) / 2
        d.rounded_rectangle([bx, by - 5, bx + barra, by + 5], radius=5, fill=(255, 255, 255, 60))
        p = max(0.0, min(1.0, float(parte) / float(total)))
        d.rounded_rectangle([bx, by - 5, bx + max(10, barra * p), by + 5], radius=5, fill=_cor(estilo["cor_destaque"]))
    img.save(destino)
    return destino


def _centro_da_peca(cfg, padrao_a):
    area = cfg.get("_area")
    if area:
        return (area[0] + area[1]) // 2
    return int(ALTURA * padrao_a)


def desenhar_palavra_solta(cfg, estilo, destino, progresso=1.0):
    """Uma palavra grande em Playfair. progresso < 1 desenha a entrada (desfoque para o nítido)."""
    tema = cfg.get("_tema", "video")
    c = cores_do_tema(tema, estilo)
    texto = cfg["texto"]
    cy = 860 if cfg.get("_formato") == "C" and not cfg.get("posicao") else _centro_da_peca(cfg, {"alto": 0.30, "centro": 0.42, "baixo": 0.58}[cfg.get("posicao", "centro")])
    tam = 170 * _escala(estilo)
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    while tam > 70 and d.textlength(texto, font=f_destaque(estilo, tam, 500)) > 960:
        tam -= 8
    camada = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    _desenhar_linhas(camada, _linhas([_peca(texto, f_destaque(estilo, tam, 500), c["destaque"], **_ouro(estilo, tema))], 980), cy, c["sombra"])
    if progresso < 1:
        e = 1 - (1 - progresso) ** 3
        esc = 0.94 + 0.06 * e
        w, h = int(LARGURA * esc), int(ALTURA * esc)
        menor = camada.resize((w, h), Image.LANCZOS)
        camada = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
        camada.alpha_composite(menor, ((LARGURA - w) // 2, int(cy - cy * esc)))
        raio = 16 * (1 - e)
        if raio > 0.5:
            camada = camada.filter(ImageFilter.GaussianBlur(raio))
        camada.putalpha(camada.getchannel("A").point(lambda v: int(v * (0.2 + 0.8 * e))))
    camada.save(destino)
    return destino


# Textos de resumo (capa, bloco, lista)

def separar(texto, tipo, maiusculas=False):
    """Quebra o texto em palavras e marca quais vão em destaque."""
    saida, marcando = [], False
    for bruta in texto.split():
        limpa = bruta.replace("*", "")
        if not limpa:
            continue
        abre = bruta.startswith("*")
        fecha = bruta.rstrip(".,;:!?").endswith("*")
        destaque = marcando or abre
        if NUMERO.search(limpa) or ORDINAL.match(limpa):
            destaque = True
        if tipo == "chamada" and limpa.isupper() and len(limpa) > 1:
            destaque = True
        if abre and not fecha:
            marcando = True
        if fecha:
            marcando = False
        saida.append((limpa.upper() if maiusculas else limpa, destaque))
    return saida


def desenhar(texto_cfg, estilo, destino):
    """Texto de resumo (capa, bloco, lista) em caixa ou solto, como sempre foi."""
    tipo = texto_cfg.get("tipo", "bloco")
    posicao = texto_cfg.get("posicao") or POSICAO_PADRAO.get(tipo, "baixo")
    tamanho = int(estilo["tamanho"] * ESCALA.get(tipo, 1.0))
    fonte = _fonte(achar_fonte(estilo.get("fonte")), tamanho, 800)

    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    palavras = separar(texto_cfg["texto"], tipo, estilo.get("maiusculas", False))
    espaco = d.textlength(" ", font=fonte)
    linhas, atual, largura = [], [], 0.0
    for palavra, dest in palavras:
        w = d.textlength(palavra, font=fonte)
        extra = w if not atual else espaco + w
        if atual and largura + extra > LARGURA_MAX_TEXTO:
            linhas.append((atual, largura))
            atual, largura = [(palavra, dest, w)], w
        else:
            atual.append((palavra, dest, w))
            largura += extra
    if atual:
        linhas.append((atual, largura))

    asc, desc = fonte.getmetrics()
    altura_linha = int((asc + desc) * 1.12)
    bloco_h = altura_linha * len(linhas)
    bloco_w = max(w for _, w in linhas)
    cy = int(ALTURA * POSICAO_Y[posicao])
    area = texto_cfg.get("_area")
    if area and not texto_cfg.get("posicao"):
        cy = area[0] + 80 if tipo == "capa" else (area[0] + area[1]) // 2
    topo = cy - bloco_h // 2
    cor_texto, cor_dest = _cor(estilo["cor_texto"]), _cor(estilo["cor_destaque"])
    raio = int(estilo.get("raio", 28))
    cor_contorno = _cor(estilo.get("cor_contorno", "#000000"))
    if tipo == "capa" or not estilo.get("caixa", True):
        contorno = max(4, tamanho // 14)
    else:
        pad_x, pad_y = 38, 26
        caixa = [(LARGURA - bloco_w) / 2 - pad_x, topo - pad_y, (LARGURA + bloco_w) / 2 + pad_x, topo + bloco_h + pad_y]
        d.rounded_rectangle(caixa, radius=raio, fill=_cor(estilo["cor_caixa"]))
        contorno, cor_contorno = 0, None
    y = topo
    for linha, w in linhas:
        x = (LARGURA - w) / 2
        for palavra, dest, pw in linha:
            d.text((x, y), palavra, font=fonte, fill=cor_dest if dest else cor_texto,
                   stroke_width=contorno, stroke_fill=cor_contorno)
            x += pw + espaco
        y += altura_linha
    img.save(destino)
    return destino


# Cartões

def _visual_cartao(tema, estilo, receita):
    if tema == "video":
        fundo = list(_cor(estilo["cor_caixa"]))
        fundo[3] = max(fundo[3], 235)
        return {"cor": tuple(fundo), "borda": None, "raio": int(estilo.get("raio", 28)) + 8, "barra": True}
    cfg = ((receita or {}).get("cartoes") or {}).get(tema) or {}
    padrao = {"escuro": ("#07544AE6", "#289A8B66", 28), "claro": ("#FFFFFFE0", "#FFFFFFFF", 32)}[tema]
    return {"cor": _cor(cfg.get("cor", padrao[0])), "borda": _cor(cfg.get("borda", padrao[1])),
            "raio": int(cfg.get("raio", padrao[2])), "barra": False}


def _quebrar_texto(texto, fonte, d, largura_max):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = f"{atual} {palavra}".strip()
        if atual and d.textlength(teste, font=fonte) > largura_max:
            linhas.append(atual)
            atual = palavra
        else:
            atual = teste
    if atual:
        linhas.append(atual)
    return linhas


def _check(d, cx, cy, r, ligado, c):
    if ligado:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c["apoio"])
        d.line([(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)],
               fill=(255, 255, 255, 255), width=max(4, r // 4), joint="curve")
    else:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=_apagar(c["texto"], 0.4), width=4)


def _conteudo(cfg, estilo, c, largura, valor, visiveis):
    """Desenha o conteúdo do cartão numa camada e devolve (camada, altura usada)."""
    tipo = cfg["tipo"]
    camada = Image.new("RGBA", (largura, 1500), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    y = 0

    def texto_central(t, f, cor, esp):
        nonlocal y
        asc, desc = f.getmetrics()
        d.text((largura / 2, y + asc), t, font=f, fill=cor, anchor="ms")
        y += asc + desc + esp

    def titulo(esp=30):
        nonlocal y
        if cfg.get("titulo"):
            f = f_texto(estilo, 50, 800)
            for linha in _quebrar_texto(cfg["titulo"], f, d, largura):
                asc, desc = f.getmetrics()
                d.text((0, y + asc), linha, font=f, fill=c["texto"], anchor="ls")
                y += asc + desc + 6
            y += esp

    if tipo == "numero":
        valor = str(cfg["valor"]) if valor is None else valor
        texto_central(valor, f_texto(estilo, 190 if len(str(cfg["valor"])) <= 5 else 140, 800), c["destaque"], 14)
        if cfg.get("rotulo"):
            f = f_texto(estilo, 48, 600)
            for linha in _quebrar_texto(cfg["rotulo"], f, d, largura):
                texto_central(linha, f, c["texto"], 6)

    elif tipo == "lista":
        titulo()
        f = f_texto(estilo, 48, 600)
        asc, desc = f.getmetrics()
        check = cfg.get("check")
        for k, item in enumerate(cfg["itens"]):
            ligado = visiveis is None or k < visiveis
            if not check and not ligado:
                y += asc + desc + 24
                continue
            cor_t = c["texto"] if ligado else _apagar(c["texto"])
            x = 0
            if check:
                _check(d, 30, y + asc * 0.62, 26, ligado, c)
                x = 80
            partes = item.split(maxsplit=1)
            if len(partes) == 2 and ORDINAL.match(partes[0]):
                d.text((x, y + asc), partes[0] + " ", font=f, fill=c["destaque"] if ligado else _apagar(c["destaque"]), anchor="ls")
                x += d.textlength(partes[0] + " ", font=f)
                item = partes[1]
            for linha in _quebrar_texto(item, f, d, largura - x):
                d.text((x, y + asc), linha, font=f, fill=cor_t, anchor="ls")
                y += asc + desc + 4
            y += 20

    elif tipo == "fluxo":
        titulo(40)
        n = len(cfg["itens"])
        passo = largura / n
        lado = min(124, int(passo * 0.62))
        fn = f_texto(estilo, int(lado * 0.42), 800)
        fr = f_rotulo(estilo, 34 if n <= 4 else 30, 600)
        topo = y
        acesos = n if visiveis is None else visiveis
        for k in range(n - 1):
            x1 = passo * k + passo / 2 + lado / 2 + 8
            x2 = passo * (k + 1) + passo / 2 - lado / 2 - 8
            ligado = k + 1 < acesos
            d.line([(x1, topo + lado / 2), (x2, topo + lado / 2)], fill=c["apoio"] if ligado else _apagar(c["apoio"], 0.35), width=5)
        for k, item in enumerate(cfg["itens"]):
            cx = passo * k + passo / 2
            ligado = k < acesos
            caixa = [cx - lado / 2, topo, cx + lado / 2, topo + lado]
            if ligado:
                d.rounded_rectangle(caixa, radius=lado // 4, fill=_cor(estilo["cor_destaque_claro"]),
                                    outline=c["destaque"] if k == acesos - 1 else c["apoio"], width=4)
                cor_n = (255, 255, 255, 255)
            else:
                d.rounded_rectangle(caixa, radius=lado // 4, outline=_apagar(c["apoio"], 0.5), width=3)
                cor_n = _apagar(c["texto"], 0.4)
            d.text((cx, topo + lado / 2), str(k + 1), font=fn, fill=cor_n, anchor="mm")
            ly = topo + lado + 20
            for linha in _quebrar_texto(item, fr, d, passo - 12):
                asc, desc = fr.getmetrics()
                d.text((cx, ly + asc), linha, font=fr, fill=c["texto"] if ligado else _apagar(c["texto"], 0.4), anchor="ms")
                ly += asc + desc
            y = max(y, ly)

    elif tipo == "comparacao":
        lados = [cfg.get("esquerda") or {}, cfg.get("direita") or {}]
        gap = 28
        col = (largura - gap) / 2
        ft, fi = f_texto(estilo, 48, 800), f_texto(estilo, 40, 600)
        alturas = []
        for k, lado in enumerate(lados):
            ligado = visiveis is None or k < visiveis
            x0 = k * (col + gap)
            yy = 28
            cor_titulo = c["destaque"] if k == 1 else c["texto"]
            asc, desc = ft.getmetrics()
            d.text((x0 + col / 2, yy + asc), lado.get("titulo", ""), font=ft,
                   fill=cor_titulo if ligado else _apagar(cor_titulo, 0.35), anchor="ms")
            yy += asc + desc + 22
            for item in lado.get("itens", []):
                for linha in _quebrar_texto(item, fi, d, col - 40):
                    a, b = fi.getmetrics()
                    d.text((x0 + col / 2, yy + a), linha, font=fi, fill=c["texto"] if ligado else _apagar(c["texto"], 0.35), anchor="ms")
                    yy += a + b
                yy += 14
            alturas.append(yy + 14)
        h = max(alturas)
        for k in range(2):
            ligado = visiveis is None or k < visiveis
            x0 = k * (col + gap)
            cor_b = (c["destaque"] if k == 1 else _apagar(c["texto"], 0.35))
            d.rounded_rectangle([x0, 0, x0 + col, h], radius=24, outline=cor_b if ligado else _apagar(cor_b, 0.35), width=4 if k == 1 else 2)
        y = h

    return camada, int(y)


def desenhar_cartao(cfg, estilo, destino, valor=None, visiveis=None, receita=None):
    """Cartão ilustrativo na identidade do estilo e do fundo do trecho.

    tipo "numero":     {"valor": "10h", "rotulo": "economizadas por semana"}
    tipo "lista":      {"titulo": "...", "itens": ["1º atende", "2º agenda"], "check": false}
    tipo "fluxo":      {"titulo": "...", "itens": ["Gatilho", "Planilha", "IA", "E-mail"]}
    tipo "comparacao": {"esquerda": {"titulo": "Antes", "itens": [...]}, "direita": {...}}
    tipo "palavra":    {"texto": "sozinho"}  (palavra solta, sem cartão)
    """
    if cfg["tipo"] == "palavra":
        return desenhar_palavra_solta(cfg, estilo, destino)
    tema = cfg.get("_tema", "video")
    c = cores_do_tema(tema, estilo)
    if tema == "video":
        c["texto"], c["destaque"] = _cor(estilo["cor_texto"]), _cor(estilo["cor_destaque"])
    visual = _visual_cartao(tema, estilo, receita)
    largura = 940 if cfg.get("_area") else 860
    pad = 60
    conteudo, h = _conteudo(cfg, estilo, c, largura - 2 * pad, valor, visiveis)
    caixa_h = h + 2 * pad
    cy = _centro_da_peca(cfg, {"alto": 0.30, "centro": 0.42, "baixo": 0.58}[cfg.get("posicao", "centro")])
    if cfg.get("posicao") and cfg.get("_area"):
        topo, base = cfg["_area"]
        cy = {"alto": topo + caixa_h // 2, "centro": cy, "baixo": base - caixa_h // 2}[cfg["posicao"]]
    x0, y0 = (LARGURA - largura) // 2, cy - caixa_h // 2
    raio = visual["raio"]

    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    sombra = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([x0, y0 + 16, x0 + largura, y0 + caixa_h + 16], radius=raio,
                                             fill=(0, 0, 0, 70 if tema == "claro" else 130))
    img = Image.alpha_composite(img, sombra.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x0 + largura, y0 + caixa_h], radius=raio, fill=visual["cor"],
                        outline=visual["borda"], width=2 if visual["borda"] else 0)
    if visual["barra"]:
        d.rounded_rectangle([x0 + raio, y0, x0 + largura - raio, y0 + 8], radius=4, fill=c["destaque"])
    img.alpha_composite(conteudo.crop((0, 0, largura - 2 * pad, max(1, h))), (x0 + pad, y0 + pad))
    img.save(destino)
    return destino


NUMERO_CONTAVEL = re.compile(r"^(\D*?)(\d{1,3}(?:\.\d{3})+|\d+)(,\d+)?(.*)$")


def quadros_do_contador(valor, quadros=20):
    """Valores intermediários para o número subir até o final. None se não der para contar."""
    m = NUMERO_CONTAVEL.match(str(valor))
    if not m:
        return None
    prefixo, inteiro, decimal, sufixo = m.groups()
    milhar = "." in inteiro
    alvo = float(inteiro.replace(".", "") + ("." + decimal[1:] if decimal else ""))
    casas = len(decimal) - 1 if decimal else 0
    if alvo < 2 or re.search(r"\d", sufixo):
        return None
    saida = []
    for i in range(quadros):
        p = (i + 1) / quadros
        atual = alvo * (1 - (1 - p) ** 3)
        parte_int = int(atual) if casas else int(round(atual))
        texto = f"{parte_int:,}".replace(",", "." if milhar else "")
        if casas:
            texto += "," + f"{atual:.{casas}f}".split(".")[1]
        saida.append(f"{prefixo}{texto}{sufixo}")
    saida[-1] = str(valor)
    return saida


__all__ = ["achar_fonte", "desenhar", "desenhar_legenda", "desenhar_manchete", "desenhar_chamada",
           "desenhar_selo", "desenhar_palavra_solta", "desenhar_cartao", "quadros_do_contador",
           "f_texto", "f_destaque", "f_rotulo", "area_da_peca", "PAINEL_PADRAO"]
