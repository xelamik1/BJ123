"""Screen capture of each table's region with mss (works on Windows, macOS, Linux)."""


class ScreenCapture:
    def __init__(self):
        import mss          # optional dependency
        import numpy as np
        self._np = np
        self._mss = mss.mss()

    def grab(self, region):
        """region = {"left", "top", "width", "height"}; returns a BGR numpy array."""
        shot = self._mss.grab(region)
        return self._np.asarray(shot)[:, :, :3].copy()   # BGRA -> BGR


def crop(frame, box, pad=6):
    """Crop (x1, y1, x2, y2) from a frame with a little padding."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = (int(v) for v in box)
    return frame[max(y1 - pad, 0):min(y2 + pad, h), max(x1 - pad, 0):min(x2 + pad, w)]
