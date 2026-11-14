# BJ123 handoff: build on your Windows 11 PC, push to GitHub

Read this first in a new Claude Code session opened on your PC, in a clone of
`xelamik1/BJ123`. It holds everything decided, built, tested and left open so far.

---

## 1. Goal

A desktop tool that watches **live-dealer online blackjack**, reads every card
off the screen, remembers every card per table, shoe, round and seat, keeps the
count, and tells you **what to bet and how to play** while you sit at the table.

- **Table seen in your video:** Pragmatic Play "Blackjack 105", $5 to $1,000,
  hosted on Rainbet. 1920x1080 recording, 24 fps, about 8 minutes.
- **Table rules you gave:** 6 decks, cut card at the final 20% (so 80% of the
  shoe is dealt), 7 seats, dealer stands on all 17s ("must draw to 16 and stand
  on all 17s" is printed on the felt), blackjack pays 3:2, insurance pays 2:1.
- **How you play:** you sit at 1 or 2 seats and bet according to the count.
  You do not wait for a seat to open (too many variables) and you do not use Bet Behind.

## 2. Rules for any Claude session on this project

- **Card, shoe and rule data stays placeholder until you measure it.** Never
  invent card data, penetration figures or simulated hands. Placeholders now:
  6 decks, 80% penetration, 7 seats, $5 unit, 0.71% house edge, +0.5% per true count.
- **Ask before building something big.** You once said "don't build anything",
  then later asked for a build. Confirm scope first.
- **Everything lives in BJ123.** Never use the NINETY repository for this project.
- **Build on the PC, then push to GitHub.** Not the other way round.
- **Your messages are speech-to-text.** Read for intent.
- **Bankroll management is NOT wanted.** Only a unit size: 1, 2, 5, 10, 20 units,
  with a unit of $5 (configurable).

## 3. The UI you asked for

Simple, black background, local browser page (`python -m blackjack serve`,
http://127.0.0.1:8765).

1. **Top:** the live feed at about 5 FPS, with the YOLO boxes and labels drawn on it.
2. **Under it:** 7 seat tiles in a row, plus the dealer.
   - Each tile shows the cards, the hand total and the bet.
   - **Empty seat = grey. Occupied by someone else = white. Mine = green.**
   - You click to mark one or two seats as yours. Example: 3 taken (white),
     2 empty (grey), 2 mine (green).
3. **For your seats:** the recommended play, using basic strategy plus
   count-based index plays. Your example: 11 against a 5 with a very low count
   means do not double even though basic strategy says to.
4. **Unit size:** "Bet 1 / 2 / 5 / 10 / 20 units" from the true count, shown in $.
5. **A button that wipes everything** for a new shoe, because shuffles can't be
   detected automatically.
6. **History:** previous rounds with each hand's cards, and your own hands marked
   win, loss, push, blackjack or bust.
7. **Edit a misread card:** click a card, type the right one or delete it, and the
   count and the stored data follow.
8. Seat state is inferred from the deal: two cards per occupied seat, then a third
   card means hit, play moving on means stand, a hand splitting in two means split,
   over 21 means bust. A covered middle card doesn't matter because every card is
   logged when it first appears.

## 4. Git state

| Branch | Contents |
|---|---|
| `main` | Only the original `README.md` |
| `claude/blackjack-tracker` | The tracker, commit `e477fa9` (30 tests pass) |
| `claude/new-session-6efxil` | The tracker plus a **work-in-progress** web UI, strategy tables and history. **47 tests run, 4 fail.** |

No pull request exists. Start from `claude/new-session-6efxil`.

Known failing tests (all from the unfinished UI work):
- `Strategy.test_basic_cells`: `IndexError` on `[10, 1]` against a 10 (hand 21 case).
- `Strategy.test_no_double_with_three_cards`: soft 18 against a 3 should stand when doubling isn't allowed, returns hit.
- `Strategy.test_surrender_setting`: 16 against a 9 with surrender on should surrender, returns hit.
- `Config.test_example_config_loads`: still expects the old 8-deck shoe (416 cards). It is now 6 decks (312). Update the test.

## 5. Repo layout

```
README.md                  setup, commands, tests
HANDOFF.md                 this file
blackjack/
  __main__.py              CLI (section 7)
  cards.py                 parse labels ("10C","AH","back") -> Card; hand_total
  counting.py              count systems, ShoeConfig, Shoe, EdgeModel, unit ramp (new)
  indices.py               Illustrious 18 + Fab 4 surrender (Hi-Lo), insurance
  strategy.py              basic strategy (new, WIP, 3 failing tests)
  memory.py                SQLite store: shoes, rounds, cards, events
  history.py               round history and win/loss results for the UI (new, WIP)
  tracker.py               TableTracker: zones, merge, tracks, commit, rounds, shoes
  detector.py              YoloDetector, per-seat crops
  capture.py               mss screen capture
  shuffle.py               shuffle-banner template match
  llm.py                   optional Claude review of low-confidence cards
  model.py                 model download, dataset scaffold, fine-tune, evaluate
  overlay.py               old tkinter window (superseded by the web UI)
  server.py                local web server, MJPEG feed, /api/* (new, WIP)
  web/                     index.html, app.js, style.css (new, WIP)
  config.py, tables.example.json, requirements.txt, ALGORITHMS.txt
tests/test_blackjack.py
research/                  full research report and notes
```

## 6. How the pipeline works

1. **Capture:** `mss` grabs the table region at `fps` (aim for 5 to 10).
2. **Detect:** YOLO runs per seat zone. Boxes touching a crop edge are dropped.
3. **Merge:** both printed corners of a card are boxed, and same-label boxes within
   `merge_distance` are merged across the frame before a zone is assigned.
4. **Zone:** the merged centre decides `dealer` or `seat1`..`seat7`.
5. **Track:** each card matches the nearest track in its zone within
   `match_distance`, adding a confidence-weighted vote each frame.
6. **Commit:** after `stable_frames` (3) the best label is counted once and written
   to SQLite. Later votes that beat it by `correction_margin` (1.5x) correct it.
   Face-down ("back") cards are never counted until they turn over.
7. **Memory:** tracks persist while cards leave the screen. A round ends after
   `empty_frames_round_end` (15) empty frames. A restart rebuilds the open shoe
   from the database and restores the cards still on the felt.
8. **Unreliable shoe:** alerts are suppressed if tracking started mid-shoe, resumed
   after 120 s, or saw more of a rank than the shoe holds.
9. **New shoe:** the manual button, the shuffle banner, or an idle timeout.
10. **Status:** running and true count, decks left, penetration, edge, insurance,
    seats to hands, and the index play for your seat.
11. **Optional Claude fallback:** low-confidence cards are re-read by Claude in a
    background thread.

SQLite schema (`runtime/blackjack.sqlite3`): `shoes`, `rounds`, `cards`, `events`.

## 7. Commands

```
python -m blackjack [--config blackjack/tables.json] <command>
  fetch-model [--format torchscript|pt]   download the pretrained model (checksum-pinned)
  calibrate                               save runtime/calibrate/<table>.png with zones and detections
  collect --every 2                       save raw frames for labelling
  init-dataset DIR                        YOLO dataset folders + data.yaml
  train DATA_YAML --weights <.pt>         fine-tune
  evaluate DATA_YAML                      precision, recall, mAP
  run [--no-overlay]                      live loop with the old tkinter window
  serve [--port 8765] [--video F] [--no-capture]   local web UI (WIP)
  history TABLE [--seat S]                stored cards per seat
  shoes TABLE                             cards and rounds per shoe
```

Run the tests: `python -m unittest discover -s tests -v`

## 8. Set up on Windows 11

Install Python 3.11 or 3.12 from python.org (tick "Add python to PATH") and Git.
Use PowerShell:

```powershell
git clone https://github.com/xelamik1/BJ123.git
cd BJ123
git checkout claude/new-session-6efxil
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r blackjack\requirements.txt
```

- **Allow scripts once** if activation is blocked:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
- **NVIDIA GPU:** install the CUDA build of PyTorch first, from the selector at
  pytorch.org (it gives the exact `pip` line), then `pip install -r blackjack\requirements.txt`.
  Training on a GPU takes minutes. On CPU it takes hours.
- **Config:** copy `blackjack\tables.example.json` to `blackjack\tables.json`
  (git-ignored) and set the screen region for your game window.
- **Game window:** run it as large as you can, borderless or maximised, always on
  the same monitor and position. Zones are pixel positions, so moving the window
  breaks them.
- **High-DPI:** if Windows display scaling is not 100%, capture coordinates may be
  scaled. Check with `calibrate`.
- **Push when done:** `git add -A`, `git commit -m "..."`, `git push`.

Test on your recording without the screen:
`python -m blackjack serve --video path\to\recording.mp4`

## 9. The YOLO model

### Candidates tried
| Model | Source | Classes | Notes |
|---|---|---|---|
| `shrimantasatpati/yolov11_playing_cards_detection` | Hugging Face | 52 | YOLO11n, MIT. Trained on photos of physical cards. `best.torchscript` SHA-256 `f04419305eb0bf8bf8b8f78d8b85ac78b50f2bbf75941d78eb33262028952157` (verified). `best.pt` SHA-256 `2617719f994cbb91e974c9f3c3a7f63e83a5cd0d9004342636099c79260260b6` is a pickle: only load it yourself for fine-tuning. |
| `sroot/lgd-cards-gen3` | Hugging Face | 52 | YOLO11s, **AGPL-3.0**. Fine-tuned on casino table video. Reported recall 0.847 and precision proxy 0.771 on its own private 225-frame holdout. Files: `model.onnx` (38 MB), `best.pt`. Gen4 was reverted for regressions, so use gen3. |
| `sroot/lgd-cards-gen1`, `gen2` | Hugging Face | 52 | Earlier generations, superseded. |
| `mustafakemal0146/playing-cards-yolov8`, `qcxiong/playing-cards-yolov8` | Hugging Face | 52 | YOLOv8n, MIT. No metrics. |

### Results so far
- **Earlier test (cloud, public photos):** per-seat crops through the tracker read
  24 of 25 cards right with 0 false, using the shrimantasatpati model.
- **Your video, frame 9 (2025 table):** both models above found **0 cards** when
  given the whole table area at 640 and 1280 px. The cards in your video are only
  about 45 to 80 px wide, so they are tiny for a model trained on close-ups.
  I did not get to test zoomed-in per-seat tiles on the video.
- **No ready-made model exists** for Pragmatic or Evolution live-dealer footage
  that I could find (web search only; Hugging Face, Roboflow and the Dubach blog
  could not be opened from the cloud container, so check them yourself).

### Plan
1. On your PC, run both models on **per-seat crops upscaled 2x to 3x** from frames
   of your video. This is the quickest test and may already work.
2. If it doesn't, **fine-tune** one of them. A public write-up (Philipp Dubach,
   philippdubach.com, "counting cards with computer vision") reached 99.5% mAP50
   from about 409 labelled cards in 117 frames on one fixed table layout. Aim for
   150 to 300 labelled frames; more if you want several tables or lighting.
3. **Label the rank only** (13 classes, or even 3 buckets: 2-6, 7-9, 10-A) if the
   suit confuses the model. Hi-Lo doesn't need suits. Suits stay useful for the
   history display.
4. **Include face-down dealer cards** as a class so they aren't read as face-up.
5. **Hold out whole rounds** as validation, not random frames, so near-duplicate
   frames don't inflate the score.
6. Collect frames with `python -m blackjack collect --every 2`, label them in
   Roboflow or CVAT, then `init-dataset`, `train`, `evaluate`.
7. **Licence note:** Ultralytics itself and `sroot/lgd-cards-gen3` are AGPL-3.0.
   That is fine for private personal use. Check it before you share the tool.

Possible extra sources of training data (none verified by opening): Roboflow
Universe blackjack sets such as `blackjack-dyhtk/card-op9fv` (568 images) and
`cvaimodels/blackjack_dataset_v1` (512 images), and general card sets
(`lucas-chan/playing-card-object-detection`, about 6,000 images).

## 10. What your video shows (frame notes)

- Seats are arranged on an arc. Each seat has a circle with a bet chip when
  occupied, and an empty seat shows a faint ring or a person icon.
- Each hand's total appears as a small white badge near the cards (for example
  18, 16, 19). **Use these badges to cross-check the cards the app read.**
  A mismatch should flag the seat for you to fix instead of miscounting silently.
