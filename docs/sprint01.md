# Sprint 01 — Mercado Spot e custos de operação

**Projeto fictício:** SpotLab  
**Diretório sugerido:** `spotlab`  
**Objetivo:** criar um exemplo didático em Python que demonstre compras e vendas no mercado Spot, execução de ordens e cálculo do resultado líquido.

Este projeto de estudo é independente do robô principal. Todos os preços, saldos, taxas e livros de ofertas serão fictícios. Esta sprint funciona localmente, sem credenciais, chamadas à Binance ou dinheiro real.

## 1. Conhecimentos trabalhados

- Par negociado, ativo base e ativo de cotação.
- Saldo disponível e saldo reservado.
- Bid, ask, spread e profundidade do livro de ofertas.
- Ordens a mercado e limitadas; execução total e parcial.
- Preço médio de execução e slippage.
- Taxas de compra e venda e resultado líquido.
- Candles OHLCV e diferença entre candle aberto e fechado.

## 2. Resultado esperado

Uma aplicação de terminal com cenários determinísticos, explicações em português e relatório dos saldos e custos. A execução deve permitir conferir os cálculos manualmente e repetir os mesmos resultados.

## 3. Prompt autossuficiente de execução

Copie o conteúdo do bloco abaixo para o agente responsável pela implementação.

````text
Você é um desenvolvedor Python experiente e deve implementar a Sprint 01 do projeto fictício SpotLab: um simulador didático de mercado Spot e custos de operação.

Implemente a aplicação e sua documentação. Não entregue apenas um plano. Trabalhe em um diretório próprio chamado spotlab, dentro do diretório de trabalho indicado pelo usuário ou, se não houver indicação, dentro do diretório atual. Não altere projetos vizinhos nem sobrescreva trabalho existente. Se spotlab já existir, inspecione seu conteúdo e preserve alterações alheias.

CONTEXTO E OBJETIVO

O usuário conhece desenvolvimento de software e está aprendendo os conceitos de negociação necessários para construir futuramente um robô de criptomoedas. Este exemplo deve ensinar a mecânica de mercado Spot sem margem ou alavancagem. USDT é o ativo de cotação e BTC é o ativo base. Explique que USDT busca acompanhar o dólar, mas não é o próprio dólar.

ESCOPO

1. Aplicação local de terminal em Python 3.11 ou superior, sem dependências de execução externas. Utilize unittest da biblioteca padrão para os testes.
2. Dados inteiramente fictícios e cenários reproduzíveis. Não use internet, API, SDK de exchange ou chaves de acesso durante a execução.
3. Não implemente estratégias de investimento, recomendações de compra, inteligência artificial, backtest, banco de dados, interface web, Docker ou AWS nesta sprint.
4. Utilize Decimal criado a partir de strings para preços, quantidades, taxas e saldos. Não converta esses valores para float. Declare precisão e política de arredondamento; arredonde apenas a apresentação, salvo quando uma regra explícita do simulador exigir ajuste.
5. Use datas com fuso UTC para os eventos. Use horários fixos nos cenários para garantir reprodução.
6. Mantenha o código simples, tipado e dividido apenas onde houver responsabilidade clara. Documentação e mensagens devem estar em português.

MODELO MÍNIMO

Represente par, níveis do livro de ofertas, carteira, ordem, execução e candle. Identifique preço, quantidade e moeda em todos os relatórios. Uma ordem pode produzir várias execuções, cada uma com preço e quantidade próprios.

Defina estados NEW, PARTIALLY_FILLED, FILLED e CANCELED. Ordens inválidas devem ser rejeitadas sem alterar a carteira ou o livro. Registre a quantidade solicitada, executada e restante.

REGRAS DO SIMULADOR

- Bid é a melhor oferta de compra; ask é a melhor oferta de venda.
- Spread absoluto = ask - bid.
- Spread percentual = (ask - bid) / ((ask + bid) / 2) * 100. Identifique explicitamente o denominador usado.
- Compras consomem asks do menor para o maior preço; vendas consomem bids do maior para o menor.
- Cada execução reduz a quantidade disponível no nível correspondente. Nunca execute volume inexistente.
- Ordem a mercado sem profundidade suficiente executa a parte disponível e cancela o restante, liberando reservas. Documente esta convenção didática; não a apresente como reprodução integral das regras da Binance.
- Ordem limitada de compra só executa a preço menor ou igual ao limite; venda só a preço maior ou igual ao limite.
- Limitadas compatíveis executam no preço da oferta existente. Quantidades restantes ficam pendentes com saldo reservado; cancelar libera somente a reserva restante.
- Para simplificar, compras são informadas em quantidade de BTC. Reserve o valor máximo necessário, incluindo taxa em USDT, antes de aceitar a ordem. Para ordens a mercado, calcule esse valor percorrendo a profundidade disponível. Rejeite por saldo insuficiente sem execuções ou mutações parciais.
- Venda reserva BTC; a taxa é descontada do valor recebido em USDT.
- Taxa fictícia padrão: Decimal("0.001"), equivalente a 0,10%, cobrada em USDT nas duas pontas, sem distinção entre maker e taker. Deixe esse modelo explícito.
- Preço médio = soma(preço * quantidade de cada execução) / quantidade total executada.
- Slippage desfavorável de compra (%) = (preço médio - ask de referência) / ask de referência * 100.
- Slippage desfavorável de venda (%) = (bid de referência - preço médio) / bid de referência * 100.
- Capture a referência antes de consumir o livro. Resultado positivo significa execução pior; negativo, melhor. Sem execução ou sem referência, apresente slippage como não aplicável.
- Não permita saldos disponíveis ou reservados negativos, quantidades/preços não positivos, valores NaN/infinito, taxa negativa ou taxa maior ou igual a 1.
- Não implemente casamento entre as próprias ordens pendentes. O livro representa ofertas externas; explique que não há fila de prioridade, concorrência ou simulação de latência.

