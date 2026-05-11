import pygame
import random
import math
import numpy as np

# config
WIDTH, HEIGHT = 1150, 750
UI_WIDTH = 300
SIM_WIDTH = WIDTH - UI_WIDTH
FPS = 60

# time Scaling: 1 second real-time = 12 hours sim-time
SIM_TIME_RATIO = 12 * 3600  
SECONDS_PER_DAY = 86400

# biology parameters
INCUBATION_PERIOD = 14 * SECONDS_PER_DAY
KILL_TIME = 3 * 3600  # 3 hours for Perforin/Granzyme delivery
TCELL_SPEED_BASE = 2.0
VIRION_SPEED = 1.3
DETECTION_RANGE = 130

# colors
BG_COLOR = (10, 10, 15)
LEAK_COLOR = (110, 40, 130) # Purple for Vascular Leak
S_CELL = (46, 204, 113)     # Healthy
E_CELL = (241, 196, 15)     # Incubating
I_CELL = (231, 76, 60)      # Infectious
D_CELL = (30, 30, 40)       # Dead
T_CELL_COLOR = (52, 152, 219)
VIRION_COLOR = (240, 240, 240)



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
        if self.state == 2: # MHC-I Presentation
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), 13, 1)

class TCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = "SEARCHING" 
        self.target = None
        self.kill_timer = 0
        self.angle = random.uniform(0, 2*math.pi)
        self.step_remaining = 0

    def update(self, dt, cells):
        if self.state == "SEARCHING":
            self.move_levy(cells)
        elif self.state == "LINGERING":
            self.linger_and_kill(dt)

    def move_levy(self, cells):
        # levy Flight: optimal for finding sparse targets (Infectious cells)
        if self.step_remaining <= 0:
            self.step_remaining = random.uniform(40, 120) if random.random() < 0.03 else random.uniform(5, 20)
            self.angle = random.uniform(0, 2*math.pi)

        # scanning for MHC-I (Antigen Presentation)
        for c in cells:
            if c.state == 2:
                dist = math.hypot(c.x - self.x, c.y - self.y)
                if dist < DETECTION_RANGE:
                    self.angle = math.atan2(c.y - self.y, c.x - self.x)
                    if dist < 10:
                        self.state = "LINGERING"
                        self.target = c
                        self.kill_timer = 0
                    break

        self.x += math.cos(self.angle) * TCELL_SPEED_BASE
        self.y += math.sin(self.angle) * TCELL_SPEED_BASE
        self.step_remaining -= TCELL_SPEED_BASE
        self.x = max(10, min(SIM_WIDTH-10, self.x))
        self.y = max(10, min(HEIGHT-10, self.y))

    def linger_and_kill(self, dt):
        if self.target and self.target.state == 2:
            self.kill_timer += dt * SIM_TIME_RATIO
            if self.kill_timer >= KILL_TIME:
                self.target.state = 3 # induce Apoptosis
                self.target.is_leaking = True
                self.state = "SEARCHING"
        else:
            self.state = "SEARCHING"

