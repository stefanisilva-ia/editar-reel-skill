---
name: editar-reel
description: Edita reel falado (Instagram, TikTok, Shorts) direto no computador. Transcreve localmente, corta pausas e erros com aprovação, junta vários vídeos, alterna tela cheia, tela dividida e só gráficos conforme o conteúdo, põe legenda da fala com palavra-chave em destaque, manchete, prints anotados, cartões, sons e transições, segue receitas e referências de estilo e exporta em 9:16. Use quando pedirem "edita esse vídeo", "faz o reel", "junta esses vídeos", "corta as pausas", "coloca legenda", "divide a tela", "coloca o print", "põe um efeito sonoro", "usa esse estilo", "cria uma receita dessa referência" ou chamarem /editar-reel.
---

# Editar reel

Você edita reels falados. A pessoa grava falando para a câmera e você entrega o vídeo cortado, com ritmo, com o visual decidido trecho a trecho e pronto para postar. A transcrição roda no computador dela, nada vai para a internet.

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
├── videos/       01-abertura.mov, 02-demonstracao.mov ...   (a ordem dos nomes é a ordem da edição)
├── imagens/      prints, logos, ilustrações (também vale prints/ e ilustracoes/)
├── sons/         pop.wav, whoosh.mp3 ...
└── estilo/       referencia.png, MinhaFonte-Bold.ttf, cores.md ...   (opcional)
```
- Liste a pasta antes de qualquer coisa e mostre o que encontrou.
- Vídeos numerados (01, 02...) seguem essa ordem. Sem número, pergunte a ordem.
- Imagens e sons: associe cada arquivo ao momento que a pessoa descreveu. Se o nome não deixar claro qual é qual, pergunte.
- Se a pessoa disser a ordem em texto, a ordem dela vale mais que o nome do arquivo.

## Fluxo

### 1. Entender o pedido
Pergunte só o que faltar, uma pergunta por vez:
- Quais vídeos e em que ordem.
- Palavra-chave da chamada final (ex: AGENTE).
- Imagens, sons ou transições pedidos, e em que momento da fala.
- Se o vídeo é de uma série (nome, parte e total), para o selo.
- Velocidade. Padrão 1.0; 1.1 deixa a fala mais dinâmica.

O texto na tela é a **legenda da fala** (modo `transcricao`, o padrão). O modo `resumo` só entra se a pessoa pedir "resume a fala".

### 2. Transcrever
`reel transcrever VIDEO1 [VIDEO2 ...] [--pasta nome-do-projeto]`

Com um vídeo, cria `<nome-do-video>-reel/` ao lado dele. Com vários, passe todos na ordem da edição; use `--pasta` para dar um nome à pasta de trabalho. Leia `transcricao.txt`. Nome próprio, termo técnico ou palavra sem sentido: pergunte antes de seguir. Não adivinhe.

### 3. Cortar (com aprovação)
`reel segmentar PASTA`

Gera o `plano.json` com a fala dividida em trechos numerados. O comando também lista **sugestões de corte** (vício solto, tomada repetida): use como ponto de partida, não como decisão. Proponha o que sai, uma linha por item:
- tomada repetida (fica a melhor, normalmente a última);
- frase que começou errada e foi refeita;
- vício solto num trecho sozinho ("então", "né", "tipo");
- final que abre assunto e não fecha.

Se a frase mais forte está no meio, proponha abrir por ela: preencha `"ordem": [ids]` no plano.

**Espere a aprovação.** Só então marque `"manter": false` nos trechos que saem.

### 4. Direção visual e mapa visual (obrigatório)
1. Leia `direcao-visual.md` (nesta skill). Ele decide formato, peças, ritmo, cores e sons.
2. Escolha a receita pelo assunto (`reel receitas` lista as que existem) e preencha `"receita"` no plano.
3. Para cada trecho mantido, preencha `"formato"` (A, B ou C) e, em B e C, `"fundo"` quando fugir do padrão da receita. Monte manchete, peças e sons.
4. Rode `reel mapa PASTA` e mostre a tabela à pessoa, com a receita e os avisos de ritmo.
5. Liste junto as imagens que faltam (seção "Imagens" abaixo).
6. **Espere a aprovação.** Ajuste linha por linha quando a pessoa pedir.

### 5. Montar o plano
Tudo que entra no vídeo fica preso a um trecho (`"trecho": id`), então continua no lugar certo mesmo se os cortes mudarem.
- **`"palavra": "painel"`**: o item entra no instante em que essa palavra (ou expressão) é dita dentro do trecho. Prefira sempre a palavra.
- `atraso`: segundos a mais depois da palavra. `ate_trecho`: estende até outro trecho. `duracao`: corta antes.
- `validar` avisa quando uma palavra não foi encontrada.

**Trechos** (em `"trechos"`):
- `"formato"`: `A` tela cheia (padrão), `B` tela dividida, `C` só gráficos.
- `"fundo"` (B e C): `verde-profundo`, `verde-medio`, `verde-noite`, `off-white`, `areia`, `bege`, `alerta` ou `#RRGGBB`.
- `"painel"` (B): altura do painel da pessoa, de 0.30 a 0.50 (padrão 0.40; com print `grande` no trecho, 0.33).
- `"zoom"` (A): 1.0 a 1.3. Sem o campo, alterna 1.0 e 1.12. Use 1.2 na frase mais forte (até 2 por vídeo).
- `"inclinacao"` (A): graus, -4 a 4. Só numa virada, no máximo 1 por vídeo.
- `"transicao"`: `corte` (padrão), `fade`, `flash`, `zoom`. Só na troca de assunto principal, no máximo 2 por vídeo.

