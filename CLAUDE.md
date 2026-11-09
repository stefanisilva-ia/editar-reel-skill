# CLAUDE.md · editar-reel

Manual de manutenção da skill. Leia antes de qualquer mudança.

## O que é
Skill do Claude Code que edita reel falado (9:16) a partir da gravação bruta. Autora: Stefani Silva (@stefanisilva.ia, GitHub stefanisilva-ia). Licença MIT só no nome dela. Skill irmã de motion graphics: `stefanisilva-ia/motion-reel-stefani`.

## Mapa
```
editar-reel/SKILL.md           o que o Claude segue ao usar a skill (fonte da verdade do comportamento)
editar-reel/direcao-visual.md  regras de decisão visual: formatos, ritmo, legenda, cores, peças, sons (lido no mapa visual)
editar-reel/estilos/           receitas: <nome>.json (o motor lê) + <nome>.md (descrição); o instalador preserva as do usuário
editar-reel/fontes/            Montserrat, Playfair Display Italic e DM Sans variáveis + licenças OFL
editar-reel/estilo-padrao.json identidade padrão da autora (o instalador preserva o do usuário)
editar-reel/motor/cli.py       comandos: checar, transcrever, segmentar, sons, estilo, receitas, referencia, mapa, validar, cartelas, renderizar, quadros
editar-reel/motor/plano.py     plano.json: carregar, validar, linha do tempo com formato/fundo/tema, âncora na palavra, legendas, contexto das peças, ritmo, mapa
editar-reel/motor/visual.py    formatos A/B/C, paleta de fundos, temas e cores por fundo, áreas, receitas, desenho de fundos e máscara do painel
editar-reel/motor/cartelas.py  fontes (peso variável), legenda que acende, manchete, chamada, selo, palavra solta, cartões, textos de resumo
editar-reel/motor/prints.py    print com moldura, inclinação, pílula e marcações animadas
editar-reel/motor/referencia.py folhas de quadros de vídeo de referência (para escrever receitas)
editar-reel/motor/segmentos.py trechos a partir da transcrição + sugestões de corte
editar-reel/motor/transcricao.py faster-whisper local, um ou vários vídeos
editar-reel/motor/render.py    uma passada de ffmpeg: cada trecho no seu formato, transições, camadas animadas, sons, -14 LUFS
editar-reel/motor/estilo.py    lê pasta estilo/ (cores de imagem e de .txt/.md, fontes)
editar-reel/motor/sons.py      sons sintetizados com ffmpeg (sem direitos autorais)
testes/teste-rapido.sh         fluxo inteiro com vídeos sintéticos, sem modelo de transcrição (tudo em formato A)
testes/teste-formatos.sh       formatos A/B/C, receita combinada, selo, manchete, print anotado, cartões novos, chamada
instalar.sh · instalar.ps1     copiam para ~/.claude/skills/editar-reel, criam .venv, preservam estilo-padrao.json
```

## Arquitetura (decisões que não mudam sem conversar com a autora)
- Só Python + ffmpeg + Pillow + faster-whisper. Nada de Node, navegador ou serviço externo. Motion pesado vai para a motion-reel.
- Um único arquivo de trabalho por vídeo: `plano.json`. Tudo que entra no vídeo é ancorado em `trecho` (e opcionalmente `palavra`), nunca em segundos fixos, para sobreviver a mudanças de corte e velocidade.
- Render em uma passada de ffmpeg. Camadas: PNG em loop, sequência de PNG (contador) ou lista concat (legenda, lista progressiva).
- Cortes nunca são aplicados sem aprovação da pessoa; capa nunca escolhida sem ela.
- Texto na tela tem dois modos: `transcricao` (padrão, decisão da autora: legenda da fala que acende palavra a palavra) e `resumo` (regras dela: até 6 palavras, números e palavra-chave em destaque, 1º 2º 3º).
- Formato por trecho (A tela cheia, B tela dividida, C só gráficos). B e C usam fundo de cena (PNG gerado) e, em B, o vídeo da pessoa recortado com máscara (alphamerge). Toda peça herda formato, tema (video, escuro, claro) e área do trecho em que está ancorada.
- Receitas em `estilos/` só têm as seções fundos, cartoes, prints, manchete, legenda. Combinação por seção. Vídeos de referência de terceiros nunca entram no repositório: só a receita, escrita no nome da autora.
- Mapa visual aprovado pela pessoa antes de renderizar.

