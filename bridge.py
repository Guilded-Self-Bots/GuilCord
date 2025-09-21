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
DISCORD_CHANNEL_ID = 1419274388469055580  # Replace with your Discord channel ID (integer)
GUILDED_CHANNEL_ID = "7e430fd3-836c-45a6-9c32-645762596458"   # Replace with your Guilded channel ID (string)

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

# --- Forwarder ---
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
                    payload = {
                        "content": f"**{author}:** {content}"
                    }
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
                    await channel.send(f"**{author}:** {content}")
                    print(f"[Forwarded] Guilded -> Discord: {author}: {content}")
            except Exception as e:
                print(f"❌ Error sending to Discord: {e}")

# --- Run both bots ---
async def main():
    asyncio.create_task(forward_messages())
    await asyncio.gather(
        discord_client.start(DISCORD_BOT_TOKEN),
        guilded_client.start(GUILDED_BOT_TOKEN),
    )

asyncio.run(main())