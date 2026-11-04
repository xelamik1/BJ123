"""Always-on-top status window, one row per table, with a new-shoe button each."""
import tkinter as tk


class Overlay:
    def __init__(self, table_ids, on_new_shoe):
        self.root = tk.Tk()
        self.root.title("Table counts")
        self.root.attributes("-topmost", True)
        self.labels = {}
        for row, table_id in enumerate(table_ids):
            label = tk.Label(self.root, font=("Consolas", 11), justify="left", anchor="w",
                             padx=8, pady=4)
            label.grid(row=row, column=0, sticky="we")
            tk.Button(self.root, text="New shoe",
                      command=lambda t=table_id: on_new_shoe(t)).grid(row=row, column=1, padx=6)
            self.labels[table_id] = label

    def show(self, status):
        lines = [f"{status['table']}  shoe {status['shoe_id']}  round {status['round']}"
                 f"  {'OK' if status['reliable'] else 'UNRELIABLE (wait for shuffle)'}",
                 f"RC {status['running_count']:+}  TC {status['true_count']:+.2f}"
                 f"  decks left {status['decks_left']}  dealt {status['penetration']:.0%}"
                 f"  edge {status['edge']:+.2%}"]
        if status["alert"]:
            lines.append(">>> COUNT IS GOOD: look for a seat <<<")
        if status["insurance"]:
            lines.append("Insurance: take it")
        for zone, hands in status["seats"].items():
            lines.append(f"  {zone}: " + " | ".join(
                f"{' '.join(h['cards'])} ({h['total']})" for h in hands))
        for play in status["advice"] or []:
            if play:
                lines.append(f"  Index play: {play['play']} {play['hand']} v {play['dealer']}"
                             f" (index {play['index']:+})")
        label = self.labels[status["table"]]
        label.config(text="\n".join(lines), bg="#2e7d32" if status["alert"] else "#202020",
                     fg="white")

    def tick(self):
        self.root.update_idletasks()
        self.root.update()
