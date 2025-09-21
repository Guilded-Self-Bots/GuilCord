import discord
from guilded import Client as GuildedClient
import asyncio

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

# Queue to move messages between bots
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
        await message_queue.put(("discord", message.content, message.author.display_name))

# --- Guilded Events ---
@guilded_client.event
async def on_ready():
    print(f"✅ Logged in to Guilded as {guilded_client.user}")

@guilded_client.event
async def on_message(message):
    if message.created_by == guilded_client.user.id:
        return
    if message.channel.id == GUILDED_CHANNEL_ID:
        await message_queue.put(("guilded", message.content, message.author.name))

# --- Forwarder Task ---
async def forward_messages():
    await discord_client.wait_until_ready()
    await guilded_client.wait_until_ready()

    while True:
        source, content, author = await message_queue.get()

        if source == "discord":
            channel = guilded_client.get_channel(GUILDED_CHANNEL_ID)
            if channel:
                await channel.send(f"**{author} (Discord):** {content}")

        elif source == "guilded":
            channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(f"**{author} (Guilded):** {content}")

# --- Run both bots together ---
async def main():
    asyncio.create_task(forward_messages())
    await asyncio.gather(
        discord_client.start(DISCORD_BOT_TOKEN),
        guilded_client.start(GUILDED_BOT_TOKEN),
    )

asyncio.run(main())
