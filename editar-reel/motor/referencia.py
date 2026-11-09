"""Folhas de quadros de um vídeo de referência, para virar uma receita de estilo.

Tira um quadro a cada N segundos e monta folhas de 12 quadros (4 x 3) com o
tempo marcado. Quem edita abre as folhas, analisa composição, legenda, cores,
peças e ritmo, e escreve a receita em estilos/<nome>.json e estilos/<nome>.md.
O vídeo de referência nunca entra na skill: só a receita, escrita por você.
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from cartelas import f_rotulo

COLUNAS, LINHAS = 4, 3
W, H = 270, 480


def duracao(video):
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(saida.strip() or 0)


def folhas(video, destino, a_cada=1.0):
    video = Path(video).expanduser().resolve()
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    total = duracao(video)
    tempos = [round(k * a_cada, 2) for k in range(int(total / a_cada) + 1) if k * a_cada < total - 0.05]
    tmp = Path(tempfile.mkdtemp())
    quadros = []
    for t in tempos:
        png = tmp / f"{t:08.2f}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t}", "-i", str(video), "-frames:v", "1",
             "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2", str(png)],
            check=True,
        )
        if png.exists():
            quadros.append((t, png))
    fonte = f_rotulo({}, 18, 700)
    por_folha = COLUNAS * LINHAS
    saidas = []
    for n in range(0, len(quadros), por_folha):
        folha = Image.new("RGB", (COLUNAS * (W + 6) + 6, LINHAS * (H + 6) + 6), "#6B6B6B")
        d = ImageDraw.Draw(folha)
        for k, (t, png) in enumerate(quadros[n:n + por_folha]):
            x, y = 6 + (k % COLUNAS) * (W + 6), 6 + (k // COLUNAS) * (H + 6)
            folha.paste(Image.open(png).convert("RGB"), (x, y))
            d.rounded_rectangle([x + 4, y + 4, x + 70, y + 30], radius=6, fill="#C9473A")
            d.text((x + 37, y + 17), f"{t:.1f}s", font=fonte, fill="white", anchor="mm")
        arq = destino / f"folha-{n // por_folha + 1:02d}.png"
        folha.save(arq)
        saidas.append(arq)
    return saidas, total
