import pygame
import random
import math
import pandas as pd
import numpy as np
from datetime import datetime

# constant
WIDTH, HEIGHT = 1150, 750
SIDEBAR_WIDTH = 320
GRID_SIZE = 25
FPS = 30 

# Colors
BG_COLOR = (10, 12, 18)
UI_BG = (28, 30, 38)
WHITE = (220, 230, 240)
HEALTHY_COLOR = (0, 150, 255)    
REPLICATION_COLOR = (255, 165, 0) 
INFECTED_COLOR = (200, 80, 255)  
APOPTOTIC_COLOR = (60, 60, 70)   
VIRION_COLOR = (255, 255, 0)     
TCELL_COLOR = (0, 255, 120)      
INTERFERON_COLOR = (0, 255, 150)


class EndothelialCell:
    def __init__(self, x, y, cell_id):
        self.id = cell_id
        self.pos = pygame.Vector2(x, y)
        self.rect = pygame.Rect(x-10, y-10, 20, 20)
        self.state = "Healthy"
        
        # biological factors
        self.beta3_density = random.uniform(0.7, 0.95)
        self.replication_timer = 0
        self.interferon_level = 0
        self.chemokine_level = 0 # CXCL9/CXCL10 signal strength

    def update(self):
        if self.state == "Replication":
            self.replication_timer -= 1
            if self.replication_timer <= 0:
                self.state = "Shedding"
        
        if self.state == "Shedding":
            self.chemokine_level = min(1.0, self.chemokine_level + 0.02)
            self.interferon_level = min(1.0, self.interferon_level + 0.01)

    def draw(self, screen):
        color = HEALTHY_COLOR
        if self.state == "Replication": color = REPLICATION_COLOR
        if self.state == "Shedding": color = INFECTED_COLOR
        if self.state == "Apoptotic": color = APOPTOTIC_COLOR
        pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), 10)
        
        if self.interferon_level > 0.5:
            pygame.draw.circle(screen, INTERFERON_COLOR, (int(self.pos.x), int(self.pos.y)), 13, 1)

