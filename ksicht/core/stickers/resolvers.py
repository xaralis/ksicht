from functools import wraps

from . import registry


def sticker(sticker_nr):
    def wrapped(resolver_fn):
        return resolver_fn

    registry.register(sticker_nr, wrapped)

    return wrapped


@sticker(1)
def solver(context):
    pass


@sticker(2)
def five_rounds(context):
    pass
