# SpotLab

Exemplo didático de mercado Spot em Python 3.11 ou superior, executado localmente
com a biblioteca padrão. Todos os preços, saldos, livros e negociações são
fictícios. A aplicação ensina a execução de ordens e o cálculo do resultado
líquido, sem margem ou alavancagem.

## Executar

Na raiz deste repositório (a própria pasta `spotlab`), sem instalar pacotes:

```bash
python -m spotlab
python -m spotlab --cenario a
python -m spotlab --cenario b
python -m spotlab --cenario c
python -m spotlab --cenario d
python -m spotlab --cenario e
python -m spotlab --help
python -m unittest discover -s tests -v
```

O primeiro comando executa todos os cenários. Cada cenário cria carteira e livro
novos. Os horários são fixos em UTC, a partir de `2026-01-01T12:00:00+00:00`.
A execução não faz chamadas de rede e não precisa de credenciais. O
`pyproject.toml` contém os metadados; setuptools só é necessário se for empacotar,
não para executar os comandos acima.

## Conceitos e cenários

Consulte o [glossário dos requisitos funcionais](docs/sprint01-glossario.md)
para explicações dos termos, fórmulas e exemplos de cada cenário.

| Cenário | Conceitos | Resultado central |
| --- | --- | --- |
| A | Par BTC/USDT, taxas de compra e venda, lucro e retorno | Lucro líquido de 0.799 USDT; saldo final de 1000.799 USDT |
| B | Melhor bid, melhor ask e spread | Spread de 20 USDT/BTC, 0.02% sobre o ponto médio; perda bruta de 0.02 USDT |
| C | Profundidade, várias execuções e slippage | Preço médio de 100040 USDT/BTC; slippage de 0.04%; desembolso de 100.14004 USDT |
| D | Limite, reserva, execução parcial e cancelamento | Reserva de 99.9999 USDT; após execução, 59.99994 USDT; ao cancelar, zero |
| E | Candle OHLCV aberto e fechado | Intervalo de um minuto, com fim exclusivo; volume de 0.01 BTC no candle fechado |

No par BTC/USDT, BTC é o ativo base e USDT é o ativo de cotação. USDT busca
acompanhar o dólar, mas não é o próprio dólar. Preços são informados em USDT/BTC,
quantidades e volumes em BTC, valores e taxas em USDT.

O **bid** é a melhor oferta externa de compra; o **ask**, a melhor oferta externa
de venda. Comprar consome asks em ordem crescente; vender consome bids em ordem
decrescente. Cada execução reduz a quantidade do respectivo nível.

- Spread absoluto = ask − bid.
- Spread percentual = (ask − bid) / ((ask + bid) / 2) × 100, usando o ponto médio.
- Preço médio = soma(preço × quantidade de cada execução) / quantidade executada.
- Slippage desfavorável de compra = (preço médio − ask de referência) / ask de referência × 100.
- Slippage desfavorável de venda = (bid de referência − preço médio) / bid de referência × 100.

A referência de slippage é capturada na aceitação da ordem, antes de consumir o
livro, e mantida nas execuções posteriores. Slippage positivo significa execução
pior; negativo, melhor. Sem execução ou sem referência inicial, não é aplicável.

O saldo **disponível** pode financiar novas ordens; o **reservado** fica vinculado
às ordens aceitas. Compra limitada reserva quantidade × limite × (1 + taxa).
Compra a mercado percorre a profundidade existente e reserva seu custo com taxa.
A checagem ocorre antes de alterar saldos ou livro: saldo insuficiente rejeita
a ordem integralmente. Venda reserva a quantidade solicitada em BTC; sua taxa
é descontada do recebimento em USDT.

Limitadas executam no preço da oferta externa compatível, respeitando o limite.
Quando uma compra executa abaixo do limite, a diferença reservada volta ao saldo
disponível. A parte pendente mantém a reserva. Cancelar libera apenas a reserva
restante e preserva as execuções anteriores.

