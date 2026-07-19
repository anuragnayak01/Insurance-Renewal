"""
One-off script to populate the KB with sample insurance content so Q1/Q2
retrieval can be demoed and tested end to end.

Replace the SAMPLE_DOCS list with real scraped/PDF content before final
submission — this is here so the pipeline is runnable today.

Run: python -m question_2_kb.seed_ingest
"""
import logging

from question_2_kb.parser import DataCleaner
from question_2_kb.embedder import KnowledgeBaseEmbedder

logging.basicConfig(level=logging.INFO)

# Deliberately messy — each doc below exercises a specific cleaning step, so
# the pipeline's effect is actually visible (not just present in code with
# nothing to clean). Compare doc["content"] to what lands in Qdrant after
# run() to see terminology/date/PII changes and dedup skips for yourself.
#
# Replace with real scraped/PDF content before final submission — this is
# here so every step of the pipeline is demonstrably exercised today.
SAMPLE_DOCS = [
    {
        "title": "Auto Policy Grace Period",
        "category": "policy_rules",
        "source": "policy_handbook_v2.pdf",
        "content": (
            "Terms of Use | Privacy Policy | Contact Us  "
            "Comprehensive Auto policies include a 14-day grace-period after "
            "the renewal wndow closing on 15/03/2026. If premia is not paid "
            "within this window, coverage lapses and any claims filed during "
            "the lapse are not payable. Policy holder can reinstate a lapsed "
            "policy within 30 days subject to a re-underwriting review. "
            "Subscribe to our newsletter for more updates."
        ),
    },
    {
        # Deliberate near-duplicate of the doc above (same fact, reworded) —
        # tests whether _is_near_duplicate() actually catches it during this
        # same ingestion run, rather than silently double-storing the fact.
        "title": "Auto Policy Grace Period (duplicate source)",
        "category": "policy_rules",
        "source": "website:/faq/auto-renewal",
        "content": (
            "Comprehensive Auto policies include a 14-day grace period after "
            "the renewal window closing on 2026-03-15. If premiums are not "
            "paid within this window, coverage lapses and any claims filed "
            "during the lapse are not payable. Policyholders can reinstate a "
            "lapsed policy within 30 days subject to a re-underwriting review."
        ),
    },
    {
        "title": "Branch Partnership Benefits",
        "category": "partnership_benefits",
        "source": "website:/partners/branch-benefits",
        "content": (
            "All Rights Reserved 2026  "
            "Operational, marketing, and technology support is provided to "
            "branch partners, including co-branded renewal reminder "
            "campaigns and access to the partner referral portal. See our "
            "Cookie Policy for details on how we track partner referrals."
        ),
    },
    {
        "title": "Motor Insurance Premium Structure",
        "category": "product_info",
        "source": "website:/products/motor-insurance",
        "content": (
            "Motor insurance premia are calculated based on vehicle age, "
            "insured declared value (IDV), no-claim bonus (NCB) percentage, "
            "and add-on riders selected such as zero depreciation and engine "
            "protect. NCB can reduce the base premium by up to 50 percent "
            "for a five-year claim-free record. Refer to the T&Cs for the "
            "full IDV depreciation schedule."
        ),
    },
    {
        "title": "Health Insurance Waiting Periods",
        "category": "policy_rules",
        "source": "policy_handbook_v2.pdf",
        "content": (
            "Health insurance policies carry a 30-day initial waiting-period "
            "for all illnesses except accidents, a 2-year waiting period for "
            "specified procedures such as cataract and hernia surgery, and a "
            "4-year waiting period for pre-existing conditions declared at "
            "the time of purchase, effective from 01/04/2026."
        ),
    },
    {
        "title": "Renewal Payment Channels",
        "category": "qualification",
        "source": "website:/faq/payments",
        "content": (
            "Renewal payments can be made via the renewal link sent by SMS "
            "or email, through net banking, UPI, or credit/debit card. "
            "Payments made after the grace-period require a fresh proposal "
            "form and may be subject to a medical re-examination for health "
            "policies. For payment support contact us at billing@insurer.com "
            "or call +919876543210."
        ),
    },
    {
        # Deliberately contains PII in multiple formats, to prove mask_pii()
        # actually catches policy IDs, phone numbers, and emails together —
        # not just one pattern in isolation.
        "title": "Sample Escalation Note (internal, PII test)",
        "category": "qualification",
        "source": "internal:/escalation_notes/sample",
        "content": (
            "Customer policy AB-2024-00931 has a pending re-underwriting "
            "review after grace-period lapse. Customer contact: "
            "+919812345678, email priya.sharma@example.com. Escalated to "
            "specialist queue on 10/02/2026 pending manager review."
        ),
    },
]


def run():
    embedder = KnowledgeBaseEmbedder()
    embedder.ensure_collection()

    summary = []
    for doc in SAMPLE_DOCS:
        cleaned = DataCleaner.clean_text(doc["content"])
        cleaned = DataCleaner.standardize_terminology(cleaned)
        cleaned = DataCleaner.standardize_dates(cleaned)
        cleaned, pii_found = DataCleaner.mask_pii(cleaned)

        result = embedder.chunk_and_upload(
            text=cleaned,
            title=doc["title"],
            category=doc["category"],
            source=doc["source"],
            version="1.0",
            contains_pii=pii_found,
        )
        summary.append(result)
        print(f"Ingested: {doc['title']} -> {result}")
        if result.get("chunks_skipped_as_duplicate", 0) > 0:
            print(f"  (dedup working: skipped {result['chunks_skipped_as_duplicate']} near-duplicate chunk(s))")
        if pii_found:
            print(f"  (PII masking working: contains_pii=True, cleaned text: {cleaned[:120]}...)")

    return summary


if __name__ == "__main__":
    run()
