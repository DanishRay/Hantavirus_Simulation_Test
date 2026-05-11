import pygame
import random
import math
import numpy as np

# --- CONFIGURATION & CONSTANTS ---
WIDTH, HEIGHT = 1150, 750
UI_WIDTH = 300
SIM_WIDTH = WIDTH - UI_WIDTH
FPS = 60

# Time Scaling: 1 second real-time = 12 hours sim-time
SIM_TIME_RATIO = 12 * 3600  
SECONDS_PER_DAY = 86400

# Biology & Engineering Parameters
INCUBATION_PERIOD = 10 * SECONDS_PER_DAY
SUPPRESS_TIME = 3 * 3600      # 3 hours for cytokine signaling to take effect
DETECTION_RANGE = 140
CYTOKINE_RADIUS = 60          # Range of the IFN-gamma/TNF-alpha cloud
TCELL_SPEED_BASE = 2.2

# Colors
BG_COLOR = (10, 12, 18)
S_CELL = (46, 204, 113)       # Healthy
E_CELL = (241, 196, 15)       # Incubating (Expressing Gn/Gc)
I_CELL = (231, 76, 60)        # Infectious
SUP_CELL = (52, 152, 219)     # Suppressed (Engineered Success)
T_CELL_COLOR = (155, 89, 182)  # Purple (Engineered T-Cell)
CYTOKINE_GLOW = (0, 255, 255, 40)

class EndothelialCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = 0  # 0:S, 1:E, 2:I, 3:Suppressed
        self.incubation_timer = 0
        self.viral_load = 0.0
        
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
        color = [S_CELL, E_CELL, I_CELL, SUP_CELL][self.state]
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 9)
        # Highlight cells expressing Hantavirus Glycoproteins (Condition A for synNotch)
        if self.state in [1, 2]:
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), 12, 1)

