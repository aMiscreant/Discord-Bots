import os
import json

import discord
import yt_dlp as ytdl
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_DOWNLOADER")
# Example:
# SOUND_CHANNEL_NAME = "📺｜𝓨outube"
SOUND_CHANNEL_NAME = ""
DOWNLOAD_DIR = "downloads"
DOWNLOADED_FILE = "downloaded_sounds.json"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.messages = True


class RemoteDownloadBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()


bot = RemoteDownloadBot(command_prefix="!", intents=intents)
sound_cache = {}  # sound_name -> URL

# Ensure download folder exists
# Ensure download folder exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Ensure downloaded sounds file exists and load downloaded sounds list or create empty set
if not os.path.exists(DOWNLOADED_FILE) or os.path.getsize(DOWNLOADED_FILE) == 0:
    with open(DOWNLOADED_FILE, "w") as f:
        json.dump([], f)

downloaded_sounds = set()
try:
    with open(DOWNLOADED_FILE, "r") as f:
        data = f.read().strip()
        if data:
            downloaded_sounds = set(json.loads(data))
except Exception as e:
    print(f"Warning: failed to load {DOWNLOADED_FILE}: {e}")
    downloaded_sounds = set()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await index_sounds()

async def index_sounds():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            print(f"Checking channel: {channel.name}")
            if channel.name == SOUND_CHANNEL_NAME:
                print(f"Indexing from #{channel.name}")
                async for msg in channel.history(limit=None, oldest_first=True):
                    try:
                        print(f"Message ID {msg.id} by {msg.author} has {len(msg.attachments)} attachments")
                        for att in msg.attachments:
                            print(f"Found attachment: {att.filename}")
                            if att.filename.endswith((".mp3", ".wav")):
                                name = os.path.splitext(att.filename)[0].lower()
                                sound_cache[name] = att.url
                                if name not in downloaded_sounds:
                                    await download_file(att.url, name)
                                    downloaded_sounds.add(name)
                                    # Save updated list after each download
                                    with open(DOWNLOADED_FILE, "w") as f:
                                        json.dump(list(downloaded_sounds), f)
                    except Exception as e:
                        print(f"Error reading message {msg.id}: {e}")
                        continue
    print(f"Indexed {len(sound_cache)} sounds, downloaded {len(downloaded_sounds)} files.")


async def download_file(url, sound_name):
    file_path = os.path.join(DOWNLOAD_DIR, f"{sound_name}.mp3")

    if os.path.exists(file_path):
        print(f"{file_path} already exists. Skipping download.")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': file_path,
        'quiet': True
    }

    try:
        print(f"Downloading {sound_name}...")
        with ytdl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Downloaded {sound_name} to {file_path}")
    except Exception as e:
        print(f"Error downloading {sound_name}: {e}")


@bot.command()
async def send_audio(ctx, *, sound_name: str):
    sound_name = sound_name.lower()
    file_path = os.path.join(DOWNLOAD_DIR, f"{sound_name}.mp3")

    if os.path.exists(file_path):
        await ctx.send(file=discord.File(file_path))
    else:
        await ctx.send(f"Sound file '{sound_name}' not found.")


bot.run(TOKEN)
