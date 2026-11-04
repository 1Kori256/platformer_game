"""Precomputed tile drawing data and local collision queries."""

import math
import pygame

TILE_SIZE = 20


class TileWorld:
    def __init__(self, tile_map, tilesets, attributes):
        self.cells = {}
        self.colliders = {}
        self.ramps = {}
        self.visible_key = None
        self.visible = []
        for cell in tile_map.values():
            x, y = cell['pos']
            for tile in cell['tiles']:
                name, index = tile['tileset'], tile['tile']
                properties = attributes.get(name, {}).get(index, {})
                try:
                    image = tilesets[name][index]
                except (KeyError, IndexError) as error:
                    raise ValueError(f'Unknown tile {name}:{index} at {x};{y}') from error
                order = (tile['depth'], y, x, name, index)
                position = (x * TILE_SIZE + properties.get('offset_x', 0),
                            y * TILE_SIZE + properties.get('offset_y', 0))
                self.cells.setdefault((x, y), []).append(
                    (order, image, position, 'invisible' in properties))
                if 'no_collide' not in properties:
                    ramp = properties.get('ramp', 0)
                    if ramp:
                        self.ramps.setdefault((x, y), []).append((x * TILE_SIZE, y * TILE_SIZE, ramp))
                    else:
                        self.colliders.setdefault((x, y), []).append(
                            pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    def render(self, surface, camera):
        # Keep the original visibility margins and depth ordering.
        start_x = int(camera[0] / TILE_SIZE) - 4
        start_y = int(camera[1] / TILE_SIZE) - 4
        columns = surface.get_width() // TILE_SIZE + 5
        rows = surface.get_height() // TILE_SIZE + 6
        key = (start_x, start_y, columns, rows)
        if key != self.visible_key:
            self.visible = sorted(
                (item for y in range(start_y, start_y + rows)
                 for x in range(start_x, start_x + columns)
                 for item in self.cells.get((x, y), ())), key=lambda item: item[0])
            self.visible_key = key
        for _, image, (x, y), invisible in self.visible:
            if not invisible:
                surface.blit(image, (x - camera[0], y - camera[1]))

    def collision_tiles(self, area):
        solids, ramps = [], []
        left, right = math.floor(area.left / TILE_SIZE), math.floor((area.right - 1) / TILE_SIZE)
        top, bottom = math.floor(area.top / TILE_SIZE), math.floor((area.bottom - 1) / TILE_SIZE)
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                solids.extend(self.colliders.get((x, y), ()))
                ramps.extend(self.ramps.get((x, y), ()))
        return solids, ramps
