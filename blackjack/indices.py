"""Hi-Lo index plays: Illustrious 18 and Fab 4 surrenders (Schlesinger, via Wizard of Odds).

Each entry is (hand, dealer_up, index, play_at_or_above, play_below). Hands are
"16" for hard totals and "TT" for a pair of tens. Dealer ace is 1. These are
multi-deck S17 peek values; no-hole-card games may differ (doubles vs an ace).
"""
from collections import namedtuple

Index = namedtuple("Index", "hand dealer index at_or_above below")

ILLUSTRIOUS_18 = [
    Index("16", 10, 0, "stand", "hit"),
    Index("15", 10, 4, "stand", "hit"),
    Index("TT", 5, 5, "split", "stand"),
    Index("TT", 6, 4, "split", "stand"),
    Index("10", 10, 4, "double", "hit"),
    Index("12", 3, 2, "stand", "hit"),
    Index("12", 2, 3, "stand", "hit"),
    Index("11", 1, 1, "double", "hit"),
    Index("9", 2, 1, "double", "hit"),
    Index("10", 1, 4, "double", "hit"),
    Index("9", 7, 3, "double", "hit"),
    Index("16", 9, 5, "stand", "hit"),
    Index("13", 2, -1, "stand", "hit"),
    Index("12", 4, 0, "stand", "hit"),
    Index("12", 5, -2, "stand", "hit"),
    Index("12", 6, -1, "stand", "hit"),
    Index("13", 3, -2, "stand", "hit"),
]
INSURANCE_INDEX = 3   # the 18th: take insurance / even money at TC >= +3

FAB_4 = [
    Index("14", 10, 3, "surrender", None),
    Index("15", 10, 0, "surrender", None),
    Index("15", 9, 2, "surrender", None),
    Index("15", 1, 1, "surrender", None),
]


def hand_key(ranks):
    """Key for a player's hand: "TT" for ten pairs, else the hard total (None if soft)."""
    if len(ranks) == 2 and ranks[0] == ranks[1] == 10:
        return "TT"
    total = sum(ranks)
    if 1 in ranks and total + 10 <= 21:
        return None   # soft hands have no I18 entry
    return str(total)


def deviation(ranks, dealer_up, true_count, surrender_allowed=False):
    """Return the index play that applies to this hand, or None."""
    key = hand_key(ranks)
    two_cards = len(ranks) == 2
    # Surrender is checked first; below its index it falls through to the I18 play.
    table = (FAB_4 if surrender_allowed and two_cards else []) + ILLUSTRIOUS_18
    for entry in table:
        if entry.hand != key or entry.dealer != dealer_up:
            continue
        if entry.at_or_above in ("double", "split", "surrender") and not two_cards:
            continue
        play = entry.at_or_above if true_count >= entry.index else entry.below
        if play:
            return {"play": play, "index": entry.index, "hand": key, "dealer": dealer_up}
    return None


def take_insurance(true_count):
    return true_count >= INSURANCE_INDEX
