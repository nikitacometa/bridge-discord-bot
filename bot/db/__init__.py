from typing import TypeVar

from pymongo import MongoClient

from bot.db.base_entity import BaseEntity
from bot.db.db_manager import DbManager
from bot.db.model import *
from env import settings

mongo_client = MongoClient(host=settings.mongodb_host, port=settings.mongodb_port)


EntityT = TypeVar('EntityT', bound=BaseEntity)


def new_collection(name: str, elem_type: type[EntityT], primary_key: str = 'id') -> DbManager[EntityT]:
    return DbManager[EntityT](name, elem_type, mongo_client[settings.service_name][name], primary_key=primary_key)


users: DbManager[User] = new_collection('users', User)
servers: DbManager[Server] = new_collection('servers', Server)
bridge_channels: DbManager[BridgeChannel] = new_collection('bridge_channels', BridgeChannel)
bridges: DbManager[Bridge] = new_collection('bridges', Bridge, primary_key='name')
bridge_messages: DbManager[BridgeMessage] = new_collection('bridge_messages', BridgeMessage)
forwarded_messages: DbManager[ForwardedMessage] = new_collection('forwarded_messages', ForwardedMessage)
