import os
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.ext import commands
from nacl.public import PrivateKey, PublicKey, SealedBox

# Load variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN_CC")

# This is a demo storage for user keys:
# In real life you'd store this securely in a DB
user_keys = {}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

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

# Command: /generate_keys
@bot.tree.command(name="generate_keys", description="Generate a new public/private key pair.")
async def generate_keys(interaction: discord.Interaction):
    private_key = PrivateKey.generate()
    public_key = private_key.public_key
    user_keys[interaction.user.id] = {
        "private_key": private_key.encode().hex(),
        "public_key": public_key.encode().hex()
    }
    await interaction.response.send_message(
        f"✅ Your keypair has been generated!\nPublic Key:\n`{public_key.encode().hex()}`",
        ephemeral=True
    )


# Command: /encrypt
@bot.tree.command(name="encrypt", description="Encrypt a message for another user (message will be entered privately).")
@app_commands.describe(to_user="User to encrypt message for")
async def encrypt(interaction: discord.Interaction, to_user: discord.User):
    if to_user.id not in user_keys:
        await interaction.response.send_message(
            "❌ That user has not generated keys yet. Ask them to run /generate_keys.",
            ephemeral=True
        )
        return

    # Store recipient ID in a custom view or session (or encode it in the modal custom_id)
    class EncryptModal(discord.ui.Modal, title="Encrypt a Message"):
        message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph)

        async def on_submit(self, modal_interaction: discord.Interaction):
            # Encrypt the message from modal
            pub_key_hex = user_keys[to_user.id]["public_key"]
            recipient_pub_key = PublicKey(bytes.fromhex(pub_key_hex))
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

# Command: /decrypt
@bot.tree.command(name="decrypt", description="Decrypt an encrypted message.")
@app_commands.describe(ciphertext="Encrypted message in hex")
async def decrypt(interaction: discord.Interaction, ciphertext: str):
    if interaction.user.id not in user_keys:
        await interaction.response.send_message(
            "❌ You don't have a keypair. Run /generate_keys first.",
            ephemeral=True
        )
        return

    priv_key_hex = user_keys[interaction.user.id]["private_key"]
    private_key = PrivateKey(bytes.fromhex(priv_key_hex))

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

# Command: /encrypt_file
@bot.tree.command(name="encrypt_file", description="Encrypt a file for another user.")
@app_commands.describe(to_user="User to encrypt file for")
async def encrypt_file(interaction: discord.Interaction, to_user: discord.User, attachment: discord.Attachment):
    await interaction.response.defer(thinking=True, ephemeral=True)

    if to_user.id not in user_keys:
        await interaction.followup.send(
            "❌ That user has not generated keys yet. Ask them to run /generate_keys.",
            ephemeral=True
        )
        return

    # Download the uploaded file
    file_bytes = await attachment.read()

    # Encrypt the file
    pub_key_hex = user_keys[to_user.id]["public_key"]
    recipient_pub_key = PublicKey(bytes.fromhex(pub_key_hex))
    sealed_box = SealedBox(recipient_pub_key)
    encrypted_bytes = sealed_box.encrypt(file_bytes)

    # Save to a temporary file
    enc_filename = f"encrypted_{attachment.filename}.bin"
    with open(enc_filename, "wb") as f:
        f.write(encrypted_bytes)

    # Send the encrypted file as an attachment
    file_to_send = discord.File(enc_filename, filename=enc_filename)

    try:
        await to_user.send(
            f"🔒 Encrypted file from {interaction.user.mention}.\nRun `/decrypt_file` to recover it.",
            file=file_to_send
        )
        await interaction.followup.send(
            f"✅ Encrypted file delivered to {to_user.mention}'s DMs.",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.followup.send(
            "❌ I couldn't send the encrypted file to that user. They may have DMs disabled.",
            ephemeral=True
        )

    # Clean up temp file
    os.remove(enc_filename)


# Command: /decrypt_file
@bot.tree.command(name="decrypt_file", description="Decrypt an encrypted file sent to you.")
async def decrypt_file(interaction: discord.Interaction, attachment: discord.Attachment):
    await interaction.response.defer(thinking=True, ephemeral=True)

    if interaction.user.id not in user_keys:
        await interaction.followup.send(
            "❌ You don't have a keypair. Run /generate_keys first.",
            ephemeral=True
        )
        return

    # Download the encrypted file
    encrypted_bytes = await attachment.read()

    priv_key_hex = user_keys[interaction.user.id]["private_key"]
    private_key = PrivateKey(bytes.fromhex(priv_key_hex))
    sealed_box = SealedBox(private_key)

    try:
        decrypted_bytes = sealed_box.decrypt(encrypted_bytes)
    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to decrypt file: {str(e)}",
            ephemeral=True
        )
        return

    # Write decrypted file
    decrypted_filename = attachment.filename.replace("encrypted_", "").replace(".bin", "")
    with open(decrypted_filename, "wb") as f:
        f.write(decrypted_bytes)

    # Send back the decrypted file privately
    decrypted_file = discord.File(decrypted_filename, filename=decrypted_filename)

    await interaction.followup.send(
        f"✅ File decrypted successfully!",
        file=decrypted_file,
        ephemeral=True
    )

    # Clean up temp file
    os.remove(decrypted_filename)


if __name__ == "__main__":
    bot.run(TOKEN)