- The dealer's up-card sits at the top centre, with the dealer total badge above it.
- A banner reads "WAIT FOR NEXT GAME" or "PLEASE TAKE A SEAT" between rounds.
- Overlays on top of the table (an "Insufficient funds" pop-up, a chat box, a
  rotating countdown over the dealer) can cover cards. Close the pop-up before
  running, and keep the zones away from the top of the screen.
- Cards overlap in fanned hands and are viewed at an angle, so a card's corner may
  be the only part visible. The tracker already tracks the corner and merges both
  printed corners.
- Cards in the first screenshot you gave (a different table) are about 45 px wide
  at 1143 px window width. In the 1080p video they are larger but still small.

## 11. Research findings (full report in `research/`)

None of the rules could be checked against an official provider rulebook; the
in-game help panel is the only authoritative source.

- **Peek with a 10 up is disputed** for the Evolution tables. Pragmatic's rules
  need checking in the in-game help.
- **Other providers:** Pragmatic reportedly allows double after split since June
  2025 (RTP 99.41%) with roughly 50 to 55% penetration. Ezugi allows double after
  split. Playtech doesn't peek and refunds half the double against a blackjack.
- **Avoid:** infinite, power and lightning blackjack, and any table that reshuffles
  every round.
- **Hi-Lo:** 2-6 = +1, 7-9 = 0, T/A = -1. True count = running count / decks left.
- **Edge** is roughly the base edge plus 0.5% per true count. Break-even sits
  around true count +1.4 with a 0.71% base edge.
