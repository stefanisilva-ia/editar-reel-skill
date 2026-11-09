# Editar reel

Skill para o Claude Code que edita reel falado sem abrir editor de vídeo.

Você grava falando para a câmera, chama `/editar-reel` e recebe o vídeo pronto para postar. Uso no meu próprio conteúdo e deixo aberta para quem quiser usar também.

## O que ela faz

1. **Transcreve no seu computador.** Nada vai para a internet, sem custo por vídeo.
2. **Propõe os cortes.** Pausas, tomadas repetidas, vícios soltos e frases que começaram erradas, com sugestões automáticas. Você aprova antes de qualquer corte.
3. **Junta vários vídeos.** Rosto e gravação de tela numa edição só, na ordem que você indicar.
4. **Decide o visual de cada trecho.** Alterna três formatos conforme o que você fala: tela cheia com você, tela dividida (você embaixo, o exemplo em cima) e só gráficos com legenda. Antes de renderizar, mostra o mapa visual para você aprovar.
5. **Legenda da fala que acende palavra por palavra**, com as palavras-chave em Playfair Display Italic, palavra de alerta em vermelho e caixa na palavra principal.
6. **Coloca peças animadas na palavra exata em que são ditas:** prints com círculo, caixa, marca-texto e seta que se desenham, números que contam, listas e etapas que acendem, comparação antes e agora, palavra solta grande, manchete por seção e selo de série.
7. **Segue receitas de estilo.** Três prontas (escuro técnico, claro vidro, print anotado), que podem ser combinadas, e novas criadas a partir de um vídeo de referência.
8. **Exporta em 9:16** com o volume no padrão das redes (-14 LUFS) e escreve a legenda do post. 1080x1920, pronto para Instagram, TikTok e Shorts.

Depois é só pedir ajuste em texto: "corta a terceira frase", "abre pela frase do resultado", "troca a cor do destaque".

## Os três formatos

| Formato | O que aparece | Quando a skill usa |
|---|---|---|
| **A. Tela cheia** | você, com a legenda na altura do peito | opinião, alerta, fala direta, virada, chamada final |
| **B. Tela dividida** | fundo de cena com o exemplo em cima, você num painel embaixo | explicar como funciona, mostrar print, provar |
| **C. Só gráficos** | fundo de cena, a peça e a legenda grande, sem você | processo, lista, número, conceito |

A escolha segue o conteúdo, não uma sequência fixa. As regras estão em `editar-reel/direcao-visual.md`: abrir em tela dividida, fechar em tela cheia, no máximo 6 s seguidos sem o seu rosto e rosto em pelo menos metade do vídeo.

Os fundos alternam entre verdes, off-white, areia e bege, mais um vermelho para momentos de erro.

## Texto na tela: legenda ou resumo

- **Legenda da fala** (padrão): sincronizada palavra por palavra, só dos trechos que ficaram. Cada palavra acende quando é dita.
- **Resumo** (se você pedir): a fala vira blocos curtos, que quem assiste sem som entende em um segundo.

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
├── imagens/  painel.png   whatsapp.png
├── sons/     pop.wav   whoosh.mp3
└── estilo/   referencia.png   MinhaFonte-Bold.ttf   cores.md   (opcional)
```

> Numere os vídeos (01, 02...) e o Claude segue essa ordem sem perguntar. Prints e sons com nomes claros ficam fáceis de citar no pedido. A pasta `estilo/` só é necessária quando o vídeo foge do seu visual de sempre.

### 1. Edição simples

```
/editar-reel o vídeo está em ~/Downloads/gravacao.MOV.
É pro Instagram, palavra-chave AGENTE. Acelera 1.1.
```

> **O que faz:** transcreve, propõe os cortes, mostra o mapa visual, monta a legenda e a chamada "comenta AGENTE". **Adapte:** troque a palavra-chave e tire o "acelera" se quiser a fala no ritmo original.

### 2. Com prints de uma pasta

```
/editar-reel o vídeo está em ~/reel-painel/videos/01-abertura.mov.
Os prints estão em ~/reel-painel/imagens.
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

> **O que faz:** tudo de uma vez. O Claude ainda mostra os cortes e o mapa visual para você aprovar antes de renderizar. **Adapte:** numere os pedidos, um por linha. Fica mais fácil para você revisar e para o Claude seguir.

### 6. Ajustando a legenda

```
/editar-reel o vídeo está em ~/Downloads/tutorial.MOV.
Legenda com 3 palavras por vez.
Corrige "cloud code" para "Claude Code" e destaca "automação".
Palavra-chave GUIA.
```

> **O que faz:** gera a legenda sincronizada com o que você fala, já sem os trechos cortados, com "Claude Code" sempre junto e "automação" em Playfair dourada. **Adapte:** menos palavras por vez deixa mais dinâmico. Para trocar pela versão resumida, peça "resume a fala".

### 7. Com tela dividida e receita

```
/editar-reel pasta do projeto: ~/reel-skills
Usa a receita escuro-tecnico com os prints da print-anotado.
É o episódio 3 de 7 da série "Claude na prática".
Quando eu falar "botão", circula o botão no painel.png.
Palavra-chave SKILL.
```