## Testar (obrigatório antes de commitar)
```bash
python3 -m py_compile editar-reel/motor/*.py
python3 testes/checar-texto.py                  # nenhum travessão
bash testes/teste-rapido.sh /tmp/teste-reel     # precisa de ffmpeg e Pillow
bash testes/teste-formatos.sh /tmp/teste-fmt    # formatos A/B/C e peças da direção visual
```
Depois abra os PNGs de `quadros/` das duas pastas e olhe de verdade: texto vazando, sobreposição, peça no momento errado. Mudou algo visual? Gere uma folha (`ffmpeg ... hstack`) e confira antes de dizer que funciona. Mudou o instalador? Rode com `HOME` apontando para uma pasta temporária.

## Convenções
- Tudo em PT-BR. Nomes de funções, variáveis e mensagens em português, como o resto do código.
- **Nunca usar travessão nem meia-risca** (os traços longos) em código, docs ou mensagens. Use vírgula ou ponto. Confira com `python3 testes/checar-texto.py`.
- Tom dos textos (README, SKILL.md, mensagens): didático, direto e confiante, profissional sem formalidade, sem gírias, sem exageros.
- Identidade padrão: verdes `#03332c` `#07544a` `#289a8b`, fundos claros off-white, areia e bege, dourado `#ab8208` a `#dfac16` só como detalhe (nunca fundo inteiro, texto longo ou sobre fundo claro), Montserrat, Playfair Display Italic nos destaques e DM Sans nos rótulos.
- Nenhum nome, marca ou referência de terceiros no código ou nos docs. Ideias de outros repositórios sem licença podem inspirar, código nunca.
- Nenhum recurso aparece em exemplo ou documentação antes de existir e ser testado.

## Ao mudar comportamento, atualize junto
1. `editar-reel/SKILL.md` (como o Claude usa)
2. `editar-reel/direcao-visual.md` e as receitas `.md`, se a regra visual mudou
3. `README.md`, seção "Como usar" e a lista "O que ela faz"
4. Avise a autora se a página de divulgação (documento A4 no Claude) precisa de ajuste

## Commits
- Autor: `Stefani Silva <stefanisilva-ia@users.noreply.github.com>`
- Mensagem em PT-BR: título curto + lista do que mudou.
- Terminar com `Co-Authored-By: Claude <noreply@anthropic.com>` (ou a linha de atribuição que a sessão indicar).
- Não commitar `.venv/`, `sons-basicos/`, `__pycache__/`, vídeos.

## Limitações conhecidas e ideias em aberto
- Transcrição depende de baixar o modelo na primeira vez (precisa de internet).
- `av<19` fica travado no requirements: o PyAV 19 quebra a leitura de áudio do faster-whisper 1.2.x. Só remover a trava depois de testar uma versão nova do faster-whisper com o PyAV 19.
- Fonte por nome fora das que vêm em `fontes/` precisa estar instalada no sistema; senão cai na Montserrat da skill com aviso.
- Fase 2 (planejada): telas de programa simuladas e animadas (janela digitando, menu, chat, grade, caixa de comentário com a palavra digitada, cartão de perfil) feitas na motion-reel e encaixadas aqui. Nada disso aparece nos docs até existir.
- Ideia: inserir cenas renderizadas pela motion-reel entre trechos (`insercoes` no plano).
- Ideia: overlay de vídeo com transparência (.mov da motion-reel) como camada, na área das peças de B e C.
- Linha de comando do ffmpeg muito longa (mais de 30 mil caracteres) vai para arquivo de filtros (`-/filter_complex` no ffmpeg 7+, `-filter_complex_script` antes).
