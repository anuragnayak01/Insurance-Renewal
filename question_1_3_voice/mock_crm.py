"""
Mock CRM — Q1's optional business action.

Appends each call outcome as a JSON line to crm_log.jsonl. This mirrors
the "push to CRM" step from the reference script without needing a real
CRM/database — good enough evidence for the assessment's "mock CRM
summary" option.
"""
import json
import os
from datetime import datetime, timezone

CRM_LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "crm_log.jsonl")


def log_outcome(customer_name: str, intent: str, escalated: bool, notes: str = "") -> dict:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer_name": customer_name,
        "intent": intent,
        "escalated": escalated,
        "notes": notes,
    }
    with open(CRM_LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record
