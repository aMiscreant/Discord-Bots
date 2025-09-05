# 🕵️ StegBot

StegBot is a secure Discord bot that combines **end-to-end encryption** with **steganography** and **image sanitization tools**.  
It allows users to generate and manage cryptographic keys, hide or reveal encrypted messages inside images, strip metadata, and securely exchange hidden data — all from within Discord.

---

## 📦 Features

### 🔑 Key Management
- Generate new **public/private key pairs** (`/generate_keys`)
- View your public key (`/list_keys`)
- Look up another user’s public key (`/lookup_key`)
- Delete your keypair from the system (`/delete_keys`)
- Admin-only access to the **keyring** of all stored keys (`/keyring`)

### 📷 Image Steganography & Sanitization
- **Steg Image Menu** (`/steg_image`)  
  Apply transformations to uploaded images:
  - 🧼 Strip Metadata (EXIF, GPS, ICC)
  - 🔀 Scramble Metadata with fake values
  - 💚 Matrixify + Watermark
  - 🎲 Full Mutation Pipeline (scrub, distort, watermark)
- Hide encrypted messages inside images (`/hide_message`)
- Reveal hidden encrypted messages from images (`/reveal_message`)
- Context menu: **Scan for Hidden Data** (right-click message → Apps → Scan for Hidden Data)

### 🔒 Encrypted Messaging
- Encrypt a message for another user (`/encrypt`)
- Decrypt received ciphertext (`/decrypt`)
- Hide + encrypt messages inside images (`/hide_message`)
- Reveal + decrypt hidden messages (`/reveal_message`)

### 🛠️ Utilities
- Robust MySQL database backend for key storage
- Private ephemeral responses for sensitive commands
- LSB (Least Significant Bit) steganography for embedding hidden data

---

## ⚙️ Setup

### 1. Install Dependencies
```bash
pip install -U discord.py pynacl pillow python-dotenv cryptography mysql-connector-python piexif
```

---

### 2. Configure Environment

#### Create a .env file in the project root:


```re
FERNET_SECRET=YOUR_FERNET_KEY_HERE
DB_PASS=YOUR_DB_PASSWORD_HERE
KEY_RING_PASS=YOUR_KEYRING_PASSWORD_HERE
DELETE_GPG_KEY_PASS=YOUR_GPG_DELETE_PASSWORD_HERE
DISCORD_TOKEN_CC=YOUR_DISCORD_BOT_TOKEN
```

- FERNET_SECRET → a base64-encoded Fernet key (used for encrypting private keys in DB)

- DB_PASS → database password

- KEY_RING_PASS → password required to view the full keyring

- DELETE_GPG_KEY_PASS → password required for users to delete their keys

- DISCORD_TOKEN_CC → your Discord bot token

---

### 3. Configure Database

#### Update database.py with your DB settings:

```re
DB_HOST = "YOUR_HOST_IP"
DB_PORT = 3306
DB_USER = "DATABASE_USERNAME"
DB_NAME = "DB_NAME_steg_securebot"
```

#### Initialize the database:

```bash
python database.py
```

---

### NOTE:

```re
EXAMPLE FERNET_KEY="f9gFLtHmOkncnNpVmiDFN1fQH5cPcFL1d5YJM2WG5Yk="
```

---

### - Commands
### - Key Management
### - Command Description

```re
/generate_keys	Generate a new keypair and store it securely in the database
/list_keys	View your stored public key
/lookup_key @user	Retrieve another user’s public key
/delete_keys password	Delete your stored keypair (requires DELETE_GPG_KEY_PASS)
/keyring password	Admin-only: View all stored keys (requires KEY_RING_PASS)
```

---