"""Livro externo, carteira e execução sem rede ou dependências externas."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from enum import Enum

# Precisão significativa de cálculo; nenhuma quantização financeira por execução.
getcontext().prec = 40
getcontext().rounding = ROUND_HALF_EVEN
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")
DEFAULT_FEE = Decimal("0.001")


def number(value: Decimal, name: str, *, positive: bool = True) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} deve ser Decimal finito criado a partir de string")
    if value < ZERO or (positive and value == ZERO):
        raise ValueError(f"{name} deve ser {'positivo' if positive else 'não negativo'}")


def utc(time: datetime) -> None:
    if not isinstance(time, datetime) or time.utcoffset() != timedelta(0):
        raise ValueError("O horário deve ter fuso UTC")


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Kind(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class Status(str, Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"


@dataclass(frozen=True)
class Pair:
    base: str = "BTC"
    quote: str = "USDT"

    def __post_init__(self) -> None:
        if not self.base or not self.quote or self.base == self.quote:
            raise ValueError("O par precisa de dois ativos distintos")


@dataclass(frozen=True)
class Level:
    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        number(self.price, "Preço")
        number(self.quantity, "Quantidade")


class Book:
    """Somente ofertas externas; níveis esgotados são removidos."""

    def __init__(self, bids: list[Level], asks: list[Level]) -> None:
        self._bids = sorted(bids, key=lambda level: level.price, reverse=True)
        self._asks = sorted(asks, key=lambda level: level.price)

    @property
    def bids(self) -> tuple[Level, ...]:
        return tuple(self._bids)

    @property
    def asks(self) -> tuple[Level, ...]:
        return tuple(self._asks)

    @property
    def bid(self) -> Decimal | None:
        return self._bids[0].price if self._bids else None

    @property
    def ask(self) -> Decimal | None:
        return self._asks[0].price if self._asks else None

    @property
    def spread(self) -> Decimal | None:
        return self.ask - self.bid if self.ask is not None and self.bid is not None else None

    @property
    def spread_percent(self) -> Decimal | None:
        if self.ask is None or self.bid is None:
            return None
        return (self.ask - self.bid) / ((self.ask + self.bid) / Decimal("2")) * HUNDRED

    def add(self, side: Side, level: Level, time: datetime) -> None:
        utc(time)
        side = Side(side)
        levels = self._bids if side == Side.BUY else self._asks
        levels.append(level)
        levels.sort(key=lambda item: item.price, reverse=side == Side.BUY)


@dataclass(frozen=True)
class Balance:
    available: Decimal = ZERO
    reserved: Decimal = ZERO

    def __post_init__(self) -> None:
        number(self.available, "Saldo disponível", positive=False)
        number(self.reserved, "Saldo reservado", positive=False)


class Wallet:
    def __init__(self, quote: Decimal, base: Decimal, pair: Pair = Pair()) -> None:
        self.pair = pair
        self._balances = {pair.quote: Balance(quote), pair.base: Balance(base)}

    def balance(self, asset: str) -> Balance:
        return self._balances[asset]

    def _change(self, asset: str, available: Decimal = ZERO, reserved: Decimal = ZERO) -> None:
        old = self.balance(asset)
        self._balances[asset] = Balance(old.available + available, old.reserved + reserved)


@dataclass(frozen=True)
class Execution:
    time: datetime
    price: Decimal
    quantity: Decimal
    fee: Decimal

    @property
    def gross(self) -> Decimal:
        return self.price * self.quantity


@dataclass
class Order:
    side: Side
    kind: Kind
    quantity: Decimal
    limit: Decimal | None
    time: datetime
    reference: Decimal | None
    fee_rate: Decimal
    status: Status = Status.NEW
    reserved: Decimal = ZERO
    executions: list[Execution] = field(default_factory=list)

    @property
    def filled(self) -> Decimal:
        return sum((item.quantity for item in self.executions), ZERO)

    @property
    def remaining(self) -> Decimal:
        return self.quantity - self.filled

    @property
    def gross(self) -> Decimal:
        return sum((item.gross for item in self.executions), ZERO)

    @property
    def fees(self) -> Decimal:
        return sum((item.fee for item in self.executions), ZERO)

    @property
    def net(self) -> Decimal:
        """Desembolso de compra ou recebimento de venda, em cotação."""
        return self.gross + self.fees if self.side == Side.BUY else self.gross - self.fees

    @property
    def average(self) -> Decimal | None:
        return self.gross / self.filled if self.filled else None

    @property
    def slippage(self) -> Decimal | None:
        average = self.average
        if average is None or self.reference is None:
            return None
        difference = average - self.reference if self.side == Side.BUY else self.reference - average
        return difference / self.reference * HUNDRED


class Simulator:
    def __init__(self, wallet: Wallet, book: Book, fee_rate: Decimal = DEFAULT_FEE) -> None:
        number(fee_rate, "Taxa", positive=False)
        if fee_rate >= ONE:
            raise ValueError("Taxa deve ser menor que 1")
        self.wallet = wallet
        self.book = book
        self.fee_rate = fee_rate
        self._orders: list[Order] = []

    def _plan(self, side: Side, quantity: Decimal, limit: Decimal | None) -> list[Level]:
        plan = []
        levels = self.book.asks if side == Side.BUY else self.book.bids
        for level in levels:
            if limit is not None and ((side == Side.BUY and level.price > limit)
                                      or (side == Side.SELL and level.price < limit)):
                break
            take = min(quantity, level.quantity)
            if take == ZERO:
                break
            plan.append(Level(level.price, take))
            quantity -= take
        return plan

    def place(self, side: Side, kind: Kind, quantity: Decimal, time: datetime,
              limit: Decimal | None = None) -> Order:
        side, kind = Side(side), Kind(kind)
        number(quantity, "Quantidade")
        utc(time)
        if kind == Kind.LIMIT:
            number(limit, "Preço limite")
        elif limit is not None:
            raise ValueError("Ordem a mercado não recebe preço limite")
        plan = self._plan(side, quantity, limit)
        if side == Side.SELL:
            reserve = quantity
            asset = self.wallet.pair.base
        else:
            gross = limit * quantity if limit is not None else sum(
                (level.price * level.quantity for level in plan), ZERO)
            reserve = gross * (ONE + self.fee_rate)
            asset = self.wallet.pair.quote
        if self.wallet.balance(asset).available < reserve:
            raise ValueError(f"Saldo insuficiente em {asset}; ordem rejeitada integralmente")
        order = Order(side, kind, quantity, limit, time,
                      self.book.ask if side == Side.BUY else self.book.bid, self.fee_rate,
                      reserved=reserve)
        self.wallet._change(asset, -reserve, reserve)
        self._orders.append(order)
        self.process(order, time)
        return order

    def _check(self, order: Order, time: datetime) -> None:
        utc(time)
        if not any(existing is order for existing in self._orders):
            raise ValueError("Ordem não pertence a este simulador")
        last_time = order.executions[-1].time if order.executions else order.time
        if time < last_time:
            raise ValueError("Evento anterior ao último evento da ordem")

    def process(self, order: Order, time: datetime) -> None:
        self._check(order, time)
        if order.status in (Status.FILLED, Status.CANCELED):
            return
        for level in self._plan(order.side, order.remaining, order.limit):
            gross = level.price * level.quantity
            fee = gross * order.fee_rate
            if order.side == Side.BUY:
                allocation = (order.limit * level.quantity * (ONE + order.fee_rate)
                              if order.limit is not None else gross + fee)
                self.wallet._change(self.wallet.pair.quote, allocation - gross - fee, -allocation)
                self.wallet._change(self.wallet.pair.base, level.quantity)
                order.reserved -= allocation
            else:
                self.wallet._change(self.wallet.pair.base, reserved=-level.quantity)
                self.wallet._change(self.wallet.pair.quote, gross - fee)
                order.reserved -= level.quantity
            levels = self.book._asks if order.side == Side.BUY else self.book._bids
            current = levels[0]
            if current.quantity == level.quantity:
                levels.pop(0)
            else:
                levels[0] = Level(current.price, current.quantity - level.quantity)
            order.executions.append(Execution(time, level.price, level.quantity, fee))
        if order.remaining == ZERO:
            order.status = Status.FILLED
            self._release(order)
        elif order.kind == Kind.MARKET:
            self.cancel(order, time)
        elif order.filled:
            order.status = Status.PARTIALLY_FILLED

    def _release(self, order: Order) -> None:
        asset = self.wallet.pair.quote if order.side == Side.BUY else self.wallet.pair.base
        self.wallet._change(asset, order.reserved, -order.reserved)
        order.reserved = ZERO

    def cancel(self, order: Order, time: datetime) -> None:
        self._check(order, time)
        if order.status in (Status.FILLED, Status.CANCELED):
            return
        self._release(order)
        order.status = Status.CANCELED
