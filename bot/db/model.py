from dataclasses import dataclass, field
from datetime import datetime

import discord
from dataclasses_json import dataclass_json

from bot.db import BaseEntity
from bot.util import get_uuid


@dataclass_json
@dataclass
class Colour:
    value: int

    @classmethod
    def from_discord(cls, colour: discord.Colour):
        if colour is None:
            return None
        return cls(colour.value)


@dataclass_json
@dataclass
class User(BaseEntity['User']):
    name: str
    display_name: str

    id: int
    colour: Colour | None = None

    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)


@dataclass_json
@dataclass
class Server(BaseEntity['Server']):
    name: str

    id: str
    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)


@dataclass_json
@dataclass
class BridgeChannel(BaseEntity['BridgeChannel']):
    name: str
    bridge_name: str
    server_id: str
    server_name: str
    creator_id: str
    jump_url: str

    id: int
    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)


@dataclass_json
@dataclass
class Bridge(BaseEntity['Bridge']):
    name: str
    creator_id: int
    channel_ids: list[int] = field(default_factory=list)

    id: str = field(default_factory=get_uuid)
    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)


@dataclass_json
@dataclass
class BridgeMessage(BaseEntity['BridgeMessage']):
    text: str
    author_id: int
    channel_id: int
    bridge_name: str

    id: int
    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)


@dataclass_json
@dataclass
class ForwardedMessage(BaseEntity['ForwardedMessage']):
    original_id: int
    original_channel_id: int
    channel_id: int
    bridge_name: str

    id: int
    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)
