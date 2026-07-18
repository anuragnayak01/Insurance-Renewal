"""
Runs the required retrieval-test queries against the KB and writes a
markdown log with: query, retrieved chunk, source, relevance explanation,
and a verdict slot (correct / partially correct / incorrect) for the
human reviewer to fill in after reading the actual retrieved content.

Run: python -m retrieval_tests.run_retrieval_tests
"""
from question_2_kb.embedder import KnowledgeBaseEmbedder

# One query per required category: product, policy, qualification, FAQ, objection.
TEST_QUERIES = [
    ("product", "How is my motor insurance premium calculated?"),
    ("policy", "What happens if I don't pay before the grace period ends?"),
    ("qualification", "Can I pay my renewal after the grace period?"),
    ("faq", "What waiting period applies to pre-existing conditions?"),
    ("objection", "Why should I renew instead of switching insurers for a cheaper rate?"),
]


def run():
    embedder = KnowledgeBaseEmbedder()
    rows = []

    for category, query in TEST_QUERIES:
        result = embedder.search_grounded_context(query)

        if result is None:
            rows.append(
                f"### [{category}] {query}\n"
                f"- Retrieved: **none** (below similarity threshold)\n"
                f"- Source: n/a\n"
                f"- Relevance: no chunk in the KB clears the confidence threshold for this query\n"
                f"- Verdict: **incorrect** (expected, if no source doc covers this) "
                f"or flag as a KB coverage gap\n"
            )
            continue

        rows.append(
            f"### [{category}] {query}\n"
            f"- Retrieved chunk: {result['content']}\n"
            f"- Source: {result['source']} (record_id: {result['record_id']}, score: {result['score']})\n"
            f"- Relevance: fill in — does the chunk actually answer the question asked?\n"
            f"- Verdict: fill in — correct / partially correct / incorrect\n"
        )

    output = "# Retrieval Test Log\n\n" + "\n".join(rows)
    with open("retrieval_tests/retrieval_test_log.md", "w") as f:
        f.write(output)
    print(output)


if __name__ == "__main__":
    run()
