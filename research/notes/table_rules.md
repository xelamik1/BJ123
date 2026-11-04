# Live-Dealer Blackjack Table Rules and Procedures (Evolution classic 7-seat vs Pragmatic Play Live, Ezugi, Playtech Live)

Research date: 2026-10-30. Scope: the rules a card-counting/spotting tool needs, plus table procedures for a player who watches and joins only when the count is good.

**Source quality warning (applies to everything below):** No official provider rulebook (evolution.com, pragmaticplaylive.net, ezugi.com, playtech.com) could be fetched. The search engine returned many spam pages (e.g. npc-for-vcmp.sourceforge.io "wiki" pages), and these were excluded. The best sources found were:
- (a) operator help pages that reproduce the in-game rules (theScore Bet Zendesk);
- (b) affiliate/review sites (Live Casino Comparer, updated Oct 2026; BTCGOSU; BlackjackInfo; LiveDealer.org);
- (c) one Wizard of Vegas forum thread from 2021.

Affiliate sites contradict each other on several rules. **The in-game "Help/Rules" panel of each table is the only authoritative source and should be read before configuring the tool.**

### Summary configuration table (best available evidence; confidence noted)

| Parameter | Evolution classic Live Blackjack (7 seats + Bet Behind) | Pragmatic Play Live (classic) | Ezugi (Seven Seat / classic) | Playtech Live (classic) |
|---|---|---|---|---|
| Decks | 8 (high: several sources agree) | 8 (medium-high) | 8 (medium, one affiliate matrix only) | 8 per matrix; Quantum Blackjack Plus said to be 6 (conflict) |
| Dealer S17 | Stands all 17s (felt text; multiple sources) | Stands all 17s | Stands 17 (matrix) | Stands 17 (matrix) |
| BJ pays | 3:2 | 3:2 | 3:2 | 3:2 |
| Hole card / peek | **Conflict.** Peeks on Ace (agreed). Peek on 10 is disputed: one 2021 forum post says no peek with 10 up; Live Casino Comparer says "Vegas rules, dealer will always peek" | Peek ("Vegas", per matrix) (low-medium) | Peek ("Vegas", per matrix) (low) | **No peek** ("dealer never checks for Blackjack"). A double lost to dealer BJ with 10 up gets half the stake back (low-medium) |
| Double | Any two cards (matrix; one affiliate claims 9-11 only, which conflicts) | Any two cards (matrix) | Any two cards (matrix) | Any two cards (matrix) |
| DAS | **No** (two sources) | **Yes since June 2025**, except after split aces | Yes (matrix + text) | No (matrix) |
| Resplit | No (split once) | No (matrix) | No (matrix) | No (matrix) |
| Split aces | One card each | One card each (matrix) | One card each (matrix) | One card each (matrix) |
| Surrender | No | No | Text says surrender vs dealer Ace on Seven Seat (matrix says no; conflict) | No on classic; "Cashback Blackjack" variant has surrender |
| Insurance | Yes, 2:1, costs half the bet, offered on dealer Ace | Yes 2:1 (matrix) | Yes 2:1 (matrix) | Yes, on Ace |
| Even money | Offered per operator text ("take even money, or take insurance") | unknown | unknown | unknown |
| Shuffle | Manual or machine "by the side of each table"; the matrix says manual | Manual, "re-shuffled mid shoe" | Manual (matrix) | "Manual & Auto" (matrix) |
| Penetration | Reported ~50% (multiple affiliates; one says the shoe is replaced when 1/4 remains, i.e. ~75%; conflict) | Reported ~50-55% | No figure found | No figure found |
| Published RTP | 99.28-99.29% typical (operator pages); 99.47% "Seven Seat" per Live Casino Comparer | 99.29% before June 2025; 99.41% after DAS added | No figure found | No figure found |

---

## 1. Number of decks, cut card placement and penetration

### Takeaway
Every source that names a deck count puts the classic tables of all four providers at 8 decks (except a 6-deck Playtech variant). Penetration is never stated officially. The widely repeated figure is about 50%: the cut card goes roughly mid-shoe and leaves about 4 decks unplayed. One source claims about 75%. No primary or forum measurement was found.

