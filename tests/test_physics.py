import unittest
import pygame
from data.entities import PhysicsObject, entity


class PhysicsTests(unittest.TestCase):
    def test_lands_and_stays_on_floor(self):
        body = PhysicsObject(5, 0, 12, 15)
        floor = [pygame.Rect(0, 20, 40, 20)]
        self.assertTrue(body.move((0, 7), floor, [])['bottom'])
        self.assertEqual(body.rect.bottom, 20)
        self.assertTrue(body.move((0, 0), floor, [])['bottom'])
        self.assertEqual(body.y, 5)

    def test_ceiling_hit(self):
        body = PhysicsObject(5, 25, 12, 15)
        result = body.move((0, -7), [pygame.Rect(0, 0, 20, 20)], [])
        self.assertTrue(result['top'])
        self.assertEqual(body.rect.top, 20)

    def test_fast_wall_hit_cannot_tunnel(self):
        body = PhysicsObject(0, 0, 12, 15)
        result = body.move((100, 0), [pygame.Rect(40, 0, 20, 20)], [])
        self.assertTrue(result['right'])
        self.assertEqual(body.rect.right, 40)

    def test_left_wall_and_nearest_obstacle(self):
        body = PhysicsObject(100, 0, 12, 15)
        result = body.move((-100, 0), [pygame.Rect(0, 0, 20, 20), pygame.Rect(40, 0, 20, 20)], [])
        self.assertTrue(result['left'])
        self.assertEqual(body.rect.left, 60)

    def test_fractional_movement_is_preserved(self):
        body = PhysicsObject(0, 0, 12, 15)
        for _ in range(4):
            body.move((0.25, 0.25), [], [])
        self.assertEqual((body.x, body.y), (1, 1))
        self.assertEqual(body.rect.topleft, (1, 1))

    def test_both_ramp_directions(self):
        for direction, x, expected in ((1, 20, 28), (2, 28, 28)):
            with self.subTest(direction=direction):
                body = PhysicsObject(x, 8, 12, 15)
                result = body.move((0, 7), [], [(20, 20, direction)])
                self.assertTrue(result['slant_bottom'])
                self.assertEqual(body.rect.bottom, expected)

    def test_jump_from_below_ramp_does_not_snap_up(self):
        body = PhysicsObject(20, 30, 12, 15)
        result = body.move((0, -6), [], [(20, 20, 1)])
        self.assertFalse(result['slant_bottom'])
        self.assertEqual(body.y, 24)

    def test_falling_from_below_ramp_does_not_snap_up(self):
        body = PhysicsObject(20, 25, 12, 15)
        result = body.move((0, 1), [], [(20, 20, 1)])
        self.assertFalse(result['slant_bottom'])
        self.assertEqual(body.y, 26)

    def test_ramp_surface_never_exceeds_tile_bounds(self):
        body = PhysicsObject(32, 0, 12, 15)
        result = body.move((0, 7), [], [(20, 20, 1)])
        self.assertTrue(result['slant_bottom'])
        self.assertEqual(body.rect.bottom, 20)

    def test_teleport_syncs_entity_and_physics(self):
        player = entity(0, 0, 12, 15)
        player.set_pos(100, -40)
        player.move((0, 0), [], [])
        self.assertEqual((player.x, player.y), (100, -40))
        self.assertEqual(player.obj.rect.topleft, (100, -40))
