try:
    import pygame
    # Some broken installs leave a namespace package named "pygame" with no API.
    if not hasattr(pygame, "init"):
        raise ImportError("Broken pygame namespace package")
except Exception:
    try:
        import pygame_ce as pygame
    except Exception as exc:
        raise ModuleNotFoundError(
            "No working pygame package found. Reinstall with: "
            "python3 -m pip uninstall -y pygame pygame-ce && "
            "python3 -m pip install --force-reinstall pygame-ce"
        ) from exc
import sys
import math
import random

KEYDOWN = pygame.KEYDOWN
QUIT = pygame.QUIT
K_LEFT = pygame.K_LEFT
K_RIGHT = pygame.K_RIGHT
K_SPACE = pygame.K_SPACE
K_RETURN = pygame.K_RETURN
K_ESCAPE = pygame.K_ESCAPE
K_1 = pygame.K_1
K_2 = pygame.K_2
K_3 = pygame.K_3
K_UP = pygame.K_UP
K_DOWN = pygame.K_DOWN

# Constants
SCALE = 2
TILE = 16
WIDTH = int(300 * SCALE)
HEIGHT = int(200 * SCALE)
FPS = 60
# SMB1 status bar is ~32 NES px tall; scale to match SCALE.
SMB1_HUD_H = 32 * SCALE

# NES Palette
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), 
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0), 
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0), 
    (0, 50, 60), (0, 0, 0), (152, 150, 152), (8, 76, 196), 
    (48, 50, 236), (92, 30, 228), (136, 20, 176), (160, 20, 100), 
    (152, 34, 32), (120, 60, 0), (84, 90, 0), (40, 114, 0), 
    (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), 
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), 
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32), 
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108), 
    (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0)
]

# Palette helper
def palette_nearest(color):
    return color  # We'll use direct palette colors

N = palette_nearest

SMB1_SKY = (92, 148, 252)
SMB1_WHITE = (252, 252, 252)
SMB1_BLACK = (0, 0, 0)
SMB1_GROUND = (200, 76, 12)
SMB1_GROUND_DARK = (120, 40, 0)
SMB1_GROUND_LIGHT = (248, 160, 68)
SMB1_BRICK = (196, 76, 28)
SMB1_BRICK_LIGHT = (248, 188, 72)
SMB1_BLOCK = (248, 176, 56)
SMB1_PIPE = (0, 168, 0)
SMB1_PIPE_DARK = (0, 88, 0)
SMB1_PIPE_LIGHT = (108, 252, 108)

_SMB1_HUD_FONT = None
_SMB1_TILE_FONT = None


def _smb1_hud_font():
    global _SMB1_HUD_FONT
    if _SMB1_HUD_FONT is None:
        # Fit four rows inside SMB1_HUD_H (32 NES px × SCALE).
        size = max(15, 8 * SCALE)
        fonts = pygame.font.get_fonts()
        chosen = None
        for face in ("couriernew", "monaco", "menlo", "consolas", "courier"):
            if face in fonts:
                chosen = face
                break
        if chosen:
            _SMB1_HUD_FONT = pygame.font.SysFont(chosen, size, bold=True)
        else:
            _SMB1_HUD_FONT = pygame.font.SysFont(None, size, bold=True)
    return _SMB1_HUD_FONT


def _smb1_tile_font():
    global _SMB1_TILE_FONT
    if _SMB1_TILE_FONT is None:
        _SMB1_TILE_FONT = pygame.font.SysFont(None, 18, bold=True)
    return _SMB1_TILE_FONT


