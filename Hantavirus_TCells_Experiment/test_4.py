import pygame
import random
import math
import numpy as np

# congig
WIDTH, HEIGHT = 1150, 750
UI_WIDTH = 300
SIM_WIDTH = WIDTH - UI_WIDTH
FPS = 60

# chemokine grid setting
GRID_SIZE = 10 
COLS, ROWS = SIM_WIDTH // GRID_SIZE, HEIGHT // GRID_SIZE

# bio parameters
SIM_TIME_RATIO = 12 * 3600  
SECONDS_PER_DAY = 86400
DIFFUSION_COEFF = 0.15   # How fast CXCL10 spreads
DECAY_RATE = 0.02        # How fast CXCL10 dissipates
CHEMO_SENSITIVITY = 15.0 # "alpha" in the chemotaxis equation

# colors
BG_COLOR = (5, 5, 10)
S_CELL = (46, 204, 113)
I_CELL = (231, 76, 60)
T_CELL_COLOR = (52, 152, 219)
CHEMO_COLOR = (100, 100, 255) 


class EndothelialCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.grid_x, self.grid_y = int(x // GRID_SIZE), int(y // GRID_SIZE)
        self.state = 0 # 0: Healthy, 1: Infected
        self.viral_load = 0.0

    def infect(self):
        if self.state == 0:
            self.state = 1
            self.viral_load = 0.1

    def update(self, dt, chem_grid):
        if self.state == 1:
            self.viral_load = min(1.0, self.viral_load + 0.05 * dt)
            # Michaelis-Menten production of CXCL10
            v_max = 5.0
            km = 0.4
            production = (v_max * self.viral_load) / (km + self.viral_load)
            chem_grid[self.grid_x, self.grid_y] += production

    def draw(self, surface):
        color = S_CELL if self.state == 0 else I_CELL
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 7)

class ChemotacticTCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vel_x = random.uniform(-1, 1)
        self.vel_y = random.uniform(-1, 1)

    def update(self, chem_grid):
        gx, gy = int(self.x // GRID_SIZE), int(self.y // GRID_SIZE)
        
        # sensing the gradient
        try:
            grad_x = chem_grid[gx+1, gy] - chem_grid[gx-1, gy]
            grad_y = chem_grid[gx, gy+1] - chem_grid[gx, gy-1]
        except IndexError:
            grad_x, grad_y = 0, 0

        # biased random walk equation
        rand_x, rand_y = random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)
        
        self.vel_x = rand_x + (grad_x * CHEMO_SENSITIVITY)
        self.vel_y = rand_y + (grad_y * CHEMO_SENSITIVITY)

        # Normalize/Cap speed
        speed = math.hypot(self.vel_x, self.vel_y)
        if speed > 3.0:
            self.vel_x = (self.vel_x / speed) * 3.0
            self.vel_y = (self.vel_y / speed) * 3.0

        self.x += self.vel_x
        self.y += self.vel_y
        
        # Boundary
        self.x = max(GRID_SIZE, min(SIM_WIDTH - GRID_SIZE, self.x))
        self.y = max(GRID_SIZE, min(HEIGHT - GRID_SIZE, self.y))

    def draw(self, surface):
        pygame.draw.circle(surface, T_CELL_COLOR, (int(self.x), int(self.y)), 8)

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.chem_grid = np.zeros((COLS, ROWS))
        self.cells = [EndothelialCell(x, y) for x in range(40, SIM_WIDTH, 50) for y in range(40, HEIGHT, 50)]
        self.tcells = [ChemotacticTCell(random.randint(0, SIM_WIDTH), random.randint(0, HEIGHT)) for _ in range(8)]
        self.font = pygame.font.SysFont("Courier New", 16, bold=True)
        # Seed infection
        random.choice(self.cells).infect()

    def diffuse_chemokines(self):
        # laplacian difffusion
        new_grid = self.chem_grid * (1 - DECAY_RATE)
        # diffusion approximation
        shift_u = np.roll(new_grid, 1, axis=1)
        shift_d = np.roll(new_grid, -1, axis=1)
        shift_l = np.roll(new_grid, 1, axis=0)
        shift_r = np.roll(new_grid, -1, axis=0)
        
        self.chem_grid = (1 - DIFFUSION_COEFF) * new_grid + (DIFFUSION_COEFF / 4) * (shift_u + shift_d + shift_l + shift_r)

    def draw_chem_cloud(self):
        # gradient visual
        for i in range(COLS):
            for j in range(ROWS):
                val = min(255, int(self.chem_grid[i, j] * 50))
                if val > 5:
                    rect = (i * GRID_SIZE, j * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(self.screen, (0, val//2, val, val//4), rect)

    def run(self):
        running = True
        while running:
            dt = 1/FPS
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False

            # Update
            self.diffuse_chemokines()
            for c in self.cells: c.update(dt, self.chem_grid)
            for t in self.tcells: t.update(self.chem_grid)

            # Draw
            self.screen.fill(BG_COLOR)
            self.draw_chem_cloud()
            for c in self.cells: c.draw(self.screen)
            for t in self.tcells: t.draw(self.screen)
            
            # UI
            pygame.draw.rect(self.screen, (20, 20, 30), (SIM_WIDTH, 0, UI_WIDTH, HEIGHT))
            self.screen.blit(self.font.render("CHEMOTAXIS MONITOR", True, CHEMO_COLOR), (SIM_WIDTH+20, 40))
            self.screen.blit(self.font.render(f"CXCL10 Peak: {np.max(self.chem_grid):.2f}", True, (200, 200, 200)), (SIM_WIDTH+20, 80))
            self.screen.blit(self.font.render("T-Cells following gradient...", True, (200, 200, 200)), (SIM_WIDTH+20, 110))
            
            pygame.display.flip()

if __name__ == "__main__":
    Simulation().run()