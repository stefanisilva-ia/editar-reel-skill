"""Efeitos sonoros básicos, sintetizados com o ffmpeg (sem direitos autorais).

Ficam em <pasta da skill>/sons-basicos/ e são criados na primeira vez que
o comando 'sons' roda. Volumes sugeridos entre 0.4 e 0.7.
"""
import subprocess
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "sons-basicos"

RECEITAS = {
    "pop": ("aevalsrc", "0.8*sin(2*PI*(700+900*exp(-30*t))*t)*exp(-28*t)", 0.18,
            "para números e palavras que aparecem na tela"),
    "click": ("aevalsrc", "0.9*sin(2*PI*2200*t)*exp(-70*t)", 0.06,
              "para itens de lista entrando, um por item"),
    "ding": ("aevalsrc", "0.55*sin(2*PI*1320*t)*exp(-5*t)+0.25*sin(2*PI*2640*t)*exp(-8*t)", 0.9,
             "para revelar um resultado"),
    "impacto": ("aevalsrc", "0.9*sin(2*PI*(55+40*exp(-12*t))*t)*exp(-6*t)", 0.7,
                "para a frase mais forte ou a capa"),
    "whoosh": ("anoisesrc", None, 0.45,
               "para a entrada de um print ou cartão, ou troca de cena"),
}


def _gerar(nome, destino):
    tipo, expr, dur, _ = RECEITAS[nome]
    if tipo == "aevalsrc":
        fonte = f"aevalsrc='{expr}|{expr}':s=48000:d={dur}"
        filtro = f"afade=t=out:st={dur * 0.7:.3f}:d={dur * 0.3:.3f}"
    else:
        fonte = f"anoisesrc=d={dur}:c=pink:a=0.6:r=48000"
        filtro = (
            "highpass=f=500,lowpass=f=4500,"
            f"afade=t=in:d={dur * 0.55:.3f}:curve=qsin,afade=t=out:st={dur * 0.55:.3f}:d={dur * 0.45:.3f},"
            "aformat=channel_layouts=stereo"
        )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", fonte, "-af", filtro, str(destino)],
        check=True,
    )


def garantir():
    """Cria os sons que faltarem e devolve {nome: (caminho, uso)}."""
    PASTA.mkdir(exist_ok=True)
    saida = {}
    for nome, receita in RECEITAS.items():
        arq = PASTA / f"{nome}.wav"
        if not arq.exists():
            _gerar(nome, arq)
        saida[nome] = (arq, receita[3])
    return saida
