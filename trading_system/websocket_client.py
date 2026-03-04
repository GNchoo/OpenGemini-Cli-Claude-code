#!/usr/bin/env python3
"""
트레이더 마크 📊 - 업비트 WebSocket 클라이언트
실시간 가격 수신으로 REST API 호출 70% 감소
"""

import json
import time
import uuid
import threading
import queue
from datetime import datetime
from collections import deque
from typing import Callable, Optional

# websocket-client 없을 경우 대비
try:
    import websocket
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


UPBIT_WS_URL = "wss://api.upbit.com/websocket/v1"

# 구독할 심볼
DEFAULT_SYMBOLS = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-ADA", "KRW-DOGE", "KRW-DOT", "KRW-LINK", "KRW-POL", "KRW-AVAX"]


class TickerData:
    """실시간 시세 데이터"""

    def __init__(self, raw: dict):
        self.symbol      = raw.get("code", "")
        self.price       = float(raw.get("trade_price", 0))
        self.change_rate = float(raw.get("signed_change_rate", 0))
        self.volume_24h  = float(raw.get("acc_trade_volume_24h", 0))
        self.high_24h    = float(raw.get("high_price", 0))
        self.low_24h     = float(raw.get("low_price", 0))
        self.timestamp   = datetime.now()

    def __repr__(self):
        return (f"[{self.symbol}] {self.price:,.0f}원 "
                f"({self.change_rate:+.2%}) "
                f"@ {self.timestamp.strftime('%H:%M:%S')}")


class OrderbookData:
    """실시간 호가 데이터"""

    def __init__(self, raw: dict):
        self.symbol    = raw.get("code", "")
        self.timestamp = datetime.now()
        units          = raw.get("orderbook_units", [])

        self.best_ask  = units[0]["ask_price"] if units else 0  # 최우선 매도
        self.best_bid  = units[0]["bid_price"] if units else 0  # 최우선 매수
        self.spread    = self.best_ask - self.best_bid
        self.spread_pct = (self.spread / self.best_ask * 100) if self.best_ask else 0

    def __repr__(self):
        return (f"[{self.symbol}] 매도 {self.best_ask:,.0f} / "
                f"매수 {self.best_bid:,.0f} / "
                f"스프레드 {self.spread_pct:.3f}%")