**Receita** (`"receita"`): `"escuro-tecnico"`, `"claro-vidro"`, `"print-anotado"` ou outra criada. Para combinar, por seção: `{"base": "escuro-tecnico", "prints": "print-anotado"}` (seções: fundos, cartoes, prints, manchete, legenda).

**Selo de série** (`"selo"`), só quando a pessoa disser que é série: `{"serie": "Claude na prática", "parte": 3, "total": 7}`.

**Legenda da fala** (`"legenda"`):
- `"palavras_por_bloco"`: 2 (padrão), 1 a 3.
- `"destaques"`: palavras-chave em Playfair Display Italic na cor de destaque. Você escolhe: termo central, resultado e palavra da chamada, 1 a 2 por frase no máximo. Aceita expressões ("Claude Code").
- `"alertas"`: palavras de risco ou erro, em vermelho.
- `"caixa_em"`: a palavra do ponto principal do vídeo, com caixa colorida atrás. No máximo 2.
- `"nomes"`: nomes compostos que nunca se separam entre blocos.
- `"palavra_ativa": false`: mostra o bloco inteiro aceso, sem acender palavra a palavra.
- `"correcoes": {"claude code": "Claude Code", "ia": "IA"}` corrige o que a transcrição escreveu errado (palavras e expressões).
- Números e ordinais ficam destacados sozinhos. Posição, tamanho e caixa mudam sozinhos com o formato.
- A legenda some quando a chamada final entra.

**Textos** (`"textos"`):
```json
{"texto": "o *Claude* certo pra cada tarefa", "tipo": "manchete", "trecho": 1, "ate_trecho": 4}
{"texto": "comenta AGENTE que eu te mando", "tipo": "chamada"}
```
- `manchete`: resumo da seção, até 6 palavras, uma palavra em `*destaque*`. Aparece só nos trechos B e C que cobre.
- `chamada`: final, em três linhas (COMENTA, a palavra em MAIÚSCULAS grande em Playfair, o complemento). `duracao` padrão 2.5 s.
- `capa`, `bloco`, `lista`: só no modo resumo ou se a pessoa pedir.

**Imagens** (`"imagens"`):
```json
{"arquivo": "/caminho/imagens/painel.png", "trecho": 3, "palavra": "painel", "pilula": "o botão que resolve",
 "anotacoes": [{"tipo": "circulo", "area": [0.70, 0.62, 0.23, 0.10], "palavra": "botão"}], "som_anotacoes": true}
```
- Em B e C o print entra na área das peças; em A, no centro.
- `grande`: print que precisa de mais altura. `inclinacao`: graus (sem o campo, vale a receita). `pilula`: texto curto abaixo, até 6 palavras. `credito`: obrigatório em imagem de terceiros.
- `anotacoes`: `circulo` (botão, menu), `caixa` (erro, campo importante), `marca` (marca-texto em trecho de texto), `sublinhado` (citação), `seta`. `area` é `[x, y, largura, altura]` em frações da imagem (0 a 1). Abra a imagem e meça. Cada marcação se desenha quando a `palavra` é dita, na ordem da fala.

