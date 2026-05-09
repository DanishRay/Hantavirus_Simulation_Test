# Hantavirus Behavior Simulation

This sub-repository contains a technical simulation focused on the movement and infection patterns of the Hantavirus at a cellular level. The project models how the virus interacts with healthy cells and spreads within a controlled tissue environment.

## Project Scope

The current version of this simulation focuses exclusively on **viral behavior**. It is designed to track the transition of cells through different states of infection based on proximity and time.

* **Cell States:** Models the change from healthy (susceptible) to exposed and eventually infectious states.
* **Infection Logic:** Simulates viral shedding and the physical spread of virions between cells.
* **Environmental Interaction:** Tracks how the virus moves through a 3D tissue grid and reacts to specific distance parameters.

**Note:** This model does not currently include immune system responses, medical treatments, or other complex biological characteristics. It is a dedicated study of viral spread mechanics.

## Technical Summary

The simulation uses mathematical logic to determine the probability of infection. Key features include:

* **Microscopic Modeling:** Visualizes individual virion particles moving toward target cells.
* **Incubation Tracking:** Uses a timer system to model the "cap-snatching" phase and the time required for a cell to become infectious.
* **Population Data:** Provides real-time counts of healthy versus infected cells within the simulation environment.

## Ongoing Development

This project is updated frequently. Future updates will refine the movement models and add more variables regarding the physical environment. 
