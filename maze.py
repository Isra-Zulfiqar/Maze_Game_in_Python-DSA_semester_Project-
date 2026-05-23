import pygame
import random
import math
import heapq
from collections import deque
from enum import Enum
import sys
import time
import os

# Initialize pygame with proper settings
pygame.init()

# Set up the window with proper flags for minimize/maximize
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT), 
    pygame.RESIZABLE | pygame.DOUBLEBUF
)
pygame.display.set_caption("Neon Maze: Pathfinder's Journey")

# Try to load a custom cursor
try:
    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
except:
    pass  # Use default if custom cursor fails

# Color scheme with modern neon aesthetics
class Colors:
    BACKGROUND = (10, 10, 20)
    WALL = (40, 40, 80)  # Darker walls for better contrast
    WALL_HIGHLIGHT = (80, 80, 140)  # Lighter wall highlight
    PATH = (20, 20, 35)
    PLAYER = (0, 200, 255)
    PLAYER_GLOW = (100, 230, 255)
    ENEMY = (255, 50, 100)
    ENEMY_GLOW = (255, 120, 150)
    EXIT = (50, 255, 100)
    EXIT_GLOW = (150, 255, 180)
    COIN = (255, 215, 0)
    COIN_GLOW = (255, 240, 150)
    TEXT = (240, 240, 255)
    TEXT_HIGHLIGHT = (255, 255, 255)
    UI_BG = (20, 20, 30, 200)
    UI_BORDER = (60, 120, 200)
    BUTTON = (40, 100, 180)
    BUTTON_HOVER = (60, 140, 220)
    BUTTON_ACTIVE = (80, 160, 240)
    VISITED = (40, 40, 70, 100)
    CURRENT_PATH = (100, 150, 255, 150)
    CURSOR = (255, 255, 255)
    CURSOR_OUTER = (100, 200, 255, 100)

# Game constants
CELL_SIZE = 40
MAZE_WIDTH = 25
MAZE_HEIGHT = 17
FPS = 60

# Direction vectors
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# Font manager with fallback fonts
class FontManager:
    def __init__(self):
        self.fonts = {}
        try:
            # Try to load system fonts
            self.fonts['title'] = pygame.font.Font(None, 72)
            self.fonts['subtitle'] = pygame.font.Font(None, 36)
            self.fonts['large'] = pygame.font.Font(None, 48)
            self.fonts['medium'] = pygame.font.Font(None, 32)
            self.fonts['small'] = pygame.font.Font(None, 24)
            self.fonts['tiny'] = pygame.font.Font(None, 18)
        except:
            # Fallback to default font
            default_font = pygame.font.get_default_font()
            self.fonts['title'] = pygame.font.Font(default_font, 72)
            self.fonts['subtitle'] = pygame.font.Font(default_font, 36)
            self.fonts['large'] = pygame.font.Font(default_font, 48)
            self.fonts['medium'] = pygame.font.Font(default_font, 32)
            self.fonts['small'] = pygame.font.Font(default_font, 24)
            self.fonts['tiny'] = pygame.font.Font(default_font, 18)
    
    def get(self, size):
        return self.fonts.get(size, self.fonts['medium'])

fonts = FontManager()

# Particle class for visual effects
class Particle:
    def __init__(self, x, y, color, velocity_x=0, velocity_y=0, size=3, lifetime=30):
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.initial_size = size
        
    def update(self):
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_x *= 0.98
        self.velocity_y *= 0.98
        self.lifetime -= 1
        self.size = max(1, self.initial_size * (self.lifetime / self.max_lifetime))
        return self.lifetime > 0
        
    def draw(self, surface):
        if self.lifetime <= 0:
            return
            
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color_with_alpha = (*self.color, alpha)
        
        # Create a temporary surface for alpha blending
        particle_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color_with_alpha, 
                          (int(self.size), int(self.size)), int(self.size))
        surface.blit(particle_surface, (int(self.x - self.size), int(self.y - self.size)))

