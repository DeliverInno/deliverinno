"""Simple SQLite database management."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
import hashlib
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "deliverinno.db")))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class Database:
    def __init__(self, path: str | Path = "data/deliverinno.db"):
        self.path = path
        self._memory_conn = None  # Кэш соединения для :memory:
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(exist_ok=True)

    def get_connection(self):
        """Get database connection."""
        # Для :memory: переиспользуем одно соединение
        if self.path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(str(self.path))
                self._memory_conn.row_factory = sqlite3.Row
            return self._memory_conn

        # Для файлов создаем новое соединение каждый раз
        # check_same_thread=False не самое хорошее решение.
        conn = sqlite3.connect(str(self.path), timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    @contextmanager
    def get_db(self):
        """Context manager for database connections."""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN DEFERRED")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            # Не закрываем :memory: соединение (оно нужно переиспользовать)
            if self.path != ":memory:":
                conn.close()

    def init_db(self):
        """Create tables if they don't exist."""
        with self.get_db() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('seller', 'buyer')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL CHECK(price >= 0),
                    quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
                    seller_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES users(id)
                )
            """)

            # Cart items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cart_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity > 0),
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    UNIQUE(user_id, product_id)
                )
            """)

            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL CHECK(total_amount >= 0),
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Order items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity > 0),
                    price_at_time REAL NOT NULL CHECK(price_at_time >= 0),
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            """)

            conn.commit()

            # Создать тестовых пользователей для разработки
            cursor.execute("SELECT * FROM users WHERE username = 'demo_seller'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO users (username, password, role)
                    VALUES (?, ?, ?)
                """, ("demo_seller", hash_password("demo123"), "seller"))
                print("Created demo seller")

            cursor.execute("SELECT * FROM users WHERE username = 'demo_buyer'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO users (username, password, role)
                    VALUES (?, ?, ?)
                """, ("demo_buyer", hash_password("demo123"), "buyer"))
                print("Created demo buyer")

            conn.commit()

            print(f"Database initialized at: {self.path}")
