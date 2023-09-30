from abc import abstractmethod
from datetime import datetime

from typing import Any, TypeVar, Generic, get_args

EntityT = TypeVar('EntityT')


# MUST be dataclass and dataclass_json
class BaseEntity(Generic[EntityT]):
    @abstractmethod
    def id(self) -> str | int:
        pass

    @abstractmethod
    def updated(self) -> datetime:
        pass

    @abstractmethod
    def created(self) -> datetime:
        pass

    @classmethod
    def from_dict(cls, data: dict) -> EntityT:
        return cls.from_dict(data)

    def to_dict(self):
        return self.to_dict()

    def field(self, name: str, default_factory: callable = None) -> Any:
        res = getattr(self, name)
        if res is None and default_factory is not None:
            res = default_factory()
            setattr(self, name, res)
        return res

    def __init_subclass__(cls) -> None:
        cls._class = get_args(cls.__orig_bases__[0])[0]  # type: ignore

    def get_class(self):
        return self._class
