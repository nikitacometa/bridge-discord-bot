import logging

import discord
from discord import Message
from discord.ext import commands

from bot import db
from env import settings

LOG_FORMAT = '[%(asctime)s][%(levelname)s][%(name)s] %(message)s'
LOG_DATE_FORMAT = '%I:%M:%S'
logging.basicConfig(
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    level=settings.log_level
)
logging.getLogger('discord').setLevel(settings.log_level)
logging.getLogger('discord.http').setLevel(logging.INFO)
logging.getLogger('discord.gateway').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


def get_user_or_create(discord_user: discord.User) -> db.User:
    user = db.users.get_by_primary_key(discord_user.id, throw_ex=False)
    if user is None:
        user = db.User(
            id=discord_user.id,
            name=discord_user.name,
            display_name=discord_user.display_name
        )
        db.users.create(user)
        logger.info(f'Created user {user}')
    return user


# COMMAND HANDLERS

@bot.command()
async def show_servers(ctx: commands.Context):
    servers = db.servers.get_all()
    text = f'In total **{len(servers)} servers.**\n\n'

    for i, server in enumerate(servers):
        text += f'{i + 1}. {server.name}\n'

    text += f'\n*!show_server_channels <number> to show channels of a server.*'
    await ctx.send(text)


@bot.command()
async def create_bridge(ctx: commands.Context, name: str):
    creator = get_user_or_create(ctx.author)
    bridge = db.bridges.create(db.Bridge(
        name=name,
        creator_id=creator.id
    ))
    logger.info(f'Created bridge {bridge}')

    text = f'Created bridge {bridge.name}.\n' \
           f'\n' \
           f'*!bridge_add_channel <name> to add a server channel to the bridge.*'

    await ctx.send(text)


@bot.command()
async def bridge_add_channel(ctx: commands.Context, name: str):
    channels = ctx.guild.channels
    text = f'In total **{len(channels)} channels on {ctx.guild.name}.**\n\n'
    for i, channel in enumerate(channels):
        text += f'{i + 1}. {channel.name}\n'
    text += f'\n' \
            f'*!bridge_add_choose <name> <number> to add.*'
    await ctx.send(text)


@bot.command()
async def bridge_add_choose(ctx: commands.Context, name: str, number: int):
    bridge = db.bridges.get_by_primary_key(name, throw_ex=False)
    if bridge is None:
        await ctx.send(f'Bridge {name} not found.')
        return

    # TODO: check if channel is already in bridge

    channels = ctx.guild.channels
    channel = channels[number - 1]
    bridge.channel_ids.append(channel.id)
    db.bridges.update(bridge)

    db.bridge_channels.create(
        db.BridgeChannel(
            id=channel.id,
            name=channel.name,
            bridge_name=bridge.name,
            jump_url=channel.jump_url,
            server_id=ctx.guild.id
        )
    )

    logger.info(f'Updated bridge {bridge}')

    text = f'Added channel {channel.name} to bridge {bridge.name}.\n' \
           f'\n' \
           f'*!bridge_add_channel <name> to add another channel from this server.*'
    await ctx.send(text)


@bot.command()
async def show_server_channels(ctx: commands.Context):
    channels = ctx.guild.channels
    text = f'In total **{len(channels)} channels on {ctx.guild.name}.**\n\n'
    for i, channel in enumerate(channels):
        text += f'{i + 1}. {channel.name}\n'

    await ctx.send(text)


# EVENT HANDLERS

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
async def on_message(message: Message):
    if message.author == bot.user:
        return

    user = get_user_or_create(message.author)
    logger.debug(f'User {user.name} sent message:\n{message}')

    bridge_channels = db.bridge_channels.get_many(id=message.channel.id)
    for bridge_channel in bridge_channels:
        bridge = db.bridges.get_by_primary_key(bridge_channel.bridge_name)
        logger.debug(f'{bridge_channel.id} channel has bridge {bridge}')
        for channel_id in bridge.channel_ids:
            if channel_id == bridge_channel.id:
                continue
            channel = bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title=f'Message from {message.author} in #{message.channel}',
                    description=message.content,
                    color=discord.Color.blue()
                )
                await channel.send(embed=embed)
            else:
                logger.error(f'Channel {channel_id} not found for bridge {bridge}')

    await bot.process_commands(message)


if __name__ == '__main__':
    bot.run(settings.discord_api_token, log_handler=None)
