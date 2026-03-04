#!/usr/bin/env python3
"""
트레이더 마크 📊 - 업비트 실제 API 클라이언트
계좌 조회 + 실시간 시세 + 주문 실행

개선사항 (2026-02-20)
- 하드코딩 키 제거
- A/B 멀티 계정 환경변수 지원
"""

import os
import jwt
import uuid
import hashlib
import requests
from urllib.parse import urlencode, unquote
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    # python-dotenv 없이도 최소 동작하도록 .env를 직접 파싱
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k and (k not in os.environ):
                    os.environ[k.strip()] = v.strip()

BASE_URL = "https://api.upbit.com/v1"


def _resolve_keys(account: str = "A", access_key: Optional[str] = None, secret_key: Optional[str] = None):
    """환경변수에서 업비트 API 키 조회.

    우선순위:
    1) 생성자 인자로 직접 전달
    2) UPBIT_ACCESS_KEY_{A|B}, UPBIT_SECRET_KEY_{A|B}
    3) 레거시 UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY (A만)
    """
    acc = (account or "A").upper()

    if access_key and secret_key:
        return access_key, secret_key

    if acc == "B":
        ak = access_key or os.getenv("UPBIT_ACCESS_KEY_B")
        sk = secret_key or os.getenv("UPBIT_SECRET_KEY_B")
    else:
        ak = access_key or os.getenv("UPBIT_ACCESS_KEY_A") or os.getenv("UPBIT_ACCESS_KEY")
        sk = secret_key or os.getenv("UPBIT_SECRET_KEY_A") or os.getenv("UPBIT_SECRET_KEY")

    return ak, sk


class UpbitLiveClient:
    """업비트 실거래 클라이언트"""

    def __init__(self, account: str = "A", access_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.account = (account or "A").upper()
        self.access_key, self.secret_key = _resolve_keys(self.account, access_key, secret_key)
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

        if not self.access_key or not self.secret_key:
            missing = []
            if not self.access_key:
                missing.append(f"UPBIT_ACCESS_KEY_{self.account}")
            if not self.secret_key:
                missing.append(f"UPBIT_SECRET_KEY_{self.account}")
            raise ValueError(f"Upbit {self.account} API 키가 누락되었습니다: {', '.join(missing)}")

    # ── 인증 토큰 생성 ──────────────────────────────────────
    def _token(self, query: dict = None) -> str:
        payload = {"access_key": self.access_key, "nonce": str(uuid.uuid4())}
        if query:
            query_str = unquote(urlencode(query, doseq=True))
            query_hash = hashlib.sha512(query_str.encode()).hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = "SHA512"
        return "Bearer " + jwt.encode(payload, self.secret_key, algorithm="HS256")

    def _get(self, endpoint: str, params: dict = None, auth: bool = False):
        headers = {}
        if auth:
            headers["Authorization"] = self._token(params)
        r = self.session.get(f"{BASE_URL}{endpoint}", params=params, headers=headers, timeout=5)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint: str, body: dict):
        headers = {"Authorization": self._token(body), "Content-Type": "application/json"}
        r = self.session.post(f"{BASE_URL}{endpoint}", json=body, headers=headers, timeout=5)
        r.raise_for_status()
        return r.json()

    def _delete(self, endpoint: str, params: dict):
        headers = {"Authorization": self._token(params)}
        r = self.session.delete(f"{BASE_URL}{endpoint}", params=params, headers=headers, timeout=5)
        r.raise_for_status()
        return r.json()

    # ── 공개 API (인증 불필요) ──────────────────────────────
    def get_ticker(self, markets: list) -> list:
        return self._get("/ticker", {"markets": ",".join(markets)})

    def get_candles(self, market: str, unit: int = 5, count: int = 200) -> list:
        return self._get(f"/candles/minutes/{unit}", {"market": market, "count": count})

    def get_orderbook(self, markets: list) -> list:
        return self._get("/orderbook", {"markets": ",".join(markets)})

    # ── 인증 API ────────────────────────────────────────────
    def get_accounts(self) -> list:
        return self._get("/accounts", auth=True)

    def get_orders(self, market: str = None, state: str = "wait") -> list:
        params = {"state": state}
        if market:
            params["market"] = market
        return self._get("/orders", params=params, auth=True)

    def place_buy_order(self, market: str, price: float, volume: float = None, order_type: str = "limit"):
        body = {"market": market, "side": "bid", "ord_type": order_type}
        if order_type == "limit":
            body["price"] = str(price)
            body["volume"] = str(volume)
        else:
            body["price"] = str(price)
        return self._post("/orders", body)

    def place_sell_order(self, market: str, volume: float, price: float = None, order_type: str = "market"):
        body = {"market": market, "side": "ask", "ord_type": order_type, "volume": str(volume)}
        if order_type == "limit" and price:
            body["price"] = str(price)
        return self._post("/orders", body)

    def get_order(self, uuid_: str) -> dict:
        """개별 주문 조회"""
        params = {"uuid": uuid_}
        return self._get("/order", params=params, auth=True)

    def cancel_order(self, uuid_: str):
        return self._delete("/order", {"uuid": uuid_})

    # ── 편의 메서드 ─────────────────────────────────────────
    def get_balance(self, currency: str = "KRW") -> float:
        accounts = self.get_accounts()
        for acc in accounts:
            if acc["currency"] == currency:
                return float(acc["balance"])
        return 0.0

    def get_current_price(self, market: str) -> float:
        tickers = self.get_ticker([market])
        if tickers:
            return float(tickers[0]["trade_price"])
        return 0.0

    def get_portfolio(self) -> dict:
        accounts = self.get_accounts()
        portfolio = {}
        for acc in accounts:
            currency = acc["currency"]
            balance = float(acc["balance"])
            if balance > 0:
                if currency == "KRW":
                    portfolio["KRW"] = {"balance": balance, "value_krw": balance}
                else:
                    market = f"KRW-{currency}"
                    try:
                        price = self.get_current_price(market)
                        avg_price = float(acc.get("avg_buy_price", 0) or 0)
                        portfolio[currency] = {
                            "balance": balance,
                            "avg_price": avg_price,
                            "cur_price": price,
                            "value_krw": balance * price,
                            "profit_pct": ((price / avg_price) - 1) if avg_price > 0 else 0,
                        }
                    except Exception:
                        portfolio[currency] = {"balance": balance, "value_krw": 0}
        return portfolio