def _draw_smb1_hud_coin(surf, x, y):
    """Small oval coin (SMB1-style) for the status bar."""
    gold = (220, 180, 48)
    hi = (248, 228, 120)
    w = max(12, 7 * SCALE // 2)
    h = max(14, 8 * SCALE // 2)
    r = pygame.Rect(int(x), int(y), w, h)
    pygame.draw.ellipse(surf, gold, r)
    pygame.draw.ellipse(surf, hi, (r.x + 2, r.y + 2, r.w - 5, r.h // 2))
    pygame.draw.ellipse(surf, (0, 0, 0), r, 1)


def draw_smb1_status_bar(surf, level_id, time_left):
    """Top HUD matching SMB1: MARIO + score | coin ×00 | WORLD / 1-1 / TIME / value."""
    surf.fill((0, 0, 0), (0, 0, WIDTH, SMB1_HUD_H))
    font = _smb1_hud_font()
    white = NES_PALETTE[28]
    row_h = SMB1_HUD_H // 4
    y0, y1, y2, y3 = [row_h * i + 2 for i in range(4)]
    margin = 8 * SCALE // 2

    surf.blit(font.render("KOOPA X", True, white), (margin, y0))
    surf.blit(font.render(f"{state.score:06d}", True, white), (margin, y1))

    coin_txt = font.render(f"×{state.coins:02d}", True, white)
    icon_gap = max(12, 7 * SCALE // 2) + 4
    coin_block_w = icon_gap + coin_txt.get_width()
    coin_x = (WIDTH - coin_block_w) // 2
    _draw_smb1_hud_coin(surf, coin_x, y0 + 2)
    surf.blit(coin_txt, (coin_x + icon_gap, y0))

    t_world = font.render("WORLD", True, white)
    t_lvl = font.render(level_id, True, white)
    t_time_lbl = font.render("TIME", True, white)
    tv = max(0, int(time_left))
    t_time_val = font.render(f"{tv:03d}", True, white)
    col_w = max(
        t_world.get_width(),
        t_lvl.get_width(),
        t_time_lbl.get_width(),
        t_time_val.get_width(),
    )
    rx = WIDTH - margin - col_w
    surf.blit(t_world, (rx, y0))
    surf.blit(t_lvl, (rx, y1))
    surf.blit(t_time_lbl, (rx, y2))
    surf.blit(t_time_val, (rx, y3))


def draw_smb1_cloud(surf, x, y):
    pygame.draw.rect(surf, SMB1_WHITE, (x + 8, y + 8, 32, 12))
    pygame.draw.ellipse(surf, SMB1_WHITE, (x, y + 8, 18, 18))
    pygame.draw.ellipse(surf, SMB1_WHITE, (x + 12, y, 22, 22))
    pygame.draw.ellipse(surf, SMB1_WHITE, (x + 28, y + 6, 20, 20))


def draw_smb1_ground_tile(surf, x, y, top=False):
    pygame.draw.rect(surf, SMB1_GROUND, (x, y, TILE, TILE))
    if top:
        pygame.draw.rect(surf, SMB1_GROUND_LIGHT, (x, y, TILE, 2))
    pygame.draw.line(surf, SMB1_GROUND_DARK, (x, y + 7), (x + TILE - 1, y + 7), 1)
    pygame.draw.line(surf, SMB1_GROUND_DARK, (x + 7, y), (x + 7, y + TILE - 1), 1)
    pygame.draw.line(surf, SMB1_GROUND_LIGHT, (x + 1, y + 1), (x + 5, y + 1), 1)
    pygame.draw.line(surf, SMB1_GROUND_LIGHT, (x + 9, y + 10), (x + 14, y + 10), 1)


def draw_smb1_brick(surf, x, y):
    pygame.draw.rect(surf, SMB1_BRICK, (x, y, TILE, TILE))
    pygame.draw.rect(surf, SMB1_BLACK, (x, y, TILE, 1))
    pygame.draw.rect(surf, SMB1_BLACK, (x, y + 7, TILE, 1))
    pygame.draw.rect(surf, SMB1_BLACK, (x, y + 15, TILE, 1))
    pygame.draw.rect(surf, SMB1_BLACK, (x + 7, y, 1, 7))
    pygame.draw.rect(surf, SMB1_BLACK, (x + 3, y + 8, 1, 7))
    pygame.draw.rect(surf, SMB1_BLACK, (x + 11, y + 8, 1, 7))
    pygame.draw.rect(surf, SMB1_BRICK_LIGHT, (x + 1, y + 1, 5, 1))
    pygame.draw.rect(surf, SMB1_BRICK_LIGHT, (x + 9, y + 9, 5, 1))


def draw_smb1_question_block(surf, x, y):
    pygame.draw.rect(surf, SMB1_BLOCK, (x, y, TILE, TILE))
    pygame.draw.rect(surf, SMB1_BLACK, (x, y, TILE, TILE), 1)
    pygame.draw.rect(surf, SMB1_GROUND_DARK, (x + 2, y + 2, TILE - 4, TILE - 4), 1)
    font = _smb1_tile_font()
    q = font.render("?", True, SMB1_WHITE)
    surf.blit(q, (x + (TILE - q.get_width()) // 2, y + (TILE - q.get_height()) // 2 - 1))


def draw_smb1_pipe_tile(surf, x, y):
    pygame.draw.rect(surf, SMB1_PIPE, (x, y, TILE, TILE))
    pygame.draw.rect(surf, SMB1_PIPE_DARK, (x, y, TILE, TILE), 1)
    pygame.draw.rect(surf, SMB1_PIPE_LIGHT, (x + 2, y + 2, 3, TILE - 4))
    pygame.draw.rect(surf, SMB1_PIPE_DARK, (x + TILE - 4, y + 1, 3, TILE - 2))


# Game State
class GameState:
    def __init__(self):
        self.slot = 0
        self.progress = [{"world": 1}, {"world": 1}, {"world": 1}]
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.world = 1  # Current world (1-8)
        self.level = 1  # Current level (1-4)
        self.time = 300
        self.mario_size = "small"  # "small" or "big"
        self.unlocked_worlds = [1]  # Which worlds are unlocked

state = GameState()

# Scene management
SCENES = []

def push(scene): SCENES.append(scene)
def pop():
    if SCENES:
        SCENES.pop()
def replace(scene):
    """Swap the top scene without growing the stack."""
    if SCENES:
        SCENES[-1] = scene
    else:
        SCENES.append(scene)

class Scene:
    def handle(self, events, keys): ...
    def update(self, dt): ...
    def draw(self, surf): ...

# World themes
WORLD_THEMES = {
    1: {"sky": 27, "ground": 20, "pipe": 14, "block": 33, "water": None, "enemy": "goomba", "name": "GRASS LAND"},
    2: {"sky": 26, "ground": 21, "pipe": 15, "block": 34, "water": None, "enemy": "koopa", "name": "DESERT HILL"},
    3: {"sky": 25, "ground": 22, "pipe": 16, "block": 35, "water": 45, "enemy": "fish", "name": "AQUA SEA"},
    4: {"sky": 24, "ground": 23, "pipe": 17, "block": 36, "water": None, "enemy": "goomba", "name": "GIANT FOREST"},
    5: {"sky": 23, "ground": 24, "pipe": 18, "block": 37, "water": None, "enemy": "spike", "name": "SKY HEIGHTS"},
    6: {"sky": 22, "ground": 25, "pipe": 19, "block": 38, "water": None, "enemy": "goomba", "name": "ICE CAVERN"},
    7: {"sky": 21, "ground": 26, "pipe": 20, "block": 39, "water": None, "enemy": "spike", "name": "LAVA CASTLE"},
    8: {"sky": 20, "ground": 27, "pipe": 21, "block": 40, "water": None, "enemy": "koopa", "name": "FINAL FORTRESS"}
}

# Generate 32 levels (8 worlds * 4 levels)
def generate_level_data():
    levels = {}
    for world in range(1, 9):
        for level in range(1, 5):
            level_id = f"{world}-{level}"
            theme = WORLD_THEMES[world]
            
            # Create a unique level pattern for each level
            level_data = []
            
            # Sky
            for i in range(10):
                level_data.append(" " * 100)
                
            # Platforms
            for i in range(10, 15):
                level_data.append(" " * 100)
                
            # Ground
            for i in range(15, 20):
                if i == 15:
                    row = "G" * 100
                else:
                    row = "D" * 100
                level_data.append(row)
            
            # Add platforms
            for i in range(5 + level):  # More platforms in later levels
                platform_y = random.randint(8, 12)
                platform_x = random.randint(10 + i*20, 15 + i*20)
                length = random.randint(4, 8)
                for j in range(length):
                    level_data[platform_y] = level_data[platform_y][:platform_x+j] + "P" + level_data[platform_y][platform_x+j+1:]
            
            # Add pipes
            for i in range(2 + level//2):  # More pipes in later levels
                pipe_x = random.randint(20 + i*30, 25 + i*30)
                pipe_height = random.randint(2, 4)
                for j in range(pipe_height):
                    level_data[19-j] = level_data[19-j][:pipe_x] + "T" + level_data[19-j][pipe_x+1:]
                    level_data[19-j] = level_data[19-j][:pipe_x+1] + "T" + level_data[19-j][pipe_x+2:]
            
            # Add bricks and question blocks
            for i in range(8 + level):  # More blocks in later levels
                block_y = random.randint(5, 10)
                block_x = random.randint(5 + i*10, 8 + i*10)
                block_type = "?" if random.random() > 0.5 else "B"
                level_data[block_y] = level_data[block_y][:block_x] + block_type + level_data[block_y][block_x+1:]
            
            # Add player start
            level_data[14] = level_data[14][:5] + "S" + level_data[14][6:]
            
            # Add flag at end (taller pole)
            level_data[10] = level_data[10][:95] + "F" + level_data[10][96:]
            
            # Add enemies
            for i in range(5 + level):  # More enemies in later levels
                enemy_y = 14
                enemy_x = random.randint(20 + i*15, 25 + i*15)
                level_data[enemy_y] = level_data[enemy_y][:enemy_x] + "E" + level_data[enemy_y][enemy_x+1:]
            
            levels[level_id] = level_data
    
    return levels

LEVELS = generate_level_data()

# Create thumbnails
THUMBNAILS = {}
for level_id, level_data in LEVELS.items():
    world = int(level_id.split("-")[0])
    theme = WORLD_THEMES[world]
    
    thumb = pygame.Surface((32, 24))
    thumb.fill(NES_PALETTE[theme["sky"]])  # Sky color
    
    # Draw a simple representation of the level
    for y, row in enumerate(level_data[10:14]):
        for x, char in enumerate(row[::3]):  # Sample every 3rd column
            if char in ("G", "B", "P", "T"):
                thumb.set_at((x, y+10), NES_PALETTE[theme["ground"]])  # Ground color
            elif char in ("?", "B"):
                thumb.set_at((x, y+10), NES_PALETTE[theme["block"]])  # Block color
    
    THUMBNAILS[level_id] = thumb

# Entity classes
class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = TILE
        self.height = TILE
        self.on_ground = False
        self.facing_right = True
        self.active = True
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def check_collision(self, other):
        return self.get_rect().colliderect(other.get_rect())
        
    def update(self, colliders, dt):
        # Apply gravity
        if not self.on_ground:
            self.vy += 0.5 * dt * 60
            
        # Update position
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        
        # Check collision with ground
        self.on_ground = False
        for rect in colliders:
            if self.get_rect().colliderect(rect):
                # Bottom collision
                if self.vy > 0 and self.y + self.height > rect.top and self.y < rect.top:
                    self.y = rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                # Top collision
                elif self.vy < 0 and self.y < rect.bottom and self.y + self.height > rect.bottom:
                    self.y = rect.bottom
                    self.vy = 0
                # Left collision
                if self.vx > 0 and self.x + self.width > rect.left and self.x < rect.left:
                    self.x = rect.left - self.width
                    self.vx = 0
                # Right collision
                elif self.vx < 0 and self.x < rect.right and self.x + self.width > rect.right:
                    self.x = rect.right
                    self.vx = 0
                    
    def draw(self, surf, cam):
        pass

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.jump_power = -5
        self.move_speed = 2
        self.invincible = 0
        self.animation_frame = 0
        self.walk_timer = 0
        
    def update(self, colliders, dt, enemies):
        # Handle input
        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        self.vx = 0
        if keys[K_LEFT]:
            self.vx = -self.move_speed
            self.facing_right = False
        if keys[K_RIGHT]:
            self.vx = self.move_speed
            self.facing_right = True
            
        # Jumping
        if keys[K_SPACE] and self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False
            
        # Update walk animation
        if self.vx != 0:
            self.walk_timer += dt
            if self.walk_timer > 0.1:
                self.walk_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 3
        else:
            self.animation_frame = 0
            
        # Update invincibility
        if self.invincible > 0:
            self.invincible -= dt
            
        super().update(colliders, dt)
        
        # Check collision with enemies
        for enemy in enemies:
            if enemy.active and self.check_collision(enemy):
                # Jumped on enemy
                if self.vy > 0 and self.y + self.height - 5 < enemy.y:
                    enemy.active = False
                    self.vy = self.jump_power / 2
                    state.score += 100
                # Hit by enemy
                elif self.invincible <= 0:
                    if state.mario_size == "big":
                        state.mario_size = "small"
                        self.invincible = 2
                    else:
                        state.lives -= 1
                        if state.lives <= 0:
                            # Game over
                            replace(GameOverScene())
                        else:
                            # Reset position
                            self.x = 50
                            self.y = 100
                            self.vx = 0
                            self.vy = 0
                    
    def draw(self, surf, cam):
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return  # Blink during invincibility
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Draw Mario based on size
        if state.mario_size == "big":
            # Body
            pygame.draw.rect(surf, NES_PALETTE[33], (x+4, y+8, 8, 16))  # Red overalls
            
            # Head
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y+4, 8, 4))  # Face
            
            # Hat
            pygame.draw.rect(surf, NES_PALETTE[33], (x+2, y, 12, 4))  # Red hat
            
            # Arms
            arm_offset = 0
            if self.animation_frame == 1 and self.vx != 0:
                arm_offset = 2 if self.facing_right else -2
                
            pygame.draw.rect(surf, NES_PALETTE[39], (x+arm_offset, y+10, 4, 6))  # Left arm
            pygame.draw.rect(surf, NES_PALETTE[39], (x+12-arm_offset, y+10, 4, 6))  # Right arm
            
            # Legs
            leg_offset = 0
            if self.animation_frame == 2 and self.vx != 0:
                leg_offset = 2 if self.facing_right else -2
                
            pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+24, 4, 8))  # Left leg
            pygame.draw.rect(surf, NES_PALETTE[21], (x+10, y+24-leg_offset, 4, 8+leg_offset))  # Right leg
        else:
            # Small Mario
            # Body
            pygame.draw.rect(surf, NES_PALETTE[33], (x+4, y+8, 8, 8))  # Red overalls
            
            # Head
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y, 8, 8))  # Face
            
            # Hat
            pygame.draw.rect(surf, NES_PALETTE[33], (x+2, y, 12, 2))  # Red hat

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.animation_frame = 0
        self.walk_timer = 0
        
    def update(self, colliders, dt):
        # Turn around at edges
        if self.on_ground:
            # Check for edge
            edge_check = pygame.Rect(self.x + (self.width if self.vx > 0 else -1), 
                                    self.y + self.height, 
                                    1, 1)
            edge_found = False
            for rect in colliders:
                if edge_check.colliderect(rect):
                    edge_found = True
                    break
                    
            if not edge_found:
                self.vx *= -1
                
        super().update(colliders, dt)
        
        # Update animation
        self.walk_timer += dt
        if self.walk_timer > 0.2:
            self.walk_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2
            
    def draw(self, surf, cam):
        if not self.active:
            return
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Body
        pygame.draw.ellipse(surf, NES_PALETTE[21], (x+2, y+4, 12, 12))  # Brown body
        
        # Feet
        foot_offset = 2 if self.animation_frame == 0 else -2
        pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+14, 4, 2))  # Left foot
        pygame.draw.rect(surf, NES_PALETTE[21], (x+10, y+14+foot_offset, 4, 2))  # Right foot
        
        # Eyes
        eye_dir = 0 if self.vx > 0 else 2
        pygame.draw.rect(surf, NES_PALETTE[0], (x+4+eye_dir, y+6, 2, 2))  # Left eye
        pygame.draw.rect(surf, NES_PALETTE[0], (x+10-eye_dir, y+6, 2, 2))  # Right eye

