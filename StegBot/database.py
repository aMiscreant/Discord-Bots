import os
import mysql.connector
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Runtime-only encryption key (not saved to disk) / Breaks Encryption
FERNET_SECRET = os.getenv("FERNET_SECRET")
if not FERNET_SECRET:
    raise RuntimeError("❌ .env is missing FERNET_SECRET or it's not loading properly.")

FERNET_KEY = FERNET_SECRET.encode()
fernet = Fernet(FERNET_KEY)

# DB connection info
DB_HOST = "YOUR_HOST_IP"
DB_PORT = 3306
DB_USER = "DATABASE_USERNAME"
DB_PASS = os.getenv("DB_PASS")  # Must be set in .env
DB_NAME = "DB_NAME_steg_securebot"

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def init_db():
    print("🔧 Initializing secure DB...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_keys (
            user_id VARCHAR(32) PRIMARY KEY,
            public_key TEXT NOT NULL,
            encrypted_private_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized and ready.")

def store_user_keys(user_id: int, public_key_hex: str, private_key_hex: str):
    encrypted_private = fernet.encrypt(private_key_hex.encode()).decode()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_keys (user_id, public_key, encrypted_private_key)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            public_key = VALUES(public_key),
            encrypted_private_key = VALUES(encrypted_private_key)
    """, (str(user_id), public_key_hex, encrypted_private))
    conn.commit()
    conn.close()

def load_user_keys(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT public_key, encrypted_private_key FROM user_keys WHERE user_id = %s", (str(user_id),))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    pub, encrypted_priv = result
    decrypted_priv = fernet.decrypt(encrypted_priv.encode()).decode()
    return {
        "public_key": pub,
        "private_key": decrypted_priv
    }

if __name__ == "__main__":
    init_db()
