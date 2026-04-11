import sqlite3
from pathlib import Path
from contextlib import contextmanager
import hashlib
import os

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Database path configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "deliverinno.db")))


def hash_password(password: str) -> str:
    """
    Hash password using SHA256.

    Args:
        password: Plain text password

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(password.encode()).hexdigest()


class Database:
    """
    SQLite database connection manager with transaction support.

    Features:
    - Reuses in-memory connections for tests
    - Creates new file connections for production
    - Automatic transaction management
    - WAL mode for concurrent access
    """

    def __init__(self, path: str | Path = "data/deliverinno.db"):
        """
        Initialize database manager.

        Args:
            path: Database file path (or ':memory:' for testing)
        """
        self.path = path
        self._memory_conn = None  # Cache connection for :memory: databases

        # Create data directory if using file-based database
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(exist_ok=True)

    def get_connection(self):
        """
        Get or create SQLite database connection.

        For :memory: databases, reuses single connection.
        For file databases, creates new connection with:
        - WAL mode: Write-Ahead Logging for concurrent writes
        - NORMAL synchronous: Balance between safety and performance
        - Foreign keys: Enable referential integrity

        Returns:
            sqlite3.Connection with row_factory = sqlite3.Row
        """
        # STEP 1: For in-memory databases, reuse single connection
        if self.path == ":memory:":
            if self._memory_conn is None:
                # Create in-memory connection (persists for test duration)
                self._memory_conn = sqlite3.connect(str(self.path))
                self._memory_conn.row_factory = sqlite3.Row
            return self._memory_conn

        # STEP 2: For file-based databases, create new connection
        conn = sqlite3.connect(
            str(self.path),
            timeout=30,  # Wait 30s if database is locked
            check_same_thread=False,  # Allow access from multiple threads
        )

        # STEP 3: Configure connection for production use
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        conn.execute("PRAGMA journal_mode=WAL;")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL;")  # Balance safety/performance
        conn.execute("PRAGMA foreign_keys=ON;")  # Enable foreign key constraints

        return conn

    @contextmanager
    def get_db(self):
        """
        Context manager for safe database transactions.

        Usage:
            with db.get_db() as conn:
                conn.execute(...)

        Features:
        - Automatically begins DEFERRED transaction
        - Commits on success
        - Rolls back on exception
        - Closes connection (except for :memory:)

        Yields:
            sqlite3.Connection
        """
        conn = self.get_connection()
        try:
            # STEP 1: Begin deferred transaction (lock acquired on first write)
            conn.execute("BEGIN DEFERRED")

            # STEP 2: Yield connection for use
            yield conn

            # STEP 3: Commit transaction if no exceptions
            conn.commit()

        except Exception:
            # STEP 4: Rollback on any exception
            conn.rollback()
            raise

        finally:
            # STEP 5: Close connection (keep :memory: open for reuse)
            if self.path != ":memory:":
                conn.close()

    def init_db(self):
        """
        Create database schema if not exists.

        Creates tables:
        - users: Buyer and seller accounts
        - products: Seller's product catalog
        - cart_items: Buyer's shopping cart
        - orders: Order headers with total amount
        - order_items: Individual items in orders

        Also seeds demo users for development.
        """
        with self.get_db() as conn:
            cursor = conn.cursor()

            # TABLE 1: Users (sellers and buyers)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('seller', 'buyer')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # TABLE 2: Products (catalog)
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

            # TABLE 3: Cart items (buyer's shopping cart)
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

            # TABLE 4: Orders (order headers with total)
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

            # TABLE 5: Order items (items in orders with snapshot prices)
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

            # SEED: Create demo seller account for development
            cursor.execute("SELECT * FROM users WHERE username = 'demo_seller'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    ("demo_seller", hash_password("demo123"), "seller")
                )
                print("✓ Created demo seller account")

            # SEED: Create demo buyer account for development
            cursor.execute("SELECT * FROM users WHERE username = 'demo_buyer'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    ("demo_buyer", hash_password("demo123"), "buyer")
                )
                print("✓ Created demo buyer account")

            conn.commit()

            print(f"✓ Database initialized at: {self.path}")
