"""Get the pretrained card model, collect your own screenshots, and fine-tune.

Pretrained weights: Hugging Face shrimantasatpati/yolov11_playing_cards_detection
(YOLO11n, MIT licence, 52 classes "10C".."QS", trained 30 epochs on Roboflow
"Playing-Cards-4"; its own validation run reports mAP50 0.995, mAP50-95 0.823).
The Ultralytics library that runs it is AGPL-3.0.

Checked on six independent Wikimedia Commons table photos (see ALGORITHMS.txt):
close-ups read correctly; a full-table view misread most cards until each seat
was cropped first, after which all 10 cards were right. Fine-tune on
screenshots of the real table before trusting it live.

Formats: "torchscript" (default) loads without running pickled Python code.
"pt" is a pickle that runs code when loaded; it is only needed as a starting
point for fine-tuning. Both downloads are pinned by SHA-256.
"""
import hashlib
from pathlib import Path
import shutil
import urllib.request

BASE_URL = ("https://huggingface.co/shrimantasatpati/yolov11_playing_cards_detection/"
            "resolve/main/detect/yolo11n_playing_cards/weights/")
PRETRAINED = {
    "torchscript": ("best.torchscript",
                    "f04419305eb0bf8bf8b8f78d8b85ac78b50f2bbf75941d78eb33262028952157"),
    "pt": ("best.pt", "2617719f994cbb91e974c9f3c3a7f63e83a5cd0d9004342636099c79260260b6"),
}
DEFAULT_PATH = Path("runtime/models/yolo11n_playing_cards.torchscript")
CLASSES = [f"{face}{suit}" for face in ("10", "2", "3", "4", "5", "6", "7", "8", "9",
                                         "A", "J", "K", "Q") for suit in "CDHS"]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_pretrained(fmt="torchscript", dest=None):
    filename, expected = PRETRAINED[fmt]
    dest = Path(dest or DEFAULT_PATH.with_suffix("." + fmt))
    if dest.exists() and sha256(dest) == expected:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(BASE_URL + filename) as response, open(partial, "wb") as out:
        shutil.copyfileobj(response, out)
    actual = sha256(partial)
    if actual != expected:
        partial.unlink()
        raise RuntimeError(f"checksum mismatch ({actual}); refusing to keep the download")
    partial.replace(dest)
    return dest


def write_dataset_yaml(root, classes=CLASSES, extra=("back",)):
    """Dataset layout for fine-tuning: root/images/{train,val}, root/labels/{train,val}.

    Adds a "back" class so face-down cards are learned instead of guessed.
    """
    root = Path(root)
    for split in ("train", "val"):
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)
    names = list(classes) + [c for c in extra if c not in classes]
    lines = [f"path: {root.resolve()}", "train: images/train", "val: images/val", "names:"]
    lines += [f"  {i}: '{name}'" for i, name in enumerate(names)]
    path = root / "data.yaml"
    path.write_text("\n".join(lines) + "\n")
    return path


def finetune(data_yaml, weights, epochs=50, image_size=640, device=None):
    """weights must be a .pt file (fetch_pretrained("pt") or your own)."""
    from ultralytics import YOLO   # optional dependency
    model = YOLO(str(weights))
    return model.train(data=str(data_yaml), epochs=epochs, imgsz=image_size, device=device,
                       project="runtime/train", name="cards")


def evaluate(data_yaml, weights, image_size=640, device=None):
    """Precision/recall/mAP of a model on your labelled val screenshots."""
    from ultralytics import YOLO   # optional dependency
    metrics = YOLO(str(weights), task="detect").val(data=str(data_yaml), imgsz=image_size,
                                                    device=device)
    return {"precision": metrics.box.mp, "recall": metrics.box.mr,
            "mAP50": metrics.box.map50, "mAP50-95": metrics.box.map}
