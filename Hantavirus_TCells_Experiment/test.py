import pygame
import random
import math
import numpy as np

# configuration
WIDTH, HEIGHT = 1150, 750
UI_WIDTH = 300
SIM_WIDTH = WIDTH - UI_WIDTH
FPS = 60

# time scaling
SIM_TIME_RATIO = 12 * 3600  
SECONDS_PER_DAY = 86400

# bio parameters
INCUBATION_PERIOD = 14 * SECONDS_PER_DAY
KILL_TIME = 2 * 3600  # 2 hours to induce apoptosis
TCELL_SPEED_BASE = 2.0
VIRION_SPEED = 1.2
DETECTION_RANGE = 120
GRID_RES = 40

# colors
BG_COLOR = (10, 10, 15)
LEAK_COLOR = (100, 30, 120) # Purple for Vascular Leak
S_CELL = (46, 204, 113)     # Healthy
E_CELL = (241, 196, 15)    # Incubating
I_CELL = (231, 76, 60)     # Infectious
D_CELL = (40, 40, 50)      # Dead
T_CELL_COLOR = (52, 152, 219)
VIRION_COLOR = (255, 255, 255)




class EndothelialCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = 0
        self.incubation_timer = 0
        self.is_leaking = False
        
    def infect(self):
        if self.state == 0:
            self.state = 1
            self.incubation_timer = 0

    def update(self, dt):
        if self.state == 1:
            self.incubation_timer += dt * SIM_TIME_RATIO
            if self.incubation_timer >= INCUBATION_PERIOD:
                self.state = 2

    def draw(self, surface):
        color = [S_CELL, E_CELL, I_CELL, D_CELL][self.state]
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 9)
        # MHC-I
        if self.state == 2:
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), 12, 1)

class TCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = "SEARCHING" 
        self.target = None
        self.kill_timer = 0
        self.angle = random.uniform(0, 2*math.pi)
        self.step_remaining = 0

    def update(self, dt, cells, chem_grid):
        if self.state == "SEARCHING":
            self.search_logic(cells)
        elif self.state == "LINGERING":
            self.linger_logic(dt)

    def search_logic(self, cells):
        # Levy Flight Movement
        if self.step_remaining <= 0:
            if random.random() < 0.05: # 5% chance of long jump
                self.step_remaining = random.uniform(40, 100)
            else:
                self.step_remaining = random.uniform(5, 15)
            self.angle = random.uniform(0, 2*math.pi)

        # Check for chemotaxis
        best_dist = DETECTION_RANGE
        for c in cells:
            if c.state == 2:
                d = math.hypot(c.x - self.x, c.y - self.y)
                if d < best_dist:
                    # move toward target
                    self.angle = math.atan2(c.y - self.y, c.x - self.x)
                    if d < 12:
                        self.state = "LINGERING"
                        self.target = c
                        self.kill_timer = 0
                    break

        self.x += math.cos(self.angle) * TCELL_SPEED_BASE
        self.y += math.sin(self.angle) * TCELL_SPEED_BASE
        self.step_remaining -= TCELL_SPEED_BASE
        
        # Keep in bounds
        self.x = max(10, min(SIM_WIDTH-10, self.x))
        self.y = max(10, min(HEIGHT-10, self.y))

    def linger_logic(self, dt):
        # T-Cell stays stuck to the cell to release Perforin/Granzyme
        if self.target and self.target.state == 2:
            self.kill_timer += dt * SIM_TIME_RATIO
            if self.kill_timer >= KILL_TIME:
                self.target.state = 3 # Cell Dies
                self.target.is_leaking = True
                self.state = "SEARCHING"
                self.target = None
        else:
            self.state = "SEARCHING"


