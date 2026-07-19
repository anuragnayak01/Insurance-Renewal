# Q3 — Localization Evidence

## ASR configuration (per brief: report provider/model, languages tested,
## code-switching behavior, approximate quality, observed errors, and
## regional-accent performance for Indonesia)

| Market | Provider/model | Language setting | Notes |
|---|---|---|---|
| Philippines | Deepgram nova-3 | `language="multi"` (set via `AGENT_LOCALE=ph` in `agent.py`) | Deepgram's `multi` mode auto-detects across supported languages per utterance, which is what natural Taglish code-switching needs — a fixed `en` or `tl` setting would force every utterance into one language and mistranscribe the other |
| Indonesia | Deepgram nova-3 | `language="multi"` (set via `AGENT_LOCALE=id`) | Same reasoning — formal/colloquial Bahasa plus English finance loanwords (cicilan, tenor, DP) code-switch within single sentences |

**Not yet measured** (needs the actual recorded calls, step below):
code-switching accuracy, transcription error examples, and — critically —
**regional-accent performance for Indonesia**, which the brief explicitly
requires as its own reported dimension, not just standard Jakarta speech.
Deepgram nova-3's `multi` mode does not let you specify a target Indonesian
region/accent directly; the honest approach is to actually test with an
accented speaker (or accented sample audio) and report what happens, not
assume it works.

## Native TTS — documented compromise
The agent currently uses **Deepgram Aura-2 `aura-2-thalia-en`** for all
three locales (English, PH, ID) — an English-only voice. This means PH/ID
responses are currently spoken with English phonetics applied to
Tagalog/Bahasa text, not a native Filipino or Indonesian voice.

This is a real gap against the brief's "use Filipino and Indonesian voices
where possible" requirement. Checked Deepgram's Aura-2 voice list — it does
not currently include dedicated Filipino or Indonesian voices. Options to
close this gap, not yet implemented:
- Swap TTS provider for PH/ID specifically to one with native voices (e.g.
  ElevenLabs has broader language coverage, but that reopens the "which
  keys are free tier" tradeoffs from earlier in this project)
- Document as a known limitation and ship as-is for this assessment, which
  is what's currently done

## Adaptation evidence — localization, not translation

### Philippines (3 examples)
1. **Payment urgency**: a literal translation of "Please pay soon to avoid
   lapse" would be stiff formal Tagalog. The actual prompt uses
   *"Bayaran po nang maaga ang premium para hindi mag-lapse ang coverage
   niyo"* — mixing the English loanwords "premium"/"coverage" naturally
   into the Tagalog sentence structure (with the respectful "po"), which is
   how this is actually said in the Philippines market, not how a
   dictionary would translate it.
2. **Register**: the system prompt explicitly instructs "handle English,
   Tagalog, and natural Taglish" and to stay "polite, helpful, and
   compliant" — encoding the expectation that a caller may switch between
   all three mid-sentence, and that politeness markers (po/opo) matter
   independent of which language is active.
3. **Objection handling tone**: rather than a generic discount pitch, the
   prompt directs the agent to "emphasize family protection, bank ease" for
   objections — reflecting that Philippine bancassurance sales culture
   leans on family-protection framing and the trust of the bank
   relationship, not a price-only argument.

### Indonesia (3 examples)
1. **Terminology, not vocabulary substitution**: the prompt uses "cicilan,
   tenor, denda, angsuran, jatuh tempo" — these are specific multifinance
   industry terms with precise meaning (tenor = loan term length, denda =
   late fee, angsuran = installment amount), not just Bahasa words for
   "payment" and "fee." Using the wrong one of these in context would sound
   foreign to an actual Indonesian borrower even though it's technically
   Bahasa.
2. **Formal/colloquial register switching**: the prompt explicitly supports
   both formal and colloquial Bahasa rather than picking one — a
   collections call to an older, formal customer and a follow-up text-style
   reminder to a younger customer would genuinely use different registers
   in real Indonesian consumer finance calls.
3. **English loanword handling**: the brief calls out "finance-related
   English loanwords" as something to support, not eliminate — e.g. "DP"
   (down payment) is used as-is in everyday Indonesian finance conversation
   rather than translated to "uang muka" every time, matching actual market
   speech patterns.

## Required test coverage — recording checklist
Run via `AGENT_LOCALE=ph` or `AGENT_LOCALE=id` + `python -m
question_1_3_voice.agent dev`, connect via the Agents Playground, speak
each scenario, paste transcripts into `test_calls/localized_test_scenarios.md`.

| # | Scenario | PH | ID |
|---|---|---|---|
| 1 | Cooperative customer | ☐ | ☐ |
| 2 | Sector-specific objection | ☐ (e.g. "mahal masyado ang premium") | ☐ (e.g. "cicilan terlalu mahal") |
| 3 | Mixed English/finance terms | ☐ | ☐ |
| 4 | Colloquial speech | ☐ | ☐ |
| 5 | Human escalation | ☐ | ☐ |
| 6 | Regional accent (ID only) | n/a | ☐ — **needs a non-Jakarta-accented speaker or sample; not yet sourced** |

Two recorded calls per market minimum, per the brief — the 6 rows above can
be combined into 2 calls per market rather than 6 separate ones (e.g. one
call covering cooperative+objection+mixed-terms, a second covering
colloquial+escalation for PH; same pattern for ID plus the accent row).