class Koopa(Goomba):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.shell_mode = False
        
    def draw(self, surf, cam):
        if not self.active:
            return
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Shell
        pygame.draw.ellipse(surf, NES_PALETTE[14], (x+2, y+4, 12, 12))  # Green shell
        
        # Head and feet
        if not self.shell_mode:
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y, 8, 4))  # Head
            pygame.draw.rect(surf, NES_PALETTE[14], (x+2, y+14, 4, 2))  # Left foot
            pygame.draw.rect(surf, NES_PALETTE[14], (x+10, y+14, 4, 2))  # Right foot

class Fish(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.animation_frame = 0
        self.swim_timer = 0
        self.in_water = True
        
    def update(self, colliders, dt):
        # Move in sine wave pattern
        self.swim_timer += dt
        self.y += math.sin(self.swim_timer * 5) * 0.5
        
        super().update(colliders, dt)
        
    def draw(self, surf, cam):
        if not self.active:
            return
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Body
        pygame.draw.ellipse(surf, NES_PALETTE[31], (x, y, 16, 8))  # Blue fish
        
        # Tail
        pygame.draw.polygon(surf, NES_PALETTE[31], [(x, y+4), (x-5, y), (x-5, y+8)])
        
        # Eye
        pygame.draw.circle(surf, NES_PALETTE[0], (x+12, y+4), 2)

class Spike(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.width = TILE
        self.height = TILE
        
    def draw(self, surf, cam):
        x = int(self.x - cam)
        y = int(self.y)
        
        # Spike base
        pygame.draw.rect(surf, NES_PALETTE[33], (x, y, TILE, TILE))
        
        # Spike
        pygame.draw.polygon(surf, NES_PALETTE[39], [
            (x + TILE//2, y),
            (x, y + TILE),
            (x + TILE, y + TILE)
        ])

class TileMap:
    def __init__(self, level_data, level_id):
        self.tiles = []
        self.colliders = []
        self.width = len(level_data[0]) * TILE
        self.height = len(level_data) * TILE
        self.flag_y_offset = 0
        self.level_id = level_id
        world = int(level_id.split("-")[0])
        self.theme = WORLD_THEMES[world]
        
        # Parse level data
        for y, row in enumerate(level_data):
            for x, char in enumerate(row):
                if char != " ":
                    rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                    self.tiles.append((x * TILE, y * TILE, char))
                    
                    if char in ("G", "D", "B", "P", "T", "?"):
                        self.colliders.append(rect)
    
    def draw(self, surf, cam):
        # Draw SMB1 overworld sky for every generated level.
        surf.fill(SMB1_SKY)
        
        # Draw clouds
        for i in range(10):
            x = (i * 80 + int(cam/3)) % (self.width + 200) - 100
            y = 30 + (i % 3) * 20
            draw_smb1_cloud(surf, x, y)
        
        # Draw tiles
        for x, y, char in self.tiles:
            draw_x = x - cam
            if draw_x < -TILE or draw_x > WIDTH:
                continue
                
            if char == "G":  # SMB1 ground surface
                draw_smb1_ground_tile(surf, draw_x, y, top=True)
            elif char == "D":  # SMB1 ground body
                draw_smb1_ground_tile(surf, draw_x, y)
            elif char == "B":  # Brick block
                draw_smb1_brick(surf, draw_x, y)
            elif char == "P":  # Platform
                draw_smb1_brick(surf, draw_x, y)
            elif char == "T":  # Pipe
                draw_smb1_pipe_tile(surf, draw_x, y)
            elif char == "?":  # Question block
                draw_smb1_question_block(surf, draw_x, y)
            elif char == "F":  # Flag
                # Pole (5 tiles tall to reach ground)
                pygame.draw.rect(surf, SMB1_WHITE, (draw_x + 7, y, 2, TILE * 5))
                pygame.draw.rect(surf, SMB1_BLACK, (draw_x + 9, y, 1, TILE * 5))
                pygame.draw.circle(surf, SMB1_PIPE, (int(draw_x + 8), y - 3), 4)
                # Flag
                fy = y + self.flag_y_offset
                pygame.draw.polygon(
                    surf,
                    SMB1_WHITE,
                    [(draw_x + 7, fy), (draw_x - 15, fy + 5), (draw_x + 7, fy + 10)],
                )
                pygame.draw.polygon(
                    surf,
                    SMB1_BLACK,
                    [(draw_x + 7, fy), (draw_x - 15, fy + 5), (draw_x + 7, fy + 10)],
                    1,
                )

# Scenes
class TitleScreen(Scene):
    def __init__(self):
        self.timer = 0
        self.animation_frame = 0
        self.logo_y = -50
        self.logo_target_y = HEIGHT // 2 - 60
        
    def handle(self, events, keys):
        for e in events:
            if e.type == KEYDOWN and e.key == K_RETURN:
                push(FileSelect())
                
    def update(self, dt):
        self.timer += dt
        if self.timer > 0.1:
            self.timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
            
        # Animate logo coming down
        if self.logo_y < self.logo_target_y:
            self.logo_y += 3
            
    def draw(self, surf):
        # Background
        surf.fill(NES_PALETTE[27])
        
        # Koopa Engine Box
        box_width, box_height = 240, 100
        box_x = (WIDTH - box_width) // 2
        box_y = self.logo_y
        
        # Draw box with border
        pygame.draw.rect(surf, NES_PALETTE[0], (box_x-4, box_y-4, box_width+8, box_height+8))
        pygame.draw.rect(surf, NES_PALETTE[33], (box_x, box_y, box_width, box_height))
        
        # Title inside box
        title_font = pygame.font.SysFont(None, 32)
        title = title_font.render("KOOPA ENGINE 1.0A", True, NES_PALETTE[39])
        surf.blit(title, (box_x + (box_width - title.get_width()) // 2, box_y + 15))
        
        subtitle_font = pygame.font.SysFont(None, 16)
        subtitle = subtitle_font.render("8 Worlds Edition", True, NES_PALETTE[21])
        surf.blit(subtitle, (box_x + (box_width - subtitle.get_width()) // 2, box_y + 50))
        
        # Copyright
        copyright_font = pygame.font.SysFont(None, 14)
        copyright = copyright_font.render("[C] Team Flames 20XX [1985] - Nintendo", True, NES_PALETTE[0])
        surf.blit(copyright, (WIDTH//2 - copyright.get_width()//2, box_y + box_height + 20))
        
        # Mario and enemies
        mario_x = WIDTH//2 - 100
        mario_y = box_y + box_height + 50
        pygame.draw.rect(surf, NES_PALETTE[33], (mario_x+4, mario_y+8, 8, 16))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x+4, mario_y+4, 8, 4))
        pygame.draw.rect(surf, NES_PALETTE[33], (mario_x+2, mario_y, 12, 4))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x, mario_y+10, 4, 6))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x+16, mario_y+10, 4, 6))
        pygame.draw.rect(surf, NES_PALETTE[21], (mario_x+2, mario_y+24, 4, 8))
        pygame.draw.rect(surf, NES_PALETTE[21], (mario_x+10, mario_y+24, 4, 8))
        
        # Goomba
        goomba_x = WIDTH//2 + 30
        goomba_y = mario_y + 20
        pygame.draw.ellipse(surf, NES_PALETTE[21], (goomba_x+2, goomba_y+4, 12, 12))
        pygame.draw.rect(surf, NES_PALETTE[21], (goomba_x+2, goomba_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[21], (goomba_x+10, goomba_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[0], (goomba_x+4, goomba_y+6, 2, 2))
        pygame.draw.rect(surf, NES_PALETTE[0], (goomba_x+10, goomba_y+6, 2, 2))
        
        # Koopa
        koopa_x = WIDTH//2 + 70
        koopa_y = mario_y + 20
        pygame.draw.ellipse(surf, NES_PALETTE[14], (koopa_x+2, koopa_y+4, 12, 12))
        pygame.draw.rect(surf, NES_PALETTE[39], (koopa_x+4, koopa_y, 8, 4))
        pygame.draw.rect(surf, NES_PALETTE[14], (koopa_x+2, koopa_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[14], (koopa_x+10, koopa_y+14, 4, 2))
        
        # Press Start
        if self.logo_y >= self.logo_target_y and int(self.timer * 10) % 2 == 0:
            font = pygame.font.SysFont(None, 24)
            text = font.render("PRESS ENTER", True, NES_PALETTE[39])
            surf.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 30))

class FileSelect(Scene):
    def __init__(self):
        self.offset = 0
        self.selected = 0
        
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN:
                if e.key in (K_1, K_2, K_3):
                    self.selected = e.key - K_1
                elif e.key == K_RETURN:
                    state.slot = self.selected
                    state.world = state.progress[state.slot]["world"]
                    push(WorldMapScene())
                elif e.key == K_ESCAPE:
                    pop()
                    
    def update(self, dt):
        self.offset += dt
        
    def draw(self, s):
        s.fill(NES_PALETTE[27])
        
        # Title
        font = pygame.font.SysFont(None, 30)
        title = font.render("SELECT PLAYER", True, NES_PALETTE[33])
        s.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Draw file slots
        for i in range(3):
            x = 50 + i * 100
            y = 90 + 5 * math.sin(self.offset * 3 + i)
            
            # Slot background
            pygame.draw.rect(s, NES_PALETTE[21], (x-5, y-5, 50, 70))
            pygame.draw.rect(s, NES_PALETTE[33], (x, y, 40, 60))
            
            # Slot number
            slot_font = pygame.font.SysFont(None, 20)
            slot_text = slot_font.render(f"{i+1}", True, NES_PALETTE[39])
            s.blit(slot_text, (x+18, y+5))
            
            # Selection indicator
            if i == self.selected:
                pygame.draw.rect(s, NES_PALETTE[39], (x-2, y-2, 44, 64), 2)
                
            # World preview
            if state.progress[i]:
                world = state.progress[i]["world"]
                world_font = pygame.font.SysFont(None, 16)
                world_text = world_font.render(f"WORLD {world}", True, NES_PALETTE[39])
                s.blit(world_text, (x+20 - world_text.get_width()//2, y+50))
                
                # Draw thumbnail
                thumb = THUMBNAILS.get(f"{world}-1", THUMBNAILS["1-1"])
                s.blit(thumb, (x+4, y+20))

class WorldMapScene(Scene):
    def __init__(self):
        self.selection = state.world
        self.offset = 0
        self.cursor_pos = (0, 0)
        self.cursor_timer = 0
        
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN:
                if e.key == K_LEFT and self.selection > 1:
                    self.selection -= 1
                elif e.key == K_RIGHT and self.selection < 8:
                    self.selection += 1
                elif e.key == K_UP and self.selection > 4:
                    self.selection -= 4
                elif e.key == K_DOWN and self.selection < 5:
                    self.selection += 4
                elif e.key == K_RETURN:
                    if self.selection <= max(state.unlocked_worlds):
                        state.world = self.selection
                        state.progress[state.slot]["world"] = self.selection
                        push(LevelScene(f"{state.world}-1"))
                elif e.key == K_ESCAPE:
                    pop()
                    
    def update(self, dt):
        self.offset += dt
        self.cursor_timer += dt
        
    def draw(self, s):
        s.fill(NES_PALETTE[27])
        
        # Title
        font = pygame.font.SysFont(None, 30)
        title = font.render("WORLD MAP", True, NES_PALETTE[33])
        s.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Draw world grid
        world_size = 40
        for world in range(1, 9):
            row = (world - 1) // 4
            col = (world - 1) % 4
            x = 30 + col * 70
            y = 70 + row * 70
            
            theme = WORLD_THEMES[world]
            
            # Draw world tile
            if world in state.unlocked_worlds:
                pygame.draw.rect(s, NES_PALETTE[theme["ground"]], (x, y, world_size, world_size))
                pygame.draw.rect(s, NES_PALETTE[theme["block"]], (x+5, y+5, world_size-10, world_size-10))
            else:
                pygame.draw.rect(s, NES_PALETTE[0], (x, y, world_size, world_size))
                pygame.draw.rect(s, NES_PALETTE[28], (x+5, y+5, world_size-10, world_size-10))
                pygame.draw.line(s, NES_PALETTE[33], (x, y), (x+world_size, y+world_size), 3)
                pygame.draw.line(s, NES_PALETTE[33], (x+world_size, y), (x, y+world_size), 3)
            
            # Draw world number
            world_font = pygame.font.SysFont(None, 20)
            world_text = world_font.render(f"{world}", True, NES_PALETTE[39])
            s.blit(world_text, (x + world_size//2 - world_text.get_width()//2, 
                               y + world_size//2 - world_text.get_height()//2))
            
            # Draw world name if selected
            if world == self.selection:
                name_font = pygame.font.SysFont(None, 14)
                name_text = name_font.render(theme["name"], True, NES_PALETTE[39])
                s.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT - 40))
                
        # Draw cursor on selected world
        row = (self.selection - 1) // 4
        col = (self.selection - 1) % 4
        x = 30 + col * 70
        y = 70 + row * 70
        
        # Animated cursor
        cursor_offset = math.sin(self.cursor_timer * 5) * 3
        pygame.draw.rect(s, NES_PALETTE[39], (x-5, y-5 + cursor_offset, world_size+10, 5))
        pygame.draw.rect(s, NES_PALETTE[39], (x-5, y+world_size + cursor_offset, world_size+10, 5))
        
        # Draw Mario at selected world
        mario_x = x + world_size//2 - 8
        mario_y = y - 30 + cursor_offset
        pygame.draw.rect(s, NES_PALETTE[33], (mario_x+4, mario_y+8, 8, 8))
        pygame.draw.rect(s, NES_PALETTE[39], (mario_x+4, mario_y, 8, 8))
        
        # Draw instructions
        font = pygame.font.SysFont(None, 14)
        text = font.render("Arrow keys: Move  Enter: Select  Esc: Back", True, NES_PALETTE[39])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 20))
        
        # Draw unlocked worlds indicator
        unlocked_text = font.render(f"Unlocked Worlds: {max(state.unlocked_worlds)}/8", True, NES_PALETTE[39])
        s.blit(unlocked_text, (10, HEIGHT - 20))

class LevelScene(Scene):
    def __init__(self, level_id):
        self.map = TileMap(LEVELS[level_id], level_id)
        self.player = Player(50, 100)
        self.enemies = []
        self.cam = 0.0
        self.level_id = level_id
        self.time = 300
        self.coins = 0
        self.end_level = False
        self.end_timer = 0
        self.mushrooms = []
        world = int(level_id.split("-")[0])
        self.theme = WORLD_THEMES[world]
        
        # Parse level for enemies and player start
        for y, row in enumerate(LEVELS[level_id]):
            for x, char in enumerate(row):
                if char == "S":
                    self.player.x = x * TILE
                    self.player.y = y * TILE
                elif char == "E":
                    enemy_kind = self.theme.get("enemy", "goomba")
                    if enemy_kind == "koopa":
                        self.enemies.append(Koopa(x * TILE, y * TILE))
                    elif enemy_kind == "fish":
                        self.enemies.append(Fish(x * TILE, y * TILE))
                    elif enemy_kind == "spike":
                        self.enemies.append(Spike(x * TILE, y * TILE))
                    else:
                        self.enemies.append(Goomba(x * TILE, y * TILE))
    
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pop()
                
    def update(self, dt):
        # Update time
        self.time -= dt
        
        # Update player
        if not self.end_level:
            self.player.update(self.map.colliders, dt, self.enemies)
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.active:
                enemy.update(self.map.colliders, dt)
        
        # Camera follow player
        target = self.player.x - WIDTH // 2
        self.cam += (target - self.cam) * 0.1
        self.cam = max(0, min(self.cam, self.map.width - WIDTH))
        
        # Check for end of level (flag touch)
        if self.player.x >= 95 * TILE and not self.end_level:
            self.end_level = True
            self.end_timer = 4  # 4 seconds to show end sequence
            self.player.x = 95 * TILE - 4  # Snap to pole
            self.player.vx = 0
            self.player.vy = 0
            
        if self.end_level:
            # Slide down the pole
            if self.map.flag_y_offset < TILE * 4:
                self.map.flag_y_offset += 100 * dt
            
            # Player slides down to ground level
            target_y = 15 * TILE - (32 if state.mario_size == "big" else 16)
            if self.player.y < target_y:
                self.player.state = "idle"
                self.player.y += 100 * dt
                if self.player.y > target_y:
                    self.player.y = target_y
            elif self.map.flag_y_offset >= TILE * 4:
                # Walk to the right (to the castle)
                self.player.state = "walk"
                self.player.x += 50 * dt
                self.player.walk_timer += dt
                
            self.end_timer -= dt
            if self.end_timer <= 0:
                # Advance to next level
                world, level = self.level_id.split("-")
                world = int(world)
                level = int(level)
                
                if level < 4:
                    next_level = f"{world}-{level+1}"
                    replace(LevelScene(next_level))
                else:
                    # World completed
                    if world < 8 and (world + 1) not in state.unlocked_worlds:
                        state.unlocked_worlds.append(world + 1)
                    
                    # Return to world map
                    pop()
        
    def draw(self, s):
        # Draw map
        self.map.draw(s, self.cam)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(s, self.cam)
            
        # Draw player
        self.player.draw(s, self.cam)
        
        draw_smb1_status_bar(s, self.level_id, self.time)

class GameOverScene(Scene):
    def __init__(self):
        self.timer = 3
        
    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            while len(SCENES) > 2:
                pop()
            state.lives = 3
            state.score = 0
            
    def draw(self, s):
        s.fill(NES_PALETTE[0])
        font = pygame.font.SysFont(None, 40)
        text = font.render("GAME OVER", True, NES_PALETTE[33])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 20))
        
        font = pygame.font.SysFont(None, 20)
        text = font.render(f"FINAL SCORE: {state.score}", True, NES_PALETTE[39])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 20))

