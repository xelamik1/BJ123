import json
from pathlib import Path
import tempfile
import unittest

from blackjack import config as config_mod
from blackjack.cards import Card, hand_total, parse_label
from blackjack.counting import SYSTEMS, EdgeModel, Shoe, ShoeConfig
from blackjack.indices import deviation, take_insurance
from blackjack.memory import Memory
from blackjack.model import CLASSES
from blackjack.tracker import Detection, TableTracker, TrackerSettings

ZONES = {"dealer": [0, 0, 400, 100], "seat1": [0, 200, 400, 100], "seat2": [500, 200, 400, 100]}


def det(label, x, y, conf=0.9, size=20):
    return Detection(label, conf, x - size, y - size, x + size, y + size)


def tracker(memory=None, **settings):
    memory = memory or Memory()
    t = TableTracker("t1", TrackerSettings(zones=ZONES, **settings), ShoeConfig(), memory)
    t.new_shoe("test start")
    return t


class Cards(unittest.TestCase):
    def test_label_formats(self):
        self.assertEqual(parse_label("10C"), Card("10", "C"))
        self.assertEqual(parse_label("ah"), Card("A", "H"))
        self.assertEqual(parse_label("queen_of_spades"), Card("Q", "S"))
        self.assertEqual(parse_label("10 of clubs").rank, 10)
        self.assertEqual(parse_label("K").rank, 10)
        self.assertIsNone(parse_label("back"))
        with self.assertRaises(ValueError):
            parse_label("joker")

    def test_model_classes_parse(self):
        self.assertEqual(len(CLASSES), 52)
        self.assertEqual(len({parse_label(c) for c in CLASSES}), 52)

    def test_soft_totals(self):
        self.assertEqual(hand_total([1, 6]), (17, True))
        self.assertEqual(hand_total([1, 6, 10]), (17, False))


class Counting(unittest.TestCase):
    def test_balanced_systems_sum_to_zero_over_a_deck(self):
        per_rank = ShoeConfig().cards_per_rank_per_deck
        for name in ("hilo", "hiopt2", "omega2", "zen", "halves2"):
            self.assertEqual(sum(SYSTEMS[name][r] * n for r, n in per_rank.items()), 0, name)

    def test_true_count_uses_decks_left(self):
        shoe = Shoe(ShoeConfig(decks=8))
        for rank in [2, 3, 4, 5, 6] * 4:
            shoe.remove(rank)
        self.assertEqual(shoe.running_count(), 20)
        self.assertAlmostEqual(shoe.true_count(), 20 / ((416 - 20) / 52))
        self.assertEqual(shoe.running_count("halves2"), 4 * (0.5 + 1 + 1 + 1.5 + 1))

    def test_restore_undoes_remove(self):
        shoe = Shoe(ShoeConfig())
        shoe.remove(5)
        shoe.restore(5)
        self.assertEqual((shoe.seen, shoe.running_count()), (0, 0))

    def test_too_many_of_a_rank_is_an_anomaly(self):
        shoe = Shoe(ShoeConfig(decks=1))
        for _ in range(5):
            shoe.remove(1)
        self.assertEqual(shoe.anomalies, 1)

    def test_edge_model(self):
        edge = EdgeModel(base_edge=-0.005, per_true_count=0.005)
        self.assertAlmostEqual(edge.break_even_true_count(), 1.0)
        self.assertEqual(edge.kelly_bet(0, 10000), 0.0)
        self.assertGreater(edge.kelly_bet(3, 10000), 0)
        self.assertLess(edge.risk_of_ruin(0.008, 500), edge.risk_of_ruin(0.008, 100))

    def test_insurance_ev_sign(self):
        shoe = Shoe(ShoeConfig(decks=1))
        self.assertLess(shoe.insurance_ev(), 0)
        for rank in [2, 3, 4, 5, 6, 7, 8, 9] * 3:
            shoe.remove(rank)
        self.assertGreater(shoe.insurance_ev(), 0)


class Indices(unittest.TestCase):
    def test_sixteen_v_ten(self):
        self.assertEqual(deviation([10, 6], 10, 0.5)["play"], "stand")
        self.assertEqual(deviation([10, 6], 10, -0.5)["play"], "hit")

    def test_doubles_need_two_cards(self):
        self.assertEqual(deviation([5, 6], 1, 2)["play"], "double")
        self.assertIsNone(deviation([2, 3, 6], 1, 2))

    def test_surrender_first_when_allowed(self):
        self.assertEqual(deviation([10, 5], 10, 1, surrender_allowed=True)["play"], "surrender")
        self.assertEqual(deviation([10, 5], 10, 1)["play"], "hit")

    def test_insurance(self):
        self.assertTrue(take_insurance(3))
        self.assertFalse(take_insurance(2.9))