# Improved Button class for UI with better error handling
class Button:
    def __init__(self, x, y, width, height, text, action=None, font_size='medium'):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.clicked = False
        self.active = False
        self.font = fonts.get(font_size)
        self.animation_progress = 0
        self.click_animation = 0
        
    def update(self):
        # Smooth hover animation
        if self.hovered:
            self.animation_progress = min(self.animation_progress + 0.2, 1)
        else:
            self.animation_progress = max(self.animation_progress - 0.1, 0)
        
        # Click animation
        if self.click_animation > 0:
            self.click_animation = max(self.click_animation - 0.3, 0)
    
    def draw(self, surface):
        try:
            # Calculate animated values
            anim = self.animation_progress
            click_anim = self.click_animation
            
            # Button color based on state
            if self.click_animation > 0:
                base_color = Colors.BUTTON_ACTIVE
            elif self.hovered:
                base_color = Colors.BUTTON_HOVER
            else:
                base_color = Colors.BUTTON
            
            # Animated size and position
            width_offset = int(20 * anim)
            height_offset = int(10 * anim)
            click_offset = int(5 * click_anim)
            
            draw_rect = self.rect.inflate(width_offset, height_offset)
            draw_rect.y -= click_offset
            
            # Draw button with animated gradient effect
            gradient_surface = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            
            # Button background with rounded corners
            pygame.draw.rect(gradient_surface, base_color, gradient_surface.get_rect(), border_radius=12)
            
            # Animated border with glow effect
            border_width = 2 + int(2 * anim)
            border_color = (
                int(Colors.UI_BORDER[0] * (1 - anim) + Colors.BUTTON_HOVER[0] * anim),
                int(Colors.UI_BORDER[1] * (1 - anim) + Colors.BUTTON_HOVER[1] * anim),
                int(Colors.UI_BORDER[2] * (1 - anim) + Colors.BUTTON_HOVER[2] * anim)
            )
            pygame.draw.rect(gradient_surface, border_color, gradient_surface.get_rect(), border_width, border_radius=12)
            
            # Draw glow effect when hovered
            if anim > 0:
                glow_surface = pygame.Surface((draw_rect.width + 20, draw_rect.height + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*Colors.UI_BORDER, int(50 * anim)), 
                               glow_surface.get_rect(), border_radius=15)
                surface.blit(glow_surface, (draw_rect.x - 10, draw_rect.y - 10))
            
            surface.blit(gradient_surface, draw_rect)
            
            # Draw text with animation
            text_color = Colors.TEXT_HIGHLIGHT if self.hovered else Colors.TEXT
            text_surf = self.font.render(self.text, True, text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            text_rect.y -= click_offset
            surface.blit(text_surf, text_rect)
            
            # Draw click effect
            if click_anim > 0:
                click_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                pygame.draw.rect(click_surface, (*Colors.TEXT_HIGHLIGHT, int(100 * click_anim)), 
                               click_surface.get_rect(), border_radius=12)
                surface.blit(click_surface, self.rect)
        except Exception as e:
            print(f"Button draw error: {e}")
            
    def handle_event(self, event, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.clicked = True
                self.click_animation = 1
                if self.action:
                    try:
                        return self.action()
                    except Exception as e:
                        print(f"Button action error: {e}")
                        return None
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.clicked = False
        
        return None

# Maze generation using Recursive Backtracking (Stack-based) with traditional maze appearance
class Maze:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Create a grid with all walls initially
        self.grid = [[{'walls': [True, True, True, True], 'visited': False} 
                 for _ in range(width)] for _ in range(height)]
        self.generate_maze()  # This now handles wall generation safely
        self.coins = []
        self.generate_coins()
        self.enemies = []
        self.generate_enemies()
        self.exit_pos = (width - 1, height - 1)
        
    # In the Maze class, modify the generate_maze method to ensure a clear path
    def generate_maze(self):
    # Start from a random cell
        start_x, start_y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
        stack = [(start_x, start_y)]
        self.grid[start_y][start_x]['visited'] = True
    
    # First ensure a clear path from start (0,0) to exit (width-1, height-1)
    # Create a direct or mostly direct path as a backbone
        self.create_clear_path()
    
        while stack:
            x, y = stack[-1]
        
            # Get unvisited neighbors
            neighbors = []
            for direction in Direction:
                dx, dy = direction.value
                nx, ny = x + dx, y + dy
            
                if 0 <= nx < self.width and 0 <= ny < self.height and not self.grid[ny][nx]['visited']:
                    neighbors.append((nx, ny, direction))
        
            if neighbors:
            # Choose random neighbor
                nx, ny, direction = random.choice(neighbors)
            
            # Remove walls between current cell and chosen neighbor
                if direction == Direction.UP:
                    self.grid[y][x]['walls'][0] = False  # Remove top wall of current
                    self.grid[ny][nx]['walls'][2] = False  # Remove bottom wall of neighbor
                elif direction == Direction.RIGHT:
                    self.grid[y][x]['walls'][1] = False  # Remove right wall of current
                    self.grid[ny][nx]['walls'][3] = False  # Remove left wall of neighbor
                elif direction == Direction.DOWN:
                    self.grid[y][x]['walls'][2] = False  # Remove bottom wall of current
                    self.grid[ny][nx]['walls'][0] = False  # Remove top wall of neighbor
                elif direction == Direction.LEFT:
                    self.grid[y][x]['walls'][3] = False  # Remove left wall of current
                    self.grid[ny][nx]['walls'][1] = False  # Remove right wall of neighbor
            
                self.grid[ny][nx]['visited'] = True
                stack.append((nx, ny))
            else:
            # Backtrack
                stack.pop()
            
    # Add some additional walls to create more dead ends and make it look more like a traditional maze
    # But ensure we don't block the clear path
        self.add_additional_walls_safely()

    def create_clear_path(self):
        """Create at least one clear path from start to exit"""
        # Clear the path from (0,0) to exit
        current_x, current_y = 0, 0
    
    # Move right and down in a mostly direct path
        while current_x < self.width - 1 or current_y < self.height - 1:
        # Decide whether to move right or down (prefer moving toward exit)
            move_right = current_x < self.width - 1
            move_down = current_y < self.height - 1
        
        # Randomize path slightly but ensure progress toward exit
            if move_right and move_down:
                if random.random() < 0.6:  # 60% chance to move toward exit
                    if current_x < current_y:  # If we're behind in X, prioritize X
                        next_x, next_y = current_x + 1, current_y
                    else:
                        next_x, next_y = current_x, current_y + 1
                else:
                    # Random choice
                    if random.random() < 0.5:
                        next_x, next_y = current_x + 1, current_y
                    else:
                        next_x, next_y = current_x, current_y + 1
            elif move_right:
                next_x, next_y = current_x + 1, current_y
            else:  # move_down
                next_x, next_y = current_x, current_y + 1
        
        # Remove walls between current and next cell
            if next_x > current_x:  # Moving right
                self.grid[current_y][current_x]['walls'][1] = False
                self.grid[next_y][next_x]['walls'][3] = False
            elif next_x < current_x:  # Moving left
                self.grid[current_y][current_x]['walls'][3] = False
                self.grid[next_y][next_x]['walls'][1] = False
            elif next_y > current_y:  # Moving down
                self.grid[current_y][current_x]['walls'][2] = False
                self.grid[next_y][next_x]['walls'][0] = False
            elif next_y < current_y:  # Moving up
                self.grid[current_y][current_x]['walls'][0] = False
                self.grid[next_y][next_x]['walls'][2] = False
        
        # Mark both cells as visited
            self.grid[current_y][current_x]['visited'] = True
            self.grid[next_y][next_x]['visited'] = True
        
        # Move to next cell
            current_x, current_y = next_x, next_y
    
    # Also create one or two alternative clear paths
        self.create_alternative_paths()

    def create_alternative_paths(self):
        """Create 1-2 alternative clear paths for variety"""
        num_alternative_paths = random.randint(1, 2)
    
        for _ in range(num_alternative_paths):
        # Choose a different starting point for alternative path
            if random.random() < 0.5:
            # Horizontal path variant
                start_y = random.randint(0, self.height - 1)
                for x in range(self.width - 1):
                # Remove right wall
                    self.grid[start_y][x]['walls'][1] = False
                    self.grid[start_y][x + 1]['walls'][3] = False
                    self.grid[start_y][x]['visited'] = True
                    self.grid[start_y][x + 1]['visited'] = True
                
                # Occasionally move up/down
                    if random.random() < 0.2 and start_y > 0:
                        self.grid[start_y][x]['walls'][0] = False
                        self.grid[start_y - 1][x]['walls'][2] = False
                        self.grid[start_y - 1][x]['visited'] = True
                        start_y -= 1
                    elif random.random() < 0.2 and start_y < self.height - 1:
                        self.grid[start_y][x]['walls'][2] = False
                        self.grid[start_y + 1][x]['walls'][0] = False
                        self.grid[start_y + 1][x]['visited'] = True
                        start_y += 1
            else:
            # Vertical path variant
                start_x = random.randint(0, self.width - 1)
                for y in range(self.height - 1):
                # Remove bottom wall
                    self.grid[y][start_x]['walls'][2] = False
                    self.grid[y + 1][start_x]['walls'][0] = False
                    self.grid[y][start_x]['visited'] = True
                    self.grid[y + 1][start_x]['visited'] = True
                
                # Occasionally move left/right
                    if random.random() < 0.2 and start_x > 0:
                        self.grid[y][start_x]['walls'][3] = False
                        self.grid[y][start_x - 1]['walls'][1] = False
                        self.grid[y][start_x - 1]['visited'] = True
                        start_x -= 1
                    elif random.random() < 0.2 and start_x < self.width - 1:
                        self.grid[y][start_x]['walls'][1] = False
                        self.grid[y][start_x + 1]['walls'][3] = False
                        self.grid[y][start_x + 1]['visited'] = True
                        start_x += 1

    def add_additional_walls_safely(self):
        """Add additional walls but ensure connectivity is maintained"""
    # First, get all cells that are part of the main path
        path_cells = set()
    
    # Simple BFS to find all reachable cells from start
        queue = deque([(0, 0)])
        visited = set([(0, 0)])
    
        while queue:
            x, y = queue.popleft()
            path_cells.add((x, y))
        
        # Check all four directions
            for dx, dy, wall_idx, opposite_wall in [(0, -1, 0, 2), (1, 0, 1, 3), 
                                                (0, 1, 2, 0), (-1, 0, 3, 1)]:
                nx, ny = x + dx, y + dy
            
                if 0 <= nx < self.width and 0 <= ny < self.height:
                # Check if there's no wall in this direction
                    if not self.grid[y][x]['walls'][wall_idx]:
                        if (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
    
    # Now add walls only if they don't disconnect the exit from start
        for _ in range(self.width * self.height // 6):  # Fewer walls than before
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
        
        # Don't add walls to critical path cells
            if (x, y) in path_cells and (x, y) != (self.width - 1, self.height - 1):
                continue
        
        # Randomly add a wall in one direction
            direction = random.choice([0, 1, 2, 3])
        
        # Check if adding this wall would block the exit
            if self.would_block_exit(x, y, direction):
                continue
            
            self.grid[y][x]['walls'][direction] = True
        
        # Also add the corresponding wall to the neighboring cell
            if direction == 0 and y > 0:  # Top wall
                self.grid[y-1][x]['walls'][2] = True
            elif direction == 1 and x < self.width - 1:  # Right wall
                self.grid[y][x+1]['walls'][3] = True
            elif direction == 2 and y < self.height - 1:  # Bottom wall
                self.grid[y+1][x]['walls'][0] = True
            elif direction == 3 and x > 0:  # Left wall
                self.grid[y][x-1]['walls'][1] = True

    def would_block_exit(self, x, y, direction):    
        """Check if adding a wall would block the path from start to exit"""
    # Temporarily add the wall
        original_wall = self.grid[y][x]['walls'][direction]
        self.grid[y][x]['walls'][direction] = True
    
    # Check if there's still a path from start to exit
        has_path = self.has_path_to_exit()
    
    # Restore original wall
        self.grid[y][x]['walls'][direction] = original_wall
    
        return not has_path

    def has_path_to_exit(self):
        """Check if there's a path from start to exit using BFS"""
        start = (0, 0)
        exit_pos = (self.width - 1, self.height - 1)
    
        queue = deque([start])
        visited = set([start])
    
        while queue:
            x, y = queue.popleft()
        
            if (x, y) == exit_pos:
                return True
        
        # Check all four directions
            for dx, dy, wall_idx in [(0, -1, 0), (1, 0, 1), (0, 1, 2), (-1, 0, 3)]:
                nx, ny = x + dx, y + dy
            
                if 0 <= nx < self.width and 0 <= ny < self.height:
                # Check if there's no wall in this direction
                    if not self.grid[y][x]['walls'][wall_idx]:
                        if (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
    
            return False
    
    def generate_coins(self):
        # Generate coins at random positions (avoiding start and exit)
        coin_count = 15
        attempts = 0
        while len(self.coins) < coin_count and attempts < 100:
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            if (x, y) != (0, 0) and (x, y) != (self.width - 1, self.height - 1) and (x, y) not in self.coins:
                # Make sure coin is placed in a path cell (not completely walled)
                walls = self.grid[y][x]['walls']
                if not (walls[0] and walls[1] and walls[2] and walls[3]):  # Not a completely walled cell
                    self.coins.append((x, y))
            attempts += 1
    
    def generate_enemies(self):
        # Generate enemies at random positions (avoiding start, exit and coins)
        enemy_count = 3
        attempts = 0
        while len(self.enemies) < enemy_count and attempts < 100:
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            if (x, y) != (0, 0) and (x, y) != (self.width - 1, self.height - 1) and (x, y) not in self.coins:
                # Make sure enemy is placed in a path cell (not completely walled)
                walls = self.grid[y][x]['walls']
                if not (walls[0] and walls[1] and walls[2] and walls[3]):  # Not a completely walled cell
                    self.enemies.append({
                        'pos': (x, y),
                        'speed': random.uniform(0.5, 1.5),
                        'last_move': 0,
                        'direction': random.choice([d for d in Direction])
                    })
            attempts += 1
    
    def draw(self, surface, offset_x, offset_y, player_pos=None, show_pathfinding=False):
        # Draw maze background
        maze_surface = pygame.Surface((self.width * CELL_SIZE, self.height * CELL_SIZE))
        maze_surface.fill(Colors.BACKGROUND)
        
        # Draw paths first (light areas between walls)
        for y in range(self.height):
            for x in range(self.width):
                cell_x = x * CELL_SIZE
                cell_y = y * CELL_SIZE
                
                # Draw cell background - paths are lighter areas
                cell_rect = pygame.Rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(maze_surface, Colors.PATH, cell_rect)
                
                # Draw walls with thicker lines for better visibility
                walls = self.grid[y][x]['walls']
                
                # Draw thicker walls for traditional maze look
                wall_thickness = 6
                
                if walls[0]:  # Top wall
                    pygame.draw.line(maze_surface, Colors.WALL, 
                                    (cell_x, cell_y), 
                                    (cell_x + CELL_SIZE, cell_y), 
                                    wall_thickness)
                if walls[1]:  # Right wall
                    pygame.draw.line(maze_surface, Colors.WALL, 
                                    (cell_x + CELL_SIZE, cell_y), 
                                    (cell_x + CELL_SIZE, cell_y + CELL_SIZE), 
                                    wall_thickness)
                if walls[2]:  # Bottom wall
                    pygame.draw.line(maze_surface, Colors.WALL, 
                                    (cell_x, cell_y + CELL_SIZE), 
                                    (cell_x + CELL_SIZE, cell_y + CELL_SIZE), 
                                    wall_thickness)
                if walls[3]:  # Left wall
                    pygame.draw.line(maze_surface, Colors.WALL, 
                                    (cell_x, cell_y), 
                                    (cell_x, cell_y + CELL_SIZE), 
                                    wall_thickness)
                
                # Add wall highlights for 3D effect
                highlight_thickness = 2
                if walls[0]:  # Top wall highlight
                    pygame.draw.line(maze_surface, Colors.WALL_HIGHLIGHT, 
                                    (cell_x, cell_y), 
                                    (cell_x + CELL_SIZE, cell_y), 
                                    highlight_thickness)
                if walls[1]:  # Right wall highlight
                    pygame.draw.line(maze_surface, Colors.WALL_HIGHLIGHT, 
                                    (cell_x + CELL_SIZE, cell_y), 
                                    (cell_x + CELL_SIZE, cell_y + CELL_SIZE), 
                                    highlight_thickness)
                if walls[3]:  # Left wall highlight
                    pygame.draw.line(maze_surface, Colors.WALL_HIGHLIGHT, 
                                    (cell_x, cell_y), 
                                    (cell_x, cell_y + CELL_SIZE), 
                                    highlight_thickness)
        
        # Draw maze surface to main screen
        surface.blit(maze_surface, (offset_x, offset_y))
        
        # Draw coins
        for coin in self.coins:
            coin_x = offset_x + coin[0] * CELL_SIZE + CELL_SIZE // 2
            coin_y = offset_y + coin[1] * CELL_SIZE + CELL_SIZE // 2
            
            # Draw coin with pulsing glow effect
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005 + coin[0] * 0.1)) * 3
            for i in range(3, 0, -1):
                radius = 8 + i + pulse
                alpha = 100 - i * 30
                glow_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*Colors.COIN_GLOW, alpha), 
                                  (int(radius), int(radius)), int(radius))
                surface.blit(glow_surface, (coin_x - radius, coin_y - radius))
            
            pygame.draw.circle(surface, Colors.COIN, (int(coin_x), int(coin_y)), 8)
            pygame.draw.circle(surface, Colors.COIN_GLOW, (int(coin_x), int(coin_y)), 5)
        
        # Draw exit
        exit_x = offset_x + self.exit_pos[0] * CELL_SIZE + CELL_SIZE // 2
        exit_y = offset_y + self.exit_pos[1] * CELL_SIZE + CELL_SIZE // 2
        
        # Draw exit with pulsing effect
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 5
        for i in range(3, 0, -1):
            radius = 12 + i + pulse
            alpha = 100 - i * 30
            glow_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*Colors.EXIT_GLOW, alpha), 
                              (int(radius), int(radius)), int(radius))
            surface.blit(glow_surface, (exit_x - radius, exit_y - radius))
        
        pygame.draw.circle(surface, Colors.EXIT, (int(exit_x), int(exit_y)), 12)
        pygame.draw.circle(surface, Colors.EXIT_GLOW, (int(exit_x), int(exit_y)), 8)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy_x = offset_x + enemy['pos'][0] * CELL_SIZE + CELL_SIZE // 2
            enemy_y = offset_y + enemy['pos'][1] * CELL_SIZE + CELL_SIZE // 2
            
            # Draw enemy with breathing glow effect
            breath = abs(math.sin(pygame.time.get_ticks() * 0.003)) * 2
            for i in range(4, 0, -1):
                radius = 10 + i + breath
                alpha = 100 - i * 20
                glow_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*Colors.ENEMY_GLOW, alpha), 
                                  (int(radius), int(radius)), int(radius))
                surface.blit(glow_surface, (enemy_x - radius, enemy_y - radius))
            
            pygame.draw.circle(surface, Colors.ENEMY, (int(enemy_x), int(enemy_y)), 10)
            
            # Draw enemy eyes
            pygame.draw.circle(surface, (255, 255, 255), (int(enemy_x - 3), int(enemy_y - 3)), 3)
            pygame.draw.circle(surface, (255, 255, 255), (int(enemy_x + 3), int(enemy_y - 3)), 3)
            pygame.draw.circle(surface, (0, 0, 0), (int(enemy_x - 3), int(enemy_y - 3)), 1)
            pygame.draw.circle(surface, (0, 0, 0), (int(enemy_x + 3), int(enemy_y - 3)), 1)
        
        # Draw pathfinding visualization if enabled
        if show_pathfinding and player_pos:
            self.draw_pathfinding(surface, offset_x, offset_y, player_pos)
    
    def draw_pathfinding(self, surface, offset_x, offset_y, player_pos):
        # Demonstrate different pathfinding algorithms
        if self.coins:
            # BFS to find nearest coin
            target_coin = min(self.coins, key=lambda c: abs(c[0] - player_pos[0]) + abs(c[1] - player_pos[1]))
            bfs_path = self.bfs(player_pos, target_coin)
            self.draw_path(surface, offset_x, offset_y, bfs_path, (100, 255, 100, 100), "BFS")
        
        # Dijkstra's algorithm to find exit
        dijkstra_path = self.dijkstra(player_pos, self.exit_pos)
        self.draw_path(surface, offset_x, offset_y, dijkstra_path, (255, 100, 100, 100), "Dijkstra")
        
        # A* algorithm to find exit
        astar_path = self.astar(player_pos, self.exit_pos)
        self.draw_path(surface, offset_x, offset_y, astar_path, (100, 100, 255, 100), "A*")
    
    def draw_path(self, surface, offset_x, offset_y, path, color, label=None):
        if len(path) < 2:
            return
            
        # Draw the path lines
        for i in range(len(path) - 1):
            start_x = offset_x + path[i][0] * CELL_SIZE + CELL_SIZE // 2
            start_y = offset_y + path[i][1] * CELL_SIZE + CELL_SIZE // 2
            end_x = offset_x + path[i+1][0] * CELL_SIZE + CELL_SIZE // 2
            end_y = offset_y + path[i+1][1] * CELL_SIZE + CELL_SIZE // 2
            
            # Draw path line with glow
            for j in range(3, 0, -1):
                line_width = 4 + j
                line_alpha = 50 - j * 15
                temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(temp_surface, (*color[:3], line_alpha), 
                               (start_x, start_y), (end_x, end_y), line_width)
                surface.blit(temp_surface, (0, 0))
            
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), 4)
            
            # Draw path nodes
            pygame.draw.circle(surface, color, (int(start_x), int(start_y)), 5)
            
            # Draw the last node
            if i == len(path) - 2:
                pygame.draw.circle(surface, color, (int(end_x), int(end_y)), 5)
        
        # Draw algorithm label
        if label and len(path) > 1:
            label_x = offset_x + path[-1][0] * CELL_SIZE + CELL_SIZE // 2
            label_y = offset_y + path[-1][1] * CELL_SIZE - 20
            label_surf = fonts.get('tiny').render(label, True, color[:3])
            surface.blit(label_surf, (label_x - label_surf.get_width() // 2, label_y))
    
    # BFS algorithm for pathfinding
    def bfs(self, start, target):
        queue = deque([(start, [start])])
        visited = set([start])
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == target:
                return path
            
            # Check all four directions
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Check if the move is valid (within bounds and no wall)
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    # Check wall between current cell and neighbor
                    can_move = False
                    if dx == -1 and not self.grid[y][x]['walls'][3]:  # Left
                        can_move = True
                    elif dx == 1 and not self.grid[y][x]['walls'][1]:  # Right
                        can_move = True
                    elif dy == -1 and not self.grid[y][x]['walls'][0]:  # Up
                        can_move = True
                    elif dy == 1 and not self.grid[y][x]['walls'][2]:  # Down
                        can_move = True
                    
                    if can_move and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [(nx, ny)]))
        
        return []
    
    # Dijkstra's algorithm for pathfinding
    def dijkstra(self, start, target):
        distances = {start: 0}
        previous = {start: None}
        pq = [(0, start)]
        
        while pq:
            current_dist, (x, y) = heapq.heappop(pq)
            
            if (x, y) == target:
                # Reconstruct path
                path = []
                current = target
                while current is not None:
                    path.append(current)
                    current = previous[current]
                return path[::-1]
            
            # Check all four directions
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Check if the move is valid
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    # Check wall between current cell and neighbor
                    can_move = False
                    if dx == -1 and not self.grid[y][x]['walls'][3]:  # Left
                        can_move = True
                    elif dx == 1 and not self.grid[y][x]['walls'][1]:  # Right
                        can_move = True
                    elif dy == -1 and not self.grid[y][x]['walls'][0]:  # Up
                        can_move = True
                    elif dy == 1 and not self.grid[y][x]['walls'][2]:  # Down
                        can_move = True
                    
                    if can_move:
                        new_dist = current_dist + 1  # Uniform cost
                        if (nx, ny) not in distances or new_dist < distances[(nx, ny)]:
                            distances[(nx, ny)] = new_dist
                            previous[(nx, ny)] = (x, y)
                            heapq.heappush(pq, (new_dist, (nx, ny)))
        
        return []
    
    # A* algorithm for pathfinding
    def astar(self, start, target):
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Manhattan distance
        
        open_set = [(0, start)]
        came_from = {start: None}
        g_score = {start: 0}
        f_score = {start: heuristic(start, target)}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == target:
                # Reconstruct path
                path = []
                while current is not None:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]
            
            x, y = current
            
            # Check all four directions
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Check if the move is valid
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    # Check wall between current cell and neighbor
                    can_move = False
                    if dx == -1 and not self.grid[y][x]['walls'][3]:  # Left
                        can_move = True
                    elif dx == 1 and not self.grid[y][x]['walls'][1]:  # Right
                        can_move = True
                    elif dy == -1 and not self.grid[y][x]['walls'][0]:  # Up
                        can_move = True
                    elif dy == 1 and not self.grid[y][x]['walls'][2]:  # Down
                        can_move = True
                    
                    if can_move:
                        neighbor = (nx, ny)
                        tentative_g_score = g_score[current] + 1
                        
                        if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g_score
                            f_score[neighbor] = tentative_g_score + heuristic(neighbor, target)
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []

