"""Editar reel: comandos da skill.

  python motor/cli.py checar
  python motor/cli.py transcrever VIDEO [VIDEO2 ...] [--pasta NOME] [--modelo small]
  python motor/cli.py segmentar PASTA [--pausa 0.45]
  python motor/cli.py estilo PASTA_ESTILO [--aplicar PASTA]
  python motor/cli.py sons
  python motor/cli.py receitas
  python motor/cli.py referencia VIDEO [--a-cada 1.0] [--pasta DESTINO]
  python motor/cli.py mapa PASTA
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
    from cartelas import FONTE_DESTAQUE, FONTE_ROTULO, FONTE_TEXTO, _da_skill
    for nome in (FONTE_TEXTO, FONTE_DESTAQUE, FONTE_ROTULO):
        arq = _da_skill(nome)
        print(f"{'OK ' if arq else 'AVISO'} fonte {nome}: {Path(arq).name if arq else 'faltando na pasta fontes/ da skill'}")
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


def cmd_receitas(_):
    from visual import FUNDOS_PADRAO, PASTA_RECEITAS, listar_receitas
    print("Receitas de estilo (campo \"receita\" do plano):\n")
    for nome in listar_receitas():
        md = PASTA_RECEITAS / f"{nome}.md"
        resumo = ""
        if md.exists():
            linhas = [l for l in md.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
            resumo = linhas[0] if linhas else ""
        print(f"  {nome:<16} {resumo}")
    print("\nFundos da paleta (campo \"fundo\" do trecho):\n")
    for nome, hexa in FUNDOS_PADRAO.items():
        print(f"  {nome:<16} {hexa}")


def cmd_referencia(a):
    from referencia import folhas
    video = Path(a.video).expanduser().resolve()
    destino = Path(a.pasta).expanduser() if a.pasta else video.parent / f"{video.stem}-referencia"
    saidas, total = folhas(video, destino, a.a_cada)
    print(f"Vídeo de {total:.1f} s, um quadro a cada {a.a_cada:g} s. Folhas para analisar:")
    for arq in saidas:
        print(f"  {arq}")


def cmd_mapa(a):
    plano = P.carregar(a.pasta)
    problemas = P.validar(plano, a.pasta)
    linhas, t, chamada = P.mapa(plano, a.pasta)
    receita = plano.get("receita") or "nenhuma (padrão)"
    print(f"Receita: {receita if isinstance(receita, str) else receita}\n")
    print("| # | Início | Fala | Formato | Fundo | Peças | Som |")
    print("|---|---|---|---|---|---|---|")
    for ln in linhas:
        fala = ln["fala"] if len(ln["fala"]) <= 46 else ln["fala"][:44] + "..."
        print(f"| {ln['id']} | {ln['inicio']:.1f} s | {fala} | {ln['formato']} | {ln['fundo']} | {ln['pecas']} | {ln['sons']} |")
    for ini, texto in chamada:
        print(f"| fim | {ini:.1f} s | (chamada) | - | - | chamada: {texto} | - |")
    total = t["total"] or 1
    partes = {fmt: sum(f["fim_final"] - f["inicio_final"] for f in t["finais"] if f["formato"] == fmt) for fmt in "ABC"}
    print(f"\nDuração: {t['total']:.1f} s. Tela cheia {partes['A'] / total:.0%}, dividida {partes['B'] / total:.0%}, "
          f"só gráficos {partes['C'] / total:.0%}.")
    for aviso in t["avisos"]:
        print(f"Aviso: {aviso}")
    if problemas:
        print("\nAjustes necessários antes de renderizar:")
        for p in problemas:
            print(f"  - {p}")


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
        desc = c.get("valor") or c.get("texto") or c.get("titulo") or ", ".join(c.get("itens", [])[:3])
        if c["tipo"] == "comparacao":
            desc = f"{(c.get('esquerda') or {}).get('titulo', '')} x {(c.get('direita') or {}).get('titulo', '')}"
        linhas.append((c["inicio_final"], c["fim_final"], f"cartão [{c['tipo']}] {desc}"))
    for im in t["imagens"]:
        linhas.append((im["inicio_final"], im["fim_final"], f"print {Path(im['arquivo']).name}"))
    for s in t["sons"]:
        linhas.append((s["inicio_final"], s["inicio_final"], f"som {Path(s['arquivo']).name}"))
    for f in t["finais"]:
        if f["formato"] != "A":
            linhas.append((f["inicio_final"], f["fim_final"], f"trecho {f['id']}: formato {f['formato']}, fundo {f['fundo_nome']}"))
    for ini, fim, txt in sorted(linhas):
        print(f"{ini:6.2f} a {fim:6.2f}  {txt}")
    for aviso in t["avisos"]:
        print(f"Aviso: {aviso}")


def cmd_cartelas(a):
    from cartelas import desenhar, desenhar_cartao, desenhar_chamada, desenhar_manchete
    from prints import desenhar_print
    plano = P.carregar(a.pasta)
    t = P.tempos(plano, a.pasta)
    estilo, receita = plano["estilo"], plano["_receita"]
    destino = Path(a.pasta) / "cartelas"
    destino.mkdir(exist_ok=True)
    for n, tx in enumerate(t["textos"], 1):
        png = destino / f"texto-{n:02d}.png"
        if tx.get("tipo") == "manchete":
            print(desenhar_manchete(tx, estilo, png, tx.get("_tema", "escuro"), receita["manchete"].get("modelo", "solta")))
        elif tx.get("tipo") == "chamada":
            print(desenhar_chamada(tx, estilo, png, tx.get("_tema", "video")))
        else:
            print(desenhar(tx, estilo, png))
    for n, im in enumerate(t["imagens"], 1):
        print(desenhar_print(im, estilo, receita, destino / f"print-{n:02d}.png", indice=n - 1))
    for n, c in enumerate(t["cartoes"], 1):
        print(desenhar_cartao(c, estilo, destino / f"cartao-{n:02d}.png", receita=receita))


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
        itens = t["textos"] + t["imagens"] + t["cartoes"] + t["legendas"][::3] + [f for f in t["finais"] if f["formato"] != "A"]
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
    sub.add_parser("receitas").set_defaults(f=cmd_receitas)
    s = sub.add_parser("referencia")
    s.add_argument("video")
    s.add_argument("--a-cada", dest="a_cada", type=float, default=1.0)
    s.add_argument("--pasta", default=None)
    s.set_defaults(f=cmd_referencia)
    for nome, f in (("mapa", cmd_mapa), ("validar", cmd_validar), ("cartelas", cmd_cartelas), ("renderizar", cmd_renderizar)):
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