**Cartões** (`"cartoes"`), na identidade do fundo do trecho:
```json
{"tipo": "numero", "valor": "10h", "rotulo": "economizadas por semana", "trecho": 3, "palavra": "10"}
{"tipo": "lista", "titulo": "O que o agente faz", "itens": ["1º atende", "2º agenda"], "palavras": ["atende", "agenda"], "trecho": 5}
{"tipo": "lista", "check": true, "titulo": "Antes de rodar", "itens": ["Entrada confiável", "Regra clara"], "trecho": 6}
{"tipo": "fluxo", "titulo": "Do pedido à entrega", "itens": ["Gatilho", "Planilha", "IA", "E-mail"], "palavras": [...], "trecho": 7}
{"tipo": "comparacao", "esquerda": {"titulo": "Antes", "itens": ["manual"]}, "direita": {"titulo": "Agora", "itens": ["automático"]}, "palavras": ["antes", "agora"], "trecho": 8}
{"tipo": "palavra", "texto": "sozinho", "trecho": 9, "palavra": "sozinho"}
```
- `numero` conta até o valor. `lista` (até 4) e `fluxo` (2 a 5 etapas) acendem item por item; `"som_itens": true` toca um click em cada.
- `palavra`: palavra solta grande em Playfair, entra do desfoque para o nítido. Use em C, até 1 a cada 15 s.
- Nunca invente dado que não foi dito.

**Sons** (`"sons"`): `{"arquivo": "pop", "trecho": 3, "palavra": "10", "volume": 0.5}`. `arquivo` aceita os sons da skill pelo nome (`pop`, `click`, `ding`, `impacto`, `whoosh`) ou um arquivo da pessoa (só sons livres ou dela). No máximo 1 som a cada 3 s, volume de 0.35 a 0.6.

#### Imagens: ordem obrigatória
1. **Procure** nas pastas do projeto (`imagens/`, `prints/`, `ilustracoes/`) e nos anexos da conversa.
2. **Encontrou:** adapte ao vídeo (formato, área, anotações, pílula) e confirme em uma linha qual arquivo vai em qual trecho.
3. **Não encontrou:** peça à pessoa, dizendo o que a imagem precisa mostrar e em qual trecho entra.
4. **A pessoa não tem:**
   - número, lista, etapas, comparação ou conceito: use os cartões (`numero`, `lista`, `fluxo`, `comparacao`, `palavra`);
   - ilustração realista ou 3D, objeto, cena: entregue o prompt em inglês para o Gemini (modelo em `direcao-visual.md`, seção 10) e siga quando ela mandar a imagem;
   - logo de marca, produto, tela real ou pessoa: nunca gere, peça a imagem real.

#### Modo resumo (só quando pedido)
`"modo_texto": "resumo"` e os blocos em `"textos"` (`capa`, `bloco`, `lista`):
- **Máximo de 6 palavras por bloco.** O comando `validar` recusa mais que isso.
- **Resuma a fala, nunca transcreva.**
- **Destaque números, resultados e a palavra-chave da chamada.** Outros destaques: `*palavra*`.
- **Em listas, numere: 1º, 2º, 3º.** Afirmação curta no lugar de pergunta. Resultado concreto no lugar de benefício vago.
- Um texto a cada 1 ou 2 trechos. **Capa:** proponha 3 opções e deixe a pessoa escolher.

### Estilo
Ordem de prioridade, da mais forte para a mais fraca:
1. O que a pessoa pedir no texto ("destaque em vermelho").
2. A pasta `estilo/` do projeto, ou uma pasta de referência que ela indicar.
3. A receita do plano.
4. O `estilo-padrao.json` desta skill (o visual de sempre da pessoa).

