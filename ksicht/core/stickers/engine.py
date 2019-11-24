from . import registry


def resolve_stickers(context):
    """Get set of stickers where provided context resolves truthy."""
    entitled_to = set()

    for sticker_nr, sticker_resolver in registry.get_all():
        if sticker_resolver(context):
            entitled_to.add(sticker_nr)

    return entitled_to


def build_context(participant, grade):
    """Build context that will be passed down to individual sticker resolver functions."""
    return {}
