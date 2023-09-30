from typing import TypeVar

from pymongo import MongoClient

from bot.db.base_entity import BaseEntity
from bot.db.db_manager import DbManager
from bot.db.model import User, Server, GroupChannel, Bridge
from env import settings

mongo_client = MongoClient(host=settings.mongodb_host, port=settings.mongodb_port)


EntityT = TypeVar('EntityT', bound=BaseEntity)


def new_collection(name: str, elem_type: type[EntityT]) -> DbManager[EntityT]:
    return DbManager[EntityT](name, elem_type, mongo_client[settings.bot_name][name])


users: DbManager[User] = new_collection('users', User)
servers: DbManager[Server] = new_collection('servers', Server)
group_channels: DbManager[GroupChannel] = new_collection('group_channels', GroupChannel)
bridges: DbManager[Bridge] = new_collection('bridges', Bridge)
