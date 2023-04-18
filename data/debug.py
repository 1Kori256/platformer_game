import pygame

def debug(surface, font, *args):
    debug_surface = pygame.Surface((100, 8 + 16 * (len(args) - 1)))
    debug_surface.set_colorkey((0, 0, 0))
    for i, arg in enumerate(args):
        text_object = font.render(f"{arg}", True, (240,240,240))
        debug_surface.blit(text_object, (0, i * 16))
    surface.blit(debug_surface, (10, 10))