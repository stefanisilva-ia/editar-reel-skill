# Direção visual

Regras para decidir o visual de cada trecho do reel. Leia antes de montar o plano, na etapa do mapa visual. Medidas em pixels para 1080x1920. Os nomes entre crases são os campos do `plano.json` (detalhes no SKILL.md).

## 1. Princípios
- O formato muda quando a ideia muda, não a cada corte de fala.
- Uma peça central por vez. No máximo 2 elementos de apoio junto.
- Toda peça entra no instante da palavra que a nomeia.
- O texto na tela é a fala transcrita. Resumo só na manchete.
- Nada de enfeite sem função: cada peça, cor ou som explica, destaca ou marca uma virada.

## 2. Formatos (`formato` do trecho)

### A. Tela cheia
Para conexão: opinião, alerta pessoal, fala direta para quem assiste, virada, história, chamada final.
- Vídeo da pessoa em 1080x1920, rosto no terço superior.
- Zoom alternado 1.00 e 1.12 entre trechos A.
- Aproximação rápida 1.20 (`zoom`) na frase mais forte. No máximo 2 por vídeo.
- Inclinação de 2° (`inclinacao`) só numa virada. No máximo 1 por vídeo.
- Legenda: centro em y 1300, Montserrat SemiBold 64 px, branca com sombra suave.

### B. Tela dividida
Para explicar com exemplo: como funciona, demonstração, prova, print.
- Fundo de cena em cima (seção 7).
- Selo de série: y 92 a 148 (se houver).
- Manchete: centro em y 280 (opcional).
- Área da peça: y 400 a 1000 com manchete, y 200 a 1000 sem.
- Legenda: logo acima do painel (centro em y 1072), Montserrat SemiBold 56 px.
- Painel da pessoa: 40% de baixo (`painel` 0.40), margem lateral de 16 px, cantos superiores de 48 px, rosto no terço superior do painel. Entra com fade e sobe 40 px quando o trecho anterior não é B.
- Print grande no trecho: o painel encolhe para 33%.

### C. Só gráficos
Para o que a imagem explica melhor que o rosto: processo, conceito, lista, número, palavra-chave.
- Sem a pessoa. A fala continua.
- Área da peça: y 260 a 960 (400 a 960 com manchete).
- Legenda: centro em y 1120, MAIÚSCULAS, Montserrat Bold 76 px.
- Print grande: área até y 1250, legenda em y 1420.
- Palavra solta: centro em y 860, Playfair Display Italic 170 px, na cor de destaque.

## 3. Escolha do formato

| O trecho faz | Formato | Peça |
|---|---|---|
| Gancho (primeiros 3 s) | B | manchete e a peça que mostra a promessa |
| Opinião, alerta pessoal, fala direta, virada | A | legenda, aproximação rápida |
| História, bastidor, experiência própria | A | legenda |
| Explica como algo funciona | B | print anotado ou fluxo |
| Mostra ferramenta real, documento, resultado real | B | print anotado |
| Processo, passo a passo | C | fluxo ou lista que acende |
| Conceito abstrato | C | palavra solta ou ilustração |
| Número ou resultado | C ou B | cartão de número |
| Enumeração | C ou B | lista que acende (1º, 2º, 3º) |
| Checagem, requisitos | C ou B | lista com check |
| Comparação, antes e depois | C ou B | cartão de comparação |
| Erro, risco, proibição | B ou C com fundo de alerta | print com caixa vermelha ou palavra de alerta |
| Chamada final | A | chamada (seção 13) |

Na dúvida entre B e C: se a peça precisa da fala para ser entendida, use B. Se a peça se explica sozinha, use C.

## 4. Ritmo
- Cada formato dura de 2 a 5 s.
- C no máximo 6 s seguidos. Depois disso, o rosto volta (A ou B).
- Rosto visível (A ou B) em pelo menos 50% do vídeo.
- Abra em B. Feche em A.
- A mesma peça não se repete em sequência.
- O mesmo formato não passa de 2 trechos seguidos quando eles somam mais de 5 s.

`reel mapa` e `reel validar` avisam quando uma dessas regras é quebrada.

## 5. Mapa visual (etapa obrigatória)
Depois da aprovação dos cortes e antes de renderizar, preencha formato, fundo e peças no plano e rode `reel mapa PASTA`. Ele mostra:

| # | Início | Fala | Formato | Fundo | Peças | Som |
|---|---|---|---|---|---|---|
| 1 | 0.0 s | Tu usa o modelo... | B | verde-noite | manchete: o *Claude* certo | - |

- Uma linha por trecho mantido, mais a chamada, a proporção de cada formato e os avisos de ritmo.
- Apresente a tabela, a receita escolhida e as imagens que faltam (seção 10).
- Espere a aprovação. Ajuste linha por linha quando a pessoa pedir.

