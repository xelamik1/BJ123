"""Per-table tracker: turns per-frame detections into cards counted once.

Each card on the felt becomes a track tied to a zone (dealer or a seat). A
track is committed to the count and to memory after it has been seen for
`stable_frames` frames, and stays in memory after it leaves the screen. Later
votes can correct a committed card; the count and the database follow.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import time

from .cards import Card, hand_total, parse_label
from .counting import EdgeModel, Shoe
from . import indices


@dataclass
class Detection:
    label: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def center(self):
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2


@dataclass
class TrackerSettings:
    """Pixel and frame values are PLACEHOLDERS; tune them per table layout."""
    zones: dict                       # name -> [x, y, w, h] in table-region pixels
    stable_frames: int = 3            # frames before a card is counted
    min_confidence: float = 0.60      # detections below this are ignored
    review_confidence: float = 0.70   # committed cards below this are sent for review
    merge_distance: float = 90.0      # same label this close = one card (corner boxes)
    match_distance: float = 60.0      # how far a card may move between frames
    hand_gap: float = 120.0           # x gap that separates split hands in one seat
    correction_margin: float = 1.5    # vote ratio needed to change a committed card
    empty_frames_round_end: int = 15  # empty frames that end a round
    shuffle_frames: int = 5           # frames of shuffle signal that start a new shoe
    idle_seconds_new_shoe: float = 0  # >0: start a new shoe after this long with no cards
    resume_max_gap_seconds: float = 120.0
    wong_in: float = 3.0              # alert at or above this Hi-Lo true count
    wong_out: float = 1.5             # leave below this
    my_seat: str | None = None
    surrender_allowed: bool = False

    @classmethod
    def from_dict(cls, data):
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class Track:
    id: int
    zone: str
    x: float
    y: float
    votes: dict = field(default_factory=dict)
    frames: int = 0
    last_frame: int = 0
    card_id: int | None = None      # memory row once committed
    card: Card | None = None
    hand_index: int = 0
    position: int = 0
    review_requested: bool = False

    def best(self):
        if not self.votes:
            return None, 0.0
        label = max(self.votes, key=self.votes.get)
        return label, self.votes[label]

    def mean_confidence(self, label):
        return self.votes.get(label, 0.0) / max(self.frames, 1)


class TableTracker:
    def __init__(self, table_id, settings, shoe_config, memory, edge=None, review=None):
        self.table_id = table_id
        self.settings = settings
        self.memory = memory
        self.edge = edge or EdgeModel()
        self.review = review          # callable(tracker, track) for low-confidence cards
        self.shoe = Shoe(shoe_config)
        self.tracks = []
        self.frame_no = 0
        self.empty_frames = 0
        self.shuffle_frames = 0
        self.last_card_time = None
        self.round_id = None
        self.round_no = 0
        self._next_track = 1
        self._zone_positions = {}
        self._past_cut_flagged = False
        self._restore()

    # Shoe lifecycle ---------------------------------------------------------
    def _restore(self):
        row = self.memory.open_shoe_for(self.table_id)
        if row is None:
            # Joined mid-shoe: cards already dealt are unknown until the next shuffle.
            self.shoe_id = self.memory.open_shoe(
                self.table_id, "tracker start", reliable=False,
                unreliable_reason="started mid-shoe; wait for the next shuffle")
            return
        self.shoe_id = row["id"]
        cards = self.memory.shoe_cards(self.shoe_id)
        for card_row in cards:
            self.shoe.remove(card_row["rank"])
        if cards:
            last = datetime.fromisoformat(cards[-1]["seen_at"])
            gap = (datetime.now(timezone.utc) - last).total_seconds()
            if gap > self.settings.resume_max_gap_seconds:
                self.memory.mark_unreliable(self.shoe_id, f"resumed after {gap:.0f}s gap")
        open_round = self.memory.open_round_for(self.shoe_id)
        if open_round is not None:
            # Rebuild tracks for cards still on the felt so they are not counted twice.
            self.round_id, self.round_no = open_round["id"], open_round["round_no"]
            for card_row in self.memory.round_cards(self.round_id):
                track = self._new_track(card_row["zone"], card_row["x"] or 0, card_row["y"] or 0)
                track.card_id = card_row["id"]
                track.card = parse_label(card_row["label"])
                track.votes[card_row["label"]] = (card_row["confidence"] or 1) * self.settings.stable_frames
                track.frames = self.settings.stable_frames
                track.hand_index, track.position = card_row["hand_index"], card_row["position"]
                self._zone_positions[track.zone] = max(self._zone_positions.get(track.zone, 0),
                                                       track.position + 1)
        self.memory.event(self.table_id, "resume", f"{len(cards)} cards", self.shoe_id)

    def new_shoe(self, reason):
        self._end_round()
        self.memory.close_shoe(self.shoe_id, reason)
        self.shoe_id = self.memory.open_shoe(self.table_id, reason)
        self.shoe.reset()
        self._past_cut_flagged = False
        self.memory.event(self.table_id, "new_shoe", reason, self.shoe_id)

    @property
    def reliable(self):
        row = self.memory.shoe(self.shoe_id)
        return bool(row["reliable"]) and self.shoe.anomalies == 0

    # Frame processing ------------------------------------------------------
    def update(self, detections, shuffle_signal=False, now=None):
        """Feed one frame. Returns a list of event strings."""
        now = time.monotonic() if now is None else now
        self.frame_no += 1
        events = []
        if shuffle_signal:
            self.shuffle_frames += 1
            if self.shuffle_frames == self.settings.shuffle_frames:
                self.new_shoe("shuffle signal")
                events.append("new_shoe")
            return events
        self.shuffle_frames = 0

        found = self._zoned(detections)
        if not found:
            self.empty_frames += 1
            if self.empty_frames == self.settings.empty_frames_round_end and self.round_id:
                self._end_round()
                events.append("round_end")
            idle = self.settings.idle_seconds_new_shoe
            if idle and self.last_card_time is not None and now - self.last_card_time > idle:
                self.new_shoe("idle timeout")
                self.last_card_time = None
                events.append("new_shoe")
            return events
        self.empty_frames = 0

        for zone, label, conf, x, y in found:
            track = self._match(zone, x, y)
            track.x, track.y = x, y
            track.votes[label] = track.votes.get(label, 0.0) + conf
            track.frames += 1
            track.last_frame = self.frame_no
        for track in self.tracks:
            events.extend(self._settle(track, now))
        if self.shoe.past_expected_cut and not self._past_cut_flagged:
            self._past_cut_flagged = True
            self.memory.event(self.table_id, "past_cut",
                              f"{self.shoe.seen} cards seen; check for a missed shuffle",
                              self.shoe_id)
            events.append("past_cut")
        return events

    def _zoned(self, detections):
        """Merge corner boxes across the whole frame, then place each card in a zone.

        Merging first matters: a card's two corner boxes can fall in neighbouring
        zones, and zoning them separately would count one card twice.
        """
        cards = []
        for det in detections:
            if det.confidence < self.settings.min_confidence:
                continue
            try:
                parse_label(det.label)
            except ValueError:
                continue
            cards.append((det.label.strip().upper(), det.confidence) + det.center)
        out = []
        for label, conf, x, y in self._merge(cards):
            zone = self._zone_at(x, y)
            if zone is not None:
                out.append((zone, label, conf, x, y))
        return out

    def _zone_at(self, x, y):
        for name, (zx, zy, zw, zh) in self.settings.zones.items():
            if zx <= x <= zx + zw and zy <= y <= zy + zh:
                return name
        return None

    def _merge(self, cards):
        """Collapse the two corner boxes many card models emit for one card."""
        merged = []
        for label, conf, x, y in sorted(cards, key=lambda c: -c[1]):
            for i, (ml, mc, mx, my, n) in enumerate(merged):
                if ml == label and math.dist((x, y), (mx, my)) <= self.settings.merge_distance:
                    merged[i] = (ml, mc, (mx * n + x) / (n + 1), (my * n + y) / (n + 1), n + 1)
                    break
            else:
                merged.append((label, conf, x, y, 1))
        return [m[:4] for m in merged]

    def _match(self, zone, x, y):
        best, best_dist = None, self.settings.match_distance
        for track in self.tracks:
            if track.zone != zone or track.last_frame == self.frame_no:
                continue
            dist = math.dist((x, y), (track.x, track.y))
            if dist <= best_dist:
                best, best_dist = track, dist
        return best or self._new_track(zone, x, y)

    def _new_track(self, zone, x, y):
        track = Track(self._next_track, zone, x, y)
        self._next_track += 1
        self.tracks.append(track)
        return track

    def _settle(self, track, now):
        label, _ = track.best()
        if label is None or track.frames < self.settings.stable_frames:
            return []
        card = parse_label(label)
        if card is None:
            return []                      # face down: wait for it to turn over
        if track.card is None:
            self._commit(track, card, label, now)
            return [f"card {track.zone} {card.label}"]
        if card != track.card:
            old_votes = track.votes.get(track.card.label, 0.0)
            if track.votes[label] >= old_votes * self.settings.correction_margin:
                self.shoe.restore(track.card.rank)
                self.shoe.remove(card.rank)
                self.memory.correct_card(track.card_id, card, track.mean_confidence(label), "votes")
                self.memory.event(self.table_id, "correction",
                                  f"{track.zone} {track.card.label}->{card.label}", self.shoe_id)
                track.card = card
                return [f"correction {track.zone} {card.label}"]
        return []

    def _commit(self, track, card, label, now):
        if self.round_id is None:
            self.round_id, self.round_no = self.memory.open_round(self.shoe_id, self.table_id)
            self._zone_positions = {}
        track.card = card
        track.position = self._zone_positions.get(track.zone, 0)
        self._zone_positions[track.zone] = track.position + 1
        track.hand_index = self._hand_index(track)
        confidence = track.mean_confidence(label)
        self.shoe.remove(card.rank)
        track.card_id = self.memory.add_card(
            self.round_id, self.shoe_id, self.table_id, track.zone, track.hand_index,
            track.position, card, confidence, "yolo", track.x, track.y)
        self.last_card_time = now
        if confidence < self.settings.review_confidence and self.review and not track.review_requested:
            track.review_requested = True
            self.review(self, track)

    def _hand_index(self, track):
        xs = sorted(t.x for t in self.tracks if t.zone == track.zone and t.card is not None)
        hand = 0
        for prev, cur in zip(xs, xs[1:]):
            if cur > track.x:
                break
            if cur - prev > self.settings.hand_gap:
                hand += 1
        return hand

    def resolve(self, track, label, confidence, source="llm"):
        """Apply an outside reading (vision LLM or manual) to a committed card."""
        card = parse_label(label)
        if card is None or track.card is None or card == track.card:
            return
        self.shoe.restore(track.card.rank)
        self.shoe.remove(card.rank)
        self.memory.correct_card(track.card_id, card, confidence, source)
        track.card = card
        track.votes[card.label] = max(track.votes.values()) * self.settings.correction_margin

    def _end_round(self):
        if self.round_id:
            self.memory.close_round(self.round_id)
        self.round_id = None
        self.tracks = []
        self._zone_positions = {}

    # Read-out --------------------------------------------------------------
    def seats(self):
        """zone -> list of hands (left to right), each a list of cards in deal order.

        Hands are regrouped from card positions on every call, since a split
        only becomes visible after later cards land.
        """
        out = {}
        by_zone = {}
        for track in self.tracks:
            if track.card is not None:
                by_zone.setdefault(track.zone, []).append(track)
        for zone, tracks in sorted(by_zone.items()):
            tracks.sort(key=lambda t: t.x)
            hands = [[tracks[0]]]
            for prev, cur in zip(tracks, tracks[1:]):
                if cur.x - prev.x > self.settings.hand_gap:
                    hands.append([])
                hands[-1].append(cur)
            for index, hand in enumerate(hands):
                for track in hand:
                    track.hand_index = index
            out[zone] = [[t.card for t in sorted(hand, key=lambda t: t.position)] for hand in hands]
        return out

    def status(self):
        tc = self.shoe.true_count("hilo")
        reliable = self.reliable
        seats = self.seats()
        dealer = seats.get("dealer", [[]])
        dealer_up = dealer[0][0].rank if dealer and dealer[0] else None
        advice = None
        mine = seats.get(self.settings.my_seat) if self.settings.my_seat else None
        if mine and dealer_up:
            advice = [indices.deviation([c.rank for c in hand], dealer_up, tc,
                                        self.settings.surrender_allowed) for hand in mine]
        return {
            "table": self.table_id, "shoe_id": self.shoe_id, "round": self.round_no,
            "reliable": reliable, "cards_seen": self.shoe.seen,
            "decks_left": round(self.shoe.decks_left, 2),
            "penetration": round(self.shoe.penetration_dealt, 3),
            "running_count": self.shoe.running_count("hilo"), "true_count": round(tc, 2),
            "other_true_counts": {s: round(self.shoe.true_count(s), 2)
                                  for s in ("hiopt2", "omega2", "zen", "halves2")},
            "edge": round(self.edge.edge(tc), 4),
            "alert": reliable and tc >= self.settings.wong_in,
            "leave": tc < self.settings.wong_out,
            "insurance": dealer_up == 1 and indices.take_insurance(tc),
            "seats": {zone: [{"cards": [c.label for c in hand],
                              "total": hand_total([c.rank for c in hand])[0]} for hand in hands]
                      for zone, hands in seats.items()},
            "advice": advice,
        }
