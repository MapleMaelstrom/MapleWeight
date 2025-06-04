import math

# Foraging weight function based on EXP
def foraging_exp_weight(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})

    # EXP-based weight
    exp = member.get("player_data", {}).get("experience", {}).get("SKILL_FORAGING", 0)
    value = ((exp + 10_000_000) / 30_000_000)
    log_term = math.log(value, 200)
    exp_score = int((1000 * log_term + 208) * 1.2)

    total_score = exp_score
    breakdown = f"{exp:,} Foraging EXP → +{exp_score}"

    return total_score, breakdown

def cloak_weight(items):
    for item in items:
        item_id = item.get("tag", {}).get("ExtraAttributes", {}).get("id", "")
        if item_id == "ANNIHILATION_CLOAK":
            return 35, "Annihilation Cloak → +35"
        elif item_id == "DESTRUCTION_CLOAK":
            return 15, "Destruction Cloak → +15"
    return 0, []

def foraging_weight(profile, uuid, items):
    foraging_weights = []

    exp_score, exp_desc = foraging_exp_weight(profile, uuid)
    foraging_weights.append([exp_desc, exp_score])

    cloak_score, cloak_desc = cloak_weight(items)
    foraging_weights.append([cloak_desc, cloak_score])

    total = sum(score for _, score in foraging_weights if score != 0)
    return total, foraging_weights
