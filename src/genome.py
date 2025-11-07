from __future__ import annotations
import math
import random

def logistic_bounded(x: float, lo: float, hi: float) -> float:
    """Map any real x to (lo, hi) via a logistic squashing."""
    return lo + (hi - lo) * (1.0 / (1.0 + math.exp(-x)))

# name: (init_mu, init_sigma, map_fn(low, high))
GENE_SPEC = {
    "rep_gene":   ( 0.0, 1.0, lambda z: logistic_bounded(z, 0.02,  0.50)), # replication_rate (per step max)
    "death_gene": (-3.0, 1.0, lambda z: logistic_bounded(z, 0.000, 0.05)), # baseline death prob per step
    "mut_gene":   (-2.0, 1.0, lambda z: logistic_bounded(z, 0.001, 0.20)), # mutation std for raw alleles
    "met_gene":   ( 0.0, 1.0, lambda z: logistic_bounded(z, 0.05,  0.60)), # metabolism: energy cost per step
}

class Genome:
    """Multi-gene genome with a clear genotype→phenotype map."""
    def __init__(self, rnd: random.Random):
        self.raw = {n: rnd.gauss(mu, sigma) for n, (mu, sigma, _) in GENE_SPEC.items()}

    def phenotype(self):
        return {
            "replication_rate": GENE_SPEC["rep_gene"][2]   (self.raw["rep_gene"]),
            "mutation_rate":    GENE_SPEC["mut_gene"][2]   (self.raw["mut_gene"]),
            "death_rate":       GENE_SPEC["death_gene"][2] (self.raw["death_gene"]),
            "metabolism":       GENE_SPEC["met_gene"][2]   (self.raw["met_gene"]),
        }

    def mutated_copy(self, rnd: random.Random) -> "Genome":
        child = Genome(rnd)
        child.raw = self.raw.copy()
        mr = self.phenotype()["mutation_rate"]
        for name in child.raw:
            scale = 0.35 * mr if name == "mut_gene" else 1.00 * mr
            child.raw[name] = child.raw[name] + rnd.gauss(0.0, scale)
        return child
