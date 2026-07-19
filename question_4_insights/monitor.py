"""
Q4 Real-time Insights & Nudges Pipeline
Simulates streaming analysis on call audio/transcript.
"""

import time
import json
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class Nudge:
    type: str
    message: str
    confidence: float
    timestamp: str

class LiveCallMonitor:
    def __init__(self):
        self.nudge_history = {}  # topic -> last_time
        self.COOLDOWN_SECONDS = 30

    def detect_signals(self, transcript: str) -> list[str]:
        text = transcript.lower()
        signals = []
        if any(kw in text for kw in ["expensive", "mahal", "switch", "ganti", "too much", "can't afford"]):
            signals.append("price_objection")
        if any(kw in text for kw in ["second vehicle", "another car", "mobil lain", "kendaraan kedua", "second car", "another policy"]):
            signals.append("cross_sell_vehicle")
        if any(kw in text for kw in ["frustrated", "hassle", "annoyed", "susah", "kesal", "ridiculous", "fed up"]):
            signals.append("rising_frustration")
        if any(kw in text for kw in ["lose my job", "lost my job", "can't pay", "cannot pay", "behind on payment", "financial difficulty", "kehilangan pekerjaan"]):
            signals.append("payment_difficulty")
        if "disclosure" not in text and any(kw in text for kw in ["important", "before we proceed", "before we continue"]):
            # Simplistic compliance heuristic: agent is about to move forward on
            # something flagged "important" without the word "disclosure" ever
            # appearing nearby — a real implementation would check this against
            # a required-disclosure checklist per call type, not a keyword gap.
            signals.append("compliance_gap")
        return signals

    def generate_nudge(self, signal: str, transcript: str) -> Nudge:
        messages = {
            "price_objection": "Suggest highlighting NCB discount or value from KB.",
            "cross_sell_vehicle": "Offer multi-vehicle discount now.",
            "rising_frustration": "Acknowledge concern and offer callback.",
            "compliance_gap": "Remind required disclosure before proceeding.",
            "payment_difficulty": "Offer an approved payment-support or callback path.",
        }
        return Nudge(
            type=signal,
            message=messages.get(signal, "General follow-up"),
            confidence=0.75,
            timestamp=datetime.now().isoformat()
        )

    def should_nudge(self, signal: str) -> bool:
        now = time.time()
        if signal in self.nudge_history and now - self.nudge_history[signal] < self.COOLDOWN_SECONDS:
            return False
        self.nudge_history[signal] = now
        return True

    def process_transcript_chunk(self, transcript: str) -> dict:
        start = time.perf_counter()
        signals = self.detect_signals(transcript)
        nudges = []
        for sig in signals:
            if self.should_nudge(sig):
                nudges.append(self.generate_nudge(sig, transcript))
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {
            "nudges": [asdict(n) for n in nudges],
            "latency_ms": latency,
            "signals_detected": signals,
            "transcript_snippet": transcript[:100]
        }

# Example usage simulation
if __name__ == "__main__":
    monitor = LiveCallMonitor()
    test_transcript = "This is too expensive, I might switch. Also I have another car."
    result = monitor.process_transcript_chunk(test_transcript)
    print(json.dumps(result, indent=2))
