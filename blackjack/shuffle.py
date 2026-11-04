"""New-shoe signals: an on-screen banner matched by template, plus a manual reset.

Take a screenshot of the provider's shuffle/new-shoe message once, crop it,
and point the table config at it. Until then use the manual reset.
"""


class BannerDetector:
    def __init__(self, template_path, zone, threshold=0.8):
        import cv2          # optional dependency
        self._cv2 = cv2
        self.template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
        if self.template is None:
            raise FileNotFoundError(template_path)
        self.zone = zone    # [x, y, w, h] inside the table region
        self.threshold = threshold

    def seen(self, frame_bgr):
        cv2 = self._cv2
        x, y, w, h = self.zone
        area = cv2.cvtColor(frame_bgr[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
        if area.shape[0] < self.template.shape[0] or area.shape[1] < self.template.shape[1]:
            return False
        scores = cv2.matchTemplate(area, self.template, cv2.TM_CCOEFF_NORMED)
        return float(scores.max()) >= self.threshold
