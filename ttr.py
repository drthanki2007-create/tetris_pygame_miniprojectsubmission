import json
import os
import random
import pygame

# Initialize Pygame
pygame.init()
pygame.font.init()

# Constants
WIDTH, HEIGHT = 700, 720
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20

# Playfield offset
GRID_X = (WIDTH - (GRID_WIDTH * BLOCK_SIZE)) // 2
GRID_Y = 40

# Colors
BLACK = (10, 10, 15)
WHITE = (240, 240, 240)
GRAY = (50, 50, 60)
LIGHT_GRAY = (90, 90, 110)
RED = (231, 76, 60)
GREEN = (46, 204, 113)

FONT_SM = pygame.font.SysFont("Arial", 14)
FONT_MD = pygame.font.SysFont("Arial", 15, bold=True)
FONT_LG = pygame.font.SysFont("Arial", 28, bold=True)

HIGHSCORE_FILE = "highscores.json"


def create_assets():
    """Generates and saves custom PNG textures locally if they don't exist."""
    os.makedirs("assets", exist_ok=True)

    # 1. Block Asset
    if not os.path.exists("assets/block.png"):
        surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
        surf.fill((200, 200, 200))
        # Inner bevel effect
        pygame.draw.rect(surf, (255, 255, 255), (2, 2, BLOCK_SIZE - 4, 4))
        pygame.draw.rect(surf, (255, 255, 255), (2, 2, 4, BLOCK_SIZE - 4))
        pygame.draw.rect(
            surf, (100, 100, 100), (2, BLOCK_SIZE - 6, BLOCK_SIZE - 4, 4)
        )
        pygame.draw.rect(
            surf, (100, 100, 100), (BLOCK_SIZE - 6, 2, 4, BLOCK_SIZE - 4)
        )
        pygame.image.save(surf, "assets/block.png")

    # 2. Button Asset (Pause/Restart)
    if not os.path.exists("assets/button.png"):
        btn_surf = pygame.Surface((120, 36))
        btn_surf.fill(LIGHT_GRAY)
        pygame.draw.rect(btn_surf, WHITE, (0, 0, 120, 36), 2)
        pygame.image.save(btn_surf, "assets/button.png")


