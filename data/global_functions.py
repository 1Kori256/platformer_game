"""
All functions that aren't game specific.
"""


import pygame


# Loads image from certain path ----------------------------------------------------------------------------
def load_image(path):

    image = pygame.image.load(path).convert()
    image.set_colorkey((255,255,255))
    return image


# Returns only part of an image as a surface ---------------------------------------------------------------
def clip(surf, x, y, x_size, y_size):
    
    clipped_rectangle = pygame.Rect(x, y, x_size, y_size)
    surf.set_clip(clipped_rectangle)
    image = surf.subsurface(surf.get_clip())
    return image.copy()