class Virion:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.angle = random.uniform(0, 2*math.pi)

    def move(self):
        self.x += math.cos(self.angle) * VIRION_SPEED
        self.y += math.sin(self.angle) * VIRION_SPEED
        if self.x < 0 or self.x > SIM_WIDTH: self.angle = math.pi - self.angle
        if self.y < 0 or self.y > HEIGHT: self.angle = -self.angle

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Hantavirus Simulation Model 4.0")
        self.clock = pygame.time.Clock()
        self.leak_layer = pygame.Surface((SIM_WIDTH, HEIGHT), pygame.SRCALPHA)
        self.font_s = pygame.font.SysFont("Courier New", 14, bold=True)
        self.font_m = pygame.font.SysFont("Courier New", 18, bold=True)
        self.reset()

    def reset(self):
        self.paused = False
        self.sim_time = 0
        self.leak_layer.fill((0,0,0,0))
        self.organ_health = 100.0
        self.cells = [EndothelialCell(x, y) for x in range(50, SIM_WIDTH, 45) for y in range(50, HEIGHT, 45)]
        self.virions = [Virion(random.randint(0, 50), random.randint(0, HEIGHT)) for _ in range(6)]
        self.tcells = [TCell(random.randint(SIM_WIDTH-100, SIM_WIDTH), random.randint(0, HEIGHT)) for _ in range(5)]

    def update_sim(self, dt):
        self.sim_time += dt * SIM_TIME_RATIO
        
        # viral sticking to cells
        for v in self.virions[:]:
            v.move()
            for c in self.cells:
                if c.state == 0 and math.hypot(v.x-c.x, v.y-c.y) < 12:
                    c.infect() 
                    if v in self.virions: self.virions.remove(v)
                    break
        
        # Cell Cycle & Budding
        for c in self.cells:
            c.update(dt)
            if c.state == 2 and random.random() < 0.004:
                self.virions.append(Virion(c.x, c.y))
            if c.is_leaking:
                pygame.draw.circle(self.leak_layer, (100, 30, 120, 90), (int(c.x), int(c.y)), 35)
                c.is_leaking = False

        for t in self.tcells: t.update(dt, self.cells)

        # update Organ Health Percentage
        total = len(self.cells)
        healthy = sum(1 for c in self.cells if c.state == 0)
        dead = sum(1 for c in self.cells if c.state == 3)
        self.organ_health = (healthy / total) * 100

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.screen.blit(self.leak_layer, (0, 0))
        for c in self.cells: c.draw(self.screen)
        for v in self.virions: pygame.draw.circle(self.screen, VIRION_COLOR, (int(v.x), int(v.y)), 3)
        for t in self.tcells:
            color = (255, 255, 0) if t.state == "LINGERING" else T_CELL_COLOR
            pygame.draw.circle(self.screen, color, (int(t.x), int(t.y)), 7)
        
        # UI Panel
        pygame.draw.rect(self.screen, (20, 20, 30), (SIM_WIDTH, 0, UI_WIDTH, HEIGHT))
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        y = 30
        self.screen.blit(self.font_m.render("ORGAN HEALTH MONITOR", True, (0, 255, 150)), (SIM_WIDTH+20, y))
        y += 40
        
        # health Bar
        health_col = (0, 255, 0) if self.organ_health > 70 else (255, 255, 0) if self.organ_health > 40 else (255, 0, 0)
        pygame.draw.rect(self.screen, (50, 50, 50), (SIM_WIDTH+20, y, 250, 25))
        pygame.draw.rect(self.screen, health_col, (SIM_WIDTH+20, y, int(2.5 * self.organ_health), 25))
        self.screen.blit(self.font_s.render(f"{self.organ_health:.1f}% INTEGRITY", True, (255, 255, 255)), (SIM_WIDTH+70, y+4))
        
        y += 60
        days = int(self.sim_time // SECONDS_PER_DAY)
        self.screen.blit(self.font_s.render(f"TIMELINE: DAY {days}", True, (200, 200, 200)), (SIM_WIDTH+20, y))
        
        y += 50
        stats = [
            (f"Healthy Cells:   {sum(1 for c in self.cells if c.state==0)}", S_CELL),
            (f"Infectious:      {sum(1 for c in self.cells if c.state==2)}", I_CELL),
            (f"Vascular Leak:   {sum(1 for c in self.cells if c.state==3)}", LEAK_COLOR),
            (f"T-Cells Active:  {len(self.tcells)}", T_CELL_COLOR)
        ]
        for txt, col in stats:
            pygame.draw.circle(self.screen, col, (SIM_WIDTH+25, y+8), 6)
            self.screen.blit(self.font_s.render(txt, True, (220, 220, 220)), (SIM_WIDTH+45, y))
            y += 30

        self.screen.blit(self.font_s.render("SPACE: PAUSE | R: RESET", True, (255, 255, 0)), (SIM_WIDTH+20, HEIGHT-40))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: self.paused = not self.paused
                    if event.key == pygame.K_r: self.reset()
            if not self.paused: self.update_sim(dt)
            self.draw()

if __name__ == "__main__":
    Simulation().run()