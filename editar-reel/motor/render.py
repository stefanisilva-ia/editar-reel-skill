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

from PIL import Image

from cartelas import ALTURA, LARGURA, desenhar, desenhar_cartao, desenhar_imagem, quadros_do_contador
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
    t = tempos(plano, pasta)
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

    # Lista com "som_itens": um click em cada item que acende.
    for c in t["cartoes"]:
        if c.get("tipo") == "lista" and c.get("som_itens"):
            from sons import garantir
            click = garantir()["click"][0]
            for ti in c.get("itens_tempo", []):
                t["sons"].append({"arquivo": str(click), "inicio_final": ti, "volume": 0.5})

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

    # Camadas visuais, de trás para a frente: prints, cartões, legenda, textos.
    animar = plano.get("animacao", True)
    camadas = []
    for n, im in enumerate(t["imagens"], 1):
        png = pasta_cartelas / f"print-{n:02d}.png"
        desenhar_imagem(im, plano["estilo"], png)
        camadas.append(_camada_png(png, im, im.get("entrada", "sobe")))
    for n, c in enumerate(t["cartoes"], 1):
        camadas.append(_camada_cartao(c, n, plano["estilo"], pasta_cartelas))
    if t["legendas"]:
        camadas.append(_trilha_legenda(t["legendas"], plano, pasta_cartelas, t["total"]))
    for n, tx in enumerate(t["textos"], 1):
        png = pasta_cartelas / f"texto-{n:02d}.png"
        desenhar(tx, plano["estilo"], png)
        padrao = "pop" if tx.get("tipo") in ("capa", "chamada") else "sobe"
        camadas.append(_camada_png(png, tx, tx.get("entrada", padrao)))

    atual = "vx"
    for n, cam in enumerate(camadas, 1):
        anim = cam["anim"] if animar else ("nenhuma" if cam["anim"] == "nenhuma" else "fade")
        entradas += cam["args"]
        cadeia = f"[{proxima}:v]format=rgba" + cam.get("pre", "")
        x, y = "0", "0"
        if anim in ("fade", "sobe", "pop"):
            dur = cam["dur"]
            cadeia += (
                f",fade=t=in:st=0:d={0.12 if anim == 'pop' else FADE}:alpha=1"
                f",fade=t=out:st={max(0, dur - FADE):.3f}:d={FADE}:alpha=1"
            )
        if anim == "pop":
            s_expr = "if(lt(t,0.32),0.86+0.14*(1+2.70158*pow(t/0.32-1,3)+1.70158*pow(t/0.32-1,2)),1)"
            cadeia += f",scale=w='trunc({LARGURA}*{s_expr}/2)*2':h='trunc({ALTURA}*{s_expr}/2)*2':eval=frame"
            x, y = "'(main_w-overlay_w)/2'", "'(main_h-overlay_h)/2'"
        elif anim == "sobe":
            ini = cam["ini"]
            y = f"'if(lt(t-{ini:.3f},0.3),44*pow(1-(t-{ini:.3f})/0.3,2),0)'"
        cadeia += f",setpts=PTS+{cam['ini']:.3f}/TB[c{n}]"
        filtros.append(cadeia)
        filtros.append(f"[{atual}][c{n}]overlay=x={x}:y={y}:eof_action=pass[o{n}]")
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
    if plano.get("volume_padrao", True):
        _padronizar_volume(saida)
    return saida, total, t


def _camada_png(png, item, anim):
    dur = max(0.4, item["fim_final"] - item["inicio_final"])
    return {
        "args": ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(png)],
        "ini": item["inicio_final"], "dur": dur, "anim": anim,
    }


def _lista_concat(estados, destino):
    """estados: [(png, duração)]. Escreve a lista do concat do ffmpeg."""
    linhas = []
    for png, dur in estados:
        linhas.append(f"file '{Path(png).resolve()}'")
        linhas.append(f"duration {max(dur, 1 / FPS):.3f}")
    linhas.append(f"file '{Path(estados[-1][0]).resolve()}'")
    Path(destino).write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return ["-f", "concat", "-safe", "0", "-i", str(destino)]


