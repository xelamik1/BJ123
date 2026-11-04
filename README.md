# BJ123

Card counting tool for live-dealer blackjack tables. It reads cards off the
screen with a YOLO model, remembers every card per table, shoe, round and seat
in SQLite, and keeps Hi-Lo (and other) running and true counts.

All shoe, rule and seat-layout values in `blackjack/tables.example.json` are
placeholders until measured at real tables.

## Setup

```sh
pip install -r blackjack/requirements.txt
python -m blackjack fetch-model            # pretrained YOLO11n card model, checksum pinned
cp blackjack/tables.example.json blackjack/tables.json   # then set your screen regions and seats
python -m blackjack calibrate              # saves runtime/calibrate/<table>.png to check zones
python -m blackjack run
```

Other commands: `collect`, `init-dataset`, `train`, `evaluate`, `history`, `shoes`
(`python -m blackjack --help`).

## Tests

```sh
python -m unittest discover -s tests -v
```

The core tracker and tests need no extra packages; live capture needs the
packages in `blackjack/requirements.txt`.

## Docs

- `blackjack/ALGORITHMS.txt`: how the counting works, and the model test results
- `research/`: research report (table rules, counting maths, vision tech, legal and
  detection risks) and the notes behind it
