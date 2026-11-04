# Vision Tech for a Live-Dealer Blackjack Card Tracker (survey, as of Oct 2026)

Scope note: this is a literature and tools survey. No card data was created or simulated and no project code was written. About 18 tool calls were used. Some hosts could not be reached (gh.r-mj.com mirror; `gh search` is blocked in this session, so the GitHub MCP search was used instead).

## Screen capture in Python (mss, dxcam/BetterCam, PIL ImageGrab, OBS virtual camera)

### Takeaway
On Windows, DXcam (built on the Desktop Duplication API) is the fastest documented option. Its author measured about 239 fps against about 76 fps for python-mss. mss is the portable cross-platform choice and is thread-safe. A live-dealer stream runs at about 25 to 30 fps and cards change on a scale of seconds, so even mss at roughly 30 to 76 fps is more than enough. Capture speed is not the bottleneck; recognition and the logic that decides which cards are new are.

### Cited Findings
- DXcam author benchmark (Ryzen 5900X + RTX 3090, 240 Hz output): DXcam 239.19 fps, D3DShot 118.36 fps, python-mss 75.87 fps. When targeting 60 fps DXcam hit 61.71 and D3DShot 47.11. When targeting 30 fps DXcam hit 30.08. The author says some claims of 1000+ fps really measure repeated reads of stale frames. — [DXcam README](https://github.com/ra1nty/DXcam)
- DXcam API: `camera.grab(region=(left, top, right, bottom))` returns a NumPy array. The streaming form is `camera.start(region=..., target_fps=60)` plus `get_latest_frame()`. The default target is 60, and values above 120 are "resource heavy". It is Windows-only and MIT-licensed, with wheels for CPython 3.10 to 3.14. An optional `winrt` (Windows Graphics Capture) backend is available. — [DXcam README](https://github.com/ra1nty/DXcam)
- A third-party benchmark from a competing project (rustcam v0.0.5) found one-shot `grab()` faster than `start()`/`get_latest_frame()`. On a 180 Hz source BetterCam `start()` delivered about 125 fps and dxcam about 155 fps. On moving content, dxcam.start() reportedly dropped to about 3 fps and BetterCam to about 60 fps, with only 60% of frames fresh. Treat this with caution because the source is a competitor. — [rustcam tags (GitLab)](https://gitlab.com/zenham/rustcam/-/tags/v0.0.5)
- An anecdotal user report: DXcam over 90 fps against about 30 fps with mss or Pillow. — [vidgear issue #316](https://www.github.com/abhiTronix/vidgear/issues/316)
- python-mss describes itself as an "ultra fast cross-platform multiple screenshots module in pure python using ctypes". It is thread-safe and supports capturing part of the screen or of a second monitor using `top/left/width/height` dicts or a PIL-style bbox. The latest release listed is 10.2.0, with deprecations planned for 11.0. — [python-mss docs](https://python-mss.readthedocs.io/en/latest/)

### Inferences
- Recommended layering: use mss as the cross-platform default and DXcam as an optional Windows fast path. Prefer `grab(region=...)` polling at a fixed 10 to 15 Hz over `start()` mode, given the stale-frame reports.
- Capturing a browser region: the simplest robust method is a user-calibrated rectangle, stored as fractions of the window so it survives resizing. Desktop Duplication captures the composited desktop, so the browser must not be covered by other windows. Windows Graphics Capture (the DXcam `winrt` backend) can capture a single window.
- An OBS virtual camera (read with `cv2.VideoCapture`) adds an encode step and latency. It is mainly useful for crop or scale preprocessing or for sending capture to another machine. No sourced latency numbers were found.

### Gaps
- No independent milliseconds-of-latency measurements were found for mss, DXcam, BetterCam, PIL ImageGrab or OBS virtual camera. These need benchmarking on the target hardware.
- macOS: mss works, but the macOS Screen Recording permission and Retina scaling were not researched with sources here. The ScreenCaptureKit Python bindings were not researched.
- No README data was fetched for BetterCam (RootKit-Org/BetterCam), such as stars or maintenance status.

## Card recognition approaches (template matching, contours, CNN, YOLO, OCR)

### Takeaway
For a fixed-camera streamed table, a small YOLO detector fine-tuned on screenshots of the actual table is the most proven route. One write-up went from 80.5% to 99.5% mAP@50 using about 177 screenshots after cleaning the labels. Classical contour plus template matching (EdjeElectronics, 744 stars) is fast and needs no training, but it is fragile to background, scale and overlap. OCR engines are a poor fit for card corners: EasyOCR missed about half of cropped cards in one test.

### Cited Findings
- Dubach's YOLO11 write-up:
  - Setup: fine-tuned YOLO11s on screenshots of an online blackjack table.
  - Dataset: an initial 117 images with 409 annotated cards, plus 60 more screenshots added later.
  - Accuracy: 80.5% mAP@50 on the first run, 99.5% mAP@50 after fixing annotations. Some boxes had included neighbouring card backs, which made face-down dealer cards register as cards.
  - Training: 13 minutes on a free Colab T4.
  - Speed: local inference about 45.5 ms per image (plus 1.3 ms preprocess and 0.4 ms postprocess). Roboflow's hosted API took about 4 s per call.
  - Data source: Roboflow Universe "cards-agurd/playing_card_classification".
  - [Philipp Dubach, "Counting Cards with Computer Vision"](https://philippdubach.com/posts/counting-cards-with-computer-vision/index.md)
- EasyOCR on YOLO crops: the readings it made were correct, but it failed to detect about half of the cards even when they were pre-cropped, so it was rejected. — [Dubach](https://philippdubach.com/posts/counting-cards-with-computer-vision/index.md)
- Ultralytics YOLO11 on COCO at 640 px:

  | Model | mAP50-95 | CPU ONNX | T4 TensorRT | Params |
  |---|---|---|---|---|
  | YOLO11n | 39.5 | 56.1 ms | 1.5 ms | 2.6M |
  | YOLO11s | 47.0 | 90.0 ms | 2.5 ms | 9.4M |
  | YOLO11m | 51.5 | 183.2 ms | 4.7 ms | 20.1M |

  The docs point to YOLO26 (NMS-free, edge-optimized) for new work and say YOLO27 is "coming soon". — [Ultralytics YOLO11 docs](https://docs.ultralytics.com/models/yolo11/)
- Roboflow Universe datasets offering YOLOv8 export:
  - Augmented Startups "playing-cards-ow27d" v4: 24,240 images at 640x640, split 21,210/2,020/1,010 — [Roboflow](https://universe.roboflow.com/augmented-startups/playing-cards-ow27d/dataset/4)
  - Skypea fork: synthetic cards blended onto backgrounds, labelled by rank and suit — [Roboflow](https://universe.roboflow.com/skypea/playing-cards-ow27d-9pnmd)
  - 7up (6,617 images) — [Roboflow](https://universe.roboflow.com/7up/playing-cards-u87ak/dataset/1)
  - mohammad-almasri (6,826 images) — [Roboflow](https://universe.roboflow.com/mohammad-almasri/playing-cards-dataset8/dataset/5)
  - steven-mcgee (1,803 images) — [Roboflow](https://universe.roboflow.com/steven-mcgee-np7ah/detect-playing-cards/dataset/1)
  - The search returned no published mAP numbers for these listings.
- Classical template matching: the OpenCV forum warns that `matchTemplate` is a specific kind of template matching that "will not work" for matching one card against many templates in an unconstrained setup. Feature matching or contour finding was suggested instead. — [OpenCV forum](https://forum.opencv.org/t/using-template-matching-to-identify-playing-cards/3390)
- The classical pipeline (dofire): threshold, find the card contour, isolate the corner, split rank and suit, then compare against stored rank and suit images. — [dofire/OpenCV-Playing-Card-Detection](https://github.com/dofire/OpenCV-Playing-Card-Detection)
- A CNN alternative classifies rank and suit with a neural net instead of templates. — [dharm1k987/Card_Recognizer](https://github.com/dharm1k987/Card_Recognizer)
- OCR engines, general benchmarks (none were specific to digits or cards):
  - Speed: Tesseract is fastest at about 0.16 s per page, against about 0.66 s for EasyOCR and 4.85 s for PaddleOCR on an M-series CPU.
  - Accuracy on one invoice: PaddleOCR 100%, Tesseract 87.5%, EasyOCR 62.5%.
  - PaddleOCR is best on rotated, noisy or low-resolution input.
  - Sources: [Codesota](https://codesota.com/ocr/best-for-python); [invoicedataextraction.com](https://invoicedataextraction.com/blog/python-ocr-library-comparison-invoices). A separate test found all three equally accurate on clean 300 DPI text — [DEV Community](https://dev.to/felipe_anyformat/best-python-ocr-libraries-179). Codesota notes that many PaddleOCR vs EasyOCR speed comparisons are not like-for-like — [Codesota](https://codesota.com/ocr/paddleocr-vs-easyocr).

### Inferences
- If the provider UI draws digital card icons or a hand-total badge, matching the icon crops at a known scale, with `matchTemplate` and one template per rank, will likely be the cheapest and most accurate signal. The scale is fixed once the browser zoom is fixed. The forum warning applies to unconstrained physical-card photos, not to fixed-pixel UI sprites. Multi-scale matching (an image pyramid) is only needed if the window size changes.
- For physical cards in the video, a hybrid works best. YOLO11n/s or YOLO26n finds the card boxes, then rank-only classification decides the count, because Hi-Lo only needs the rank. Classes can collapse to 13 ranks, or even 3 count buckets as an auxiliary head, which reduces confusion between suits.
- For counting, the 10/J/Q/K distinction does not matter. A detector that confuses face cards with 10 costs nothing.
- OCR is useful mainly for large on-screen text such as hand totals, "Shuffle" or "Place your bets" banners and seat totals, not for card corners. PaddleOCR or Tesseract with a digit whitelist on a binarized crop is the likely best fit.
- The public Roboflow sets are mostly photos of physical cards on a table. The domain gap to compressed overhead studio video means a few hundred labelled frames from the target table matter more than dataset size, which matches Dubach's experience.

### Gaps
- No published mAP or FPS was found for models trained on the specific Roboflow sets listed, or on studio-stream footage specifically.
- It is unconfirmed whether Evolution's UI shows per-card digital icons or only hand totals. Searches returned no reliable Evolution UI documentation, so this has to be checked by looking at the actual client.
- No sources were found on how video compression or motion blur affects card-corner recognition at stream bitrates.

## Vision LLM (Claude) as low-confidence fallback

### Takeaway
Claude accepts cropped images cheaply: a 200x200 crop is 64 visual tokens, roughly $0.06 to $0.26 per 1,000 crops at Haiku 4.5 or Opus 5.5 input prices before prompt and output tokens. Responses can be forced to match a JSON schema with `output_config.format`. One practitioner measured 99.9% accuracy on YOLO-cropped cards but found it too slow for real-time use. It therefore suits occasional, asynchronous disambiguation, not the main path.

### Cited Findings
- Token cost is `ceil(width/28) × ceil(height/28)` visual tokens:
  - 200x200 is 64 tokens.
  - 1000x1000 is 1,296 tokens.
  - 1920x1080 is 1,560 tokens on the standard tier (downscaled to 1456x819) or 2,691 on the high-resolution tier (Claude 4.7 and later; long edge up to 2,576 px, at most 4,784 tokens).
  - [Anthropic Vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)
- Pricing examples from the docs: Haiku 4.5 at $1 per million input tokens makes a 1000x1000 image about $1.30 per 1,000 images. Opus 5.5 at $4 per million makes it about $5.18 per 1,000 images. — [Anthropic Vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)
- Documented limits:
  - Claude "might hallucinate or make mistakes when interpreting low-quality, rotated, or very small images under 200 pixels".
  - Counting is approximate.
  - Coordinates are approximate.
  - Maximum 8000x8000 px per image and 10 MB base64 per image on the API. Above 20 images per request, keep each image under 3,000 px.
  - [Anthropic Vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)
- Structured output:
  - How to request it: `output_config: {format: {type: "json_schema", schema: {...}}}`. Constrained decoding guarantees schema-valid JSON. The Python SDK's `client.messages.parse()` accepts a Pydantic model. `output_format` is deprecated.
  - Exceptions to check for: `stop_reason: "refusal"` or `"max_tokens"`. Enum values may differ only in capitalization.
  - Unsupported schema features: numeric or length constraints, and `minItems` greater than 1.
  - Supported models: Haiku 4.5 and 5.5, Sonnet 4.5 and later, Opus 4.5 and later.
  - The first use of a schema adds compilation latency; compiled schemas are cached for 24 hours.
  - [Anthropic Structured Outputs docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- Accuracy and speed in practice: YOLO crops plus Claude vision gave 99.9% accuracy, but "too slow for real-time". No latency figure was given. — [Dubach](https://philippdubach.com/posts/counting-cards-with-computer-vision/index.md)

### Inferences
- Design pattern: only send crops whose detector confidence is below a threshold, or where frames disagree. Upscale card crops so they are at least 200 px on the short side, given the documented weakness on images under 200 px. Request an enum schema such as `{"rank": "A|2|...|K|unknown", "confidence": ...}` and include an explicit "unknown" option to reduce forced guesses. Apply the result asynchronously as a count correction.
- A batch of several crops in one request amortizes prompt overhead.

### Gaps
- No measured round-trip latency (in seconds) was found for Claude image calls on small crops. Expect it to vary by model, so measure it.
- No independent benchmark of LLM accuracy on playing-card rank reading was found beyond Dubach's single anecdote.
- Current Haiku 5.5 and Sonnet 5.5 per-token prices were not fetched; only the doc's examples above are cited. Check [claude.com/pricing](https://claude.com/pricing).

## De-duplication across frames, splits, dealer hole card, occlusion, round and shoe boundaries

### Takeaway
The existing hobby projects use simple temporal heuristics: majority voting over frames and a per-class cooldown. These break when the same rank appears twice in a round. A more robust design ties each card to a spatial slot (seat × card index, plus dealer) and counts a card only once it has stayed stable for N frames. Each slot is counted once per round, and the slots reset when a round boundary is detected.

### Cited Findings
- AceTrack-AI uses YOLO11 with temporal majority voting and a 4-second cooldown per recognized card class to prevent double-counting. This comes from a search snippet; the README could not be fetched because the mirror host was unreachable. — [AceTrack-AI (search result)](https://gh.r-mj.com/zer0dayf/AceTrack-AI)
- Face-down dealer cards were mistaken for valid cards until the labels were fixed. A "card back" negative class or clean labels are needed. — [Dubach](https://philippdubach.com/posts/counting-cards-with-computer-vision/index.md)
- Shoe context:
  - Evolution lists Salon Privé blackjack as 8-deck — [theScore Bet help (Evolution)](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873608581645-Salon-Prive-Blackjack-A)
  - A secondary guide says live 8-deck games commonly run near 50% penetration and some use continuous shuffling machines — [deucescracked live blackjack](https://www.deucescracked.com/casino/blackjack/live-dealer-blackjack). This is not confirmed for Evolution specifically.
  - A forum claim of 6 decks with a 75% cut is unverified and conflicts with the above.
  - Some studios use a digital "player cut" prompt that tells the dealer where to place the cut card — [dlu.co.id](https://dlu.co.id/live-blackjack-card-shuffling-procedures). This is a low-quality source.

### Inferences
- Slot-based state machine:
  - The ROIs are fixed because the camera is fixed.
  - A card is committed when the same rank is seen in the same slot for at least K consecutive frames, or for a majority of a window, with confidence above the threshold.
  - Committed slots are never re-counted.
  - When a new detection appears in a slot to the right of or below an existing card, it becomes the next index.
  - Splits appear as a seat's cards moving into two groups. Re-key by spatial clustering, and do not count cards again when they move. Track identity with IoU or centroid tracking (ByteTrack or BoT-SORT are built into Ultralytics' `track` mode) so a moved card keeps its ID.
- Dealer hole card: count it only when it is revealed (a back turning into a face in the dealer slot). If the round ends without a reveal, for example everyone busts, the card is never seen and should not be counted.
- Round boundary: all slots empty for at least N frames, a "place your bets" or "bets closed" banner (OCR or template), or a betting timer reappearing. Shuffle or new shoe: OCR or template-match the shuffle banner or message, and allow a manual reset hotkey as a fallback. Treat a long period with no cards plus the shuffle text as a reset of the running count.
- Occlusion (dealer hands, card overlap): only commit when a card is stable. Use the hand-total OCR as a consistency check: the sum of committed card values in a seat should equal the total on screen. On a mismatch, flag the seat for an LLM fallback.
- A per-class cooldown (AceTrack's approach) is wrong whenever duplicate ranks are dealt in one round, which is very common with 8 decks. Prefer slot or track identity.

### Gaps
- No primary Evolution documentation was found on shoe size, penetration, CSM use or on-screen shuffle messages per table variant. For example, Infinite Blackjack's shuffling was not verified.
- No published evaluation of de-duplication accuracy for any open-source project was found.

## Existing open-source projects

### Takeaway
The ecosystem is made up of small hobby or student repos, all under 20 stars except one. The most mature reusable pieces are EdjeElectronics' classical OpenCV detector (744 stars) and the YOLO plus Hi-Lo counters. None is a polished, maintained live-casino screen reader.

### Cited Findings (stars as of the Oct 2026 GitHub search)
- [EdjeElectronics/OpenCV-Playing-Card-Detector](https://github.com/EdjeElectronics/OpenCV-Playing-Card-Detector): 744 stars, 232 forks, updated Oct 2026. Classical OpenCV pipeline (contour, corner, rank and suit template) on PiCamera video. Reusable: corner isolation and rank/suit template logic.
- [dofire/OpenCV-Playing-Card-Detection](https://github.com/dofire/OpenCV-Playing-Card-Detection): 16 stars. Jupyter version of the threshold, contour, corner and rank/suit comparison pipeline.
- [darcyg32/Automated-Blackjack-Assistant](https://github.com/darcyg32/Automated-Blackjack-Assistant): 4 stars. Card counting with CV plus ML; updated Aug 2026.
- [tomalmog/CV-CardCounting](https://github.com/tomalmog/CV-CardCounting): 2 stars. Custom YOLOv8, real-time count; updated Sep 2026.
- [S-Panjwani/JackBlack](https://github.com/S-Panjwani/JackBlack): 2 stars. Pretrained YOLO and a running count; created Jan 2026.
- [irudrakshgupta/Real-Time-Blackjack-Poker-Counter](https://github.com/irudrakshgupta/Real-Time-Blackjack-Poker-Counter): 2 stars. Camera or manual input, Hi-Lo, "whisper-mode" audio prompts and a stealth UI. Reusable as UI and audio reference.
- [Gonzi09/Blackjack-AI-Card-Counter](https://github.com/Gonzi09/Blackjack-AI-Card-Counter): 0 stars. Running and true count with an on-screen overlay.
- [rushman454/blackjack-computer-vision-card-counter](https://github.com/rushman454/blackjack-computer-vision-card-counter): 0 stars. NumPy and OpenCV webcam counter.
- [jtlocati/ALAN](https://github.com/jtlocati/ALAN): 0 stars. CV table reader that scores how likely a player is to be card counting (the casino-side view).
- [Greg2828/blackjack-cv](https://github.com/Greg2828/blackjack-cv): two YOLOv8 detectors on a Raspberry Pi camera, studying whether a detector can classify a counting player.
- ianjure/blackjack-card-counter: YOLOv8s trained on Roboflow cards with Hi-Lo; 1 star, last push Aug 2024 — [ecosyste.ms listing](https://awesome.ecosyste.ms/projects/github.com%2Fianjure%2Fblackjack-card-counter)
- zer0dayf/AceTrack-AI: YOLO11, temporal majority voting, 4 s per-class cooldown — [mirror link (unreachable)](https://gh.r-mj.com/zer0dayf/AceTrack-AI)
- mihkuno/VRACKJACK: YOLOv5 with an augmented-reality web client — [mirror link](https://gh.r-mj.com/mihkuno/VRACKJACK)
- [dharm1k987/Card_Recognizer](https://github.com/dharm1k987/Card_Recognizer): neural-network rank and suit classifier.
- Dubach's write-up and Monte Carlo odds gist (no CV repo published) — [blog](https://philippdubach.com/posts/counting-cards-with-computer-vision/index.md)

### Inferences
- Nearly all of these target physical cards in front of a webcam, not browser streams. The reusable parts are the training recipes, the Hi-Lo logic and the overlay ideas, not end-to-end code.
- The training recipe from Dubach is the most actionable: label 100 to 200 screenshots of the target table, fine-tune YOLO11s or YOLO26, and keep labels tight.

### Gaps
- Licenses, code quality and recent commit activity of most small repos were not checked.
- `geaxgx/playing-card-detection` (a synthetic dataset generator often cited for YOLO card training) could not be confirmed in this session.

## Overlay/UI options and audio alerts

### Takeaway
No authoritative sources were fetched for this question within the tool budget. The options below are standard engineering knowledge, not cited findings. One existing repo (irudrakshgupta) shows audio "whisper-mode" prompts and a stealth UI as prior art.

### Cited Findings
- Prior art: an on-screen overlay showing running and true count — [Gonzi09/Blackjack-AI-Card-Counter](https://github.com/Gonzi09/Blackjack-AI-Card-Counter). Whisper-mode audio prompts and a stealth UI — [irudrakshgupta/Real-Time-Blackjack-Poker-Counter](https://github.com/irudrakshgupta/Real-Time-Blackjack-Poker-Counter).

### Inferences
- These are unsourced, standard options:
  - tkinter with `wm_attributes('-topmost', True)` and `overrideredirect` gives a small always-on-top panel and is in the standard library.
  - PyQt or PySide with `Qt.WindowStaysOnTopHint | FramelessWindowHint` and `WA_TranslucentBackground` allows a translucent, click-through overlay.
  - A local web dashboard (FastAPI or Flask with WebSocket) suits a second monitor or phone.
  - Audio can use `winsound` (Windows), `simpleaudio` or `playsound`, or text-to-speech with `pyttsx3`.
- Keep the recognition loop in its own thread or process. Push state such as count, true count, seat confidence and "needs review" flags to the UI over a queue so the overlay never blocks capture.

### Gaps
- No sourced comparison of overlay frameworks (for example click-through support per OS) or audio libraries was gathered.
- Legal and terms-of-service context matters for the report writer:
  - Nevada NRS 465.075 makes it unlawful to use or possess with intent to use a device or software that assists in keeping track of cards played. The Nevada Gaming Control Board applied it to a card-counting iPhone app in a licensed establishment in 2009 — [NRS 465.075](https://nevada.public.law/statutes/nrs_465.075); [NGCB 2009 notice](https://gaming.nv.gov/uploadedFiles/gamingnvgov/content/about/industry-notices/2009-02-05-.pdf).
  - No source was found on how such statutes or online-casino terms of service apply to remote and online play. Many operators prohibit third-party assistance software, but this was not verified here, and account closure or forfeited winnings are the likely practical risk.
  - Combined with roughly 50% penetration on 8-deck live shoes (unconfirmed for Evolution), the practical counting edge may be small.
