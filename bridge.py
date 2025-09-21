import discord
from guilded import Client as GuildedClient
import asyncio
import aiohttp

# --- Discord Setup ---
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# --- Guilded Setup ---
guilded_client = GuildedClient()

# --- Channel IDs (replace these with your own) ---
DISCORD_CHANNEL_ID = 1419347716336652399  # Replace with your Discord channel ID (integer)
GUILDED_CHANNEL_ID = "02738b0e-9898-42d2-ba58-a8166e022e49"   # Replace with your Guilded channel ID (string)

# --- Tokens (replace with your bot tokens) ---
DISCORD_BOT_TOKEN = "MTQxOTMyODcyOTYyMDE1NjY0Ng.GO0djX.H-KlkbQBOc0BVKu78PhvUme22m1Ndwix2WrxU0"
GUILDED_BOT_TOKEN = "gapi_0e4vkcSar3JWvPDHrLYH0JXI3rRhgrDoV4nb9rFKsrIcP/g5BLUTAg59HoGuEJlbyTyplWjsNuueuZEXxawwnA=="

# Shared queue
message_queue = asyncio.Queue()

# --- Discord Events ---
@discord_client.event
async def on_ready():
    print(f"✅ Logged in to Discord as {discord_client.user}")

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return
    if message.channel.id == DISCORD_CHANNEL_ID:
        print(f"[Discord -> Queue] {message.author.display_name}: {message.content}")
        await message_queue.put(("discord", message.content, message.author.display_name))

# --- Guilded Events ---
@guilded_client.event
async def on_ready():
    print(f"✅ Logged in to Guilded as {guilded_client.user}")

@guilded_client.event
async def on_message(message):
    if message.author_id == guilded_client.user.id:
        return
    if message.channel.id == GUILDED_CHANNEL_ID:
        print(f"[Guilded -> Queue] {message.author.name}: {message.content}")
        await message_queue.put(("guilded", message.content, message.author.name))

# --- Forwarder Task ---
async def forward_messages():
    while True:
        source, content, author = await message_queue.get()

        if source == "discord":
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://www.guilded.gg/api/v1/channels/{GUILDED_CHANNEL_ID}/messages"
                    headers = {
                        "Authorization": f"Bearer {GUILDED_BOT_TOKEN}",
                        "Content-Type": "application/json"
                    }
                    payload = {"content": f"**{author} (Discord):** {content}"}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status == 201:
                            print(f"[Forwarded] Discord -> Guilded: {author}: {content}")
                        else:
                            text = await resp.text()
                            print(f"❌ Guilded API error {resp.status}: {text}")
            except Exception as e:
                print(f"❌ Error sending to Guilded: {e}")

        elif source == "guilded":
            try:
                channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
                if channel:
                    await channel.send(f"**{author} (Guilded):** {content}")
                    print(f"[Forwarded] Guilded -> Discord: {author}: {content}")
            except Exception as e:
                print(f"❌ Error sending to Discord: {e}")

# --- Console Input Task ---
async def console_input():
    loop = asyncio.get_event_loop()
    while True:
        msg = await loop.run_in_executor(None, input, "> ")
        if not msg.strip():
            continue
        if msg.strip().lower() == "/quit":
            print("🛑 Shutting down bots...")
            await discord_client.close()
            await guilded_client.close()
            break

        # Send to Discord
        try:
            channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(f"**[Console]:** {msg}")
                print(f"[Console -> Discord] {msg}")
        except Exception as e:
            print(f"❌ Error sending console message to Discord: {e}")

        # Send to Guilded
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://www.guilded.gg/api/v1/channels/{GUILDED_CHANNEL_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {GUILDED_BOT_TOKEN}",
                    "Content-Type": "application/json"
                }
                payload = {"content": f"**[Console]:** {msg}"}
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 201:
                        print(f"[Console -> Guilded] {msg}")
                    else:
                        text = await resp.text()
                        print(f"❌ Guilded API error {resp.status}: {text}")
        except Exception as e:
            print(f"❌ Error sending console message to Guilded: {e}")

# --- Main ---
async def main():
    asyncio.create_task(forward_messages())
    asyncio.create_task(console_input())
    await asyncio.gather(
        discord_client.start(DISCORD_BOT_TOKEN),
        guilded_client.start(GUILDED_BOT_TOKEN),
    )

asyncio.run(main())