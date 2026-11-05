"""Agregação OHLCV no intervalo UTC [início, fim)."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from .market import ZERO, number, utc


@dataclass(frozen=True)
class Trade:
    time: datetime
    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        utc(self.time)
        number(self.price, "Preço")
        number(self.quantity, "Quantidade")


@dataclass(frozen=True)
class Candle:
    start: datetime
    end: datetime
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: Decimal
    closed: bool

    @classmethod
    def at(cls, start: datetime, trades: list[Trade], now: datetime) -> "Candle":
        utc(start)
        utc(now)
        if now < start:
            raise ValueError("Observação anterior ao início do candle")
        end = start + timedelta(minutes=1)
        visible = sorted((trade for trade in trades
                          if start <= trade.time < end and trade.time <= now),
                         key=lambda trade: trade.time)
        prices = [trade.price for trade in visible]
        return cls(start, end, prices[0] if prices else None, max(prices) if prices else None,
                   min(prices) if prices else None, prices[-1] if prices else None,
                   sum((trade.quantity for trade in visible), ZERO), now >= end)
