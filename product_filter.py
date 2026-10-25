"""Transparent rule-based screening for YouTube product-discovery candidates."""
import re

DEMO_WORDS = ("demo", "before and after", "how to", "review", "test", "asmr", "satisfying", "comparison", "works", "hack")
PROBLEM_WORDS = ("clean", "organize", "organizer", "remove", "fix", "save space", "portable", "leak", "pain", "mess", "solution", "easy")
EMOTION_WORDS = ("wow", "satisfying", "genius", "amazing", "life changing", "must have", "you need", "surprising")
BUNDLE_WORDS = ("set", "kit", "bundle", "3 in 1", "2 in 1", "accessories", "multi")
EVERGREEN_WORDS = ("kitchen", "home", "cleaning", "pet", "travel", "storage", "organizer", "fitness", "office")
RISK_WORDS = ("weapon", "gun", "tobacco", "vape", "supplement", "medical cure", "counterfeit", "adult toy", "fire cracker")


def screen_video_candidates(items: list[dict]) -> list[dict]:
    """Add a transparent screening score; this is not a sales or virality prediction."""
    results = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('description', '')}".casefold()
        signals = {
            "demonstration_signal": any(word in text for word in DEMO_WORDS),
            "problem_solving_signal": any(word in text for word in PROBLEM_WORDS),
            "emotional_hook_signal": any(word in text for word in EMOTION_WORDS),
            "bundle_potential_signal": any(word in text for word in BUNDLE_WORDS),
            "evergreen_category_signal": any(word in text for word in EVERGREEN_WORDS),
        }
        score = round(100 * sum(signals.values()) / len(signals))
        risk_flags = [word for word in RISK_WORDS if re.search(r"\\b" + re.escape(word) + r"\\b", text)]
        if risk_flags:
            score = min(score, 20)
        reasons = [label.replace("_signal", "").replace("_", " ") for label, matched in signals.items() if matched]
        results.append({
            **item,
            "screening_score": score,
            "screening_band": "Investigate" if score >= 60 and not risk_flags else ("Review carefully" if risk_flags else "Low evidence"),
            "matched_signals": ", ".join(reasons) if reasons else "No keyword signals found",
            "risk_flags": ", ".join(risk_flags),
            "assessment_limits": "Keyword-based first-pass screen only. Product size, supplier cost, shipping, competition, year-round demand, and actual sales are not verified.",
        })
    return sorted(results, key=lambda item: item["screening_score"], reverse=True)
