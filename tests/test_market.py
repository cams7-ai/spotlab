"""Verifica resultados observáveis, sem rede e sem tolerâncias de float."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import unittest

from spotlab.candles import Candle, Trade
from spotlab.market import Balance, Book, Kind, Level, Pair, Side, Simulator, Status, Wallet

D = Decimal
T = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def book(bids: tuple = (), asks: tuple = ()) -> Book:
    return Book([Level(D(p), D(q)) for p, q in bids], [Level(D(p), D(q)) for p, q in asks])


class MarketTests(unittest.TestCase):
    def snapshot(self, sim: Simulator) -> tuple:
        return (sim.wallet.balance("BTC"), sim.wallet.balance("USDT"), sim.book.bids, sim.book.asks)

    def assert_balances(self, wallet: Wallet, quote: str, base: str,
                        reserved_quote: str = "0", reserved_base: str = "0") -> None:
        self.assertEqual(wallet.balance("USDT"), Balance(D(quote), D(reserved_quote)))
        self.assertEqual(wallet.balance("BTC"), Balance(D(base), D(reserved_base)))

    def test_a_complete_operation(self) -> None:
        wallet = Wallet(D("1000"), D("0"))
        sim = Simulator(wallet, book(asks=(("100000", "0.001"),)))
        buy = sim.place(Side.BUY, Kind.MARKET, D("0.001"), T)
        self.assertEqual((buy.gross, buy.fees, buy.net), (D("100"), D("0.1"), D("100.1")))
        self.assertEqual((buy.status, buy.filled, buy.remaining), (Status.FILLED, D("0.001"), D("0")))
        self.assert_balances(wallet, "899.9", "0.001")
        sim.book = book(bids=(("101000", "0.001"),))
        sell = sim.place(Side.SELL, Kind.MARKET, D("0.001"), T + timedelta(minutes=1))
        self.assertEqual((sell.gross, sell.fees, sell.net), (D("101"), D("0.101"), D("100.899")))
        self.assertEqual(sell.gross - buy.gross, D("1"))
        self.assertEqual(sell.fees + buy.fees, D("0.201"))
        self.assertEqual(sell.net - buy.net, D("0.799"))
        result = (sell.net - buy.net) / buy.net * D("100")
        self.assertEqual(result.quantize(D("0.000001")), D("0.798202"))
        self.assert_balances(wallet, "1000.799", "0")

    def test_b_spread_round_trip(self) -> None:
        wallet = Wallet(D("1000"), D("0"))
        sim = Simulator(wallet, book(bids=(("99990", "1"),), asks=(("100010", "1"),)))
        self.assertEqual(sim.book.spread, D("20"))
        self.assertEqual(sim.book.spread_percent, D("0.02"))
        buy = sim.place(Side.BUY, Kind.MARKET, D("0.001"), T)
        sell = sim.place(Side.SELL, Kind.MARKET, D("0.001"), T)
        self.assertEqual(sell.gross - buy.gross, D("-0.02"))
        self.assertEqual(sell.net - buy.net, D("-0.22"))
        self.assert_balances(wallet, "999.78", "0")
        self.assertEqual((sim.book.asks[0].quantity, sim.book.bids[0].quantity), (D("0.999"), D("0.999")))

    def test_c_depth_and_slippage(self) -> None:
        wallet = Wallet(D("1000"), D("0"))
        sim = Simulator(wallet, book(asks=(("100100", "0.0004"), ("100000", "0.0006"))))
        order = sim.place(Side.BUY, Kind.MARKET, D("0.001"), T)
        self.assertEqual([(e.price, e.quantity) for e in order.executions],
                         [(D("100000"), D("0.0006")), (D("100100"), D("0.0004"))])
        self.assertEqual((order.gross, order.average, order.slippage), (D("100.04"), D("100040"), D("0.04")))
        self.assertEqual((order.fees, order.net), (D("0.10004"), D("100.14004")))
        self.assertEqual(sim.book.asks, ())
        self.assert_balances(wallet, "899.85996", "0.001")

    def test_d_limit_reserve_partial_and_cancel(self) -> None:
        wallet = Wallet(D("1000"), D("0"))
        sim = Simulator(wallet, book(asks=(("100010", "1"),)))
        order = sim.place(Side.BUY, Kind.LIMIT, D("0.001"), T, D("99900"))
        self.assertEqual((order.status, order.reserved, order.filled), (Status.NEW, D("99.9999"), D("0")))
        self.assert_balances(wallet, "900.0001", "0", "99.9999")
        sim.book.add(Side.SELL, Level(D("99900"), D("0.0004")), T + timedelta(seconds=10))
        sim.process(order, T + timedelta(seconds=10))
        self.assertEqual((order.status, order.filled, order.remaining),
                         (Status.PARTIALLY_FILLED, D("0.0004"), D("0.0006")))
        self.assertEqual(order.net, D("39.99996"))
        self.assertEqual(order.reserved, D("59.99994"))
        self.assert_balances(wallet, "900.0001", "0.0004", "59.99994")
        sim.cancel(order, T + timedelta(seconds=20))
        self.assertEqual((order.status, order.reserved), (Status.CANCELED, D("0")))
        self.assert_balances(wallet, "960.00004", "0.0004")
        self.assertEqual(sim.book.asks, (Level(D("100010"), D("1")),))
        before = self.snapshot(sim)
        sim.cancel(order, T + timedelta(seconds=21))
        sim.process(order, T + timedelta(seconds=21))
        self.assertEqual(self.snapshot(sim), before)

    def test_market_buy_insufficient_depth(self) -> None:
        wallet = Wallet(D("100.14004"), D("0"))
        sim = Simulator(wallet, book(asks=(("100000", "0.0006"), ("100100", "0.0004"))))
        order = sim.place(Side.BUY, Kind.MARKET, D("0.002"), T)
        self.assertEqual((order.status, order.filled, order.remaining), (Status.CANCELED, D("0.001"), D("0.001")))
        self.assertEqual(order.reserved, D("0"))
        self.assert_balances(wallet, "0", "0.001")

    def test_sell_multiple_levels_and_insufficient_depth(self) -> None:
        wallet = Wallet(D("0"), D("0.003"))
        sim = Simulator(wallet, book(bids=(("99000", "0.001"), ("100000", "0.001"))))
        order = sim.place(Side.SELL, Kind.MARKET, D("0.003"), T)
        self.assertEqual([e.price for e in order.executions], [D("100000"), D("99000")])
        self.assertEqual((order.gross, order.fees, order.net), (D("199"), D("0.199"), D("198.801")))
        self.assertEqual((order.average, order.slippage), (D("99500"), D("0.5")))
        self.assertEqual((order.status, order.remaining), (Status.CANCELED, D("0.001")))
        self.assertEqual(sim.book.bids, ())
        self.assert_balances(wallet, "198.801", "0.001")

    def test_limit_buy_better_price_releases_difference(self) -> None:
        wallet = Wallet(D("110.11"), D("0"))
        sim = Simulator(wallet, book(asks=(("100000", "0.0004"), ("120000", "1"))))
        order = sim.place(Side.BUY, Kind.LIMIT, D("0.001"), T, D("110000"))
        self.assertEqual(order.status, Status.PARTIALLY_FILLED)
        self.assert_balances(wallet, "4.004", "0.0004", "66.066")
        sim.book.add(Side.SELL, Level(D("105000"), D("0.0006")), T)
        sim.process(order, T)
        self.assertEqual(order.status, Status.FILLED)
        self.assertEqual(order.gross, D("103"))
        self.assertEqual(order.net, D("103.103"))
        self.assert_balances(wallet, "7.007", "0.001")
        self.assertEqual(sim.book.ask, D("120000"))

    def test_limit_sell_pending_partial_cancel(self) -> None:
        wallet = Wallet(D("0"), D("0.002"))
        sim = Simulator(wallet, book(bids=(("99000", "1"),)))
        order = sim.place(Side.SELL, Kind.LIMIT, D("0.002"), T, D("100000"))
        self.assertEqual(order.status, Status.NEW)
        self.assert_balances(wallet, "0", "0", reserved_base="0.002")
        sim.book.add(Side.BUY, Level(D("101000"), D("0.001")), T)
        sim.process(order, T)
        self.assertEqual((order.status, order.net), (Status.PARTIALLY_FILLED, D("100.899")))
        self.assert_balances(wallet, "100.899", "0", reserved_base="0.001")
        self.assertEqual(order.slippage, (D("99000") - D("101000")) / D("99000") * D("100"))
        sim.cancel(order, T)
        self.assert_balances(wallet, "100.899", "0.001")
        self.assertEqual(sim.book.bid, D("99000"))

    def test_limit_sell_full_at_existing_price(self) -> None:
        wallet = Wallet(D("0"), D("0.001"))
        sim = Simulator(wallet, book(bids=(("101000", "1"),)))
        order = sim.place(Side.SELL, Kind.LIMIT, D("0.001"), T, D("100000"))
        self.assertEqual((order.status, order.average), (Status.FILLED, D("101000")))
        self.assert_balances(wallet, "100.899", "0")
        before = self.snapshot(sim)
        sim.cancel(order, T)
        self.assertEqual(self.snapshot(sim), before)
        self.assertEqual(order.status, Status.FILLED)

    def test_insufficient_funds_rejected_without_mutation(self) -> None:
        for side, kind, quantity, limit in [
            (Side.BUY, Kind.MARKET, "0.002", None),
            (Side.BUY, Kind.LIMIT, "0.001", D("100000")),
            (Side.SELL, Kind.MARKET, "0.002", None),
            (Side.SELL, Kind.LIMIT, "0.002", D("100000")),
        ]:
            with self.subTest(side=side, kind=kind):
                sim = Simulator(Wallet(D("100"), D("0.001")),
                                book(bids=(("100000", "1"),), asks=(("100000", "0.001"), ("101000", "1"))))
                before = self.snapshot(sim)
                with self.assertRaises(ValueError):
                    sim.place(side, kind, D(quantity), T, limit)
                self.assertEqual(self.snapshot(sim), before)

    def test_pending_reserves_cannot_be_spent_again(self) -> None:
        sim = Simulator(Wallet(D("100.1"), D("0.001")), book())
        buy = sim.place(Side.BUY, Kind.LIMIT, D("0.001"), T, D("100000"))
        sell = sim.place(Side.SELL, Kind.LIMIT, D("0.001"), T, D("100000"))
        # Ordens próprias não se casam nem entram no livro externo.
        self.assertEqual((buy.status, sell.status), (Status.NEW, Status.NEW))
        self.assertEqual((sim.book.bids, sim.book.asks), ((), ()))
        before = self.snapshot(sim)
        for side in Side:
            with self.assertRaises(ValueError):
                sim.place(side, Kind.LIMIT, D("0.001"), T, D("100000"))
            self.assertEqual(self.snapshot(sim), before)
        sim.cancel(buy, T)
        sim.cancel(sell, T)
        self.assert_balances(sim.wallet, "100.1", "0.001")

    def test_empty_market_cancels_and_releases(self) -> None:
        for side in Side:
            sim = Simulator(Wallet(D("1000"), D("1")), book())
            before = self.snapshot(sim)
            order = sim.place(side, Kind.MARKET, D("0.001"), T)
            self.assertEqual(order.status, Status.CANCELED)
            self.assertIsNone(order.average)
            self.assertIsNone(order.slippage)
            self.assertEqual(order.reserved, D("0"))
            self.assertEqual(self.snapshot(sim), before)
            self.assertIsNone(sim.book.spread)
            self.assertIsNone(sim.book.spread_percent)

    def test_invalid_orders_leave_everything_unchanged(self) -> None:
        sim = Simulator(Wallet(D("1000"), D("1")), book(asks=(("100000", "1"),)))
        before = self.snapshot(sim)
        for value in (D("0"), D("-1"), D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity"), "1", 1):
            with self.subTest(value=str(value)):
                with self.assertRaises(ValueError):
                    sim.place(Side.BUY, Kind.MARKET, value, T)
                with self.assertRaises(ValueError):
                    sim.place(Side.BUY, Kind.LIMIT, D("0.001"), T, value)
                self.assertEqual(self.snapshot(sim), before)
        for side, kind, time, limit in [("invalid", Kind.MARKET, T, None),
                                        (Side.BUY, "invalid", T, None),
                                        (Side.BUY, Kind.LIMIT, T, None),
                                        (Side.BUY, Kind.MARKET, T, D("100000")),
                                        (Side.BUY, Kind.MARKET, T.replace(tzinfo=None), None)]:
            with self.assertRaises(ValueError):
                sim.place(side, kind, D("0.001"), time, limit)
            self.assertEqual(self.snapshot(sim), before)

    def test_invalid_balances_levels_fees(self) -> None:
        for invalid in (D("-1"), D("NaN"), D("Infinity"), D("sNaN")):
            with self.subTest(value=str(invalid)):
                for available, reserved in ((invalid, D("0")), (D("0"), invalid)):
                    with self.assertRaises(ValueError):
                        Balance(available, reserved)
                with self.assertRaises(ValueError):
                    Wallet(invalid, D("0"))
                with self.assertRaises(ValueError):
                    Wallet(D("0"), invalid)
        for invalid in (D("0"), D("-1"), D("NaN"), D("Infinity")):
            with self.assertRaises(ValueError):
                Level(invalid, D("1"))
            with self.assertRaises(ValueError):
                Level(D("1"), invalid)
        for invalid in (D("-0.001"), D("1"), D("2"), D("NaN"), D("Infinity")):
            with self.assertRaises(ValueError):
                Simulator(Wallet(D("1"), D("1")), book(), invalid)
        with self.assertRaises(ValueError):
            Pair("BTC", "BTC")

    def test_zero_fee(self) -> None:
        wallet = Wallet(D("100"), D("0"))
        sim = Simulator(wallet, book(asks=(("100000", "0.001"),)), D("0"))
        order = sim.place(Side.BUY, Kind.MARKET, D("0.001"), T)
        self.assertEqual(order.fees, D("0"))
        self.assert_balances(wallet, "0", "0.001")

    def test_foreign_order_and_past_event_rejected(self) -> None:
        sim = Simulator(Wallet(D("1000"), D("0")), book())
        order = sim.place(Side.BUY, Kind.LIMIT, D("0.001"), T, D("100000"))
        other = Simulator(Wallet(D("1000"), D("0")), book())
        before = self.snapshot(sim)
        with self.assertRaises(ValueError):
            other.process(order, T)
        with self.assertRaises(ValueError):
            sim.cancel(order, T - timedelta(seconds=1))
        self.assertEqual(self.snapshot(sim), before)


class CandleTests(unittest.TestCase):
    def test_open_closed_and_exclusive_end(self) -> None:
        trades = [Trade(T + timedelta(seconds=s), D(p), D(q)) for s, p, q in
                  [(50, "100050", "0.004"), (0, "100000", "0.001"), (20, "100100", "0.002"),
                   (40, "99900", "0.003"), (60, "101000", "0.005"), (-1, "1", "1")]]
        opened = Candle.at(T, trades, T + timedelta(seconds=20))
        self.assertFalse(opened.closed)
        self.assertEqual((opened.open, opened.high, opened.low, opened.close, opened.volume),
                         (D("100000"), D("100100"), D("100000"), D("100100"), D("0.003")))
        updated = Candle.at(T, trades, T + timedelta(seconds=50))
        self.assertFalse(updated.closed)
        closed = Candle.at(T, trades, T + timedelta(minutes=1))
        self.assertTrue(closed.closed)
        self.assertEqual((closed.open, closed.high, closed.low, closed.close, closed.volume),
                         (D("100000"), D("100100"), D("99900"), D("100050"), D("0.01")))
        self.assertEqual((updated.open, updated.high, updated.low, updated.close, updated.volume),
                         (closed.open, closed.high, closed.low, closed.close, closed.volume))
        self.assertEqual(Candle.at(T, trades, T + timedelta(minutes=2)), closed)
        following = Candle.at(T + timedelta(minutes=1), trades, T + timedelta(minutes=1))
        self.assertEqual((following.open, following.volume), (D("101000"), D("0.005")))
        self.assertFalse(following.closed)

    def test_empty_candle(self) -> None:
        candle = Candle.at(T, [], T)
        self.assertEqual((candle.open, candle.high, candle.low, candle.close, candle.volume),
                         (None, None, None, None, D("0")))

    def test_invalid_trade_and_time(self) -> None:
        for value in (D("0"), D("-1"), D("NaN"), D("Infinity")):
            with self.assertRaises(ValueError):
                Trade(T, value, D("1"))
            with self.assertRaises(ValueError):
                Trade(T, D("1"), value)
        with self.assertRaises(ValueError):
            Trade(T.replace(tzinfo=None), D("1"), D("1"))
        with self.assertRaises(ValueError):
            Candle.at(T, [], T - timedelta(seconds=1))
        with self.assertRaises(ValueError):
            Candle.at(T.replace(tzinfo=None), [], T)


if __name__ == "__main__":
    unittest.main()
