import asyncio
import io
import os

import discord
import binascii
from PIL import Image
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from nacl.public import PrivateKey, PublicKey, SealedBox
from nacl.exceptions import CryptoError

from database import store_user_keys, load_user_keys, init_db, get_connection  # your DB functions
from steg_helpers import (
    scrub_image_metadata,
    sanitize_image,
    steg_scrub_and_mutate,
    apply_matrix_style_effect,
    watermark_image,
    lsb_encode,
    lsb_decode
)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN_CC")
KEY_RING_PASS = os.getenv("KEY_RING_PASS")
DELETE_GPG_KEY_PASS = os.getenv("DELETE_GPG_KEY_PASS")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def async_store_user_keys(user_id: int, public_key_hex: str, private_key_hex: str):
    await asyncio.to_thread(store_user_keys, user_id, public_key_hex, private_key_hex)

async def async_load_user_keys(user_id: int):
    return await asyncio.to_thread(load_user_keys, user_id)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
        for cmd in synced:
            print(f"- {cmd.name}: {cmd.description}")
    except Exception as e:
        print(e)

@bot.tree.command(name="generate_keys", description="Generate a new public/private key pair.")
async def generate_keys(interaction: discord.Interaction):
    private_key = PrivateKey.generate()
    public_key = private_key.public_key
    priv_hex = private_key.encode().hex()
    pub_hex = public_key.encode().hex()

    await async_store_user_keys(interaction.user.id, pub_hex, priv_hex)

    await interaction.response.send_message(
        f"✅ Your keypair has been generated!\nPublic Key:\n`{pub_hex}`",
        ephemeral=True
    )

@bot.tree.command(name="list_keys", description="View your stored public key.")
async def list_keys(interaction: discord.Interaction):
    user_keys = await async_load_user_keys(interaction.user.id)

    if not user_keys:
        await interaction.response.send_message(
            "❌ You don't have a keypair stored. Run `/generate_keys` first.",
            ephemeral=True
        )
        return

    pub = user_keys["public_key"]

    await interaction.response.send_message(
        f"🔑 **Your Public Key:**\n`{pub}`",
        ephemeral=True
    )

@bot.tree.command(name="lookup_key", description="Get someone else's public key.")
@app_commands.describe(user="The user to look up")
async def lookup_key(interaction: discord.Interaction, user: discord.User):
    user_keys = await async_load_user_keys(user.id)

    if not user_keys:
        await interaction.response.send_message(
            f"❌ {user.mention} has not generated a key yet.",
            ephemeral=True
        )
        return

    pub = user_keys["public_key"]
    await interaction.response.send_message(
        f"🔎 **Public Key for {user.mention}:**\n`{pub}`",
        ephemeral=True
    )

@bot.tree.command(name="delete_keys", description="Delete your keypair from the system.")
@app_commands.describe(password="Password to authorize deletion")
async def delete_keys(interaction: discord.Interaction, password: str):
    if password != DELETE_GPG_KEY_PASS:
        await interaction.response.send_message("❌ Invalid password.", ephemeral=True)
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_keys WHERE user_id = %s", (interaction.user.id,))
    conn.commit()
    conn.close()

    await interaction.response.send_message("🗑️ Your keypair has been deleted.", ephemeral=True)

@bot.tree.command(name="keyring", description="List all users with stored public keys.")
@app_commands.describe(password="Password to access keyring")
async def keyring(interaction: discord.Interaction, password: str):
    if password != KEY_RING_PASS:
        await interaction.response.send_message("❌ Invalid password.", ephemeral=True)
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, public_key FROM user_keys")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await interaction.response.send_message("📭 No keys stored yet.", ephemeral=True)
        return

    content = "🧾 **Keyring:**\n" + "\n".join(f"<@{uid}> — `{pub}`" for uid, pub in rows)
    await interaction.response.send_message(content, ephemeral=True)

