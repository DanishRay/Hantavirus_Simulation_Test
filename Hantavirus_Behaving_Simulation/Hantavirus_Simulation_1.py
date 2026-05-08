import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
import matplotlib.lines as mlines

# parameters
n_cells = 200
grid_size = 20
infect_radius = 3.5
prob_infect = 0.3
expose_time = 15        # 15 ticks = 30-54 hours

# states
susceptible, exposed, infectious = 0, 1, 2
colors = {susceptible: 'blue', exposed: 'yellow', infectious: 'red'}

# initialization
pos = np.random.uniform(0, grid_size, (n_cells, 3))
states = np.zeros(n_cells, dtype=int)
timers = np.zeros(n_cells, dtype=int)
states[0] = infectious


# visualization setup
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
plt.subplots_adjust(bottom=0.2, right=0.75)

sc = ax.scatter(pos[:, 0], pos[:, 1], pos[:, 2], c='blue', s=60, edgecolors='black', alpha=0.7)

ax.set_title('Hantavirus Behavior Model Test 1', pad=20)
ax.set_xlabel('x-axis Tissue')
ax.set_ylabel('y-axis Tissue')
ax.set_zlabel('z-axis Tissue')

blue_dot = mlines.Line2D([], [], color='blue', marker='o', linestyle='None', markersize=10, label='Healthy')
yellow_dot = mlines.Line2D([], [], color='yellow', marker='o', linestyle='None', markersize=10, label='Exposed')
red_dot = mlines.Line2D([], [], color='red', marker='o', linestyle='None', markersize=10, label='Infectious')


# controls
paused = False

def pause_sim(event):
    global paused
    paused = not paused
    btn_pause.label.set_text('Resume' if paused else 'Pause')

def reset_sim(event):
    global states, timers
    states[:] = susceptible
    timers[:] = 0
    states[np.random.randint(0, n_cells)] = infectious

ax_pause = plt.axes([0.55, 0.05, 0.1, 0.06])
ax_reset = plt.axes([0.67, 0.05, 0.1, 0.06])
btn_pause = Button(ax_pause, 'Pause')
btn_reset = Button(ax_reset, 'Reset')
btn_pause.on_clicked(pause_sim)
btn_reset.on_clicked(reset_sim)


# update loop
def update(frame):
    global states, timers
    if paused: return sc,

    new_states = states.copy()
    inf_idx = np.where(states == infectious)[0]
    
    for i in range(n_cells):
        if states[i] == susceptible:
            for j in inf_idx:
                if np.linalg.norm(pos[i] - pos[j]) < infect_radius:
                    if np.random.random() < prob_infect:
                        new_states[i] = exposed
                        break
        elif states[i] == exposed:
            timers[i] += 1
            if timers[i] >= expose_time:
                new_states[i] = infectious

    states = new_states
    sc.set_color([colors[s] for s in states])

    # Dynamic Label Logic
    s_count = np.sum(states == susceptible)
    e_count = np.sum(states == exposed)
    i_count = np.sum(states == infectious)
    
    # Update the legend with live counts
    ax.legend(handles=[blue_dot, yellow_dot, red_dot], 
              labels=[f"Healthy: {s_count}", f"Exposed: {e_count}", f"Infectious: {i_count}"],
              title="Population Count",
              loc="upper left", bbox_to_anchor=(1.05, 1))

    return sc,

ani = FuncAnimation(fig, update, interval=100, cache_frame_data=False)
plt.show()