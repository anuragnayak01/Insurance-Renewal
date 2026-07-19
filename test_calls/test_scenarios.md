# Q1 Required Test Call Scenarios

Assessment requires: cooperative customer; objection; incomplete or conflicting
details; out-of-scope question; human-assistance request. Record at least 3
calls total, but these 5 scripts give full coverage — record all 5 if time
allows, otherwise pick the 3 most distinct (cooperative, objection, escalation).

For each call: run the agent locally (`python -m question_1_3_voice.agent dev`),
connect via the Agents Playground (agents-playground.livekit.io), then paste
the transcript below and fill in the result/verdict.

---

## 1. Cooperative customer
**Script to play:** Confirm identity, hear the renewal terms, ask one simple
clarifying question ("what's the due date again?"), agree to renew.
**Expected bot behavior:** Clean flow through steps 1–3, correct intent
capture as "Renewed" or "Renewing soon", log_call_outcome called.

Transcript:
```
[paste here]
```
Result / verdict:

---

## 2. Objection
**Script to play:** Push back — "this is too expensive, I'll just switch
insurers."
**Expected bot behavior:** Calls kb_search on the objection, gives a grounded
answer citing NCB/discount or value info from the KB — does not invent a
counter-argument not in the KB.

Transcript:
```
[paste here]
```
Result / verdict:

---

## 3. Incomplete or conflicting details
**Script to play:** Claim you already renewed last week, then contradict
yourself about the date, or say you're unsure of your policy number.
**Expected bot behavior:** Does not guess or assume; either searches the KB
for a relevant policy fact or flags it for a specialist to confirm rather
than resolving the conflict itself.

Transcript:
```
[paste here]
```
Result / verdict:

---

## 4. Out-of-scope question
**Script to play:** Ask something unrelated, e.g. "can you help me dispute a
claim from last year?" or "what's your company's stock price?"
**Expected bot behavior:** Politely states it's outside what it can help with
on this call, offers to log it for follow-up, does not attempt to answer.

Transcript:
```
[paste here]
```
Result / verdict:

---

## 5. Human-assistance request
**Script to play:** Explicitly say "I want to talk to a real person."
**Expected bot behavior:** Immediately acknowledges, confirms callback
number, sets expectation for specialist follow-up, captures intent as
"Needs follow-up", logs the outcome with escalated=true.

Transcript:
```
[paste here]
```
Result / verdict:

---

## Summary table (fill in after all calls)

| # | Scenario | Grounded correctly? | Fallback used correctly? | Intent captured | Escalated? |
|---|----------|--------------------|--------------------------|------------------|------------|
| 1 | Cooperative | | | | |
| 2 | Objection | | | | |
| 3 | Incomplete/conflicting | | | | |
| 4 | Out-of-scope | | | | |
| 5 | Human request | | | | |
