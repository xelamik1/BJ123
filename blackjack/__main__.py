"""Command line: python -m blackjack <command> [options]

  fetch-model [--format pt]   download the pretrained YOLO card model (checksum pinned)
  calibrate                   save a screenshot of each table with zones and detections drawn
  collect --every 2           save raw table frames for labelling / fine-tuning
  init-dataset DIR            create a YOLO dataset folder + data.yaml (52 cards + "back")
  train DATA_YAML             fine-tune the model on your labelled screenshots
  evaluate DATA_YAML          precision / recall / mAP on your labelled val screenshots
  run [--no-overlay]          watch the tables, count, remember, alert
  history TABLE [--seat S]    print remembered cards for a table or seat
  shoes TABLE                 cards and rounds per shoe (measures penetration)
"""
import argparse
from pathlib import Path
import time

from . import config as config_mod
from .memory import Memory
from .tracker import TableTracker


def _load(args):
    return config_mod.load(args.config)


def cmd_fetch_model(args):
    from .model import fetch_pretrained
    print(fetch_pretrained(args.format, args.dest))


def _draw(frame, table, detections):
    import cv2
    for name, (x, y, w, h) in table.tracker.zones.items():
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 255), 2)
        cv2.putText(frame, name, (x + 4, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)
    for det in detections:
        p1, p2 = (int(det.x1), int(det.y1)), (int(det.x2), int(det.y2))
        cv2.rectangle(frame, p1, p2, (0, 255, 0), 1)
        cv2.putText(frame, f"{det.label} {det.confidence:.2f}", (p1[0], p1[1] - 3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
    return frame


def _detect(detector, frame, table, cfg):
    if cfg.detect_per_zone:
        return detector.detect_zones(frame, table.tracker.zones, cfg.zone_padding)
    return detector.detect(frame)


def cmd_calibrate(args):
    import cv2
    from .capture import ScreenCapture
    cfg = _load(args)
    capture = ScreenCapture()
    detector = None
    if Path(cfg.weights).exists():
        from .detector import YoloDetector
        detector = YoloDetector(cfg.weights, cfg.detector_confidence)
    out = Path("runtime/calibrate")
    out.mkdir(parents=True, exist_ok=True)
    for table in cfg.tables:
        frame = capture.grab(table.region)
        detections = _detect(detector, frame, table, cfg) if detector else []
        path = out / f"{table.id}.png"
        cv2.imwrite(str(path), _draw(frame, table, detections))
        print(path, f"{len(detections)} detections")


def cmd_collect(args):
    import cv2
    from .capture import ScreenCapture
    cfg = _load(args)
    capture = ScreenCapture()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"saving frames to {out} every {args.every}s; Ctrl+C to stop")
    while True:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        for table in cfg.tables:
            cv2.imwrite(str(out / f"{table.id}-{stamp}.png"), capture.grab(table.region))
        time.sleep(args.every)


def cmd_init_dataset(args):
    from .model import write_dataset_yaml
    print(write_dataset_yaml(args.dir))


def cmd_train(args):
    from .model import finetune
    finetune(args.data, args.weights, args.epochs, device=args.device)


def cmd_evaluate(args):
    from .model import evaluate
    cfg = _load(args)
    for key, value in evaluate(args.data, args.weights or cfg.weights, device=args.device).items():
        print(f"{key}: {value:.3f}")


def cmd_run(args):
    from .capture import ScreenCapture, crop
    from .detector import YoloDetector
    from .shuffle import BannerDetector
    cfg = _load(args)
    memory = Memory(cfg.database)
    capture = ScreenCapture()
    detector = YoloDetector(cfg.weights, cfg.detector_confidence)
    reviewer = None
    pending = []
    if cfg.llm.get("enabled"):
        from .llm import ClaudeReviewer
        reviewer = ClaudeReviewer(cfg.llm.get("model", "claude-opus-5-5"))
    trackers, banners = {}, {}
    for table in cfg.tables:
        trackers[table.id] = TableTracker(
            table.id, table.tracker, table.shoe, memory, table.edge,
            review=(lambda tr, tk: pending.append((tr, tk))) if reviewer else None)
        if table.shuffle_banner:
            banners[table.id] = BannerDetector(table.shuffle_banner["template"],
                                               table.shuffle_banner["zone"],
                                               table.shuffle_banner.get("threshold", 0.8))
    manual = set()
    overlay = None
    if not args.no_overlay:
        from .overlay import Overlay
        overlay = Overlay(list(trackers), manual.add)
    crop_w, crop_h = cfg.llm.get("crop_size", [120, 170])
    period = 1 / cfg.fps
    try:
        while True:
            started = time.monotonic()
            for table in cfg.tables:
                tracker = trackers[table.id]
                if table.id in manual:
                    manual.discard(table.id)
                    tracker.new_shoe("manual")
                frame = capture.grab(table.region)
                banner = banners.get(table.id)
                events = tracker.update(_detect(detector, frame, table, cfg),
                                        shuffle_signal=bool(banner and banner.seen(frame)))
                for tr, tk in pending:
                    box = (tk.x - crop_w / 2, tk.y - crop_h / 2, tk.x + crop_w / 2, tk.y + crop_h / 2)
                    reviewer.submit(tr, tk, crop(frame, box))
                pending.clear()
                status = tracker.status()
                if overlay:
                    overlay.show(status)
                for event in events:
                    print(f"[{table.id}] {event}  RC {status['running_count']:+}"
                          f"  TC {status['true_count']:+.2f}"
                          f"{'  ALERT' if status['alert'] else ''}")
            if reviewer:
                reviewer.apply_results()
            if overlay:
                overlay.tick()
            time.sleep(max(period - (time.monotonic() - started), 0))
    except KeyboardInterrupt:
        pass
    finally:
        memory.close()


def cmd_history(args):
    cfg = _load(args)
    memory = Memory(cfg.database)
    zones = [args.seat] if args.seat else sorted(
        {r["zone"] for r in memory.db.execute("SELECT zone FROM cards WHERE table_id=?", (args.table,))})
    for zone in zones:
        rows = memory.seat_history(args.table, zone, args.limit)
        print(f"{zone}: " + " ".join(f"{r['label']}" for r in reversed(rows)))


def cmd_shoes(args):
    cfg = _load(args)
    memory = Memory(cfg.database)
    for row in memory.shoe_summary(args.table, args.limit):
        print(f"shoe {row['id']}  {row['started_at']} -> {row['ended_at'] or 'open'}"
              f"  cards {row['cards']}  rounds {row['rounds']}"
              f"  {'reliable' if row['reliable'] else 'unreliable'}  ({row['end_reason'] or ''})")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m blackjack", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="blackjack/tables.json")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("fetch-model")
    p.add_argument("--format", choices=["torchscript", "pt"], default="torchscript")
    p.add_argument("--dest", default=None)
    p.set_defaults(func=cmd_fetch_model)
    sub.add_parser("calibrate").set_defaults(func=cmd_calibrate)
    p = sub.add_parser("collect")
    p.add_argument("--every", type=float, default=2.0)
    p.add_argument("--out", default="runtime/dataset/unlabelled")
    p.set_defaults(func=cmd_collect)
    p = sub.add_parser("init-dataset")
    p.add_argument("dir")
    p.set_defaults(func=cmd_init_dataset)
    p = sub.add_parser("train")
    p.add_argument("data")
    p.add_argument("--weights", default="runtime/models/yolo11n_playing_cards.pt")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--device", default=None)
    p.set_defaults(func=cmd_train)
    p = sub.add_parser("evaluate")
    p.add_argument("data")
    p.add_argument("--weights", default=None)
    p.add_argument("--device", default=None)
    p.set_defaults(func=cmd_evaluate)
    p = sub.add_parser("run")
    p.add_argument("--no-overlay", action="store_true")
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("history")
    p.add_argument("table")
    p.add_argument("--seat")
    p.add_argument("--limit", type=int, default=100)
    p.set_defaults(func=cmd_history)
    p = sub.add_parser("shoes")
    p.add_argument("table")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_shoes)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
