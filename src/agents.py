from __future__ import annotations
from typing import Optional, Tuple
import random
from mesa import Agent
from .genome import Genome

class ResourcePatch(Agent):
    """A simple resource patch with logistic-like regrowth."""
    def __init__(self, model, cap: float = 10.0, regrowth: float = 0.10, init: float = 5.0):
        super().__init__(model)
        self.cap = cap
        self.regrowth = regrowth
        self.amount = max(0.0, min(cap, init))

    def step(self):
        # logistic-ish regrowth towards capacity
        self.amount += self.regrowth * (self.cap - self.amount)
        if self.amount > self.cap:
            self.amount = self.cap
        if self.amount < 0.0:
            self.amount = 0.0

class ReplicatorAgent(Agent):
    """Replicators move, harvest, pay metabolic cost, die or replicate."""
    def __init__(self, model, genome: Genome, energy: float, lineage_id: int):
        super().__init__(model)
        self.genome = genome
        self.energy = energy
        self.lineage_id = lineage_id

    def traits(self):
        return self.genome.phenotype()

    def step(self):
        if self.energy <= 0.0:
            self.model.to_remove.add(self)
            return

        t = self.traits()

        # 1) Move to a random Moore neighbor (torus grid)
        neighborhood = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True, radius=1)
        new_pos = self.random.choice(neighborhood)
        self.model.grid.move_agent(self, new_pos)

        # 2) Harvest from the patch underfoot
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        patch = next((o for o in cellmates if isinstance(o, ResourcePatch)), None)
        if patch is not None:
            # intake scales with inverse metabolism (crude efficiency proxy)
            base_intake = 1.0 / (1.0 + t["metabolism"])
            intake = min(patch.amount, base_intake * self.random.uniform(0.8, 1.2))
            patch.amount -= intake
            if patch.amount < 0.0:
                patch.amount = 0.0
            self.energy += intake

        # 3) Pay metabolism
        self.energy -= t["metabolism"]

        # 4) Baseline death
        if self.random.random() < t["death_rate"] or self.energy <= 0.0:
            self.model.to_remove.add(self)
            return

        # 5) Replication: need surplus energy + Bernoulli gate
        if self.energy > 1.5:
            p = t["replication_rate"] * min(1.0, (self.energy - 1.5) / 2.0)
            if self.random.random() < p:
                # find an empty neighbor cell to place child if possible
                neighbors = list(self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False, radius=1))
                self.random.shuffle(neighbors)
                child_pos = None
                for pos in neighbors:
                    child_pos = pos
                    break

                child_genome = self.genome.mutated_copy(self.random)
                child_energy = self.energy * 0.5
                self.energy *= 0.5
                child = ReplicatorAgent(self.model, child_genome, child_energy, self.lineage_id)
                self.model.grid.place_agent(child, child_pos if child_pos else self.pos)
                self.model.register_birth(self.lineage_id)
