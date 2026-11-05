# Sprint 01 — Glossário dos requisitos funcionais

Este documento explica os termos usados na [especificação da Sprint 01](sprint01.md)
e mostra como aparecem no SpotLab. Os exemplos descrevem as regras fictícias
do simulador, com o objetivo de facilitar a leitura dos requisitos e da saída
do terminal.

Nos textos abaixo, usamos a notação brasileira: `0,001` significa um milésimo
e `100.000` significa cem mil. No código e no terminal, os mesmos números
aparecem como `0.001` e `100000`.

## 1. Requisito funcional, regra de negócio e cenário

**Requisito funcional** descreve um comportamento que o sistema deve oferecer.
Por exemplo: receber uma ordem limitada, executar a parte compatível com o livro
e permitir cancelar o restante. Ele responde à pergunta: “o que o sistema faz?”.

**Regra de negócio** define as condições e os cálculos desse comportamento.
Exemplo: uma compra limitada só pode executar por preço menor ou igual ao
limite informado.

**Cenário** é uma situação concreta usada para demonstrar o comportamento.
No cenário D, uma compra de 0,001 BTC começa pendente, executa 0,0004 BTC e
tem os 0,0006 BTC restantes cancelados.

**Critério de aceite** é uma condição verificável para considerar um requisito
atendido. Nesse cenário, a reserva deve ser de 99,9999 USDT na aceitação,
59,99994 USDT após a execução parcial e zero depois do cancelamento.

Usar Python 3.11 ou superior e não ter dependências externas são restrições
técnicas da implementação. Já calcular a taxa e liberar uma reserva são
comportamentos funcionais.

## 2. Mercado, ativos e unidades

| Termo | Significado no exemplo |
| --- | --- |
| Mercado Spot | Compra e venda do próprio ativo. A compra do exemplo aumenta o saldo em BTC e reduz o saldo em USDT. |
| Ativo | Algo representado por um saldo e negociado no sistema. Aqui, BTC e USDT. |
| BTC | Símbolo usado para bitcoin; é o ativo comprado ou vendido no exemplo. |
| USDT | Ativo usado para expressar preços e pagar a compra. Busca acompanhar o dólar, mas não é o próprio dólar. |
| Par negociado | Combinação de dois ativos, como BTC/USDT, que informa o que é negociado e em qual ativo o preço é expresso. |
| Ativo base | Primeiro ativo do par: BTC. As quantidades das ordens são informadas nele. |
| Ativo de cotação | Segundo ativo do par: USDT. É usado para calcular valores de compra, venda e taxas. |
| Preço | Quanto custa uma unidade do ativo base. Um preço de 100.000 USDT/BTC significa 100.000 USDT por 1 BTC. |
| Quantidade | Quanto do ativo base será negociado. Exemplo: 0,001 BTC. |
| Margem | Uso de garantias para sustentar posições, que podem envolver recursos emprestados. Não é implementada nesta sprint. |
| Alavancagem | Exposição a uma posição maior do que os recursos próprios usados para sustentá-la. Não é implementada nesta sprint. |

É importante distinguir preço e valor da operação:

```text
Preço:       100.000 USDT/BTC
Quantidade:    0,001 BTC
Valor bruto: 100.000 × 0,001 = 100 USDT
```

`BTC/USDT` é o nome do par. `USDT/BTC`, quando acompanha um número de preço,
indica a unidade “USDT por BTC”.

## 3. Carteira e saldos

**Carteira** é o registro dos saldos por ativo dentro do simulador. Neste
projeto, ela é uma estrutura em memória, sem endereço blockchain, custódia
ou transferência real.

**Saldo disponível** é a quantidade que pode ser usada para aceitar novas ordens.
**Saldo reservado** é a quantidade separada para uma ordem já aceita, que não
pode financiar outra ordem ao mesmo tempo.

Reservar não significa que a negociação já ocorreu. Considere o início do
cenário D:

| Momento | USDT disponível | USDT reservado | BTC disponível |
| --- | ---: | ---: | ---: |
| Antes da ordem | 1.000 | 0 | 0 |
| Compra limitada aceita, sem execução | 900,0001 | 99,9999 | 0 |
| Após comprar 0,0004 BTC | 900,0001 | 59,99994 | 0,0004 |
| Após cancelar o restante | 960,00004 | 0 | 0,0004 |

**Liberação de reserva** devolve ao saldo disponível aquilo que não será mais
necessário para executar a ordem. O cancelamento não desfaz a parte já comprada.

**Saldo insuficiente** ocorre quando o disponível não cobre a reserva exigida.
A compra de 100 USDT com taxa de 0,1 USDT exige 100,1 USDT disponíveis.
Ter exatamente 100 USDT não é suficiente.

## 4. Livro de ofertas, bid, ask e spread

