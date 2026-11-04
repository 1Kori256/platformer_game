"""Measure tile rendering and local collision queries without display scaling or a frame cap."""

import argparse
import json
import os
from pathlib import Path
import statistics
import sys
import time

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from main import Game


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=int, default=1200)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.frames < 1:
        parser.error('--frames must be positive')
    game = Game()
    try:
        samples = []
        area = pygame.Rect(200, 220, 20, 25)
        for frame in range(args.frames + 30):
            camera = (100 + (frame // 2) % 300, 90)
            start = time.perf_counter()
            game.world.render(game.surface, camera)
            game.world.collision_tiles(area)
            if frame >= 30:
                samples.append((time.perf_counter() - start) * 1000)
        if args.preview:
            for _ in range(120):
                game.update()
            game.render(show_debug=False)
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(pygame.transform.scale(game.surface, game.screen.get_size()), str(args.preview))
        print(json.dumps({'frames': args.frames, 'world_median_ms': round(statistics.median(samples), 3)}, indent=2))
    finally:
        game.close()


if __name__ == '__main__':
    main()
