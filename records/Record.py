import dataclasses
import weakref


class RecordMeta(type):
    _dataclass_kwargs = weakref.WeakKeyDictionary()

    def __new__(mcs, name, bases, dic, *, encapsulating=frozenset(), **kwargs):
        new = super().__new__(mcs, name, bases, dic)

        dataclass_kwargs = {}

        for ancestor in reversed(type.mro(new)):
            if isinstance(ancestor, RecordMeta) and ancestor is not new:
                dataclass_kwargs.update(mcs._dataclass_kwargs[ancestor])
        dataclass_kwargs.update(kwargs)

        mcs._dataclass_kwargs[new] = dataclass_kwargs
        new = dataclasses.dataclass(**dataclass_kwargs)(new)

        for field in dataclasses.fields(new):
            setattr(new, field.name, field)

        return new


@dataclasses.dataclass
class Record(metaclass=RecordMeta):
    pass
