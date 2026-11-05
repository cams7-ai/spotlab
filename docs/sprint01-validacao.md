# Sprint 01 — Validação

Validação local em **2026-11-05**, com **Python 3.12.14**, na raiz do repositório
`spotlab`. Não houve chamadas externas, uso de credenciais ou ordens reais.

## Passo a passo e comandos executados

Sem instalar dependências, executar na raiz:

```bash
python --version
python -m spotlab
python -m spotlab --cenario a
python -m spotlab --cenario b
python -m spotlab --cenario c
python -m spotlab --cenario d
python -m spotlab --cenario e
python -m spotlab --help
python -m unittest discover -s tests -v
```

Todos os comandos acima foram executados com código de saída **0**. A execução
conjunta exibiu os cinco cenários; cada seleção individual exibiu somente o seu
cenário, além do cabeçalho comum. A ajuda apresentou `--cenario {a,b,c,d,e}`.

Na conferência final, a execução conjunta foi repetida duas vezes e as saídas
foram comparadas integralmente: eram idênticas. Cada cenário individual também
foi comparado ao respectivo trecho da execução conjunta, com igualdade, e foi
confirmada a ausência dos demais cenários na seleção individual.

## Resultados esperados e efetivamente verificados

Valores abaixo usam ponto decimal, como a aplicação. Os testes comparam valores
`Decimal` exatos, exceto o retorno periódico, conferido em seis casas decimais.

| Cenário | Esperado | Verificado |
| --- | --- | --- |
| A — compra | Bruto 100; taxa 0.1; desembolso 100.1 USDT | Valores idênticos na CLI e nos testes |
| A — venda | Bruto 101; taxa 0.101; líquido 100.899 USDT | Valores idênticos na CLI e nos testes |
| A — resultado | Bruto 1; taxas 0.201; líquido 0.799 USDT | Valores idênticos na CLI e nos testes |
| A — saldos finais | 1000.799 USDT, 0 BTC, reservas zeradas | Conferidos na CLI e nos testes |
| A — retorno | Aproximadamente 0.798202% | CLI: 0.798201798202%; teste: 0.798202% em seis casas |
| B — spread | 20 USDT/BTC; 0.02% sobre ponto médio de 100000 USDT/BTC | Valores idênticos na CLI e nos testes |
| B — ida e volta | Perda bruta de 0.02 USDT | Resultado bruto −0.02 USDT; líquido −0.22 USDT; saldo 999.78 USDT |
| C — profundidade | Duas execuções de 0.0006 e 0.0004 BTC | Quantidades e preços conferidos; asks esgotados |
| C — custos | Bruto 100.04; taxa 0.10004; total 100.14004 USDT | Valores idênticos na CLI e nos testes |
| C — média/slippage | 100040 USDT/BTC; 0.04% | Valores idênticos na CLI e nos testes |
| C — falta de volume | Compra de 0.002 BTC executa 0.001 BTC e cancela 0.001 BTC | `CANCELED`, restante 0.001 BTC, reserva zero; sem execução além do livro |
| D — aceitação | `NEW`, reserva 99.9999 USDT | Conferido, disponível 900.0001 USDT |
| D — execução parcial | `PARTIALLY_FILLED`, 0.0004 BTC; débito 39.99996 USDT; reserva 59.99994 USDT | Valores e estado idênticos na CLI e nos testes |
| D — cancelamento | Cancelar 0.0006 BTC e liberar reserva restante | `CANCELED`, reserva zero; saldo 960.00004 USDT e 0.0004 BTC |
| E — aberto às 12:00:20 UTC | O=100000, H=100100, L=100000, C=100100; volume 0.003 BTC | Valores conferidos; `ABERTO` |
| E — fechado às 12:01:00 UTC | O=100000, H=100100, L=99900, C=100050; volume 0.01 BTC | Valores conferidos; `FECHADO` |
| E — negociação no fim | 101000 USDT/BTC e 0.005 BTC pertencem ao candle seguinte | Excluída do primeiro candle e incluída no próximo |

## Testes automatizados

`python -m unittest discover -s tests -v`: **19 testes aprovados**, resultado `OK`.

Além de A–E, foram verificados:

- Venda em vários níveis, preço médio e slippage de venda; cancelamento do
  restante quando falta volume e liberação do BTC não executado.
- Compra limitada com preço melhor que o limite, devolução da diferença,
  execução parcial e posterior conclusão.
- Venda limitada pendente, execução parcial, cancelamento e execução completa
  no preço da oferta existente.
- Repetir processamento/cancelamento de ordens terminais sem alterar saldos;
  rejeitar ordens de outro simulador e eventos anteriores à ordem.
- Reservas que impedem gastar o mesmo saldo novamente; ordens próprias não
  se casam nem alteram o livro externo.
- Saldo insuficiente em compra/venda, limitada/mercado, sem alteração da carteira
  ou do livro, incluindo taxas e profundidade além do primeiro nível.
- Livro vazio, slippage não aplicável, taxa zero, preços/quantidades inválidos,
  saldos negativos, NaN/infinito, taxas fora de `[0, 1)` e horários sem UTC.
- Candle vazio, ordenação temporal das negociações, exclusão das negociações
  futuras e anteriores ao intervalo, fechamento no fim e limite exclusivo.

## Limitações

A validação ocorreu em Python 3.12.14; o código declara Python >=3.11, mas não
foi executado em outras versões. O modelo usa precisão de 40 dígitos e não
representa regras completas de exchange. Não simula concorrência, latência,
prioridade, ordens próprias no livro ou condições reais de negociação.
Não há comandos de aceite pendentes.
