import dataclasses

from datetime import datetime
from typing import Set, Tuple, Optional, Sequence

from decorators import aggregator
from records.friendly_fields import field, get_friendly_fields

DATETIME_FRIENDLY_FORMAT = "%Y-%m-%d %H:%M"


def format_datetime(dt: datetime):
    return dt.strftime(DATETIME_FRIENDLY_FORMAT)


@dataclasses.dataclass(frozen=True)
class ItchGamePageInfo:
    description: Optional[str] = None
    published_at: Optional[datetime] = field(friendly_formatter=format_datetime, default=None)
    updated_at: Optional[datetime] = field(friendly_formatter=format_datetime, default=None)
    status: Optional[str] = None
    category: Optional[str] = None
    mean_rating: Optional[float] = None
    number_of_ratings: Optional[int] = None
    author_names: Sequence[str] = field(friendly_formatter=", ".join, default=())
    author_urls: Sequence[str] = field(friendly_name="Author URLs", friendly_formatter="\n".join, default=())
    genre: Optional[str] = None
    tags: Set[str] = field(friendly_formatter=", ".join, default=frozenset())
    links: Set[Tuple[str, str]] = field(
        friendly_formatter=lambda pairs: "\n".join(f"{pair[0]}: {pair[1]}" for pair in pairs),
        default=frozenset()
    )


@dataclasses.dataclass(frozen=True)
class GameInfo:
    title: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = field(friendly_name="URL", default=None)
    operating_systems: Set[str] = field(friendly_formatter=", ".join, default=frozenset())
    file_count: int = 1
    details: Optional[ItchGamePageInfo] = field(is_friendly=False, default=ItchGamePageInfo())

    @classmethod
    def _get_user_facing_data(cls):
        return [
            (f.friendly_name, f) for f in get_friendly_fields(cls)
        ] + [
            (f.friendly_name, lambda self, f=f: f(self.details)) for f in get_friendly_fields(ItchGamePageInfo)
        ]

    @classmethod
    @aggregator(tuple)
    def get_user_facing_field_names(cls):
        for name, getter in cls._get_user_facing_data():
            yield name

    @aggregator(tuple)
    def get_user_facing_field_values(self):
        for name, getter in self._get_user_facing_data():
            yield getter(self)