class WinScreen(Scene):
    def __init__(self):
        self.timer = 5
        self.fireworks = []
        
    def update(self, dt):
        self.timer -= dt
        
        # Add fireworks
        if random.random() < 0.2:
            self.fireworks.append({
                "x": random.randint(50, WIDTH-50),
                "y": HEIGHT,
                "size": random.randint(20, 40),
                "color": random.choice([NES_PALETTE[33], NES_PALETTE[39], NES_PALETTE[31]]),
                "particles": []
            })
            
        # Update fireworks
        for fw in self.fireworks[:]:
            fw["y"] -= 3
            if fw["y"] < HEIGHT//3:
                # Explode
                for i in range(20):
                    angle = random.uniform(0, math.pi*2)
                    speed = random.uniform(2, 5)
                    fw["particles"].append({
                        "x": fw["x"],
                        "y": fw["y"],
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed,
                        "life": 1.0
                    })
                self.fireworks.remove(fw)
                
        # Update particles
        for fw in self.fireworks:
            for p in fw["particles"][:]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.1
                p["life"] -= 0.02
                if p["life"] <= 0:
                    fw["particles"].remove(p)
                    
        if self.timer <= 0:
            SCENES[:] = [TitleScreen()]
            
    def draw(self, s):
        s.fill(NES_PALETTE[0])
        
        # Draw fireworks
        for fw in self.fireworks:
            pygame.draw.circle(s, NES_PALETTE[39], (int(fw["x"]), int(fw["y"])), 3)
            for p in fw["particles"]:
                alpha = int(p["life"] * 255)
                color = (min(255, fw["color"][0]), min(255, fw["color"][1]), min(255, fw["color"][2]))
                pygame.draw.circle(s, color, (int(p["x"]), int(p["y"])), 2)
        
        # Text
        font = pygame.font.SysFont(None, 40)
        text = font.render("CONGRATULATIONS!", True, NES_PALETTE[33])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 50))
        
        font = pygame.font.SysFont(None, 30)
        text = font.render("YOU SAVED THE PRINCESS!", True, NES_PALETTE[39])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 100))
        
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"FINAL SCORE: {state.score}", True, NES_PALETTE[31])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 150))

# Main game
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("KOOPA ENGINE 1.0A - 8 Worlds Edition")
clock = pygame.time.Clock()

# Start with title screen
push(TitleScreen())

while SCENES:
    dt = clock.tick(FPS) / 1000
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    
    # Handle quit events
    for e in events:
        if e.type == QUIT:
            pygame.quit()
            sys.exit()
    
    # Update current scene
    scene = SCENES[-1]
    scene.handle(events, keys)
    scene.update(dt)
    scene.draw(screen)
    
    pygame.display.flip()

pygame.quit()
sys.exit()
