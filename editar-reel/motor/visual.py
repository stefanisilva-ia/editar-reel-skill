"""Formatos de tela, fundos de cena, temas de cor e receitas de estilo.

Formatos (campo "formato" de cada trecho):
  A  tela cheia: o vídeo da pessoa ocupa a tela.
  B  tela dividida: fundo de cena em cima, a pessoa num painel embaixo.
  C  só gráficos: fundo de cena, peças e legenda; a fala continua.

Fundos (campo "fundo" do trecho, só em B e C): um nome da paleta
(verde-profundo, verde-medio, verde-noite, off-white, areia, bege, alerta)
ou uma cor #RRGGBB. Sem fundo, vale o padrão da receita.

Receitas (pasta estilos/, campo "receita" do plano): definem fundos,
cartões, prints, manchete e legenda. "receita": "escuro-tecnico" usa uma só;
{"base": "escuro-tecnico", "prints": "print-anotado"} combina por seção.
"""
import copy
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

LARGURA, ALTURA = 1080, 1920
PASTA_SKILL = Path(__file__).resolve().parent.parent
PASTA_RECEITAS = PASTA_SKILL / "estilos"

FORMATOS = {"A", "B", "C"}
FUNDOS_PADRAO = {
    "verde-profundo": "#03332C",
    "verde-medio": "#07544A",
    "verde-noite": "#0A2420",
    "off-white": "#F7F4EE",
    "areia": "#EDE3D1",
    "bege": "#DDCDB4",
    "alerta": "#A8382C",
}
PAINEL_PADRAO = 0.40
PAINEL_GRANDE = 0.33
MARGEM_PAINEL = 16
RAIO_PAINEL = 48
HEX = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")

SECOES = ("fundos", "cartoes", "prints", "manchete", "legenda")
RECEITA_BASE = {
    "fundos": {"padrao": "verde-profundo", "brilho": 0.12, "arco": False},
    "cartoes": {
        "escuro": {"cor": "#07544AE6", "borda": "#289A8B66", "raio": 28},
        "claro": {"cor": "#FFFFFFE0", "borda": "#FFFFFFFF", "raio": 32},
    },
    "prints": {"borda": 0, "cor_borda": "#289A8B", "raio": 28, "inclinacao": 0},
    "manchete": {"modelo": "solta"},
    "legenda": {},
}


def cor(hexa):
    h = hexa.lstrip("#")
    if len(h) == 6:
        h += "FF"
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))


def eh_claro(hexa):
    r, g, b, _ = cor(hexa)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 > 0.55


# Receitas

def listar_receitas():
    return sorted(p.stem for p in PASTA_RECEITAS.glob("*.json"))


def _ler_receita(nome):
    arq = PASTA_RECEITAS / f"{nome}.json"
    if not arq.exists():
        raise ValueError(f"receita '{nome}' não existe. Disponíveis: {', '.join(listar_receitas()) or 'nenhuma'}.")
    return json.loads(arq.read_text(encoding="utf-8"))


def _mesclar(destino, origem):
    for k, v in origem.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and isinstance(destino.get(k), dict):
            _mesclar(destino[k], v)
        else:
            destino[k] = v


def montar_receita(cfg):
    """cfg: None, "nome" ou {"base": "nome", "prints": "outra", ...}. Devolve a receita completa."""
    final = copy.deepcopy(RECEITA_BASE)
    if not cfg:
        return final
    if isinstance(cfg, str):
        cfg = {"base": cfg}
    base = _ler_receita(cfg["base"]) if cfg.get("base") else {}
    for secao in SECOES:
        origem = _ler_receita(cfg[secao]) if cfg.get(secao) else base
        if isinstance(origem.get(secao), dict):
            _mesclar(final[secao], origem[secao])
    return final


# Fundos e temas

def cor_do_fundo(nome, estilo=None):
    fundos = {**FUNDOS_PADRAO, **((estilo or {}).get("fundos") or {})}
    if nome in fundos:
        return fundos[nome]
    if isinstance(nome, str) and HEX.match(nome):
        return nome[:7]
    return None


def tema(formato, fundo_hex):
    """video (formato A), claro ou escuro (formatos B e C, pelo fundo)."""
    if formato == "A":
        return "video"
    return "claro" if eh_claro(fundo_hex) else "escuro"


