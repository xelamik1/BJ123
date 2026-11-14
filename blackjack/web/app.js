"use strict";
const SUIT = {C: "♣", D: "♦", H: "♥", S: "♠"};
const $ = (id) => document.getElementById(id);
let table = null, lastSeats = "", lastStats = "", lastHist = "", busy = false, frameSeq = -1;

function pretty(label) {
  const m = /^(10|[2-9AJQKT])([CDHS])?$/.exec(label);
  return m ? m[1] + (m[2] ? SUIT[m[2]] : "") : label;
}
const red = (label) => /[DH]$/.test(label);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));

async function post(path, body) {
  const r = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json"},
                               body: JSON.stringify({table, ...body})});
  if (!r.ok) alert((await r.json()).error || "request failed");
  poll();
}

function cardsHtml(cards) {
  return cards.map((c) => `<span class="card${red(c.label) ? " red" : ""}" data-edit="${c.id}" data-label="${esc(c.label)}">${esc(pretty(c.label))}</span>`).join("");
}
function totalText(h) {
  if (!h.cards.length) return "";
  if (h.bust) return `${h.total} BUST`;
  if (h.blackjack) return "Blackjack 21";
  return h.soft ? `soft ${h.total}` : `${h.total}`;
}
function adviceHtml(a) {
  if (!a) return "";
  if (!a.play) return `<div class="advice"><div class="why">${esc(a.reason)}</div></div>`;
  return `<div class="advice${a.deviation ? " dev" : ""}"><div class="play">${a.play.toUpperCase()}</div><div class="why">${esc(a.reason)}</div></div>`;
}

function renderSeats(s) {
  const bet = s.bet;
  $("seats").innerHTML = s.seats.map((seat) => {
    const hands = seat.hands.map((h) => `<div class="hand"><div class="cards">${cardsHtml(h.cards)}</div>
      <div class="total${h.bust ? " bust" : ""}">${esc(totalText(h))}</div>${adviceHtml(h.advice)}</div>`).join("");
    const occ = seat.occupancy_source === "manual" ? "manual" : "auto";
    const betTxt = seat.bet == null ? "—" : "$" + seat.bet;
    return `<div class="seat ${seat.state}" data-seat="${seat.seat}">
      <div class="top"><span>${seat.seat.replace("seat", "Seat ")}</span>
        <span><button class="mini" data-add="${seat.seat}" title="add a missed card">+</button>
        <button class="mini" data-occ="${seat.seat}" title="occupancy: auto / occupied / empty" data-manual="${occ === "manual" ? 1 : ""}">${occ === "manual" ? (seat.occupied ? "occupied" : "empty") : "auto"}</button></span></div>
      <div class="tag">${seat.mine ? "MINE" : seat.state}</div>
      ${hands || '<div class="hand">—</div>'}
      <div class="bet" data-bet="${seat.seat}">bet ${esc(betTxt)}</div>
      ${seat.mine ? `<div class="sugg">Bet ${bet.units} unit${bet.units > 1 ? "s" : ""} = $${bet.amount}</div>` : ""}
    </div>`;
  }).join("");
}

function renderDealer(s) {
  const hands = s.dealer.hands;
  const cards = hands.map((h) => `<span class="cards">${cardsHtml(h.cards)}</span> <span>${esc(totalText(h))}</span>`).join(" ");
  $("dealer").innerHTML = `<span class="label">Dealer</span>${cards || "—"}
    <button class="mini" data-add="dealer" title="add a missed card">+</button>`;
}

function renderStats(s) {
  const st = s.status, b = s.bet;
  const item = (k, v, cls = "") => `<span class="stat ${cls}"><span>${k}</span><b>${v}</b></span>`;
  const sign = (n) => (n > 0 ? "+" : "") + n;
  $("stats").innerHTML =
    item("table", esc(s.table)) + item("RC", sign(st.running_count)) +
    item("TC", sign(Number(st.true_count).toFixed(2))) + item("decks left", st.decks_left) +
    item("dealt", Math.round(st.penetration * 100) + "%") + item("cards", st.cards_seen) +
    item("shoe", st.reliable ? "reliable" : "UNRELIABLE", st.reliable ? "ok" : "bad") +
    item("suggested bet (placeholder ramp)", `${b.units}u = $${b.amount}`, "bet");
  const notes = [];
  if (st.alert) notes.push('<div class="alert">Count is good: look for a seat</div>');
  if (st.insurance) notes.push('<div class="alert">Insurance: take it</div>');
  if (!st.reliable) notes.push('<div class="warn">Shoe marked unreliable (started mid-shoe or a card anomaly): press NEW SHOE after the next shuffle.</div>');
  if (s.capture.error) notes.push(`<div class="warn">Capture error: ${esc(s.capture.error)}</div>`);
  if (s.capture.ended) notes.push('<div class="warn">Video ended.</div>');
  $("banner").innerHTML = notes.join("");
}

