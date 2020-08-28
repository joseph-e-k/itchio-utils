import dataclasses
from typing import Set, Optional


@dataclasses.dataclass
class GameInfo:
    title: str
    summary: str
    url: str = dataclasses.field(metadata=dict(friendly_name="URL"))
    operating_systems: Set[str] = dataclasses.field(metadata=dict(friendly_formatter=", ".join))
    file_count: int

    @classmethod
    def _iter_friendly_field_names(cls):
        for field in dataclasses.fields(cls):
            yield field.metadata.get('friendly_name') or field.name.replace("_", " ").capitalize()

    @classmethod
    def get_friendly_field_names(cls):
        return tuple(cls._iter_friendly_field_names())

    def _iter_friendly_field_values(self):
        for field, value in zip(dataclasses.fields(self), dataclasses.astuple(self)):
            friendly_formatter = field.metadata.get("friendly_formatter") or str
            yield friendly_formatter(value)

    def get_friendly_field_values(self):
        return tuple(self._iter_friendly_field_values())
