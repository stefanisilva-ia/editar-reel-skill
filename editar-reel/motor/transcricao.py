"""Transcrição local com tempo de cada palavra (faster-whisper).

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


def transcrever(video, pasta, modelo=None, idioma="pt"):
    from faster_whisper import WhisperModel

    modelo = modelo or os.environ.get("EDITAR_REEL_MODELO", "medium")
    dispositivo, precisao = _dispositivo()
    print(f"Transcrevendo com o modelo '{modelo}' ({dispositivo}). Na primeira vez o download leva alguns minutos.")
    try:
        whisper = WhisperModel(modelo, device=dispositivo, compute_type=precisao)
    except Exception:
        if dispositivo == "cpu":
            raise
        print("Placa de vídeo indisponível, seguindo no processador.")
        whisper = WhisperModel(modelo, device="cpu", compute_type="int8")

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

    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    dados = {"video": str(Path(video).resolve()), "duracao": round(info.duration, 3), "palavras": palavras}
    (pasta / "transcricao.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    (pasta / "transcricao.txt").write_text(" ".join(p["p"] for p in palavras), encoding="utf-8")
    return dados
