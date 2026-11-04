"""Monta o reel final com uma única passada de ffmpeg.

Ordem: cada vídeo de origem é convertido para cor normal (se for HDR),
enquadrado em 9:16 e padronizado; os trechos são cortados, ganham a
alternância de plano e a transição de entrada; tudo é juntado, a
velocidade é aplicada, os efeitos sonoros entram na trilha e os prints
e textos vão por cima com entrada e saída suaves.
"""
import json
import subprocess
from pathlib import Path

from cartelas import ALTURA, LARGURA, desenhar, desenhar_imagem
from plano import linha_do_tempo, tempos

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
    return {
        "hdr": v.get("color_transfer") in TRANSFERENCIAS_HDR,
        "audio": any(s["codec_type"] == "audio" for s in streams),
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
    partes.append("crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'")
    partes.append(f"scale={LARGURA}:{ALTURA}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p")
    return ",".join(partes)


def _transicao(tipo):
    if tipo == "fade":
        return ",fade=t=in:st=0:d=0.3", ",afade=t=in:d=0.2"
    if tipo == "flash":
        return ",fade=t=in:st=0:d=0.2:color=white", ""
    if tipo == "zoom":
        esc = "1+0.18*max(0,1-t/0.35)"
        return (
            f",scale=w='trunc(iw*({esc})/2)*2':h='trunc(ih*({esc})/2)*2':eval=frame,"
            f"crop={LARGURA}:{ALTURA}"
        ), ""
    return "", ""


def renderizar(pasta, plano):
    pasta = Path(pasta)
    videos = [Path(v).expanduser() for v in plano["videos"]]
    infos = [sondar(v) for v in videos]
    finais, total = linha_do_tempo(plano)
    t = tempos(plano)
    vel = float(plano.get("velocidade") or 1.0)
    zoom = plano.get("zoom") or {}

    pasta_cartelas = pasta / "cartelas"
    pasta_cartelas.mkdir(exist_ok=True)
    for antigo in pasta_cartelas.glob("*.png"):
        antigo.unlink()

    entradas, filtros = [], []
    for v in videos:
        entradas += ["-i", str(v)]

    # Cada vídeo é preparado uma vez e dividido entre os seus trechos.
    usos = {n: [i for i, f in enumerate(finais) if f["video"] == n + 1] for n in range(len(videos))}
    for n, idx in usos.items():
        if not idx:
            continue
        k = len(idx)
        filtros.append(f"[{n}:v]{_cadeia_base(infos[n])},split={k}" + "".join(f"[vb{i}]" for i in idx))
        fonte_audio = (
            f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo"
            if infos[n]["audio"] else "anullsrc=r=48000:cl=stereo"
        )
        filtros.append(f"{fonte_audio},asplit={k}" + "".join(f"[ab{i}]" for i in idx))

    for i, f in enumerate(finais):
        ini, fim = f["inicio_original"], f["fim_original"]
        cadeia = f"[vb{i}]trim={ini}:{fim},setpts=PTS-STARTPTS"
        if zoom.get("ativo", True) and i % 2 == 1:
            fz = float(zoom.get("fator", 1.12))
            alto = float(zoom.get("altura_rosto", 0.35))
            w, h = int(LARGURA * fz) // 2 * 2, int(ALTURA * fz) // 2 * 2
            cadeia += f",scale={w}:{h},crop={LARGURA}:{ALTURA}:{(w - LARGURA) // 2}:{int((h - ALTURA) * alto)}"
        tv, ta = _transicao(f["transicao"]) if i > 0 or f["transicao"] == "fade" else ("", "")
        filtros.append(cadeia + tv + f",setsar=1[v{i}]")
        filtros.append(
            f"[ab{i}]atrim={ini}:{fim},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.02,afade=t=out:st={max(0, fim - ini - 0.03):.3f}:d=0.03{ta}[a{i}]"
        )

    k = len(finais)
    filtros.append("".join(f"[v{i}][a{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=1[vc][ac]")
    filtros.append(f"[vc]setpts=PTS/{vel},fps={FPS}[vx]")
    filtros.append(f"[ac]atempo={vel}[ax]")

    # Efeitos sonoros: entram por cima da fala, sem mudar de velocidade.
    proxima = len(videos)
    trilha = "ax"
    if t["sons"]:
        rotulos = []
        for s in t["sons"]:
            entradas += ["-i", str(Path(s["arquivo"]).expanduser())]
            ms = int(s["inicio_final"] * 1000)
            vol = float(s.get("volume", 0.8))
            filtros.append(
                f"[{proxima}:a]aresample=48000,aformat=channel_layouts=stereo,"
                f"volume={vol},adelay={ms}:all=1[s{proxima}]"
            )
            rotulos.append(f"[s{proxima}]")
            proxima += 1
        filtros.append(f"[ax]{''.join(rotulos)}amix=inputs={len(rotulos) + 1}:duration=first:normalize=0[am]")
        trilha = "am"

    # Prints primeiro (ficam atrás), textos depois (ficam na frente).
    camadas = []
    for n, im in enumerate(t["imagens"], 1):
        png = pasta_cartelas / f"print-{n:02d}.png"
        desenhar_imagem(im, plano["estilo"], png)
        camadas.append((png, im))
    for n, tx in enumerate(t["textos"], 1):
        png = pasta_cartelas / f"texto-{n:02d}.png"
        desenhar(tx, plano["estilo"], png)
        camadas.append((png, tx))

    atual = "vx"
    for n, (png, item) in enumerate(camadas, 1):
        dur = max(0.4, item["fim_final"] - item["inicio_final"])
        entradas += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(png)]
        filtros.append(
            f"[{proxima}:v]format=rgba,fade=t=in:st=0:d={FADE}:alpha=1,"
            f"fade=t=out:st={max(0, dur - FADE):.3f}:d={FADE}:alpha=1,"
            f"setpts=PTS+{item['inicio_final']:.3f}/TB[c{n}]"
        )
        filtros.append(f"[{atual}][c{n}]overlay=0:0:eof_action=pass[o{n}]")
        atual = f"o{n}"
        proxima += 1

    filtros.append(f"[{atual}]format=yuv420p[vout]")
    saida = pasta / plano.get("saida", "reel-final.mp4")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"] + entradas
    cmd += ["-filter_complex", ";".join(filtros), "-map", "[vout]", "-map", f"[{trilha}]"]
    cmd += [
        "-c:a", "aac", "-b:a", "192k",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", "-t", f"{total:.3f}", str(saida),
    ]
    subprocess.run(cmd, check=True)
    return saida, total, t