class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Hantavirus T-Cell Simulation: Endothelial Pathogenesis & Immune Response")
        self.clock = pygame.time.Clock()
        
        self.leak_layer = pygame.Surface((SIM_WIDTH, HEIGHT), pygame.SRCALPHA)
        
        self.font_s = pygame.font.SysFont("Verdana", 14)
        self.font_m = pygame.font.SysFont("Verdana", 18, bold=True)
        self.reset()

    def reset(self):
        self.paused = False
        self.sim_time = 0
        self.leak_layer.fill((0,0,0,0))
        
        self.cells = []
        for x in range(50, SIM_WIDTH, 45):
            for y in range(50, HEIGHT, 45):
                self.cells.append(EndothelialCell(x, y))
        
        self.virions = [Virion(random.randint(0, 50), random.randint(0, HEIGHT)) for _ in range(8)]
        self.tcells = [TCell(random.randint(SIM_WIDTH-100, SIM_WIDTH), random.randint(0, HEIGHT)) for _ in range(4)]

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: self.paused = not self.paused
                    if event.key == pygame.K_r: self.reset()

            if not self.paused:
                self.update_sim(dt)
            
            self.draw()

    def update_sim(self, dt):
        self.sim_time += dt * SIM_TIME_RATIO
        
        # virion behavior
        for v in self.virions[:]:
            v.move()
            for c in self.cells:
                if c.state == 0 and math.hypot(v.x-c.x, v.y-c.y) < 12:
                    c.infect()
                    if v in self.virions: self.virions.remove(v)
                    break
        
        # cell update & budding
        for c in self.cells:
            c.update(dt)
            if c.state == 2 and random.random() < 0.003: # release new virions
                self.virions.append(Virion(c.x, c.y))
            
            # if cell died, purple leaked
            if c.is_leaking:
                pygame.draw.circle(self.leak_layer, (100, 30, 120, 80), (int(c.x), int(c.y)), 30)
                c.is_leaking = False

        # 3. T-Cell Search & Linger
        for t in self.tcells:
            t.update(dt, self.cells, None)

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Draw Vascular Leak Background
        self.screen.blit(self.leak_layer, (0, 0))
        
        for c in self.cells: c.draw(self.screen)
        for v in self.virions: pygame.draw.circle(self.screen, VIRION_COLOR, (int(v.x), int(v.y)), 3)
        for t in self.tcells:
            color = (255, 255, 0) if t.state == "LINGERING" else T_CELL_COLOR
            pygame.draw.circle(self.screen, color, (int(t.x), int(t.y)), 7)

        # UI Panel
        pygame.draw.rect(self.screen, (25, 25, 35), (SIM_WIDTH, 0, UI_WIDTH, HEIGHT))
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        days = int(self.sim_time // SECONDS_PER_DAY)
        hours = int((self.sim_time % SECONDS_PER_DAY) // 3600)
        
        y = 30
        self.screen.blit(self.font_m.render("REAL-TIME", True, (0, 200, 255)), (SIM_WIDTH+20, y))
        y += 40
        self.screen.blit(self.font_s.render(f"Simulation Clock: Day {days}, Hour {hours}", True, (255, 255, 255)), (SIM_WIDTH+20, y))
        
        
        y += 50
        counts = [
            (f"Healthy: {sum(1 for c in self.cells if c.state==0)}", S_CELL),
            (f"Incubating: {sum(1 for c in self.cells if c.state==1)}", E_CELL),
            (f"Infectious: {sum(1 for c in self.cells if c.state==2)}", I_CELL),
            (f"Vascular Leak: {sum(1 for c in self.cells if c.state==3)}", LEAK_COLOR),
            (f"Viral Load: {len(self.virions)}", VIRION_COLOR)
        ]
        for txt, col in counts:
            pygame.draw.rect(self.screen, col, (SIM_WIDTH+20, y+4, 12, 12))
            self.screen.blit(self.font_s.render(txt, True, (220, 220, 220)), (SIM_WIDTH+40, y))
            y += 25
            
        # # Legend
        # y += 40
        # self.screen.blit(self.font_m.render("MECHANISMS", True, (0, 200, 255)), (SIM_WIDTH+20, y))
        # y += 30
        # mechanics = [
        #     "Viral Budding: Released from Red cells",
        #     "T-Cell Search: Levy Flight Patterns",
        #     "Cytotoxicity: Lingering Kill (2hrs)",
        #     "Vascular Leak: Purple Spills (Apoptosis)"
        # ]
        # for m in mechanics:
        #     self.screen.blit(self.font_s.render("• " + m, True, (160, 160, 160)), (SIM_WIDTH+20, y))
        #     y += 22

        # Status Button
        status_txt = "PAUSED" if self.paused else "RUNNING"
        status_col = (255, 50, 50) if self.paused else (50, 255, 50)
        self.screen.blit(self.font_m.render(f"[{status_txt}]", True, status_col), (SIM_WIDTH+20, HEIGHT-80))
        self.screen.blit(self.font_s.render("SPACE: Pause | R: Reset", True, (200, 200, 0)), (SIM_WIDTH+20, HEIGHT-40))

class Virion:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.angle = random.uniform(0, 2*math.pi)

    def move(self):
        self.x += math.cos(self.angle) * VIRION_SPEED
        self.y += math.sin(self.angle) * VIRION_SPEED
        if self.x < 0 or self.x > SIM_WIDTH: self.angle = math.pi - self.angle
        if self.y < 0 or self.y > HEIGHT: self.angle = -self.angle

if __name__ == "__main__":
    sim = Simulation()
    sim.run()