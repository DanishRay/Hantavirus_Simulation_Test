import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# parameters & ratios
CELL_RADIUS = 0.15
healthy_pos = np.array([0.7, 0.5])
infected_pos = np.array([0.2, 0.5])

# time scaling
HOURS_PER_TICK = 2
INCUBATION_TICKS = 18 

n_virions = 15
virion_pos = np.tile(infected_pos, (n_virions, 1)) + np.random.uniform(-0.05, 0.05, (n_virions, 2))

# states & tracking
state = "Healthy"
incubation_timer = 0
simulation_complete = False # flag to stop the clock
final_hours = 0


# visualization
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')

circle_src = plt.Circle(infected_pos, CELL_RADIUS, color='red', alpha=0.3, label="Source (Infectious)")
circle_target = plt.Circle(healthy_pos, CELL_RADIUS, color='blue', alpha=0.3)
ax.add_patch(circle_src); ax.add_patch(circle_target)

particles, = ax.plot([], [], 'ro', markersize=3, label="Virions")

status_text = ax.text(0.7, 0.7, f"Status: {state}", ha='center', fontweight='bold')
clock_text = ax.text(0.05, 0.95, "Real-Time: 0 hours", transform=ax.transAxes)

ax.set_title("Hantavirus Simulation: Microscopic Entry & Incubation Phase")


# animation
def update(frame):
    global virion_pos, state, incubation_timer, simulation_complete, final_hours
    
    # update clock only if simulation is not complete
    if not simulation_complete:
        final_hours = frame * HOURS_PER_TICK
    
    clock_text.set_text(f"Simulation Time: {final_hours} hours (~{final_hours/24:.1f} days)")

    # virions physic
    step = np.random.normal(0, 1, (n_virions, 2)) * 0.008
    step[:, 0] += 0.006 
    virion_pos += step

    # collison logic
    for i in range(n_virions):
        dist = np.linalg.norm(virion_pos[i] - healthy_pos)
        
        if state == "Healthy" and dist < CELL_RADIUS:
            state = "Exposed (Cap-Snatching)"
            circle_target.set_color('yellow')
            status_text.set_text(f"Status: {state}")
            
        if "Exposed" in state:
            incubation_timer += 1
            if incubation_timer >= INCUBATION_TICKS:
                state = "Infectious (Shedding)"
                circle_target.set_color('red')
                status_text.set_text(f"Status: {state}")
                simulation_complete = True # stops the clock

        if dist < CELL_RADIUS or virion_pos[i, 0] > 1:
            virion_pos[i] = infected_pos + np.random.uniform(-0.02, 0.02, 2)

    particles.set_data(virion_pos[:, 0], virion_pos[:, 1])
    return particles, circle_target, status_text, clock_text


ani = FuncAnimation(fig, update, interval=200, blit=True, cache_frame_data=False)
plt.show()