### Cited Findings
- Evolution Salon Privé Blackjack (operator rules text): "Played with 8 decks." — [theScore Bet help: Salon Privé Blackjack A](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873608581645-Salon-Prive-Blackjack-A)
- Live Casino Comparer (updated Oct 24 2026) provider matrix lists 8 decks for Evolution, Pragmatic Play, Ezugi and Playtech. Its prose says Playtech Live Quantum Blackjack Plus is a 6-deck game, which conflicts with the matrix. — [Live Casino Comparer: Blackjack Table Rules](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Live Casino Comparer, manual-shuffle tables: "Re-shuffles occur when half the shoe has been used." — [Live Casino Comparer: Blackjack Table Rules](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Contradiction on the same site's Evolution page: "The game uses eight decks of cards, which get replaced only [when] a 1/4 of the shoe remains" (~75% penetration). — [Live Casino Comparer: Evolution Live Blackjack](https://www.livecasinocomparer.com/live-casino-software/evolution-live-casino-software/evolution-live-blackjack/)
- BTCGOSU comparison of Evolution and Pragmatic: both use 8 decks, and "Shoe penetration on both tables runs at roughly 50-55%." — [BTCGOSU: Evolution vs Pragmatic Live Blackjack](https://www.btcgosu.com/blog/blackjack-pragmatic-evolution/)
- Secondary guides repeat that Evolution uses 8-deck shoes and shuffles at about 50% penetration. One says the dealer "inserts the plastic cut card directly in the middle." These are affiliate pages and may all copy one original source. — [DeucesCracked live dealer blackjack](https://www.deucescracked.com/casino/blackjack/live-dealer-blackjack); [CountPilot guide](https://countpilot.app/guides/can-you-count-cards-in-online-live-blackjack.html)
- Pragmatic: "Dealt from 8 deck shoe, manually re-shuffled mid shoe" (search snippet; the page returned 403 when fetched). — [LiveDealer.org: Pragmatic Play Live Blackjack](https://www.livedealer.org/live-casino-games/live-blackjack/pragmatic-play-live-blackjack/)
- Blackjack Review (Sep 2026) on what can be checked from a stream:
  - the stream may not show the original deck count or the exact cut-card depth;
  - the cut card "might only appear briefly";
  - penetration can only be estimated by watching repeatedly;
  - counting rounds is not the same as counting cards.
  - [Blackjack Review: Deck Penetration in Live Dealer Games](https://www.blackjackreview.com/wp/2026/09/09/deck-penetration-in-live-dealer-games/)

### Inferences
- Default the tool to 8 decks with about 4 decks dealt per shoe (~50%). Make the penetration a per-table setting the user calibrates by observation, for example by logging cards seen between two shuffle events. The sources disagree (50% vs 75%), and none of them is a measurement.
- At about 50% penetration on 8 decks, the true count rarely moves far from zero. Affiliate commentary calls counting at these tables marginal or unprofitable. This is opinion, not a simulation.

### Gaps
- No official Evolution, Pragmatic, Ezugi or Playtech statement of cut-card placement was found.
- No forum or Reddit thread with player-measured penetration (cards dealt per shoe) was found. Wizard of Vegas, Blackjack Apprenticeship and r/blackjack searches returned nothing relevant.
- No penetration figure was found for Ezugi or Playtech.

## 2. Dealer hole card: peek vs ENHC, and what is lost to a dealer blackjack

### Takeaway
Evolution classic is a hole-card game: the second dealer card is dealt face down. All sources agree the dealer checks for blackjack with an Ace up, after insurance. Whether Evolution also peeks with a 10 up is **disputed**. If it does not peek on a 10, the treatment of doubled and split money against a 10-up dealer blackjack is undocumented. Playtech classic is reported as no-peek, with a partial refund on doubles.

### Cited Findings
- Wizard of Vegas forum (Glunn11, Nov 9 2021, about Evolution Lightning Blackjack; older info): "8 decks; dealer stands on soft 17; no double after split; no re-split" and "Dealer only peeks for blackjack with A showing; does NOT peek with 10 showing." — [Wizard of Vegas: Lightning Blackjack from Evolution](https://wizardofvegas.com/forum/gambling/blackjack/36643-lightning-blackjack-from-evolution/)
- Live Casino Comparer (Oct 2026): Evolution Live Blackjack is played to Vegas rules, and "the dealer will always peek for Blackjack and offer Insurance if his up card is an Ace." The wording only confirms the Ace peek. Its matrix marks Evolution, Pragmatic and Ezugi as "Peek ✓" and Playtech as no peek. — [Live Casino Comparer: Blackjack Table Rules](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Evolution Power Blackjack (a variant with 9s and 10s removed): the dealer checks for blackjack on J, Q, K and A, per an operator help page. This suggests the variant peeks on ten-value face cards too. — [theScore Bet help: Power Blackjack](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873574137869-Power-Blackjack)
- Evolution operator text (VIP Alpha): "only the dealer's first card is shown." — [theScore Bet help: Blackjack VIP Alpha](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873609104397-Blackjack-VIP-Alpha)
- Playtech Live Blackjack: "the dealer never checks for Blackjack," but "if you double when the dealer is showing ten, and you lose your hand to a Blackjack, you get half of your stake back." — [Live Casino Comparer: Blackjack Table Rules](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Ezugi: the matrix marks "Split bets returned" on dealer blackjack, which is an ENHC-protection style rule. — [Live Casino Comparer: Blackjack Table Rules](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Generic cost of no-hole-card play (full loss of doubles and splits): about +0.11% house edge. — [Live Casino Comparer: Blackjack Table Rules](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)

### Inferences
- The tool should treat "peek on 10" as a configurable flag (Ace-only vs Ace+10). It should also treat "loss on dealer BJ" as configurable: original bet only (OBO), full loss (ENHC), or Playtech's half-refund on doubles. Evolution's in-game help is needed to settle this.
- If Evolution peeks on Ace only and takes doubles and splits against a 10-up blackjack, the basic strategy deviations against a dealer 10 (don't double 11 vs 10; don't split 8s vs 10 in strict ENHC) matter for the tool's strategy layer.

### Gaps
- No official text was found saying whether Evolution classic peeks on a 10-up, or how doubles and splits are settled if it doesn't. The only evidence is one 2021 forum post about the Lightning variant against an affiliate's wording.

## 3. Doubling, DAS, splits, surrender, insurance and bet limits

### Takeaway
Evolution classic: double on any first two cards, **no DAS**, split once (no resplit), split aces get one card, no surrender, insurance 2:1. Pragmatic matches it but **added DAS in June 2025** (not after split aces). Ezugi reportedly allows DAS, and its text claims surrender vs Ace. Playtech classic lacks DAS. Limits vary widely by table.

### Cited Findings
- Evolution: "You can split matched pairs and double your hand whenever you like"; "Split Aces only get one card"; insurance "will cost you half your initial stake." — [Live Casino Comparer: Evolution Live Blackjack](https://www.livecasinocomparer.com/live-casino-software/evolution-live-casino-software/evolution-live-blackjack/)
- Evolution vs Pragmatic: "Pragmatic's tables allow you to double your bet after splitting a pair. Evolution's don't." — [BTCGOSU](https://www.btcgosu.com/blog/blackjack-pragmatic-evolution/)
- Evolution no DAS and no resplit (2021 post). — [Wizard of Vegas](https://wizardofvegas.com/forum/gambling/blackjack/36643-lightning-blackjack-from-evolution/)
- Conflict on doubling range: one affiliate says Evolution doubling is limited to 9/10/11, while others say any two cards. — [Online Casino Directory: Blackjack Live](https://online.worldcasinodirectory.com/evolution-gaming/blackjack-live); [Live Casino Comparer matrix](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Pragmatic DAS change: "Double Down permitted after a Split, except when splitting Aces (changed June 2025)." BlackjackInfo says published RTP rose from 99.29% to 99.41%. Pragmatic does not offer surrender. — [BlackjackInfo: Pragmatic Play Blackjack](https://www.blackjackinfo.com/live-blackjack-game/pragmatic-play/blackjack-2/); [LiveDealer.org: DAS now allowed on Pragmatic](https://www.livedealer.org/double-after-split-now-allowed-on-pragmatics-live-blackjack-tables/)
- Ezugi Seven Seat: "will allow you to surrender your hand if the dealer's up card is an Ace"; listed with "DDAS, Surrender." The site's own matrix shows no surrender, so this conflicts. — [Live Casino Comparer](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Playtech: classic has no DAS (matrix). The "Cashback Blackjack" variant offers surrender. — [Live Casino Comparer](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Evolution insurance (operator text): offered when the dealer shows an Ace and costs half the bet; it pays 2:1 if the dealer has blackjack. Even money is listed as an option. — [theScore: VIP Alpha](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873609104397-Blackjack-VIP-Alpha)
- Bet limit examples (Evolution, theScore Ontario): VIP Alpha $100-$10,000; Salon Privé $2,000-$10,000. — [VIP Alpha](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873609104397-Blackjack-VIP-Alpha); [Salon Privé A](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873608581645-Salon-Prive-Blackjack-A)
- Evolution decision timer: when time runs out, totals of 11 or below are treated as a hit and 12 or above as a stand (Salon Privé). A disconnect defaults to Stand on other tables. — [theScore: Salon Privé A](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873608581645-Salon-Prive-Blackjack-A); [Live Casino Comparer: Evolution](https://www.livecasinocomparer.com/live-casino-software/evolution-live-casino-software/evolution-live-blackjack/)

### Inferences
- The tool's rules model needs separate toggles for DAS (Evolution off, Pragmatic on since 06/2025), surrender (Ezugi possibly on), and peek mode. Pragmatic's DAS change shows that rules change over time, so the tool should let the user re-check rules against each table's help panel.

### Gaps
- No official limits for standard (non-VIP) classic tables were found; they vary by operator.
- Ezugi and Playtech rules come from one affiliate matrix with internal contradictions.

## 4. Shuffle procedure and how the client signals a new shoe

### Takeaway
Classic tables are reported as manual or machine-assisted batch shuffles of a single 8-deck shoe, done at the table's side. A second pre-shuffled shoe is plausibly being prepared on the other side, which matches the two-shoe layout in the screenshot. This is unconfirmed by any source. Some premium/VIP tables reshuffle every round. No documentation of the client's new-shoe UI message was found.

### Cited Findings
- Evolution: "The cards get shuffled by hand or a machine by the side of each table," then loaded into a clear perspex shoe. — [Live Casino Comparer: Evolution](https://www.livecasinocomparer.com/live-casino-software/evolution-live-casino-software/evolution-live-blackjack/)
- Playtech matrix: "Manual & Auto" shuffling. Auto-shuffle tables return discards to the shoe before each hand, and the page says counting "won't work" there. — [Live Casino Comparer](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Evolution Blackjack VIP Alpha (theScore, Ontario): "The cards are re-shuffled for each game round." — [theScore: VIP Alpha](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873609104397-Blackjack-VIP-Alpha)
- Evolution Salon Privé: the player controls "the shuffle" (private table). — [theScore: Salon Privé A](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873608581645-Salon-Prive-Blackjack-A)
- A fast shuffle does not prove a CSM; it could be a batch shuffler preparing another shoe. With a CSM, shoe penetration is "largely redundant." — [Blackjack Review (Sep 2026)](https://www.blackjackreview.com/wp/2026/09/09/deck-penetration-in-live-dealer-games/)
- No burn card before hands on any of the ten providers (matrix). — [Live Casino Comparer](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)

### Inferences
- Two shoes on the table usually means one shoe is dealt while the other is shuffled off-camera or at the side, so play can continue right away. For the tool, any shoe swap must reset the running count to zero, because the new shoe is a fresh full 8-deck shoe.
- The tool should not depend on a UI "new shoe" message existing. It should also detect a reset from the video (shoe swap, cut card appearing) or require a manual reset button.
- Some tables (seen on VIP Alpha) reshuffle every round. Each table needs its own check.

### Gaps
- No documentation or screenshot description was found of an Evolution, Pragmatic, Ezugi or Playtech UI message announcing a shuffle or shoe change, or of a "cards remaining" indicator. This must be checked by watching the live client.
- The two-shoe alternating procedure is not documented in any source found.

## 5. Seat rules: mid-shoe entry, skipped rounds, overlays

### Takeaway
Evolution's classic tables have 7 seats, plus Bet Behind for people without a seat. No source states a "no mid-shoe entry" rule or the number of rounds a seated player can skip before losing the seat. Front players can control whether others bet behind them.

### Cited Findings
- Evolution's classic tables are "seven-seat games with the option to Bet Behind if all seats are already taken." — [Studio Spins: five Evolution table families](https://studiospins.com/blog/how-to-play-live-blackjack-online-evolution-table-families/)
- On Evolution, players choose whether others may Bet Behind them. Settings also control what bet-behind players do when the front player doubles or splits; the default is to match. — [Live Casino Comparer: Evolution](https://www.livecasinocomparer.com/live-casino-software/evolution-live-casino-software/evolution-live-blackjack/); [Online Casino Directory](https://online.worldcasinodirectory.com/evolution-gaming/blackjack-live)
- Pragmatic "Bet Behind Pro" lets spectators bet behind seated players at any time instead of waiting for a seat. — [OLBG: Bet Behind Pro](https://www.olbg.com/casino-sites/articles/bet-behind-pro-blackjack)
- A targeted search for seat-inactivity or skipped-round removal rules (Evolution/Pragmatic) found nothing. — (search performed 2026-10-30; no source)

### Inferences
- Bet Behind is the natural way in for a player who watches and enters only on good counts at a full 7-seat table. However, the bet-behind player has no control over how the hand is played, and can only follow doubles and splits or decline them.
- Classic 7-seat tables give each player their own cards, so every seated player's cards are dealt from the shoe and are visible on stream. The tool must count all seven hands plus the dealer.

### Gaps
- No source was found for: the seat-inactivity limit (rounds skipped before removal), whether a seat can be taken mid-shoe, whether a free seat only opens between rounds, or whether the client shows digital card/total overlays for all seats. All need direct observation or the in-game help text.

## 6. Variants and counting hostility

### Takeaway
Infinite, Power, Lightning and Free Bet variants change the game structure: a shared common hand, an altered deck, fees, or pushes on 22. Classic counting indices don't carry over. Infinite and Power use one common starting hand for unlimited players, so only one set of cards is drawn per round. Lightning charges a 100% fee.

### Cited Findings
- Infinite Blackjack: unlimited seats; every player gets the same two-card start; Six Card Charlie (-0.16% edge); low limits. — [Studio Spins](https://studiospins.com/blog/how-to-play-live-blackjack-online-evolution-table-families/); [Live Casino Comparer](https://www.livecasinocomparer.com/casino-guides/blackjack-table-rules/)
- Power Blackjack: 8 decks with 9s and 10s removed (64 fewer cards); double, triple or quadruple down, even after a split; same two initial cards for all players. — [Studio Spins](https://studiospins.com/blog/how-to-play-live-blackjack-online-evolution-table-families/); [theScore: Power Blackjack](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873574137869-Power-Blackjack)
- Lightning Blackjack: unlimited players; "Player must pay a fee equal to 100% of the ante on each hand"; next-round multiplier from 2x to 25x; documented RTP 99.56% (2021). — [Wizard of Vegas (2021)](https://wizardofvegas.com/forum/gambling/blackjack/36643-lightning-blackjack-from-evolution/); [Studio Spins](https://studiospins.com/blog/how-to-play-live-blackjack-online-evolution-table-families/)
- Free Bet Blackjack: free double on hard 9, 10 and 11; free split on pairs except ten-values. — [Studio Spins](https://studiospins.com/blog/how-to-play-live-blackjack-online-evolution-table-families/)
- Speed Blackjack (Evolution) also offers Cash Out, as do classic tables. — [Live Casino Comparer: Evolution](https://www.livecasinocomparer.com/live-casino-software/evolution-live-casino-software/evolution-live-blackjack/)

### Inferences
- Power Blackjack needs a different count system: a 9/10-removed deck makes Hi-Lo tags and indices wrong. Lightning's fee and multiplier, and Free Bet's push-on-22, also make standard indices invalid.
- Common-hand games (Infinite, Power, Lightning) burn far fewer cards per round than a full 7-seat table. Counting is possible in principle, but information builds slowly per round.

### Gaps
- No source confirmed Infinite Blackjack's shuffle procedure or penetration (whether it uses a CSM or a shoe).
- Speed Blackjack and Free Bet shuffle details were not found.

## 7. Base house edge

### Takeaway
Published Evolution classic RTP is about 99.28-99.29%, a house edge of about 0.71%. Pragmatic is 99.41% (0.59%) after adding DAS. No Ezugi or Playtech figures were found.

### Cited Findings
- Evolution VIP Alpha and Salon Privé: RTP 99.29%. — [theScore: VIP Alpha](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873609104397-Blackjack-VIP-Alpha); [Salon Privé A](https://thescorebethelp.zendesk.com/hc/en-us/articles/13873608581645-Salon-Prive-Blackjack-A)
- BetMGM Blackjack Live (Evolution): RTP 99.28%, "may differ from one jurisdiction to another." — [Studio Spins](https://studiospins.com/blog/how-to-play-live-blackjack-online-evolution-table-families/)
- Live Casino Comparer gives Seven Seat at 99.47%, and a range of 98.45-99.54% (FAQ: 98.85-99.54%) across Evolution versions. These figures conflict with the operator figures. — [Live Casino Comparer: Evolution](https://www.livecasinocomparer.com/live-casino-software/evolution-live-casino-software/evolution-live-blackjack/)
- Evolution house edge 0.71% vs Pragmatic 0.60% (basic strategy). — [BTCGOSU](https://www.btcgosu.com/blog/blackjack-pragmatic-evolution/)
- Pragmatic: 99.29% before June 2025, 99.41% after. — [BlackjackInfo](https://www.blackjackinfo.com/live-blackjack-game/pragmatic-play/blackjack-2/)

### Inferences
- A 0.71% edge for 8D S17 no-DAS no-resplit no-surrender fits the rules in section 3. That edge is roughly what Ace-only peek or OBO rules would give, but this is a consistency check, not proof.

### Gaps
- No Wizard of Odds page specific to live dealer providers could be reached (404). No Ezugi or Playtech RTP was found.
