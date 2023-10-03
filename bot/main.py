import logging

import discord
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
            display_name=discord_user.display_name,
            colour=db.Colour.from_discord(discord_user.colour)
        )
        db.users.create(user)
        logger.info(f'Created user {user}')
    return user


# COMMAND HANDLERS

@bot.command()
async def get_servers(ctx: commands.Context):
    servers = db.servers.get_all()
    text = f'In total **{len(servers)} servers.**\n' \
           f'\n'

    for i, server in enumerate(servers):
        text += f'{i + 1}. {server.name}\n'

    text += f'*!get_server_channels to show channels of **the current server**.*'
    await ctx.send(text)


@bot.command()
async def get_server_channels(ctx: commands.Context):
    channels = ctx.guild.channels
    text = f'In total **{len(channels)} channels on {ctx.guild.name}.**\n\n'
    for i, channel in enumerate(channels):
        text += f'{i + 1}. {channel.name}\n'
    text += f'\n' \
            f'*!bridge_add_channel <name> <number> to add to the bridge **<name>**.*'
    await ctx.send(text)


@bot.command()
async def create_bridge(ctx: commands.Context, name: str):
    creator = get_user_or_create(ctx.author)
    bridge = db.bridges.get_one(name=name)
    if bridge is not None:
        await ctx.send(f'Sorry, bridge **{name}** already exists. Please try different name.')
        return

    bridge = db.bridges.create(db.Bridge(
        name=name,
        creator_id=creator.id
    ))
    logger.info(f'Created bridge {bridge}')

    text = f'Congratulations! New bridge **{bridge.name}**.\n' \
           f'\n' \
           f'*!bridge_add_channel to add the current server channel to the bridge.*'

    await ctx.send(text)


@bot.command()
async def get_bridges(ctx: commands.Context):
    bridges = db.bridges.get_many(creator_id=ctx.author.id)
    text = f'In total you created **{len(bridges)} bridges.**\n' \
           f'\n'

    for i, bridge in enumerate(bridges):
        text += f'{i + 1}. **{bridge.name}**\n'

    text += f'*!get_bridge <name> to show channels of a bridge.*'
    await ctx.send(text)


@bot.command()
async def get_bridge(ctx: commands.Context, name: str):
    bridge = db.bridges.get_one(name=name)
    if bridge is None:
        await ctx.send(f'So sorry, but... Bridge {name} not found.')
        return

    bridge_channels = db.bridge_channels.get_many(bridge_name=bridge.name)
    channels_str = '\n'.join([
        f'{i + 1}. #{bridge_channel.name} from **{bridge_channel.server_name}**'
        for i, bridge_channel in enumerate(bridge_channels)
    ])
    text = f'Bridge **{bridge.name}** has {len(bridge_channels)} channels:\n' \
           f'\n' \
           f'{channels_str}'
    await ctx.send(text)


@bot.command()
async def bridge_add_channel(ctx: commands.Context, name: str, number: int):
    bridge = db.bridges.get_one(name=name)
    if bridge is None:
        await ctx.send(f'Oof, sorry. Bridge {name} not found.')
        return

    channels = ctx.guild.channels
    channel = channels[number - 1]
    bridge_channel = db.bridge_channels.get_one(id=channel.id, bridge_name=name)
    if bridge_channel is not None:
        await ctx.send(f'Oops, channel **{channel.name}** already in the bridge **{name}**.')
        return

    bridge_channel = db.BridgeChannel(id=channel.id, name=channel.name, bridge_name=bridge.name, creator_id=ctx.author.id,
                                      jump_url=channel.jump_url, server_id=ctx.guild.id, server_name=ctx.guild.name)
    db.bridge_channels.create(bridge_channel)
    logger.info(f'Created bridge channel: {bridge_channel}')

    bridge.channel_ids.append(channel.id)
    db.bridges.update(bridge)
    logger.info(f'Updated bridge: {bridge}')

    text = f'Added channel **{channel.name}** to bridge {bridge.name}.\n' \
           f'\n' \
           f'*!bridge_add_channel {bridge.name} <number> to add another.*'
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


async def bridge_send_message(bridge_channel: db.BridgeChannel, message: discord.Message):
    bridge = db.bridges.get_one(name=bridge_channel.bridge_name)
    if bridge is None:
        logger.error(f'Bridge {bridge_channel.bridge_name} not found for channel {bridge_channel.id}')
        return
    if len(bridge.channel_ids) <= 1:
        logger.warning(f'Bridge {bridge_channel.bridge_name} has only one channel, nowhere to forward.')
        return

    bridge_message = db.BridgeMessage(
        id=message.id,
        text=message.content,
        author_id=message.author.id,
        channel_id=message.channel.id,
        bridge_name=bridge.name
    )
    db.bridge_messages.create(bridge_message)
    logger.debug(f'Forwarding message {bridge_message} to bridge {bridge}')

    for channel_id in bridge.channel_ids:
        if channel_id == bridge_channel.id:
            # skip current channel
            continue

        channel = bot.get_channel(channel_id)
        if channel is None:
            logger.error(f'Channel {channel_id} not found for bridge {bridge}')

        embed = discord.Embed(
            title=f'Message from {message.author} in #{message.channel}',
            description=message.content,
            color=discord.Color.blue()
        )
        bot_message = await channel.send(embed=embed)
        forwarded_message = db.ForwardedMessage(
            id=bot_message.id,
            original_id=bridge_message.id,
            original_channel_id=bridge_message.channel_id,
            channel_id=channel_id,
            bridge_name=bridge.name
        )
        db.forwarded_messages.create(forwarded_message)
        logger.debug(f'Forwarded message {forwarded_message}')


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    user = get_user_or_create(message.author)
    logger.debug(f'User {user.name} sent message:\n{message}')

    bridge_channels = db.bridge_channels.get_many(id=message.channel.id)
    for bridge_channel in bridge_channels:
        await bridge_send_message(bridge_channel, message)

    await bot.process_commands(message)


if __name__ == '__main__':
    bot.run(settings.discord_api_token, log_handler=None)
