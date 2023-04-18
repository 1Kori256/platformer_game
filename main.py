"""
This file contains main game loop!
This is the script supposed to be run to play the game. 
Made by Samuel Koribanič!
"""


# ALL IMPORTS ----------------------------------------------------------------------------------------------
import pygame 
import sys 
import os
import json

import data.global_functions as functions
import data.world_data as world_data
import data.entities as entities
from data.debug import debug


def render_tiles(surface, tile_map, tilesets, tileset_dat, camera_offset):
    
    """
    Render all tiles that are within screen borders.
    """

    tile_size = 20

    to_render = []
    render_box = [int(surface.get_width() / tile_size) + 5, int(surface.get_height() / tile_size) + 6]

    for y in range(render_box[1]):
            y += int(camera_offset[1] / tile_size) - 4

            for x in range(render_box[0]):
                x += int(camera_offset[0] / tile_size) - 4

                pos = f"{x};{y}"

                if pos in tile_map:
                    for tile in tile_map[pos]["tiles"]:
                        to_render.append([tile["depth"], tile_map[pos]["pos"][1], tile_map[pos]["pos"][0], tile["tileset"], tile["tile"]])

    to_render.sort()

    for image in to_render:
        
        offset = [0,0]
        try:
            tile_attributes = tileset_dat[image[3]][image[4]]

        except KeyError:
            tile_attributes = []

        if 'offset_x' in tile_attributes:
            offset[0] = tile_attributes['offset_x']
        if 'offset_y' in tile_attributes:
            offset[1] = tile_attributes['offset_y']
        if 'invisible' not in tile_attributes:

            surface.blit(tilesets[image[3]][image[4]], (image[2] * tile_size - camera_offset[0] + offset[0], image[1] * tile_size - camera_offset[1] + offset[1]))

    return to_render


def list_to_ints(list_):

    """
    Makes all strings in list integers.
    """

    new_list = list_.copy()
    for i in range(len(new_list)):
        new_list[i] = int(new_list[i])
    return new_list


def normalize(num, amount):

    """
    Normalizes value to certain fixed amount.
    """


    if num > amount:
        num -= amount
    elif num < -amount:
        num += amount
    else:
        num = 0
    return num

animation_database = {}
class animation_obj(object):

    def __init__(self, x, y, animation_id, flip=False):
        self.id = animation_id
        self.timer = 0
        img = self.get_image()
        self.x = x - int(img.get_width() / 2)
        self.y = y - int(img.get_height() / 2)
        self.flip = flip

    def get_image(self):
        global animation_database

        """
        Returns current image in animation.
        """

        if self.id not in animation_database:

            path = f"data/images/animations/{self.id}/"
            image_list = os.listdir(path)
            image_list.sort()

            file = open(f"{path}speed.txt")
            speed = int(file.read())
            file.close()
            
            animation_database[self.id] = [speed, []]
            for image in image_list:
                if image[-4:] == '.png':
                    animation_database[self.id][1].append(functions.load_image(path + image))

        animation_data = animation_database[self.id]
        frame_num = int(self.timer / animation_data[0])

        try:
            return animation_data[1][frame_num]
        except IndexError:
            return animation_data[1][0]

    def change_frame(self, amount):

        """
        Changes frame based on time elapsed.
        """

        self.timer += amount

        if self.timer >= len(animation_database[self.id][1]) * animation_database[self.id][0]:
            return "delete"
        else:
            return None

    def render(self, surface,offset):

        """
        Renders properly fliped image on position. 
        """

        if self.flip == False:
            surface.blit(self.get_image(), (self.x - offset[0], self.y - offset[1]))
        else:
            surface.blit(pygame.transform.flip(self.get_image(), True, False), (self.x - offset[0], self.y - offset[1]))


