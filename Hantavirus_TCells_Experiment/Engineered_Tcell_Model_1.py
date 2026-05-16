import pygame
import random
import math
import numpy as np

# config
WIDTH, HEIGHT = 1150, 750
UI_WIDTH = 300
SIM_WIDTH = WIDTH - UI_WIDTH
FPS = 60

# time simulation - real-time
SIM_TIME_RATIO = 12 * 3600  
SECONDS_PER_DAY = 86400

# pathogenesis constants
PEAK_VIRAL_TIME = 2.5 * SECONDS_PER_DAY 
VIRAL_GROWTH_RATE = 1.0 / PEAK_VIRAL_TIME
INFECTIOUS_THRESHOLD = 0.4  

# suppression constant
SUPPRESSION_DECAY_RATE = 0.15   # Rate at which protection wears off per sim hour
SUPPRESSION_THRESHOLD = 0.1    # Level below which a cell becomes active again
RECOVERY_SPEED = 0.25          # How fast T-cells boost suppression level

# physics
GRID_SIZE = 10
DIFFUSION_COEFF = 0.15
DECAY_RATE = 0.02
CHEMO_SENSITIVITY = 30.0
SUPPRESS_TIME = 3 * 3600 
CYTOKINE_RADIUS = 65

# colors
BG_COLOR = (8, 10, 15)
S_CELL = (46, 204, 113)      # Healthy
E_CELL = (241, 196, 15)      # Infected/Expressing
SUP_CELL = (52, 152, 219)    # Suppressed
T_CELL_COLOR = (155, 89, 182)
VIRION_COLOR = (255, 50, 50)
CHEMO_GLOW = (0, 100, 255)
TEXT_COL = (220, 220, 225)


class Virion:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.angle = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(1.5, 3.0)
        self.active = True

    def update(self):
        self.angle += random.uniform(-0.5, 0.5)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        if self.x < 5 or self.x > SIM_WIDTH - 5: self.angle = math.pi - self.angle
        if self.y < 5 or self.y > HEIGHT - 5: self.angle = -self.angle
        self.x = max(5, min(SIM_WIDTH-5, self.x))
        self.y = max(5, min(HEIGHT-5, self.y))

    def draw(self, surface):
        pygame.draw.circle(surface, VIRION_COLOR, (int(self.x), int(self.y)), 2)

class EndothelialCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.grid_x, self.grid_y = int(x // GRID_SIZE), int(y // GRID_SIZE)
        self.state = 0  # 0:Healthy, 1:Infected, 2:Suppressed
        self.viral_load = 0.0
        self.suppression_level = 0.0
        
    def infect(self):
        if self.state == 0:
            self.state = 1
            self.viral_load = 0.1

    def update(self, dt_sim, chem_grid, tcells):
        # suppression logic
        nearby_tcells = [t for t in tcells if t.state == "SUPPRESSING" and math.hypot(self.x-t.x, self.y-t.y) < CYTOKINE_RADIUS]
        
        if nearby_tcells:
            self.suppression_level = min(1.0, self.suppression_level + RECOVERY_SPEED * (dt_sim / 3600))
        else:
            self.suppression_level = max(0.0, self.suppression_level - SUPPRESSION_DECAY_RATE * (dt_sim / 3600))

        # transition
        if self.state == 1:
            if self.suppression_level > 0.8:
                self.state = 2
            else:
                self.viral_load = min(1.0, self.viral_load + (VIRAL_GROWTH_RATE * dt_sim))
        elif self.state == 2:
            if self.suppression_level < SUPPRESSION_THRESHOLD:
                self.state = 1 # Virus resumes replication

        # chemical signaling
        if self.state == 1:
            production = (8.0 * self.viral_load) / (0.3 + self.viral_load)
            try:
                chem_grid[self.grid_x, self.grid_y] += production
            except IndexError: pass

    def draw(self, surface):
        color = [S_CELL, E_CELL, SUP_CELL][self.state]
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 8)
        
        if self.state == 1:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 4
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), 9 + pulse, 1)
        
        if self.suppression_level > 0.1:
            r = int(self.suppression_level * 6)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), r, 1)

class SmartTCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = "SEARCHING"
        self.target = None
        self.suppress_timer = 0
        self.vel = [random.uniform(-1,1), random.uniform(-1,1)]

    def update(self, dt_sim, chem_grid, cells):
        if self.state == "SEARCHING":
            cols, rows = chem_grid.shape
            gx = max(0, min(cols - 1, int(self.x // GRID_SIZE)))
            gy = max(0, min(rows - 1, int(self.y // GRID_SIZE)))
            
            gx_prev, gx_next = max(0, gx-1), min(cols-1, gx+1)
            gy_prev, gy_next = max(0, gy-1), min(rows-1, gy+1)

            grad_x = chem_grid[gx_next, gy] - chem_grid[gx_prev, gy]
            grad_y = chem_grid[gx, gy_next] - chem_grid[gx, gy_prev]
            
            self.vel[0] = random.uniform(-0.5, 0.5) + (grad_x * CHEMO_SENSITIVITY)
            self.vel[1] = random.uniform(-0.5, 0.5) + (grad_y * CHEMO_SENSITIVITY)
            
            mag = math.hypot(*self.vel)
            if mag > 3.8: self.vel = [(v/mag)*3.8 for v in self.vel]
            
            self.x += self.vel[0]
            self.y += self.vel[1]

            for c in cells:
                if c.state == 1 and math.hypot(c.x-self.x, c.y-self.y) < 25:
                    self.state = "SUPPRESSING"
                    self.target = c
                    self.suppress_timer = 0
                    break
        
        elif self.state == "SUPPRESSING":
            self.suppress_timer += dt_sim
            if self.suppress_timer >= SUPPRESS_TIME:
                self.state = "SEARCHING"

        self.x = max(10, min(SIM_WIDTH-10, self.x))
        self.y = max(10, min(HEIGHT-10, self.y))

    def draw(self, surface):
        color = (0, 255, 255) if self.state == "SUPPRESSING" else T_CELL_COLOR
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 8)
        if self.state == "SUPPRESSING":
            s = pygame.Surface((CYTOKINE_RADIUS*2, CYTOKINE_RADIUS*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 255, 255, 40), (CYTOKINE_RADIUS, CYTOKINE_RADIUS), CYTOKINE_RADIUS)
            surface.blit(s, (int(self.x-CYTOKINE_RADIUS), int(self.y-CYTOKINE_RADIUS)))

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("HTNV - T-Cell : Engineered T-Cell Suppression Test")
        self.font_s = pygame.font.SysFont("Courier New", 14, bold=True)
        self.font_m = pygame.font.SysFont("Courier New", 18, bold=True)
        self.clock = pygame.time.Clock()
        self.reset_sim()

    def reset_sim(self):
        self.paused = False
        self.total_sim_seconds = 0
        self.chem_grid = np.zeros((SIM_WIDTH // GRID_SIZE, HEIGHT // GRID_SIZE))
        self.cells = [EndothelialCell(x, y) for x in range(45, SIM_WIDTH, 50) for y in range(45, HEIGHT, 50)]
        self.tcells = [SmartTCell(random.randint(SIM_WIDTH-50, SIM_WIDTH), random.randint(0, HEIGHT)) for _ in range(50)] # 50 T-cell active
        self.virions = []
        random.choice(self.cells).infect()

    def update(self):
        real_dt = self.clock.tick(FPS) / 1000.0
        if self.paused: return
        
        dt_sim = real_dt * SIM_TIME_RATIO
        self.total_sim_seconds += dt_sim
        
        new_grid = self.chem_grid * (1 - DECAY_RATE)
        laplacian = np.zeros_like(new_grid)
        laplacian[1:-1, 1:-1] = (new_grid[:-2, 1:-1] + new_grid[2:, 1:-1] + 
                                 new_grid[1:-1, :-2] + new_grid[1:-1, 2:]) - 4 * new_grid[1:-1, 1:-1]
        self.chem_grid = new_grid + DIFFUSION_COEFF * laplacian

        for c in self.cells: 
            c.update(dt_sim, self.chem_grid, self.tcells)
            if c.state == 1 and c.viral_load > INFECTIOUS_THRESHOLD:
                if random.random() < 0.08: self.virions.append(Virion(c.x, c.y))

        for v in self.virions[:]:
            v.update()
            for c in self.cells:
                if c.state == 0 and math.hypot(v.x - c.x, v.y - c.y) < 12:
                    c.infect()
                    v.active = False
                    break
            if not v.active: self.virions.remove(v)

        for t in self.tcells: t.update(dt_sim, self.chem_grid, self.cells)

    def draw_ui(self):
        pygame.draw.rect(self.screen, (20, 20, 30), (SIM_WIDTH, 0, UI_WIDTH, HEIGHT))
        y = 30
        days = int(self.total_sim_seconds // SECONDS_PER_DAY)
        hours = int((self.total_sim_seconds % SECONDS_PER_DAY) // 3600)
        self.screen.blit(self.font_m.render(f"DAY {days} | {hours:02d} HOURS", True, (255, 255, 0)), (SIM_WIDTH+20, y))
        
        y = 110
        healthy = sum(1 for c in self.cells if c.state == 0)
        infected = sum(1 for c in self.cells if c.state == 1)
        suppressed = sum(1 for c in self.cells if c.state == 2)
        
        self.screen.blit(self.font_s.render(f"HEALTHY:    {healthy}", True, S_CELL), (SIM_WIDTH+20, y))
        self.screen.blit(self.font_s.render(f"INFECTED:   {infected}", True, E_CELL), (SIM_WIDTH+20, y+20))
        self.screen.blit(self.font_s.render(f"SUPPRESSED: {suppressed}", True, SUP_CELL), (SIM_WIDTH+20, y+40))
        self.screen.blit(self.font_s.render(f"VIRIONS:    {len(self.virions)}", True, VIRION_COLOR), (SIM_WIDTH+20, y+60))

        # Organ Integrity Bar
        y = 220
        integrity = ((healthy + suppressed) / len(self.cells)) * 100
        self.screen.blit(self.font_s.render(f"ORGAN INTEGRITY: {integrity:.1f}%", True, (0, 255, 150)), (SIM_WIDTH+20, y))
        pygame.draw.rect(self.screen, (50, 50, 60), (SIM_WIDTH+20, y+20, 250, 15))
        pygame.draw.rect(self.screen, (0, 255, 100), (SIM_WIDTH+20, y+20, int(2.5*integrity), 15))

        y = 300
        self.screen.blit(self.font_m.render("LEGEND", True, (200, 200, 200)), (SIM_WIDTH+20, y))
        items = [("Healthy Cell", S_CELL), ("Infected", E_CELL), ("Suppressed", SUP_CELL), ("Engineered T-Cell", T_CELL_COLOR), ("Active Virion", VIRION_COLOR)]
        for label, color in items:
            pygame.draw.circle(self.screen, color, (SIM_WIDTH+35, y+40), 7)
            self.screen.blit(self.font_s.render(label, True, TEXT_COL), (SIM_WIDTH+55, y+33))
            y += 35

        self.screen.blit(self.font_s.render("SPACE: PAUSE | R: RESET", True, (255, 50, 50)), (SIM_WIDTH+20, HEIGHT-40))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: self.paused = not self.paused
                    if event.key == pygame.K_r: self.reset_sim()

            self.update()
            self.screen.fill(BG_COLOR)
            
            for i in range(self.chem_grid.shape[0]):
                for j in range(self.chem_grid.shape[1]):
                    alpha = min(140, int(self.chem_grid[i, j] * 35))
                    if alpha > 3:
                        s = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                        s.fill((*CHEMO_GLOW, alpha))
                        self.screen.blit(s, (i*GRID_SIZE, j*GRID_SIZE))

            for v in self.virions: v.draw(self.screen)
            for c in self.cells: c.draw(self.screen)
            for t in self.tcells: t.draw(self.screen)
            self.draw_ui()
            pygame.display.flip()

if __name__ == "__main__":
    Simulation().run()