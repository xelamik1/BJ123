"""Card labels: parse detector class names into (rank, suit)."""
from dataclasses import dataclass
import re

# Rank 1 is an ace; 10 covers T/J/Q/K for counting, but the face is kept for memory.
FACES = {"A": 1, "J": 10, "Q": 10, "K": 10, "T": 10}
SUITS = {"C": "C", "D": "D", "H": "H", "S": "S",
         "CLUBS": "C", "DIAMONDS": "D", "HEARTS": "H", "SPADES": "S"}
BACK_LABELS = {"BACK", "CARD_BACK", "CARDBACK", "FACEDOWN", "FACE_DOWN", "HIDDEN"}
WORD_RANKS = {"ACE": "A", "TWO": "2", "THREE": "3", "FOUR": "4", "FIVE": "5", "SIX": "6",
              "SEVEN": "7", "EIGHT": "8", "NINE": "9", "TEN": "10", "JACK": "J",
              "QUEEN": "Q", "KING": "K"}


@dataclass(frozen=True)
class Card:
    face: str          # "A", "2".."10", "J", "Q", "K"
    suit: str | None   # "C", "D", "H", "S" or None when the model has no suit

    @property
    def rank(self):
        return FACES.get(self.face) or int(self.face)

    @property
    def label(self):
        return self.face + (self.suit or "")


def parse_label(label):
    """Return a Card, or None for a face-down card. Raises ValueError if unknown.

    Accepts "10C", "AH", "Qs", "ace_of_hearts", "10 of clubs", "K".
    """
    text = label.strip().upper().replace("-", "_")
    if text in BACK_LABELS:
        return None
    words = [w for w in re.split(r"[_\s]+", text) if w and w != "OF"]
    if len(words) == 2 and words[1] in SUITS:
        face = WORD_RANKS.get(words[0], words[0])
        return _card(face, SUITS[words[1]], label)
    match = re.fullmatch(r"(10|[2-9]|[AJQKT])([CDHS])?", text)
    if not match:
        raise ValueError(f"unknown card label: {label!r}")
    return _card(match.group(1), match.group(2), label)


def _card(face, suit, label):
    face = "10" if face == "T" else face
    if face not in FACES and not (face.isdigit() and 2 <= int(face) <= 10):
        raise ValueError(f"unknown card label: {label!r}")
    return Card(face, suit)


def hand_total(ranks):
    """Best blackjack total and whether it is soft."""
    total = sum(ranks)
    if 1 in ranks and total + 10 <= 21:
        return total + 10, True
    return total, False
