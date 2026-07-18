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

SAMPLE_DOCS = [
    {
        "title": "Auto Policy Grace Period",
        "category": "policy_rules",
        "source": "policy_handbook_v2.pdf",
        "content": (
            "Comprehensive Auto policies include a 14-day grace period after the "
            "renewal due date. If the premium is not paid within this window, "
            "coverage lapses and any claims filed during the lapse are not payable. "
            "Policyholders can reinstate a lapsed policy within 30 days subject to "
            "a re-underwriting review."
        ),
    },
    {
        "title": "Branch Partnership Benefits",
        "category": "partnership_benefits",
        "source": "website:/partners/branch-benefits",
        "content": (
            "Operational, marketing, and technology support is provided to branch "
            "partners, including co-branded renewal reminder campaigns and access "
            "to the partner referral portal."
        ),
    },
    {
        "title": "Motor Insurance Premium Structure",
        "category": "product_info",
        "source": "website:/products/motor-insurance",
        "content": (
            "Motor insurance premiums are calculated based on vehicle age, insured "
            "declared value (IDV), no-claim bonus (NCB) percentage, and add-on "
            "riders selected such as zero depreciation and engine protect. NCB can "
            "reduce the base premium by up to 50 percent for a five-year claim-free "
            "record."
        ),
    },
    {
        "title": "Health Insurance Waiting Periods",
        "category": "policy_rules",
        "source": "policy_handbook_v2.pdf",
        "content": (
            "Health insurance policies carry a 30-day initial waiting period for "
            "all illnesses except accidents, a 2-year waiting period for specified "
            "procedures such as cataract and hernia surgery, and a 4-year waiting "
            "period for pre-existing conditions declared at the time of purchase."
        ),
    },
    {
        "title": "Renewal Payment Channels",
        "category": "qualification",
        "source": "website:/faq/payments",
        "content": (
            "Renewal payments can be made via the renewal link sent by SMS or "
            "email, through net banking, UPI, or credit/debit card. Payments made "
            "after the grace period require a fresh proposal form and may be "
            "subject to a medical re-examination for health policies."
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

    return summary


if __name__ == "__main__":
    run()