class EngineeredTCell:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.state = "PATROL" 
        self.target = None
        self.suppress_timer = 0
        self.angle = random.uniform(0, 2*math.pi)
        self.speed = 2.2

    def check_logic_gate(self, cells):
        """ synNotch AND-Gate Logic """
        # Condition A: Detect Hantavirus Glycoproteins (Gn/Gc)
        nearby_infected = [c for c in cells if c.state in [1, 2] and math.hypot(c.x-self.x, c.y-self.y) < DETECTION_RANGE]
        
        # Condition B: Healthy Environment Signal
        # (Check if the surrounding 150px has > 50% healthy cells)
        neighbors = [c for c in cells if math.hypot(c.x-self.x, c.y-self.y) < 150]
        healthy_ratio = sum(1 for n in neighbors if n.state == 0) / (len(neighbors) + 1)
        
        condition_a = len(nearby_infected) > 0
        condition_b = healthy_ratio > 0.5
        
        if condition_a and condition_b:
            self.target = nearby_infected[0]
            return True
        return False

    def update(self, dt, cells):
        if self.state == "PATROL":
            if self.check_logic_gate(cells):
                self.state = "SUPPRESSING"
                self.suppress_timer = 0
            
            # Move (Random search)
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed
            if random.random() < 0.02: self.angle = random.uniform(0, 2*math.pi)
            
        elif self.state == "SUPPRESSING":
            if self.target and self.target.state in [1, 2]:
                # Move toward target
                dist = math.hypot(self.target.x - self.x, self.target.y - self.y)
                if dist > 5:
                    self.x += (self.target.x - self.x) * 0.1
                    self.y += (self.target.y - self.y) * 0.1
                
                self.suppress_timer += dt * SIM_TIME_RATIO
                if self.suppress_timer >= SUPPRESS_TIME:
                    self.target.state = 3 # Successfully suppressed non-lytically
                    self.state = "PATROL"
            else:
                self.state = "PATROL"

        # Boundary checks
        self.x = max(10, min(SIM_WIDTH-10, self.x))
        self.y = max(10, min(HEIGHT-10, self.y))

    def draw(self, surface):
        color = (0, 255, 255) if self.state == "SUPPRESSING" else T_CELL_COLOR
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), 8)
        if self.state == "SUPPRESSING":
            # Visual for Cytokine release (IFN-g / TNF-a)
            s = pygame.Surface((CYTOKINE_RADIUS*2, CYTOKINE_RADIUS*2), pygame.SRCALPHA)
            pygame.draw.circle(s, CYTOKINE_GLOW, (CYTOKINE_RADIUS, CYTOKINE_RADIUS), CYTOKINE_RADIUS)
            surface.blit(s, (int(self.x-CYTOKINE_RADIUS), int(self.y-CYTOKINE_RADIUS)))

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Engineered T-Cell: Non-Lytic Therapy")
        self.clock = pygame.time.Clock()
        self.font_s = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_m = pygame.font.SysFont("Arial", 18, bold=True)
        self.reset()

    def reset(self):
        self.paused = False
        self.sim_time = 0
        self.cells = [EndothelialCell(x, y) for x in range(50, SIM_WIDTH, 45) for y in range(50, HEIGHT, 45)]
        # Start with a few infection points
        for _ in range(3):
            random.choice(self.cells).infect()
        self.tcells = [EngineeredTCell(random.randint(SIM_WIDTH-100, SIM_WIDTH), random.randint(0, HEIGHT)) for _ in range(6)]

    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        if self.paused: return

        self.sim_time += dt * SIM_TIME_RATIO
        
        for c in self.cells:
            c.update(dt)
            # Viral Budding Logic
            # P(budding) is suppressed in state 3
            prob = 0.003 if c.state == 2 else 0.0001 if c.state == 3 else 0
            if random.random() < prob:
                # Infect a random nearby healthy cell
                targets = [n for n in self.cells if n.state == 0 and math.hypot(n.x-c.x, n.y-c.y) < 100]
                if targets: random.choice(targets).infect()

        for t in self.tcells:
            t.update(dt, self.cells)

    def draw(self):
        self.screen.fill(BG_COLOR)
        for c in self.cells: c.draw(self.screen)
        for t in self.tcells: t.draw(self.screen)
        
        # UI
        pygame.draw.rect(self.screen, (25, 25, 35), (SIM_WIDTH, 0, UI_WIDTH, HEIGHT))
        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        y = 30
        self.screen.blit(self.font_m.render("SYN-NOTCH MONITOR", True, (0, 255, 255)), (SIM_WIDTH+20, y))
        y += 50
        
        # Stats
        healthy = sum(1 for c in self.cells if c.state == 0)
        suppressed = sum(1 for c in self.cells if c.state == 3)
        infectious = sum(1 for c in self.cells if c.state == 2)
        
        # Organ Integrity (Suppressed cells count as functional!)
        integrity = ((healthy + suppressed) / len(self.cells)) * 100
        
        stats = [
            (f"Organ Integrity: {integrity:.1f}%", (255,255,255)),
            (f"Healthy Cells:   {healthy}", S_CELL),
            (f"Viral Suppression: {suppressed}", SUP_CELL),
            (f"Active Infection:  {infectious}", I_CELL),
            (f"T-Cells (Patrol):  {len(self.tcells)}", T_CELL_COLOR)
        ]
        
        for txt, col in stats:
            self.screen.blit(self.font_s.render(txt, True, col), (SIM_WIDTH+20, y))
            y += 35
        
        y += 20
        # Logic Gate status
        gate_txt = "GATE STATUS: ACTIVE" if integrity > 50 else "GATE STATUS: OFFLINE"
        self.screen.blit(self.font_s.render(gate_txt, True, (255, 255, 0)), (SIM_WIDTH+20, y))
        
        self.screen.blit(self.font_s.render("SPACE: PAUSE | R: RESET", True, (150, 150, 150)), (SIM_WIDTH+20, HEIGHT-40))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: self.paused = not self.paused
                    if event.key == pygame.K_r: self.reset()
            self.update()
            self.draw()

if __name__ == "__main__":
    Simulation().run()