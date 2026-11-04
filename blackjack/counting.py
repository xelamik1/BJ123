"""Counting systems, shoe composition, true count, edge and bet sizing.

See blackjack/ALGORITHMS.txt for where each number comes from.
"""
from dataclasses import dataclass, field
import math

# Tags indexed by rank 1 (ace) .. 10 (ten-valued). Level-2+ systems with a
# separate ace count are listed with their ace-neutral tags where noted.
SYSTEMS = {
    "hilo":    {1: -1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 0, 8: 0, 9: 0, 10: -1},
    "ko":      {1: -1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 0, 9: 0, 10: -1},
    "hiopt2":  {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 1, 7: 1, 8: 0, 9: 0, 10: -2},
    "omega2":  {1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 1, 8: 0, 9: -1, 10: -2},
    "zen":     {1: -1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 1, 8: 0, 9: 0, 10: -2},
    # Wong Halves uses half points; stored doubled and halved in running_count().
    "halves2": {1: -2, 2: 1, 3: 2, 4: 2, 5: 3, 6: 2, 7: 1, 8: 0, 9: -1, 10: -2},
}
SCALE = {"halves2": 0.5}
BALANCED = {"hilo", "hiopt2", "omega2", "zen", "halves2"}


@dataclass
class ShoeConfig:
    """All values are PLACEHOLDERS until measured at a real table."""
    decks: int = 8
    cards_per_rank_per_deck: dict = field(default_factory=lambda: {
        1: 4, 2: 4, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4, 10: 16})
    penetration: float = 0.5   # fraction of the shoe dealt before the shuffle

    @property
    def cards_per_deck(self):
        return sum(self.cards_per_rank_per_deck.values())

    @property
    def total_cards(self):
        return self.decks * self.cards_per_deck

    @classmethod
    def from_dict(cls, data):
        counts = data.get("cards_per_rank_per_deck")
        kwargs = {k: data[k] for k in ("decks", "penetration") if k in data}
        if counts:
            kwargs["cards_per_rank_per_deck"] = {int(k): int(v) for k, v in counts.items()}
        return cls(**kwargs)


class Shoe:
    """Remaining composition and running counts for one shoe."""

    def __init__(self, config):
        self.config = config
        self.reset()

    def reset(self):
        self.remaining = {r: n * self.config.decks
                          for r, n in self.config.cards_per_rank_per_deck.items()}
        self.seen = 0
        self.anomalies = 0
        self._raw = {name: 0 for name in SYSTEMS}

    def remove(self, rank):
        if self.remaining.get(rank, 0) <= 0:
            # More of a rank than the configured shoe holds: misread or wrong placeholder.
            self.anomalies += 1
        else:
            self.remaining[rank] -= 1
        self.seen += 1
        for name, tags in SYSTEMS.items():
            self._raw[name] += tags[rank]

    def restore(self, rank):
        """Undo a remove() (used when a committed card is corrected)."""
        self.remaining[rank] = self.remaining.get(rank, 0) + 1
        self.seen -= 1
        for name, tags in SYSTEMS.items():
            self._raw[name] -= tags[rank]

    def running_count(self, system="hilo"):
        return self._raw[system] * SCALE.get(system, 1)

    @property
    def cards_left(self):
        return max(self.config.total_cards - self.seen, 0)

    @property
    def decks_left(self):
        return self.cards_left / self.config.cards_per_deck

    @property
    def penetration_dealt(self):
        return self.seen / self.config.total_cards

    @property
    def past_expected_cut(self):
        return self.penetration_dealt > self.config.penetration

    def true_count(self, system="hilo"):
        if system not in BALANCED:
            raise ValueError(f"{system} is unbalanced; use running_count()")
        # Exact decks remaining; floor at a quarter deck so the end of a shoe stays finite.
        return self.running_count(system) / max(self.decks_left, 0.25)

    def probabilities(self):
        left = sum(self.remaining.values())
        return {r: n / left for r, n in self.remaining.items()} if left else {}

    def insurance_ev(self):
        """EV per unit of insurance: pays 2:1 when the hole card is ten-valued."""
        p_ten = self.probabilities().get(10, 0.0)
        return 3 * p_ten - 1


@dataclass
class EdgeModel:
    """Linear edge model: edge = base_edge + per_true_count * TC (PLACEHOLDERS)."""
    base_edge: float = -0.0071      # ~99.29% published RTP
    per_true_count: float = 0.005   # ~0.5% per Hi-Lo true count
    variance: float = 1.30          # per-hand variance, 6-8 decks

    def edge(self, true_count):
        return self.base_edge + self.per_true_count * true_count

    def break_even_true_count(self):
        return -self.base_edge / self.per_true_count

    def kelly_bet(self, true_count, bankroll, fraction=0.5):
        edge = self.edge(true_count)
        return 0.0 if edge <= 0 else bankroll * fraction * edge / self.variance

    def n0(self, edge):
        return self.variance / edge ** 2

    def risk_of_ruin(self, edge, bankroll_units):
        """Flat-bet approximation exp(-2 * EV * bankroll / variance)."""
        return 1.0 if edge <= 0 else math.exp(-2 * edge * bankroll_units / self.variance)
