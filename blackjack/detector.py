"""YOLO card detector (Ultralytics). Imported only when live capture runs.

Cards are small in a full-table view, and the pretrained model misreads them
there. Detecting inside each zone crop (which YOLO scales up to its input
size) read every card correctly in testing, so detect_zones() is the default.
"""
from .tracker import Detection


class YoloDetector:
    def __init__(self, weights, confidence=0.25, image_size=640, device=None):
        from ultralytics import YOLO   # optional dependency
        self.model = YOLO(str(weights), task="detect")
        self.names = self.model.names
        self.confidence = confidence
        self.image_size = image_size
        self.device = device

    def _predict(self, images):
        return self.model.predict(images, conf=self.confidence, imgsz=self.image_size,
                                  device=self.device, verbose=False)

    @staticmethod
    def _boxes(result):
        for box in result.boxes:
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
            yield int(box.cls[0]), float(box.conf[0]), x1, y1, x2, y2

    def detect(self, frame_bgr):
        result = self._predict(frame_bgr)[0]
        return [Detection(self.names[c], conf, x1, y1, x2, y2)
                for c, conf, x1, y1, x2, y2 in self._boxes(result)]

    def detect_zones(self, frame_bgr, zones, pad=20, edge=2):
        """Run the model on each zone crop and map boxes back to frame pixels."""
        h, w = frame_bgr.shape[:2]
        crops, offsets = [], []
        for zx, zy, zw, zh in zones.values():
            x1, y1 = max(int(zx) - pad, 0), max(int(zy) - pad, 0)
            x2, y2 = min(int(zx + zw) + pad, w), min(int(zy + zh) + pad, h)
            if x2 > x1 and y2 > y1:
                crops.append(frame_bgr[y1:y2, x1:x2])
                offsets.append((x1, y1))
        out = []
        for result, crop, (ox, oy) in zip(self._predict(crops) if crops else [], crops, offsets):
            ch, cw = crop.shape[:2]
            for c, conf, x1, y1, x2, y2 in self._boxes(result):
                # A box touching an inner crop edge is a card cut off by the crop; the
                # neighbouring zone's crop sees it whole, so counting it here would double it.
                if ((ox and x1 <= edge) or (oy and y1 <= edge)
                        or (ox + cw < w and x2 >= cw - edge) or (oy + ch < h and y2 >= ch - edge)):
                    continue
                out.append(Detection(self.names[c], conf, x1 + ox, y1 + oy, x2 + ox, y2 + oy))
        return out