function setTables(s) {
  const sel = $("table");
  if (sel.options.length !== s.tables.length) {
    sel.innerHTML = s.tables.map((t) => `<option>${esc(t)}</option>`).join("");
  }
  sel.value = s.table;
  sel.style.display = s.tables.length > 1 ? "" : "none";
  if (document.activeElement !== $("unit")) $("unit").value = s.bet.unit_value;
}

function updateFeed(s) {
  const c = s.capture;
  $("feedbox").classList.toggle("live", c.has_frame);
  $("nofeed").textContent = c.mode === "none" ? "capture off (--no-capture)" : "no frames yet";
  if (c.has_frame && c.frame_seq !== frameSeq) {
    frameSeq = c.frame_seq;
    $("feed").src = `/frame.jpg?table=${encodeURIComponent(s.table)}&n=${frameSeq}`;
  }
}

async function poll() {
  if (busy) return;
  busy = true;
  try {
    const r = await fetch("/api/state" + (table ? `?table=${encodeURIComponent(table)}` : ""));
    const s = await r.json();
    table = s.table;
    setTables(s);
    updateFeed(s);
    const stats = JSON.stringify([s.status, s.bet, s.capture.error, s.capture.ended]);
    if (stats !== lastStats) { lastStats = stats; renderStats(s); }
    const seats = JSON.stringify([s.seats, s.dealer, s.bet.units, s.bet.amount]);
    if (seats !== lastSeats) { lastSeats = seats; renderDealer(s); renderSeats(s); }
  } catch (e) { /* server restarting */ }
  busy = false;
}

async function pollHistory() {
  try {
    const r = await fetch("/api/history?limit=20" + (table ? `&table=${encodeURIComponent(table)}` : ""));
    const h = await r.json();
    const key = JSON.stringify(h);
    if (key === lastHist) return;
    lastHist = key;
    const mine = new Set(h.rounds.length ? h.rounds[0].mine : []);
    $("history").innerHTML = h.rounds.map((rd) => {
      const dealer = rd.dealer.cards.map(pretty).join(" ") + (rd.dealer.total ? ` (${rd.dealer.total})` : "");
      const seats = Object.entries(rd.seats).map(([name, hands]) => {
        const isMine = mine.has(name);
        const body = hands.map((x) => `<span class="mini-cards">${x.cards.map(pretty).join(" ")} (${x.total})</span>` +
          (isMine && x.result ? ` <span class="res ${x.result}">${x.result}</span>` : "")).join(" | ");
        return `<span class="grp${isMine ? " mine-grp" : ""}"><span class="name">${name.replace("seat", "S")}</span>${body}</span>`;
      }).join("");
      return `<div class="round"><span class="no">#${rd.round_no}</span>
        <span class="grp"><span class="name">dealer</span><span class="mini-cards">${dealer || "—"}</span></span>${seats}</div>`;
    }).join("") || '<div class="hint">No finished rounds yet.</div>';
  } catch (e) { /* ignore */ }
}

document.addEventListener("click", (ev) => {
  const t = ev.target;
  if (t.dataset.edit) {
    const cur = t.dataset.label;
    const v = prompt(`Card ${cur}: new label (e.g. QH, 10S) or leave empty to delete`, cur);
    if (v !== null && v !== cur) post("/api/card", {id: Number(t.dataset.edit), label: v.trim()});
    return;
  }
  if (t.dataset.add) {
    const v = prompt(`Add a missed card to ${t.dataset.add} (e.g. QH)`);
    if (v) post("/api/card/add", {zone: t.dataset.add, label: v.trim()});
    return;
  }
  if (t.dataset.occ) { cycleOcc(t.dataset.occ); return; }
  if (t.dataset.bet) {
    const v = prompt("Bet amount for " + t.dataset.bet + " (empty to clear)");
    if (v !== null) post("/api/bet", {seat: t.dataset.bet, amount: v.trim() === "" ? null : Number(v)});
    return;
  }
  const seat = t.closest(".seat");
  if (seat) post("/api/mine", {seat: seat.dataset.seat, mine: !seat.classList.contains("mine")});
});

document.addEventListener("contextmenu", (ev) => {
  const seat = ev.target.closest(".seat");
  if (seat) { ev.preventDefault(); cycleOcc(seat.dataset.seat); }
});

function cycleOcc(seat) {
  const el = document.querySelector(`.seat[data-seat="${seat}"]`);
  const manual = !!el.querySelector("[data-occ]").dataset.manual;
  const next = !manual ? "occupied" : el.classList.contains("occupied") ? "empty" : "auto";
  post("/api/occupancy", {seat, value: next === "auto" ? null : next});
}

$("newshoe").addEventListener("click", () => {
  if (confirm("Wipe the current shoe and start a new count?")) post("/api/new_shoe", {});
});
$("table").addEventListener("change", (e) => { table = e.target.value; lastSeats = lastStats = lastHist = ""; frameSeq = -1; poll(); });
$("unit").addEventListener("change", (e) => post("/api/settings", {unit_value: Number(e.target.value)}));

poll(); pollHistory();
setInterval(poll, 200);
setInterval(pollHistory, 2000);