class TetrisGame:

    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pygame Tetris Clone")
        self.clock = pygame.time.Clock()

        create_assets()
        self.block_img = pygame.image.load("assets/block.png").convert()
        self.btn_img = pygame.image.load("assets/button.png").convert()

        self.high_scores = self.load_high_scores()
        self.reset_game()

    def load_high_scores(self):
        """Loads top 5 high scores from file, or defaults if missing/corrupted."""
        default_scores = [10000, 7500, 5000, 2500, 1000]
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return sorted(data, reverse=True)[:5]
            except Exception:
                pass
        return default_scores

    def save_high_scores(self):
        """Saves current top 5 high scores to file."""
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                json.dump(self.high_scores, f)
        except Exception:
            pass

    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.paused = False

        self.base_fall_speed = 500
        self.fall_speed = self.base_fall_speed

        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.fall_time = 0
        self.score_recorded = False  # Track if score was finalized for this run

    def update_speed(self):
        self.level = min(20, (self.lines_cleared // 10) + 1)
        speed_multiplier = (0.95) ** (self.level - 1)
        self.fall_speed = max(50, int(self.base_fall_speed * speed_multiplier))

    def new_piece(self):
        shape_idx = random.randint(0, len(SHAPES) - 1)
        return {
            "shape": SHAPES[shape_idx],
            "color": SHAPE_COLORS[shape_idx],
            "x": GRID_WIDTH // 2 - len(SHAPES[shape_idx][0]) // 2,
            "y": 0,
        }

    def valid_space(self, piece, offset_x=0, offset_y=0):
        for r, row in enumerate(piece["shape"]):
            for c, val in enumerate(row):
                if val:
                    new_x = piece["x"] + c + offset_x
                    new_y = piece["y"] + r + offset_y
                    if (
                        new_x < 0
                        or new_x >= GRID_WIDTH
                        or new_y >= GRID_HEIGHT
                    ):
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return False
        return True

    def lock_piece(self):
        for r, row in enumerate(self.current_piece["shape"]):
            for c, val in enumerate(row):
                if val:
                    if self.current_piece["y"] + r < 0:
                        self.trigger_game_over()
                        return
                    self.grid[self.current_piece["y"] + r][
                        self.current_piece["x"] + c
                    ] = self.current_piece["color"]

        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        if not self.valid_space(self.current_piece):
            self.trigger_game_over()

    def clear_lines(self):
        full_rows = []
        for r, row in enumerate(self.grid):
            if all(row):
                full_rows.append(r)

        for r in full_rows:
            del self.grid[r]
            self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])

        if full_rows:
            lines = len(full_rows)
            self.lines_cleared += lines
            points = [0, 100, 300, 500, 800]
            self.score += points[lines] * self.level
            self.update_speed()
            # Dynamically update high scores during gameplay as score increases
            self.check_and_update_high_scores()

    def check_and_update_high_scores(self):
        """Adds current score into high scores if it qualifies, keeps top 5."""
        if self.score > 0:
            combined = self.high_scores + [self.score]
            combined = sorted(list(set(combined)), reverse=True)[:5]
            self.high_scores = combined
            self.save_high_scores()

    def trigger_game_over(self):
        self.game_over = True
        if not self.score_recorded:
            self.check_and_update_high_scores()
            self.score_recorded = True

    def rotate_piece(self):
        rotated = [
            [
                self.current_piece["shape"][r][c]
                for r in range(len(self.current_piece["shape"]) - 1, -1, -1)
            ]
            for c in range(len(self.current_piece["shape"][0]))
        ]
        old_shape = self.current_piece["shape"]
        self.current_piece["shape"] = rotated
        if not self.valid_space(self.current_piece):
            self.current_piece["shape"] = old_shape

    def draw(self):
        self.screen.fill(BLACK)

        # ==================== LEFT PANEL ====================
        left_panel_x = 25

        # 1. Next Piece Box
        next_lbl = FONT_MD.render("NEXT BLOCK", True, WHITE)
        self.screen.blit(next_lbl, (left_panel_x, 40))
        pygame.draw.rect(
            self.screen, GRAY, (left_panel_x, 68, 140, 90), 2, border_radius=4
        )
        if self.next_piece:
            np_shape = self.next_piece["shape"]
            np_color = self.next_piece["color"]
            ox = left_panel_x + (140 - len(np_shape[0]) * BLOCK_SIZE) // 2
            oy = 68 + (90 - len(np_shape) * BLOCK_SIZE) // 2
            for r, row in enumerate(np_shape):
                for c, val in enumerate(row):
                    if val:
                        tinted_img = self.block_img.copy()
                        tinted_img.fill(np_color, special_flags=pygame.BLEND_MULT)
                        self.screen.blit(tinted_img, (ox + c * 20, oy + r * 20))

        # 2. Top 5 Scores Box
        hs_y = 185
        hs_title = FONT_MD.render("TOP 5 SCORES", True, WHITE)
        self.screen.blit(hs_title, (left_panel_x, hs_y))
        pygame.draw.rect(
            self.screen,
            GRAY,
            (left_panel_x, hs_y + 28, 140, 160),
            2,
            border_radius=4,
        )
        for idx, score in enumerate(self.high_scores):
            score_txt = FONT_SM.render(f"{idx+1}. {score}", True, LIGHT_GRAY)
            self.screen.blit(
                score_txt, (left_panel_x + 15, hs_y + 42 + idx * 26)
            )

        # ==================== CENTER: PLAYFIELD GRID ====================
        pygame.draw.rect(
            self.screen,
            GRAY,
            (
                GRID_X - 2,
                GRID_Y - 2,
                GRID_WIDTH * BLOCK_SIZE + 4,
                GRID_HEIGHT * BLOCK_SIZE + 4,
            ),
            2,
        )
        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                pygame.draw.rect(
                    self.screen,
                    (15, 15, 22),
                    (
                        GRID_X + c * BLOCK_SIZE,
                        GRID_Y + r * BLOCK_SIZE,
                        BLOCK_SIZE,
                        BLOCK_SIZE,
                    ),
                    1,
                )

        # Locked Blocks
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val:
                    tinted_img = self.block_img.copy()
                    tinted_img.fill(val, special_flags=pygame.BLEND_MULT)
                    self.screen.blit(
                        tinted_img,
                        (GRID_X + c * BLOCK_SIZE, GRID_Y + r * BLOCK_SIZE),
                    )

        # Active Piece
        if self.current_piece:
            for r, row in enumerate(self.current_piece["shape"]):
                for c, val in enumerate(row):
                    if val:
                        px = GRID_X + (self.current_piece["x"] + c) * BLOCK_SIZE
                        py = GRID_Y + (self.current_piece["y"] + r) * BLOCK_SIZE
                        if py >= GRID_Y:
                            tinted_img = self.block_img.copy()
                            tinted_img.fill(
                                self.current_piece["color"],
                                special_flags=pygame.BLEND_MULT,
                            )
                            self.screen.blit(tinted_img, (px, py))

        # ==================== RIGHT PANEL ====================
        right_panel_x = GRID_X + (GRID_WIDTH * BLOCK_SIZE) + 25

        # Stats Box
        stats_lbl = FONT_MD.render("STATS", True, WHITE)
        self.screen.blit(stats_lbl, (right_panel_x, 40))
        pygame.draw.rect(
            self.screen,
            GRAY,
            (right_panel_x, 68, 140, 120),
            2,
            border_radius=4,
        )

        score_txt = FONT_SM.render("Score:", True, LIGHT_GRAY)
        score_val = FONT_MD.render(f"{self.score}", True, WHITE)
        level_txt = FONT_SM.render("Level:", True, LIGHT_GRAY)
        level_val = FONT_MD.render(
            f"{self.level}/20", True, GREEN if self.level < 20 else RED
        )
        lines_txt = FONT_SM.render(
            f"Lines: {self.lines_cleared}", True, LIGHT_GRAY
        )

        self.screen.blit(score_txt, (right_panel_x + 15, 82))
        self.screen.blit(score_val, (right_panel_x + 15, 102))
        self.screen.blit(level_txt, (right_panel_x + 15, 128))
        self.screen.blit(level_val, (right_panel_x + 15, 148))

        # Action Buttons (Pause & Restart) safely at bottom right
        btn_x = right_panel_x + 10
        pause_y = 560
        restart_y = 615

        self.screen.blit(self.btn_img, (btn_x, pause_y))
        self.screen.blit(self.btn_img, (btn_x, restart_y))

        pause_text_str = "RESUME" if self.paused else "PAUSE"
        pause_txt = FONT_MD.render(pause_text_str, True, WHITE)
        restart_txt = FONT_MD.render("RESTART", True, WHITE)

        self.screen.blit(
            pause_txt,
            (
                btn_x + (120 - pause_txt.get_width()) // 2,
                pause_y + (36 - pause_txt.get_height()) // 2,
            ),
        )
        self.screen.blit(
            restart_txt,
            (
                btn_x + (120 - restart_txt.get_width()) // 2,
                restart_y + (36 - restart_txt.get_height()) // 2,
            ),
        )

        # Pause/Game Over Overlays
        if self.paused and not self.game_over:
            pause_overlay = FONT_LG.render("GAME PAUSED", True, WHITE)
            self.screen.blit(
                pause_overlay,
                (
                    GRID_X + (GRID_WIDTH * BLOCK_SIZE - pause_overlay.get_width()) // 2,
                    HEIGHT // 2 - 20,
                ),
            )

        if self.game_over:
            go_surf = FONT_LG.render("GAME OVER", True, RED)
            sub_surf = FONT_SM.render(
                "Press Restart or 'R' to play again", True, WHITE
            )
            self.screen.blit(
                go_surf,
                (
                    GRID_X + (GRID_WIDTH * BLOCK_SIZE - go_surf.get_width()) // 2,
                    HEIGHT // 2 - 40,
                ),
            )
            self.screen.blit(
                sub_surf,
                (
                    GRID_X + (GRID_WIDTH * BLOCK_SIZE - sub_surf.get_width()) // 2,
                    HEIGHT // 2 + 10,
                ),
            )

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    right_panel_x = GRID_X + (GRID_WIDTH * BLOCK_SIZE) + 25
                    btn_x = right_panel_x + 10

                    # Pause Button Check
                    if btn_x <= mx <= btn_x + 120 and 560 <= my <= 596:
                        self.paused = not self.paused
                    # Restart Button Check
                    elif btn_x <= mx <= btn_x + 120 and 615 <= my <= 651:
                        self.reset_game()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_p:
                        self.paused = not self.paused

                    if not self.paused and not self.game_over:
                        if event.key == pygame.K_LEFT:
                            if self.valid_space(
                                self.current_piece, offset_x=-1
                            ):
                                self.current_piece["x"] -= 1
                        elif event.key == pygame.K_RIGHT:
                            if self.valid_space(
                                self.current_piece, offset_x=1
                            ):
                                self.current_piece["x"] += 1
                        elif event.key == pygame.K_DOWN:
                            if self.valid_space(
                                self.current_piece, offset_y=1
                            ):
                                self.current_piece["y"] += 1
                        elif event.key == pygame.K_UP:
                            self.rotate_piece()
                        elif event.key == pygame.K_SPACE:
                            while self.valid_space(
                                self.current_piece, offset_y=1
                            ):
                                self.current_piece["y"] += 1
                            self.lock_piece()

            if not self.paused and not self.game_over:
                self.fall_time += dt
                if self.fall_time >= self.fall_speed:
                    self.fall_time = 0
                    if self.valid_space(self.current_piece, offset_y=1):
                        self.current_piece["y"] += 1
                    else:
                        self.lock_piece()

            self.draw()

        pygame.quit()


# Tetrimino definitions
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 0, 0], [1, 1, 1]],  # L
    [[0, 0, 1], [1, 1, 1]],  # J
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
]

SHAPE_COLORS = [
    (0, 240, 240),  # Cyan
    (240, 240, 0),  # Yellow
    (160, 0, 240),  # Purple
    (240, 160, 0),  # Orange
    (0, 0, 240),  # Blue
    (0, 240, 0),  # Green
    (240, 0, 0),  # Red
]

if __name__ == "__main__":
    game = TetrisGame()
    game.run()