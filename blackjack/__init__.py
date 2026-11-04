"""Live-dealer blackjack table watcher.

Reads cards off the screen with a YOLO model, remembers every card per table,
shoe, round and seat in SQLite, and keeps running counts for several counting
systems. Shoe-size and rule values in the example config are placeholders until
they are measured from real tables.

Optional dependencies (only needed for live capture): ultralytics, opencv-python,
mss, numpy; anthropic + pydantic for the vision-LLM fallback.
"""
