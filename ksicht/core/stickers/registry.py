STICKERS = {}


def register(sticker_nr, validator_fn):
    STICKERS[sticker_nr] = validator_fn


def get(sticker_nr):
    return STICKERS[sticker_nr]


def get_all():
    return STICKERS.items()
