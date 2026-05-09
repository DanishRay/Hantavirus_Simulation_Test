import pygame
import random
import math
import time

# configuration
width, height = 1150, 750
fps = 60
cell_radius = 210
nucleus_radius = 65
virus_radius = 9
interferon_color = (255, 180, 180)

# colors
white = (255, 255, 255)
cytoplasm_color = (245, 222, 179)
membrane_color = (101, 67, 33)
virus_color = (46, 139, 87)
nucleus_color = (70, 130, 180)
ui_big = (40, 44, 52)


class virion:
    def __init__(self, x, y, state = 'SEARCHING'):
        self.x = x
        self.y = y
        self.state = state
        self.timer = 0
        self.angle = random.uniform(0, 2 * math.pi)

    def move_levy(self):
        # levy flight search pattern
        if self.state == 'SEARCHING':
            step_size = random.uniform(20, 50) if random.random() > 0.96 else random.uniform(1, 4)
            self.angle += random.uniform(-0.6, 0.6)
            self.x += math.cos(self.angle) * step_size
            self.y += math.sin(self.angle) * step_size
            self.x %= width
            self.y %= height
        
    def draw (self, surface):
        # representing fatty envelope
        color = (218, 165, 32) if self.state == "INTERNAL" else virus_color
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), virus_radius)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x), int(self.y)), virus_radius, 2)


class simulation :
    def __init__(self):
        self.reset()

    def reset(self):
        self.center = (width // 2 + 120, height // 2)
        self.virions = [virion(random.randint(350, width), random.randint(0, height)) for _ in range(10)]
        self.attached_count = 0
        self.internal_rna = 0
        self.shed_count = 0
        self.caps_snatched = 0 
        self.is_alarmed = False
        self.paused = False
        self.replication_timer = 0
        self.start_ticks = pygame.time.get_ticks()
        self.total_paused_ticks = 0
        self.pause_start_tick = 0

    def update(self):
        if self.paused: return
        self.elapsed_sim_seconds = (pygame.time.get_ticks() - self.start_ticks - self.total_paused_ticks) / 1000
        cell_x, cell_y = self.center

        for v in self.virions[:]:
            if v.state == 'SEARCHING':
                v.move_levy()
                if math.hypot(v.x - cell_x, v.y - cell_y) < cell_radius:
                    v.state = 'ATTACHED' # binding to B3 Integrins
                    self.attached_count += 1
            
            elif v.state == 'ATTACHED':
                v.timer += 1
                if v.timer > 50:    # entry phase
                    v.state = 'INTERNAL'
                    v.x, v.y = cell_x + random.randint(-80, 80), cell_y + random.randint(-80, 80)

            elif v.state == 'INTERNAL':
                # movement restricted to cytoplasm, avoiding nucleus
                v.x += random.uniform(-1.5, 1.5)
                v.y += random.uniform(-1.5, 1.5)
                dist = math.hypot(v.x - cell_x, v.y - cell_y)
                if dist > cell_radius - 15: v.x -= (v.x - cell_x) * 0.1
                if dist < nucleus_radius + 10: v.x += (v.x - cell_x) * 0.1

                # RdRp cap-snatching from host mRNA
                if random.random() > 0.985:
                    self.caps_snatched += 1
                    self.internal_rna += 0.4

                # sensing by RIG-I / MDA5
                if self.internal_rna > 12 : self.is_alarmed = True

        # persistent budding from membrane
        if self.internal_rna > 15:
            self.replication_timer += 1
            if self.replication_timer > 110:
                angle = random.uniform(0, 2*math.pi)
                self.virions.append(virion(cell_x + math.cos(angle)*cell_radius, 
                                           cell_y + math.sin(angle)*cell_radius, "SEARCHING"))
                self.shed_count += 1
                self.replication_timer = 0

    def draw_ui(self, screen):
        # ui panel background
        pygame.draw.rect(screen, ui_big, (0, 0, 320, height))
        pygame.draw.line(screen, white, (320, 0), (320, height), 3)

        f_bold = pygame.font.SysFont('Arial', 22, bold=True)
        f_reg = pygame.font.SysFont('Arial', 18)
        
        # real time correlate (1s = 1hr)
        time_text = f"Infection Time: {int(self.elapsed_sim_seconds)}h {int((self.elapsed_sim_seconds%1)*60)}m"
        screen.blit(f_bold.render(time_text, True, (0, 255, 0)), (20, 20))

        # object logos and data
        y_off = 70
        items = [
            ("●", virus_color, "Virion (Gn/Gc Keys)", f"Bound: {self.attached_count}"),
            ("截", (255, 165, 0), "RdRp (Cap-Snatching)", f"Caps Stolen: {self.caps_snatched}"),
            ("≈", (100, 200, 255), "Viral RNA (Cytoplasm)", f"Conc: {int(self.internal_rna)} units"),
            ("↑", white, "Budding (Viral Shed)", f"Shed count: {self.shed_count}"),
        ]

        for logo, color, title, data in items:
            screen.blit(f_bold.render(logo, True, color), (20, y_off))
            screen.blit(f_reg.render(title, True, white), (50, y_off))
            screen.blit(f_reg.render(data, True, (200, 200, 200)), (50, y_off + 22))
            y_off += 65

        
        # defense system signaling
        pygame.draw.rect(screen, (60, 60, 60), (15, y_off, 290, 80))
        status = "SIGNALING: Type I Interferon" if self.is_alarmed else "SCANNING: RIG-I/MDA5"
        color = (255, 100, 100) if self.is_alarmed else (100, 255, 100)
        screen.blit(f_reg.render("Immune Response:", True, white), (25, y_off + 10))
        screen.blit(f_bold.render(status, True, color), (25, y_off + 35))
    
    def draw (self, screen):
        bg = interferon_color if self.is_alarmed else cytoplasm_color
        pygame.draw.circle(screen, bg, self.center, cell_radius)
        pygame.draw.circle(screen, membrane_color, self.center, cell_radius, 6) # endothelial wall
        pygame.draw.circle(screen, nucleus_color, self.center, nucleus_radius)
        for v in self.virions: v.draw(screen)
        self.draw_ui(screen)


def main():
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Hantavirus Virology Simulation 3: Host-Cell Interaction Sim")
    clock = pygame.time.Clock()
    sim = simulation()
    while True:
        screen.fill((20, 20, 25))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    sim.paused = not sim.paused
                    if sim.paused: sim.pause_start_tick = pygame.time.get_ticks()
                    else: sim.total_paused_ticks += (pygame.time.get_ticks() - sim.pause_start_tick)
                if event.key == pygame.K_r: sim.reset()
        sim.update()
        sim.draw(screen)
        pygame.display.flip()
        clock.tick(fps)

if __name__ == '__main__': main()
