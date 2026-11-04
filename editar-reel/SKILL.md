---
name: editar-reel
description: Edita reel falado (Instagram, TikTok, Shorts) direto no computador. Transcreve localmente, corta pausas e erros com aprovação, junta vários vídeos, alterna planos, aplica transições, coloca texto na tela, prints e efeitos sonoros e exporta em 9:16. Use quando pedirem "edita esse vídeo", "faz o reel", "junta esses vídeos", "corta as pausas", "coloca o print", "põe um efeito sonoro" ou chamarem /editar-reel.
---

# Editar reel

Você edita reels falados. A pessoa grava falando para a câmera e você entrega o vídeo cortado, com ritmo, com texto na tela e pronto para postar. A transcrição roda no computador dela, nada vai para a internet.

## Como rodar os comandos

Todos os comandos usam o Python da pasta `.venv` que o instalador cria dentro desta skill:
- Mac e Linux: `<pasta da skill>/.venv/bin/python <pasta da skill>/motor/cli.py COMANDO`
- Windows: `<pasta da skill>\.venv\Scripts\python.exe <pasta da skill>\motor\cli.py COMANDO`

Abaixo, `reel` significa essa linha inteira. Caminhos com espaço vão entre aspas.

Na primeira vez, rode `reel checar`. Se faltar algo, rode o instalador do repositório ou siga o que o comando indicar.

## Organização de arquivos que a pessoa pode usar

Quando a pessoa indicar uma pasta, procure nela:
```
meu-reel/
├── videos/   01-abertura.mov, 02-demonstracao.mov ...   (a ordem dos nomes é a ordem da edição)
├── prints/   painel.png, whatsapp.png ...
└── sons/     pop.wav, whoosh.mp3 ...
```
- Liste a pasta antes de qualquer coisa e mostre o que encontrou.
- Vídeos numerados (01, 02...) seguem essa ordem. Sem número, pergunte a ordem.
- Prints e sons: associe cada arquivo ao momento que a pessoa descreveu. Se o nome não deixar claro qual é qual, pergunte.
- Se a pessoa disser a ordem em texto ("primeiro o vídeo da tela, depois o meu rosto"), a ordem dela vale mais que o nome do arquivo.

## Fluxo

### 1. Entender o pedido
Pergunte só o que faltar, uma pergunta por vez:
- Quais vídeos e em que ordem.
- Palavra-chave da chamada final (ex: AGENTE). Se não tiver, a chamada pode ser outra ação curta.
- Prints, sons ou transições pedidos, e em que momento da fala.
- Velocidade. Padrão 1.0; 1.1 deixa a fala mais dinâmica.

### 2. Transcrever
`reel transcrever VIDEO1 [VIDEO2 ...] [--pasta nome-do-projeto]`

Com um vídeo, cria `<nome-do-video>-reel/` ao lado dele. Com vários, passe todos na ordem da edição; use `--pasta` para dar um nome à pasta de trabalho. Leia `transcricao.txt`. Nome próprio, termo técnico ou palavra sem sentido: pergunte antes de seguir. Não adivinhe.

### 3. Cortar (com aprovação)
`reel segmentar PASTA`

Gera o `plano.json` com a fala dividida em trechos numerados (com vários vídeos, cada trecho mostra de qual veio). Proponha o que sai, uma linha por item:
- tomada repetida (fica a melhor, normalmente a última);
- frase que começou errada e foi refeita;
- vício solto num trecho sozinho ("então", "né", "tipo");
- final que abre assunto e não fecha.

Se a frase mais forte está no meio, proponha abrir por ela: preencha `"ordem": [ids]` no plano. `ordem` também troca a sequência entre vídeos.

**Espere a aprovação.** Só então marque `"manter": false` nos trechos que saem.

### 4. Montar o plano
Tudo que entra no vídeo fica preso a um trecho (`"trecho": id`), então continua no lugar certo mesmo se os cortes mudarem. `atraso` (segundos depois do início do trecho) acerta o momento exato, por exemplo quando a palavra é dita: confira o tempo da palavra no `transcricao.json`.

**Texto na tela** (`"textos"`):
```json
{"texto": "pronto em 10 minutos", "tipo": "bloco", "trecho": 4}
```
- `tipo`: `capa` (abertura, grande), `bloco` (padrão), `lista` (item numerado), `chamada` (final, entra nos últimos segundos, sem `trecho`).
- `posicao`: `alto`, `centro` ou `baixo`. Só mude se cobrir o rosto ou um print.
- `ate_trecho`: estende até outro trecho. `duracao`: corta antes (na chamada, padrão 2.5 s).
- Destaque automático: números, ordinais (1º) e, na chamada, palavras em MAIÚSCULAS. Outros destaques: `*palavra*`.

