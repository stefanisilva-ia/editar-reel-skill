# Editar reel

Skill para o Claude Code que edita reel falado sem abrir editor de vídeo.

Você grava falando para a câmera, chama `/editar-reel` e recebe o vídeo pronto para postar. Uso no meu próprio conteúdo e deixo aberta para quem quiser usar também.

## O que ela faz

1. **Transcreve no seu computador.** Nada vai para a internet, sem custo por vídeo.
2. **Propõe os cortes.** Pausas, tomadas repetidas e frases que começaram erradas. Você aprova antes de qualquer corte.
3. **Dá ritmo.** Alterna plano aberto e plano fechado a cada frase, como se houvesse duas câmeras.
4. **Coloca texto na tela.** Resume a fala em blocos de até 6 palavras, com números e resultados destacados na cor da marca.
5. **Exporta em 9:16.** 1080x1920, pronto para Instagram, TikTok e Shorts.

Depois é só pedir ajuste em texto: "corta a terceira frase", "abre pela frase do resultado", "troca a cor do destaque".

## Texto na tela

A skill segue regras fixas, porque texto na tela não é legenda:

- Máximo de 6 palavras por bloco
- Resume a fala, nunca transcreve
- Números, resultados e palavra-chave em destaque
- Listas numeradas: 1º, 2º, 3º
- Afirmação curta no lugar de pergunta
- Resultado concreto no lugar de benefício vago

| A fala | Na tela |
|---|---|
| "ficou pronto em uns dez minutos" | **pronto em 10 minutos** |
| "a segunda é o atendimento vinte e quatro horas" | **2º ATENDIMENTO 24H** |
| "o cliente não precisa mais ligar pra confirmar" | **agenda confirmada sozinha** |
| "comenta a palavra agente" | **comenta AGENTE** |

## O que você precisa

- [Claude Code](https://claude.com/claude-code)
- Python 3.9 ou mais novo
- ffmpeg

| | Mac | Windows | Linux |
|---|---|---|---|
| Python | já vem instalado (ou `brew install python`) | `winget install Python.Python.3.12` | `sudo apt install python3 python3-venv` |
| ffmpeg | `brew install ffmpeg` | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` |

Com placa NVIDIA, a transcrição usa a placa. Sem ela, roda no processador: um reel de 1 minuto leva poucos minutos. Se ficar lento, use o modelo menor com `EDITAR_REEL_MODELO=small`.

## Instalação

**Mais rápido:** abra o Claude Code e cole:

```
https://github.com/stefanisilva-ia/editar-reel-skill

Instala essa skill pra mim e confere as dependências.
```

**Pelo terminal (Mac e Linux):**

```bash
git clone https://github.com/stefanisilva-ia/editar-reel-skill.git
cd editar-reel-skill
bash instalar.sh
```

**Pelo PowerShell (Windows):**

```powershell
git clone https://github.com/stefanisilva-ia/editar-reel-skill.git
cd editar-reel-skill
powershell -ExecutionPolicy Bypass -File instalar.ps1
```

Para atualizar, rode o instalador de novo. Ele troca os arquivos e mantém o que já foi baixado.

## Como usar

```
/editar-reel o vídeo está em ~/Downloads/gravacao.MOV, palavra-chave AGENTE
```

Na primeira vez, o modelo de transcrição é baixado. Leva alguns minutos e acontece uma vez só.

## Para gravar melhor

- Fale olhando para a câmera e respire entre as frases. A pausa vira ponto de corte.
- Errou? Repita a frase inteira. A skill identifica a repetição e propõe ficar com a melhor.
- Diga números e resultados em voz alta. Eles viram destaque na tela.
- Grave na vertical, com o rosto no terço de cima do quadro.

## Personalização

Cores, fonte e tamanho ficam no `plano.json` de cada vídeo, no campo `estilo`:

```json
"estilo": {
  "cor_texto": "#FFFFFF",
  "cor_destaque": "#FFD60A",
  "cor_caixa": "#000000B8",
  "fonte": "~/Fontes/MinhaFonte-Bold.ttf",
  "tamanho": 68
}
```

## Estrutura

| Arquivo | Função |
|---|---|
| `editar-reel/SKILL.md` | Passo a passo e regras que o Claude segue |
| `editar-reel/motor/cli.py` | Comandos: checar, transcrever, segmentar, validar, renderizar, quadros |
| `editar-reel/motor/transcricao.py` | Transcrição local com o tempo de cada palavra |
| `editar-reel/motor/segmentos.py` | Divide a fala em trechos e cria o plano |
| `editar-reel/motor/plano.py` | Valida o plano e calcula a linha do tempo final |
| `editar-reel/motor/cartelas.py` | Desenha o texto na tela |
| `editar-reel/motor/render.py` | Corta, enquadra, dá ritmo e exporta |
| `instalar.sh` e `instalar.ps1` | Instaladores |

## Licença

MIT. Pode usar, adaptar e compartilhar.