## 6. Texto na tela

### Legenda (sempre)
- Transcrição da fala, sincronizada palavra a palavra, só dos trechos mantidos.
- Blocos de 2 palavras (padrão), 1 a 3 no máximo.
- Nomes compostos ficam no mesmo bloco (`nomes` e `correcoes` com espaço).
- O bloco aparece inteiro. A palavra ainda não dita fica em 45% de opacidade e acende quando é falada.
- Sem vírgula nem ponto final. Mantém "?" em pergunta.
- Corrija nomes e termos técnicos antes de renderizar (Claude, IA, n8n).
- Posição, tamanho e caixa conforme o formato (seção 2).
- Some quando a chamada final entra.

### Palavra-chave (`destaques`)
- Playfair Display Italic, 1,15 vez o tamanho da legenda, na mesma linha.
- Cor: dourado `#DFAC16` em fundo escuro e sobre o vídeo, verde `#07544A` em fundo claro.
- No máximo 1 a 2 por frase: termo central, resultado, número ou palavra da chamada.
- Palavra de risco ou erro (`alertas`: "proibido", "erro", "perigo"): vermelho `#C9473A`. Sobre o fundo de alerta, ela sai dourada para não sumir.
- Caixa atrás da palavra (`caixa_em`): só no ponto principal do vídeo, no máximo 2 vezes.
- Números e ordinais ficam destacados sozinhos.

### Palavra solta (cartão `palavra`)
- Em C, quando uma palavra resume a cena ("sozinho", "barato", "pronto").
- Até 1 a cada 15 s.

### Manchete (`tipo: manchete`, opcional)
- Só aparece nos trechos B e C que cobre.
- Resumo da seção em até 6 palavras, Montserrat ExtraBold 62 px, maiúsculas.
- Uma palavra em `*destaque*`: Playfair Display Italic na cor de destaque, ou dentro de etiqueta verde (receita print-anotado).
- Muda a cada seção, não a cada trecho.

### Selo de série (`selo`, opcional)
- Só quando a pessoa disser que o vídeo é de uma série.
- Duas pílulas no topo: nome da série e "parte X/Y" com barra de progresso. DM Sans 30 px.
- Fica nos três formatos, do começo ao fim.

## 7. Cores e fundos

| Papel | Cores |
|---|---|
| Fundos escuros | `verde-profundo` `#03332C`, `verde-medio` `#07544A`, `verde-noite` `#0A2420` |
| Fundos claros | `off-white` `#F7F4EE`, `areia` `#EDE3D1`, `bege` `#DDCDB4` |
| Fundo de alerta | `alerta` `#A8382C` |
| Texto | branco `#FFFFFF` no escuro, `#111111` no claro |
| Destaque | dourado `#DFAC16` (gradiente `#DFAC16` a `#AB8208` em palavras grandes) no escuro, verde `#07544A` no claro |
| Apoio | verde-água `#289A8B` em linhas, ícones, bordas, checks e marcações |
| Alerta | vermelho `#C9473A` em palavra, caixa de marcação e seta |

- Fundo com brilho radial suave no topo central. A receita escuro-tecnico acrescenta um arco fino.
- A troca de fundo marca troca de seção ou de emoção, nunca a cada trecho.
- Até 3 fundos por vídeo, mais o de alerta.
- Misturar escuro e claro no mesmo vídeo é permitido.
- Dourado nunca sobre fundo claro, nunca em texto longo, nunca como fundo inteiro.
- Prints, logos e ilustrações mantêm as cores originais. A moldura segue a paleta.

## 8. Tipografia

| Uso | Fonte |
|---|---|
| Legenda, manchete, chamada, cartões | Montserrat (SemiBold a ExtraBold) |
| Palavra-chave, palavra solta, palavra da chamada | Playfair Display Italic |
| Selo, pílulas, rótulos | DM Sans |

As três vêm na pasta `fontes/` da skill (licença OFL).

## 9. Peças visuais
- **Print anotado:** print real em cartão, com moldura e inclinação da receita (alternando o lado). Marcações: `circulo`, `caixa`, `marca` (marca-texto), `sublinhado`, `seta`. Pílula curta abaixo explicando o print (até 6 palavras).
- **Cartão de número:** conta de zero até o valor.
- **Lista:** cada item entra quando é dito (1º, 2º, 3º). Com `check`, todos aparecem apagados e ganham o check quando são ditos.
- **Fluxo:** 2 a 5 etapas numeradas e ligadas; cada uma acende quando é dita.
- **Comparação:** duas colunas (antes e agora); a da direita leva o destaque.
- **Palavra solta:** seção 6.
- **Imagem, ícone ou logo:** com fundo transparente ou como print.
- Os cartões seguem o fundo do trecho: verde escuro com borda verde-água no escuro, branco translúcido no claro.
- Nunca invente dado, nome, número ou tela que não existe na fala ou no material da pessoa.