# Main Loop ------------------------------------------------------------------------------------------------
def main(surface):

    mouse_pos = (-100, -100)

    tilesets = world_data.load_tilesets(f"{MAIN_PATH}/data/images/tilesets/")
    tileset_data = world_data.load_tileset_data(f"{MAIN_PATH}/data/images/tilesets/")

    world_save = "save1"

    spawn, borders, finish = world_data.load_world_data(f"{MAIN_PATH}/data/{world_save}.json")

    with open(f"{MAIN_PATH}/data/{world_save}.json") as file:
        tile_map = json.load(file)

    main_hero = "player"

    player_idle_anim = entities.animation_sequence([[0, 40], [1, 20]], f"{MAIN_PATH}/data/images/{main_hero}/idle/stand_")
    player_run_anim = entities.animation_sequence([[0, 4], [1, 4], [2, 4], [3, 4], [4, 4], [5, 4]], f"{MAIN_PATH}/data/images/{main_hero}/run/run_")

    player_jump_img = functions.load_image(f"{MAIN_PATH}/data/images/{main_hero}/jump.png")
    player_spin_img = functions.load_image(f"{MAIN_PATH}/data/images/{main_hero}/spin.png")

    player = entities.entity(spawn[0] * 20 + 2, spawn[1] * 20 - 7, 12, 15)
    player.obj.setup_hitbox(4, 10, 7, 7)

    player.set_animation(player_idle_anim)
    player.set_animation_tags(['loop'])
    player.set_image(player_jump_img)
    player.set_image(player_jump_img)
    player_movement = [0, 0]
    player_momentum = [0, 0]

    finish_entity = entities.entity(finish[0] * 20 + 1, finish[1] * 20 - 6, 20, 20)

    speed = 4
    jumps = 2
    air_time = 0
    spin_timer = 0

    sky_colors = {"1": (0, 230, 255)}
    background_image = functions.load_image(f"{MAIN_PATH}/data/images/backgrounds/world_1.png")

    world = "1"

    camera_offset = [0, 0]

    dead = False
    paused = False

    right, left = False, False

    tile_rects = None

    animation_objs = []

    run = True
    while run:

        # Transform mouse position according real res / visual res -----------------------------------------
        mouse_pos = pygame.mouse.get_pos()
        mouse_pos = (int(mouse_pos[0] * (GAME_WIDTH / SCREEN_WIDTH)),
                     int(mouse_pos[1] * (GAME_HEIGHT / SCREEN_HEIGHT)))

        # Binds --------------------------------------------------------------------------------------------
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                run = False
                pygame.display.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    run = False
                    pygame.display.quit()
                    sys.exit()

                if event.key == pygame.K_d:
                    animation_objs.append(animation_obj(player.x + 8, player.y + 2, 'turn'))
                    right = True

                if event.key == pygame.K_a:
                    animation_objs.append(animation_obj(player.x + 8, player.y + 2, 'turn', True))
                    left = True

                if event.key == pygame.K_SPACE:
                    if dead == False:
                        if jumps > 0:
                            animation_objs.append(animation_obj(player.x + 8, player.y + 2, 'jump'))
                            jumps -= 1
                            player_momentum[1] = -6
                            if jumps == 0:
                                player.image = player_spin_img
                                if player.flip == True:
                                    spin_timer = -15
                                else:
                                    spin_timer = 15
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_d:
                    right = False
                if event.key == pygame.K_a:
                    left = False


            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()


        # Creating background
        surface.fill(sky_colors[world])

        background_x = -1 * ((camera_offset[0] / 8) % 400)

        surface.blit(background_image, (background_x, (-camera_offset[1] + borders[1] - 190) / 8))
        surface.blit(background_image, (background_x + 400, (-camera_offset[1] + borders[1] - 190) / 8))


        # Move camera based on player position
        target_x = player.x - int(surface.get_width() / 2) + 7
        target_y = player.y - int(surface.get_height() / 2) + 14

        if target_x < borders[0]: # handle left border
            target_x = borders[0]

        if target_x + surface.get_width() > borders[2]: # handle right border
            target_x = borders[2] - surface.get_width()

        if target_y + surface.get_height() > borders[1]: # handle bottom border
            target_y = borders[1] - surface.get_height()

        if tile_rects == None:
            camera_offset[0] = target_x
            camera_offset[1] = target_y

        if dead == False:
            camera_offset[0] += (target_x - camera_offset[0]) / 13
            camera_offset[1] += (target_y - camera_offset[1]) / 13


        # Render tiles
        rendered = render_tiles(surface, tile_map, tilesets, tileset_data, list_to_ints(camera_offset))
        tile_rects = []


        # Get colliding tiles
        player_speed_multiplier = 1
        ramps = []
        for tile in rendered:
            collisions = True
            ramp = 0
            try:
                tile_attributes = tileset_data[tile[3]][tile[4]]
                if 'no_collide' in tile_attributes:
                    collisions = False
                if 'ramp' in tile_attributes:
                    ramp = tile_attributes['ramp']
            except KeyError:
                pass
            if collisions == True:
                if ramp == 0:
                    tile_rects.append(pygame.Rect(tile[2] * 20, tile[1] * 20, 20, 20))
                else:
                    ramps.append([tile[2] * 20, tile[1] * 20, ramp])
    

        # Update player position
        player_movement = [0,0]
        player_movement[0] += player_momentum[0] * player_speed_multiplier
        player_movement[1] += player_momentum[1] * player_speed_multiplier

        if dead == False:
            player_momentum[0] = normalize(player_momentum[0], 0.25)

        if dead == False:
            if abs(player_momentum[0]) < 4:
                if right == True:
                    player_movement[0] += speed * player_speed_multiplier
                if left == True:
                    player_movement[0] -= speed * player_speed_multiplier

        player_momentum[1] += 0.45
        if player_momentum[1] > 7:
            player_momentum[1] = 7


        # Handle collisions
        if tile_rects != None:
            if paused == False:

                if dead == False:
                    player_collisions = player.move(player_movement, tile_rects, ramps)
                else:
                    player_collisions = player.move(player_movement, [], [])

                if player_collisions['bottom'] == True:
                    jumps = 2
                    player_momentum[1] = 0
                    air_time = 0
                    player.rotation = 0

                elif player_collisions['slant_bottom'] == True:
                    jumps = 2
                    air_time = 0
                    player.rotation = 0

                else:
                    air_time += 1


        # Handle current player image
        if player_movement[0] != 0:
            player.animation = player_run_anim
        else:
            player.animation = player_idle_anim
        
        if air_time > 6:
            player.animation = None
        
        if player_movement[0] < 0:
            player.flip = True
        elif player_movement[0] > 0:
            player.flip = False
    
        if spin_timer > 0:
            spin_timer -= 1
            player.rotation -= 24

        elif spin_timer < 0:
            spin_timer += 1
            player.rotation += 24
        else:
            player.image = player_jump_img

        player.change_frame(1)

        if dead == True:
            player.rotation -= 24
        

        # Handle border collision
        if player.y > borders[1]:
            if dead == False:
                dead = True
                player_momentum = [3, -8]

        if player.x < borders[0]:
            player.x = borders[0]
            player.obj.rect.x = borders[0]
            player.obj.x = borders[0]

        if player.x + 15 > borders[2]:
            player.x = borders[2] - 15
            player.obj.rect.x = borders[2] - 15
            player.obj.x = borders[2] - 15


        # Blit entities 
        player.display(surface, list_to_ints(camera_offset))

        if player.obj.rect.colliderect(finish_entity.obj.rect):
            player.set_pos(spawn[0] * 20 + 2, spawn[1] * 20 - 7)
            player_momentum = [0, 0]

        for obj in animation_objs:
            obj.render(surface, list_to_ints(camera_offset))
            if obj.change_frame(1) != None:
                animation_objs.remove(obj)


        debug(surface, FONT, mouse_pos, round(MAIN_CLOCK.get_fps(), 2))

        # Update -------------------------------------------------------------------------------------------
        SCREEN.blit(pygame.transform.scale(surface, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
        pygame.display.update()
        elapsed_time = MAIN_CLOCK.tick(60) / 1000
 

# GLOBAL ---------------------------------------------------------------------------------------------------
if __name__ == "__main__":


    # Setup pygame/window ----------------------------------------------------------------------------------
    GAME_NAME = "MindTaker"
    VERSION = "alpha-1.0"
    MAIN_PATH = os.path.dirname(os.path.abspath(__file__))

    pygame.init()
    pygame.font.init()

    MAIN_CLOCK = pygame.time.Clock()

    SCREEN_WIDTH = 1920 // 2
    SCREEN_HEIGHT = 1080 // 2
    GAME_WIDTH = 480
    GAME_HEIGHT = 270

    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    GAME_WINDOW = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption(f"{GAME_NAME} v: {VERSION}")
    pygame.display.set_icon(functions.load_image(f"{MAIN_PATH}/data/images/game_icon.png"))

    FONT = pygame.font.Font(f"{MAIN_PATH}/data/font/game_font.ttf", 8)


    # Run Game ---------------------------------------------------------------------------------------------
    main(GAME_WINDOW)

    # Close ------------------------------------------------------------------------------------------------
    pygame.quit()
    sys.exit()