CENÁRIOS OBRIGATÓRIOS

Cada cenário começa com uma carteira e um livro novos, sem compartilhar mutações com os demais.

A. Par e custos de uma operação completa
   Carteira inicial: 1.000 USDT e 0 BTC.
   Compra executada: 0,001 BTC a 100.000 USDT.
   Venda posterior executada: 0,001 BTC a 101.000 USDT, em um novo livro fictício.
   Taxa em cada ponta: 0,10%, paga em USDT.
   Resultados exatos esperados:
   - Valor de compra: 100 USDT; taxa: 0,1 USDT; desembolso: 100,1 USDT.
   - Valor de venda: 101 USDT; taxa: 0,101 USDT; recebimento líquido: 100,899 USDT.
   - Lucro bruto: 1 USDT; taxas totais: 0,201 USDT; lucro líquido: 0,799 USDT.
   - Saldo final: 1.000,799 USDT e 0 BTC, sem reservas.
   - Retorno líquido: 0,799 / 100,1 * 100, aproximadamente 0,798202%.
   Mostre fórmulas e explique que preços executados já incorporam os efeitos do spread e do slippage: não desconte esses custos novamente.

B. Bid, ask e spread
   Melhor bid: 99.990 USDT; melhor ask: 100.010 USDT.
   Spread esperado: 20 USDT e 0,02% sobre o ponto médio.
   Demonstre, em livro com volume suficiente, que comprar 0,001 BTC no ask e vender imediatamente no bid gera perda bruta de 0,02 USDT, antes das taxas.

C. Profundidade e slippage
   Asks: 0,0006 BTC a 100.000 USDT e 0,0004 BTC a 100.100 USDT.
   Compra a mercado de 0,001 BTC, com saldo suficiente.
   Esperado: duas execuções; valor bruto de 100,04 USDT; preço médio de 100.040 USDT; slippage de 0,04% contra o ask inicial; taxa de 0,10004 USDT; desembolso total de 100,14004 USDT.
   Mostre também uma ordem maior que a profundidade disponível e a regra de cancelamento do restante.

D. Ordem limitada e reserva
   Livro inicial com menor ask de 100.010 USDT.
   Compra limitada de 0,001 BTC a 99.900 USDT: fica NEW, com 99,9999 USDT reservados, incluindo taxa.
   Adicione, por evento explícito, uma oferta externa de 0,0004 BTC a 99.900 USDT e processe novamente a ordem.
   Esperado: PARTIALLY_FILLED, 0,0004 BTC comprados, débito de 39,99996 USDT e reserva restante de 59,99994 USDT.
   Cancele a quantidade restante de 0,0006 BTC e confira liberação integral da reserva, preservando a compra executada.

E. Candle aberto e fechado
   Use um candle fictício de um minuto, com início UTC fixo e intervalo [início, fim).
   Inclua negociações com horário, preço e quantidade. Calcule OHLC e volume em BTC a partir dessas negociações.
   Antes do fim do intervalo, novas negociações podem alterar o candle; no fim, ele é considerado fechado. Uma negociação exatamente no fim pertence ao próximo candle.
   Explique que OHLCV sozinho não revela toda a sequência intraperíodo, nem determina qual de dois níveis de saída foi atingido primeiro.

INTERFACE E ENTREGÁVEIS

- pyproject.toml com metadados básicos e versão mínima de Python.
- Pacote spotlab executável pelo comando python -m spotlab a partir da raiz do projeto.
- python -m spotlab deve executar todos os cenários; permita selecionar um por --cenario a, b, c, d ou e.
- python -m spotlab --help deve explicar a execução.
- Relatório de terminal deve separar valores brutos, taxas, resultado líquido, slippage, saldo disponível e saldo reservado. Mostre a precisão suficiente para conferir os valores esperados.
- README.md com objetivo, conceitos, estrutura, comandos, exemplo de saída e simplificações.
- docs/sprint01-validacao.md com passo a passo, resultados esperados e resultados efetivamente verificados, sem inventar execuções.
- Testes automatizados com unittest para regras financeiras e transições de estado.

VALIDAÇÃO E ACEITE

Execute python -m spotlab, cada cenário individualmente, --help e python -m unittest discover -s tests -v.
Valide os valores exatos dos cenários A, B, C e D com Decimal. Cubra venda em múltiplos níveis, compra/venda limitada, cancelamento e liberação de reservas, saldo insuficiente sem mutação, profundidade insuficiente e entradas inválidas. Verifique o limite temporal do candle.
Não crie testes que apenas repitam funções internas: confira resultados, saldos, quantidades e invariantes observáveis.
O exemplo estará concluído quando todos os cenários forem reproduzíveis, os cálculos estiverem corretos, os testes passarem e os comandos estiverem documentados.
Ao finalizar, informe arquivos criados, comandos executados, resultados e limitações. Se algo não puder ser executado, registre a causa e o comando pendente. Não faça commits, publique ou envie ordens externas sem solicitação.
````

## 4. Limites desta sprint

O SpotLab ensina a mecânica das operações; não avalia rentabilidade futura. Taxas e regras são convenções didáticas e não representam condições vigentes de uma exchange. A próxima etapa de estudo é Python aplicado ao robô: valores decimais, datas UTC, tipagem e tratamento de erros.
