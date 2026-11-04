"""Load the tables config (see blackjack/tables.example.json)."""
from dataclasses import dataclass
import json
from pathlib import Path

from .counting import EdgeModel, ShoeConfig
from .tracker import TrackerSettings


@dataclass
class TableConfig:
    id: str
    region: dict                 # screen region {"left", "top", "width", "height"}
    tracker: TrackerSettings
    shoe: ShoeConfig
    edge: EdgeModel
    shuffle_banner: dict | None


@dataclass
class AppConfig:
    weights: str
    database: str
    fps: float
    detector_confidence: float
    detect_per_zone: bool
    zone_padding: int
    llm: dict
    tables: list


def _strip_notes(data):
    if isinstance(data, dict):
        return {k: _strip_notes(v) for k, v in data.items() if not k.startswith("_")}
    if isinstance(data, list):
        return [_strip_notes(v) for v in data]
    return data


def load(path):
    data = _strip_notes(json.loads(Path(path).read_text()))
    defaults = data.get("defaults", {})
    tables = []
    for table in data["tables"]:
        merged = {key: {**defaults.get(key, {}), **table.get(key, {})}
                  for key in ("tracker", "shoe", "edge")}
        tables.append(TableConfig(
            id=table["id"], region=table["region"],
            tracker=TrackerSettings.from_dict(merged["tracker"]),
            shoe=ShoeConfig.from_dict(merged["shoe"]),
            edge=EdgeModel(**merged["edge"]),
            shuffle_banner=table.get("shuffle_banner")))
    return AppConfig(weights=data.get("weights", "runtime/models/yolo11n_playing_cards.torchscript"),
                     database=data.get("database", "runtime/blackjack.sqlite3"),
                     fps=float(data.get("fps", 10)),
                     detector_confidence=float(data.get("detector_confidence", 0.25)),
                     detect_per_zone=bool(data.get("detect_per_zone", True)),
                     zone_padding=int(data.get("zone_padding", 0)),
                     llm=data.get("llm", {"enabled": False}), tables=tables)
