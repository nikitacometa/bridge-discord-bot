from dataclasses import dataclass
from datetime import datetime

from pymongo.collection import Collection
from typing import TypeVar, Generic, Any

EntityT = TypeVar('EntityT', bound='BaseEntity')


@dataclass
class DbManager(Generic[EntityT]):
    name: str
    elem_type: Any
    collection: Collection
    primary_key: str = 'id'

    def create(self, item: EntityT) -> EntityT:
        self.collection.insert_one(item.to_dict())
        return item

    def create_with(self, **kwargs) -> EntityT:
        item = self.elem_type(**kwargs)
        return self.create(item)

    def get_one(self, **kwargs) -> EntityT:
        item_dict = self.collection.find_one(kwargs)
        return self.from_dict(item_dict)

    def get_by_primary_key(self, val: Any, throw_ex: bool = True) -> EntityT:
        res = self.get_one(**{self.primary_key: val})
        if res is None and throw_ex:
            raise ValueError(f'No {self.name} found with {self.primary_key}={val}')
        return res

    def get_or_create(self, item: EntityT) -> EntityT:
        item_dict = item.to_dict()
        res = self.get_by_primary_key(item_dict.get(self.primary_key), throw_ex=False)
        if res is None:
            res = self.create(item)
        return res

    def get_or_create_with(self, **kwargs) -> EntityT:
        res = self.get_by_primary_key(kwargs.get(self.primary_key), throw_ex=False)
        if res is None:
            res = self.create_with(**kwargs)
        return res

    def get_many(self, **kwargs) -> list[EntityT]:
        items = self.collection.find(kwargs)
        return [self.elem_type.from_dict(i) for i in items]

    def get_by_array(self, field_name: str, values: list[Any]) -> list[EntityT]:
        return self.get_many(**{field_name: {'$in': values}})

    def get_all(self) -> list[EntityT]:
        return self.get_many()

    def count(self) -> int:
        return self.collection.count_documents({})

    def update(self, item: EntityT) -> EntityT:
        item.last_updated = datetime.utcnow()
        item_dict = item.to_dict()
        self.collection.update_one(
            {self.primary_key: item_dict.get(self.primary_key)}, {'$set': item_dict}
        )
        return item

    def update_with(self, item: EntityT, **kwargs) -> EntityT:
        item.last_updated = datetime.utcnow()
        item_dict = item.to_dict()
        item_dict.update(kwargs)
        self.collection.update_one(
            {self.primary_key: item_dict.get(self.primary_key)}, {'$set': item_dict}
        )
        return self.from_dict(item_dict)

    def remove(self, item: EntityT):
        item_dict = item.to_dict()
        return self.collection.delete_one(
            {self.primary_key: item_dict.get(self.primary_key)}
        )

    def remove_by(self, **kwargs) -> int:
        res = self.collection.delete_many(kwargs)
        return res.deleted_count

    def from_dict(self, item_dict: dict | None = None) -> EntityT:
        return self.elem_type.from_dict(item_dict) if item_dict is not None else None
