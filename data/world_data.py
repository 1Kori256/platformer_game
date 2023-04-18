# ALL IMPORTS ----------------------------------------------------------------------------------------------
import pygame 
from pygame.locals import *
import os
import json

try:
    import global_functions as functions
except ImportError:
    import data.global_functions as functions

def load_tileset(path):

    """
    Function that gets tiles from one tileset image, 
    based on corner pixel colors
    top left is purple while top right and bottom left are cyan
    """


    tileset_image = functions.load_image(path)
    tileset = []
    
    for y in range(tileset_image.get_height()):
        for x in range(tileset_image.get_width()):
            
            color = tileset_image.get_at((x, y))
            if color == (255, 0, 255, 255):
                tile_pos = [x + 1, y + 1, None, None]

                current_x = x
                while tile_pos[2] == None:
                    color_end = tileset_image.get_at((current_x, y))
                    if color_end == (0, 255, 255, 255):
                        tile_pos[2] = current_x - tile_pos[0]
                    current_x += 1

                current_y = y
                while tile_pos[3] == None:
                    color_end = tileset_image.get_at((x, current_y))
                    if color_end == (0, 255, 255, 255):
                        tile_pos[3] = current_y - tile_pos[1]
                    current_y += 1
                
                tileset.append(functions.clip(
                    tileset_image, tile_pos[0], tile_pos[1], tile_pos[2], tile_pos[3]
                ))

    return tileset


def load_tilesets(path):

    """
    Load all tilesets from certain folder.
    """


    tilesets = {}
    tileset_images = os.listdir(path)

    for image_path in tileset_images: 

        if image_path[-4:] == ".png": # List through all tileset images ------------------------------------
            
            image_id = image_path[:-4]

            if image_path[:8] == "tileset_":
                tilesets[image_id] = load_tileset(path + image_path)

                if image_id == 'tileset_muck':
                    for image in tilesets[image_id]:
                        image.set_alpha(190)

            else:
                image = pygame.image.load(path + image_path)
                image.set_colorkey((255,255,255))
                tilesets[image_id] = [image.copy()]

    return tilesets


def load_tileset_data(path):

    """
    Load specific attributes about each tileset.
    """


    tileset_data = {}

    f = open(path + "tileset_data.txt","r")
    data = f.read()
    f.close()
    lines = data.split('\n')

    for line in lines:

        if line != "":

            sections = line.split("=")
            name_data = sections[0].split(":")
            changes = sections[1].split(";")
            
            change_list = {}
            for change in changes:
                change_data = change.split(":")
                if change != "":
                    change_list[change_data[0]] = int(change_data[1])
            
            if name_data[0] not in tileset_data:
                tileset_data[name_data[0]] = {}

            tileset_data[name_data[0]][int(name_data[1])] = change_list


    return tileset_data


def load_world_data(path, tile_size = 20):

    """
    Transform saved text document to tile map. Tile map is then rendered on screen. 
    """

    with open(f"{path}") as file:
        tile_map = json.load(file)

    spawn = [0, 0]
    finish = [0, 0]
    borders = [9999, -9999, -9999]

    for pos, tile_list in tile_map.items():
        if pos != "":
            x = tile_list["pos"][0]
            y = tile_list["pos"][1]
            for tile_data in tile_list["tiles"]:
                if tile_data["tileset"] == "spawn":
                    spawn = [x, y]
                if tile_data["tileset"] == "finish":
                    finish = [x, y]
                if x < borders[0]:
                    borders[0] = x
                if x > borders[2]:
                    borders[2] = x
                if y > borders[1]:
                    borders[1] = y

    n = 0
    for border in borders:
        borders[n] *= tile_size
        if n != 0:
            borders[n] += tile_size
        n += 1

    return spawn, borders, finish