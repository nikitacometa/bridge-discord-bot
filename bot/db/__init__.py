from typing import Any

from pymongo import MongoClient

from bot.db.base_entity import BaseEntity
from bot.db.db_manager import DbManager
from env import settings

mongo_client = MongoClient(host=settings.mongodb_host, port=settings.mongodb_port)


EntityT = type('EntityT', bound=BaseEntity)


def new_collection(name: str, elem_type: type[EntityT]) -> DbManager[EntityT]:
    return DbManager[EntityT](name, elem_type, mongo_client[settings.service_name][name])