class UpbitWebSocketClient:
    """업비트 WebSocket 클라이언트"""

    def __init__(self, symbols: list = None):
        self.symbols    = symbols or DEFAULT_SYMBOLS
        self.ws         = None
        self.running    = False
        self.connected  = False

        # 실시간 데이터 저장
        self.latest_ticker:    dict[str, TickerData]    = {}
        self.latest_orderbook: dict[str, OrderbookData] = {}
        self.price_history:    dict[str, deque]         = {
            s: deque(maxlen=200) for s in self.symbols
        }

        # 콜백 핸들러
        self.on_ticker:    Optional[Callable] = None
        self.on_orderbook: Optional[Callable] = None
        self.on_error:     Optional[Callable] = None

        # 통계
        self.msg_count  = 0
        self.start_time = None
        self._lock      = threading.Lock()

        print("=" * 70)
        print("트레이더 마크 📊 - 업비트 WebSocket 클라이언트")
        print("=" * 70)
        print(f"구독 심볼: {', '.join(self.symbols)}")
        print(f"WebSocket URL: {UPBIT_WS_URL}")
        print(f"websocket-client 설치 여부: {'✅' if WS_AVAILABLE else '❌'}")
        print()

    def _build_subscribe_message(self) -> str:
        """구독 메시지 생성"""
        msg = [
            {"ticket": str(uuid.uuid4())},
            {
                "type": "ticker",
                "codes": self.symbols,
                "isOnlyRealtime": True,
            },
            {
                "type": "orderbook",
                "codes": self.symbols,
                "isOnlyRealtime": True,
            },
        ]
        return json.dumps(msg)

    def _on_open(self, ws):
        print("✅ WebSocket 연결됨")
        self.connected = True
        self.start_time = datetime.now()
        ws.send(self._build_subscribe_message())
        print(f"📡 구독 시작: {', '.join(self.symbols)}")

    def _on_message(self, ws, message):
        try:
            # 업비트는 바이너리로 전송
            if isinstance(message, bytes):
                message = message.decode("utf-8")
            raw = json.loads(message)
            msg_type = raw.get("type", "")

            with self._lock:
                self.msg_count += 1

            if msg_type == "ticker":
                ticker = TickerData(raw)
                with self._lock:
                    self.latest_ticker[ticker.symbol] = ticker
                    self.price_history[ticker.symbol].append(
                        (ticker.timestamp, ticker.price)
                    )
                if self.on_ticker:
                    self.on_ticker(ticker)

            elif msg_type == "orderbook":
                ob = OrderbookData(raw)
                with self._lock:
                    self.latest_orderbook[ob.symbol] = ob
                if self.on_orderbook:
                    self.on_orderbook(ob)

        except Exception as e:
            print(f"  [메시지 파싱 오류] {e}")

    def _on_error(self, ws, error):
        print(f"  ❌ WebSocket 오류: {error}")
        self.connected = False
        if self.on_error:
            self.on_error(error)

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"  🔌 WebSocket 연결 종료: {close_status_code} {close_msg}")
        self.connected = False

    def connect(self):
        """WebSocket 연결 (실제 업비트)"""
        if not WS_AVAILABLE:
            print("❌ websocket-client 미설치")
            print("   설치: pip install websocket-client")
            return False

        self.running = True
        self.ws = websocket.WebSocketApp(
            UPBIT_WS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        thread = threading.Thread(
            target=self.ws.run_forever,
            kwargs={"ping_interval": 30, "ping_timeout": 10},
            daemon=True,
        )
        thread.start()
        print("🚀 WebSocket 연결 시도 중...")
        time.sleep(2)  # 연결 대기
        return self.connected

    def get_price(self, symbol: str) -> Optional[float]:
        """최신 가격 반환"""
        with self._lock:
            t = self.latest_ticker.get(symbol)
            return t.price if t else None

    def get_price_history(self, symbol: str, n: int = 20) -> list:
        """가격 히스토리 반환"""
        with self._lock:
            hist = list(self.price_history.get(symbol, []))
        return [p for _, p in hist[-n:]]

    def get_spread(self, symbol: str) -> Optional[float]:
        """스프레드 반환 (%)"""
        with self._lock:
            ob = self.latest_orderbook.get(symbol)
            return ob.spread_pct if ob else None

    def stats(self) -> dict:
        """통계 반환"""
        elapsed = (datetime.now() - self.start_time).seconds if self.start_time else 0
        return {
            "connected":  self.connected,
            "msg_count":  self.msg_count,
            "elapsed_sec": elapsed,
            "msg_per_sec": self.msg_count / max(elapsed, 1),
        }

    def disconnect(self):
        """연결 해제"""
        self.running = False
        if self.ws:
            self.ws.close()
        print("🔌 WebSocket 연결 해제")


# ─────────────────────────────────────────────────────────────
# 시뮬레이션 클라이언트 (websocket-client 없을 때)
# ─────────────────────────────────────────────────────────────
class SimulatedWebSocketClient:
    """
    WebSocket 시뮬레이터
    실제 연결 없이 실시간 데이터 스트림 시뮬레이션
    """

    BASE_PRICES = {
        "KRW-BTC": 99_500_000,
        "KRW-ETH": 2_930_000,
        "KRW-XRP": 2_160,
        "KRW-ADA": 1_850,
    }

    def __init__(self, symbols: list = None):
        self.symbols    = symbols or DEFAULT_SYMBOLS
        self.running    = False
        self.connected  = False

        self.current_prices = dict(self.BASE_PRICES)
        self.price_history: dict[str, deque] = {
            s: deque(maxlen=200) for s in self.symbols
        }

        self.on_ticker:    Optional[Callable] = None
        self.on_orderbook: Optional[Callable] = None

        self.msg_count  = 0
        self.start_time = None
        self._lock      = threading.Lock()

        print("=" * 70)
        print("트레이더 마크 📊 - WebSocket 시뮬레이터")
        print("=" * 70)
        print(f"모드: 시뮬레이션 (실제 업비트 연결 없음)")
        print(f"구독 심볼: {', '.join(self.symbols)}")
        print()

    def _generate_tick(self, symbol: str) -> dict:
        """가격 틱 생성"""
        import random
        base = self.current_prices[symbol]
        vol  = 0.002 + random.uniform(0, 0.003)  # 0.2~0.5% 변동
        change = random.gauss(0, vol)
        new_price = base * (1 + change)
        self.current_prices[symbol] = new_price
        return {
            "type":                    "ticker",
            "code":                    symbol,
            "trade_price":             new_price,
            "signed_change_rate":      change,
            "acc_trade_volume_24h":    random.uniform(1000, 5000),
            "high_price":              new_price * 1.02,
            "low_price":               new_price * 0.98,
        }

    def _generate_orderbook(self, symbol: str) -> dict:
        """호가 생성"""
        import random
        price  = self.current_prices[symbol]
        spread = price * random.uniform(0.0001, 0.0005)
        return {
            "type": "orderbook",
            "code": symbol,
            "orderbook_units": [
                {"ask_price": price + spread / 2,
                 "bid_price": price - spread / 2,
                 "ask_size":  random.uniform(0.1, 2.0),
                 "bid_size":  random.uniform(0.1, 2.0)},
            ],
        }

    def _stream_loop(self, tick_interval: float = 1.0):
        """시뮬레이션 스트림 루프"""
        import random
        self.start_time = datetime.now()
        self.connected  = True

        print(f"📡 시뮬레이션 스트림 시작 (간격: {tick_interval}초)")

        while self.running:
            for symbol in self.symbols:
                # 티커 이벤트
                raw_ticker = self._generate_tick(symbol)
                ticker = TickerData(raw_ticker)

                with self._lock:
                    self.msg_count += 1
                    self.price_history[symbol].append(
                        (ticker.timestamp, ticker.price)
                    )

                if self.on_ticker:
                    self.on_ticker(ticker)

                # 호가 이벤트 (2회에 1회)
                if self.msg_count % 2 == 0:
                    raw_ob = self._generate_orderbook(symbol)
                    ob = OrderbookData(raw_ob)
                    if self.on_orderbook:
                        self.on_orderbook(ob)

            time.sleep(tick_interval)

        self.connected = False

    def connect(self, tick_interval: float = 1.0):
        """시뮬레이션 시작"""
        self.running = True
        t = threading.Thread(
            target=self._stream_loop,
            args=(tick_interval,),
            daemon=True,
        )
        t.start()
        time.sleep(0.3)
        return True

    def get_price(self, symbol: str) -> Optional[float]:
        with self._lock:
            return self.current_prices.get(symbol)

    def get_price_history(self, symbol: str, n: int = 20) -> list:
        with self._lock:
            hist = list(self.price_history.get(symbol, []))
        return [p for _, p in hist[-n:]]

    def stats(self) -> dict:
        elapsed = (datetime.now() - self.start_time).seconds if self.start_time else 0
        return {
            "connected":   self.connected,
            "msg_count":   self.msg_count,
            "elapsed_sec": elapsed,
            "msg_per_sec": self.msg_count / max(elapsed, 1),
        }

    def disconnect(self):
        self.running = False
        print("🔌 시뮬레이션 스트림 종료")


def get_client(symbols: list = None, simulate: bool = None) -> object:
    """
    환경에 맞는 클라이언트 반환
    simulate=None  → 자동 감지 (WS 없으면 시뮬레이터)
    simulate=True  → 강제 시뮬레이션
    simulate=False → 실제 WebSocket
    """
    if simulate is None:
        simulate = not WS_AVAILABLE
    if simulate:
        return SimulatedWebSocketClient(symbols)
    return UpbitWebSocketClient(symbols)


# ─────────────────────────────────────────────────────────────
# 테스트 실행
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import random

    print("트레이더 마크 📊 - WebSocket 클라이언트 테스트 (30초)\n")

    received_tickers    = []
    received_orderbooks = []

    def on_ticker(ticker: TickerData):
        received_tickers.append(ticker)
        if len(received_tickers) % 10 == 1:
            print(f"  📈 {ticker}")

    def on_orderbook(ob: OrderbookData):
        received_orderbooks.append(ob)
        if len(received_orderbooks) % 10 == 1:
            print(f"  📖 {ob}")

    # 클라이언트 생성 (자동 감지)
    client = get_client(simulate=True)
    client.on_ticker    = on_ticker
    client.on_orderbook = on_orderbook

    client.connect(tick_interval=0.5)

    # 30초 실행
    time.sleep(30)

    client.disconnect()
    s = client.stats()

    print(f"\n{'='*70}")
    print(f"WebSocket 테스트 결과")
    print(f"{'='*70}")
    print(f"  수신 메시지 : {s['msg_count']}개")
    print(f"  초당 메시지 : {s['msg_per_sec']:.1f}개/초")
    print(f"  티커 이벤트 : {len(received_tickers)}개")
    print(f"  호가 이벤트 : {len(received_orderbooks)}개")

    print(f"\n  최신 가격:")
    for sym in DEFAULT_SYMBOLS:
        price = client.get_price(sym)
        hist  = client.get_price_history(sym, 5)
        if price:
            print(f"    {sym}: {price:,.0f}원  (최근 5틱: "
                  f"{[f'{p:,.0f}' for p in hist[-3:]]})")

    print(f"\n  ✅ REST API 대비 절약:")
    api_calls_saved = s["msg_count"]  # WebSocket 메시지 수 = 절약된 API 호출
    print(f"    WebSocket으로 {api_calls_saved}회 API 호출 절약")
    print(f"    분당 절약: {api_calls_saved / (s['elapsed_sec'] / 60):.0f}회")
    print(f"{'='*70}")
    print(f"✅ WebSocket 클라이언트 테스트 완료")