- **Variance** is about 1.3 per hand. Spreading bets to 20 units at high counts
  with a small bankroll carries real risk of ruin; the app shows units, not bankroll.
- **Legal and terms of service (general information, not legal advice):** counting
  in your head is legal everywhere checked. Device laws are written for casino
  premises (Nevada, New Jersey). The real risk is the operator's terms: bans on
  third-party software, voided winnings, closed accounts. An operator can see every
  card next to every bet, so a spectate-then-join or big bet-spread pattern is easy
  to spot. Rainbet's terms were not read.
- **Observation checklist** (23 items) is in the research report. Key unknowns:
  cards dealt per shoe, peek rule with a 10 up, shuffle signals, seat availability,
  cut-card position, rounds per hour.

## 12. Open items, in priority order

1. **Prove card reading on your video.** Test per-seat upscaled crops with both
   models. Score every card by eye on 20 to 30 frames. Fine-tune if recall is poor.
2. **Finish the web UI** (section 3) and fix the 4 failing tests.
3. **Seat occupancy** from the chip circle or empty-seat marker.
4. **Hand total badge cross-check** to catch misreads.
5. **Fixed zones for the Pragmatic layout** (7 seats and the dealer) from a real frame.
6. **Round results** for your hands (win, loss, push, blackjack, bust).
7. **Basic strategy for these rules**, then check it against the in-game help.
8. **Replace placeholders** with observed values.
9. **Shuffle banner template** if one appears reliably.
10. **Known limits:** two identical cards close together in one seat could merge;
    the 0.6 confidence floor was tuned on one photo; hand grouping uses only the x-gap.

## 13. Environment notes

- The cloud container blocked Hugging Face, PyTorch's CPU wheel host and Roboflow by
  default. Hugging Face hosts were allowed for this environment, which is not needed
  on your PC.
- The cloud session refused to load `.pt` pickle files from outside sources and to
  force-push. Nothing relies on either.
- The cloud container has no tkinter and no screen, so live capture can only be
  tested on your PC. `serve --video` works in either place.
- The first build went into the NINETY repository by mistake and was removed.
  Do not use NINETY for this project.