**Prints** (`"imagens"`):
```json
{"arquivo": "/caminho/prints/painel.png", "trecho": 3, "atraso": 0.5, "credito": "fonte: site.com"}
```
- Entra flutuando, com cantos arredondados e sombra. `largura` (padrão 860), `posicao` (padrão `centro`), `ate_trecho`, `duracao`.
- Print com texto na tela no mesmo momento: ponha o texto em `alto` ou `baixo` para não sobrepor.
- Imagem de terceiros só com confirmação da pessoa, e sempre com `credito`.

**Efeitos sonoros** (`"sons"`):
```json
{"arquivo": "/caminho/sons/pop.wav", "trecho": 3, "atraso": 0.5, "volume": 0.7}
```
- Toca por cima da fala, sem mudar de velocidade. `volume` de 0 a 1 (padrão 0.8).
- A skill não traz sons: use os arquivos que a pessoa indicar. Só sons livres ou dela.

**Transições** (no próprio trecho): `"transicao": "fade" | "flash" | "zoom" | "corte"` define como o trecho entra.
- `corte`: padrão, direto. `fade`: escurece e abre. `flash`: clarão branco rápido. `zoom`: aproximação rápida.
- Use pouco: uma transição na troca de vídeo ou de assunto. Em todo trecho, cansa.

#### Regras do texto na tela (obrigatórias)
- **Máximo de 6 palavras por bloco.** O comando `validar` recusa mais que isso.
- **Resuma a fala, nunca transcreva.** O texto é a ideia em poucas palavras, não legenda.
- **Destaque números, resultados e a palavra-chave da chamada.**
- **Em listas, numere: 1º, 2º, 3º.**
- **Prefira afirmação curta a pergunta.**
- **Troque benefício vago por resultado concreto.**
- Sem gírias, sem exageros, sem travessão.

| A fala | Texto na tela |
|---|---|
| "Isso me economizou muito tempo, ficou pronto em uns dez minutos" | `pronto em 10 minutos` |
| "A segunda coisa é que o atendimento funciona vinte e quatro horas" | `2º ATENDIMENTO 24H` (tipo lista) |
| "O cliente não precisa mais ficar ligando pra confirmar" | `agenda confirmada *sozinha*` |
| "Comenta aí embaixo a palavra agente" | `comenta AGENTE` (tipo chamada) |

Um texto a cada 1 ou 2 trechos é o ritmo certo.

**Capa:** proponha 3 opções (a ideia central em até 6 palavras) e deixe a pessoa escolher. Nunca escolha sozinho.

### 5. Validar
`reel validar PASTA`

Mostra a duração final e a linha do tempo de textos, prints e sons. Corrija o que ele apontar.

### 6. Renderizar
`reel renderizar PASTA`

Gera `reel-final.mp4` na pasta: 1080x1920, 30 fps. Vídeo horizontal é recortado pelo centro. Vídeo HDR do iPhone é convertido para cor normal. Vídeos de tamanhos ou taxas diferentes são padronizados.

### 7. Conferir
`reel quadros PASTA`

Tira um quadro no meio de cada texto e print e salva em `PASTA/quadros/`. Abra e olhe: algo cobre o rosto? O texto está legível? O print está nítido? Ajuste e renderize de novo.

### 8. Entregar
- Caminho do vídeo e duração.
- **Legenda do post**, salva em `PASTA/legenda.txt`: primeira linha com a ideia da capa, corpo curto (3 a 5 linhas) no tom da pessoa, chamada com a palavra-chave no fim. Se ela pedir hashtags, até 5, no fim.

## Ajustes depois da entrega
- "corta a frase X": `"manter": false` no trecho, renderize.
- "abre pela frase X" ou "inverte os vídeos": ajuste `"ordem"`, renderize.
- "troca o texto", "tira esse print", "tira o som": edite a lista certa, valide e renderize.
- "põe uma transição entre os vídeos": `"transicao"` no primeiro trecho do segundo vídeo.
- "sem zoom": `"zoom": {"ativo": false}`.
- "acelera": `"velocidade": 1.1`.
- "muda a cor": `"estilo": {"cor_destaque": "#HEX"}`. Também dá para trocar `cor_texto`, `cor_caixa` (com transparência no fim, ex: `#000000B8`), `tamanho`, `maiusculas` e `fonte` (caminho de um .ttf ou .otf).
- Rosto cortado no plano fechado: `"zoom": {"altura_rosto": 0.3}` (0 é o topo, 1 é a base).

## Regras gerais
- Nunca invente fala, número ou nome no texto na tela. Na dúvida, pergunte.
- Nunca corte sem aprovação. Nunca escolha a capa sozinho.
- Nunca apague nem altere os arquivos originais.
- Não coloque música no arquivo. A pessoa escolhe no próprio app, onde já vem licenciada.