class Tracking(unittest.TestCase):
    def test_card_counted_once_after_stable_frames(self):
        t = tracker(stable_frames=3)
        for _ in range(10):
            t.update([det("5H", 100, 250)])
        self.assertEqual(t.shoe.seen, 1)
        self.assertEqual(t.shoe.running_count(), 1)
        self.assertEqual(len(t.memory.shoe_cards(t.shoe_id)), 1)

    def test_flicker_below_stable_frames_not_counted(self):
        t = tracker(stable_frames=3)
        t.update([det("5H", 100, 250)])
        t.update([])
        self.assertEqual(t.shoe.seen, 0)

    def test_corner_boxes_merge_into_one_card(self):
        t = tracker(stable_frames=2, merge_distance=90)
        for _ in range(3):
            t.update([det("KS", 100, 220), det("KS", 160, 280)])
        self.assertEqual(t.shoe.seen, 1)

    def test_same_label_on_two_seats_counts_twice(self):
        t = tracker(stable_frames=2)
        for _ in range(3):
            t.update([det("8D", 100, 250), det("8D", 600, 250)])
        self.assertEqual(t.shoe.seen, 2)
        self.assertEqual(set(t.seats()), {"seat1", "seat2"})

    def test_cards_stay_remembered_when_off_screen(self):
        t = tracker(stable_frames=2, empty_frames_round_end=5)
        for _ in range(3):
            t.update([det("9C", 100, 250), det("4D", 200, 50)])
        for _ in range(2):          # briefly hidden, round not over
            t.update([])
        for _ in range(3):          # same cards back: not counted again
            t.update([det("9C", 100, 250), det("4D", 200, 50)])
        self.assertEqual(t.shoe.seen, 2)
        self.assertEqual(t.status()["seats"]["dealer"][0]["cards"], ["4D"])

    def test_round_end_and_new_round(self):
        t = tracker(stable_frames=2, empty_frames_round_end=3)
        for _ in range(3):
            t.update([det("2C", 100, 250)])
        events = [e for _ in range(3) for e in t.update([])]
        self.assertIn("round_end", events)
        for _ in range(3):
            t.update([det("2C", 100, 250)])   # same spot, new round: a new card
        self.assertEqual(t.shoe.seen, 2)
        self.assertEqual(t.round_no, 2)

    def test_vote_correction_updates_count_and_memory(self):
        t = tracker(stable_frames=2, correction_margin=1.5)
        for _ in range(2):
            t.update([det("3H", 100, 250)])
        for _ in range(5):
            t.update([det("8H", 100, 250)])
        self.assertEqual(t.shoe.seen, 1)
        self.assertEqual(t.shoe.running_count(), 0)
        row = t.memory.shoe_cards(t.shoe_id)[0]
        self.assertEqual((row["label"], row["corrected_from"]), ("8H", "3H"))

    def test_face_down_card_waits_until_turned(self):
        t = tracker(stable_frames=2)
        for _ in range(3):
            t.update([det("back", 300, 50)])
        self.assertEqual(t.shoe.seen, 0)
        for _ in range(8):
            t.update([det("TD", 300, 50)])
        self.assertEqual(t.shoe.seen, 1)

    def test_split_hands_in_one_seat(self):
        t = tracker(stable_frames=1, hand_gap=120)
        t.update([det("8S", 50, 250)])
        t.update([det("8S", 50, 250), det("3C", 250, 250)])
        self.assertEqual(len(t.status()["seats"]["seat1"]), 2)

    def test_shuffle_signal_starts_reliable_shoe(self):
        memory = Memory()
        t = TableTracker("t1", TrackerSettings(zones=ZONES, stable_frames=1, shuffle_frames=2),
                         ShoeConfig(), memory)
        self.assertFalse(t.reliable)          # joined mid-shoe
        t.update([det("5C", 100, 250)])
        t.update([], shuffle_signal=True)
        t.update([], shuffle_signal=True)
        self.assertTrue(t.reliable)
        self.assertEqual(t.shoe.seen, 0)

    def test_alert_needs_reliable_shoe_and_count(self):
        t = tracker(stable_frames=1, wong_in=3, empty_frames_round_end=1)
        x = 20
        for rank in ["2", "3", "4", "5", "6"] * 6:
            t.update([det(rank + "C", x, 250)])
            t.update([])                       # each card its own round
        self.assertGreaterEqual(t.status()["true_count"], 3)
        self.assertTrue(t.status()["alert"])

    def test_restart_restores_shoe_and_cards_on_felt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "bj.sqlite3")
            first = tracker(Memory(path), stable_frames=2)
            for _ in range(3):
                first.update([det("6H", 100, 250)])
            first.memory.close()
            second = TableTracker("t1", TrackerSettings(zones=ZONES, stable_frames=2),
                                  ShoeConfig(), Memory(path))
            self.assertEqual(second.shoe.seen, 1)
            for _ in range(3):
                second.update([det("6H", 100, 250)])
            self.assertEqual(second.shoe.seen, 1)     # not double counted
            self.assertTrue(second.reliable)
            second.memory.close()

    def test_outside_zones_ignored(self):
        t = tracker(stable_frames=1)
        t.update([det("5H", 450, 150)])
        self.assertEqual(t.shoe.seen, 0)


