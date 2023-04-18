import pygame
from pygame.locals import *

animation_database = {}

def collision_test(Object1, ObjectList):
    
    collision_list = []
    for Object in ObjectList:
        if Object.colliderect(Object1):
            collision_list.append(Object)

    return collision_list


def flip(img, boolean=True):

    return pygame.transform.flip(img, boolean, False)


def blit_center(surface, surface2, pos):

    x = surface2.get_width() // 2
    y = surface2.get_height() // 2
    surface.blit(surface2, (pos[0] - x, pos[1] - y))


def animation_sequence(sequence, base_path, colorkey=(255, 255, 255), transparency=255):
    global animation_database
    
    result = []
    
    for frame in sequence:
    
        image_id = base_path + str(frame[0])
        image = pygame.image.load(image_id + ".png").convert()
        image.set_colorkey(colorkey)
        image.set_alpha(transparency)
        animation_database[image_id] = image.copy()
    
        for i in range(frame[1]):
            result.append(image_id)
    
    return result


def get_frame(id):

    global animation_database
    return animation_database[id]


class entity(object): 

    global animation_database

    def __init__(self, x, y, size_x, size_y):
        self.x = x
        self.y = y
        self.size_x = size_x
        self.size_y = size_y
        self.obj = PhysicsObject(x, y, size_x, size_y)
        self.animation = None
        self.image = None
        self.animation_frame = 0
        self.animation_tags = []
        self.flip = False
        self.offset = [0,0]
        self.rotation = 0

    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.obj.x = x
        self.obj.y = y
        self.obj.rect.x = x
        self.obj.rect.y = y    

    def move(self, momentum, platforms, ramps):
        collisions = self.obj.move(momentum, platforms, ramps)
        self.x = self.obj.x
        self.y = self.obj.y
        return collisions

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
        if self.animation != None:
            while self.animation_frame < 0:
                if "loop" in self.animation_tags:
                    self.animation_frame += len(self.animation)
                else:
                    self.animation = 0
            while self.animation_frame >= len(self.animation):
                if "loop" in self.animation_tags:
                    self.animation_frame -= len(self.animation)
                else:
                    self.animation_frame = len(self.animation) - 1

    def get_current_img(self):
        if self.animation == None:
            if self.image != None:
                return flip(self.image, self.flip)
            else:
                return None
        else:
            return flip(animation_database[self.animation[self.animation_frame]], self.flip)            

    def display(self, surface, scroll):
        if self.animation == None:
            if self.image != None:
                image_to_render = flip(self.image, self.flip).copy()
        else:
            image_to_render = flip(animation_database[self.animation[self.animation_frame]], self.flip).copy()
        center_x = image_to_render.get_width() / 2
        center_y = image_to_render.get_height() / 2
        image_to_render = pygame.transform.rotate(image_to_render, self.rotation)
        blit_center(surface, image_to_render, 
            (int(self.x) - scroll[0] + self.offset[0] + center_x,
             int(self.y) - scroll[1] + self.offset[1] + center_y))

class PhysicsObject(object):

    def __init__(self, x, y, x_size, y_size):
        self.width = x_size
        self.height = y_size
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.x = x
        self.y = y
        self.hitbox = None
    
    def setup_hitbox(self, x_offset, y_offset, x_size, y_size):
        self.hitbox = [x_offset, y_offset, x_size, y_size]

    def get_hitbox(self):
        return pygame.Rect(self.x + self.hitbox[0], self.y + self.hitbox[1], self.hitbox[2], self.hitbox[3])

    def move(self, movement, platforms, ramps):

        tile_size = 20

        self.x += movement[0]
        self.rect.x = int(self.x)
        block_hit_list = collision_test(self.rect, platforms)

        collision_types = {"top": False,
                           "bottom": False,
                           "right": False,
                           "left": False,
                           "slant_bottom": False}

        for block in block_hit_list:

            if movement[0] > 0:
                self.rect.right = block.left
                collision_types['right'] = True

            elif movement[0] < 0:
                self.rect.left = block.right
                collision_types['left'] = True

            self.x = self.rect.x

        self.y += movement[1]
        self.rect.y = int(self.y)
        block_hit_list = collision_test(self.rect, platforms)

        for block in block_hit_list:

            if movement[1] > 0:
                self.rect.bottom = block.top
                collision_types['bottom'] = True

            elif movement[1] < 0:
                self.rect.top = block.bottom
                collision_types['top'] = True

            self.change_y = 0
            self.y = self.rect.y

        for ramp in ramps:

            ramp_rectangle = pygame.Rect(ramp[0], ramp[1], tile_size, tile_size)

            if self.rect.colliderect(ramp_rectangle):

                if ramp[2] == 1:
                    if self.rect.right - ramp[0] + self.rect.bottom - ramp[1] > tile_size:
                        self.rect.bottom = ramp[1] + tile_size - (self.rect.right - ramp[0])
                        self.y = self.rect.y
                        collision_types['slant_bottom'] = True

                if ramp[2] == 2:
                    if ramp[0] + tile_size - self.rect.left + self.rect.bottom - ramp[1] > tile_size:
                        self.rect.bottom = ramp[1] + tile_size - (ramp[0] + tile_size - self.rect.left)
                        self.y = self.rect.y
                        collision_types['slant_bottom'] = True

        return collision_types