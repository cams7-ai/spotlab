"""Cenários determinísticos e relatórios em português."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .candles import Candle, Trade
from .market import Book, Kind, Level, Order, Side, Simulator, Wallet

D = Decimal
TIME = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def fmt(value: Decimal | None) -> str:
    if value is None:
        return "não aplicável"
    # Até 12 casas na apresentação; cálculos mantêm 40 dígitos significativos.
    return format(value, ".12f").rstrip("0").rstrip(".") or "0"


def wallet_report(wallet: Wallet) -> None:
    for asset in (wallet.pair.quote, wallet.pair.base):
        balance = wallet.balance(asset)
        print(f"  {asset}: disponível={fmt(balance.available)}; reservado={fmt(balance.reserved)}")


def order_report(order: Order, wallet: Wallet) -> None:
    pair = wallet.pair
    print(f"{order.side.value} {order.kind.value}: {order.status.value} — criada em {order.time.isoformat()}")
    print(f"  Solicitada={fmt(order.quantity)} {pair.base}; executada={fmt(order.filled)} {pair.base}; "
          f"restante={fmt(order.remaining)} {pair.base}")
    for index, execution in enumerate(order.executions, 1):
        print(f"  Execução {index}: {fmt(execution.quantity)} {pair.base} a "
              f"{fmt(execution.price)} {pair.quote}/{pair.base}; "
              f"taxa={fmt(execution.fee)} {pair.quote}; {execution.time.isoformat()}")
    label = "Desembolso total" if order.side == Side.BUY else "Recebimento líquido"
    print(f"  Valor bruto={fmt(order.gross)} {pair.quote}; taxas={fmt(order.fees)} {pair.quote}")
    print(f"  {label}={fmt(order.net)} {pair.quote}; preço médio={fmt(order.average)} {pair.quote}/{pair.base}")
    slippage = "não aplicável" if order.slippage is None else f"{fmt(order.slippage)}%"
    print(f"  Referência inicial={fmt(order.reference)} {pair.quote}/{pair.base}; "
          f"slippage desfavorável={slippage}")
    print(f"  Reserva da ordem={fmt(order.reserved)} "
          f"{pair.quote if order.side == Side.BUY else pair.base}")
    wallet_report(wallet)


def scenario_a() -> None:
    print("\nA. Par e custos de uma operação completa")
    wallet = Wallet(D("1000"), D("0"))
    wallet_report(wallet)
    sim = Simulator(wallet, Book([], [Level(D("100000"), D("0.001"))]))
    buy = sim.place(Side.BUY, Kind.MARKET, D("0.001"), TIME)
    order_report(buy, wallet)
    sim.book = Book([Level(D("101000"), D("0.001"))], [])
    sell = sim.place(Side.SELL, Kind.MARKET, D("0.001"), TIME + timedelta(minutes=1))
    order_report(sell, wallet)
    gross = sell.gross - buy.gross
    fees = buy.fees + sell.fees
    net = sell.net - buy.net
    print(f"Lucro bruto = venda - compra = {fmt(sell.gross)} - {fmt(buy.gross)} = {fmt(gross)} USDT")
    print(f"Taxas totais = {fmt(buy.fees)} + {fmt(sell.fees)} = {fmt(fees)} USDT")
    print(f"Lucro líquido = bruto - taxas = {fmt(gross)} - {fmt(fees)} = {fmt(net)} USDT")
    print(f"Retorno líquido = {fmt(net)} / {fmt(buy.net)} * 100 = {fmt(net / buy.net * D('100'))}%")
    print("Os preços executados já incorporam spread e slippage; não desconte esses custos novamente.")


def scenario_b() -> None:
    print("\nB. Bid, ask e spread")
    wallet = Wallet(D("1000"), D("0"))
    book = Book([Level(D("99990"), D("1"))], [Level(D("100010"), D("1"))])
    print(f"Bid (melhor compra)={fmt(book.bid)} USDT/BTC; ask (melhor venda)={fmt(book.ask)} USDT/BTC")
    print(f"Spread = ask - bid = {fmt(book.spread)} USDT/BTC")
    print(f"Spread percentual = (ask - bid) / ((ask + bid) / 2) * 100 = {fmt(book.spread_percent)}%")
    print("Denominador: ponto médio de 100000 USDT/BTC.")
    sim = Simulator(wallet, book)
    buy = sim.place(Side.BUY, Kind.MARKET, D("0.001"), TIME)
    order_report(buy, wallet)
    sell = sim.place(Side.SELL, Kind.MARKET, D("0.001"), TIME + timedelta(seconds=1))
    order_report(sell, wallet)
    print(f"Resultado bruto antes de taxas = {fmt(sell.gross - buy.gross)} USDT")
    print(f"Resultado líquido após taxas = {fmt(sell.net - buy.net)} USDT")


def depth_book() -> Book:
    return Book([], [Level(D("100000"), D("0.0006")), Level(D("100100"), D("0.0004"))])


def scenario_c() -> None:
    print("\nC. Profundidade e slippage")
    wallet = Wallet(D("1000"), D("0"))
    sim = Simulator(wallet, depth_book())
    order_report(sim.place(Side.BUY, Kind.MARKET, D("0.001"), TIME), wallet)
    print("Preço médio = soma(preço * quantidade) / quantidade executada.")
    print("Slippage de compra = (preço médio - ask inicial) / ask inicial * 100.")
    print("Slippage de venda = (bid inicial - preço médio) / bid inicial * 100.")
    print("Slippage positivo significa execução pior; negativo significa execução melhor.")
    print("Novo experimento independente: compra de 0.002 BTC com apenas 0.001 BTC disponível.")
    wallet = Wallet(D("1000"), D("0"))
    sim = Simulator(wallet, depth_book())
    order_report(sim.place(Side.BUY, Kind.MARKET, D("0.002"), TIME), wallet)
    print("Convenção didática: executa o disponível e cancela o restante, liberando reservas.")


def scenario_d() -> None:
    print("\nD. Ordem limitada e reserva")
    wallet = Wallet(D("1000"), D("0"))
    book = Book([], [Level(D("100010"), D("1"))])
    sim = Simulator(wallet, book)
    order = sim.place(Side.BUY, Kind.LIMIT, D("0.001"), TIME, D("99900"))
    order_report(order, wallet)
    event = TIME + timedelta(seconds=10)
    print(f"Evento externo {event.isoformat()}: oferta de venda de 0.0004 BTC a 99900 USDT/BTC.")
    book.add(Side.SELL, Level(D("99900"), D("0.0004")), event)
    sim.process(order, event)
    order_report(order, wallet)
    print("Cancelamento dos 0.0006 BTC restantes; somente a reserva restante é liberada.")
    sim.cancel(order, TIME + timedelta(seconds=20))
    order_report(order, wallet)


def candle_report(candle: Candle) -> None:
    print(f"Candle [{candle.start.isoformat()}, {candle.end.isoformat()}) — "
          f"{'FECHADO' if candle.closed else 'ABERTO'}")
    print(f"  O={fmt(candle.open)}; H={fmt(candle.high)}; L={fmt(candle.low)}; "
          f"C={fmt(candle.close)} USDT/BTC; volume={fmt(candle.volume)} BTC")


def scenario_e() -> None:
    print("\nE. Candle aberto e fechado")
    trades = [Trade(TIME + timedelta(seconds=seconds), D(price), D(quantity))
              for seconds, price, quantity in [(0, "100000", "0.001"), (20, "100100", "0.002"),
                                               (40, "99900", "0.003"), (50, "100050", "0.004"),
                                               (60, "101000", "0.005")]]
    for trade in trades:
        print(f"Negociação {trade.time.isoformat()}: {fmt(trade.quantity)} BTC a {fmt(trade.price)} USDT/BTC")
    for seconds in (20, 50, 60):
        now = TIME + timedelta(seconds=seconds)
        print(f"Observação em {now.isoformat()}:")
        candle_report(Candle.at(TIME, trades, now))
    print("A negociação exatamente no fim pertence ao próximo candle:")
    candle_report(Candle.at(TIME + timedelta(minutes=1), trades, TIME + timedelta(minutes=1)))
    print("OHLCV não revela toda a sequência intraperíodo nem qual de dois níveis de saída foi atingido primeiro.")


SCENARIOS = dict(zip("abcde", (scenario_a, scenario_b, scenario_c, scenario_d, scenario_e)))