class FakeBox:
    def __init__(self, cls, conf, xyxy):
        self.cls, self.conf, self.xyxy = [cls], [conf], [FakeTensor(xyxy)]


class FakeTensor(list):
    def tolist(self):
        return list(self)


class FakeCrop:
    def __init__(self, h, w):
        self.shape = (h, w, 3)


class FakeFrame:
    shape = (500, 900, 3)

    def __getitem__(self, key):
        rows, cols = key
        return FakeCrop(rows.stop - rows.start, cols.stop - cols.start)


class ZoneDetection(unittest.TestCase):
    def test_zone_boxes_map_back_to_frame(self):
        from blackjack.detector import YoloDetector
        detector = YoloDetector.__new__(YoloDetector)
        detector.names = {0: "AS"}
        seen = []

        def predict(crops):
            seen.extend(crops)
            return [type("R", (), {"boxes": [FakeBox(0, 0.9, [5, 5, 25, 35])]})() for _ in crops]

        detector._predict = predict
        dets = detector.detect_zones(FakeFrame(), {"dealer": [100, 50, 200, 80],
                                                   "seat1": [0, 0, 50, 50]}, pad=10)
        self.assertEqual(len(seen), 2)
        self.assertEqual((dets[0].x1, dets[0].y1, dets[0].x2, dets[0].y2), (95, 45, 115, 75))
        self.assertEqual((dets[1].x1, dets[1].y1), (5, 5))     # clipped at the frame edge

    def test_card_cut_off_by_crop_edge_is_dropped(self):
        from blackjack.detector import YoloDetector
        detector = YoloDetector.__new__(YoloDetector)
        detector.names = {0: "JC"}
        detector._predict = lambda crops: [
            type("R", (), {"boxes": [FakeBox(0, 0.9, [0, 10, 30, 40]),        # touches left edge
                                     FakeBox(0, 0.9, [40, 10, 70, 40])]})() for _ in crops]
        dets = detector.detect_zones(FakeFrame(), {"seat2": [300, 100, 200, 100]}, pad=0)
        self.assertEqual([(d.x1, d.y1) for d in dets], [(340, 110)])


class Config(unittest.TestCase):
    def test_example_config_loads(self):
        cfg = config_mod.load(Path(__file__).resolve().parents[1] / "blackjack" / "tables.example.json")
        table = cfg.tables[0]
        self.assertEqual(table.shoe.total_cards, 416)
        self.assertIn("dealer", table.tracker.zones)
        self.assertEqual(len([z for z in table.tracker.zones if z.startswith("seat")]), 6)
        self.assertTrue(cfg.detect_per_zone)

    def test_table_overrides_defaults(self):
        data = {"defaults": {"shoe": {"decks": 8}, "tracker": {"stable_frames": 3}},
                "tables": [{"id": "a", "region": {}, "shoe": {"decks": 6},
                            "tracker": {"zones": ZONES}}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            path.write_text(json.dumps(data))
            table = config_mod.load(path).tables[0]
        self.assertEqual((table.shoe.decks, table.tracker.stable_frames), (6, 3))


if __name__ == "__main__":
    unittest.main()
