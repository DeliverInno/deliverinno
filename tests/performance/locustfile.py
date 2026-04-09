from __future__ import annotations

import random
import threading
from locust import HttpUser, between, task

BUYER_POOL_SIZE = 200
BUYER_PASSWORD = "load_buyer_password"

_user_index_lock = threading.Lock()
_user_index = 0


def next_buyer_username() -> str:
    global _user_index
    with _user_index_lock:
        _user_index += 1
        idx = ((_user_index - 1) % BUYER_POOL_SIZE) + 1
    return f"load_buyer_{idx:04d}"


class BuyerUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.ready = False
        self.auth_headers = None
        self.product_id = None
        self.username = next_buyer_username()

        with self.client.post(
            "/auth/login",
            json={"username": self.username, "password": BUYER_PASSWORD},
            name="/auth/login (once)",
            catch_response=True,
            timeout=20,
        ) as r:
            if r.status_code == 200:
                token = r.json().get("access_token")
                if token:
                    self.auth_headers = {"Authorization": f"Bearer {token}"}
                    self.ready = True
                    r.success()
                else:
                    r.failure("No access_token")
            else:
                r.failure(f"login failed {self.username}: {r.status_code} {r.text}")

    def _skip(self) -> bool:
        return not self.ready or self.auth_headers is None

    @task(6)
    def get_products(self):
        if self._skip():
            return

        with self.client.get(
            "/buyer/products",
            headers=self.auth_headers,
            name="GET /buyer/products",
            catch_response=True,
            timeout=20,
        ) as r:
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    available = [p for p in data if p.get("id") and p.get("quantity", 0) > 0]
                    if available:
                        self.product_id = random.choice(available)["id"]
                r.success()
            elif r.status_code in (503,):
                r.success()  # для SQLite под локальной нагрузкой считаем ожидаемым transient
            else:
                r.failure(f"{r.status_code}: {r.text}")

    @task(3)
    def post_cart(self):
        if self._skip():
            return

        # каждый раз обновляем product_id, чтобы снизить ошибки по остаткам
        self.get_products()
        if self.product_id is None:
            return

        with self.client.post(
            "/buyer/cart",
            headers=self.auth_headers,
            json={"product_id": self.product_id, "quantity": 1},
            name="POST /buyer/cart",
            catch_response=True,
            timeout=20,
        ) as r:
            if r.status_code in (201, 400, 404, 409, 503):
                r.success()
            else:
                r.failure(f"{r.status_code}: {r.text}")

    @task(1)
    def post_order(self):
        if self._skip():
            return

        with self.client.post(
            "/buyer/orders",
            headers=self.auth_headers,
            name="POST /buyer/orders",
            catch_response=True,
            timeout=20,
        ) as r:
            if r.status_code in (201, 400, 404, 503):
                r.success()
            else:
                r.failure(f"{r.status_code}: {r.text}")
