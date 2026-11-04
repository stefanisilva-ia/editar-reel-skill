"""Desenha cada texto na tela como uma imagem transparente 1080x1920.

Destaque automático (na cor_destaque):
  - palavras entre asteriscos: "pronto em *10 minutos*"
  - números e ordinais: 10, 24H, 3x, 1º, 2º
  - na chamada final, palavras em MAIÚSCULAS: "comenta PALAVRA"

Estilo (no plano ou na pasta estilo/): cor_texto, cor_destaque, cor_caixa,
caixa (false = texto solto com contorno), cor_contorno, raio, fonte
(caminho de arquivo ou nome da família, ex: "Montserrat"), tamanho, maiusculas.
"""
import platform
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

LARGURA, ALTURA = 1080, 1920
LARGURA_MAX_TEXTO = 900

# Centro vertical de cada posição (fração da altura). O "baixo" fica acima
# da área onde o Instagram desenha legenda, curtidas e botões.
POSICAO_Y = {"alto": 0.22, "centro": 0.50, "baixo": 0.70}
POSICAO_PADRAO = {"capa": "alto", "bloco": "baixo", "lista": "baixo", "chamada": "centro", "legenda": "baixo"}
ESCALA = {"capa": 1.45, "bloco": 1.0, "lista": 1.0, "chamada": 1.2, "legenda": 0.9}

PASTAS_DE_FONTES = [
    "~/Library/Fonts", "/Library/Fonts", "/System/Library/Fonts", "/System/Library/Fonts/Supplemental",
    "C:/Windows/Fonts", "~/AppData/Local/Microsoft/Windows/Fonts",
    "~/.local/share/fonts", "~/.fonts", "/usr/share/fonts", "/usr/local/share/fonts",
]
PESOS = ["extrabold", "black", "bold", "semibold", "medium", "regular", ""]

FONTES_SISTEMA = {
    "Darwin": [
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    "Windows": [
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
    ],
    "Linux": [
        "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
}

NUMERO = re.compile(r"\d")
ORDINAL = re.compile(r"^\d+[ºª°]$")


def _por_nome(nome):
    """Procura uma fonte instalada pelo nome da família, preferindo pesos fortes."""
    alvo = re.sub(r"[^a-z0-9]", "", nome.lower())
    achadas = []
    for pasta in PASTAS_DE_FONTES:
        raiz = Path(pasta).expanduser()
        if not raiz.is_dir():
            continue
        for arq in raiz.rglob("*"):
            if arq.suffix.lower() in (".ttf", ".otf") and alvo in re.sub(r"[^a-z0-9]", "", arq.stem.lower()):
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


def achar_fonte(preferida=None):
    if preferida:
        caminho = Path(preferida).expanduser()
        if caminho.is_file():
            return str(caminho)
        if caminho.suffix.lower() not in (".ttf", ".otf"):
            achada = _por_nome(preferida)
            if achada:
                return achada
        print(f"Aviso: não achei a fonte '{preferida}', usando uma padrão do sistema.")
    for c in FONTES_SISTEMA.get(platform.system(), []) + sum(FONTES_SISTEMA.values(), []):
        if Path(c).expanduser().exists():
            return str(Path(c).expanduser())
    return None


def _fonte(caminho, tamanho):
    if caminho:
        return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default(size=tamanho)


def _cor(hexa):
    h = hexa.lstrip("#")
    if len(h) == 6:
        h += "FF"
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))


def separar(texto, tipo, maiusculas=False):
    """Quebra o texto em palavras e marca quais vão em destaque."""
    saida, marcando = [], False
    for bruta in texto.split():
        limpa = bruta.strip("*")
        if not limpa:
            continue
        abre = bruta.startswith("*")
        fecha = bruta.endswith("*")
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


def _quebrar_linhas(palavras, fonte, desenho):
    espaco = desenho.textlength(" ", font=fonte)
    linhas, atual, largura = [], [], 0.0
    for palavra, dest in palavras:
        w = desenho.textlength(palavra, font=fonte)
        extra = w if not atual else espaco + w
        if atual and largura + extra > LARGURA_MAX_TEXTO:
            linhas.append((atual, largura))
            atual, largura = [(palavra, dest, w)], w
        else:
            atual.append((palavra, dest, w))
            largura += extra
    if atual:
        linhas.append((atual, largura))
    return linhas, espaco


