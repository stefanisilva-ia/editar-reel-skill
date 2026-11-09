"""Prints reais na tela: moldura, inclinação, pílula e anotações que se desenham.

Campos de cada item em "imagens" (além de arquivo, trecho, palavra, ate_trecho, duracao):
  credito      texto pequeno abaixo (obrigatório em imagem de terceiros)
  largura      largura máxima em px
  grande       true: o print ocupa mais altura (em C a legenda desce; em B o painel encolhe)
  inclinacao   graus, de -4 a 4. Sem o campo, vale a receita, alternando o lado a cada print
  pilula       texto curto abaixo do print, até 6 palavras
  anotacoes    lista de marcações:
               {"tipo": "circulo|caixa|marca|sublinhado|seta", "area": [x, y, largura, altura],
                "palavra": "botão", "cor": "#HEX"}
               "area" em frações da imagem (0 a 1) ou em pixels da imagem original.
               Cada marcação se desenha quando a palavra é dita.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from cartelas import f_rotulo
from visual import ALTURA, LARGURA, cor, cores_do_tema

TIPOS_ANOTACAO = {"circulo", "caixa", "marca", "sublinhado", "seta"}
QUADROS_ANOTACAO = 7
POSICAO_A = {"alto": 0.30, "centro": 0.42, "baixo": 0.62}


def _area_px(area, w0, h0, escala, off):
    x, y, l, a = (float(v) for v in area)
    if max(x, y, l, a) <= 1.0:
        x, y, l, a = x * w0, y * h0, l * w0, a * h0
    return off + x * escala, off + y * escala, off + (x + l) * escala, off + (y + a) * escala


def _parcial(d, pontos, p, cor_, largura):
    """Desenha a fração p (0 a 1) de uma linha com vários pontos."""
    trechos = list(zip(pontos, pontos[1:]))
    total = sum(math.dist(a, b) for a, b in trechos)
    resta = total * p
    for a, b in trechos:
        comp = math.dist(a, b)
        if resta <= 0:
            break
        if resta >= comp:
            d.line([a, b], fill=cor_, width=largura)
        else:
            f = resta / comp
            d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=cor_, width=largura)
        resta -= comp


def _anotar(cartao, an, caixa, p, c):
    tipo = an.get("tipo", "circulo")
    padrao = {"circulo": c["apoio"], "caixa": c["alerta"], "marca": c["apoio"], "sublinhado": c["apoio"], "seta": c["alerta"]}[tipo]
    cor_ = cor(an["cor"]) if an.get("cor") else padrao
    x1, y1, x2, y2 = caixa
    camada = Image.new("RGBA", cartao.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    if tipo == "circulo":
        m = 16
        d.arc([x1 - m, y1 - m, x2 + m, y2 + m], start=-90, end=-90 + 360 * p, fill=cor_, width=6)
    elif tipo == "caixa":
        m = 8
        _parcial(d, [(x1 - m, y1 - m), (x2 + m, y1 - m), (x2 + m, y2 + m), (x1 - m, y2 + m), (x1 - m, y1 - m)], p, cor_, 6)
    elif tipo == "marca":
        d.rectangle([x1 - 4, y1 - 2, x1 - 4 + (x2 - x1 + 8) * p, y2 + 2], fill=cor_[:3] + (80,))
    elif tipo == "sublinhado":
        d.line([(x1, y2 + 8), (x1 + (x2 - x1) * p, y2 + 8)], fill=cor_, width=6)
    elif tipo == "seta":
        w, h = cartao.size
        ini = (min(w - 14, x2 + 150), min(h - 14, y2 + 110))
        fim = (x2 + 6, y2 + 6)
        if math.dist(ini, fim) < 40:
            ini = (max(14, x1 - 150), min(h - 14, y2 + 110))
            fim = (x1 - 6, y2 + 6)
        _parcial(d, [ini, fim], p, cor_, 7)
        if p >= 1:
            ang = math.atan2(fim[1] - ini[1], fim[0] - ini[0])
            for lado in (-0.5, 0.5):
                d.line([fim, (fim[0] - 34 * math.cos(ang + lado), fim[1] - 34 * math.sin(ang + lado))], fill=cor_, width=7)
    cartao.alpha_composite(camada)


def inclinacao_do_print(im, receita, indice):
    if im.get("inclinacao") is not None:
        return float(im["inclinacao"])
    base = float(((receita or {}).get("prints") or {}).get("inclinacao", 0))
    return -base if indice % 2 == 0 else base


def desenhar_print(im, estilo, receita, destino, progresso=None, indice=0):
    """Print flutuando na área das peças. progresso: fração desenhada de cada anotação."""
    origem = ImageOps.exif_transpose(Image.open(Path(im["arquivo"]).expanduser())).convert("RGBA")
    w0, h0 = origem.size
    tema = im.get("_tema", "video")
    c = cores_do_tema(tema, estilo)
    cfg = (receita or {}).get("prints") or {}
    borda = int(cfg.get("borda", 0))
    cor_borda = cor(cfg.get("cor_borda", estilo["cor_apoio"]))
    raio = int(cfg.get("raio", 28))
    pilula = im.get("pilula")
    area = im.get("_area")
    if area:
        topo, base = area
        reserva = (110 if pilula else 0) + (44 if im.get("credito") else 0)
        largura_max = min(int(im.get("largura", 960 if im.get("_formato") == "C" else 940)), LARGURA - 60)
        altura_max = (base - topo) - reserva - 20
        cy = topo + altura_max / 2 + 10
    else:
        largura_max = min(int(im.get("largura", 860)), LARGURA - 80)
        altura_max = int(ALTURA * 0.5)
        cy = int(ALTURA * POSICAO_A[im.get("posicao", "centro")])
    escala = min((largura_max - 2 * borda) / w0, (altura_max - 2 * borda) / h0)
    w, h = max(1, int(w0 * escala)), max(1, int(h0 * escala))
    foto = origem.resize((w, h), Image.LANCZOS)

    cartao = Image.new("RGBA", (w + 2 * borda, h + 2 * borda), (0, 0, 0, 0))
    dc = ImageDraw.Draw(cartao)
    if borda:
        dc.rounded_rectangle([0, 0, cartao.width - 1, cartao.height - 1], radius=raio, fill=cor_borda)
    mascara = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, w - 1, h - 1], radius=max(8, raio - borda), fill=255)
    foto.putalpha(Image.composite(foto.getchannel("A"), Image.new("L", (w, h), 0), mascara))
    cartao.alpha_composite(foto, (borda, borda))

    for k, an in enumerate(im.get("anotacoes") or []):
        p = 1.0 if progresso is None else progresso[k]
        if p > 0 and an.get("area"):
            _anotar(cartao, an, _area_px(an["area"], w0, h0, escala, borda), p, c)

    ang = inclinacao_do_print(im, receita, indice)
    if ang:
        cartao = cartao.rotate(ang, resample=Image.BICUBIC, expand=True)

    img = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    x, y = (LARGURA - cartao.width) // 2, int(cy - cartao.height / 2)
    sombra = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    alfa = cartao.getchannel("A").point(lambda v: int(v * (0.35 if tema == "claro" else 0.6)))
    preto = Image.new("RGBA", cartao.size, (0, 0, 0, 255))
    preto.putalpha(alfa)
    sombra.alpha_composite(preto, (x, y + 18))
    img = Image.alpha_composite(img, sombra.filter(ImageFilter.GaussianBlur(26)))
    img.alpha_composite(cartao, (x, y))

    d = ImageDraw.Draw(img)
    fim_y = y + cartao.height + 26
    if pilula:
        fp = f_rotulo(estilo, 34, 600)
        tw = d.textlength(pilula, font=fp)
        px0, px1 = (LARGURA - tw) / 2 - 26, (LARGURA + tw) / 2 + 26
        d.rounded_rectangle([px0, fim_y, px1, fim_y + 64], radius=32, fill=(3, 51, 44, 240),
                            outline=c["apoio"][:3] + (140,), width=2)
        d.text((LARGURA / 2, fim_y + 32), pilula, font=fp, fill=(255, 255, 255, 255), anchor="mm")
        fim_y += 84
    credito = im.get("credito")
    if credito:
        fc = f_rotulo(estilo, 28, 500)
        if tema == "claro":
            d.text((LARGURA / 2, fim_y + 18), credito, font=fc, fill=c["texto"][:3] + (170,), anchor="mm")
        else:
            d.text((LARGURA / 2, fim_y + 18), credito, font=fc, fill=(255, 255, 255, 220), anchor="mm",
                   stroke_width=3 if tema == "video" else 0, stroke_fill=(0, 0, 0, 200))
    img.save(destino)
    return destino
