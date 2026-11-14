"""Finished-round history read from the SQLite memory, with win/loss results."""
from .cards import hand_total


def _total(ranks):
    return hand_total(ranks)[0]


def round_result(player_ranks, dealer_ranks, split=False):
    """WIN / LOSS / PUSH / BJ / BUST, or None while the dealer's hand is unfinished.

    BJ is a two-card 21 on an unsplit hand; the dealer's own two-card 21 beats
    a non-BJ 21 and pushes a BJ.
    """
    player = _total(player_ranks)
    if player > 21:
        return "BUST"
    if not dealer_ranks:
        return None
    dealer = _total(dealer_ranks)
    player_bj = len(player_ranks) == 2 and player == 21 and not split
    dealer_bj = len(dealer_ranks) == 2 and dealer == 21
    if dealer_bj:
        return "PUSH" if player_bj else "LOSS"
    if player_bj:
        return "BJ"
    if dealer > 21:
        return "WIN"
    if dealer < 17:
        return None
    return "WIN" if player > dealer else "LOSS" if player < dealer else "PUSH"


def recent_rounds(memory, table_id, limit=20):
    """Newest finished rounds: dealer cards and every seat's hands with results."""
    rounds = memory.db.execute(
        "SELECT id, shoe_id, round_no, started_at FROM rounds WHERE table_id=? AND ended_at IS NOT NULL"
        " AND EXISTS (SELECT 1 FROM cards c WHERE c.round_id=rounds.id AND c.void=0)"
        " ORDER BY id DESC LIMIT ?", (table_id, limit)).fetchall()
    out = []
    for r in rounds:
        hands = {}
        for c in memory.round_cards(r["id"]):
            hands.setdefault(c["zone"], {}).setdefault(c["hand_index"], []).append((c["label"], c["rank"]))
        dealer = [x for h in hands.pop("dealer", {}).values() for x in h]
        dealer_ranks = [rank for _, rank in dealer]
        seats = {}
        for zone, by_hand in sorted(hands.items()):
            split = len(by_hand) > 1
            seats[zone] = [{"cards": [l for l, _ in h], "total": _total([k for _, k in h]),
                            "result": round_result([k for _, k in h], dealer_ranks, split)}
                           for _, h in sorted(by_hand.items())]
        out.append({"round_id": r["id"], "shoe_id": r["shoe_id"], "round_no": r["round_no"],
                    "started_at": r["started_at"],
                    "dealer": {"cards": [l for l, _ in dealer],
                               "total": _total(dealer_ranks) if dealer_ranks else None},
                    "seats": seats})
    return out
