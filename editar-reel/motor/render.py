"""Monta o reel final com uma única passada de ffmpeg.

Ordem: cada vídeo de origem é convertido para cor normal (se for HDR),
enquadrado em 9:16 e padronizado; cada trecho é montado no seu formato
(A tela cheia, B tela dividida, C só gráficos) e ganha a transição de
entrada; tudo é juntado, a velocidade é aplicada, os efeitos sonoros
entram na trilha e prints, cartões, legenda, manchete, chamada e selo
vão por cima com as suas entradas.
"""
import json
import subprocess
from pathlib import Path

from PIL import Image

from cartelas import (desenhar, desenhar_cartao, desenhar_chamada, desenhar_legenda, desenhar_manchete,
                      desenhar_palavra_solta, desenhar_selo, quadros_do_contador)
from plano import tempos
from prints import QUADROS_ANOTACAO, desenhar_print
from visual import ALTURA, LARGURA, MARGEM_PAINEL, altura_painel, desenhar_fundo, desenhar_mascara, topo_painel

FPS = 30
FADE = 0.15
QUADROS_PALAVRA = 9
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


def _opcao_script():
    """Opção do ffmpeg que lê os filtros de um arquivo (o nome mudou na versão 7)."""
    versao = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout
    try:
        maior = int(versao.split("version")[1].strip().split(".")[0].lstrip("n"))
    except (IndexError, ValueError):
        maior = 6
    return "-/filter_complex" if maior >= 7 else "-filter_complex_script"


