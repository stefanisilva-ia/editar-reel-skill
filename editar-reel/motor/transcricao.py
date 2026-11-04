"""Transcrição local com tempo de cada palavra (faster-whisper).

Aceita um ou mais vídeos. Com vários, cada um é transcrito em separado e
a ordem em que foram passados vira a ordem da edição.

Nada sai do computador. Na primeira vez o modelo é baixado e fica em cache.
Modelo padrão: 'medium'. Para máquinas lentas, use --modelo small.
"""
import json
import os
from pathlib import Path


def _dispositivo():
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def _carregar_modelo(modelo):
    from faster_whisper import WhisperModel

    dispositivo, precisao = _dispositivo()
    print(f"Modelo '{modelo}' ({dispositivo}). Na primeira vez o download leva alguns minutos.")
    try:
        return WhisperModel(modelo, device=dispositivo, compute_type=precisao)
    except Exception:
        if dispositivo == "cpu":
            raise
        print("Placa de vídeo indisponível, seguindo no processador.")
        return WhisperModel(modelo, device="cpu", compute_type="int8")


def transcrever(videos, pasta, modelo=None, idioma="pt"):
    modelo = modelo or os.environ.get("EDITAR_REEL_MODELO", "medium")
    whisper = _carregar_modelo(modelo)

    resultado = []
    for n, video in enumerate(videos, 1):
        video = Path(video).expanduser().resolve()
        print(f"[{n}/{len(videos)}] Transcrevendo {video.name}")
        segmentos, info = whisper.transcribe(
            str(video),
            language=idioma,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        palavras = []
        for seg in segmentos:
            for p in seg.words or []:
                texto = p.word.strip()
                if texto:
                    palavras.append({"p": texto, "i": round(p.start, 3), "f": round(p.end, 3)})
        resultado.append({"arquivo": str(video), "duracao": round(info.duration, 3), "palavras": palavras})

    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "transcricao.json").write_text(
        json.dumps({"videos": resultado}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    linhas = []
    for n, v in enumerate(resultado, 1):
        if len(resultado) > 1:
            linhas.append(f"## Vídeo {n}: {Path(v['arquivo']).name}")
        linhas.append(" ".join(p["p"] for p in v["palavras"]))
        linhas.append("")
    (pasta / "transcricao.txt").write_text("\n".join(linhas), encoding="utf-8")
    return resultado
