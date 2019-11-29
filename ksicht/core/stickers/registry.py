STICKERS = {}


def register(sticker_nr, validator_fn):
    global STICKERS  # pylint: disable=global-statement
    STICKERS[sticker_nr] = validator_fn


def get(sticker_nr):
    global STICKERS  # pylint: disable=global-statement
    return STICKERS[sticker_nr]


def get_all():
    global STICKERS  # pylint: disable=global-statement
    return STICKERS.items()
