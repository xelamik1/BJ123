# Card-Counting Mathematics for Back-Counting (Wonging) an 8-Deck S17 3:2 Shoe at ~50% Penetration

Scope note: about 21 search/fetch calls. Several primary sources were not reachable: Blackjack Attack tables, CVCX/CVData output, the Qfit risk-of-ruin page (HTTP 500), and Wizard of Odds true-count frequency tables. Figures from them appear only where a secondary source quoted them. Every number below is cited. Uncited reasoning is under "Inferences", and missing figures are under "Gaps". No simulations were run.

## 1. Count system choice and true-count conversion

### Takeaway
Hi-Lo (2-6 = +1, 7-9 = 0, T-A = -1) is the standard reference count. True count = running count / decks remaining. Published comparisons show multilevel counts gain only marginally over Hi-Lo, and the gain is mostly in playing efficiency, which matters little in a wonging game where betting correlation drives profit. An automated tool can use Wong Halves or a level-2/3 count at no mental cost, but the expected gain is small (one source: ~0.1%).

### Cited Findings
- Hi-Lo tags are 2,3,4,5,6 = +1; 7,8,9 = 0; 10,J,Q,K,A = -1. True count = running count ÷ decks remaining. Wizard of Odds example: RC +7 with ~4 decks left gives 1.75, rounded to 2 — [Wizard of Odds, High-Low](https://wizardofodds.com/games/blackjack/card-counting/high-low/)
- Tag values of the alternative systems (from Wikipedia's table) — [Wikipedia: Card counting](https://en.wikipedia.org/wiki/Card_counting):

  | System | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | T | A | Level |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | Hi-Lo | +1 | +1 | +1 | +1 | +1 | 0 | 0 | 0 | −1 | −1 | 1 |
  | KO (unbalanced) | +1 | +1 | +1 | +1 | +1 | +1 | 0 | 0 | −1 | −1 | 1 |
  | Hi-Opt II | +1 | +1 | +2 | +2 | +1 | +1 | 0 | 0 | −2 | 0 | 2 |
  | Omega II | +1 | +1 | +2 | +2 | +2 | +1 | 0 | −1 | −2 | 0 | 2 |
  | Zen | +1 | +1 | +2 | +2 | +2 | +1 | 0 | 0 | −2 | −1 | 2 |
  | Wong Halves | +0.5 | +1 | +1 | +1.5 | +1 | +0.5 | 0 | −0.5 | −1 | −1 | 3 |
- Wikipedia says playing efficiency "can approach 70%" without side counts but gives no per-system BC/PE/IC table. It notes that counting the ace raises betting correlation (BC) but lowers playing efficiency (PE), and that some counters earn more with a simple count played quickly — [Wikipedia: Card counting](https://en.wikipedia.org/wiki/Card_counting)
- BC/PE figures quoted in a secondary search summary: Hi-Lo BC 0.97, KO BC 0.98, Omega II BC 0.92 / PE 0.67, Wong Halves BC 0.99 / PE 0.56. Sources disagree on the Wong Halves and Omega II values. Treat these as approximate and verify against Griffin's *Theory of Blackjack* or Snyder's tables — [LVA: What's the best card counting system](https://www.lasvegasadvisor.com/gambling-with-an-edge/whats-the-best-card-counting-system/)
- Arnold Snyder's combined ranking scores Wong Halves and Hi-Opt II both at 1.96. Snyder says his "Blackjack Formula indicates a negligible superiority" of higher-level counts over Zen "under most conditions". Another source says higher-level systems perform "only 0.1% better" — [LVA: A Comparison of the Top 100](https://www.lasvegasadvisor.com/blog/whats-the-best-card-counting-system/)
- Edge per count-per-deck depends on the system's scale: Hi-Lo is about 0.5% per true count. For higher-level counts (Halves, Point Count, APC), each count-per-deck is about 0.3% — [Snyder excerpt, LVA](https://www.lasvegasadvisor.com/blog/an-excerpt-from-arnold-snyders-beat-the-6-deck-game/)
- Deck-estimation resolution used in published sims:
  - Wizard of Odds' 6-deck Hi-Lo sims round remaining decks "to the nearest half deck" — [Wizard of Odds](https://wizardofodds.com/games/blackjack/card-counting/high-low/)
  - Blackjack in Color's sims use "Hi-Lo, truncate, half-deck resolution" — [Blackjack in Color, penetration](https://blackjackincolor.com/penetration3.htm), [Blackjack in Color, true count](https://blackjackincolor.com/truecount5.htm)
- Hi-Lo had "a slightly better SCORE than KO" in a 6D S17 DAS LS sim (values not given) — [Blackjack in Color](https://blackjackincolor.com/penetration3.htm)

### Inferences
- **Recommendation for the tool:** compute the running count with Hi-Lo tags. Because the tool sees every card dealt (assuming the live stream shows them all), compute decks remaining exactly as (416 − cards seen)/52 instead of half-deck estimation, and keep the true count as an unrounded float internally. When looking up integer-index tables, choose floor or truncate to match the convention the table was generated with. Published Hi-Lo indices (I18/Fab 4) are commonly used with rounding or flooring; Wizard of Odds rounds in its example. The difference matters mainly at the TC 0 to +1 boundary.
- A tool can also run Wong Halves (or a level-3 count) in parallel, to compare and to bet off the better betting-correlation count. The cited sources suggest the edge gain in a wonging game will be at most about 0.1% of edge on hands played. An exact-composition (combinatorial) EV calculation per round is the theoretical ceiling, but I found no published figure for its gain over Hi-Lo in 8D.
- Because the tool wongs (plays only positive counts), betting correlation matters far more than playing efficiency. The ace-reckoned, high-BC counts (Hi-Lo, Halves, KO, Zen) are better fits than ace-neutral Hi-Opt II or Omega II unless the tool keeps an ace side count.

### Gaps
- No primary-source BC/PE/IC table was retrieved (Griffin's or Snyder's original tables are not online in fetchable form).
- No published figure was found for the extra edge from level-3 or exact-composition counting in 8D at 50% pen.
- No published comparison was found of floor vs truncate vs round effects on win rate. Blackjack in Color has a "truncate" setting but no comparison text.

## 2. Baseline edge, edge per true count, and ENHC

### Takeaway
An 8D S17 DAS 3:2 game with peek has a house edge of about 0.45-0.55%. Wizard of Odds puts 8D H17 DAS at 0.66%, and S17 improves that by ~0.19-0.2%. No-hole-card (ENHC) adds ~0.11%, and having no DAS adds another ~0.12-0.16%. Each Hi-Lo true count adds roughly 0.5%, so the break-even true count is about +1 (peek) to +1.2 (ENHC). Wonging-in at TC +1 is therefore close to neutral, and TC +2 is clearly positive.

### Cited Findings
- Wizard of Odds house edge by deck count (DAS, RSP to 4, no hitting split aces, no surrender, DOA, OBO/peek, **H17**, cut card): 8 decks = 0.66%, 6 decks = 0.64% — [Wikipedia: Blackjack, citing Wizard of Odds House Edge Calculator](https://en.wikipedia.org/wiki/Blackjack)
- S17 instead of H17 lowers the house edge by about 0.2%. No-hole-card raises it by about 0.11%, and "original bets only" has the same effect as a hole-card game. No DAS raises it by about 0.12%. 6:5 blackjack adds about 1.4% — [Wikipedia: Blackjack](https://en.wikipedia.org/wiki/Blackjack)
- Wizard of Odds rule-effect table (relative to Wong's benchmark):
  - S17: +0.191% EV, variance −0.008
  - DAS: +0.159% EV
  - Late surrender: +0.088%
  - RSA: +0.070%
  - Eight decks (vs 6): −0.025%

  Source: [Wizard of Odds, Appendix 4](https://wizardofodds.com/games/blackjack/appendix/4/)
- Wizard of Odds baseline EVs:
  - 6D S17 DAS LS RSA: −0.281%, variance 1.303
  - 6D S17 no DAS/LS/RSA: −0.573%
  - 8D H17 no DAS/LS/RSA: −0.812%, variance 1.309

  Source: [Wizard of Odds, Appendix 4](https://wizardofodds.com/games/blackjack/appendix/4/)
- A forum estimate puts the 8D DAS DA2 S17 3:2 house edge at ~0.55%, with each true count adding ~0.5%, so the player's edge starts at about +2. This is a forum post, not a published sim — [Wizard of Vegas forum](https://wizardofvegas.com/forum/gambling/blackjack/4728-card-counting-8-deck-and-cutting-card/)
- Hi-Lo: "each true count (or count-per-deck) is equal to a 0.5% change in your advantage" (Wong, as quoted by Snyder) — [Snyder excerpt, LVA](https://www.lasvegasadvisor.com/blog/an-excerpt-from-arnold-snyders-beat-the-6-deck-game/)
- A secondary rule-variation table using an 8D S17 DAS baseline gives ENHC −0.11% and no-DAS −0.14%. This is a low-quality aggregator mirror, so treat it as corroboration only — [aggregator](https://liaduperli1981.netlify.app/blackjack-odds-wiki)

### Inferences
- **Baseline for the tool:** take Wizard's 8D H17 DAS peek figure of −0.66% and add 0.19-0.2% for S17. That gives an 8D S17 DAS peek baseline of about −0.46%. Without DAS it is about −0.6%. For ENHC (typical of European-style live-dealer tables) add ~0.11%: about −0.57% with DAS, about −0.7% without.
- **Edge model for the tool:** EV(TC) ≈ baseline + 0.5% × TC. Break-even TC ≈ |baseline| / 0.5 ≈ +0.9 (peek, DAS) to +1.4 (ENHC, no DAS). Examples:
  - Peek, DAS: EV(+1) ≈ +0.04%, EV(+2) ≈ +0.54%, EV(+3) ≈ +1.04%
  - ENHC with DAS: EV(+2) ≈ +0.43%

  These figures are linear-model estimates, not simulation output. In practice the slope is slightly nonlinear, and the true value depends on penetration and indices.
- Some live-dealer online games use ENHC with "original bets only" or bet-behind variants. If the dealer only collects original bets, the hole-card penalty disappears.

### Gaps
- I did not retrieve an exact Wizard of Odds figure for 8D S17 DAS ENHC. The numbers above are derived additively.
- No published ENHC-specific index adjustments were retrieved (e.g. not doubling 11 vs T/A, not splitting vs T/A). LVA sells a "6-Deck S17 DAS ENHC ES" Hi-Lo index guide, but its contents were not accessible — [LVA product](https://www.lasvegasadvisor.com/shop/?p=838436)

## 3. Frequency distribution of true counts at 50% penetration, 8 decks

### Takeaway
I found no published table of true-count frequencies for 8D at 50% penetration. Published frequency distributions are for 6D at 75%, and they show that positive edges are scarce even there. At 50% of an 8-deck shoe, high true counts are rarer still, because a count of +2 needs a much larger running count with 4+ decks left.

### Cited Findings
- Snyder's frequency distribution (*Beat the 6-Deck Game*), 6D S17 DOA, 75% dealt, Hi-Lo-type count, 100 hands/hr. Hands per 100 by advantage:

  | Advantage | Hands per 100 |
  |---|---|
  | −0.5% | 34 |
  | 0.0% | 13 |
  | +0.5% | 8.5 |
  | +1.0% | 4.5 |
  | +1.5% | 3.5 |
  | +2.0% | 2.0 |
  | +2.5% | 2.0 |
  | +3.0% | 1.0 |
  | +3.5% | 0.5 |

  That is about 22 hands per 100 at ≥ +0.5% advantage and about 13.5 per 100 at ≥ +1.0%. Snyder also published 50%/65%/85% pen charts and a separate 8-deck report, but they were not in the excerpt — [Snyder excerpt, LVA](https://www.lasvegasadvisor.com/blog/an-excerpt-from-arnold-snyders-beat-the-6-deck-game/)
- An unsourced secondary site claims that at 50% penetration in 8 decks the true count "rarely exceeds +2" (unverified) — [search result summary: deucescracked](https://www.deucescracked.com/casino/blackjack/card-counting-guide)
- On the 6D penetration effect: "The win rate with .5 decks cut off is seven times the win rate with 2.5 decks cut off." Advantage rises from ~0.64% (130 cards cut) to 1.67% (26 cards cut) in a 1-12 optimal-betting sim — [Blackjack in Color](https://blackjackincolor.com/penetration3.htm)
- Blackjack Attack Ch. 10 data (quoted on a forum), 1-12 spread, H17 DAS:
  - 8D dealt to 6.5 decks: SCORE 10.27
  - 8D dealt to 7 decks: SCORE 18.49
  - 6D dealt to 4.5 decks: SCORE 12.64

  Source: [blackjackinfo forum](https://www.blackjackinfo.com/community/threads/what-penetration-increase-is-needed-for-8-deck-to-beat-6.13102/)

### Inferences
- As a rough approximation, the true count of a shoe after n of N decks are dealt has standard deviation that grows like sqrt(n / (N(N−n)))-ish. At 4 of 8 decks dealt, the spread of TC at the cut is smaller than in 6D at 4.5/6. So expect well under the ~13% of hands at ≥ +1% advantage seen in 6D/75%. A plausible guess is low single digits of percent at TC ≥ +3, but this is not a published figure. **The tool should collect empirical TC frequencies from its own observations, or the user should consult CVData/CVCX or Snyder's 8-deck report.**
- Since penetration is the dominant driver of SCORE (8D going from 6.5 to 7 decks dealt roughly doubles SCORE in Blackjack Attack), a 4-of-8 game sits far below the published 8D SCORE values. Wonging is close to the only way to make it positive.

### Gaps
- No published TC-frequency table for 8D / 50% pen (Hi-Lo) was found. Schlesinger's Blackjack Attack, Wong's Professional Blackjack and CVCX are the likely places but were not accessible. The Wizard of Odds TC frequency appendix was not located.

## 4. Wong-in / wong-out thresholds, edge on hands played, hands per hour

### Takeaway
The only peer-reviewed analysis (Werthamer 2006) finds the optimal 6-deck entry at TC +2 to +3, with exit at −2 to −3 when entry and exit are optimized jointly. Common practitioner sims for 8D use wong-in at +1 and wong-out below +1. For 8D at 50% pen, with a break-even near TC +1 (or higher under ENHC), entering at +2 and leaving below +1 (or at the shuffle) is a reasonable default. Wonging greatly reduces the bankroll needed relative to play-all.

### Cited Findings
- Werthamer, "Optimal Betting in Casino Blackjack II: Back-Counting," *International Gambling Studies* 6(2), 2006, pp. 111-122. For a typical 6-deck game, optimal entry is TC +2 to +3 depending on risk tolerance. Adding an exit threshold improves performance only slightly, and the jointly optimal exit count is −2 to −3. Because risk of ruin is very low, back-counters can bet more aggressively or flat bet — [IDEAS/RePEc abstract](https://ideas.repec.org/a/taf/intgms/v6y2006i2p111-122.html)
- 8D S17 DAS sims, 1-12 spread, 4 players, $10k bank, 5% RoR. "Wonging" means enter at TC +1 and exit below +1. "Semi-wonging" means enter at TC 0 and exit below 0. Results in units per 100 hands seen, and bankroll for 5% RoR in units:

  | Pen | Play-all optimal EV | Bankroll | Wonging EV | Bankroll |
  |---|---|---|---|---|
  | 75% | 1.62 | 2111 | 1.16 | 671 |
  | 81% | 1.95 | 1724 | 1.58 | 664 |
  | 88% | 2.29 | 1300 | 2.16 | 630 |

  With LS at 75%: wonging 1.36 u/100, bankroll 535. Wonging ramp: TC +1 = 1u, +2 = 2u, +3 = 4u, +4 = 6u, +5+ = 12u. With a fixed $10k bankroll, wonging gives the highest $/100 hands because of its smaller RoR bankroll. No source data is cited for these sims — [Casino News Daily, Evaluating eight-deck games](https://www.casinonewsdaily.com/blackjack-guide/evaluating-eight-deck-games/)
- RoR rescaling for those tables: 1% RoR = 5% bankroll × 1.54; 10% = ÷1.30; 15% = ÷1.58 — [Casino News Daily](https://www.casinonewsdaily.com/blackjack-guide/evaluating-eight-deck-games/)
- 6D Atlantic City, 1-8 spread, 200M hands (LVA forum post): Wong Play All +0.50%, "No Neg." (sit out negative counts) +0.98% — [LVA, gambling with an edge](https://www.lasvegasadvisor.com/gambling-with-an-edge/?p=123553) (from search summary; page not fetched directly)
- 8D, Adelaide rules (Australian ENHC-type), 50% penetration, Wong Halves, 2 boxes, 60 rounds/hr: win rate 0.539% with a 25-unit base and a 1-20 max spread, about 5.17 units/8 hr. Single-hand variance 1.13, covariance of 2 hands 0.5 — [urbino.net](https://urbino.net/?p=1599)
- An open-source simulator implements wonging as "doesn't play when TC < 1" — [blackjack-strategy-simulator docs](https://blackjack-strategy-simulator.readthedocs.io/en/latest/betting_strategies.html)

### Inferences
- **Suggested defaults for the tool** (configurable): wong-in at TC ≥ +2 (peek) or ≥ +2 to +3 (ENHC / no DAS). Stay while TC ≥ +1. Wong out when TC < +1 or at the shuffle. These sit inside Werthamer's +2 to +3 range and above the TC ≈ +1 to +1.4 break-even derived in Section 2.
- At 50% pen the cut comes after ~4 decks. On a live-dealer table at ~60 rounds/hr (the urbino.net assumption) with ~6-7 players, a shoe lasts roughly 30-40 rounds. Only the later rounds of a shoe are likely to cross +2, so most shoes yield zero or a handful of playable rounds. The cost of observing is low for an online tool, which can watch several tables at once.
- Edge on hands played at a TC +2 entry is roughly +0.5% to +1% (linear model). The hourly result depends on how many tables are monitored, not on the edge per hand.

### Gaps
- No published wonging sim for 8D at exactly 50% pen was found. The Casino News Daily sims start at 75%. The Adelaide 50% pen figure is play-all-style with Wong Halves, not back-counting.
- No published "hands played per shoe at TC ≥ X" for 8D/50% was found.

## 5. Index plays (Illustrious 18, Fab 4, insurance)

### Takeaway
Schlesinger's Illustrious 18 and Fab 4 surrenders (Hi-Lo, multi-deck) are published verbatim by Wizard of Odds. Insurance is at TC ≥ +3. Adding all indices instead of just I18 + Fab 4 adds only ~0.02-0.035% in 6D sims.

### Cited Findings
- Illustrious 18 (Schlesinger, *Blackjack Attack*, via Wizard of Odds). The play applies at TC ≥ index; negative indices mean hit/stand at or below. Source: [Wizard of Odds, High-Low](https://wizardofodds.com/games/blackjack/card-counting/high-low/)

  | # | Play | Index |
  |---|---|---|
  | 1 | Insurance | +3 |
  | 2 | 16 v 10 (stand) | 0 |
  | 3 | 15 v 10 (stand) | +4 |
  | 4 | T,T v 5 (split) | +5 |
  | 5 | T,T v 6 (split) | +4 |
  | 6 | 10 v 10 (double) | +4 |
  | 7 | 12 v 3 (stand) | +2 |
  | 8 | 12 v 2 (stand) | +3 |
  | 9 | 11 v A (double) | +1 |
  | 10 | 9 v 2 (double) | +1 |
  | 11 | 10 v A (double) | +4 |
  | 12 | 9 v 7 (double) | +3 |
  | 13 | 16 v 9 (stand) | +5 |
  | 14 | 13 v 2 (hit below) | −1 |
  | 15 | 12 v 4 (hit below) | 0 |
  | 16 | 12 v 5 (hit below) | −2 |
  | 17 | 12 v 6 (hit below) | −1 |
  | 18 | 13 v 3 (hit below) | −2 |
- Fab 4 surrenders: 14 v 10 at +3; 15 v 10 at 0; 15 v 9 at +2; 15 v A at +1 — [Wizard of Odds](https://wizardofodds.com/games/blackjack/card-counting/high-low/)
- "The player should take insurance if the True Count is +3 or greater" — [Wizard of Odds](https://wizardofodds.com/games/blackjack/card-counting/high-low/)
- 6D S17 DAS LS RSA sims, I18 + F4 vs all indices:
  - 1-10 spread at 4.5 decks: 0.587% vs 0.608%
  - 1-15 spread at 5 decks: 1.147% vs 1.182%

  Source: [Wizard of Odds](https://wizardofodds.com/games/blackjack/card-counting/high-low/)
- An early secondary source says the I18 assume Hi-Lo with true-count conversion and fall into insurance/stand/double/split groups (1986 origin) — [billzender.com](https://billzender.com/?p=1247)

### Inferences
- Implement the I18 as a lookup keyed on (player total/pair, dealer upcard) → (index, direction). Use Fab 4 only if the online table offers late surrender; most live-dealer tables do not.
- **ENHC caveats:** under no-hole-card rules some I18 entries change, most notably 11 v A and 10 v A (doubling against an ace is worse when the dealer can still have blackjack and you lose the double). T,T v 5/6 is unaffected. No published ENHC index values were retrieved.
- In 8D the I18 indices are close to the 6D values. The Wizard list is labelled generically for shoe games.

### Gaps
- No 8D-specific I18 values and no ENHC-specific index values were retrieved. LVA sells rule-specific index books (6D S17 DAS ENHC ES, etc.) — [LVA product](https://www.lasvegasadvisor.com/shop/?p=838436)

## 6. Bet sizing, variance, Kelly, RoR, N0, SCORE

### Takeaway
Per-hand variance for 6-8D blackjack is about 1.3 (SD about 1.14). Published wonging ramps for 8D are 1-2-4-6-12 units at TC +1/+2/+3/+4/+5. Schlesinger's SCORE and N0 (= variance / EV², the hands needed for one SD of profit) are the standard comparison metrics. A wonger's bankroll requirement for 5% RoR is about 1/3 that of a play-all counter in 8D sims.

### Cited Findings
- Variance per hand:
  - 6D S17 DAS LS RSA: 1.303, SD 1.142
  - 8D H17: 1.309
  - Covariance of two simultaneous hands: ~0.48-0.49
  - Variance per hand rises to 1.782 with 2 hands/round and 2.262 with 3

  Source: [Wizard of Odds Appendix 4](https://wizardofodds.com/games/blackjack/appendix/4/)
- Adelaide 8D figure: single-hand variance 1.13, 2-hand covariance 0.5 — [urbino.net](https://urbino.net/?p=1599)
- Wizard of Odds 6D sims report SD per initial bet of 1.50 to 3.54 depending on spread (1-5 to 1-15) — [Wizard of Odds, High-Low](https://wizardofodds.com/games/blackjack/card-counting/high-low/)
- N0 = variance / (EV per hand)², which gives about an 84% chance of being ahead after N0 hands — [west-point.org, Bank NO](https://www.west-point.org/users/usma1955/20228/V/Bank_NO.htm)
- SCORE (Schlesinger, *Blackjack Attack*) = "Standard Comparison of Risk and Expectation", a game-comparison metric assuming optimal betting — [Wikipedia: Don Schlesinger](https://en.wikipedia.org/wiki/Don_Schlesinger)
- One source describes SCORE as accounting "for optimal betting and risk in addition to advantage" and says it "directly relates to your hourly win rate" — [Blackjack in Color](https://blackjackincolor.com/penetration3.htm)
- *Blackjack Attack* contains a "simple risk of ruin" formula (p. 112) and a trip-ruin formula. One unreliable source gives the approximation RoR ≈ exp(−2·B·E/s²) (B = bankroll, E = EV per hand, s = SD per hand) — [search summary, low-quality calculator pages](https://adpoldipmametmag.netlify.app/blackjack-risk-of-ruin-calculator)
- 8D S17 DAS optimal ramps for play-all, 1-12 spread, 5% RoR: TC +1 ≈ 3.7u, +2 ≈ 9.3u, +3+ = 12u at 75% pen; TC +1 ≈ 2.4u, +2 ≈ 5.5u at 88%. Wonging ramp: 0 / 1 / 2 / 4 / 6 / 12 — [Casino News Daily](https://www.casinonewsdaily.com/blackjack-guide/evaluating-eight-deck-games/)
- Werthamer: back-counters face very low risk of ruin and may bet more aggressively or simply flat bet — [IDEAS/RePEc](https://ideas.repec.org/a/taf/intgms/v6y2006i2p111-122.html)
- A CVCX calculator reportedly reports SCORE, advantage and N0 for various penetrations at 13.5% RoR (garbled snippet, unverified) — search summary

### Inferences (standard formulas; not taken from a fetched primary source)
- **Kelly bet** for a single wager with small edge: f* ≈ EV / variance. With variance ≈ 1.3 and EV(TC) ≈ baseline + 0.005·TC: bet(TC) ≈ bankroll × (−0.0046 + 0.005·TC) / 1.3. Examples for peek with DAS:
  - TC +2: ≈ 0.42% of bankroll
  - TC +3: ≈ 0.80%
  - TC +4: ≈ 1.18%

  Half-Kelly (common practice) halves these. Full Kelly corresponds to 13.5% RoR in Schlesinger's convention (consistent with the CVCX "13.5%" snippet).
- **RoR approximation** for the tool: RoR ≈ exp(−2·μ·B / σ²), with μ = average win per hand in units and σ² = variance per hand of the actual bet distribution (Σ p_i·b_i²·1.3 + ...). Required bankroll for a target RoR r: B = −σ²·ln(r) / (2μ).
- **N0** = σ²/μ² on the same quantities. SCORE = μ²/σ² × 10⁶ × ... (Schlesinger normalizes to a $10,000 bank at optimal bets; exact normalization not retrieved). Practically, SCORE ∝ μ²/σ², so the tool can rank tables or settings by (EV/SD)².
- For a wonger flat-betting 1 unit only at TC ≥ +2 with EV ≈ 0.6%: N0 ≈ 1.3/0.006² ≈ 36,000 hands played. At 5% RoR, B ≈ 1.3·ln(20)/(2·0.006) ≈ 325 units. With a bet ramp (e.g. 1u at +2, 2u at +3, 4u at +4+), B grows roughly with average bet².
- All of these are approximations under the linear-edge model, not simulation results.

### Gaps
- Schlesinger's exact SCORE normalization and the Blackjack Attack RoR formula text could not be retrieved.
- The Qfit RoR page returned HTTP 500.
- No CVCX output for 8D/50% wonging was found.

## 7. Practical effect of 50% penetration on opportunity frequency

### Takeaway
Penetration is the single largest driver of counting profitability. In 8D, going from 6.5 to 7 decks dealt raises SCORE ~80% (Blackjack Attack via forum). Win rate at 0.5 decks cut is 7× that at 2.5 decks cut in 6D. At 4 of 8 decks, playable counts arise in a minority of shoes and late in the shoe. Wonging across many tables is the only practical way to accumulate volume.

### Cited Findings
- 8D H17 DAS 1-12: SCORE 10.27 at 6.5/8 dealt vs 18.49 at 7/8 dealt (Blackjack Attack Ch. 10, quoted) — [blackjackinfo forum](https://www.blackjackinfo.com/community/threads/what-penetration-increase-is-needed-for-8-deck-to-beat-6.13102/)
- 6D: "win rate with .5 decks cut off is seven times the win rate with 2.5 decks cut off" — [Blackjack in Color](https://blackjackincolor.com/penetration3.htm)
- "Where less decks are dealt out a card counter must increase his/her unit spread to achieve the same percentage profit" (8D, Adelaide, 50%) — [urbino.net](https://urbino.net/?p=1599)
- Wizard of Odds 6D: 4 decks dealt with a 1-10 spread gives +0.368%; 5 decks dealt gives +0.837% (I18+F4, S17 DAS LS RSA). Deeper penetration more than doubles the edge — [Wizard of Odds](https://wizardofodds.com/games/blackjack/card-counting/high-low/)

### Inferences
- A 50%-pen 8D shoe (4 decks dealt) is markedly worse than the shallowest 6D case in Wizard's table (4 of 6 decks = 67%). Expect play-all counting to be roughly break-even or negative even with spreads of 1-10+. Back-counting is necessary, not optional.
- The tool should log, per table, cards seen, the TC trajectory, and the hands at each TC bucket. That builds its own empirical frequency distribution, which no published source covers for this exact game.

### Gaps
- No published hands-per-hour or opportunities-per-shoe figures for live-dealer online 8D tables were found.
