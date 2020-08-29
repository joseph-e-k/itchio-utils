import dataclasses

from datetime import datetime
from typing import Set, Tuple, Optional

DATETIME_FRIENDLY_FORMAT = "%Y-%m-%d %H:%M"


def field(**kwargs):
    base_kwargs = {}

    for key in ["default"]:
        if key in kwargs:
            base_kwargs[key] = kwargs.pop(key)

    return dataclasses.field(metadata=kwargs, **base_kwargs)


def format_datetime(dt: datetime):
    return dt.strftime(DATETIME_FRIENDLY_FORMAT)


@dataclasses.dataclass
class ItchMetadataBlock:
    published_at: Optional[datetime] = field(friendly_formatter=format_datetime, default=None)
    updated_at: Optional[datetime] = field(friendly_formatter=format_datetime, default=None)
    status: Optional[str] = None
    category: Optional[str] = None
    mean_rating: Optional[float] = None
    number_of_ratings: Optional[int] = None
    author_names: Set[str] = field(friendly_formatter=", ".join, default=frozenset())
    author_urls: Set[str] = field(friendly_name="Author URLs", friendly_formatter="\n".join, default=frozenset())
    genre: Optional[str] = None
    tags: Set[str] = field(friendly_formatter=", ".join, default=frozenset())
    links: Set[Tuple[str, str]] = field(
        friendly_formatter=lambda pairs: "\n".join(f"{pair[0]}: {pair[1]}" for pair in pairs),
        default=frozenset()
    )


@dataclasses.dataclass
class GameInfo(ItchMetadataBlock):
    title: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = field(friendly_name="URL", default=None)
    operating_systems: Set[str] = field(friendly_formatter=", ".join, default=frozenset())
    file_count: int = 1

    @classmethod
    def _iter_fields(cls):
        fields = list(dataclasses.fields(cls))
        fields.sort(key=lambda field: field in dataclasses.fields(ItchMetadataBlock))
        yield from fields

    @classmethod
    def _iter_friendly_field_names(cls):
        for field in cls._iter_fields():
            yield field.metadata.get("friendly_name") or field.name.replace("_", " ").capitalize()

    @classmethod
    def get_friendly_field_names(cls):
        return tuple(cls._iter_friendly_field_names())

    def _iter_friendly_field_values(self):
        for field in self._iter_fields():
            value = getattr(self, field.name)

            if value is None:
                yield str()
            else:
                friendly_formatter = field.metadata.get("friendly_formatter") or str
                yield friendly_formatter(value)

    def get_friendly_field_values(self):
        return tuple(self._iter_friendly_field_values())
