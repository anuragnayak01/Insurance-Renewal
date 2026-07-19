# Q4 — Live Insights Test Log

## Method
`question_4_insights/simulate_call.py` replays a sample call transcript
chunk-by-chunk, paced by estimated real-time speaking duration (not
delivered all at once), through the full pipeline: ASR → signal detection →
nudge generation → delivery. This satisfies the brief's "recording replayed
at real-time speed in chunks" streaming-input method.

Two ASR modes are supported:
- **Live**: each chunk is synthesized to audio via Deepgram Aura TTS, then
  transcribed back via Deepgram nova-3 STT — a genuine, measured round-trip
  latency, not an assumed number.
- **Simulated**: used when no Deepgram credentials are available; uses a
  labeled constant (250ms) based on Deepgram's published nova-3 streaming
  latency. Every report is tagged with which mode produced it.

Run any scenario:
```bash
python -m question_4_insights.simulate_call <call_name>
python -m question_4_insights.simulate_call <call_name> --speed 3
python -m question_4_insights.simulate_call <call_name> --api-base https://your-render-url.onrender.com
```

## Required test coverage — all 4 scenarios run

### 1. Missed cross-sell opportunity (`missed_cross_sell`)
Customer mentions buying a second car mid-call. Correctly fires
`cross_sell_vehicle` → "Offer multi-vehicle discount now."

**Also exposed a real false positive here**: chunk 3 ("...any questions
before we proceed") incidentally triggered `compliance_gap`, because the
current compliance heuristic is just "'before we proceed' appears without
the word 'disclosure' nearby." That's too naive for production — a real
implementation needs a per-call-type required-disclosure checklist, not a
keyword-adjacency guess. Kept as honest evidence rather than tuned away.

### 2. Skipped disclosure / compliance gap (`skipped_disclosure`)
Agent moves to "before we proceed" with the renewal terms without ever
stating a formal disclosure. Correctly fires `compliance_gap`.

### 3. Rising frustration (`rising_frustration`)
Customer expresses frustration twice in close succession ("such a hassle" /
"getting annoying", then "this is ridiculous"). **Only one nudge fired**,
not two — direct evidence the 30-second cooldown/duplicate-suppression
logic (`should_nudge`) is working as designed, not just present in code.

### 4. Noisy/ambiguous call (`noisy_ambiguous`)
Call with interruptions, a distracted customer, and no genuine
objection/frustration/cross-sell/compliance content. **Zero nudges fired**
across all 8 chunks — correct suppression, no false positives.

## Latency summary (simulated-ASR mode, 4 sample calls, 32 chunks total)

| Stage | P50 | P95 |
|---|---|---|
| End-to-end | 250.0ms | 250.2ms |
| ASR (simulated) | 250.0ms | 250.0ms |
| Signal extraction | 0.0ms | 0.1ms |

Signal extraction is consistently sub-millisecond — the keyword-based
detector is not the bottleneck; ASR dominates total latency, as expected.
**Re-run with live Deepgram credentials before final submission** (drop
`--simulated-asr`) to get a genuinely measured ASR number instead of the
labeled 250ms estimate — the harness supports this already, it just wasn't
run with real credentials in this environment.

## Known limitations
- Signal detection is keyword-based, not semantic — misses paraphrased
  objections/frustration, and is prone to the false positive documented
  above. At 10x call volume or with real (noisy, accented, code-switched)
  audio, keyword-matching accuracy would degrade further; a production
  version should use a small classifier or LLM-based signal extraction
  with the keyword version as a fast pre-filter.
- `delivery_ms` in the simulator only measures POSTing to `/api/insights`
  when `--api-base` is supplied — without it, delivery latency is reported
  as 0.0ms since there's nowhere real to deliver to.
- False-positive rate here is anecdotal (1 spurious nudge across 32 test
  chunks) — not a statistically rigorous rate, since the sample set is 4
  scripted calls, not a large/random real-call sample.