**Livro de ofertas**, ou *order book*, é a coleção de ofertas de compra e venda
disponíveis. Uma oferta ainda pode ser negociada; uma execução já aconteceu.
No SpotLab, o livro contém somente ofertas externas à carteira simulada.

**Nível do livro** registra um preço e uma quantidade disponível nesse preço.
Exemplo: uma oferta de venda de 0,0006 BTC a 100.000 USDT/BTC.

| Termo | Explicação |
| --- | --- |
| Bid | Oferta de compra. O melhor bid é o maior preço disponível entre os compradores. |
| Ask | Oferta de venda. O melhor ask é o menor preço disponível entre os vendedores. |
| Consumir uma oferta | Executar uma negociação contra ela, reduzindo sua quantidade disponível. |
| Profundidade | Quantidade disponível nos diferentes níveis de preço do livro. |
| Liquidez | Facilidade de negociar uma quantidade sem precisar deslocar muito o preço. No exemplo, pode ser observada pela quantidade e pelos preços das ofertas disponíveis. |
| Spread | Diferença entre o melhor ask e o melhor bid. |
| Ponto médio | Média aritmética entre melhor ask e melhor bid; é o denominador do spread percentual adotado nesta sprint. |

No cenário B:

```text
Melhor bid = 99.990 USDT/BTC
Melhor ask = 100.010 USDT/BTC
Spread absoluto = 100.010 − 99.990 = 20 USDT/BTC
Ponto médio = (100.010 + 99.990) / 2 = 100.000 USDT/BTC
Spread percentual = 20 / 100.000 × 100 = 0,02%
```

Ao comprar imediatamente, a ordem encontra os vendedores e consome asks.
Ao vender imediatamente, encontra os compradores e consome bids. Por isso,
comprar 0,001 BTC no ask e vender no bid do exemplo gera perda bruta de
`20 × 0,001 = 0,02 USDT`, antes das taxas.

## 5. Ordens e execuções

**Ordem** é a instrução para comprar ou vender uma quantidade. **Execução**,
também chamada de *fill*, é uma negociação efetivamente realizada para atender
essa instrução. Uma ordem pode gerar nenhuma, uma ou várias execuções.

| Identificador | Termo | Comportamento no SpotLab |
| --- | --- | --- |
| `BUY` | Compra | Usa USDT para receber BTC; a taxa também é paga em USDT. |
| `SELL` | Venda | Usa BTC para receber USDT; a taxa é descontada do valor recebido. |
| `MARKET` | Ordem a mercado | Consome as ofertas existentes, começando pelo melhor preço, sem um preço limite definido pelo usuário. |
| `LIMIT` | Ordem limitada | Só executa se houver uma oferta compatível com o preço limite. A parte restante fica pendente. |

**Preço limite** é o maior preço aceito numa compra ou o menor preço aceito
numa venda. Uma compra limitada a 99.900 USDT/BTC pode executar a 99.900 ou menos;
uma venda limitada a esse preço pode executar a 99.900 ou mais.

No simulador, uma limitada compatível executa pelo preço da oferta externa
existente. Se uma compra tem limite de 100.000 USDT/BTC e encontra uma venda
a 99.900 USDT/BTC, executa a 99.900, liberando a diferença reservada com taxa.

**Execução total** atende toda a quantidade solicitada. **Execução parcial**
atende apenas parte dela. **Quantidade restante** é a solicitada menos a
executada. Depois de um cancelamento, o relatório continua mostrando essa
quantidade como registro do que deixou de ser executado; ela já não está pendente.

### Estados da ordem

| Estado | Tradução | Significado |
| --- | --- | --- |
| `NEW` | Nova | Ordem aceita que ainda não teve execução. |
| `PARTIALLY_FILLED` | Parcialmente executada | Parte foi negociada e a parte restante continua pendente. |
| `FILLED` | Totalmente executada | Toda a quantidade foi negociada. |
| `CANCELED` | Cancelada | A parte não executada foi encerrada. Pode haver execuções anteriores preservadas. |

**Transição de estado** é uma mudança entre esses estados. O cenário D percorre
`NEW → PARTIALLY_FILLED → CANCELED`. Uma limitada também pode ir diretamente
de `NEW` para `FILLED` se houver volume compatível suficiente.

Uma ordem a mercado com volume insuficiente executa o disponível e termina
como `CANCELED`, mesmo que uma parte tenha sido negociada. Essa é uma convenção
didática do SpotLab. Uma ordem inválida é **rejeitada** antes de ser aceita;
ela não recebe um estado `REJECTED`, pois esse estado não faz parte do modelo.

**Casamento de ordens**, ou *matching*, é encontrar uma oferta de sentido
oposto com preço compatível para realizar uma negociação. O SpotLab casa
ordens da carteira apenas com ofertas externas. Ordens pendentes da própria
carteira não são inseridas no livro nem negociam entre si.

