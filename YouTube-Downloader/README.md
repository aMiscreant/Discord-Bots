# 🎵 YouTube-Downloader Bot

YouTube-Downloader is a Discord bot that allows users to **search, select, and download YouTube audio directly into Discord**.  
It supports **direct YouTube links, search queries, playlists**, and returns **MP3 files** for quick sharing.

---

## 📦 Features

- 🔍 Search YouTube directly from Discord with `/discord-dl <query>`
- 📎 Paste direct YouTube links (video or playlist)
- 🎶 Downloads best available **audio-only format**
- 📝 Auto-converts to **128kbps MP3**
- ⏱ Clips audio to a maximum of **5 minutes per track** (configurable via `ffmpeg`)
- 📂 Ensures all downloads are stored in the `downloads/` folder before being sent
- ✅ Supports playlists (up to 25 entries max per batch)
- 🖱 Interactive **dropdown menu** for search results
- 🔒 Deletes temporary files after sending to Discord

---

## ⚙️ Setup

### 1. Install Dependencies
Make sure you have Python 3.8+ installed, then run:

```bash
pip install -U discord.py yt-dlp python-dotenv
```

---

### 2. Configure Environment

Create a .env file in the project root:

YOUTUBE_DOWNLOADER=YOUR_DISCORD_BOT_TOKEN

---

### 3. Folder Setup

The bot requires a downloads/ folder to exist in the project root:

```bash
mkdir downloads
```

**This is where temporary MP3s will be stored before being sent to Discord.
They are automatically deleted after upload.**

---

### - Commands
### - Download Audio

```re
Command	Description
/discord-dl <query>	Search YouTube or paste a link to download audio

```

### _Notes & Limitations_

- Audio files are capped at 5 minutes to avoid hitting Discord’s file limits.

- Uses yt-dlp under the hood with cookies.txt and a spoofed User-Agent for reliability.

- Large playlists are trimmed to 25 items for safety.

- The bot does not cache downloads — everything is processed on demand.

---