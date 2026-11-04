"""Claude vision fallback for low-confidence card crops.

Runs in a background thread so it never stalls capture; its answer corrects the
committed card through TableTracker.resolve().
"""
import base64
import queue
import threading

MODEL = "claude-opus-5-5"
PROMPT = ("This is a crop from a live blackjack table showing one playing card. "
          "Give its rank and suit. If the card is face down or unreadable, say so.")


def _schema():
    from pydantic import BaseModel   # optional dependency

    class CardReading(BaseModel):
        readable: bool
        rank: str      # A, 2-10, J, Q, K
        suit: str      # C, D, H, S

    return CardReading


class ClaudeReviewer:
    def __init__(self, model=MODEL, min_side=200):
        import anthropic                 # optional dependency
        import cv2
        self._cv2 = cv2
        self.client = anthropic.Anthropic()
        self.model = model
        self.min_side = min_side
        self.schema = _schema()
        self.jobs = queue.Queue()
        self.results = queue.Queue()
        threading.Thread(target=self._work, daemon=True).start()

    def submit(self, tracker, track, crop_bgr):
        self.jobs.put((tracker, track, crop_bgr))

    def apply_results(self):
        """Call from the capture loop; applies finished readings on that thread."""
        while not self.results.empty():
            tracker, track, label, error = self.results.get()
            if error:
                tracker.memory.event(tracker.table_id, "llm_error", error, tracker.shoe_id)
            elif label:
                tracker.resolve(track, label, confidence=0.99, source="llm")

    def _work(self):
        while True:
            tracker, track, crop_bgr = self.jobs.get()
            try:
                label = self.read(crop_bgr)
            except Exception as exc:     # network or API trouble: keep the YOLO reading
                self.results.put((tracker, track, None, str(exc)))
                continue
            self.results.put((tracker, track, label, None))

    def read(self, crop_bgr):
        cv2 = self._cv2
        h, w = crop_bgr.shape[:2]
        scale = max(self.min_side / max(min(h, w), 1), 1)   # small images read poorly
        if scale > 1:
            crop_bgr = cv2.resize(crop_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        ok, png = cv2.imencode(".png", crop_bgr)
        if not ok:
            return None
        response = self.client.messages.parse(
            model=self.model, max_tokens=1024, output_format=self.schema,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                             "data": base64.standard_b64encode(png.tobytes()).decode()}},
                {"type": "text", "text": PROMPT}]}])
        reading = response.parsed_output
        if response.stop_reason == "refusal" or reading is None or not reading.readable:
            return None
        return reading.rank.upper() + reading.suit.upper()[:1]