# Player class with improved movement
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.moving = False
        self.speed = 0.4  # Increased speed for better responsiveness
        self.score = 0
        self.moves = 0
        self.particles = []
        self.trail = []
        self.max_trail_length = 20
        self.last_move_time = 0
        self.move_delay = 100  # milliseconds between moves
        self.queued_move = None
        
    def move(self, dx, dy, maze):
        current_time = pygame.time.get_ticks()
        
        # If already moving, queue the next move
        if self.moving:
            self.queued_move = (dx, dy)
            return False
            
        # Check if enough time has passed since last move
        if current_time - self.last_move_time < self.move_delay:
            return False
            
        new_x, new_y = self.x + dx, self.y + dy
        
        # Check if move is within bounds
        if 0 <= new_x < maze.width and 0 <= new_y < maze.height:
            # Check if there's a wall in the way
            can_move = False
            if dx == -1 and not maze.grid[self.y][self.x]['walls'][3]:  # Left
                can_move = True
            elif dx == 1 and not maze.grid[self.y][self.x]['walls'][1]:  # Right
                can_move = True
            elif dy == -1 and not maze.grid[self.y][self.x]['walls'][0]:  # Up
                can_move = True
            elif dy == 1 and not maze.grid[self.y][self.x]['walls'][2]:  # Down
                can_move = True
            
            if can_move:
                self.target_x = new_x
                self.target_y = new_y
                self.moving = True
                self.moves += 1
                self.last_move_time = current_time
                
                # Add trail position
                self.trail.append((self.x * CELL_SIZE + CELL_SIZE // 2, 
                                  self.y * CELL_SIZE + CELL_SIZE // 2))
                if len(self.trail) > self.max_trail_length:
                    self.trail.pop(0)
                
                return True
        
        return False
    
    def update(self):
        # Update position if moving
        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            
            if abs(dx) > 0:
                self.x += dx * self.speed
                if abs(self.x - self.target_x) < 0.1:
                    self.x = self.target_x
            elif abs(dy) > 0:
                self.y += dy * self.speed
                if abs(self.y - self.target_y) < 0.1:
                    self.y = self.target_y
            
            # Check if reached target
            if self.x == self.target_x and self.y == self.target_y:
                self.moving = False
                
                # Check for queued move
                if self.queued_move:
                    # This will be processed in the next frame
                    pass
                
                # Create arrival particles
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(0.5, 2)
                    self.particles.append(Particle(
                        self.x * CELL_SIZE + CELL_SIZE // 2,
                        self.y * CELL_SIZE + CELL_SIZE // 2,
                        Colors.PLAYER_GLOW,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        random.uniform(2, 4),
                        random.randint(20, 40)
                    ))
        
        # Update particles
        self.particles = [p for p in self.particles if p.update()]
        
        # Add idle particles occasionally
        if random.random() < 0.1 and not self.moving:
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(5, 15)
            self.particles.append(Particle(
                self.x * CELL_SIZE + CELL_SIZE // 2 + math.cos(angle) * radius,
                self.y * CELL_SIZE + CELL_SIZE // 2 + math.sin(angle) * radius,
                Colors.PLAYER_GLOW,
                0, 0,
                random.uniform(1, 2),
                random.randint(30, 60)
            ))
    
    def draw(self, surface, offset_x, offset_y):
        # Draw player trail
        for i, (trail_x, trail_y) in enumerate(self.trail):
            alpha = int(100 * (i / len(self.trail)))
            trail_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (*Colors.PLAYER, alpha), 
                              (CELL_SIZE // 2, CELL_SIZE // 2), 
                              int(CELL_SIZE // 4 * (i / len(self.trail))))
            surface.blit(trail_surface, (trail_x - CELL_SIZE // 2 + offset_x, 
                                        trail_y - CELL_SIZE // 2 + offset_y))
        
        # Draw particles
        for particle in self.particles:
            particle.draw(surface)
        
        # Calculate screen position
        screen_x = offset_x + self.x * CELL_SIZE + CELL_SIZE // 2
        screen_y = offset_y + self.y * CELL_SIZE + CELL_SIZE // 2
        
        # Draw player with glow effect
        for i in range(5, 0, -1):
            radius = 12 + i
            alpha = 100 - i * 15
            glow_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*Colors.PLAYER_GLOW, alpha), 
                              (int(radius), int(radius)), int(radius))
            surface.blit(glow_surface, (screen_x - radius, screen_y - radius))
        
        # Draw player
        pygame.draw.circle(surface, Colors.PLAYER, (int(screen_x), int(screen_y)), 12)
        
        # Draw player inner glow
        pygame.draw.circle(surface, Colors.PLAYER_GLOW, (int(screen_x), int(screen_y)), 8)
        
        # Draw player direction indicator if moving
        if self.moving:
            direction_x = self.target_x - self.x
            direction_y = self.target_y - self.y
            
            if direction_x != 0 or direction_y != 0:
                # Normalize direction
                length = max(0.1, math.sqrt(direction_x**2 + direction_y**2))
                dir_x = direction_x / length
                dir_y = direction_y / length
                
                # Draw direction indicator
                indicator_x = screen_x + dir_x * 20
                indicator_y = screen_y + dir_y * 20
                pygame.draw.circle(surface, Colors.PLAYER_GLOW, 
                                  (int(indicator_x), int(indicator_y)), 6)

# Main Game class with proper state management
class Game:
    def __init__(self):
        self.maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
        self.player = Player(0, 0)
        self.level = 1
        self.game_state = "menu"  # menu, playing, paused, game_over, win
        self.particles = []
        self.show_pathfinding = False
        self.clock = pygame.time.Clock()
        self.start_time = time.time()
        self.elapsed_time = 0
        self.mouse_pos = (0, 0)
        self.showing_instructions = False
        
        # Create UI buttons with proper layout
        button_width = 250
        button_height = 60
        center_x = SCREEN_WIDTH // 2 - button_width // 2
        
        # Main menu buttons
        self.menu_buttons = [
            Button(center_x, 400, button_width, button_height, "Start Game", self.start_game, 'large'),
            Button(center_x, 480, button_width, button_height, "Toggle Pathfinding", self.toggle_pathfinding, 'medium'),
            Button(center_x, 560, button_width, button_height, "Instructions", self.show_instructions, 'medium'),
            Button(center_x, 640, button_width, button_height, "Quit", self.quit_game, 'medium')
        ]
        
        # Pause menu buttons
        self.pause_buttons = [
            Button(center_x, 350, button_width, button_height, "Resume", self.resume_game, 'large'),
            Button(center_x, 430, button_width, button_height, "Restart Level", self.restart_level, 'medium'),
            Button(center_x, 510, button_width, button_height, "Main Menu", self.go_to_menu, 'medium')
        ]
        
        # Game over buttons
        self.game_over_buttons = [
            Button(center_x, 450, button_width, button_height, "Restart", self.restart_level, 'large'),
            Button(center_x, 530, button_width, button_height, "Main Menu", self.go_to_menu, 'medium')
        ]
        
        # Win screen buttons
        self.win_buttons = [
            Button(center_x, 450, button_width, button_height, "Next Level", self.next_level, 'large'),
            Button(center_x, 530, button_width, button_height, "Main Menu", self.go_to_menu, 'medium')
        ]
        
        # Current active buttons
        self.active_buttons = self.menu_buttons
        
        # Track pressed keys for smooth movement
        self.keys_pressed = {
            pygame.K_UP: False,
            pygame.K_w: False,
            pygame.K_DOWN: False,
            pygame.K_s: False,
            pygame.K_LEFT: False,
            pygame.K_a: False,
            pygame.K_RIGHT: False,
            pygame.K_d: False
        }
    
    def start_game(self):
        try:
            self.game_state = "playing"
            self.start_time = time.time()
            self.active_buttons = []
            return True
        except Exception as e:
            print(f"Error in start_game: {e}")
            return False
    
    def resume_game(self):
        self.game_state = "playing"
        self.active_buttons = []
        return True
    
    def toggle_pathfinding(self):
        self.show_pathfinding = not self.show_pathfinding
        return True
    
    def show_instructions(self):
        self.showing_instructions = not self.showing_instructions
        return True
    
    def restart_level(self):
        self.maze = Maze(MAZE_WIDTH, MAZE_HEIGHT)
        self.player = Player(0, 0)
        self.start_time = time.time()
        self.game_state = "playing"
        self.active_buttons = []
        return True
    
    def go_to_menu(self):
        self.game_state = "menu"
        self.active_buttons = self.menu_buttons
        self.showing_instructions = False
        return True
    
    def next_level(self):
        self.level += 1
        self.restart_level()
        return True
    
    def quit_game(self):
        pygame.quit()
        sys.exit()
    
    def update(self):
        current_time = pygame.time.get_ticks()
        
        # Update elapsed time
        if self.game_state == "playing":
            self.elapsed_time = time.time() - self.start_time
        
        # Update player
        self.player.update()
        
        # Update buttons
        for button in self.active_buttons:
            button.update()
        
        # Update enemies
        for enemy in self.maze.enemies:
            # Move enemy occasionally
            if current_time - enemy['last_move'] > 1000 / enemy['speed']:
                # Simple enemy AI - try to continue in same direction
                dx, dy = enemy['direction'].value
                new_x, new_y = enemy['pos'][0] + dx, enemy['pos'][1] + dy
                
                # Check if move is valid
                can_move = False
                x, y = enemy['pos']
                if 0 <= new_x < self.maze.width and 0 <= new_y < self.maze.height:
                    # Check if there's a wall in the way
                    if dx == -1 and not self.maze.grid[y][x]['walls'][3]:  # Left
                        can_move = True
                    elif dx == 1 and not self.maze.grid[y][x]['walls'][1]:  # Right
                        can_move = True
                    elif dy == -1 and not self.maze.grid[y][x]['walls'][0]:  # Up
                        can_move = True
                    elif dy == 1 and not self.maze.grid[y][x]['walls'][2]:  # Down
                        can_move = True
                
                if can_move:
                    enemy['pos'] = (new_x, new_y)
                else:
                    # Choose new random direction
                    enemy['direction'] = random.choice([d for d in Direction])
                
                enemy['last_move'] = current_time
                
                # Create enemy move particles
                for _ in range(5):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(0.5, 1.5)
                    self.particles.append(Particle(
                        enemy['pos'][0] * CELL_SIZE + CELL_SIZE // 2,
                        enemy['pos'][1] * CELL_SIZE + CELL_SIZE // 2,
                        Colors.ENEMY_GLOW,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        random.uniform(1, 3),
                        random.randint(15, 30)
                    ))
        
        # Handle queued player movement
        if self.player.queued_move and not self.player.moving:
            dx, dy = self.player.queued_move
            self.player.move(dx, dy, self.maze)
            self.player.queued_move = None
        
        # Handle continuous key presses for smooth movement
        if self.game_state == "playing" and not self.player.moving:
            current_time = pygame.time.get_ticks()
            if current_time - self.player.last_move_time >= self.player.move_delay:
                if self.keys_pressed[pygame.K_UP] or self.keys_pressed[pygame.K_w]:
                    self.player.move(0, -1, self.maze)
                elif self.keys_pressed[pygame.K_DOWN] or self.keys_pressed[pygame.K_s]:
                    self.player.move(0, 1, self.maze)
                elif self.keys_pressed[pygame.K_LEFT] or self.keys_pressed[pygame.K_a]:
                    self.player.move(-1, 0, self.maze)
                elif self.keys_pressed[pygame.K_RIGHT] or self.keys_pressed[pygame.K_d]:
                    self.player.move(1, 0, self.maze)
        
        # Check collision with coins
        coin_to_remove = None
        for i, coin in enumerate(self.maze.coins):
            if (self.player.x, self.player.y) == coin:
                coin_to_remove = i
                self.player.score += 10
                
                # Create coin collection particles
                for _ in range(20):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(1, 3)
                    self.particles.append(Particle(
                        coin[0] * CELL_SIZE + CELL_SIZE // 2,
                        coin[1] * CELL_SIZE + CELL_SIZE // 2,
                        Colors.COIN_GLOW,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        random.uniform(2, 4),
                        random.randint(20, 40)
                    ))
        
        if coin_to_remove is not None:
            self.maze.coins.pop(coin_to_remove)
        
        # Check collision with enemies
        for enemy in self.maze.enemies:
            if (self.player.x, self.player.y) == enemy['pos']:
                self.game_state = "game_over"
                self.active_buttons = self.game_over_buttons
                
                # Create game over particles
                for _ in range(50):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(1, 5)
                    self.particles.append(Particle(
                        self.player.x * CELL_SIZE + CELL_SIZE // 2,
                        self.player.y * CELL_SIZE + CELL_SIZE // 2,
                        Colors.ENEMY_GLOW,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        random.uniform(2, 5),
                        random.randint(30, 60)
                    ))
        
        # Check if reached exit
        if (self.player.x, self.player.y) == self.maze.exit_pos:
            # Add bonus score based on time and moves
            time_bonus = max(0, 500 - int(self.elapsed_time * 10))
            move_bonus = max(0, 300 - self.player.moves * 5)
            self.player.score += time_bonus + move_bonus
            self.game_state = "win"
            self.active_buttons = self.win_buttons
            
            # Create win particles
            for _ in range(50):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1, 3)
                self.particles.append(Particle(
                    self.player.x * CELL_SIZE + CELL_SIZE // 2,
                    self.player.y * CELL_SIZE + CELL_SIZE // 2,
                    Colors.EXIT_GLOW,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.uniform(2, 4),
                    random.randint(40, 80)
                ))
        
        # Update particles
        self.particles = [p for p in self.particles if p.update()]
    
    def handle_events(self):
        # Get current mouse position
        self.mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Handle window resize
            elif event.type == pygame.VIDEORESIZE:
                global SCREEN_WIDTH, SCREEN_HEIGHT
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                # Recreate screen with new size
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            
            # Handle key presses for movement tracking
            elif event.type == pygame.KEYDOWN:
                if event.key in self.keys_pressed:
                    self.keys_pressed[event.key] = True
                
                # Handle game state changes
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing":
                        self.game_state = "paused"
                        self.active_buttons = self.pause_buttons
                    elif self.game_state == "paused":
                        self.resume_game()
                    elif self.game_state in ["game_over", "win"]:
                        self.go_to_menu()
                
                elif event.key == pygame.K_f:
                    self.toggle_pathfinding()
                
                elif event.key == pygame.K_r and self.game_state == "playing":
                    self.restart_level()
                
                elif event.key == pygame.K_i and self.game_state == "menu":
                    self.show_instructions()
                
                elif event.key == pygame.K_SPACE and self.game_state == "menu":
                    self.start_game()
                
                elif event.key == pygame.K_n and self.game_state == "win":
                    self.next_level()
            
            # Handle key releases
            elif event.type == pygame.KEYUP:
                if event.key in self.keys_pressed:
                    self.keys_pressed[event.key] = False
            
            # Handle mouse events for buttons
            for button in self.active_buttons:
                button.handle_event(event, self.mouse_pos)
    
    def draw(self, surface):
        try:
            # Calculate maze offset to center it on screen
            maze_width_px = self.maze.width * CELL_SIZE
            maze_height_px = self.maze.height * CELL_SIZE
            offset_x = (SCREEN_WIDTH - maze_width_px) // 2
            offset_y = (SCREEN_HEIGHT - maze_height_px) // 2 + 50
            
            # Draw background
            surface.fill(Colors.BACKGROUND)
            
            # Draw decorative background elements
            self.draw_background(surface)
            
            # Draw maze and player if in playing state
            if self.game_state in ["playing", "paused", "game_over", "win"]:
                self.maze.draw(surface, offset_x, offset_y, 
                              (self.player.x, self.player.y), 
                              self.show_pathfinding)
                self.player.draw(surface, offset_x, offset_y)
            
            # Draw UI overlay
            self.draw_ui(surface, offset_x, offset_y)
            
            # Draw particles
            for particle in self.particles:
                particle.draw(surface)
            
            # Draw game state specific screens
            if self.game_state == "menu":
                self.draw_menu(surface)
            elif self.game_state == "paused":
                self.draw_pause_menu(surface)
            elif self.game_state == "game_over":
                self.draw_game_over(surface)
            elif self.game_state == "win":
                self.draw_win_screen(surface)
            
            # Draw custom cursor
            self.draw_cursor(surface)
            
        except Exception as e:
            print(f"Error in draw: {e}")
    
    def draw_background(self, surface):
        # Draw a grid of faint dots in the background
        for x in range(0, SCREEN_WIDTH, 40):
            for y in range(0, SCREEN_HEIGHT, 40):
                alpha = random.randint(10, 30)
                radius = random.randint(1, 2)
                pygame.draw.circle(surface, (50, 70, 120, alpha), (x, y), radius)
        
        # Draw some floating particles in the background
        for i in range(5):
            x = (pygame.time.get_ticks() * 0.02 + i * 100) % SCREEN_WIDTH
            y = SCREEN_HEIGHT // 2 + math.sin(pygame.time.get_ticks() * 0.001 + i) * 100
            radius = 2 + math.sin(pygame.time.get_ticks() * 0.002 + i) * 1
            pygame.draw.circle(surface, (100, 150, 255, 50), (int(x), int(y)), int(radius))
    
    def draw_ui(self, surface, offset_x, offset_y):
        # Create a semi-transparent UI panel at the top
        ui_rect = pygame.Rect(20, 20, SCREEN_WIDTH - 40, 80)
        ui_surface = pygame.Surface((ui_rect.width, ui_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(ui_surface, Colors.UI_BG, ui_surface.get_rect(), border_radius=10)
        pygame.draw.rect(ui_surface, Colors.UI_BORDER, ui_surface.get_rect(), 2, border_radius=10)
        surface.blit(ui_surface, ui_rect)
        
        # Draw game info with better spacing
        info_x = 40
        info_spacing = 200
        
        # Score
        score_text = fonts.get('medium').render(f"Score: {self.player.score}", True, Colors.TEXT)
        surface.blit(score_text, (info_x, 40))
        
        # Level
        level_text = fonts.get('medium').render(f"Level: {self.level}", True, Colors.TEXT)
        surface.blit(level_text, (info_x, 70))
        
        # Time
        time_x = info_x + info_spacing
        time_text = fonts.get('medium').render(f"Time: {int(self.elapsed_time)}s", True, Colors.TEXT)
        surface.blit(time_text, (time_x, 40))
        
        # Moves
        moves_text = fonts.get('medium').render(f"Moves: {self.player.moves}", True, Colors.TEXT)
        surface.blit(moves_text, (time_x, 70))
        
        # Coins remaining
        coins_x = info_x + info_spacing * 2
        coins_text = fonts.get('medium').render(f"Coins: {len(self.maze.coins)}", True, Colors.TEXT)
        surface.blit(coins_text, (coins_x, 40))
        
        # Pathfinding indicator
        indicator_x = info_x + info_spacing * 3
        if self.show_pathfinding:
            path_text = fonts.get('medium').render("Pathfinding: ON", True, (100, 255, 100))
        else:
            path_text = fonts.get('medium').render("Pathfinding: OFF", True, (255, 100, 100))
        surface.blit(path_text, (indicator_x, 40))
        
        # Draw controls hint if in playing state
        if self.game_state == "playing":
            controls_y = SCREEN_HEIGHT - 40
            controls_text = fonts.get('small').render(
                "WASD/Arrows: Move | P/ESC: Pause | F: Toggle Pathfinding | R: Restart", 
                True, Colors.TEXT
            )
            surface.blit(controls_text, (SCREEN_WIDTH // 2 - controls_text.get_width() // 2, controls_y))
    
    def draw_menu(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Draw game title with enhanced effects
        title_y = 100
        title = fonts.get('title').render("NEON MAZE", True, Colors.PLAYER)
        subtitle = fonts.get('subtitle').render("Pathfinder's Journey", True, Colors.PLAYER_GLOW)
        
        # Draw title with multiple glow layers
        for i in range(5, 0, -1):
            glow_alpha = 80 - i * 15
            glow_title = fonts.get('title').render("NEON MAZE", True, (*Colors.PLAYER_GLOW, glow_alpha))
            offset = i * 2
            surface.blit(glow_title, (SCREEN_WIDTH // 2 - glow_title.get_width() // 2 + offset, 
                                      title_y + offset))
        
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, title_y))
        surface.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, title_y + 70))
        
        # Draw DSA concepts used in two columns
        concepts_left = [
            "Data Structures & Algorithms:",
            "- Recursive Backtracking",
            "- BFS Pathfinding",
            "- Dijkstra's Algorithm",
            "- A* Search Algorithm"
        ]
        
        concepts_right = [
            "Concepts Demonstrated:",
            "- Stack (Maze Generation)",
            "- Queue (BFS)",
            "- Priority Queue",
            "- Graph Traversal"
        ]
        
        left_x = SCREEN_WIDTH // 4 - 150
        right_x = 3 * SCREEN_WIDTH // 4 - 150
        
        for i, concept in enumerate(concepts_left):
            color = Colors.TEXT_HIGHLIGHT if i == 0 else Colors.TEXT
            font_size = 'small' if i == 0 else 'tiny'
            text = fonts.get(font_size).render(concept, True, color)
            surface.blit(text, (left_x, 220 + i * 30))
        
        for i, concept in enumerate(concepts_right):
            color = Colors.TEXT_HIGHLIGHT if i == 0 else Colors.TEXT
            font_size = 'small' if i == 0 else 'tiny'
            text = fonts.get(font_size).render(concept, True, color)
            surface.blit(text, (right_x, 220 + i * 30))
        
        # Draw buttons
        for button in self.active_buttons:
            button.draw(surface)
        
        # Draw instructions if toggled
        if self.showing_instructions:
            instructions_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            instructions_overlay.fill((0, 0, 0, 200))
            surface.blit(instructions_overlay, (0, 0))
            
            instructions = [
                "HOW TO PLAY:",
                "1. Use WASD or Arrow Keys to move through the maze",
                "2. Collect all gold coins to increase your score",
                "3. Avoid the red enemies that move randomly",
                "4. Reach the green exit portal to complete the level",
                "5. Toggle pathfinding to see different algorithms in action",
                "",
                "CONTROLS:",
                "WASD / Arrow Keys - Move",
                "P / ESC - Pause game",
                "F - Toggle pathfinding visualization",
                "R - Restart level",
                "ESC in menu - Quit game",
                "",
                "Press I again to close instructions"
            ]
            
            instructions_y = 150
            for i, line in enumerate(instructions):
                color = Colors.TEXT_HIGHLIGHT if i == 0 or i == 7 else Colors.TEXT
                font_size = 'medium' if i == 0 else 'small'
                text = fonts.get(font_size).render(line, True, color)
                surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, instructions_y + i * 30))
        else:
            # Draw game instructions below buttons
            instructions = [
                "Collect all coins and reach the exit to win.",
                "Avoid enemies that move randomly through the maze.",
                "Toggle pathfinding to visualize different algorithms."
            ]
            
            for i, line in enumerate(instructions):
                text = fonts.get('small').render(line, True, Colors.TEXT)
                surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 700 + i * 25))
    
    def draw_pause_menu(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 200))
        surface.blit(overlay, (0, 0))
        
        # Draw pause title
        title = fonts.get('title').render("GAME PAUSED", True, Colors.TEXT_HIGHLIGHT)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        
        # Draw pause message
        message = fonts.get('medium').render("Take a break! Ready to continue?", True, Colors.TEXT)
        surface.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, 280))
        
        # Draw buttons
        for button in self.active_buttons:
            button.draw(surface)
    
    def draw_game_over(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 0, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Draw game over title
        title = fonts.get('title').render("GAME OVER", True, Colors.ENEMY)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        
        # Draw game over message
        message = fonts.get('subtitle').render("An enemy caught you!", True, Colors.ENEMY_GLOW)
        surface.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, 280))
        
        # Draw stats
        stats_y = 350
        time_text = fonts.get('medium').render(f"Time Survived: {int(self.elapsed_time)} seconds", True, Colors.TEXT_HIGHLIGHT)
        moves_text = fonts.get('medium').render(f"Moves Made: {self.player.moves}", True, Colors.TEXT_HIGHLIGHT)
        score_text = fonts.get('medium').render(f"Final Score: {self.player.score}", True, Colors.TEXT_HIGHLIGHT)
        
        surface.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, stats_y))
        surface.blit(moves_text, (SCREEN_WIDTH // 2 - moves_text.get_width() // 2, stats_y + 40))
        surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, stats_y + 80))
        
        # Draw buttons
        for button in self.active_buttons:
            button.draw(surface)
    
    def draw_win_screen(self, surface):
        # Draw semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 30, 0, 200))
        surface.blit(overlay, (0, 0))
        
        # Draw win title
        title = fonts.get('title').render("LEVEL COMPLETE!", True, Colors.EXIT)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        
        # Draw congratulations message
        message = fonts.get('subtitle').render(f"Congratulations! You've completed Level {self.level}", True, Colors.EXIT_GLOW)
        surface.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, 280))
        
        # Draw stats
        stats_y = 350
        time_text = fonts.get('medium').render(f"Completion Time: {int(self.elapsed_time)} seconds", True, Colors.TEXT_HIGHLIGHT)
        moves_text = fonts.get('medium').render(f"Moves Used: {self.player.moves}", True, Colors.TEXT_HIGHLIGHT)
        score_text = fonts.get('medium').render(f"Total Score: {self.player.score}", True, Colors.TEXT_HIGHLIGHT)
        
        surface.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, stats_y))
        surface.blit(moves_text, (SCREEN_WIDTH // 2 - moves_text.get_width() // 2, stats_y + 40))
        surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, stats_y + 80))
        
        # Draw buttons
        for button in self.active_buttons:
            button.draw(surface)
    
    def draw_cursor(self, surface):
        mx, my = self.mouse_pos
        
        # Draw outer cursor ring
        pygame.draw.circle(surface, Colors.CURSOR_OUTER, (mx, my), 10, 2)
        
        # Draw inner cursor dot
        pygame.draw.circle(surface, Colors.CURSOR, (mx, my), 3)

# Main game loop with proper error handling
def main():
    try:
        game = Game()
        running = True
        
        # Performance tracking
        frame_count = 0
        fps_timer = pygame.time.get_ticks()
        
        # Main game loop
        while running:
            # Handle events
            game.handle_events()
            
            # Update game state
            game.update()
            
            # Draw everything
            game.draw(screen)
            
            # Update display
            pygame.display.flip()
            
            # Cap the frame rate
            game.clock.tick(FPS)
            
            # Calculate and display FPS occasionally
            frame_count += 1
            current_time = pygame.time.get_ticks()
            if current_time - fps_timer >= 1000:  # Every second
                fps = frame_count * 1000 / (current_time - fps_timer)
                pygame.display.set_caption(f"Neon Maze: Pathfinder's Journey - FPS: {fps:.1f}")
                frame_count = 0
                fps_timer = current_time
        
        pygame.quit()
        
    except Exception as e:
        print(f"Game error: {e}")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()