from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import dataclass_json
from discord import Colour

from bot.db import BaseEntity
from bot.util import get_uuid


@dataclass_json
@dataclass
class User(BaseEntity['User']):
    name: str
    display_name: str
    colour: Colour

    id: str
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
class GroupChannel(BaseEntity['GroupChannel']):
    name: str
    jump_url: str
    server_id: str

    id: int
    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)


@dataclass_json
@dataclass
class Bridge(BaseEntity['Bridge']):
    name: str
    creator_id: str
    channel_ids: list[str] = field(default_factory=list)

    id: str = field(default_factory=get_uuid)
    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)