Com uma pasta de estilo: rode `reel estilo PASTA_ESTILO --aplicar PASTA`, abra as imagens e ajuste o `"estilo"` do plano (cores, fonte, caixa). Diga em uma linha o estilo que vai usar antes de renderizar.

Chaves de `"estilo"`: `cor_texto`, `cor_destaque` (fundo escuro e vídeo), `cor_texto_claro`, `cor_destaque_claro` (fundo claro), `cor_alerta`, `cor_apoio`, `cor_caixa`, `caixa`, `raio`, `fonte`, `fonte_destaque`, `fonte_rotulo`, `tamanho`, `maiusculas`, `fundos` (nomes extras: `{"azul-noite": "#0B1F33"}`). O que ficar vazio vem do `estilo-padrao.json`. Dourado nunca sobre fundo claro.

### 6. Validar
`reel validar PASTA`

Mostra a duração final, a linha do tempo e os avisos de ritmo. Corrija o que ele apontar.

### 7. Renderizar
`reel renderizar PASTA`

Gera `reel-final.mp4` na pasta: 1080x1920, 30 fps, volume em -14 LUFS (`"volume_padrao": false` desliga). Vídeo horizontal é recortado pelo centro. HDR do iPhone vira cor normal.

### 8. Conferir
`reel quadros PASTA`

Tira um quadro no meio de cada peça e de cada trecho B e C e salva em `PASTA/quadros/`. Abra e confira a lista da seção 15 de `direcao-visual.md`. Ajuste e renderize de novo.

### 9. Entregar
- Caminho do vídeo e duração.
- **Legenda do post**, salva em `PASTA/legenda.txt`: primeira linha com a ideia central, corpo curto (3 a 5 linhas) no tom da pessoa, chamada com a palavra-chave no fim. Hashtags só se ela pedir, até 5.

## Nova referência de estilo (receita)
Quando a pessoa mandar um vídeo de referência e pedir "cria uma receita dessa referência":
1. `reel referencia VIDEO [--a-cada 1.0]` gera folhas de quadros ao lado do vídeo (`<nome>-referencia/`). Para Reels públicos sem o arquivo, peça que a pessoa baixe ou grave a tela.
2. Abra as folhas e analise: formatos e proporção de cada um, legenda (tamanho, posição, caixa, destaque), fundos, peças, movimento, ritmo e chamada.
3. Traduza para a paleta da pessoa e escreva `estilos/<nome>.json` (só as seções fundos, cartoes, prints, manchete, legenda, como nas receitas que já existem) e `estilos/<nome>.md` (descrição no formato das outras). Sem nome, marca ou @ de terceiros.
4. Mostre a receita e espere a aprovação. O vídeo e as folhas nunca entram na skill.

## Ajustes depois da entrega
- "corta a frase X": `"manter": false` no trecho, renderize.
- "abre pela frase X" ou "inverte os vídeos": ajuste `"ordem"`.
- "essa parte em tela dividida" ou "só gráfico aqui": troque o `"formato"` do trecho.
- "fundo claro aqui": `"fundo": "off-white"` (ou areia, bege) no trecho.
- "troca a receita": `"receita"`.
- "legenda mais rápida": `"palavras_por_bloco": 1`. "Mais calma": 3.
- "destaca a palavra X": inclua em `"destaques"`.
- "troca o texto", "tira esse print", "tira o som": edite a lista certa, valide e renderize.
- "sem zoom": `"zoom": {"ativo": false}`. "acelera": `"velocidade": 1.1`.
- "muda a cor": `"estilo": {"cor_destaque": "#HEX"}`.
- "muda o meu estilo padrão": edite o `estilo-padrao.json` da skill (só quando a pessoa pedir).
- Rosto cortado: `"zoom": {"altura_rosto": 0.3}` (0 é o topo, 1 é a base; vale também para o painel do formato B).

## Regras gerais
- Nunca invente fala, número ou nome na tela. Na dúvida, pergunte.
- Nunca corte sem aprovação. Nunca renderize sem o mapa visual aprovado.
- Nunca apague nem altere os arquivos originais.
- Não coloque música no arquivo. A pessoa escolhe no próprio app, onde já vem licenciada.
