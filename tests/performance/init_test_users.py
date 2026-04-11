from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path


BUYER_PASSWORD = "load_buyer_password"
SELLER_USERNAME = "load_seller"
SELLER_PASSWORD = "load_seller_password"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def ensure_user(conn: sqlite3.Connection, username: str, password: str, role: str) -> int:
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    pwd_hash = hash_password(password)

    if row:
        conn.execute(
            "UPDATE users SET password = ?, role = ? WHERE username = ?",
            (pwd_hash, role, username),
        )
        user_id = int(row[0])
    else:
        cur = conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, pwd_hash, role),
        )
        user_id = int(cur.lastrowid)

    return user_id


def ensure_buyer_pool(conn: sqlite3.Connection, pool_size: int):
    for i in range(1, pool_size + 1):
        username = f"load_buyer_{i:04d}"
        ensure_user(conn, username, BUYER_PASSWORD, "buyer")
    print(f"[init] buyer pool ready: {pool_size}")


def ensure_seller(conn: sqlite3.Connection) -> int:
    seller_id = ensure_user(conn, SELLER_USERNAME, SELLER_PASSWORD, "seller")
    print(f"[init] seller ready: {SELLER_USERNAME} (id={seller_id})")
    return seller_id


def ensure_products(conn: sqlite3.Connection, seller_id: int, target_count: int):
    row = conn.execute(
        "SELECT COUNT(*) FROM products WHERE seller_id = ?",
        (seller_id,),
    ).fetchone()
    existing = int(row[0]) if row else 0
    need = max(0, target_count - existing)

    for i in range(need):
        conn.execute(
            """
            INSERT INTO products (name, description, price, quantity, seller_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                f"load_product_{i}",
                f"autocreated product {i}",
                float(100 + i),
                1000,
                seller_id,
            ),
        )

    print(f"[init] products: existing={existing}, created={need}")


def main(db_path: str, products: int, buyer_pool_size: int):
    db_file = Path(db_path).resolve()
    if not db_file.exists():
        raise FileNotFoundError(
            f"DB file not found: {db_file}\n"
            "Запусти backend хотя бы один раз, чтобы init_db создал таблицы."
        )

    conn = sqlite3.connect(str(db_file))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")

        ensure_buyer_pool(conn, buyer_pool_size)
        seller_id = ensure_seller(conn)
        ensure_products(conn, seller_id=seller_id, target_count=products)

        conn.commit()
        print("[init] done")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default="../../data/deliverinno.db")
    parser.add_argument("--products", type=int, default=30)
    parser.add_argument("--buyer-pool-size", type=int, default=200)
    args = parser.parse_args()
    main(args.db_path, args.products, args.buyer_pool_size)
