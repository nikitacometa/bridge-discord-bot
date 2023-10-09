import logging

import discord
from discord.ext import commands
from discord.ui import Button, View

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
logging.getLogger('discord.client').setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
logging.getLogger('discord.gateway').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
COMMAND_PREFIX = '/'
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)


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


# BRIDGE MANAGEMENT

@bot.command()
async def show_my_bridges(ctx: commands.Context):
    bridges = db.bridges.get_many(creator_id=ctx.author.id)
    text = f'🤝 You created **{len(bridges)} bridges.**\n' \
           f'\n'

    for i, bridge in enumerate(bridges):
        text += f'{i + 1}. **{bridge.name}**\n'

    text += f'***{COMMAND_PREFIX}show_bridge <name>** to show bridge channels.*\n' \
            f'***{COMMAND_PREFIX}create_bridge <name>** to create a new bridge.*'
    await ctx.send(text)


# BRIDGE COMMANDS

@bot.command()
async def create_bridge(ctx: commands.Context, bridge_name: str):
    creator = get_user_or_create(ctx.author)
    bridge = db.bridges.get_one(name=bridge_name)
    if bridge is not None:
        await ctx.send(f'Sorry, bridge **{bridge_name}** already exists. Please try different name.')
        return

    bridge = db.bridges.create(db.Bridge(
        name=bridge_name,
        creator_id=creator.id
    ))
    logger.info(f'Created bridge {bridge}')

    text = f'✅ Congratulations! New bridge **{bridge.name}**.\n' \
           f'\n' \
           f'***{COMMAND_PREFIX}add_channel_to_bridge {bridge_name}** to add a channel from server **{ctx.guild.name}**.*'

    await ctx.send(text)


@bot.command()
async def show_bridge(ctx: commands.Context, bridge_name: str):
    bridge = db.bridges.get_one(name=bridge_name)
    if bridge is None:
        await ctx.send(f'So sorry, but... Bridge {bridge_name} not found.')
        return

    bridge_channels = db.bridge_channels.get_many(bridge_name=bridge.name)
    channels_str = '\n'.join([
        f'{i + 1}. #{bridge_channel.name} from **{bridge_channel.server_name}**'
        for i, bridge_channel in enumerate(bridge_channels)
    ])
    text = f'💡 Bridge **{bridge.name}** has {len(bridge_channels)} channels.\n' \
           f'\n' \
           f'{channels_str}\n' \
           f'\n' \
           f'*{COMMAND_PREFIX}add_channel_to_bridge {bridge.name} to add another.*\n' \
           f'*{COMMAND_PREFIX}remove_channel_from_bridge {bridge.name} to remove.*'
    await ctx.send(text)


# BRIDGE ADD

class AddChannelButton(Button):
    def __init__(self, channel: discord.TextChannel, bridge: db.Bridge, server_name: str, creator_id: int):
        super().__init__(label=channel.name, style=discord.ButtonStyle.primary)
        self.channel = channel
        self.bridge = bridge
        self.server_name = server_name
        self.creator_id = creator_id

    async def callback(self, interaction: discord.Interaction):
        bridge_channel = db.bridge_channels.get_one(id=self.channel.id, bridge_name=self.bridge.name)
        if bridge_channel is not None:
            await interaction.response.send_message(
                f'Oops, channel **{self.channel.name}** already in the bridge **{self.bridge.name}**.'
            )
            return

        bridge_channel = db.BridgeChannel(
            id=self.channel.id,
            name=self.channel.name,
            bridge_name=self.bridge.name,
            creator_id=self.creator_id,
            server_name=self.server_name
        )
        db.bridge_channels.create(bridge_channel)
        logger.info(f'Created bridge channel: {bridge_channel}')

        self.bridge.channel_ids.append(self.channel.id)
        db.bridges.update(self.bridge)
        logger.info(f'Updated bridge: {self.bridge}')

        text = f'✅ Added channel **{self.channel.name}** to bridge {self.bridge.name}.'
        await interaction.response.send_message(text)


class AddChannelSelector(View):
    def __init__(self, channels: list[discord.TextChannel], bridge: db.Bridge, creator_id: int, server_name: str):
        super().__init__()
        for channel in channels:
            self.add_item(
                AddChannelButton(channel=channel, bridge=bridge, creator_id=creator_id, server_name=server_name)
            )


@bot.command()
async def add_channel_to_bridge(ctx: commands.Context, bridge_name: str):
    bridge = db.bridges.get_one(name=bridge_name)
    if bridge is None:
        await ctx.send(f'Oof, sorry. Bridge {bridge_name} not found.')
        return

    channels = ctx.guild.text_channels
    i = 0
    while i < len(channels):
        # max 25 buttons per view
        chunk_last_idx = min(i + 25, len(channels))
        view = AddChannelSelector(channels[i:chunk_last_idx], bridge, ctx.author.id, ctx.guild.name)
        await ctx.send(f'👇 Select **{ctx.guild.name}** channel to add to the bridge **{bridge_name}**:', view=view)
        i += 25


# BRIDGE REMOVE

