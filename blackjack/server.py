"""Local web UI: python -m blackjack serve  ->  http://127.0.0.1:8765

Stdlib only (http.server). The capture loop runs in a thread and keeps the
latest annotated frame; the browser polls /api/state at ~5 Hz and /frame.jpg.

  GET  /api/state?table=ID      live status, dealer, seats, advice, bet suggestion
  GET  /api/history?table=ID    finished rounds with WIN/LOSS/PUSH/BJ/BUST results
  GET  /frame.jpg?table=ID      latest frame with YOLO boxes (404 if none)
  GET  /feed.mjpg?table=ID      the same as an MJPEG stream
  POST /api/mine {seat, mine}   mark/unmark my seat (at most two)
  POST /api/occupancy {seat, value}  "occupied" | "empty" | null (auto)
  POST /api/bet {seat, amount}  optional bet shown for a seat (null clears)
  POST /api/settings {unit_value}
  POST /api/new_shoe {}         tracker.new_shoe("manual")
  POST /api/card {id, label}    correct a card; empty label deletes it
  POST /api/card/add {zone, label}  add a card the detector missed
All POSTs take JSON and an optional "table".
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlparse

from .cards import hand_total
from .counting import DEFAULT_BET_RAMP, bet_units
from .history import recent_rounds
from .strategy import StrategySettings, recommend

WEB = Path(__file__).parent / "web"
STATIC = {"/": ("index.html", "text/html; charset=utf-8"),
          "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/style.css": ("style.css", "text/css; charset=utf-8")}
MAX_MINE = 2


class TableRuntime:
    """One table: its tracker plus UI state and the latest frame."""

    def __init__(self, table_id, tracker, mode="none"):
        self.id = table_id
        self.tracker = tracker
        self.mine = []            # seat names, oldest selection first
        self.occupancy = {}       # seat -> bool override
        self.bets = {}            # seat -> optional bet amount
        self.jpeg = None
        self.frame_seq = 0
        self.cond = threading.Condition()
        self.capture = {"mode": mode, "frames": 0, "detections": 0, "error": None,
                        "last_frame_at": None, "ended": False}

    def set_frame(self, jpeg, detections):
        with self.cond:
            self.jpeg = jpeg
            self.frame_seq += 1
            self.capture["frames"] += 1
            self.capture["detections"] = detections
            self.capture["last_frame_at"] = time.time()
            self.cond.notify_all()


class App:
    def __init__(self, runtimes, memory, bet=None, strategy=None, lock=None):
        self.runtimes = {rt.id: rt for rt in runtimes}
        self.default_table = runtimes[0].id
        self.memory = memory
        bet = bet or {}
        self.unit_value = float(bet.get("unit_value", 5))
        self.ramp = bet.get("ramp") or DEFAULT_BET_RAMP
        self.strategy = StrategySettings.from_dict(strategy)
        self.lock = lock or threading.RLock()   # guards trackers and memory (shared with capture)

    def runtime(self, table_id=None):
        try:
            return self.runtimes[table_id or self.default_table]
        except KeyError:
            raise KeyError(f"unknown table {table_id}")

    # Read ------------------------------------------------------------------
    def state(self, table_id=None):
        rt = self.runtime(table_id)
        with self.lock:
            status = rt.tracker.status()
            cards = rt.tracker.seat_cards()
            zones = dict(rt.tracker.settings.zones)
        tc = status.get("true_count", 0.0)
        dealer_hands = [self._hand(h, rt) for h in cards.get("dealer", [])]
        up = None
        if dealer_hands and dealer_hands[0]["cards"]:
            up = dealer_hands[0]["cards"][0]["rank"]
        names = sorted((z for z in zones if z != "dealer"), key=lambda z: (zones[z][0], z))
        occ_status = status.get("occupancy") or {}
        seats = []
        for name in names:
            hands = [self._hand(h, rt) for h in cards.get(name, [])]
            mine = name in rt.mine
            has_cards = bool(hands)
            override, reported = rt.occupancy.get(name), occ_status.get(name)
            occupied = override if override is not None else (
                reported if reported is not None else has_cards)
            source = "manual" if override is not None else "tracker" if reported is not None else "cards"
            if mine:
                for hand in hands:
                    hand["advice"] = self._advice(hand, up, tc, len(hands))
            seats.append({"seat": name, "mine": mine, "occupied": bool(occupied or mine),
                          "occupancy_source": source, "bet": rt.bets.get(name), "hands": hands,
                          "state": "mine" if mine else "occupied" if occupied else "empty"})
        units = bet_units(tc, self.ramp)
        return {"tables": list(self.runtimes), "table": rt.id, "status": status,
                "dealer": {"hands": dealer_hands, "up": up}, "seats": seats, "mine": list(rt.mine),
                "bet": {"units": units, "amount": units * self.unit_value,
                        "unit_value": self.unit_value, "ramp": self.ramp, "placeholder": True},
                "capture": {**rt.capture, "has_frame": rt.jpeg is not None,
                            "frame_seq": rt.frame_seq},
                "server_time": time.time()}

    @staticmethod
    def _hand(cards, rt=None):
        ranks = [c["rank"] for c in cards]
        total, soft = hand_total(ranks) if ranks else (0, False)
        return {"cards": cards, "total": total, "soft": soft, "bust": total > 21,
                "blackjack": len(cards) == 2 and total == 21}

    def _advice(self, hand, up, tc, n_hands):
        if not hand["cards"] or hand["bust"] or hand["total"] >= 21:
            return None
        if up is None:
            return {"play": None, "reason": "waiting for the dealer's upcard"}
        ranks = [c["rank"] for c in hand["cards"]]
        two = len(ranks) == 2
        return recommend(ranks, up, tc, self.strategy,
                         can_split=two and ranks[0] == ranks[1] and n_hands < 4, can_double=two)

    def history(self, table_id=None, limit=20):
        rt = self.runtime(table_id)
        with self.lock:
            rounds = recent_rounds(self.memory, rt.id, limit)
        for r in rounds:
            r["mine"] = list(rt.mine)
        return {"table": rt.id, "rounds": rounds}

    # Write -----------------------------------------------------------------
    def set_mine(self, table, seat, mine):
        rt = self.runtime(table)
        if seat not in rt.tracker.settings.zones or seat == "dealer":
            raise KeyError(f"unknown seat {seat}")
        if mine and seat not in rt.mine:
            rt.mine.append(seat)
            del rt.mine[:-MAX_MINE]
        elif not mine and seat in rt.mine:
            rt.mine.remove(seat)

    def set_occupancy(self, table, seat, value):
        rt = self.runtime(table)
        if value in (None, "auto"):
            rt.occupancy.pop(seat, None)
        elif value in ("occupied", "empty"):
            rt.occupancy[seat] = value == "occupied"
        else:
            raise ValueError("value must be occupied, empty or null")

    def set_bet(self, table, seat, amount):
        rt = self.runtime(table)
        if amount in (None, ""):
            rt.bets.pop(seat, None)
        else:
            rt.bets[seat] = float(amount)

    def set_unit(self, value):
        value = float(value)
        if value <= 0:
            raise ValueError("unit value must be positive")
        self.unit_value = value

    def new_shoe(self, table):
        rt = self.runtime(table)
        with self.lock:
            rt.tracker.new_shoe("manual")

    def edit_card(self, table, track_id, label):
        rt = self.runtime(table)
        with self.lock:
            rt.tracker.edit_card(int(track_id), (label or "").strip())

    def add_card(self, table, zone, label):
        rt = self.runtime(table)
        with self.lock:
            return rt.tracker.add_card_manual(zone, label.strip())


class Handler(BaseHTTPRequestHandler):
    server_version = "bj-ui"

    def log_message(self, *args):
        pass

    @property
    def app(self):
        return self.server.app

    def _send(self, code, body, ctype="application/json"):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _local_only(self):
        """Refuse DNS-rebinding and cross-site requests to this local server."""
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost", "[::1]"):
            return False
        origin = self.headers.get("Origin")
        return not origin or (urlparse(origin).hostname or "") in ("127.0.0.1", "localhost", "::1")

    def do_GET(self):
        url = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        if not self._local_only():
            return self._send(403, {"error": "forbidden"})
        try:
            if url.path in STATIC:
                name, ctype = STATIC[url.path]
                return self._send(200, (WEB / name).read_bytes(), ctype)
            if url.path == "/api/state":
                return self._send(200, self.app.state(query.get("table")))
            if url.path == "/api/history":
                return self._send(200, self.app.history(query.get("table"),
                                                        int(query.get("limit", 20))))
            if url.path == "/frame.jpg":
                rt = self.app.runtime(query.get("table"))
                return (self._send(200, rt.jpeg, "image/jpeg") if rt.jpeg
                        else self._send(404, {"error": "no frame yet"}))
            if url.path == "/feed.mjpg":
                return self._mjpeg(self.app.runtime(query.get("table")))
        except KeyError as e:
            return self._send(404, {"error": str(e)})
        except (ValueError, OSError) as e:
            return self._send(400, {"error": str(e)})
        self._send(404, {"error": "not found"})

    def _mjpeg(self, rt):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        seq = -1
        try:
            while True:
                with rt.cond:
                    rt.cond.wait_for(lambda: rt.frame_seq != seq, timeout=5)
                    jpeg, seq = rt.jpeg, rt.frame_seq
                if jpeg:
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                     + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def do_POST(self):
        if not self._local_only():
            return self._send(403, {"error": "forbidden"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            table, path, app = body.get("table"), urlparse(self.path).path, self.app
            if path == "/api/mine":
                app.set_mine(table, body["seat"], bool(body.get("mine", True)))
            elif path == "/api/occupancy":
                app.set_occupancy(table, body["seat"], body.get("value"))
            elif path == "/api/bet":
                app.set_bet(table, body["seat"], body.get("amount"))
            elif path == "/api/settings":
                app.set_unit(body["unit_value"])
            elif path == "/api/new_shoe":
                app.new_shoe(table)
            elif path == "/api/card":
                app.edit_card(table, body["id"], body.get("label"))
            elif path == "/api/card/add":
                app.add_card(table, body["zone"], body["label"])
            else:
                return self._send(404, {"error": "not found"})
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as e:
            return self._send(400, {"error": f"{type(e).__name__}: {e}"})
        self._send(200, {"ok": True})


def make_server(app, host="127.0.0.1", port=8765):
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    server.app = app
    return server


# Capture -------------------------------------------------------------------
class VideoSource:
    """Frames from a video file, sampled at `fps` per second of real time."""

    def __init__(self, path, fps):
        import cv2
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise OSError(f"cannot open video {path}")
        self.step = max(1, round((self.cap.get(cv2.CAP_PROP_FPS) or 30) / fps))
        self.ended = False

    def grab(self, region=None):
        for _ in range(self.step - 1):
            self.cap.grab()
        ok, frame = self.cap.read()
        self.ended = not ok
        return frame if ok else None


def draw_frame(frame, zones, detections, max_width=1100):
    """Annotated JPEG bytes: seat zones plus YOLO boxes with labels."""
    import cv2
    img = frame.copy()
    for name, (x, y, w, h) in zones.items():
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 200, 255), 2)
        cv2.putText(img, name, (x + 4, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)
    for d in detections:
        p1, p2 = (int(d.x1), int(d.y1)), (int(d.x2), int(d.y2))
        cv2.rectangle(img, p1, p2, (0, 255, 0), 2)
        cv2.putText(img, f"{d.label} {d.confidence:.2f}", (p1[0], max(p1[1] - 4, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    if img.shape[1] > max_width:
        scale = max_width / img.shape[1]
        img = cv2.resize(img, (max_width, int(img.shape[0] * scale)))
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buf.tobytes() if ok else None


class CaptureLoop(threading.Thread):
    """The same capture -> detect -> track loop as `run`, feeding the web UI."""

    def __init__(self, app, tables, source, detector, cfg, banners=None, reviewer=None, pending=None):
        super().__init__(daemon=True)
        self.app, self.tables, self.source, self.detector, self.cfg = app, tables, source, detector, cfg
        self.banners, self.reviewer = banners or {}, reviewer
        self.pending = pending if pending is not None else []
        self.stop_flag = threading.Event()

    def _detect(self, frame, table):
        if self.detector is None:
            return []
        if self.cfg.detect_per_zone:
            return self.detector.detect_zones(frame, table.tracker.zones, self.cfg.zone_padding)
        return self.detector.detect(frame)

    def run(self):
        from .capture import crop
        crop_w, crop_h = self.cfg.llm.get("crop_size", [120, 170])
        period = 1 / self.cfg.fps
        while not self.stop_flag.is_set():
            started = time.monotonic()
            for table in self.tables:
                rt = self.app.runtime(table.id)
                try:
                    frame = self.source.grab(table.region)
                    if frame is None:
                        rt.capture["ended"] = True
                        continue
                    detections = self._detect(frame, table)
                    banner = self.banners.get(table.id)
                    with self.app.lock:
                        events = rt.tracker.update(
                            detections, shuffle_signal=bool(banner and banner.seen(frame)))
                        for tr, tk in self.pending:
                            box = (tk.x - crop_w / 2, tk.y - crop_h / 2,
                                   tk.x + crop_w / 2, tk.y + crop_h / 2)
                            self.reviewer.submit(tr, tk, crop(frame, box))
                        self.pending.clear()
                        if self.reviewer:
                            self.reviewer.apply_results()
                        status = rt.tracker.status()
                    for event in events:
                        print(f"[{table.id}] {event}  RC {status['running_count']:+}"
                              f"  TC {status['true_count']:+.2f}")
                    rt.set_frame(draw_frame(frame, table.tracker.zones, detections), len(detections))
                    rt.capture["error"] = None
                except Exception as e:   # keep the UI alive; show the error in the page
                    rt.capture["error"] = f"{type(e).__name__}: {e}"
            self.stop_flag.wait(max(period - (time.monotonic() - started), 0))


def load_extras(path):
    """The optional top-level "bet" and "strategy" sections of the tables JSON."""
    from .config import _strip_notes
    data = _strip_notes(json.loads(Path(path).read_text()))
    return data.get("bet", {}), data.get("strategy", {})