## 6. Preço médio e slippage

**Preço médio de execução** é a média dos preços ponderada pelas quantidades
negociadas. Uma execução maior tem mais peso no resultado. Não é, em geral,
a média simples dos preços.

O cenário C compra em dois níveis:

| Execução | Quantidade | Preço | Valor bruto |
| --- | ---: | ---: | ---: |
| 1 | 0,0006 BTC | 100.000 USDT/BTC | 60 USDT |
| 2 | 0,0004 BTC | 100.100 USDT/BTC | 40,04 USDT |
| Total | 0,001 BTC | — | 100,04 USDT |

```text
Preço médio = (60 + 40,04) / 0,001 = 100.040 USDT/BTC
```

**Preço de referência** é o preço usado para comparar a execução. O SpotLab
registra o melhor ask para uma compra ou o melhor bid para uma venda no momento
da aceitação da ordem, antes de consumir o livro. A referência permanece a mesma
quando uma ordem pendente é processada novamente.

**Slippage** é a diferença entre o preço médio executado e essa referência.
O relatório usa a convenção de **slippage desfavorável**:

```text
Compra (%) = (preço médio − ask de referência) / ask de referência × 100
Venda (%)  = (bid de referência − preço médio) / bid de referência × 100
```

Assim, valor positivo significa preço pior; negativo significa preço melhor.
No cenário C: `(100.040 − 100.000) / 100.000 × 100 = 0,04%`.
Sem execução ou sem referência inicial, o resultado é “não aplicável”.

Spread compara os dois lados do livro em um momento. Slippage compara a
execução com sua referência. A taxa é uma cobrança separada. O efeito do spread
e do slippage já aparece nos preços executados; descontá-los novamente do lucro
contaria o mesmo efeito duas vezes.

## 7. Taxas, valores e resultado

**Taxa de negociação** é a cobrança aplicada à operação. Nesta sprint, é
fictícia e igual a 0,10% do valor bruto em cada ponta, paga em USDT.
“Cada ponta” significa que a compra e a venda têm cobranças próprias.

`0,10%` em formato percentual equivale a `0,001` como fator de multiplicação,
por isso o código usa `Decimal("0.001")`.

| Termo | Fórmula adotada |
| --- | --- |
| Valor bruto | Soma de preço × quantidade de cada execução, antes da taxa. |
| Taxa em USDT | Valor bruto × fator da taxa. |
| Desembolso total de compra | Valor bruto da compra + taxa da compra. |
| Recebimento líquido de venda | Valor bruto da venda − taxa da venda. |
| Lucro bruto | Valor bruto da venda − valor bruto da compra. |
| Taxas totais | Taxa da compra + taxa da venda. |
| Lucro líquido | Lucro bruto − taxas totais; equivale ao recebimento líquido de venda menos o desembolso de compra. |
| Retorno líquido percentual | Lucro líquido / desembolso total de compra × 100. |

As fórmulas de lucro e retorno acima são usadas para a compra e a venda da
mesma quantidade no ciclo completo do cenário A:

```text
Compra: 100 USDT brutos + 0,1 USDT de taxa = 100,1 USDT desembolsados
Venda:  101 USDT brutos − 0,101 USDT de taxa = 100,899 USDT recebidos
Lucro bruto: 101 − 100 = 1 USDT
Taxas totais: 0,1 + 0,101 = 0,201 USDT
Lucro líquido: 1 − 0,201 = 0,799 USDT
Retorno líquido: 0,799 / 100,1 × 100 ≈ 0,798202%
```

O denominador desse retorno é o capital desembolsado na compra, incluindo
a taxa, e não o saldo inicial completo de 1.000 USDT.

**Maker** é a ordem, ou a parte dela, que adiciona uma oferta ao livro e aguarda
uma contraparte. **Taker** é a que executa contra uma oferta já disponível,
retirando liquidez. Ser limitada não torna uma ordem automaticamente maker:
ela pode encontrar uma oferta compatível e executar imediatamente. O SpotLab
não classifica nem diferencia taxas maker/taker.

## 8. Candles, OHLCV e tempo

**Negociação**, ou *trade*, é um negócio realizado, com horário, preço e
quantidade. O cenário E usa uma lista fictícia dessas negociações para montar
o candle, sem obtê-las de uma exchange.

**Candle** é um resumo das negociações de um intervalo. **OHLCV** é a sigla dos
cinco campos desse resumo:

| Campo | Nome em inglês | Significado |
| --- | --- | --- |
| O | Open | Preço da primeira negociação do intervalo. |
| H | High | Maior preço negociado no intervalo. |
| L | Low | Menor preço negociado no intervalo. |
| C | Close | Preço da última negociação do intervalo. |
| V | Volume | Soma das quantidades negociadas; nesta sprint, em BTC. |

