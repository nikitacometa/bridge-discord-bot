import logging

import discord
from discord import Message
from discord.abc import GuildChannel
from discord.ext import commands

from bot import db
from env import settings

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

logger = logging.getLogger(__name__)


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')


@bot.event
async def on_guild_join(discord_guild: discord.Guild):
    server = db.servers.get_or_create_with(
        id=discord_guild.id,
        name=discord_guild.name
    )
    logger.info(f'Joined server {server}')


@bot.event
async def on_guild_channel_create(discord_channel: GuildChannel):
    channel = db.group_channels.get_or_create_with(
        id=discord_channel.id,
        name=discord_channel.name,
        jump_url=discord_channel.jump_url,
        server_id=discord_channel.guild.id
    )
    logger.info(f'Created channel {channel}')


def get_user_or_create(discord_user: discord.User) -> db.User:
    user = db.users.get_by_primary_key(discord_user.id, throw_ex=False)
    if user is None:
        user = db.User(
            id=discord_user.id,
            name=discord_user.name,
            display_name=discord_user.display_name,
            colour=discord_user.colour
        )
        db.users.create(user)
        logger.info(f'Created user {user}')
    return user


@bot.event
async def on_message(message: Message):
    if message.author == bot.user:
        return

    user = get_user_or_create(message.author)
    logger.debug(f'User {user} sent message "{message.content}"')

    bridge_channels = db.group_channels.get_all()
    for channel in bridge_channels:
        channel = bot.get_channel(channel.id)
        if channel and channel != message.channel:
            embed = discord.Embed(
                title=f'Message from {message.author} in #{message.channel}',
                description=message.content,
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)

    await bot.process_commands(message)


if __name__ == '__main__':
    bot.run(settings.discord_api_token)
