"""Editar reel: comandos da skill.

  python motor/cli.py checar
  python motor/cli.py transcrever VIDEO [--modelo small]
  python motor/cli.py segmentar PASTA [--pausa 0.45]
  python motor/cli.py validar PASTA
  python motor/cli.py cartelas PASTA
  python motor/cli.py renderizar PASTA
  python motor/cli.py quadros PASTA [--tempos 1,4,9]

PASTA é a pasta de trabalho criada ao lado do vídeo: <nome-do-video>-reel/
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plano as P  # noqa: E402


def pasta_do_video(video):
    video = Path(video).expanduser().resolve()
    return video.parent / f"{video.stem}-reel"


def cmd_checar(_):
    ok = True
    for prog in ("ffmpeg", "ffprobe"):
        achou = shutil.which(prog)
        print(f"{'OK ' if achou else 'FALTA'} {prog}")
        ok &= bool(achou)
    for mod, nome in (("PIL", "Pillow"), ("faster_whisper", "faster-whisper")):
        try:
            __import__(mod)
            print(f"OK  {nome}")
        except ImportError:
            print(f"FALTA {nome}  (rode o instalador da skill)")
            ok = False
    from cartelas import achar_fonte
    fonte = achar_fonte()
    print(f"{'OK ' if fonte else 'AVISO'} fonte: {fonte or 'nenhuma negrito encontrada, vou usar a padrão'}")
    sys.exit(0 if ok else 1)


def cmd_transcrever(a):
    from transcricao import transcrever
    pasta = pasta_do_video(a.video)
    dados = transcrever(Path(a.video).expanduser(), pasta, a.modelo)
    print(f"\n{len(dados['palavras'])} palavras, {dados['duracao']:.1f} s.")
    print(f"Pasta de trabalho: {pasta}")
    print(f"Texto: {pasta / 'transcricao.txt'}")


def cmd_segmentar(a):
    from segmentos import segmentar
    caminho, trechos = segmentar(a.pasta, a.pausa)
    total = sum(t["fim"] - t["inicio"] for t in trechos)
    print(f"{len(trechos)} trechos, {total:.1f} s de fala. Plano em {caminho}\n")
    for t in trechos:
        print(f"[{t['id']:>2}] {t['inicio']:6.2f} a {t['fim']:6.2f}  {t['fala']}")


def cmd_validar(a):
    plano = P.carregar(a.pasta)
    problemas = P.validar(plano)
    if problemas:
        print("Ajustes necessários:")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)
    textos, total = P.tempos_dos_textos(plano)
    print(f"Plano ok. Duração final: {total:.1f} s.\n")
    for tx in textos:
        print(f"{tx['inicio_final']:6.2f} a {tx['fim_final']:6.2f}  [{tx.get('tipo', 'bloco')}] {tx['texto']}")


def cmd_cartelas(a):
    from cartelas import desenhar
    plano = P.carregar(a.pasta)
    destino = Path(a.pasta) / "cartelas"
    destino.mkdir(exist_ok=True)
    for n, tx in enumerate(plano["textos"], 1):
        print(desenhar(tx, plano["estilo"], destino / f"texto-{n:02d}.png"))


def cmd_renderizar(a):
    from render import renderizar
    plano = P.carregar(a.pasta)
    problemas = P.validar(plano)
    if problemas:
        print("O plano tem problemas, rode 'validar' e corrija:")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)
    saida, total, _ = renderizar(a.pasta, plano)
    print(f"\nPronto: {saida} ({total:.1f} s)")


def cmd_quadros(a):
    plano = P.carregar(a.pasta)
    video = Path(a.pasta) / plano.get("saida", "reel-final.mp4")
    if a.tempos:
        tempos = [float(t) for t in a.tempos.split(",")]
    else:
        textos, total = P.tempos_dos_textos(plano)
        tempos = [round((t["inicio_final"] + t["fim_final"]) / 2, 2) for t in textos] or [total / 2]
    destino = Path(a.pasta) / "quadros"
    destino.mkdir(exist_ok=True)
    for t in tempos:
        png = destino / f"quadro-{t:06.2f}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", str(video),
             "-frames:v", "1", "-vf", "scale=540:-2", str(png)],
            check=True,
        )
        print(png)


def main():
    ap = argparse.ArgumentParser(description="Editar reel")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("checar").set_defaults(f=cmd_checar)
    s = sub.add_parser("transcrever")
    s.add_argument("video")
    s.add_argument("--modelo", default=None)
    s.set_defaults(f=cmd_transcrever)
    s = sub.add_parser("segmentar")
    s.add_argument("pasta")
    s.add_argument("--pausa", type=float, default=0.45)
    s.set_defaults(f=cmd_segmentar)
    for nome, f in (("validar", cmd_validar), ("cartelas", cmd_cartelas), ("renderizar", cmd_renderizar)):
        s = sub.add_parser(nome)
        s.add_argument("pasta")
        s.set_defaults(f=f)
    s = sub.add_parser("quadros")
    s.add_argument("pasta")
    s.add_argument("--tempos", default=None)
    s.set_defaults(f=cmd_quadros)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