def desenhar(texto_cfg, estilo, destino):
    tipo = texto_cfg.get("tipo", "bloco")
    posicao = texto_cfg.get("posicao") or POSICAO_PADRAO[tipo]
    tamanho = int(estilo["tamanho"] * ESCALA[tipo])
    fonte = _fonte(achar_fonte(estilo.get("fonte")), tamanho)

    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    palavras = separar(texto_cfg["texto"], tipo, estilo.get("maiusculas", False))
    linhas, espaco = _quebrar_linhas(palavras, fonte, d)

    asc, desc = fonte.getmetrics()
    altura_linha = int((asc + desc) * 1.12)
    bloco_h = altura_linha * len(linhas)
    bloco_w = max(w for _, w in linhas)
    cy = int(ALTURA * POSICAO_Y[posicao])
    topo = cy - bloco_h // 2

    cor_texto = _cor(estilo["cor_texto"])
    cor_dest = _cor(estilo["cor_destaque"])

    raio = int(estilo.get("raio", 28))
    cor_contorno = _cor(estilo.get("cor_contorno", "#000000"))
    if tipo == "capa" or not estilo.get("caixa", True):
        contorno = max(4, tamanho // 14)
        if tipo == "chamada":
            contorno += 2
    else:
        pad_x, pad_y = 38, 26
        caixa = [
            (LARGURA - bloco_w) / 2 - pad_x, topo - pad_y,
            (LARGURA + bloco_w) / 2 + pad_x, topo + bloco_h + pad_y,
        ]
        d.rounded_rectangle(caixa, radius=raio, fill=_cor(estilo["cor_caixa"]))
        if tipo == "chamada":
            d.rounded_rectangle(caixa, radius=raio, outline=cor_dest, width=5)
        contorno, cor_contorno = 0, None

    y = topo
    for linha, w in linhas:
        x = (LARGURA - w) / 2
        for palavra, dest, pw in linha:
            d.text(
                (x, y), palavra, font=fonte,
                fill=cor_dest if dest else cor_texto,
                stroke_width=contorno, stroke_fill=cor_contorno,
            )
            x += pw + espaco
        y += altura_linha

    img.save(destino)
    return destino


def desenhar_imagem(im_cfg, estilo, destino):
    """Print flutuando: cantos arredondados, sombra e crédito opcional.

    Campos: arquivo, largura (px, padrão 860), posicao (padrão centro),
    credito (texto pequeno abaixo, ex: "fonte: site.com").
    """
    origem = Image.open(Path(im_cfg["arquivo"]).expanduser())
    origem = ImageOps.exif_transpose(origem).convert("RGBA")
    largura = min(int(im_cfg.get("largura", 860)), LARGURA - 80)
    altura_max = int(ALTURA * 0.5)
    escala = min(largura / origem.width, altura_max / origem.height)
    w, h = max(1, int(origem.width * escala)), max(1, int(origem.height * escala))
    foto = origem.resize((w, h), Image.LANCZOS)

    raio = 28
    mascara = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, w - 1, h - 1], radius=raio, fill=255)
    foto.putalpha(Image.composite(foto.getchannel("A"), Image.new("L", (w, h), 0), mascara))

    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    posicao = im_cfg.get("posicao", "centro")
    cy = int(ALTURA * {"alto": 0.30, "centro": 0.42, "baixo": 0.62}[posicao])
    x, y = (LARGURA - w) // 2, cy - h // 2

    sombra = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle([x, y + 18, x + w, y + h + 18], radius=raio, fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img, sombra.filter(ImageFilter.GaussianBlur(26)))
    img.alpha_composite(foto, (x, y))

    credito = im_cfg.get("credito")
    if credito:
        d = ImageDraw.Draw(img)
        fonte = _fonte(achar_fonte(estilo.get("fonte")), 30)
        tw = d.textlength(credito, font=fonte)
        d.text(((LARGURA - tw) / 2, y + h + 22), credito, font=fonte,
               fill=_cor(estilo["cor_texto"]), stroke_width=3, stroke_fill=(0, 0, 0, 200))

    img.save(destino)
    return destino
