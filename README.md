# Editar reel

Skill para o Claude Code que edita reel falado sem abrir editor de vídeo.

Você grava falando para a câmera, chama `/editar-reel` e recebe o vídeo pronto para postar. Uso no meu próprio conteúdo e deixo aberta para quem quiser usar também.

## O que ela faz

1. **Transcreve no seu computador.** Nada vai para a internet, sem custo por vídeo.
2. **Propõe os cortes.** Pausas, tomadas repetidas e frases que começaram erradas. Você aprova antes de qualquer corte.
3. **Junta vários vídeos.** Rosto e gravação de tela numa edição só, na ordem que você indicar.
4. **Dá ritmo.** Alterna plano aberto e plano fechado a cada frase, com transições onde você pedir.
5. **Coloca texto, imagens e sons.** Texto na tela em resumo ou legenda da fala, cartões ilustrativos com números e listas, prints flutuando e efeitos sonoros no momento exato.
6. **Segue referências de estilo.** Cores, fontes e prints de uma pasta `estilo/` valem para aquele vídeo.
7. **Exporta em 9:16** e escreve a legenda do post. 1080x1920, pronto para Instagram, TikTok e Shorts.

Depois é só pedir ajuste em texto: "corta a terceira frase", "abre pela frase do resultado", "troca a cor do destaque".

## Texto na tela: resumo ou legenda

Você escolhe, a cada vídeo:

- **Resumo** (padrão): a fala vira blocos curtos, que quem assiste sem som entende em um segundo.
- **Transcrição**: legenda sincronizada com a fala, palavra por palavra, só dos trechos que ficaram.

No modo resumo, a skill segue regras fixas:

- Máximo de 6 palavras por bloco
- Números, resultados e palavra-chave em destaque
- Listas numeradas: 1º, 2º, 3º
- Afirmação curta no lugar de pergunta
- Resultado concreto no lugar de benefício vago

| A fala | Resumo na tela |
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

## Como usar

Na primeira vez, o modelo de transcrição é baixado. Leva alguns minutos e acontece uma vez só.

Quanto mais claro o pedido, menos perguntas o Claude faz. Um bom pedido diz **onde estão os arquivos**, **a ordem**, **o que entra em cada momento** e **a palavra-chave da chamada**.

### Organize a pasta assim

```
reel-painel/
├── videos/   01-abertura.mov   02-tela.mov
├── prints/   painel.png   whatsapp.png
├── sons/     pop.wav   whoosh.mp3
└── estilo/   referencia.png   MinhaFonte-Bold.ttf   cores.md   (opcional)
```

> Numere os vídeos (01, 02...) e o Claude segue essa ordem sem perguntar. Prints e sons com nomes claros ficam fáceis de citar no pedido. A pasta `estilo/` só é necessária quando o vídeo foge do seu visual de sempre.

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

> **O que faz:** encaixa cada som no momento descrito, por cima da fala. **Adapte:** "volume baixo" vira 0.4, "normal" 0.8. Sem arquivos seus, a skill usa os próprios: pop, click, ding, impacto e whoosh, criados por ela e livres de direitos autorais.

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

### 6. Com legenda da fala

```
/editar-reel o vídeo está em ~/Downloads/tutorial.MOV.
Quero legenda transcrevendo a fala, 3 palavras por vez.
Corrige "cloud code" para "Claude Code". Palavra-chave GUIA.
```

> **O que faz:** gera a legenda sincronizada com o que você fala, já sem os trechos cortados, e mantém a capa e a chamada final. **Adapte:** menos palavras por vez deixa mais dinâmico. Para voltar ao resumo, peça "resume a fala".

### 7. Com referência de estilo

```
/editar-reel pasta do projeto: ~/reel-campanha
Usa o estilo da pasta estilo: as cores do cores.md,
a fonte que está lá e o jeito de texto da referencia.png.
```

Exemplo de `cores.md`:

```
destaque: #FF5A1F
fundo da caixa: #1B1B3A
texto: #FFFFFF
fonte: Montserrat
```