class StegImageMenu(discord.ui.View):
    def __init__(self, image_bytes: bytes):
        super().__init__(timeout=60)
        self.image_bytes = image_bytes

    @discord.ui.select(
        placeholder="Choose how to process your image...",
        options=[
            discord.SelectOption(label="Strip Metadata", description="Remove all EXIF, GPS, and ICC metadata"),
            discord.SelectOption(label="Scramble Metadata", description="Replace metadata with fake random values"),
            discord.SelectOption(label="Matrixify + Watermark", description="Apply Matrix effect + watermark"),
            discord.SelectOption(label="Full Mutation Pipeline", description="Scrub, distort, watermark"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        choice = select.values[0]
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            if choice == "Strip Metadata":
                result = scrub_image_metadata(self.image_bytes)
                label = "🧼 Metadata stripped"
            elif choice == "Scramble Metadata":
                result = sanitize_image(self.image_bytes, scramble_metadata=True)
                label = "🔀 Metadata scrambled"
            elif choice == "Matrixify + Watermark":
                img = Image.open(io.BytesIO(self.image_bytes)).convert("RGB")
                img = apply_matrix_style_effect(img)
                img = watermark_image(img)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                result = buf.read()
                label = "💚 Matrix effect applied"
            else:  # Full Mutation
                result = steg_scrub_and_mutate(self.image_bytes)
                label = "🎲 Full mutation complete"

            file = discord.File(io.BytesIO(result), filename="processed.png")
            await interaction.followup.send(label, file=file, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Failed to process image: {e}", ephemeral=True)

# Slash command
@bot.tree.command(name="steg_image", description="Upload an image and apply steganographic filters.")
@app_commands.describe(attachment="The image to transform")
async def steg_image(interaction: discord.Interaction, attachment: discord.Attachment):
    if not attachment.content_type or not attachment.content_type.startswith("image/"):
        await interaction.response.send_message("❌ Please upload a valid image file.", ephemeral=True)
        return

    image_bytes = await attachment.read()
    await interaction.response.send_message(
        "📷 Select how you'd like to process your image:",
        view=StegImageMenu(image_bytes),
        ephemeral=True
    )

@bot.tree.command(name="encrypt", description="Encrypt a message for another user (message will be entered privately).")
@app_commands.describe(to_user="User to encrypt message for")
async def encrypt(interaction: discord.Interaction, to_user: discord.User):
    recipient_keys = await async_load_user_keys(to_user.id)
    if not recipient_keys:
        await interaction.response.send_message(
            "❌ That user has not generated keys yet. Ask them to run /generate_keys.",
            ephemeral=True
        )
        return

    class EncryptModal(discord.ui.Modal, title="Encrypt a Message"):
        message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph)

        async def on_submit(self, modal_interaction: discord.Interaction):
            recipient_pub_key = PublicKey(bytes.fromhex(recipient_keys["public_key"]))
            sealed_box = SealedBox(recipient_pub_key)
            encrypted = sealed_box.encrypt(self.message.value.encode())

            try:
                await to_user.send(
                    f"🔒 Encrypted message from {interaction.user.mention}:\n```\n{encrypted.hex()}\n```"
                )
                await modal_interaction.response.send_message(
                    f"✅ Encrypted message delivered to {to_user.mention}'s DMs.",
                    ephemeral=True
                )
            except discord.Forbidden:
                await modal_interaction.response.send_message(
                    "❌ Couldn't send DM to that user. They might have DMs disabled.",
                    ephemeral=True
                )

    await interaction.response.send_modal(EncryptModal())

@bot.tree.command(name="decrypt", description="Decrypt an encrypted message.")
@app_commands.describe(ciphertext="Encrypted message in hex")
async def decrypt(interaction: discord.Interaction, ciphertext: str):
    user_keys = await async_load_user_keys(interaction.user.id)
    if not user_keys:
        await interaction.response.send_message(
            "❌ You don't have a keypair. Run /generate_keys first.",
            ephemeral=True
        )
        return

    private_key = PrivateKey(bytes.fromhex(user_keys["private_key"]))
    sealed_box = SealedBox(private_key)

    try:
        decrypted = sealed_box.decrypt(bytes.fromhex(ciphertext))
        plaintext = decrypted.decode()
        await interaction.response.send_message(
            f"✅ Decrypted message:\n```\n{plaintext}\n```",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Failed to decrypt: {str(e)}",
            ephemeral=True
        )

@bot.tree.command(name="hide_message", description="Encrypt a message and hide it inside an image.")
@app_commands.describe(to_user="Recipient user", message="Message to hide", attachment="Image to hide message in")
async def hide_message(interaction: discord.Interaction, to_user: discord.User, message: str, attachment: discord.Attachment):
    recipient_keys = await async_load_user_keys(to_user.id)
    if not recipient_keys:
        await interaction.response.send_message("❌ That user has not generated keys yet. Ask them to run /generate_keys.", ephemeral=True)
        return

    try:
        # Read image bytes
        image_bytes = await attachment.read()

        # Encrypt message
        recipient_pub_key = PublicKey(bytes.fromhex(recipient_keys["public_key"]))
        sealed_box = SealedBox(recipient_pub_key)
        encrypted = sealed_box.encrypt(message.encode())

        # Load image and embed encrypted message
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_with_data = lsb_encode(img, encrypted.hex())  # encode hex string

        # Save modified image to bytes
        output = io.BytesIO()
        img_with_data.save(output, format="PNG")
        output.seek(0)

        file = discord.File(fp=output, filename="hidden_message.png")
        await interaction.response.send_message(f"✅ Message encrypted and hidden inside the image for {to_user.mention}.", file=file, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to hide message: {e}", ephemeral=True)

@bot.tree.command(name="reveal_message", description="Reveal and decrypt a hidden message inside an image.")
@app_commands.describe(attachment="Image with hidden message")
async def reveal_message(interaction: discord.Interaction, attachment: discord.Attachment):
    await interaction.response.defer(thinking=True, ephemeral=True)  # <-- add this first!

    user_keys = await async_load_user_keys(interaction.user.id)
    if not user_keys:
        await interaction.followup.send("❌ You don't have a keypair. Run /generate_keys first.", ephemeral=True)
        return

    try:
        # Read image bytes
        image_bytes = await attachment.read()

        # Load image and decode hidden hex string
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        hidden_hex = lsb_decode(img)

        if not hidden_hex:
            await interaction.followup.send("❌ No hidden message found in the image.", ephemeral=True)
            return

        # Decrypt the hidden message
        private_key = PrivateKey(bytes.fromhex(user_keys["private_key"]))
        sealed_box = SealedBox(private_key)
        encrypted_bytes = bytes.fromhex(hidden_hex)

        decrypted = sealed_box.decrypt(encrypted_bytes)
        plaintext = decrypted.decode()

        await interaction.followup.send(f"🔓 Hidden message revealed:\n```\n{plaintext}\n```", ephemeral=True)

    except CryptoError:
        await interaction.followup.send("❌ Failed to decrypt hidden message. Are you the intended recipient?", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to reveal message: {e}", ephemeral=True)

@bot.tree.context_menu(name="Scan for Hidden Data")
async def scan_for_hidden_data(interaction: discord.Interaction, message: discord.Message):
    image = next((a for a in message.attachments if a.content_type and a.content_type.startswith("image/")), None)

    if not image:
        await interaction.response.send_message("❌ No image attachment found in that message.", ephemeral=True)
        return

    image_bytes = await image.read()

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        hidden_data = lsb_decode(img)

        if not hidden_data:
            await interaction.response.send_message("📭 No hidden message found.", ephemeral=True)
            return

        # Try hex-decode
        try:
            encrypted_bytes = bytes.fromhex(hidden_data)

            user_keys = await async_load_user_keys(interaction.user.id)
            if not user_keys:
                await interaction.response.send_message("❌ You need a keypair. Run /generate_keys first.", ephemeral=True)
                return

            private_key = PrivateKey(bytes.fromhex(user_keys["private_key"]))
            sealed_box = SealedBox(private_key)

            decrypted = sealed_box.decrypt(encrypted_bytes).decode()

            await interaction.response.send_message(f"🕵️ Hidden encrypted message:\n```\n{decrypted}\n```", ephemeral=True)

        except ValueError:
            # Not valid hex – treat as plaintext
            await interaction.response.send_message(f"📄 Hidden plaintext message:\n```\n{hidden_data}\n```", ephemeral=True)

        except CryptoError:
            await interaction.response.send_message("❌ Hidden data looks like encrypted hex but couldn't be decrypted — are you the intended recipient?", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"❌ Error scanning image: {e}", ephemeral=True)
        
# Similarly update encrypt_file and decrypt_file commands with async DB calls
def verify_db_ready():
    """
    Checks if the expected tables exist. Returns True if ready, False if not.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'user_keys'")
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"⚠️ DB verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking database status...")
    try:
        init_db()
        if verify_db_ready():
            print("✅ Database tables verified.")
            bot.run(TOKEN)
        else:
            print("❌ Table check failed. Exiting.")
    except Exception as e:
        print(f"❌ Failed to initialize or connect to DB: {e}")
