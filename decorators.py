import functools


def aggregator(aggregate):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            iterable = func(*args, **kwargs)
            return aggregate(iterable)
        return wrapper
    return decorator
