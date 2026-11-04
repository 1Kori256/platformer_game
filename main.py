"""MindTaker: the original platformer, running at a fixed 60 physics steps/second."""

import argparse
import json
from pathlib import Path
import pygame

from data import entities, global_functions as functions, world_data
from data.debug import debug
from data.tile_world import TileWorld

MAIN_PATH = Path(__file__).resolve().parent
GAME_SIZE = (480, 270)
FIXED_STEP = 1 / 60
animation_database = {}


class animation_obj:
    def __init__(self, x, y, animation_id, flip=False):
        self.id, self.timer, self.flip = animation_id, 0, flip
        if animation_id not in animation_database:
            path = MAIN_PATH / 'data' / 'images' / 'animations' / animation_id
            speed = int((path / 'speed.txt').read_text())
            frames = [functions.load_image(str(image)) for image in sorted(path.glob('*.png'))]
            if speed <= 0 or not frames:
                raise ValueError(f'Invalid animation: {animation_id}')
            animation_database[animation_id] = (speed, frames)
        image = self.get_image()
        self.x, self.y = x - image.get_width() // 2, y - image.get_height() // 2

    def get_image(self):
        speed, frames = animation_database[self.id]
        return frames[min(self.timer // speed, len(frames) - 1)]

    def change_frame(self, amount):
        self.timer += amount
        speed, frames = animation_database[self.id]
        return 'delete' if self.timer >= len(frames) * speed else None

    def render(self, surface, offset):
        image = entities.flip(self.get_image(), self.flip)
        surface.blit(image, (self.x - offset[0], self.y - offset[1]))


class Game:
    def __init__(self, level=None, size=(960, 540)):
        pygame.init()
        try:
            self.screen = pygame.display.set_mode(size)
            pygame.display.set_caption('MindTaker v: alpha-1.0')
            self.surface = pygame.Surface(GAME_SIZE).convert()
            pygame.display.set_icon(functions.load_image(str(MAIN_PATH / 'data/images/game_icon.png')))
            self.font = pygame.font.Font(str(MAIN_PATH / 'data/font/game_font.ttf'), 8)
            tiles_path = str(MAIN_PATH / 'data/images/tilesets') + '/'
            tilesets = world_data.load_tilesets(tiles_path)
            attributes = world_data.load_tileset_data(tiles_path)
            path = Path(level) if level else MAIN_PATH / 'data/save1.json'
            self.spawn, self.borders, finish = world_data.load_world_data(path)
            with path.open(encoding='utf-8') as source:
                self.world = TileWorld(json.load(source), tilesets, attributes)
            player_path = str(MAIN_PATH / 'data/images/player')
            self.idle = entities.animation_sequence([[0, 40], [1, 20]], player_path + '/idle/stand_')
            self.run_animation = entities.animation_sequence([[i, 4] for i in range(6)], player_path + '/run/run_')
            self.jump_image = functions.load_image(player_path + '/jump.png')
            self.spin_image = functions.load_image(player_path + '/spin.png')
            self.background = functions.load_image(str(MAIN_PATH / 'data/images/backgrounds/world_1.png'))
            self.player = entities.entity(0, 0, 12, 15)
            self.player.obj.setup_hitbox(4, 10, 7, 7)
            self.player.set_animation_tags(['loop'])
            self.finish = pygame.Rect(finish[0] * 20 + 1, finish[1] * 20 - 6, 20, 20)
            self.clock = pygame.time.Clock()
            self.held = set()
            self.running = True
            self.accumulator = 0
            self.mouse = (-100, -100)
            self.restart()
        except Exception:
            pygame.quit()
            raise

    def restart(self):
        self.player.set_pos(self.spawn[0] * 20 + 2, self.spawn[1] * 20 - 7)
        self.player.set_animation(self.idle)
        self.player.set_image(self.jump_image)
        self.player.rotation = 0
        self.player.flip = False
        self.momentum = [0, 0]
        self.jumps, self.air_time, self.spin_timer = 2, 0, 0
        self.dead = False
        self.effects = []
        self.camera = list(self.camera_target())

    def camera_target(self):
        left, bottom, right = self.borders
        x = max(left, min(self.player.x - GAME_SIZE[0] // 2 + 7, right - GAME_SIZE[0]))
        y = min(self.player.y - GAME_SIZE[1] // 2 + 14, bottom - GAME_SIZE[1])
        return x, y

    def jump(self):
        if self.dead or self.jumps <= 0:
            return
        self.effects.append(animation_obj(self.player.x + 8, self.player.y + 2, 'jump'))
        self.jumps -= 1
        self.momentum[1] = -6
        if self.jumps == 0:
            self.player.image = self.spin_image
            self.spin_timer = -15 if self.player.flip else 15

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and not getattr(event, 'repeat', False):
                if event.key in (pygame.K_F1, pygame.K_ESCAPE):
                    self.running = False
                elif event.key == pygame.K_r:
                    self.restart()
                elif event.key == pygame.K_SPACE:
                    self.jump()
                if event.key in (pygame.K_a, pygame.K_d, pygame.K_LEFT, pygame.K_RIGHT):
                    self.held.add(event.key)
                    left = event.key in (pygame.K_a, pygame.K_LEFT)
                    self.effects.append(animation_obj(self.player.x + 8, self.player.y + 2, 'turn', left))
            elif event.type == pygame.KEYUP:
                self.held.discard(event.key)
            elif event.type == pygame.WINDOWFOCUSLOST:
                self.held.clear()
            elif event.type == pygame.MOUSEMOTION:
                width, height = self.screen.get_size()
                self.mouse = (int(event.pos[0] * GAME_SIZE[0] / width),
                              int(event.pos[1] * GAME_SIZE[1] / height))

    def update(self):
        if not self.dead:
            target = self.camera_target()
            for axis in (0, 1):
                self.camera[axis] += (target[axis] - self.camera[axis]) / 13
        movement = self.momentum.copy()
        if not self.dead:
            value = self.momentum[0]
            self.momentum[0] = max(0, value - 0.25) if value > 0 else min(0, value + 0.25)
            if abs(self.momentum[0]) < 4:
                right = bool(self.held & {pygame.K_d, pygame.K_RIGHT})
                left = bool(self.held & {pygame.K_a, pygame.K_LEFT})
                movement[0] += 4 * (right - left)
        self.momentum[1] = min(self.momentum[1] + 0.45, 7)
        area = self.player.obj.rect.union(self.player.obj.rect.move(int(movement[0]), int(movement[1]))).inflate(2, 2)
        solids, ramps = self.world.collision_tiles(area) if not self.dead else ([], [])
        collisions = self.player.move(movement, solids, ramps)
        if collisions['bottom'] or collisions['slant_bottom']:
            self.jumps, self.air_time = 2, 0
            self.momentum[1] = 0
            self.player.rotation = 0
        else:
            self.air_time += 1
        if collisions['top'] and self.momentum[1] < 0:
            self.momentum[1] = 0
        self.player.animation = self.run_animation if movement[0] else self.idle
        if self.air_time > 6:
            self.player.animation = None
        if movement[0]:
            self.player.flip = movement[0] < 0
        if self.spin_timer:
            turn = 1 if self.spin_timer > 0 else -1
            self.spin_timer -= turn
            self.player.rotation -= 24 * turn
        else:
            self.player.image = self.jump_image
        self.player.change_frame(1)
        if self.dead:
            self.player.rotation -= 24
        if self.player.y > self.borders[1]:
            if not self.dead:
                self.dead = True
                self.momentum = [3, -8]
            elif self.player.y > self.borders[1] + GAME_SIZE[1]:
                self.restart()
                return
        x = max(self.borders[0], min(self.player.x, self.borders[2] - 15))
        if x != self.player.x:
            self.player.set_pos(x, self.player.y)
        if not self.dead and self.player.obj.rect.colliderect(self.finish):
            self.restart()
            return
        self.effects = [effect for effect in self.effects if effect.change_frame(1) is None]

    def render(self, show_debug=True):
        self.surface.fill((0, 230, 255))
        camera = [int(value) for value in self.camera]
        background_x = -((self.camera[0] / 8) % 400)
        background_y = (-self.camera[1] + self.borders[1] - 190) / 8
        for x in (background_x, background_x + 400):
            self.surface.blit(self.background, (x, background_y))
        self.world.render(self.surface, camera)
        self.player.display(self.surface, camera)
        for effect in self.effects:
            effect.render(self.surface, camera)
        if show_debug:
            debug(self.surface, self.font, self.mouse, round(self.clock.get_fps(), 2))

    def frame(self, elapsed):
        self.events()
        if not self.running:
            return False
        self.accumulator += min(max(elapsed, 0), 0.25)
        while self.accumulator + 1e-12 >= FIXED_STEP:
            self.update()
            self.accumulator -= FIXED_STEP
        self.render()
        pygame.transform.scale(self.surface, self.screen.get_size(), self.screen)
        pygame.display.flip()
        return True

    def run(self):
        while self.frame(self.clock.tick(60) / 1000):
            pass

    def close(self):
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--level', type=Path, help='JSON map from the level editor')
    args = parser.parse_args()
    game = None
    try:
        game = Game(level=args.level)
        game.run()
    except (OSError, ValueError, pygame.error) as error:
        parser.exit(1, f'Cannot start game: {error}\n')
    finally:
        if game is not None:
            game.close()


if __name__ == '__main__':
    main()
