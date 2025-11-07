from __future__ import annotations
import mesa
from mesa.visualization.solara_viz import SolaraViz

class Walker(mesa.Agent):
    """Picks a random neighboring cell each step."""
    def __init__(self, model):
        super().__init__(model)

    def step(self):
        neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=True
        )
        new_pos = self.random.choice(neighborhood)
        self.model.grid.move_agent(self, new_pos)

class TinyWorld(mesa.Model):
    """10x10 torus with N random walkers."""
    def __init__(self, width=10, height=10, N=8, seed=None):
        super().__init__(seed=seed)
        self.grid = mesa.space.MultiGrid(width, height, torus=True)

        for _ in range(N):
            a = Walker(self)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

    def step(self):
        self.agents.shuffle_do("step")

# Create the model instance
model = TinyWorld(width=10, height=10, N=8, seed=42)

# Create the visualization page
page = SolaraViz(model, components="default")