def _luminancia(c):
    def canal(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c[:3]
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(c1, c2):
    a, b = sorted((_luminancia(c1), _luminancia(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def cores_do_tema(nome_tema, estilo, fundo=None):
    """Cores de texto, destaque, alerta e apoio para o tema (e para o fundo, se informado)."""
    if nome_tema == "claro":
        c = {
            "texto": cor(estilo["cor_texto_claro"]),
            "destaque": cor(estilo["cor_destaque_claro"]),
            "alerta": cor(estilo["cor_alerta"]),
            "apoio": cor(estilo["cor_apoio"]),
            "sombra": False,
        }
    else:
        c = {
            "texto": cor(estilo["cor_texto"]),
            "destaque": cor(estilo["cor_destaque"]),
            "alerta": cor(estilo["cor_alerta"]),
            "apoio": cor(estilo["cor_apoio"]),
            "sombra": nome_tema == "video",
        }
    if fundo:
        f = cor(fundo)
        if contraste(c["alerta"], f) < 2.2:
            c["alerta"] = c["destaque"] if contraste(c["destaque"], f) >= 2.2 else c["texto"]
    return c


# Geometria

def altura_painel(painel):
    return int(round(ALTURA * float(painel) / 2)) * 2


def topo_painel(painel):
    return ALTURA - altura_painel(painel)


def area_da_peca(formato, painel=PAINEL_PADRAO, manchete=False, grande=False):
    """(topo, base) da área das peças em B e C. None em A."""
    if formato == "B":
        topo = 400 if manchete else 200
        return topo, topo_painel(painel) - 150
    if formato == "C":
        topo = 400 if manchete else 260
        return topo, 1250 if grande else 960
    return None


def y_legenda(formato, painel=PAINEL_PADRAO, grande=False):
    if formato == "B":
        return topo_painel(painel) - 80
    if formato == "C":
        return 1420 if grande else 1120
    return 1300


# Desenho dos fundos

def _brilho(img, cor_brilho, forca):
    """Brilho radial suave no topo central."""
    p = Image.new("RGBA", (LARGURA // 4, ALTURA // 4), (0, 0, 0, 0))
    ImageDraw.Draw(p).ellipse([-40, -110, LARGURA // 4 + 40, 230], fill=cor_brilho[:3] + (int(255 * forca * 2.2),))
    p = p.filter(ImageFilter.GaussianBlur(48)).resize((LARGURA, ALTURA), Image.BICUBIC)
    return Image.alpha_composite(img, p)


def desenhar_fundo(fundo_hex, receita, estilo, destino, painel=None):
    """Fundo de cena 1080x1920. Com painel (formato B), já leva a sombra do painel."""
    img = Image.new("RGBA", (LARGURA, ALTURA), cor(fundo_hex))
    claro = eh_claro(fundo_hex)
    forca = float(receita["fundos"].get("brilho", 0.12))
    if forca > 0:
        img = _brilho(img, (255, 255, 255) if claro else cor(estilo["cor_apoio"]), forca)
    if receita["fundos"].get("arco") and not claro:
        camada = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
        d = ImageDraw.Draw(camada)
        apoio = cor(estilo["cor_apoio"])[:3]
        cx, cy, r = int(LARGURA * 1.08), int(ALTURA * 0.40), int(LARGURA * 0.56)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=apoio + (56,), width=3)
        r2 = int(r * 1.32)
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=apoio + (26,), width=2)
        img = Image.alpha_composite(img, camada)
    if painel is not None:
        topo = topo_painel(painel)
        sombra = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
        ImageDraw.Draw(sombra).rounded_rectangle(
            [MARGEM_PAINEL, topo - 6, LARGURA - MARGEM_PAINEL, ALTURA + 60], radius=RAIO_PAINEL,
            fill=(0, 0, 0, 70 if claro else 130))
        img = Image.alpha_composite(img, sombra.filter(ImageFilter.GaussianBlur(26)))
    img.convert("RGB").save(destino)
    return destino


def desenhar_mascara(painel, destino):
    """Máscara do painel da pessoa: cantos superiores arredondados."""
    w, h = LARGURA - 2 * MARGEM_PAINEL, altura_painel(painel)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h + RAIO_PAINEL], radius=RAIO_PAINEL, fill=255)
    m.save(destino)
    return destino
