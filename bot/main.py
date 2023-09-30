import discord
from discord.ext import commands
from pymongo import MongoClient

# Replace this with your bot's token and MongoDB URI
TOKEN = 'your_bot_token'
MONGO_URI = 'your_mongo_uri'

bot = commands.Bot(command_prefix='!')

# Set up the MongoDB client
client = MongoClient(MONGO_URI)
db = client['discord_bot_db']
channels_collection = db['channels']


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.event
async def on_guild_channel_create(channel):
    # Save the new channel to the database
    channels_collection.insert_one({'channel_id': channel.id})


@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Forward the message to all other saved channels
    saved_channels = channels_collection.find()
    for saved_channel in saved_channels:
        channel_id = saved_channel['channel_id']
        channel = bot.get_channel(channel_id)
        if channel and channel != message.channel:
            embed = discord.Embed(
                title=f"Message from {message.author} in #{message.channel}",
                description=message.content,
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)

    # Process commands after handling the message
    await bot.process_commands(message)


bot.run(TOKEN)
