# Editar reel

Skill para o Claude Code que edita reel falado sem abrir editor de vídeo.

Você grava falando para a câmera, chama `/editar-reel` e recebe o vídeo pronto para postar. Uso no meu próprio conteúdo e deixo aberta para quem quiser usar também.

## O que ela faz

1. **Transcreve no seu computador.** Nada vai para a internet, sem custo por vídeo.
2. **Propõe os cortes.** Pausas, tomadas repetidas e frases que começaram erradas. Você aprova antes de qualquer corte.
3. **Junta vários vídeos.** Rosto e gravação de tela numa edição só, na ordem que você indicar.
4. **Dá ritmo.** Alterna plano aberto e plano fechado a cada frase, com transições onde você pedir.
5. **Coloca texto, prints e sons.** Texto na tela em blocos de até 6 palavras, prints flutuando e efeitos sonoros no momento exato da fala.
6. **Exporta em 9:16** e escreve a legenda do post. 1080x1920, pronto para Instagram, TikTok e Shorts.

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

Na primeira vez, o modelo de transcrição é baixado. Leva alguns minutos e acontece uma vez só.

Quanto mais claro o pedido, menos perguntas o Claude faz. Um bom pedido diz **onde estão os arquivos**, **a ordem**, **o que entra em cada momento** e **a palavra-chave da chamada**.

### Organize a pasta assim

```
reel-painel/
├── videos/   01-abertura.mov   02-tela.mov
├── prints/   painel.png   whatsapp.png
└── sons/     pop.wav   whoosh.mp3
```

> Numere os vídeos (01, 02...) e o Claude segue essa ordem sem perguntar. Prints e sons com nomes claros ficam fáceis de citar no pedido.

### 1. Edição simples

```
/editar-reel o vídeo está em ~/Downloads/gravacao.MOV.
É pro Instagram, palavra-chave AGENTE. Acelera 1.1.
```

> **O que faz:** transcreve, propõe os cortes, monta o texto na tela e a chamada "comenta AGENTE". **Adapte:** troque a palavra-chave e tire o "acelera" se quiser a fala no ritmo original.

### 2. Com prints de uma pasta

```
/editar-reel o vídeo está em ~/reel-painel/videos/01-abertura.mov.
Os prints estão em ~/reel-painel/prints.
Quando eu falar "painel", mostra o painel.png.
Quando eu falar "WhatsApp", mostra o whatsapp.png até o fim da frase.
Coloca o crédito "print: sistema do cliente" embaixo dos dois.
```

> **O que faz:** encontra a palavra na transcrição e faz o print entrar flutuando nesse momento. **Adapte:** cite qualquer palavra que você diz no vídeo. Sem crédito, é só não pedir.

### 3. Juntando dois vídeos

```
/editar-reel junta os vídeos da pasta ~/reel-painel/videos numa edição só.
Primeiro o 01-abertura (eu falando), depois o 02-tela (gravação da tela).
Corta as pausas dos dois e usa transição fade na troca de vídeo.
```

> **O que faz:** transcreve os dois, propõe os cortes de cada um e entrega um reel só, na ordem pedida. **Adapte:** para inverter, diga a ordem em texto. Vale para três ou mais vídeos.

### 4. Com efeitos sonoros

```
/editar-reel o vídeo está em ~/reel-painel/videos/01-abertura.mov.
Os sons estão em ~/reel-painel/sons.
Põe o pop.wav quando o número "10 horas" aparecer na tela
e o whoosh.mp3 na entrada do print. Volume baixo nos dois.
```

> **O que faz:** encaixa cada som no momento descrito, por cima da fala. **Adapte:** "volume baixo" vira 0.4, "normal" 0.8. A skill não traz sons: use arquivos seus ou de bancos livres.

### 5. Pedido completo

```
/editar-reel pasta do projeto: ~/reel-painel
1. Junta 01-abertura e 02-tela, nessa ordem.
2. Abre pela frase "economizei 10 horas por semana".
3. Mostra o painel.png quando eu falar "painel", com o pop.wav junto.
4. Transição flash na troca de vídeo.
5. Palavra-chave PAINEL. Acelera 1.1.
6. Escreve a legenda do post com 3 hashtags.
```

> **O que faz:** tudo de uma vez. O Claude ainda mostra os cortes e as opções de capa para você aprovar antes de renderizar. **Adapte:** numere os pedidos, um por linha. Fica mais fácil para você revisar e para o Claude seguir.

### Ajustes depois da entrega

Peça em texto, como faria com um editor:

| Pedido | O que muda |
|---|---|
| `corta a terceira frase` | remove o trecho e renderiza de novo |
| `troca o texto "pronto em 1 dia" por "pronto em 24h"` | só o texto na tela |
| `tira o print do WhatsApp` | remove a imagem |
| `som mais baixo` | reduz o volume dos efeitos |
| `sem zoom nos cortes` | desliga a alternância de plano |
| `muda o destaque para #dfac16` | troca a cor dos números e palavras-chave |
| `refaz a legenda do post, mais curta` | reescreve o `legenda.txt` |

### O que cada transição faz

| Transição | Efeito | Quando usar |
|---|---|---|
| `corte` | direto, padrão | quase sempre |
| `fade` | escurece e abre | troca de vídeo ou de assunto |
| `flash` | clarão branco rápido | revelar um resultado |
| `zoom` | aproximação rápida | dar ênfase a uma frase |

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
