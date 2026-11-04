"""Monta o reel final com uma única passada de ffmpeg.

Ordem: converte HDR para cor normal (se precisar), enquadra em 9:16,
corta os trechos, alterna plano aberto e fechado, junta, aplica a
velocidade e põe os textos por cima com entrada e saída suaves.
"""
import json
import subprocess
from pathlib import Path

from cartelas import ALTURA, LARGURA, desenhar
from plano import linha_do_tempo, tempos_dos_textos

FPS = 30
FADE = 0.15
TRANSFERENCIAS_HDR = {"arib-std-b67", "smpte2084"}


def sondar(video):
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout
    streams = json.loads(saida)["streams"]
    v = next(s for s in streams if s["codec_type"] == "video")
    tem_audio = any(s["codec_type"] == "audio" for s in streams)
    rot = 0
    for side in v.get("side_data_list", []) or []:
        if "rotation" in side:
            rot = abs(int(side["rotation"]))
    return {
        "hdr": v.get("color_transfer") in TRANSFERENCIAS_HDR,
        "audio": tem_audio,
        "rotacao": rot,
    }


def _tem_filtro(nome):
    lista = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return f" {nome} " in lista


def _cadeia_base(info):
    partes = []
    if info["hdr"]:
        if _tem_filtro("zscale") and _tem_filtro("tonemap"):
            partes.append(
                "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv"
            )
        else:
            print("Aviso: vídeo HDR e este ffmpeg não tem zscale. A cor pode sair lavada.")
    # Enquadra em 9:16 pelo centro e padroniza em 1080x1920.
    partes.append(f"crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'")
    partes.append(f"scale={LARGURA}:{ALTURA}:flags=lanczos,setsar=1,format=yuv420p")
    return ",".join(partes)


def renderizar(pasta, plano):
    pasta = Path(pasta)
    video = Path(plano["video"])
    info = sondar(video)
    finais, total = linha_do_tempo(plano)
    textos, _ = tempos_dos_textos(plano)
    v = float(plano.get("velocidade") or 1.0)
    zoom = plano.get("zoom") or {}
    k = len(finais)

    pasta_cartelas = pasta / "cartelas"
    pasta_cartelas.mkdir(exist_ok=True)
    for antigo in pasta_cartelas.glob("*.png"):
        antigo.unlink()

    entradas = ["-i", str(video)]
    filtros = [f"[0:v]{_cadeia_base(info)},split={k}" + "".join(f"[vb{i}]" for i in range(k))]
    if info["audio"]:
        filtros.append(f"[0:a]asplit={k}" + "".join(f"[ab{i}]" for i in range(k)))

    # Trechos: corte + alternância de plano.
    for i, t in enumerate(finais):
        cadeia = f"[vb{i}]trim={t['inicio_original']}:{t['fim_original']},setpts=PTS-STARTPTS"
        if zoom.get("ativo", True) and i % 2 == 1:
            f = float(zoom.get("fator", 1.12))
            alto = float(zoom.get("altura_rosto", 0.35))
            w, h = int(LARGURA * f) // 2 * 2, int(ALTURA * f) // 2 * 2
            cadeia += f",scale={w}:{h},crop={LARGURA}:{ALTURA}:{(w - LARGURA) // 2}:{int((h - ALTURA) * alto)}"
        filtros.append(cadeia + f",setsar=1[v{i}]")
        if info["audio"]:
            filtros.append(
                f"[ab{i}]atrim={t['inicio_original']}:{t['fim_original']},asetpts=PTS-STARTPTS,"
                f"afade=t=in:d=0.02,afade=t=out:st={max(0, t['fim_original'] - t['inicio_original'] - 0.03):.3f}:d=0.03[a{i}]"
            )

    pares = "".join(f"[v{i}][a{i}]" if info["audio"] else f"[v{i}]" for i in range(k))
    a_flag = 1 if info["audio"] else 0
    saida_concat = "[vc][ac]" if info["audio"] else "[vc]"
    filtros.append(f"{pares}concat=n={k}:v=1:a={a_flag}{saida_concat}")
    filtros.append(f"[vc]setpts=PTS/{v},fps={FPS}[vx]")
    if info["audio"]:
        filtros.append(f"[ac]atempo={v}[ax]")

    # Textos por cima.
    atual = "vx"
    for n, tx in enumerate(textos, 1):
        png = pasta_cartelas / f"texto-{n:02d}.png"
        desenhar(tx, plano["estilo"], png)
        dur = max(0.4, tx["fim_final"] - tx["inicio_final"])
        entradas += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(png)]
        filtros.append(
            f"[{n}:v]format=rgba,fade=t=in:st=0:d={FADE}:alpha=1,"
            f"fade=t=out:st={max(0, dur - FADE):.3f}:d={FADE}:alpha=1,"
            f"setpts=PTS+{tx['inicio_final']:.3f}/TB[t{n}]"
        )
        filtros.append(f"[{atual}][t{n}]overlay=0:0:eof_action=pass[o{n}]")
        atual = f"o{n}"

    filtros.append(f"[{atual}]format=yuv420p[vout]")
    saida = pasta / plano.get("saida", "reel-final.mp4")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"] + entradas
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[vout]"]
    if info["audio"]:
        cmd += ["-map", "[ax]", "-c:a", "aac", "-b:a", "192k"]
    cmd += [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", "-t", f"{total:.3f}", str(saida),
    ]
    subprocess.run(cmd, check=True)
    return saida, total, textos
