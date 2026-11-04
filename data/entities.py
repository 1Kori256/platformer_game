import math
from functools import lru_cache
import pygame

animation_database = {}


def collision_test(rect, platforms):
    return [platforms[i] for i in rect.collidelistall(platforms)]


@lru_cache(maxsize=256)
def transformed(image, flipped, rotation):
    if flipped:
        image = pygame.transform.flip(image, True, False)
    return pygame.transform.rotate(image, rotation) if rotation else image


def flip(image, boolean=True):
    return transformed(image, boolean, 0)


def blit_center(surface, image, pos):
    surface.blit(image, (pos[0] - image.get_width() // 2, pos[1] - image.get_height() // 2))


def animation_sequence(sequence, base_path, colorkey=(255, 255, 255), transparency=255):
    result = []
    for number, duration in sequence:
        image_id = base_path + str(number)
        if image_id not in animation_database:
            image = pygame.image.load(image_id + '.png').convert()
            image.set_colorkey(colorkey)
            image.set_alpha(transparency)
            animation_database[image_id] = image
        result.extend([image_id] * duration)
    return result


def get_frame(id):
    return animation_database[id]


class entity:
    def __init__(self, x, y, size_x, size_y):
        self.x, self.y = x, y
        self.size_x, self.size_y = size_x, size_y
        self.obj = PhysicsObject(x, y, size_x, size_y)
        self.animation = None
        self.image = None
        self.animation_frame = 0
        self.animation_tags = []
        self.flip = False
        self.offset = [0, 0]
        self.rotation = 0

    def set_pos(self, x, y):
        self.x = self.obj.x = x
        self.y = self.obj.y = y
        self.obj.rect.topleft = (int(x), int(y))

    def move(self, movement, platforms, ramps):
        result = self.obj.move(movement, platforms, ramps)
        self.x, self.y = self.obj.x, self.obj.y
        return result

    def rect(self):
        return pygame.Rect(self.x, self.y, self.size_x, self.size_y)

    def set_flip(self, boolean):
        self.flip = boolean

    def set_animation_tags(self, tags):
        self.animation_tags = tags

    def set_animation(self, sequence):
        self.animation = sequence
        self.animation_frame = 0

    def clear_animation(self):
        self.animation = None

    def set_image(self, image):
        self.image = image

    def set_offset(self, offset):
        self.offset = offset

    def set_frame(self, amount):
        self.animation_frame = amount

    def change_frame(self, amount):
        self.animation_frame += amount
        if self.animation:
            if 'loop' in self.animation_tags:
                self.animation_frame %= len(self.animation)
            else:
                self.animation_frame = max(0, min(self.animation_frame, len(self.animation) - 1))

    def get_current_img(self):
        image = animation_database[self.animation[self.animation_frame]] if self.animation else self.image
        return flip(image, self.flip) if image is not None else None

    def display(self, surface, scroll):
        image = animation_database[self.animation[self.animation_frame]] if self.animation else self.image
        if image is None:
            return
        rendered = transformed(image, self.flip, self.rotation % 360)
        blit_center(surface, rendered,
                    (int(self.x) - scroll[0] + self.offset[0] + image.get_width() / 2,
                     int(self.y) - scroll[1] + self.offset[1] + image.get_height() / 2))


class PhysicsObject:
    def __init__(self, x, y, x_size, y_size):
        self.width, self.height = x_size, y_size
        self.rect = pygame.Rect(x, y, x_size, y_size)
        self.x, self.y = x, y
        self.hitbox = None

    def setup_hitbox(self, x_offset, y_offset, x_size, y_size):
        self.hitbox = [x_offset, y_offset, x_size, y_size]

    def get_hitbox(self):
        if self.hitbox is None:
            return self.rect.copy()
        x, y, width, height = self.hitbox
        return pygame.Rect(self.x + x, self.y + y, width, height)

    def move(self, movement, platforms, ramps):
        result = dict.fromkeys(('top', 'bottom', 'right', 'left', 'slant_bottom'), False)
        steps = max(1, math.ceil(max(abs(v) for v in movement) / min(self.width, self.height, 20)))
        dx, dy = movement[0] / steps, movement[1] / steps
        for _ in range(steps):
            previous_bottom = self.rect.bottom
            self.x += dx
            self.rect.x = int(self.x)
            hits = collision_test(self.rect, platforms)
            if hits and dx:
                if dx > 0:
                    self.rect.right = min(block.left for block in hits)
                    result['right'] = True
                else:
                    self.rect.left = max(block.right for block in hits)
                    result['left'] = True
                self.x = self.rect.x
                dx = 0
            self.y += dy
            self.rect.y = int(self.y)
            hits = collision_test(self.rect, platforms)
            if hits and dy:
                if dy > 0:
                    self.rect.bottom = min(block.top for block in hits)
                    result['bottom'] = True
                else:
                    self.rect.top = max(block.bottom for block in hits)
                    result['top'] = True
                self.y = self.rect.y
                dy = 0
            if movement[1] >= 0:
                if collision_test(self.rect.move(0, 1), platforms):
                    result['bottom'] = True
                    self.y = self.rect.y
                for x, y, direction in ramps:
                    if not self.rect.move(0, 1).colliderect(pygame.Rect(x, y, 20, 20)):
                        continue
                    foot = self.rect.right - x if direction == 1 else x + 20 - self.rect.left
                    height = y + 20 - max(0, min(20, foot))
                    if previous_bottom <= height + abs(movement[0] / steps) + 1 and self.rect.bottom >= height:
                        self.rect.bottom = height
                        self.y = self.rect.y
                        result['slant_bottom'] = True
        return result
