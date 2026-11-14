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


class BetUnits(unittest.TestCase):
    def test_default_ramp(self):
        from blackjack.counting import bet_units
        cases = [(-5, 1), (0.99, 1), (1, 2), (1.9, 2), (2, 5), (3, 10), (3.99, 10), (4, 20), (9, 20)]
        for tc, units in cases:
            self.assertEqual(bet_units(tc), units, tc)

    def test_custom_ramp_unsorted(self):
        from blackjack.counting import bet_units
        ramp = [[2, 4], [0, 1]]
        self.assertEqual((bet_units(-1, ramp), bet_units(0, ramp), bet_units(2.5, ramp)), (1, 1, 4))


class Strategy(unittest.TestCase):
    def play(self, ranks, up, tc=0.0, **kw):
        from blackjack.strategy import recommend
        return recommend(ranks, up, tc, **kw)["play"]

    def test_basic_cells(self):
        self.assertEqual(self.play([10, 2], 4), "stand")      # 12 v 4
        self.assertEqual(self.play([10, 2], 3, -1), "hit")    # 12 v 3 hits at low count
        self.assertEqual(self.play([5, 4], 3), "double")      # 9 v 3
        self.assertEqual(self.play([5, 4], 7), "hit")
        self.assertEqual(self.play([10, 1], 10), "stand")     # 21
        self.assertEqual(self.play([1, 7], 3), "double")      # A7 v 3
        self.assertEqual(self.play([1, 7], 9), "hit")         # A7 v 9
        self.assertEqual(self.play([1, 7], 2), "stand")
        self.assertEqual(self.play([1, 6], 6), "double")
        self.assertEqual(self.play([8, 8], 10), "split")
        self.assertEqual(self.play([1, 1], 6), "split")
        self.assertEqual(self.play([10, 10], 6), "stand")
        self.assertEqual(self.play([4, 4], 5), "split")       # DAS
        self.assertEqual(self.play([4, 4], 5, settings=__import__("blackjack.strategy").strategy.StrategySettings(das=False)), "hit")
        self.assertEqual(self.play([5, 5], 9), "double")      # played as hard 10
        self.assertEqual(self.play([9, 9], 7), "stand")

    def test_no_double_with_three_cards(self):
        self.assertEqual(self.play([2, 3, 6], 6, can_double=False), "hit")
        self.assertEqual(self.play([1, 2, 4], 6, can_double=False), "hit")
        self.assertEqual(self.play([1, 3, 3], 3, can_double=False), "stand")   # soft 18 v 3: Ds -> stand

    def test_11_v_5_low_count_just_hits(self):
        from blackjack.strategy import recommend
        self.assertEqual(self.play([5, 6], 5, 0.0), "double")
        r = recommend([5, 6], 5, -9.0)
        self.assertEqual(r["play"], "hit")
        self.assertTrue(r["deviation"])
        self.assertIn("double 11 vs 5 only at TC >=", r["reason"])

    def test_16_v_10_stands_at_nonnegative_count(self):
        self.assertEqual(self.play([10, 6], 10, -1.0), "hit")
        self.assertEqual(self.play([10, 6], 10, 0.0), "stand")
        self.assertEqual(self.play([10, 6], 10, 2.0), "stand")

    def test_pair_not_overridden_by_hard_index(self):
        self.assertEqual(self.play([8, 8], 10, 3.0), "split")

    def test_surrender_setting(self):
        from blackjack.strategy import StrategySettings
        self.assertEqual(self.play([10, 6], 9, settings=StrategySettings(surrender=True)), "surrender")
        self.assertEqual(self.play([10, 6], 9), "hit")


class RoundResults(unittest.TestCase):
    def test_results(self):
        from blackjack.history import round_result as rr
        self.assertEqual(rr([10, 1], [10, 9]), "BJ")
        self.assertEqual(rr([10, 1], [10, 1]), "PUSH")
        self.assertEqual(rr([10, 5, 6], [10, 1]), "LOSS")      # 21 loses to dealer blackjack
        self.assertEqual(rr([10, 5, 6], [10, 9]), "WIN")
        self.assertEqual(rr([10, 1], [10, 9], split=True), "WIN")
        self.assertEqual(rr([10, 6, 8], [10, 7]), "BUST")
        self.assertEqual(rr([10, 8], [10, 6, 10]), "WIN")        # dealer busts
        self.assertEqual(rr([10, 8], [10, 8]), "PUSH")
        self.assertEqual(rr([10, 7], [10, 8]), "LOSS")
        self.assertIsNone(rr([10, 8], []))
        self.assertIsNone(rr([10, 8], [6]))                      # dealer still drawing

    def test_recent_rounds_from_memory(self):
        from blackjack.history import recent_rounds
        mem = Memory()
        t = tracker(mem, stable_frames=1)
        for _ in range(2):
            t.update([det("KH", 100, 50), det("9C", 160, 50), det("AS", 100, 250), det("KD", 160, 250),
                      det("5C", 600, 250), det("6D", 660, 250)])
        for _ in range(t.settings.empty_frames_round_end):
            t.update([])
        rounds = recent_rounds(mem, "t1")
        self.assertEqual(len(rounds), 1)
        r = rounds[0]
        self.assertEqual(r["dealer"]["total"], 19)
        self.assertEqual(r["seats"]["seat1"][0]["result"], "BJ")
        self.assertEqual(r["seats"]["seat2"][0]["result"], "LOSS")


