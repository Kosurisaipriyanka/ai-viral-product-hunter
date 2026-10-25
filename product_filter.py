"""Transparent rule-based screening for YouTube product-discovery candidates."""
import re

DEMO_WORDS = ("demo", "demonstration", "before and after", "how to use", "review", "unboxing", "test", "asmr", "satisfying", "comparison", "works", "hack")
PROBLEM_WORDS = ("clean", "organize", "organizer", "remove", "fix", "save space", "portable", "leak", "mess", "solution", "easy", "spill", "charge", "store")
EMOTION_WORDS = ("wow", "satisfying", "genius", "amazing", "life changing", "must have", "you need", "surprising", "cool gadget")
BUNDLE_WORDS = ("set", "kit", "bundle", "3 in 1", "2 in 1", "accessories", "multi", "pack")
EVERGREEN_WORDS = ("kitchen", "home", "cleaning", "pet", "travel", "storage", "organizer", "fitness", "office", "blender", "lamp", "bottle", "vacuum", "charger", "mop", "brush", "shaver", "massager", "bag", "fan", "tool", "gadget", "grinder", "chopper", "light", "holder")
PRODUCT_WORDS = ("product", "products", "gadget", "gadgets", "blender", "juicer", "organizer", "cleaner", "vacuum", "bottle", "lamp", "light", "charger", "mop", "brush", "shaver", "massager", "bag", "fan", "tool", "kitchen", "pet", "travel", "storage", "accessory", "accessories", "amazon finds", "home improvement", "fitness equipment", "phone stand", "tripod", "headphones", "earbuds", "power bank", "water filter", "air fryer", "mini oven", "drawer", "scrubber", "dispenser")
IRRELEVANT_WORDS = ("resume", "resumes", "recruiter", "recruitment", "job interview", "shortlisted for", "product management role", "mba admission", "exam preparation", "stock market", "crypto trading", "political speech")
RISK_WORDS = ("weapon", "gun", "tobacco", "vape", "supplement", "medical cure", "counterfeit", "adult toy", "fire cracker")


def screen_video_candidates(items: list[dict]) -> list[dict]:
    """Keep likely physical-product videos and rank them using explainable keyword signals."""
    results = []
    rejected_count = 0
    for item in items:
        text = f"{item.get('title', '')} {item.get('description', '')}".casefold()
        irrelevant = [word for word in IRRELEVANT_WORDS if word in text]
        product_matches = [word for word in PRODUCT_WORDS if word in text]
        if irrelevant or not product_matches:
            rejected_count += 1
            continue

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
            "matched_signals": ", ".join(reasons) if reasons else "No positive keyword signals found",
            "product_keyword_matches": ", ".join(product_matches[:8]),
            "risk_flags": ", ".join(risk_flags),
            "assessment_limits": "Keyword-based first-pass screen only. Product size, supplier cost, shipping, competition, year-round demand, and actual sales are not verified.",
        })
    results.sort(key=lambda item: (item["screening_score"], item.get("views") or 0), reverse=True)
    return results
