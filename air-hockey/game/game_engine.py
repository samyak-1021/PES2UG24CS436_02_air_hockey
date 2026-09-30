"""
GameEngine: owns the puck, both paddles, and the computer AI, and runs
one frame's worth of game logic.

Starter version: the puck bounces around and paddles can hit it, but
there is no scoring, no match timer, and the reset that happens after
a goal is incomplete. That's what Tasks 2-4 fix/add.
"""

import math
import random

import pygame

from game.puck import Puck
from game.paddle import Paddle
from game.ai import ComputerAI
from game.collisions import handle_paddle_collision
from game.renderer import WIDTH, HEIGHT, MARGIN, GOAL_TOP, GOAL_BOTTOM

PLAYER_SPEED = 6
PUCK_RADIUS = 12
PADDLE_RADIUS = 28
INITIAL_PUCK_SPEED = 4.5
MATCH_DURATION = 30  # seconds


class GameEngine:
    def __init__(self):
        self.puck = Puck(WIDTH / 2, HEIGHT / 2, PUCK_RADIUS)
        self._launch_puck()

        self.player = Paddle(
            x=WIDTH * 0.15, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=MARGIN + PADDLE_RADIUS, max_x=WIDTH / 2 - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.computer = Paddle(
            x=WIDTH * 0.85, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=WIDTH / 2 + PADDLE_RADIUS, max_x=WIDTH - MARGIN - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.ai = ComputerAI()

        # Match scoring: a point goes to whoever's opponent goal the puck enters.
        self.player_score = 0
        self.computer_score = 0

        # 30-second match timer.
        self.game_over = False
        self.winner = None
        self.match_start_ms = pygame.time.get_ticks()

    def reset(self):
        """Restart the whole match: scores, puck, paddles and timer."""
        self.__init__()

    def time_left(self):
        """Seconds remaining in the match (never below 0)."""
        elapsed = (pygame.time.get_ticks() - self.match_start_ms) / 1000.0
        return max(0.0, MATCH_DURATION - elapsed)

    def _launch_puck(self):
        angle_choices = [0.3, 0.6, -0.3, -0.6]
        direction = random.choice([-1, 1])
        vy_factor = random.choice(angle_choices)
        self.puck.vx = INITIAL_PUCK_SPEED * direction
        self.puck.vy = INITIAL_PUCK_SPEED * vy_factor

    def handle_input(self, keys_pressed):
        # R restarts the whole match at any time.
        if keys_pressed[pygame.K_r]:
            self.reset()
            return

        dx = dy = 0
        if keys_pressed[pygame.K_UP]:
            dy -= PLAYER_SPEED
        if keys_pressed[pygame.K_DOWN]:
            dy += PLAYER_SPEED
        if keys_pressed[pygame.K_LEFT]:
            dx -= PLAYER_SPEED
        if keys_pressed[pygame.K_RIGHT]:
            dx += PLAYER_SPEED
        self.player.move_by(dx, dy)

    def update(self):
        if self.game_over:
            return

        # When time runs out, freeze the puck and lock in the result.
        if self.time_left() <= 0:
            self.game_over = True
            self.winner = self.get_winner()
            self.puck.vx = 0
            self.puck.vy = 0
            return

        self.ai.update(self.computer, self.puck)

        self.puck.move()
        self.puck.bounce_off_walls(HEIGHT, MARGIN)

        handle_paddle_collision(self.puck, self.player)
        handle_paddle_collision(self.puck, self.computer)

        self._handle_goals()

    def _handle_goals(self):
        if self.puck.x - self.puck.radius < MARGIN:
            if GOAL_TOP < self.puck.y < GOAL_BOTTOM:
                # Puck fully entered the LEFT (player's) goal -> computer scores.
                self.computer_score += 1
                self._reset_puck()
            else:
                self.puck.x = MARGIN + self.puck.radius
                self.puck.vx = -self.puck.vx
        elif self.puck.x + self.puck.radius > WIDTH - MARGIN:
            if GOAL_TOP < self.puck.y < GOAL_BOTTOM:
                # Puck fully entered the RIGHT (computer's) goal -> player scores.
                self.player_score += 1
                self._reset_puck()
            else:
                self.puck.x = WIDTH - MARGIN - self.puck.radius
                self.puck.vx = -self.puck.vx

    def get_winner(self):
        """Decide the result from the current scores (used when a match ends)."""
        if self.player_score > self.computer_score:
            return "Player"
        elif self.computer_score > self.player_score:
            return "Computer"
        return "Draw"

    def _reset_puck(self):
        self.puck.x, self.puck.y = WIDTH / 2, HEIGHT / 2
        self.puck.vx = 0
        self.puck.vy = 0

    def draw(self, surface, font):
        from game import renderer
        renderer.draw_table(surface)
        renderer.draw_paddle(surface, self.player, renderer.COLOR_PLAYER)
        renderer.draw_paddle(surface, self.computer, renderer.COLOR_COMPUTER)
        renderer.draw_puck(surface, self.puck)

        # Live scores: player (blue) on the left, computer (red) on the right.
        renderer.draw_text(surface, font, f"Player: {self.player_score}",
                           (MARGIN + 10, MARGIN + 8), renderer.COLOR_PLAYER)
        comp_text = f"Computer: {self.computer_score}"
        comp_w = font.size(comp_text)[0]
        renderer.draw_text(surface, font, comp_text,
                           (WIDTH - MARGIN - 10 - comp_w, MARGIN + 8), renderer.COLOR_COMPUTER)

        # Countdown timer, centred at the top.
        timer_text = f"Time: {math.ceil(self.time_left())}"
        timer_w = font.size(timer_text)[0]
        renderer.draw_text(surface, font, timer_text, (WIDTH / 2 - timer_w / 2, MARGIN + 8))

        # When the match is over, show the result and how to restart.
        if self.game_over:
            result = "Draw" if self.winner == "Draw" else f"{self.winner} Wins!"
            renderer.draw_banner(surface, font, result)
            hint = "Press R to restart"
            hint_w = font.size(hint)[0]
            renderer.draw_text(surface, font, hint,
                               (WIDTH / 2 - hint_w / 2, HEIGHT / 2 + 30))