class FakeTracker:
    """Duck-typed tracker for the server tests."""

    def __init__(self):
        self.settings = TrackerSettings(zones={**ZONES, "seat3": [900, 200, 100, 100]})
        self.calls = []

    def status(self):
        return {"table": "t1", "shoe_id": 1, "round": 1, "reliable": True, "cards_seen": 7,
                "decks_left": 5.9, "penetration": 0.02, "running_count": 2, "true_count": 0.34,
                "alert": False, "insurance": False, "seats": {}, "advice": None,
                "occupancy": {"seat2": True}}

    def seat_cards(self):
        c = lambda i, label, rank: {"id": i, "label": label, "rank": rank}
        return {"dealer": [[c(1, "6D", 6)]], "seat1": [[c(2, "5H", 5), c(3, "6S", 6)]],
                "seat3": [[c(4, "AC", 1), c(5, "6C", 6)]]}

    def new_shoe(self, reason):
        self.calls.append(("new_shoe", reason))

    def edit_card(self, track_id, label):
        self.calls.append(("edit", track_id, label))

    def add_card_manual(self, zone, label):
        self.calls.append(("add", zone, label))
        return 99


class ServerApi(unittest.TestCase):
    def setUp(self):
        import threading
        from blackjack import server
        self.fake = FakeTracker()
        self.app = server.App([server.TableRuntime("t1", self.fake)], Memory(),
                              bet={"unit_value": 5})
        self.httpd = server.make_server(self.app, "127.0.0.1", 0)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def call(self, path, body=None):
        import urllib.error
        import urllib.request
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.read(), r.headers
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers

    def state(self):
        return json.loads(self.call("/api/state")[1])

    def test_state_shape(self):
        s = self.state()
        for key in ("tables", "table", "status", "dealer", "seats", "mine", "bet", "capture"):
            self.assertIn(key, s)
        self.assertEqual([x["seat"] for x in s["seats"]], ["seat1", "seat2", "seat3"])
        self.assertEqual(s["dealer"]["up"], 6)
        self.assertEqual(s["bet"]["units"], 1)
        seat1, seat2, seat3 = s["seats"]
        self.assertEqual((seat1["state"], seat2["state"], seat3["state"]),
                         ("occupied", "occupied", "occupied"))
        self.assertEqual(seat1["hands"][0]["total"], 11)
        self.assertTrue(seat3["hands"][0]["soft"])
        self.assertNotIn("advice", seat1["hands"][0])

    def test_mine_advice_and_limit(self):
        for seat in ("seat1", "seat2", "seat3"):
            self.call("/api/mine", {"seat": seat, "mine": True})
        s = self.state()
        self.assertEqual(s["mine"], ["seat2", "seat3"])        # at most two
        self.assertEqual(s["seats"][2]["hands"][0]["advice"]["play"], "double")   # A6 v 6
        self.call("/api/mine", {"seat": "seat1", "mine": True})
        hand = self.state()["seats"][0]["hands"][0]
        self.assertEqual(hand["advice"]["play"], "double")      # 11 v 6
        self.assertIn("reason", hand["advice"])

    def test_occupancy_override_and_empty(self):
        self.call("/api/occupancy", {"seat": "seat1", "value": "empty"})
        self.assertEqual(self.state()["seats"][0]["state"], "empty")
        self.call("/api/occupancy", {"seat": "seat1", "value": None})
        self.assertEqual(self.state()["seats"][0]["state"], "occupied")

    def test_writes_reach_tracker(self):
        self.assertEqual(self.call("/api/new_shoe", {})[0], 200)
        self.call("/api/card", {"id": 2, "label": "QH"})
        self.call("/api/card/add", {"zone": "seat1", "label": "2C"})
        self.assertEqual(self.fake.calls, [("new_shoe", "manual"), ("edit", 2, "QH"),
                                           ("add", "seat1", "2C")])

    def test_unit_value_and_bad_requests(self):
        self.call("/api/settings", {"unit_value": 25})
        self.assertEqual(self.state()["bet"]["unit_value"], 25.0)
        self.assertEqual(self.call("/api/settings", {"unit_value": -1})[0], 400)
        self.assertEqual(self.call("/api/mine", {"seat": "nope", "mine": True})[0], 400)
        self.assertEqual(self.call("/api/nothing", {})[0], 404)

    def test_static_history_and_frame(self):
        status, body, _ = self.call("/")
        self.assertEqual(status, 200)
        self.assertIn(b"NEW SHOE", body)
        self.assertEqual(self.call("/frame.jpg")[0], 404)
        self.app.runtime().set_frame(b"\xff\xd8jpeg", 0)
        self.assertEqual(self.call("/frame.jpg")[1], b"\xff\xd8jpeg")
        self.assertEqual(json.loads(self.call("/api/history")[1])["rounds"], [])


class ManualTrackerEdits(unittest.TestCase):
    def test_edit_delete_add_keep_count_consistent(self):
        mem = Memory()
        t = tracker(mem, stable_frames=1)
        t.update([det("5C", 100, 250), det("KD", 160, 250)])
        self.assertEqual(t.shoe.running_count(), 0)             # +1 and -1
        ids = [c["id"] for c in t.seat_cards()["seat1"][0]]
        t.edit_card(ids[1], "3H")                                # K -> 3: count +2
        self.assertEqual(t.shoe.running_count(), 2)
        t.edit_card(ids[0], "")                                  # delete the 5
        self.assertEqual((t.shoe.running_count(), t.shoe.seen), (1, 1))
        t.add_card_manual("seat1", "AS")                         # ace: -1
        self.assertEqual((t.shoe.running_count(), t.shoe.seen), (0, 2))
        labels = [c["label"] for c in t.seat_cards()["seat1"][0]]
        self.assertEqual(sorted(labels), ["3H", "AS"])
        rows = mem.shoe_cards(t.shoe_id)
        self.assertEqual(sorted(r["label"] for r in rows), ["3H", "AS"])
        with self.assertRaises(KeyError):
            t.edit_card(9999, "2C")


if __name__ == "__main__":
    unittest.main()
