# 🎧 RemoteDownloadBot

RemoteDownloadBot works alongside **YouTube-Downloader Bot** to automatically **index, fetch, and locally store audio files** that were uploaded to a specific Discord channel.  
It scans the configured channel for audio attachments, downloads them to your machine, and keeps track of already-downloaded files in a JSON cache.

---

## 📦 Features

- 🔍 Indexes all messages in a target channel (`SOUND_CHANNEL_NAME`)
- 📥 Downloads all `.mp3` and `.wav` files to the local `downloads/` directory
- 📝 Maintains a **download history** in `downloaded_sounds.json` to prevent duplicates
- 🎶 Play back previously downloaded audio via `!send_audio <name>`
- ♻️ Automatically resumes indexing if restarted

---

## ⚙️ Setup

### 1. Install Dependencies
```bash
pip install -U discord.py yt-dlp python-dotenv
```

---

### 2. Configure Environment

#### Create a .env file in the project root:

```re
DISCORD_DOWNLOADER=YOUR_DISCORD_BOT_TOKEN
```

---

### 3. Required Files & Folders

#### The bot will not run correctly unless these exist:

```re
📂 downloads/ → storage folder for all downloaded audio
📜 downloaded_sounds.json → JSON file tracking which files have been downloaded

Create them manually if missing:

mkdir downloads
echo "[]" > downloaded_sounds.json
```

---

### 4. Configure the Channel

 - Edit the source file and set the channel name where YouTube-Downloader posts files:

```re
# Example:
SOUND_CHANNEL_NAME = "📺｜𝓨outube"
```

#### _This must exactly match the text channel name._

---