## 10. Imagens e ilustrações
Ordem obrigatória:
1. **Procurar:** pastas `imagens/`, `prints/` e `ilustracoes/` do projeto e os anexos da conversa.
2. **Encontrou:** adapte ao vídeo (formato, área, marcações, pílula, entrada). Confirme em uma linha qual arquivo vai em qual trecho.
3. **Não encontrou:** peça à pessoa e diga o que a imagem precisa mostrar e em qual trecho entra.
4. **A pessoa não tem:**
   - Número, lista, etapas, comparação ou conceito: use os cartões da seção 9.
   - Ilustração realista ou 3D, objeto, cena: entregue um prompt em inglês para o Gemini (modelo abaixo).
   - Logo de marca, produto, tela real ou pessoa: nunca gere. Peça a imagem real.

Modelo de prompt para o Gemini:
```
3D render of [subject], soft clay style, rounded shapes, soft studio lighting,
centered, isolated on a plain [#F7F4EE off-white | #03332C deep green] background,
color palette deep green #07544A, teal #289A8B, gold accents #DFAC16,
no text, no logos, square 1:1, clean edges for background removal
```
Depois que a pessoa gerar a imagem e mandar, siga o passo 2.

## 11. Movimento e transições
- Troca de formato: corte seco.
- Painel da pessoa entrando em B: fade de 0,2 s e sobe 40 px.
- Peças: entrada sobe (0,3 s) ou pop (número e chamada).
- Palavra solta: entra do desfoque para o nítido em 0,3 s, crescendo de 0,94 para 1.
- Marcações de print: se desenham em 0,23 s, na palavra dita.
- Lista, fluxo e comparação: cada parte acende na palavra dita.
- Fundo de alerta: entra e sai com corte seco.
- `fade`, `flash` e `zoom`: só na troca de assunto principal, no máximo 2 por vídeo.

## 12. Sons
Use pelo nome (`"arquivo": "pop"`) ou um arquivo da pessoa.

| Som | Quando |
|---|---|
| whoosh | entrada em C ou de peça grande (não em toda troca) |
| pop | palavra solta, cartão |
| click | itens de lista e fluxo (`som_itens`), marcações (`som_anotacoes`) |
| ding | check, resultado |
| impacto | frase mais forte, no máximo 1 por vídeo |

- No máximo 1 som a cada 3 s, volume de 0,35 a 0,6.
- Música: a pessoa escolhe no app, em volume baixo e contínuo. O arquivo final sai sem música.

## 13. Chamada final
- Formato A.
- "COMENTA": Montserrat ExtraBold 60 px, maiúsculas, branco, centro em y 1340.
- A palavra: Playfair Display Italic 160 px, na cor de destaque, centro em y 1470.
- Complemento curto ("que eu te mando"): Montserrat 44 px, centro em y 1590.
- A legenda da fala some quando a chamada entra.

## 14. Estilos (receitas)
Cada receita fica em `estilos/` (`.json` que o motor lê e `.md` que descreve) e define fundos, cartões, prints, manchete e legenda. As regras deste arquivo valem para todas. `reel receitas` lista as disponíveis.
- `escuro-tecnico`: ferramentas de IA, bastidores técnicos, Claude, automação.
- `claro-vidro`: explicação de processo, conteúdo educativo, comparações.
- `print-anotado`: ferramenta real, documentação, prova, passo a passo com telas reais.

Escolha:
1. O que a pessoa pedir.
2. A pasta `estilo/` do projeto.
3. A receita que combina com o assunto. Diga qual vai usar no mapa visual.

Combinar: use a base de uma receita e uma seção de outra (ex.: `{"base": "escuro-tecnico", "prints": "print-anotado"}`). Diga a combinação no mapa visual.

Receita nova: a partir de um vídeo de referência, com `reel referencia` (SKILL.md, "Nova referência de estilo").

## 15. Conferência antes de entregar
- Legenda não cobre rosto nem peça.
- Rosto inteiro no painel, sem cortar testa nem queixo.
- Texto legível em todos os fundos.
- Nenhuma cena C passa de 6 s.
- Rosto visível em pelo menos 50% do vídeo.
- Dourado não aparece sobre fundo claro.
- No máximo 2 palavras-chave por frase.
- Nenhum dado, nome ou número inventado.
- Imagem de terceiros só com confirmação da pessoa e com crédito.
