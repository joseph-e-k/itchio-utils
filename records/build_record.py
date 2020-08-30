_decorated_functions = {}


class RecordBuilder:
    _field_builders = {}

    @classmethod
    def _get_field_builders(cls):
        field_builders = dict()

        for ancestor in cls.mro():
            if not issubclass(ancestor, RecordBuilder):
                continue
            field_builders.update(ancestor._field_builders)

        return field_builders

    def __init_subclass__(cls, **kwargs):
        for cls_member in vars(cls).values():
            if not callable(cls_member):
                continue
            try:
                field = _decorated_functions[cls_member]
            except KeyError:
                continue
            cls._field_builders[field] = cls_member

    def build(self, record_type, *args, **kwargs):
        field_names_to_values = {}
        for field, builder_method in self._get_field_builders().items():
            if field is None:
                pass
            field_names_to_values[field.name] = builder_method(self, *args, **kwargs)

        return record_type(**field_names_to_values)


def field_builder(field):
    def decorator(func):
        _decorated_functions[func] = field
        return func
    return decorator
