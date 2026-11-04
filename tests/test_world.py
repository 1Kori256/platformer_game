import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import random
import unittest
import pygame
from data.tile_world import TileWorld


def cell(x, y, index=0, depth=0):
    return {'pos': [x, y], 'tiles': [{'depth': depth, 'tileset': 'test', 'tile': index}]}


class WorldTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((100, 100))
        red, green, blue = [pygame.Surface((20, 20)) for _ in range(3)]
        for image, color in zip((red, green, blue), ('red', 'green', 'blue')):
            image.fill(color)
        self.tiles = {'test': [red, green, blue]}

    def tearDown(self):
        pygame.quit()

    def test_cached_drawing_preserves_depth_offsets_and_invisibility(self):
        data = {'0;0': cell(0, 0), '1;0': cell(1, 0, 1, -1), '0;1': cell(0, 1, 2)}
        attrs = {'test': {1: {'offset_x': -10}, 2: {'invisible': 1, 'no_collide': 1}}}
        world = TileWorld(data, self.tiles, attrs)
        surface = pygame.Surface((60, 60))
        for camera in ((0, 0), (1, 1), (20, 0), (0, 0)):
            surface.fill('black')
            world.render(surface, camera)
            expected = (255, 0, 0) if camera[0] < 20 else (0, 255, 0)
            self.assertEqual(surface.get_at((max(0, 15 - camera[0]), 5))[:3], expected)
        surface.fill('black')
        world.render(surface, (0, 0))
        self.assertEqual(surface.get_at((5, 25))[:3], (0, 0, 0))

    def test_collision_queries_are_independent_of_camera(self):
        world = TileWorld({'0;0': cell(0, 0)}, self.tiles, {})
        world.render(pygame.Surface((60, 60)), (10000, 10000))
        solids, ramps = world.collision_tiles(pygame.Rect(0, 0, 12, 15))
        self.assertEqual(solids, [pygame.Rect(0, 0, 20, 20)])
        self.assertEqual(ramps, [])

    def test_grid_queries_include_all_overlapping_tiles(self):
        rng = random.Random(1)
        world = TileWorld({f'{x};{y}': cell(x, y) for x in range(-5, 6) for y in range(-5, 6)}, self.tiles, {})
        all_solids = [rect for rects in world.colliders.values() for rect in rects]
        for _ in range(100):
            area = pygame.Rect(rng.randint(-150, 150), rng.randint(-150, 150),
                               rng.randint(1, 100), rng.randint(1, 100))
            actual, _ = world.collision_tiles(area)
            expected = [rect for rect in all_solids if rect.colliderect(area)]
            self.assertEqual(sorted(tuple(rect) for rect in expected),
                             sorted(tuple(rect) for rect in actual if rect.colliderect(area)))

    def test_ramps_and_noncolliding_tiles(self):
        data = {'0;0': cell(0, 0), '1;0': cell(1, 0, 1), '2;0': cell(2, 0, 2)}
        world = TileWorld(data, self.tiles, {'test': {1: {'ramp': 1}, 2: {'no_collide': 1}}})
        solids, ramps = world.collision_tiles(pygame.Rect(0, 0, 60, 20))
        self.assertEqual(solids, [pygame.Rect(0, 0, 20, 20)])
        self.assertEqual(ramps, [(20, 0, 1)])