def renderizar(pasta, plano):
    pasta = Path(pasta)
    videos = [Path(v).expanduser() for v in plano["videos"]]
    infos = [sondar(v) for v in videos]
    t = tempos(plano, pasta)
    finais, total = t["finais"], t["total"]
    vel = float(plano.get("velocidade") or 1.0)
    zoom = plano.get("zoom") or {}
    estilo, receita = plano["estilo"], plano.get("_receita")

    pasta_cartelas = pasta / "cartelas"
    pasta_cartelas.mkdir(exist_ok=True)
    for antigo in list(pasta_cartelas.glob("*.png")) + list(pasta_cartelas.glob("*.txt")):
        antigo.unlink()
    vazio = pasta_cartelas / "vazio.png"
    Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0)).save(vazio)

    entradas, filtros = [], []
    for v in videos:
        entradas += ["-i", str(v)]
    proxima = len(videos)

    # Cada vídeo é preparado uma vez e dividido entre os trechos que mostram a pessoa (A e B).
    for n in range(len(videos)):
        com_imagem = [i for i, f in enumerate(finais) if f["video"] == n + 1 and f["formato"] != "C"]
        todos = [i for i, f in enumerate(finais) if f["video"] == n + 1]
        if com_imagem:
            filtros.append(f"[{n}:v]{_cadeia_base(infos[n])},split={len(com_imagem)}" + "".join(f"[vb{i}]" for i in com_imagem))
        if todos:
            fonte_audio = (
                f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo"
                if infos[n]["audio"] else "anullsrc=r=48000:cl=stereo"
            )
            filtros.append(f"{fonte_audio},asplit={len(todos)}" + "".join(f"[ab{i}]" for i in todos))

    # Fundos de cena (B e C) e máscaras do painel (B): uma entrada por imagem, dividida entre os usos.
    dur_max = max((f["fim_original"] - f["inicio_original"] for f in finais), default=1.0) + 0.5
    fundos, paineis = {}, {}
    for i, f in enumerate(finais):
        if f["formato"] == "A":
            continue
        fundos.setdefault((f["fundo"], f["painel"] if f["formato"] == "B" else None), []).append(i)
        if f["formato"] == "B":
            paineis.setdefault(f["painel"], []).append(i)
    for (hexa, painel), idx in fundos.items():
        png = pasta_cartelas / f"fundo-{hexa.lstrip('#')}-{int(painel * 100) if painel else 'c'}.png"
        desenhar_fundo(hexa, receita, estilo, png, painel)
        entradas += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur_max:.3f}", "-i", str(png)]
        filtros.append(f"[{proxima}:v]format=yuv420p,split={len(idx)}" + "".join(f"[fb{i}]" for i in idx))
        proxima += 1
    for painel, idx in paineis.items():
        png = pasta_cartelas / f"mascara-{int(painel * 100)}.png"
        desenhar_mascara(painel, png)
        entradas += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur_max:.3f}", "-i", str(png)]
        filtros.append(f"[{proxima}:v]format=gray,split={len(idx)}" + "".join(f"[mk{i}]" for i in idx))
        proxima += 1

    alterna, anterior = 0, None
    alto = float(zoom.get("altura_rosto", 0.35))
    for i, f in enumerate(finais):
        ini, fim = f["inicio_original"], f["fim_original"]
        d = fim - ini
        tv, ta = _transicao(f["transicao"]) if i > 0 or f["transicao"] == "fade" else ("", "")
        fim_cadeia = f"{tv},fps={FPS},format=yuv420p,setsar=1[v{i}]"
        if f["formato"] == "A":
            cadeia = f"[vb{i}]trim={ini}:{fim},setpts=PTS-STARTPTS"
            fz = f["zoom"]
            if fz is None:
                fz = float(zoom.get("fator", 1.12)) if zoom.get("ativo", True) and alterna % 2 == 1 else 1.0
            alterna += 1
            fz, ang = float(fz), f["inclinacao"]
            if ang:
                fz = max(fz, 1.0 + abs(ang) * 0.035)
            if fz > 1.0:
                w, h = int(LARGURA * fz) // 2 * 2, int(ALTURA * fz) // 2 * 2
                cadeia += f",scale={w}:{h}"
                if ang:
                    cadeia += f",rotate=a={ang}*PI/180:ow={LARGURA}:oh={ALTURA}:c=black"
                else:
                    cadeia += f",crop={LARGURA}:{ALTURA}:{(w - LARGURA) // 2}:{int((h - ALTURA) * alto)}"
            filtros.append(cadeia + fim_cadeia)
        elif f["formato"] == "B":
            ph, pw = altura_painel(f["painel"]), LARGURA - 2 * MARGEM_PAINEL
            ch = int(round(LARGURA * ph / pw / 2)) * 2
            topo = int(max(0, min(ALTURA - ch, alto * ALTURA - 0.36 * ch)))
            entra = i > 0 and anterior != "B"
            filtros.append(f"[vb{i}]trim={ini}:{fim},setpts=PTS-STARTPTS,crop={LARGURA}:{ch}:0:{topo},"
                           f"scale={pw}:{ph},format=yuva420p[pp{i}]")
            filtros.append(f"[mk{i}]trim=duration={d:.3f},setpts=PTS-STARTPTS[mm{i}]")
            filtros.append(f"[pp{i}][mm{i}]alphamerge" + (",fade=t=in:st=0:d=0.2:alpha=1" if entra else "") + f"[pa{i}]")
            filtros.append(f"[fb{i}]trim=duration={d:.3f},setpts=PTS-STARTPTS[bg{i}]")
            y0 = topo_painel(f["painel"])
            y = f"'{y0}+40*max(0,1-t/0.2)'" if entra else str(y0)
            filtros.append(f"[bg{i}][pa{i}]overlay=x={MARGEM_PAINEL}:y={y}:eval=frame:shortest=1" + fim_cadeia)
        else:
            filtros.append(f"[fb{i}]trim=duration={d:.3f},setpts=PTS-STARTPTS" + fim_cadeia)
        filtros.append(
            f"[ab{i}]atrim={ini}:{fim},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.02,afade=t=out:st={max(0, d - 0.03):.3f}:d=0.03{ta}[a{i}]"
        )
        anterior = f["formato"]

    k = len(finais)
    filtros.append("".join(f"[v{i}][a{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=1[vc][ac]")
    filtros.append(f"[vc]setpts=PTS/{vel},fps={FPS}[vx]")
    filtros.append(f"[ac]atempo={vel}[ax]")

    # Um click em cada item que acende (lista e fluxo com "som_itens") e em cada marcação de print.
    from sons import garantir
    click = None
    for c in t["cartoes"]:
        if c.get("tipo") in ("lista", "fluxo") and c.get("som_itens"):
            click = click or garantir()["click"][0]
            for ti in c.get("itens_tempo", []):
                t["sons"].append({"arquivo": str(click), "inicio_final": ti, "volume": 0.5})
    for im in t["imagens"]:
        if im.get("som_anotacoes"):
            click = click or garantir()["click"][0]
            for ti in im.get("anotacoes_tempo", []):
                t["sons"].append({"arquivo": str(click), "inicio_final": ti, "volume": 0.5})

    # Efeitos sonoros: entram por cima da fala, sem mudar de velocidade.
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

    # Camadas visuais, de trás para a frente: prints, cartões, legenda, textos, selo.
    animar = plano.get("animacao", True)
    camadas = []
    for n, im in enumerate(t["imagens"], 1):
        camadas.append(_camada_print(im, n, plano, pasta_cartelas))
    for n, c in enumerate(t["cartoes"], 1):
        camadas.append(_camada_cartao(c, n, plano, pasta_cartelas))
    if t["legendas"]:
        camadas.append(_trilha_legenda(t["legendas"], plano, pasta_cartelas, total, vazio))
    for n, tx in enumerate(t["textos"], 1):
        tipo = tx.get("tipo", "bloco")
        if tipo == "manchete":
            cam = _trilha_manchete(tx, n, finais, plano, pasta_cartelas, vazio)
            if cam:
                camadas.append(cam)
            continue
        png = pasta_cartelas / f"texto-{n:02d}.png"
        if tipo == "chamada":
            desenhar_chamada(tx, estilo, png, tx.get("_tema", "video"))
        else:
            desenhar(tx, estilo, png)
        camadas.append(_camada_png(png, tx, tx.get("entrada", "pop" if tipo in ("capa", "chamada") else "sobe")))
    if plano.get("selo"):
        png = pasta_cartelas / "selo.png"
        desenhar_selo(plano["selo"], estilo, png)
        camadas.append({**_camada_png(png, {"inicio_final": 0.0, "fim_final": total}, "nenhuma")})

    atual = "vx"
    for n, cam in enumerate(camadas, 1):
        anim = cam["anim"] if animar else ("nenhuma" if cam["anim"] == "nenhuma" else "fade")
        entradas += cam["args"]
        cadeia = f"[{proxima}:v]format=rgba" + cam.get("pre", "")
        x, y = "0", "0"
        dur = cam["dur"]
        if anim in ("fade", "sobe", "pop"):
            cadeia += f",fade=t=in:st=0:d={0.12 if anim == 'pop' else FADE}:alpha=1"
        if anim in ("fade", "sobe", "pop", "saida"):
            cadeia += f",fade=t=out:st={max(0, dur - FADE):.3f}:d={FADE}:alpha=1"
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
    if len(" ".join(cmd)) > 30000:
        # Linha de comando longa demais para o Windows: os filtros vão num arquivo.
        script = pasta_cartelas / "filtros.txt"
        script.write_text(";\n".join(filtros), encoding="utf-8")
        i = cmd.index("-filter_complex")
        cmd[i:i + 2] = [_opcao_script(), str(script)]
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
        linhas.append(f"file '{Path(png).resolve().as_posix()}'")
        linhas.append(f"duration {max(dur, 1 / FPS):.3f}")
    linhas.append(f"file '{Path(estados[-1][0]).resolve().as_posix()}'")
    Path(destino).write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return ["-f", "concat", "-safe", "0", "-i", str(destino)]


def _sequencia(pasta, prefixo, desenhar_quadro, n, dur):
    """Entrada animada desenhada quadro a quadro, que segura o último quadro até o fim."""
    for k in range(n):
        desenhar_quadro(k, pasta / f"{prefixo}-{k:03d}.png")
    resto = max(0.0, dur - n / FPS)
    return {"args": ["-framerate", str(FPS), "-i", str(pasta / f"{prefixo}-%03d.png")],
            "pre": f",tpad=stop_mode=clone:stop_duration={resto:.3f}"}


def _camada_cartao(c, n, plano, pasta):
    estilo, receita = plano["estilo"], plano.get("_receita")
    dur = max(0.4, c["fim_final"] - c["inicio_final"])
    anim = c.get("entrada", "pop" if c["tipo"] == "numero" else "sobe")
    base = {"ini": c["inicio_final"], "dur": dur, "anim": anim}

    if c["tipo"] == "palavra":
        def quadro(k, png):
            desenhar_palavra_solta(c, estilo, png, progresso=(k + 1) / QUADROS_PALAVRA)
        return {**base, **_sequencia(pasta, f"palavra-{n:02d}", quadro, QUADROS_PALAVRA, dur), "anim": "saida"}

    if c["tipo"] == "numero" and c.get("contar", True):
        valores = quadros_do_contador(c["valor"])
        if valores:
            def quadro(k, png):
                desenhar_cartao(c, estilo, png, valor=valores[k], receita=receita)
            return {**base, **_sequencia(pasta, f"cartao-{n:02d}", quadro, len(valores), dur)}

    if c["tipo"] in ("lista", "fluxo", "comparacao") and c.get("itens_tempo"):
        marcos = [c["inicio_final"]] + c["itens_tempo"] + [c["fim_final"]]
        estados = []
        for k in range(len(c["itens_tempo"]) + 1):
            png = pasta / f"cartao-{n:02d}-item{k}.png"
            desenhar_cartao(c, estilo, png, visiveis=k, receita=receita)
            estados.append((png, marcos[k + 1] - marcos[k]))
        args = _lista_concat(estados, pasta / f"cartao-{n:02d}.txt")
        return {**base, "args": args, "pre": f",fps={FPS},trim=duration={dur:.3f}"}

    png = pasta / f"cartao-{n:02d}.png"
    desenhar_cartao(c, estilo, png, receita=receita)
    return _camada_png(png, c, anim)


def _camada_print(im, n, plano, pasta):
    estilo, receita = plano["estilo"], plano.get("_receita")
    dur = max(0.4, im["fim_final"] - im["inicio_final"])
    anim = im.get("entrada", "sobe")
    anots = im.get("anotacoes") or []
    marcos = im.get("anotacoes_tempo") or []
    if anots and marcos:
        ini, fim = im["inicio_final"], im["fim_final"]
        estados = []
        png = pasta / f"print-{n:02d}-base.png"
        desenhar_print(im, estilo, receita, png, progresso=[0.0] * len(anots), indice=n - 1)
        estados.append((png, marcos[0] - ini))
        for k in range(len(anots)):
            prox = marcos[k + 1] if k + 1 < len(anots) else fim
            for q in range(1, QUADROS_ANOTACAO + 1):
                prog = [1.0] * k + [q / QUADROS_ANOTACAO] + [0.0] * (len(anots) - k - 1)
                png = pasta / f"print-{n:02d}-{k:02d}-{q:02d}.png"
                desenhar_print(im, estilo, receita, png, progresso=prog, indice=n - 1)
                d = 1 / FPS if q < QUADROS_ANOTACAO else max(1 / FPS, prox - marcos[k] - (QUADROS_ANOTACAO - 1) / FPS)
                estados.append((png, d))
        args = _lista_concat(estados, pasta / f"print-{n:02d}.txt")
        return {"ini": ini, "dur": dur, "anim": anim, "args": args, "pre": f",fps={FPS},trim=duration={dur:.3f}"}
    png = pasta / f"print-{n:02d}.png"
    desenhar_print(im, estilo, receita, png, indice=n - 1)
    return _camada_png(png, im, anim)


def _trilha_legenda(legendas, plano, pasta, total, vazio):
    """Toda a legenda numa trilha só; cada palavra acende quando é dita."""
    ativa = plano["legenda"].get("palavra_ativa", True)
    estados, cursor = [], 0.0
    for b, leg in enumerate(legendas):
        if leg["inicio_final"] > cursor + 0.001:
            estados.append((vazio, leg["inicio_final"] - cursor))
        tempos_p = leg["palavras_ini"] if ativa else [leg["inicio_final"]]
        for j, ini in enumerate(tempos_p):
            fim = min(tempos_p[j + 1], leg["fim_final"]) if j + 1 < len(tempos_p) else leg["fim_final"]
            if j > 0 and ini >= leg["fim_final"]:
                break
            png = pasta / f"legenda-{b:03d}-{j:02d}.png"
            desenhar_legenda(leg, plano["estilo"], png, ativa=j if ativa else None)
            estados.append((png, max(0.0, fim - max(ini, cursor))))
        cursor = leg["fim_final"]
    if total > cursor:
        estados.append((vazio, total - cursor))
    args = _lista_concat(estados, pasta / "legenda.txt")
    return {"args": args, "ini": 0.0, "dur": total, "anim": "nenhuma", "pre": f",fps={FPS}"}


def _trilha_manchete(m, n, finais, plano, pasta, vazio):
    """Manchete visível só nos trechos B e C que ela cobre, na cor do fundo de cada um."""
    ini, fim = m["inicio_final"], m["fim_final"]
    modelo = (plano.get("_receita") or {}).get("manchete", {}).get("modelo", "solta")
    estados, desenhadas = [], {}
    for f in finais:
        a, b = max(ini, f["inicio_final"]), min(fim, f["fim_final"])
        if b <= a + 0.001:
            continue
        if f["formato"] == "A":
            png = vazio
        else:
            if f["tema"] not in desenhadas:
                desenhadas[f["tema"]] = desenhar_manchete(m, plano["estilo"], pasta / f"manchete-{n:02d}-{f['tema']}.png",
                                                          f["tema"], modelo)
            png = desenhadas[f["tema"]]
        estados.append((png, b - a))
    if not desenhadas:
        return None
    args = _lista_concat(estados, pasta / f"manchete-{n:02d}.txt")
    return {"args": args, "ini": ini, "dur": fim - ini, "anim": m.get("entrada", "sobe"),
            "pre": f",fps={FPS},trim=duration={fim - ini:.3f}"}


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
