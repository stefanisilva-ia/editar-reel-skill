"""Editar reel: comandos da skill.

  python motor/cli.py checar
  python motor/cli.py transcrever VIDEO [VIDEO2 ...] [--pasta NOME] [--modelo small]
  python motor/cli.py segmentar PASTA [--pausa 0.45]
  python motor/cli.py estilo PASTA_ESTILO [--aplicar PASTA]
  python motor/cli.py sons
  python motor/cli.py validar PASTA
  python motor/cli.py cartelas PASTA
  python motor/cli.py renderizar PASTA
  python motor/cli.py quadros PASTA [--tempos 1,4,9]

PASTA é a pasta de trabalho criada ao lado do (primeiro) vídeo: <nome-do-video>-reel/
Com --pasta, ela é criada com esse nome ao lado do primeiro vídeo.
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
    primeiro = Path(a.videos[0]).expanduser().resolve()
    pasta = primeiro.parent / a.pasta if a.pasta else pasta_do_video(primeiro)
    dados = transcrever(a.videos, pasta, a.modelo)
    for n, v in enumerate(dados, 1):
        print(f"Vídeo {n}: {Path(v['arquivo']).name}, {len(v['palavras'])} palavras, {v['duracao']:.1f} s.")
    print(f"\nPasta de trabalho: {pasta}")
    print(f"Texto: {pasta / 'transcricao.txt'}")


def cmd_segmentar(a):
    from segmentos import segmentar
    caminho, trechos = segmentar(a.pasta, a.pausa)
    total = sum(t["fim"] - t["inicio"] for t in trechos)
    print(f"{len(trechos)} trechos, {total:.1f} s de fala. Plano em {caminho}\n")
    varios = len({t["video"] for t in trechos}) > 1
    for t in trechos:
        origem = f"v{t['video']} " if varios else ""
        print(f"[{t['id']:>2}] {origem}{t['inicio']:6.2f} a {t['fim']:6.2f}  {t['fala']}")
    from segmentos import sugerir_cortes
    sugestoes = sugerir_cortes(trechos)
    if sugestoes:
        print("\nSugestões de corte (confirme com a pessoa antes de aplicar):")
        for s in sugestoes:
            print(f"  - {s}")


def cmd_estilo(a):
    import json
    from estilo import ler, sugerir
    achado = ler(a.pasta_estilo)
    print(f"Imagens: {len(achado['imagens'])}  Fontes: {len(achado['fontes'])}  Textos: {len(achado['textos'])}\n")
    for im in achado["imagens"]:
        cores = ", ".join(f"{c} ({int(pc * 100)}%)" for c, pc in im["cores"])
        print(f"  {Path(im['arquivo']).name}: {cores}")
    for f in achado["fontes"]:
        print(f"  fonte: {Path(f).name}")
    for t in achado["textos"]:
        print(f"  {Path(t['arquivo']).name}: {', '.join(t['cores']) or 'sem cores'}")
    if achado["rotuladas"]:
        print(f"  cores com função definida: {achado['rotuladas']}")
    if achado["fonte_nome"]:
        print(f"  fonte citada: {achado['fonte_nome']}")
    sugestao = sugerir(achado)
    print("\nEstilo sugerido:")
    print(json.dumps(sugestao, ensure_ascii=False, indent=2))
    if a.aplicar:
        plano = json.loads((Path(a.aplicar) / "plano.json").read_text(encoding="utf-8"))
        plano.setdefault("estilo", {}).update(sugestao)
        P.salvar(a.aplicar, plano)
        print(f"\nAplicado em {Path(a.aplicar) / 'plano.json'}. Ajuste à mão o que as imagens mostrarem (caixa, maiúsculas).")


def cmd_sons(_):
    from sons import garantir
    print("Efeitos sonoros básicos (use o caminho no campo 'arquivo' de 'sons'):\n")
    for nome, (arq, uso) in garantir().items():
        print(f"  {nome:<8} {arq}\n           {uso}")


def cmd_validar(a):
    plano = P.carregar(a.pasta)
    problemas = P.validar(plano, a.pasta)
    if problemas:
        print("Ajustes necessários:")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)
    t = P.tempos(plano, a.pasta)
    print(f"Plano ok. Duração final: {t['total']:.1f} s.\n")
    linhas = []
    if t["legendas"]:
        linhas.append((t["legendas"][0]["inicio_final"], t["legendas"][-1]["fim_final"],
                       f"legenda da fala: {len(t['legendas'])} blocos"))
    for tx in t["textos"]:
        linhas.append((tx["inicio_final"], tx["fim_final"], f"texto [{tx.get('tipo', 'bloco')}] {tx['texto']}"))
    for c in t["cartoes"]:
        desc = c.get("valor") or c.get("texto") or c.get("titulo") or ""
        linhas.append((c["inicio_final"], c["fim_final"], f"cartão [{c['tipo']}] {desc}"))
    for im in t["imagens"]:
        linhas.append((im["inicio_final"], im["fim_final"], f"print {Path(im['arquivo']).name}"))
    for s in t["sons"]:
        linhas.append((s["inicio_final"], s["inicio_final"], f"som {Path(s['arquivo']).name}"))
    for ini, fim, txt in sorted(linhas):
        print(f"{ini:6.2f} a {fim:6.2f}  {txt}")
    for aviso in t["avisos"]:
        print(f"Aviso: {aviso}")


def cmd_cartelas(a):
    from cartelas import desenhar, desenhar_imagem
    plano = P.carregar(a.pasta)
    destino = Path(a.pasta) / "cartelas"
    destino.mkdir(exist_ok=True)
    for n, tx in enumerate(plano["textos"], 1):
        print(desenhar(tx, plano["estilo"], destino / f"texto-{n:02d}.png"))
    for n, im in enumerate(plano["imagens"], 1):
        print(desenhar_imagem(im, plano["estilo"], destino / f"print-{n:02d}.png"))
    from cartelas import desenhar_cartao
    for n, c in enumerate(plano["cartoes"], 1):
        print(desenhar_cartao(c, plano["estilo"], destino / f"cartao-{n:02d}.png"))


def cmd_renderizar(a):
    from render import renderizar
    plano = P.carregar(a.pasta)
    problemas = P.validar(plano, a.pasta)
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
        t = P.tempos(plano, a.pasta)
        itens = t["textos"] + t["imagens"] + t["cartoes"] + t["legendas"][::3]
        tempos = sorted({round((i["inicio_final"] + i["fim_final"]) / 2, 2) for i in itens}) or [t["total"] / 2]
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
    s.add_argument("videos", nargs="+")
    s.add_argument("--pasta", default=None)
    s.add_argument("--modelo", default=None)
    s.set_defaults(f=cmd_transcrever)
    s = sub.add_parser("segmentar")
    s.add_argument("pasta")
    s.add_argument("--pausa", type=float, default=0.45)
    s.set_defaults(f=cmd_segmentar)
    s = sub.add_parser("estilo")
    s.add_argument("pasta_estilo")
    s.add_argument("--aplicar", default=None)
    s.set_defaults(f=cmd_estilo)
    sub.add_parser("sons").set_defaults(f=cmd_sons)
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
