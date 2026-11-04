import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import pygame
from main import Game, MAIN_PATH, animation_obj


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        pygame.event.clear()

    def tearDown(self):
        self.game.close()

    def test_double_jump_and_third_press(self):
        self.game.jump()
        self.assertEqual(self.game.jumps, 1)
        self.game.jump()
        self.assertEqual(self.game.jumps, 0)
        self.assertEqual(self.game.momentum[1], -6)
        self.assertEqual(abs(self.game.spin_timer), 15)
        self.game.momentum[1] = -2
        self.game.jump()
        self.assertEqual(self.game.momentum[1], -2)

    def test_landing_restores_double_jump(self):
        for _ in range(60):
            self.game.update()
        self.game.jump()
        self.game.jump()
        for _ in range(120):
            self.game.update()
        self.assertEqual(self.game.jumps, 2)
        self.assertEqual(self.game.momentum[1], 0)

    def test_ceiling_clears_upward_momentum(self):
        self.game.world = SimpleNamespace(collision_tiles=lambda area: ([pygame.Rect(200, 200, 20, 20)], []))
        self.game.player.set_pos(202, 222)
        self.game.momentum[1] = -6
        self.game.update()
        self.assertEqual(self.game.momentum[1], 0)
        self.assertEqual(self.game.player.y, 220)

    def test_death_automatically_respawns(self):
        self.game.player.set_pos(self.game.player.x, self.game.borders[1] + 1)
        self.game.update()
        self.assertTrue(self.game.dead)
        for _ in range(180):
            self.game.update()
        self.assertFalse(self.game.dead)
        self.assertEqual(self.game.jumps, 2)
        self.assertLess(self.game.player.y, self.game.borders[1])

    def test_restart_resets_momentum_spin_and_effects(self):
        self.game.jump()
        self.game.jump()
        self.game.dead = True
        self.game.player.rotation = 123
        self.game.momentum = [5, 7]
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        self.game.events()
        self.assertFalse(self.game.dead)
        self.assertEqual(self.game.momentum, [0, 0])
        self.assertEqual((self.game.jumps, self.game.spin_timer, self.game.player.rotation), (2, 0, 0))
        self.assertEqual(self.game.effects, [])
        self.assertEqual(self.game.player.obj.rect.topleft,
                         (self.game.spawn[0] * 20 + 2, self.game.spawn[1] * 20 - 7))

    def test_finish_resets_double_jump_and_spin(self):
        self.game.player.set_pos(self.game.finish.x, self.game.finish.y)
        self.game.jumps, self.game.spin_timer = 0, 5
        self.game.update()
        self.assertEqual((self.game.jumps, self.game.spin_timer), (2, 0))
        self.assertEqual(self.game.player.x, self.game.spawn[0] * 20 + 2)

    def test_arrow_controls_and_focus_release(self):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        self.game.events()
        x = self.game.player.x
        self.game.update()
        self.assertEqual(self.game.player.x - x, 4)
        pygame.event.post(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.game.events()
        self.assertEqual(self.game.held, set())

    def test_expired_effects_removed_together(self):
        self.game.effects = [animation_obj(0, 0, 'turn') for _ in range(3)]
        for effect in self.game.effects:
            effect.timer = 10000
        self.game.update()
        self.assertEqual(self.game.effects, [])

    def test_render_rate_does_not_change_physics(self):
        for _ in range(60):
            self.game.frame(1 / 60)
        expected = (self.game.player.x, self.game.player.y, self.game.momentum.copy(), self.game.jumps)
        self.game.restart()
        self.game.accumulator = 0
        for _ in range(30):
            self.game.frame(1 / 30)
        self.assertEqual((self.game.player.x, self.game.player.y, self.game.momentum, self.game.jumps), expected)

    def test_quit_returns_without_rendering(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        with patch.object(self.game, 'render') as render:
            self.assertFalse(self.game.frame(1 / 60))
            render.assert_not_called()

    def test_assets_work_from_another_directory_and_other_map(self):
        previous = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                game = Game(level=MAIN_PATH / 'data/test1.json')
                game.jump()
                game.frame(1 / 60)
                self.assertEqual(game.spawn, [6, -1])
                game.close()
        finally:
            os.chdir(previous)
