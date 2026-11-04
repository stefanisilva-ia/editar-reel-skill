---
name: editar-reel
description: Edita reel falado (Instagram, TikTok, Shorts) direto no computador. Transcreve localmente, corta pausas e erros com aprovação, alterna plano aberto e fechado, coloca texto na tela resumindo a fala e exporta em 9:16. Use quando pedirem "edita esse vídeo", "faz o reel", "corta as pausas", "coloca texto na tela" ou chamarem /editar-reel.
---

# Editar reel

Você edita reels falados. A pessoa grava falando para a câmera e você entrega o vídeo cortado, com ritmo, com texto na tela e pronto para postar. A transcrição roda no computador dela, nada vai para a internet.

## Como rodar os comandos

Todos os comandos usam o Python da pasta `.venv` que o instalador cria dentro desta skill:
- Mac e Linux: `<pasta da skill>/.venv/bin/python <pasta da skill>/motor/cli.py COMANDO`
- Windows: `<pasta da skill>\.venv\Scripts\python.exe <pasta da skill>\motor\cli.py COMANDO`

Abaixo, `reel` significa essa linha inteira. Caminhos com espaço vão entre aspas.

Na primeira vez, rode `reel checar`. Se faltar algo, rode o instalador do repositório ou siga o que o comando indicar.

## Fluxo

### 1. Entender o pedido
Pergunte só o que faltar, uma pergunta por vez:
- Caminho do vídeo.
- Palavra-chave da chamada final (ex: AGENTE). Se não tiver, a chamada pode ser outra ação curta.
- Velocidade. Padrão 1.0; 1.1 deixa a fala mais dinâmica.

### 2. Transcrever
`reel transcrever VIDEO`

Cria a pasta `<nome-do-video>-reel/` ao lado do vídeo, com `transcricao.txt`. Leia o texto. Nome próprio, termo técnico ou palavra sem sentido na frase: pergunte antes de seguir. Não adivinhe.

### 3. Cortar (com aprovação)
`reel segmentar PASTA`

Gera o `plano.json` com a fala dividida em trechos numerados. Proponha o que sai, uma linha por item:
- tomada repetida (fica a melhor, normalmente a última);
- frase que começou errada e foi refeita;
- vício solto num trecho sozinho ("então", "né", "tipo");
- final que abre assunto e não fecha.

Se a frase mais forte está no meio, proponha abrir por ela: preencha `"ordem": [ids]` no plano.

**Espere a aprovação.** Só então marque `"manter": false` nos trechos que saem.

### 4. Escrever o texto na tela
Preencha `"textos"` no `plano.json`. Cada texto fica preso a um trecho, então continua no lugar certo mesmo se os cortes mudarem.

```json
{"texto": "pronto em 10 minutos", "tipo": "bloco", "trecho": 4}
```

Campos:
- `texto`: o que aparece.
- `tipo`: `capa` (abertura, grande, sem caixa), `bloco` (padrão), `lista` (item numerado), `chamada` (final, entra nos últimos segundos, não precisa de `trecho`).
- `trecho`: id do trecho em que o texto aparece. `ate_trecho` estende até outro trecho.
- `posicao`: `alto`, `centro` ou `baixo`. Cada tipo já tem um padrão bom, só mude se cobrir o rosto.
- `atraso`: segundos depois do início do trecho para o texto entrar (ex: entrar quando a palavra for dita).
- `duracao`: só na chamada, padrão 2.5 s.

Destaque na cor da marca: números, ordinais (1º) e, na chamada, palavras em MAIÚSCULAS ficam destacados sozinhos. Para destacar outra palavra, use asteriscos: `"agenda confirmada *sozinha*"`.

#### Regras do texto na tela (obrigatórias)
- **Máximo de 6 palavras por bloco.** O comando `validar` recusa mais que isso.
- **Resuma a fala, nunca transcreva.** O texto é a ideia em poucas palavras, não legenda.
- **Destaque números, resultados e a palavra-chave da chamada.**
- **Em listas, numere: 1º, 2º, 3º.**
- **Prefira afirmação curta a pergunta.**
- **Troque benefício vago por resultado concreto.**
- Sem gírias, sem exageros, sem travessão.

Exemplos:

| A fala | Texto na tela |
|---|---|
| "Isso me economizou muito tempo, ficou pronto em uns dez minutos" | `pronto em 10 minutos` |
| "A segunda coisa é que o atendimento funciona vinte e quatro horas" | `2º ATENDIMENTO 24H` (tipo lista) |
| "O cliente não precisa mais ficar ligando pra confirmar" | `agenda confirmada *sozinha*` |
| "Comenta aí embaixo a palavra agente" | `comenta AGENTE` (tipo chamada) |

Um texto a cada 1 ou 2 trechos é o ritmo certo. Não precisa ter texto em todo trecho.

**Capa:** proponha 3 opções de capa (a ideia central do vídeo em até 6 palavras) e deixe a pessoa escolher. Nunca escolha sozinho.

### 5. Validar
`reel validar PASTA`

Mostra a duração final e quando cada texto entra e sai. Corrija o que ele apontar.

### 6. Renderizar
`reel renderizar PASTA`

Gera `reel-final.mp4` na pasta: 1080x1920, 30 fps, pronto para postar. Vídeo horizontal é recortado pelo centro. Vídeo HDR do iPhone é convertido para cor normal.

### 7. Conferir
`reel quadros PASTA`

Tira um quadro no meio de cada texto e salva em `PASTA/quadros/`. Abra e olhe: o texto cobre o rosto? Está legível? Se cobrir, mude a `posicao` daquele texto e renderize de novo.

### 8. Entregar
Diga o caminho do vídeo, a duração e sugira a legenda do post: primeira linha com a ideia da capa, corpo curto, chamada com a palavra-chave no fim.

## Ajustes depois da entrega
- "corta a frase X": `"manter": false` no trecho, renderize.
- "abre pela frase X": ajuste `"ordem"`, renderize.
- "troca o texto", "tira esse texto": edite `"textos"`, valide e renderize.
- "sem zoom": `"zoom": {"ativo": false}`.
- "acelera": `"velocidade": 1.1`.
- "muda a cor": `"estilo": {"cor_destaque": "#HEX"}`. Também dá para trocar `cor_texto`, `cor_caixa` (com transparência no fim, ex: `#000000B8`), `tamanho`, `maiusculas` e `fonte` (caminho de um arquivo .ttf ou .otf).
- Rosto cortado no plano fechado: ajuste `"zoom": {"altura_rosto": 0.3}` (0 é o topo, 1 é a base).

## Regras gerais
- Nunca invente fala, número ou nome no texto na tela. Na dúvida, pergunte.
- Nunca corte sem aprovação. Nunca escolha a capa sozinho.
- Nunca apague nem altere o vídeo original.
- Não coloque música no arquivo. A pessoa escolhe no próprio app, onde já vem licenciada.
