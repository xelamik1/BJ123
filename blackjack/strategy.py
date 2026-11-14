"""Basic strategy plus count-based index plays (6 decks, dealer stands on soft 17).

Defaults: double after split allowed, double any two cards, no surrender.
Index plays come from indices.py (Illustrious 18 / Fab 4) plus the extra double
indices below, which are APPROXIMATE PLACEHOLDERS: verify them by simulation.
"""
from dataclasses import dataclass

from .cards import hand_total
from . import indices

# Dealer upcards 2,3,4,5,6,7,8,9,T,A. D = double else hit, d = double else stand.
HARD = {9: "HDDDDHHHHH", 10: "DDDDDDDDHH", 11: "DDDDDDDDDD", 12: "HHSSSHHHHH",
        13: "SSSSSHHHHH", 14: "SSSSSHHHHH", 15: "SSSSSHHHHH", 16: "SSSSSHHHHH"}
SOFT = {13: "HHHDDHHHHH", 14: "HHHDDHHHHH", 15: "HHDDDHHHHH", 16: "HHDDDHHHHH",
        17: "HDDDDHHHHH", 18: "SddddSSHHH", 19: "SSSSSSSSSS"}
PAIRS = {1: "YYYYYYYYYY", 2: "YYYYYYNNNN", 3: "YYYYYYNNNN", 4: "NNNYYNNNNN",
         6: "YYYYYNNNNN", 7: "YYYYYYNNNN", 8: "YYYYYYYYYY", 9: "YYYYYNYYNN"}
PAIRS_NO_DAS = {2: "NNYYYYNNNN", 3: "NNYYYYNNNN", 4: "NNNNNNNNNN", 6: "NNYYYNNNNN"}

# (hand, dealer, index, play at/above, play below): extra double indices, PLACEHOLDER values.
EXTRA_INDICES = [
    indices.Index("11", 5, -6, "double", "hit"),
    indices.Index("11", 6, -7, "double", "hit"),
    indices.Index("8", 6, 2, "double", "hit"),
    indices.Index("8", 5, 4, "double", "hit"),
]


@dataclass
class StrategySettings:
    das: bool = True
    double_any: bool = True      # False: double only on hard 9-11
    surrender: bool = False

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def rank_name(rank):
    return "A" if rank == 1 else str(rank)


def _col(dealer_up):
    return 9 if dealer_up == 1 else dealer_up - 2


def basic_play(ranks, dealer_up, settings=None, can_split=True, can_double=True):
    """One of hit, stand, double, split, surrender."""
    s = settings or StrategySettings()
    two = len(ranks) == 2
    col = _col(dealer_up)
    total, soft = hand_total(ranks)
    if two and ranks[0] == ranks[1] and can_split:
        table = PAIRS if s.das else {**PAIRS, **PAIRS_NO_DAS}
        if table.get(ranks[0], "N" * 10)[col] == "Y":
            return "split"
    if s.surrender and two and not soft:
        if (total == 16 and dealer_up in (9, 10, 1)) or (total == 15 and dealer_up == 10):
            return "surrender"
    if soft:
        code = SOFT.get(total, "S" if total >= 19 else "H")[col]
    elif total >= 17:
        code = "S"
    elif total <= 8:
        code = "H"
    else:
        code = HARD[total][col]
    if code in "Dd":
        ok = can_double and two and (s.double_any or (not soft and 9 <= total <= 11))
        return "double" if ok else ("hit" if code == "D" else "stand")
    return "stand" if code == "S" else "hit"


def _extra_deviation(ranks, dealer_up, true_count):
    if len(ranks) != 2:
        return None
    key = indices.hand_key(ranks)
    for e in EXTRA_INDICES:
        if e.hand == key and e.dealer == dealer_up:
            play = e.at_or_above if true_count >= e.index else e.below
            return {"play": play, "index": e.index, "hand": key, "dealer": dealer_up}
    return None


def recommend(ranks, dealer_up, true_count, settings=None, can_split=True, can_double=True):
    """Best play: index deviation if one applies, else basic strategy, with the reason."""
    s = settings or StrategySettings()
    base = basic_play(ranks, dealer_up, s, can_split, can_double)
    dev = (indices.deviation(ranks, dealer_up, true_count, s.surrender)
           or _extra_deviation(ranks, dealer_up, true_count))
    play, reason, deviated = base, "basic strategy", False
    if base == "split" and dev and dev["hand"] != "TT":
        dev = None   # a hard-total index does not override splitting a pair
    if dev:
        feasible = not ((dev["play"] == "double" and not can_double)
                        or (dev["play"] == "split" and not can_split)
                        or (dev["play"] == "surrender" and len(ranks) != 2))
        if feasible and dev["play"] != base:
            play, deviated = dev["play"], True
            hand = f"{dev['hand']} vs {rank_name(dealer_up)}"
            if true_count >= dev["index"]:
                reason = f"index: {play} {hand} at TC >= {dev['index']:+g} (TC {true_count:+.1f})"
            else:
                reason = (f"index: {base} {hand} only at TC >= {dev['index']:+g}; "
                          f"TC {true_count:+.1f}, so {play}")
    return {"play": play, "base": base, "deviation": deviated, "reason": reason}