**Candle aberto** é aquele cujo intervalo ainda não terminou. Novas negociações
podem alterar sua máxima, mínima, fechamento e volume. Seu campo Close é o
preço mais recente disponível, ainda provisório. **Candle fechado** é aquele
cujo intervalo já terminou.

**UTC** é o padrão de tempo usado para identificar os horários sem depender
do fuso local. `2026-01-01T12:00:00+00:00` significa meio-dia em UTC; o
`+00:00` identifica o deslocamento zero em relação a UTC.

**Intervalo com fim exclusivo**, escrito `[início, fim)`, inclui o instante
inicial e exclui o final. O candle de 12:00:00 até 12:01:00 inclui uma negociação
às 12:00:00; uma negociação às 12:01:00 pertence ao próximo candle.

No cenário E, o candle fechado tem O=100.000, H=100.100, L=99.900 e C=100.050
USDT/BTC, com volume de 0,01 BTC. A negociação de 0,005 BTC exatamente às
12:01:00 fica fora dele.

**Sequência intraperíodo** é a ordem dos acontecimentos dentro do intervalo.
OHLCV não preserva essa sequência completa. Saber que houve máxima de 100.100
e mínima de 99.900 não revela, por si só, qual delas aconteceu primeiro nem
qual de dois níveis de saída foi atingido antes.

## 9. Termos de funcionamento do simulador

| Termo | Significado e aplicação |
| --- | --- |
| `Decimal` | Tipo numérico decimal usado para preços, quantidades, taxas e saldos. É criado de strings, como `Decimal("0.001")`, para evitar introduzir aproximações de um float. |
| Precisão | Quantidade de dígitos significativos usada nos cálculos. O SpotLab define 40, o que não significa 40 casas depois da vírgula. Divisões periódicas continuam sujeitas a essa precisão. |
| Arredondamento | Regra para reduzir dígitos. A saída mostra até 12 casas decimais; os valores internos não são substituídos pelos números formatados do relatório. |
| `ROUND_HALF_EVEN` | Em um empate exato de arredondamento, escolhe o último dígito par. Em duas casas, `1,245` vira `1,24` e `1,255` vira `1,26`. |
| NaN e infinito | Valores especiais que não representam preços ou saldos finitos válidos. NaN significa “não é um número”; ambos são rejeitados pelo simulador. |
| Validação de entrada | Conferência dos dados antes de aceitar uma operação. Por exemplo: quantidade positiva, taxa menor que 1 e saldo suficiente. |
| Sem mutação em uma rejeição | Rejeitar uma entrada inválida sem alterar carteira ou livro. Uma tentativa de compra sem saldo não pode deixar uma compra parcial realizada. |
| Invariante | Condição que deve continuar verdadeira durante o funcionamento. Exemplos: saldo nunca negativo e volume executado nunca maior que o disponível. |
| Evento explícito | Ação informada ao simulador, como adicionar uma oferta externa e mandar processar novamente uma ordem. O cenário D demonstra esse mecanismo. |
| Determinístico ou reproduzível | Os mesmos dados e ações produzem os mesmos resultados. Os cenários usam horários fixos e começam com carteiras e livros novos. |
| CLI ou terminal | Interface de linha de comando. `python -m spotlab --cenario c` executa apenas o cenário C. |
| Teste automatizado | Código que compara o comportamento observado ao esperado. Os testes usam `unittest` e verificam valores, estados, saldos e livro. |
| Fila de prioridade | Regra para decidir qual ordem tem preferência quando várias competem. Não é simulada nesta sprint. |
| Concorrência | Processamento de ações que podem disputar recursos ao mesmo tempo. O SpotLab opera de forma sequencial. |
| Latência | Tempo entre enviar uma ação e ela ser recebida ou executada. Não é simulada. |

## 10. Onde observar cada grupo de termos

| Para observar | Execute | Implementação principal |
| --- | --- | --- |
| Par, taxas, lucro e retorno | `python -m spotlab --cenario a` | [scenarios.py](../spotlab/scenarios.py) e [market.py](../spotlab/market.py) |
| Bid, ask e spread | `python -m spotlab --cenario b` | [market.py](../spotlab/market.py) |
| Profundidade, execuções e slippage | `python -m spotlab --cenario c` | [market.py](../spotlab/market.py) |
| Reserva, estados e cancelamento | `python -m spotlab --cenario d` | [market.py](../spotlab/market.py) |
| Negociações, OHLCV e intervalo UTC | `python -m spotlab --cenario e` | [candles.py](../spotlab/candles.py) |

O [README](../README.md) reúne os comandos e as simplificações. O
[relatório de validação](sprint01-validacao.md) registra os resultados conferidos.