Estados: `NEW` (aceita sem execução), `PARTIALLY_FILLED` (parte executada e parte
pendente), `FILLED` (execução completa), `CANCELED` (restante cancelado, com ou sem
execuções anteriores). Reprocessar ou cancelar uma ordem terminal não altera
saldos. Preços e quantidades devem ser positivos e finitos; saldos não podem ser
negativos. Taxas precisam ser finitas no intervalo `[0, 1)`.

Candles são fotografias calculadas das negociações conhecidas até o horário de
observação. O intervalo é `[início, fim)`; uma negociação exatamente no fim entra
no candle seguinte. Open/close seguem a ordem temporal (em horários iguais,
a ordem fornecida); high/low são extremos e o volume é a soma em BTC. Sem
negociações, OHLC fica ausente e o volume é zero. OHLCV sozinho não revela a
sequência intraperíodo nem qual de dois níveis de saída foi atingido primeiro.

## Exemplo de saída

Trechos do cenário A; o relatório completo também mostra cada execução, reserva,
slippage e saldos intermediários:

```text
Valor bruto=100 USDT; taxas=0.1 USDT
Desembolso total=100.1 USDT; preço médio=100000 USDT/BTC
Valor bruto=101 USDT; taxas=0.101 USDT
Recebimento líquido=100.899 USDT; preço médio=101000 USDT/BTC
USDT: disponível=1000.799; reservado=0
BTC: disponível=0; reservado=0
Lucro bruto = venda - compra = 101 - 100 = 1 USDT
Taxas totais = 0.1 + 0.101 = 0.201 USDT
Lucro líquido = bruto - taxas = 1 - 0.201 = 0.799 USDT
Retorno líquido = 0.799 / 100.1 * 100 = 0.798201798202%
```

Os preços executados já incorporam os efeitos do spread e do slippage; esses
custos não são descontados novamente do resultado.

## Estrutura

```text
pyproject.toml                 Metadados e versão mínima de Python
spotlab/__init__.py            Pacote
spotlab/__main__.py            CLI
spotlab/market.py              Par, livro, carteira, ordens e execuções
spotlab/candles.py             Negociações e candles OHLCV
spotlab/scenarios.py           Cenários reproduzíveis e apresentação
tests/test_market.py           Testes de resultados e invariantes
docs/sprint01.md               Especificação original
docs/sprint01-glossario.md     Termos dos requisitos com exemplos
docs/sprint01-validacao.md     Procedimento e resultados verificados
```

## Simplificações

- Taxa fictícia padrão de `Decimal("0.001")` (0.10%) em USDT nas duas pontas,
  sem distinção entre maker e taker. Ordens de compra usam quantidade em BTC.
- Uma ordem a mercado executa somente o volume disponível e cancela o restante,
  liberando reservas. Uma venda exige saldo para toda a quantidade solicitada,
  mesmo quando há menos profundidade no livro.
- O livro contém somente ofertas externas. Não há casamento entre as próprias
  ordens pendentes, fila de prioridade, concorrência ou latência. Novas ofertas
  e o reprocessamento de ordens são eventos explícitos. A API do motor usa os
  identificadores `BUY`, `SELL`, `MARKET`, `LIMIT` e os estados acima.
- Valores monetários e quantidades são `Decimal` criados de strings, com
  precisão de 40 dígitos significativos e `ROUND_HALF_EVEN`. Não há conversão
  para float nem quantização por execução. Divisões periódicas respeitam essa
  precisão; a apresentação arredonda para até 12 casas decimais. O ponto é o
  separador decimal na saída, sem agrupamento de milhares.
- O motor é um exemplo em memória para uso sequencial. Ordens retornadas devem
  ser tratadas como registros de consulta; mudanças passam por `Simulator`.
- Não há regras de tick size, lote mínimo, mínimo nocional, descontos de taxa,
  persistência, integração de exchange ou avaliação de rentabilidade futura.
  As regras não reproduzem integralmente a Binance ou qualquer exchange.

Os resultados efetivamente executados estão em
[docs/sprint01-validacao.md](docs/sprint01-validacao.md).