def _camada_cartao(c, n, estilo, pasta):
    dur = max(0.4, c["fim_final"] - c["inicio_final"])
    anim = c.get("entrada", "pop" if c["tipo"] == "numero" else "sobe")
    base = {"ini": c["inicio_final"], "dur": dur, "anim": anim}

    if c["tipo"] == "numero" and c.get("contar", True):
        valores = quadros_do_contador(c["valor"])
        if valores:
            for k, v in enumerate(valores):
                desenhar_cartao(c, estilo, pasta / f"cartao-{n:02d}-{k:03d}.png", valor=v)
            resto = max(0.0, dur - len(valores) / FPS)
            return {**base,
                    "args": ["-framerate", str(FPS), "-i", str(pasta / f"cartao-{n:02d}-%03d.png")],
                    "pre": f",tpad=stop_mode=clone:stop_duration={resto:.3f}"}

    if c["tipo"] == "lista" and c.get("itens_tempo"):
        marcos = [c["inicio_final"]] + c["itens_tempo"] + [c["fim_final"]]
        estados = []
        for k in range(len(c["itens"]) + 1):
            png = pasta / f"cartao-{n:02d}-item{k}.png"
            desenhar_cartao(c, estilo, png, visiveis=k)
            estados.append((png, marcos[k + 1] - marcos[k]))
        args = _lista_concat(estados, pasta / f"cartao-{n:02d}.txt")
        return {**base, "args": args, "pre": f",fps={FPS},trim=duration={dur:.3f}"}

    png = pasta / f"cartao-{n:02d}.png"
    desenhar_cartao(c, estilo, png)
    return _camada_png(png, c, anim)


def _trilha_legenda(legendas, plano, pasta, total):
    """Toda a legenda numa trilha só, com a palavra ativa marcada."""
    vazio = pasta / "vazio.png"
    Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0)).save(vazio)
    ativa = plano["legenda"].get("palavra_ativa", True)
    estados, cursor = [], 0.0
    for b, leg in enumerate(legendas):
        if leg["inicio_final"] > cursor + 0.001:
            estados.append((vazio, leg["inicio_final"] - cursor))
        tempos_p = leg["palavras_ini"] if ativa else [leg["inicio_final"]]
        for j, ini in enumerate(tempos_p):
            fim = tempos_p[j + 1] if j + 1 < len(tempos_p) else leg["fim_final"]
            cfg = dict(leg)
            if ativa:
                cfg["ativa"] = leg["indices"][j]
            png = pasta / f"legenda-{b:03d}-{j:02d}.png"
            desenhar(cfg, plano["estilo"], png)
            estados.append((png, max(0.0, fim - max(ini, cursor))))
        cursor = leg["fim_final"]
    if total > cursor:
        estados.append((vazio, total - cursor))
    args = _lista_concat(estados, pasta / "legenda.txt")
    return {"args": args, "ini": 0.0, "dur": total, "anim": "nenhuma", "pre": f",fps={FPS}"}


def _padronizar_volume(arquivo, alvo=-14.0, pico=-1.0):
    """Volume final no padrão das redes: -14 LUFS, pico em -1 dBTP (duas passadas)."""
    medida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(arquivo), "-af",
         f"loudnorm=I={alvo}:TP={pico}:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    try:
        bloco = medida[medida.rindex("{"):medida.rindex("}") + 1]
        m = json.loads(bloco)
    except ValueError:
        print("Aviso: não consegui medir o volume; o arquivo ficou como estava.")
        return
    filtro = (
        f"loudnorm=I={alvo}:TP={pico}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
    )
    temp = Path(arquivo).with_suffix(".volume.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(arquivo), "-c:v", "copy",
         "-af", filtro + ",aresample=48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(temp)],
        check=True,
    )
    temp.replace(arquivo)
    print(f"Volume padronizado: {alvo} LUFS (antes {float(m['input_i']):.1f}).")
