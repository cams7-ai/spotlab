"""Interface de terminal: python -m spotlab."""

import argparse

from .scenarios import SCENARIOS


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m spotlab", add_help=False,
                                     description="SpotLab: cenários fictícios de mercado Spot, executados localmente.")
    parser._optionals.title = "Opções"
    parser.add_argument("-h", "--help", action="help", help="Mostra esta ajuda e encerra.")
    parser.add_argument("--cenario", choices=list(SCENARIOS), metavar="{a,b,c,d,e}",
                        help="Executa somente o cenário escolhido; por padrão executa todos.")
    args = parser.parse_args()
    print("SpotLab — BTC/USDT: BTC é o ativo base; USDT é o ativo de cotação.")
    print("USDT busca acompanhar o dólar, mas não é o próprio dólar. Sem margem ou alavancagem.")
    print("Dados fictícios; sem rede, credenciais ou dinheiro real.")
    print("Taxa fictícia: 0.10% em USDT na compra e na venda, sem distinção maker/taker.")
    print("Valor bruto = soma(preço * quantidade); taxa = bruto * 0.001.")
    print("Desembolso de compra = bruto + taxa; recebimento líquido de venda = bruto - taxa.")
    print("Decimal: 40 dígitos significativos, ROUND_HALF_EVEN; apresentação com até 12 casas decimais.")
    print("O livro contém ofertas externas; sem casamento de ordens próprias, fila, concorrência ou latência.")
    print("As convenções não reproduzem integralmente as regras da Binance ou de outra exchange.")
    selected = [args.cenario] if args.cenario else SCENARIOS
    for key in selected:
        SCENARIOS[key]()


if __name__ == "__main__":
    main()
