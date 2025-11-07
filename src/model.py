from __future__ import annotations
from typing import Dict
from collections import defaultdict
import random
import numpy as np

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

from .genome import Genome
from .agents import ResourcePatch, ReplicatorAgent

class ReplicatorWorld(Model):
    def __init__(self, width=40, height=40, seed=7, founders=10, steps=600,
                 patch_cap=10.0, patch_regrowth=0.10, init_patch=5.0,
                 max_agents=20000):
        super().__init__()
        self.seed = seed
        self.random = random.Random(seed)
        np.random.seed(seed)

        self.grid = MultiGrid(width, height, torus=True)
        self.steps = steps
        self.max_agents = max_agents

        self.to_remove = set()
        self.lineage_births: Dict[int, int] = defaultdict(int)
        self.history_lineage_counts: Dict[int, list] = defaultdict(list)
        self.lineage_founder_genes: Dict[int, Dict] = {}

        # add patches (one per grid cell)
        for x in range(width):
            for y in range(height):
                p = ResourcePatch(self, cap=patch_cap, regrowth=patch_regrowth, init=init_patch)
                self.grid.place_agent(p, (x, y))

        # seed initial replicators at random positions with distinct lineages
        for lin in range(founders):
            g = Genome(self.random)
            a = ReplicatorAgent(self, g, energy=2.0, lineage_id=lin)
            # Store founder genes
            self.lineage_founder_genes[lin] = g.phenotype()
            self.grid.place_agent(a, (self.random.randrange(width), self.random.randrange(height)))

        self.datacollector = DataCollector(
            model_reporters={
                "N": lambda m: sum(1 for a in m.agents if isinstance(a, ReplicatorAgent)),
                "lineages": lambda m: dict(self._count_lineages_alive())
            }
        )

    def register_birth(self, lineage_id: int):
        self.lineage_births[lineage_id] += 1

    def _count_lineages_alive(self):
        counts = defaultdict(int)
        for a in self.agents:
            if isinstance(a, ReplicatorAgent):
                counts[a.lineage_id] += 1
        return counts

    def step(self):
        # Remove flagged agents (deaths)
        for a in list(self.to_remove):
            self.grid.remove_agent(a)
            self.deregister_agent(a)
        self.to_remove.clear()

        # Step all agents in random order (Mesa 3.3 style)
        agents_to_step = list(self.agents)
        self.random.shuffle(agents_to_step)
        for agent in agents_to_step:
            agent.step()

        # After step, record lineage counts
        counts = self._count_lineages_alive()
        for lin, c in counts.items():
            self.history_lineage_counts[lin].append(int(c))
        # also keep 0 for absent lineages to align lengths
        for lin in list(self.history_lineage_counts.keys()):
            if lin not in counts:
                self.history_lineage_counts[lin].append(0)

        self.datacollector.collect(self)

    def run(self):
        for _ in range(self.steps):
            alive = sum(1 for a in self.agents if isinstance(a, ReplicatorAgent))
            if alive == 0:
                break
            if alive > self.max_agents:
                break
            self.step()
        return self.datacollector.get_model_vars_dataframe()
