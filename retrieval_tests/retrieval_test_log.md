# Q2 — Retrieval Testing Log

## How to reproduce these results
```bash
python -m question_2_kb.seed_ingest        # populates Qdrant with SAMPLE_DOCS
python -m retrieval_tests.run_retrieval_tests
```
Or query directly via the deployed API:
```bash
curl -X POST https://<your-render-url>/api/kb-search -H "Content-Type: application/json" -d '{"query": "..."}'
```

Each result below needs: **user question**, **retrieved chunk**, **source
reference**, **relevance explanation**, and **verdict** (correct / partially
correct / incorrect) — per the brief's required format. Run each query
above and fill in the retrieved chunk / score / verdict columns, replacing
the `[PENDING — run and paste]` placeholders.

**Before running**: `RETRIEVAL_SCORE_THRESHOLD` in `config.py` was `0.20`
(too loose — verified during testing that it let a wrong document through
as "grounded"). Recommend raising to `0.45-0.5` and re-running these 5
queries to confirm results tighten up, since a looser threshold risks a
"partially correct" or "incorrect" verdict slipping through as if it were
correct.

---

## 1. Product question
**Query:** "How is my motor insurance premium calculated?"
**Expected match:** Motor Insurance Premium Structure
**Retrieved chunk:** `[PENDING — run and paste]`
**Source:** `[PENDING]`
**Score:** `[PENDING]`
**Relevance explanation:** `[PENDING — does the retrieved chunk actually answer this, or just mention similar keywords?]`
**Verdict:** `[PENDING — correct / partially correct / incorrect]`

---

## 2. Policy question
**Query:** "What's the waiting period for pre-existing conditions on my health policy?"
**Expected match:** Health Insurance Waiting Periods
**Retrieved chunk:** `[PENDING]`
**Source:** `[PENDING]`
**Score:** `[PENDING]`
**Relevance explanation:** `[PENDING]`
**Verdict:** `[PENDING]`

---

## 3. Qualification / process question
**Query:** "What payment methods can I use to renew?"
**Expected match:** Renewal Payment Channels
**Retrieved chunk:** `[PENDING]`
**Source:** `[PENDING]`
**Score:** `[PENDING]`
**Relevance explanation:** `[PENDING]`
**Verdict:** `[PENDING]`
**Note:** already confirmed working in earlier manual testing — scored
0.8062, correctly returned Renewal Payment Channels. Re-run here for the
formal record.

---

## 4. FAQ / grace-period question
**Query:** "What happens if I miss my renewal payment deadline?"
**Expected match:** Auto Policy Grace Period
**Retrieved chunk:** `[PENDING]`
**Source:** `[PENDING]`
**Score:** `[PENDING]`
**Relevance explanation:** `[PENDING]`
**Verdict:** `[PENDING]`
**Note:** with two near-duplicate "Auto Policy Grace Period" docs seeded
(testing dedup), confirm which source actually got stored — check
`seed_ingest.py`'s console output for a "dedup working: skipped N
near-duplicate chunk(s)" line to see whether the second copy was
correctly suppressed rather than double-indexed.

---

## 5. Objection question
**Query:** "This renewal is too expensive, why should I stay with this insurer?"
**Expected match:** Motor Insurance Premium Structure (NCB discount angle) or no match — this is a genuine edge case
**Retrieved chunk:** `[PENDING]`
**Source:** `[PENDING]`
**Score:** `[PENDING]`
**Relevance explanation:** `[PENDING — this is the hardest of the 5: does retrieval find the NCB-discount fact, or does it correctly return "no grounded answer" rather than force a weak match?]`
**Verdict:** `[PENDING]`
**Note:** this is the most important one to get right. If it forces a
weak/wrong match instead of admitting no strong answer exists, that's
worth reporting as-is (honest evidence) rather than swapping in an easier
query — the brief explicitly wants to see this handled correctly, not
avoided.

---

## Summary table (fill in after running all 5)

| # | Question type | Verdict | Notes |
|---|---|---|---|
| 1 | Product | | |
| 2 | Policy | | |
| 3 | Qualification | | |
| 4 | FAQ | | |
| 5 | Objection | | |
