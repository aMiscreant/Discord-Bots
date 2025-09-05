# 🔐 CryptoCompanion

CryptoCompanion is a Discord bot designed to provide **end-to-end encrypted communication** between users directly within Discord.  
It allows users to generate cryptographic keypairs, exchange encrypted messages or files, and securely decrypt received content — all through Discord slash commands.

---

## 📦 Features

- Generate **public/private key pairs** per user (`/generate_keys`)
- Encrypt and send secure **messages** to other users (`/encrypt`)
- Decrypt received **messages** (`/decrypt`)
- Encrypt and send secure **files** (`/encrypt_file`)
- Decrypt received **files** (`/decrypt_file`)
- Private ephemeral responses so only the intended user sees sensitive data
- Uses **NaCl (libsodium)** sealed boxes for robust encryption

---

## ⚙️ Setup

1. Clone this repository or copy the bot code into your project.

2. Install dependencies:

   ```bash
   pip install -U discord.py pynacl python-dotenv
# 🔐 CryptoCompanion

CryptoCompanion is a Discord bot designed to provide **end-to-end encrypted communication** between users directly within Discord.  
It allows users to generate cryptographic keypairs, exchange encrypted messages or files, and securely decrypt received content — all through Discord slash commands.

---

## 📦 Features

- Generate **public/private key pairs** per user (`/generate_keys`)
- Encrypt and send secure **messages** to other users (`/encrypt`)
- Decrypt received **messages** (`/decrypt`)
- Encrypt and send secure **files** (`/encrypt_file`)
- Decrypt received **files** (`/decrypt_file`)
- Private ephemeral responses so only the intended user sees sensitive data
- Uses **NaCl (libsodium)** sealed boxes for robust encryption

---

## ⚙️ Setup

1. Clone this repository or copy the bot code into your project.

2. Install dependencies:

3. ```bash
   pip install -U discord.py pynacl python-dotenv
   ```

4. Create a .env file in the project root:

   ```re
   DISCORD_TOKEN_CC=YOUR_API_KEY_HERE
   ```
   - Replace YOUR_API_KEY_HERE with your actual Discord bot token.