class CD8TCell:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.speed = 2.2
        self.scanning_target = None
        self.scan_timer = 0

    def move(self, cells):
        if self.scanning_target:
            self.scan_timer -= 1
            if self.scan_timer <= 0:
                if self.scanning_target.state in ["Replication", "Shedding"]:
                    self.scanning_target.state = "Apoptotic"
                self.scanning_target = None
            return

        # chemotaxis: Move towards highest chemokine signal
        target = None
        max_sig = 0
        for c in cells:
            dist = self.pos.distance_to(c.pos)
            if dist < 200 and c.chemokine_level > max_sig:
                max_sig = c.chemokine_level
                target = c
        
        if target:
            dir = (target.pos - self.pos).normalize()
            self.pos += dir * self.speed
            if self.pos.distance_to(target.pos) < 15:
                self.scanning_target = target
                self.scan_timer = 30 # TCR Scanning time
        else:
            self.pos += pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_sm = pygame.font.SysFont("Consolas", 14)
        self.font_md = pygame.font.SysFont("Consolas", 18, bold=True)
        self.font_lg = pygame.font.SysFont("Consolas", 24, bold=True)
        
        # UI Buttons
        self.btn_pause = pygame.Rect(20, 620, 135, 45)
        self.btn_reset = pygame.Rect(165, 620, 135, 45)
        self.btn_export = pygame.Rect(20, 675, 280, 45)
        
        self.data_history = []
        self.reset()

    def reset(self):
        self.paused = True
        self.ticks = 0
        self.cells = []
        for y in range(60, HEIGHT - 60, GRID_SIZE + 10):
            for x in range(SIDEBAR_WIDTH + 60, WIDTH - 60, GRID_SIZE + 10):
                self.cells.append(EndothelialCell(x, y, len(self.cells)))
        
        self.virions = [pygame.Vector2(random.randint(SIDEBAR_WIDTH, WIDTH), random.randint(0, HEIGHT)) for _ in range(5)]
        self.tcells = [CD8TCell(random.randint(SIDEBAR_WIDTH, WIDTH), random.randint(0, HEIGHT)) for _ in range(4)]

    def export_power_bi(self):
        # preparing raw data and metrics logs
        raw_data = []
        for c in self.cells:
            raw_data.append({
                "Tick": self.ticks,
                "Sim_Hour": self.ticks // 60,
                "Cell_ID": c.id,
                "Status": c.state,
                "Interferon": c.interferon_level,
                "Chemokine": c.chemokine_level
            })
        
        summary_data = [{
            "Timestamp": datetime.now(),
            "Total_Virions": len(self.virions),
            "Active_TCells": len(self.tcells),
            "Total_Infected": sum(1 for c in self.cells if c.state != "Healthy")
        }]

        filename = f"Hantavirus_Analysis_{datetime.now().strftime('%H%M%S')}.xlsx"
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            pd.DataFrame(raw_data).to_excel(writer, sheet_name='Simulation_Logs', index=False)
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary_Stats', index=False)
        print(f"Data Exported to {filename}")

    def draw_ui(self):
        pygame.draw.rect(self.screen, UI_BG, (0, 0, SIDEBAR_WIDTH, HEIGHT))
        self.screen.blit(self.font_lg.render("Simulation Model 3.5", True, WHITE), (20, 30))
        
        # real-time simulation clock (1 sec real = 1 hour sim)
        sim_h = self.ticks // 60
        sim_m = (self.ticks % 60)
        self.screen.blit(self.font_md.render(f"SIM TIME: {sim_h:02d}:{sim_m:02d} HOURS", True, INTERFERON_COLOR), (20, 70))

        # object counters
        stats = [
            (HEALTHY_COLOR, f"Endothelial: {len([c for c in self.cells if c.state=='Healthy'])}"),
            (INFECTED_COLOR, f"Shedding Cells: {len([c for c in self.cells if c.state=='Shedding'])}"),
            (VIRION_COLOR, f"Virions: {len(self.virions)}"),
            (TCELL_COLOR, f"CD8+ T-Cells: {len(self.tcells)}")
        ]
        for i, (col, txt) in enumerate(stats):
            pygame.draw.rect(self.screen, col, (20, 130 + i*35, 15, 15))
            self.screen.blit(self.font_sm.render(txt, True, WHITE), (45, 130 + i*35))

        # button
        for btn, label, color in [(self.btn_pause, "PAUSE/PLAY", (60, 65, 80)), 
                                  (self.btn_reset, "RESET", (100, 40, 40)),
                                  (self.btn_export, "EXPORT (.xlsx)", (40, 90, 60))]:
            pygame.draw.rect(self.screen, color, btn, border_radius=5)
            pygame.draw.rect(self.screen, WHITE, btn, 1, border_radius=5)
            txt_surf = self.font_sm.render(label, True, WHITE)
            self.screen.blit(txt_surf, (btn.centerx - txt_surf.get_width()//2, btn.centery - 7))

    def run(self):
        running = True
        while running:
            self.screen.fill(BG_COLOR)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_pause.collidepoint(event.pos): self.paused = not self.paused
                    if self.btn_reset.collidepoint(event.pos): self.reset()
                    if self.btn_export.collidepoint(event.pos): self.export_power_bi()

            if not self.paused:
                self.ticks += 1
                # virion logic
                for v in self.virions[:]:
                    v += pygame.Vector2(random.uniform(-4, 4), random.uniform(-4, 4))
                    for c in self.cells:
                        if c.state == "Healthy" and c.pos.distance_to(v) < 12:
                            if random.random() < c.beta3_density:
                                c.state = "Replication"
                                c.replication_timer = 90
                                if v in self.virions: self.virions.remove(v)

                for c in self.cells:
                    c.update()
                    if c.state == "Shedding" and random.random() < 0.03:
                        self.virions.append(pygame.Vector2(c.pos.x, c.pos.y))

                for t in self.tcells:
                    t.move(self.cells)

            # environment
            for c in self.cells: c.draw(self.screen)
            for v in self.virions: pygame.draw.circle(self.screen, VIRION_COLOR, (int(v.x), int(v.y)), 2)
            for t in self.tcells:
                pygame.draw.polygon(self.screen, (255, 255, 255) if t.scanning_target else TCELL_COLOR, 
                                   [(t.pos.x, t.pos.y-8), (t.pos.x-6, t.pos.y+6), (t.pos.x+6, t.pos.y+6)])

            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    Simulation().run()