> **O que faz:** depois dos cortes, mostra o mapa visual com o formato, o fundo e as peças de cada trecho. Com a sua aprovação, renderiza com o selo da série, a manchete de cada seção e o print com o círculo se desenhando na palavra "botão". **Adapte:** sem receita, a skill escolhe pelo assunto. Para mudar um trecho, diga "essa parte só gráfico" ou "fundo claro aqui".

### 8. Criando uma receita a partir de uma referência

```
/editar-reel cria uma receita dessa referência: ~/referencias/video-que-gostei.mp4
```

> **O que faz:** tira quadros do vídeo, analisa composição, legenda, cores, peças e ritmo e escreve uma receita nova na sua paleta. O vídeo de referência não entra na skill, só a receita. **Adapte:** guarde as referências numa pasta `referencias/` no seu computador.

### 9. Com referência de estilo

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

### 10. Deixando o Claude decidir

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
| `essa parte em tela dividida` | troca o formato do trecho |
| `só gráfico quando eu falar das etapas` | troca o formato e coloca o fluxo |
| `fundo areia nessa parte` | troca o fundo do trecho |
| `circula o botão no print` | acrescenta a marcação |
| `troca o texto "pronto em 1 dia" por "pronto em 24h"` | só o texto na tela |
| `tira o print do WhatsApp` | remove a imagem |
| `som mais baixo` | reduz o volume dos efeitos |
| `sem zoom nos cortes` | desliga a alternância de plano |
| `muda o destaque para #dfac16` | troca a cor dos números e palavras-chave |
| `refaz a legenda do post, mais curta` | reescreve o `legenda.txt` |
| `resume a fala em vez de legendar` | muda o modo do texto |
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
- Grave na vertical, com o rosto no terço de cima do quadro. Na tela dividida, o painel mostra rosto e ombros.

## Estilo

O visual de sempre fica em `editar-reel/estilo-padrao.json` (já vem com verde, dourado, Montserrat, Playfair Display e DM Sans). Troque pelos seus valores; as atualizações da skill mantêm esse arquivo.

```json
{
  "cor_texto": "#FFFFFF",
  "cor_destaque": "#DFAC16",
  "cor_texto_claro": "#111111",
  "cor_destaque_claro": "#07544A",
  "cor_alerta": "#C9473A",
  "cor_apoio": "#289A8B",
  "fonte": "Montserrat",
  "fonte_destaque": "Playfair Display",
  "fonte_rotulo": "DM Sans"
}
```

As receitas em `editar-reel/estilos/` definem fundos, cartões, prints e manchete. Para um vídeo com outro visual, use a pasta `estilo/` (exemplo 9). O que você pedir em texto vale mais que a pasta, a pasta vale mais que a receita, e a receita vale mais que o padrão.

As fontes vêm com a skill, na pasta `editar-reel/fontes/` (Montserrat, Playfair Display e DM Sans, todas com licença OFL). Você também pode usar o nome de uma fonte instalada ou um arquivo `.ttf`/`.otf`.

## Atualizar

Rode o instalador de novo, ou peça no Claude Code:

```
Atualiza a skill editar-reel a partir de https://github.com/stefanisilva-ia/editar-reel-skill
```

O instalador troca os arquivos da skill e mantém as bibliotecas já baixadas, o seu `estilo-padrao.json` e as receitas que você criou.

## Estrutura

| Arquivo | Função |
|---|---|
| `editar-reel/SKILL.md` | Passo a passo e regras que o Claude segue |
| `editar-reel/direcao-visual.md` | Quando usar cada formato, ritmo, legenda, cores, peças e sons |
| `editar-reel/estilos/` | Receitas de estilo (`.json` para o motor, `.md` com a descrição) |
| `editar-reel/fontes/` | Montserrat, Playfair Display e DM Sans, com as licenças |
| `editar-reel/estilo-padrao.json` | O seu visual de sempre |
| `editar-reel/motor/cli.py` | Comandos: checar, transcrever, segmentar, estilo, sons, receitas, referencia, mapa, validar, cartelas, renderizar, quadros |
| `editar-reel/motor/transcricao.py` | Transcrição local com o tempo de cada palavra |
| `editar-reel/motor/segmentos.py` | Divide a fala em trechos e cria o plano |
| `editar-reel/motor/plano.py` | Valida o plano, calcula a linha do tempo, o ritmo e o mapa visual |
| `editar-reel/motor/visual.py` | Formatos, fundos de cena, cores por fundo e receitas |
| `editar-reel/motor/cartelas.py` | Legenda, manchete, chamada, selo, palavra solta e cartões |
| `editar-reel/motor/prints.py` | Prints com moldura, pílula e marcações |
| `editar-reel/motor/referencia.py` | Folhas de quadros de um vídeo de referência |
| `editar-reel/motor/estilo.py` | Lê a pasta de referências de estilo |
| `editar-reel/motor/sons.py` | Cria os efeitos sonoros básicos |
| `editar-reel/motor/render.py` | Monta cada formato, junta, anima as peças e exporta |
| `instalar.sh` e `instalar.ps1` | Instaladores |

## Licença

MIT. Pode usar, adaptar e compartilhar. As fontes da pasta `editar-reel/fontes/` seguem a licença OFL de cada uma, que acompanha os arquivos.
