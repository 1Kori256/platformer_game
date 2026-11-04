from functools import lru_cache


@lru_cache(maxsize=128)
def text(font, value):
    return font.render(value, True, (240, 240, 240))


def debug(surface, font, *args):
    for i, arg in enumerate(args):
        surface.blit(text(font, str(arg)), (10, 10 + 16 * i))
