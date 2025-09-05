# 🤖 Discord-Bots

A collection of custom Discord bots built for **learning, experimentation, and utility**.  
Each bot serves a unique purpose — from encryption tools to media handling.

---

## 📦 Included Bots

### 🔑 [CryptoCompanion](./CryptoCompanion)
A secure messaging bot with:
- Public/Private key generation  
- Encrypted messages & file transfers  
- End-to-end decryption inside Discord  

---

### 🕵️ [StegBot](./StegBot)
A steganography & security toolkit:
- Hide/reveal encrypted messages inside images  
- Strip or scramble metadata (EXIF, GPS, ICC)  
- Keyring management with database backend  

---

### 🎵 [YouTube-Downloader](./YouTube-Downloader)
A YouTube audio downloader with:
- Direct link or search query support  
- Playlist downloads (clipped to 25 items)  
- Auto-converts audio to MP3 for sharing  

---

### 🎧 [RemoteDownloadBot](./RemoteDownloadBot)
A companion bot for YouTube-Downloader:
- Indexes a target channel for audio files  
- Downloads & stores them locally  
- Keeps track of fetched files in JSON cache  

---

## ⚙️ Setup

Each bot has its own **README.md** with detailed setup instructions.  
At minimum, you’ll need:  

- Python 3.8+  
- `discord.py`, `yt-dlp`, `python-dotenv`, and other per-bot dependencies  
- A valid **Discord Bot Token** for each bot  

---

## 📜 License
These bots are provided for **educational purposes only**.  
Use responsibly and in accordance with Discord’s Terms of Service.  
