# Q3 Required Test Call Scenarios — Philippines & Indonesia

Run with `AGENT_LOCALE=ph` or `AGENT_LOCALE=id` set before starting the
agent (`python -m question_1_3_voice.agent dev`), connect via the Agents
Playground, record, paste transcripts below. See
`question_3_localized/localization_evidence.md` for the ASR/TTS
configuration and localization-adaptation writeup this pairs with.

---

## Philippines — Call 1 (cooperative + objection + mixed terms)
**Script to play:** Confirm identity in Taglish, agree to the renewal terms,
then push back once — "grabe naman, ang mahal ng premium" (price
objection) — mixing English insurance terms into Tagalog naturally.
**Expected bot behavior:** Responds in matching Taglish register, calls
`kb_search` on the objection, cites a KB fact rather than inventing a
counter-argument.

Transcript:
```
[paste here]
```
Result / verdict:

---

## Philippines — Call 2 (colloquial + human escalation)
**Script to play:** Speak casually/colloquially throughout, then explicitly
ask for a human — "gusto ko makausap yung tao, hindi bot."
**Expected bot behavior:** Stays in Taglish/Tagalog (no unexpected English
switch), acknowledges, confirms callback, logs `escalated=true`.

Transcript:
```
[paste here]
```
Result / verdict:

---

## Indonesia — Call 1 (cooperative + objection + mixed terms)
**Script to play:** Confirm identity, hear the installment reminder, object
once — "cicilan ini kemahalan, tenornya juga terlalu pendek" — using real
multifinance terminology mixed with a mild objection.
**Expected bot behavior:** Responds in matching Bahasa register, calls
`kb_search`, uses correct terminology back (denda/tenor/angsuran), doesn't
default to generic translated phrasing.

Transcript:
```
[paste here]
```
Result / verdict:

---

## Indonesia — Call 2 (colloquial + human escalation)
**Script to play:** Speak colloquially, then ask for a human agent —
"saya mau bicara sama orang aja deh, bukan bot."
**Expected bot behavior:** Stays in Bahasa (no unexpected English switch),
confirms callback, logs `escalated=true`.

Transcript:
```
[paste here]
```
Result / verdict:

---

## Indonesia — Call 3 (regional accent, required by brief)
**Script to play:** Same cooperative flow as Call 1, but spoken by (or
using sample audio from) a speaker with a non-Jakarta regional accent —
e.g. Javanese, Sundanese, or Batak-accented Indonesian.
**Expected bot behavior:** Same as Call 1 — this call specifically tests
whether Deepgram's `multi` STT mode transcribes accented Indonesian
accurately, or degrades compared to standard-accent Call 1.
**Status:** not yet recorded — needs a speaker or sample audio with a
genuine non-Jakarta accent; using a standard-accent speaker here would not
actually satisfy this requirement.

Transcript:
```
[paste here]
```
Result / verdict:
**Comparison to Call 1 (standard accent):** [note any accuracy difference observed]

---

## Summary table

| Market | Call | Scenario | Result |
|---|---|---|---|
| PH | 1 | Cooperative + objection + mixed terms | |
| PH | 2 | Colloquial + escalation | |
| ID | 1 | Cooperative + objection + mixed terms | |
| ID | 2 | Colloquial + escalation | |
| ID | 3 | Regional accent | |