> **O que faz:** lê as cores, a fonte e as imagens de referência e aplica só neste vídeo. Antes de renderizar, o Claude diz qual estilo vai usar. **Adapte:** sem `cores.md`, as cores saem das imagens. Para mudar o seu visual de sempre, peça "salva esse estilo como padrão".

### 8. Deixando o Claude decidir

```
/editar-reel o vídeo está em ~/reels/agentes/video.mov.
As referências de estilo (imagens e cores) estão em ~/marca/estilo.

Este vídeo é para o Instagram. Crie imagens que ilustrem e complementem o que está sendo falado, inserindo-as nos momentos correspondentes do vídeo.

Adicione efeitos sonoros quando fizer sentido, especialmente para reforçar informações, palavras ou momentos de destaque. Utilize transições suaves entre as cenas.

Mantenha legendas completas na tela, destacando visualmente palavras-chave e termos de maior ênfase. Quando eu mencionar números ou listar informações, dê destaque visual a esses elementos.

Se precisar de imagens de referência para manter a identidade visual ou representar algo específico, solicite-as antes de prosseguir.
```

> **O que faz:** aplica o estilo da pasta indicada, gera cartões ilustrativos para números, listas e conceitos (no seu visual), coloca sons da skill nos momentos de destaque, usa fade entre as cenas e legenda completa com palavras-chave destacadas. Para algo que um cartão não representa, como um produto ou uma tela, ele pede a imagem antes. **Adapte:** troque "legendas completas" por "resuma a fala" para o modo resumo.

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
| `troca o resumo por legenda da fala` | muda o modo do texto |
| `texto sem caixa, em maiúsculas` | muda o estilo só deste vídeo |

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

## Estilo

O visual de sempre fica em `editar-reel/estilo-padrao.json` (já vem com verde, dourado e Montserrat). Troque pelos seus valores; as atualizações da skill mantêm esse arquivo.

```json
{
  "cor_texto": "#FFFFFF",
  "cor_destaque": "#DFAC16",
  "cor_caixa": "#03332CD9",
  "caixa": true,
  "fonte": "Montserrat",
  "tamanho": 68,
  "maiusculas": false
}
```

Para um vídeo com outro visual, use a pasta `estilo/` (exemplo 7). O que você pedir em texto vale mais que a pasta, e a pasta vale mais que o padrão.

A fonte pode ser o nome de uma fonte instalada no computador ou um arquivo `.ttf`/`.otf`. Montserrat é gratuita no Google Fonts.

## Atualizar

Rode o instalador de novo, ou peça no Claude Code:

```
Atualiza a skill editar-reel a partir de https://github.com/stefanisilva-ia/editar-reel-skill
```

O instalador troca os arquivos da skill e mantém as bibliotecas já baixadas e o seu `estilo-padrao.json`.

## Estrutura

| Arquivo | Função |
|---|---|
| `editar-reel/SKILL.md` | Passo a passo e regras que o Claude segue |
| `editar-reel/motor/cli.py` | Comandos: checar, transcrever, segmentar, estilo, sons, validar, renderizar, quadros |
| `editar-reel/motor/transcricao.py` | Transcrição local com o tempo de cada palavra |
| `editar-reel/motor/segmentos.py` | Divide a fala em trechos e cria o plano |
| `editar-reel/motor/plano.py` | Valida o plano e calcula a linha do tempo final |
| `editar-reel/motor/cartelas.py` | Desenha o texto na tela, os prints e os cartões |
| `editar-reel/motor/estilo.py` | Lê a pasta de referências de estilo |
| `editar-reel/motor/sons.py` | Cria os efeitos sonoros básicos |
| `editar-reel/estilo-padrao.json` | O seu visual de sempre |
| `editar-reel/motor/render.py` | Corta, enquadra, dá ritmo e exporta |
| `instalar.sh` e `instalar.ps1` | Instaladores |

## Licença

MIT. Pode usar, adaptar e compartilhar.
