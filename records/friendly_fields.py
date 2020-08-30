import dataclasses


IS_FRIENDLY = "is_friendly"
FRIENDLY_NAME = "friendly_name"
FRIENDLY_FORMATTER = "friendly_formatter"


class FriendlyField:
    def __init__(self, f, /):
        self._field = f

    def __repr__(self):
        return f"{type(self).__name__}({self._field!r})"

    def __call__(self, instance):
        value = getattr(instance, self._field.name)
        if value is None:
            return str()
        return self.friendly_formatter(value)

    friendly_formatter = property(lambda self: self._field.metadata.get(FRIENDLY_FORMATTER, str))

    @property
    def friendly_name(self):
        return self._field.metadata.get(FRIENDLY_NAME) or self._field.name.replace("_", " ").capitalize()


def field(*args, **kwargs):
    metadata = kwargs.pop("metadata", {})

    for keyword in [IS_FRIENDLY, FRIENDLY_NAME, FRIENDLY_FORMATTER]:
        try:
            metadata[keyword] = kwargs.pop(keyword)
        except KeyError:
            continue

    return dataclasses.field(*args, metadata=metadata, **kwargs)


def get_friendly_fields(class_or_instance):
    for f in dataclasses.fields(class_or_instance):
        if not f.metadata.get(IS_FRIENDLY, True):
            continue

        yield FriendlyField(f)
