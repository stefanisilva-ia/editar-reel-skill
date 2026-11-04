"""Lê uma pasta de referências de estilo e sugere o estilo do vídeo.

O que a pasta pode ter (tudo opcional):
  - imagens (.png .jpg .jpeg .webp): prints de referência; as cores
    dominantes de cada uma são extraídas
  - fontes (.ttf .otf): a de peso mais forte vira a fonte do texto
  - textos (.txt .md): cores em hexadecimal (#RRGGBB) e nomes de fontes.
    Uma linha como "destaque: #DFAC16" ou "fonte: Montserrat" vale direto.

As imagens também devem ser olhadas por quem edita: caixa ou texto solto,
maiúsculas, posição e tamanho não dá para medir só pela cor.
"""
import colorsys
import re
from pathlib import Path

from PIL import Image

IMAGENS = {".png", ".jpg", ".jpeg", ".webp"}
FONTES = {".ttf", ".otf"}
TEXTOS = {".txt", ".md"}
HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
CHAVES = {
    "cor_texto": ("texto", "letra", "text"),
    "cor_destaque": ("destaque", "acento", "accent", "highlight", "principal"),
    "cor_caixa": ("caixa", "fundo", "background", "box"),
    "cor_contorno": ("contorno", "borda", "stroke", "outline"),
}
PESOS = ["extrabold", "black", "bold", "semibold", "medium"]


def _hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb[:3])


def _cores_da_imagem(arq, n=6):
    img = Image.open(arq).convert("RGB")
    img.thumbnail((240, 240))
    paleta = img.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    cores = paleta.getpalette()[: n * 3]
    contagem = sorted(paleta.getcolors(), reverse=True)
    total = sum(c for c, _ in contagem)
    return [(_hex(cores[i * 3:i * 3 + 3]), round(c / total, 2)) for c, i in contagem if c / total >= 0.02]


def _hsv(hexa):
    r, g, b = (int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)


def ler(pasta_estilo):
    pasta = Path(pasta_estilo).expanduser().resolve()
    if not pasta.is_dir():
        raise SystemExit(f"Pasta de estilo não encontrada: {pasta}")

    achado = {"imagens": [], "fontes": [], "textos": [], "rotuladas": {}, "fonte_nome": None}
    for arq in sorted(pasta.rglob("*")):
        ext = arq.suffix.lower()
        if ext in IMAGENS:
            achado["imagens"].append({"arquivo": str(arq), "cores": _cores_da_imagem(arq)})
        elif ext in FONTES:
            achado["fontes"].append(str(arq))
        elif ext in TEXTOS:
            texto = arq.read_text(encoding="utf-8", errors="ignore")
            achado["textos"].append({"arquivo": str(arq), "cores": HEX.findall(texto)})
            for linha in texto.splitlines():
                baixa = linha.lower()
                cor = HEX.search(linha)
                if cor:
                    for chave, palavras in CHAVES.items():
                        if chave not in achado["rotuladas"] and any(p in baixa for p in palavras):
                            achado["rotuladas"][chave] = cor.group(0).upper()
                            break
                m = re.search(r"(?:fonte|font|tipografia)\s*[:=]\s*([^,;#\n]+)", linha, re.I)
                if m and not achado["fonte_nome"]:
                    achado["fonte_nome"] = m.group(1).strip(" *`_")
    return achado


def sugerir(achado):
    """Monta um estilo a partir do que foi achado. Cores rotuladas vencem as deduzidas."""
    estilo = {}

    if achado["fontes"]:
        def nota(caminho):
            nome = Path(caminho).stem.lower()
            for i, peso in enumerate(PESOS):
                if peso in nome and "italic" not in nome:
                    return i
            return len(PESOS)
        estilo["fonte"] = sorted(achado["fontes"], key=nota)[0]
    elif achado["fonte_nome"]:
        estilo["fonte"] = achado["fonte_nome"]

    candidatas = [c.upper() for t in achado["textos"] for c in t["cores"]]
    for im in achado["imagens"]:
        candidatas += [c for c, _ in im["cores"]]
    vistas = []
    for c in candidatas:
        if c not in vistas:
            vistas.append(c)

    if vistas:
        escuras = sorted(vistas, key=lambda c: _hsv(c)[2])
        vivas = sorted(vistas, key=lambda c: -(_hsv(c)[1] * _hsv(c)[2]))
        caixa = escuras[0]
        if _hsv(caixa)[2] < 0.35:
            estilo["cor_caixa"] = caixa + "D9"
            estilo["cor_texto"] = "#FFFFFF"
        else:
            estilo["cor_caixa"] = "#000000B8"
        destaque = next((c for c in vivas if c != caixa and _hsv(c)[1] > 0.35), None)
        if destaque:
            estilo["cor_destaque"] = destaque

    for chave, cor in achado["rotuladas"].items():
        estilo[chave] = cor + "D9" if chave == "cor_caixa" else cor
    return estilo
