

def compute_recyclability_score(item):
    material_scores = {
        "plastic": 10,
        "metal": 10,
        "glass": 10,
        "paper": 10,
        "styrofoam": -30,
        "plastic+foil": -20,
    }
    
    score = 0

    # Base score by category
    if item.get("category") == "recycling":
        score += 50
    elif item.get("category") == "trash":
        score -= 30

    # Material score
    score += material_scores.get(item.get("material", "").lower(), 0)

    # Cleanliness
    if item.get("clean", False):
        score += 10
    if item.get("contaminated", False):
        score -= 30

    # Confidence adjustment
    confidence = item.get("confidence", 1.0)
    score += int((confidence - 0.5) * 20)  # ±10 adjustment

    return max(0, min(100, score))
    

def compute_tray_score(items):
    scores = [compute_recyclability_score(item) for item in items]
    return round(sum(scores) / len(scores), 2) if scores else 0.0