class RemoveChannelButton(Button):
    def __init__(self, bridge_channel: db.BridgeChannel, bridge: db.Bridge):
        super().__init__(label=f'#{bridge_channel.name}:{bridge_channel.server_name}', style=discord.ButtonStyle.primary)
        self.bridge_channel = bridge_channel
        self.bridge = bridge

    async def callback(self, interaction: discord.Interaction):
        db.bridge_channels.remove_by(id=self.bridge_channel.id, bridge_name=self.bridge.name)

        self.bridge.channel_ids.remove(self.bridge_channel.id)
        db.bridges.update(self.bridge)
        logger.info(f'Updated bridge: {self.bridge}')

        text = f'✅ Removed channel **{self.label}** from the bridge **{self.bridge.name}**.'
        await interaction.response.send_message(text)


class RemoveChannelSelector(View):
    def __init__(self, bridge_channels: list[db.BridgeChannel], bridge: db.Bridge):
        super().__init__()
        for bridge_channel in bridge_channels:
            self.add_item(
                RemoveChannelButton(bridge_channel=bridge_channel, bridge=bridge)
            )


@bot.command()
async def remove_channel_from_bridge(ctx: commands.Context, bridge_name: str):
    bridge = db.bridges.get_one(name=bridge_name)
    if bridge is None:
        await ctx.send(f'Oof, sorry. Bridge {bridge_name} not found.')
        return
    if bridge.creator_id != ctx.author.id:
        await ctx.send(f'Sorry, only bridge creator can remove channels.')
        return

    bridge_channels = db.bridge_channels.get_many(bridge_name=bridge.name)
    if len(bridge_channels) == 0:
        await ctx.send(f'Oops, bridge **{bridge.name}** has no channels.')
        return

    i = 0
    while i < len(bridge_channels):
        # max 25 buttons per view
        chunk_last_idx = min(i + 25, len(bridge_channels))
        view = RemoveChannelSelector(bridge_channels[i:chunk_last_idx], bridge)
        await ctx.send(f'👇 Choose channel to remove from the bridge **{bridge_name}**:', view=view)
        i += 25


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
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    user = get_user_or_create(message.author)
    logger.debug(f'User {user.name} sent message:\n{message}')

    if not message_is_command(message):
        reply_handled = await handle_reply_message(message)
        if not reply_handled:
            await handle_bridge_message(message)

    await bot.process_commands(message)


# IMPLEMENTATIONS (move to separate files)

def get_user_color(user: discord.User) -> discord.Colour:
    if not user.colour:
        return discord.Colour.green()
    return user.colour


async def bridge_channel_forward_message(
        channel: discord.TextChannel,
        bridge_name: str,
        message: discord.Message,
        reference: discord.MessageReference | None = None
):
    embed = discord.Embed(
        description=message.content,
        color=get_user_color(message.author)
    )
    embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url, url=message.jump_url)
    embed.set_footer(text=f'Server: {message.guild.name}', icon_url=message.guild.icon.url)
    embed.set_thumbnail(url=message.jump_url)
    bot_message = await channel.send(embed=embed, reference=reference)
    forwarded_message = db.ForwardedMessage(
        id=bot_message.id,
        original_id=message.id,
        original_channel_id=message.channel.id,
        channel_id=channel.id,
        bridge_name=bridge_name
    )
    db.forwarded_messages.create(forwarded_message)
    logger.debug(f'Forwarded message {forwarded_message}')


async def bridge_forward_message(
        bridge_name: str,
        message: discord.Message,
        channel_id: int,
        reference: discord.MessageReference | None = None
):
    channel = bot.get_channel(channel_id)
    if channel is None:
        logger.error(f'Channel {channel_id} not found for bridge {bridge_name}')

    await bridge_channel_forward_message(channel, bridge_name, message, reference)


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
    logger.debug(f'Forwarding message {bridge_message.id} to bridge {bridge.name}')

    for channel_id in bridge.channel_ids:
        if channel_id == bridge_channel.id:
            # skip current channel
            continue

        await bridge_forward_message(bridge.name, message, channel_id)


def message_is_command(message: discord.Message) -> bool:
    return message.content is not None and message.content.startswith(COMMAND_PREFIX)


async def handle_bridge_message(message: discord.Message):
    bridge_channels = db.bridge_channels.get_many(id=message.channel.id)
    if len(bridge_channels) == 0:
        return

    for bridge_channel in bridge_channels:
        await bridge_send_message(bridge_channel, message)


async def handle_reply_message(message: discord.Message) -> bool:
    if message.reference is None:
        return False

    forwarded_message = db.forwarded_messages.get_one(id=message.reference.message_id)
    if forwarded_message is None:
        # has reply but not to bridge message
        return False

    await bridge_forward_message(
        forwarded_message.bridge_name,
        message,
        forwarded_message.original_channel_id,
        reference=discord.MessageReference(
            message_id=forwarded_message.original_id,
            channel_id=forwarded_message.original_channel_id
        )
    )
    return True


if __name__ == '__main__':
    bot.run(settings.discord_api_token, log_handler=None)
