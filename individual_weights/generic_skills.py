import math

# Alchemy weight based on the provided logarithmic formula
def alchemy_weight(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})
    exp = member.get("player_data", {}).get("experience", {}).get("SKILL_ALCHEMY", 0)

    value = ((exp + 10_000_000) / 30_000_000)
    log_term = math.log(value, 200)
    score = int((1000 * log_term + 208) * 0.5)

    return score, [f"{exp:,} Alchemy EXP → +{score}"]

# Carpentry weight uses same formula as alchemy, scaled by 0.8
def carpentry_weight(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})
    exp = member.get("player_data", {}).get("experience", {}).get("SKILL_CARPENTRY", 0)

    value = ((exp + 10_000_000) / 30_000_000)
    log_term = math.log(value, 200)
    score = int((1000 * log_term + 208) * 0.4)

    return score, [f"{exp:,} Carpentry EXP → +{score}"]

# Enchanting weight uses same formula as alchemy, scaled by 0.4
def enchanting_weight(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})
    exp = member.get("player_data", {}).get("experience", {}).get("SKILL_ENCHANTING", 0)

    value = ((exp + 10_000_000) / 30_000_000)
    log_term = math.log(value, 200)
    score = int((1000 * log_term + 208) * 0.2)

    return score, [f"{exp:,} Enchanting EXP → +{score}"]

# Taming weight function based on EXP and sacrificed pets
def taming_weight(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})

    # EXP-based weight
    exp = member.get("player_data", {}).get("experience", {}).get("SKILL_TAMING", 0)
    value = ((exp + 10_000_000) / 30_000_000)
    log_term = math.log(value, 200)
    exp_score = int((1000 * log_term + 208) * 0.2)

    # Sacrificed pets score
    sacrificed = member.get("pets_data", {}).get("pet_care", {}).get("pet_types_sacrificed", [])
    num_sacrificed = len(sacrificed)

    if num_sacrificed >= 10:
        pet_score = 150
    else:
        pet_score = 9 * num_sacrificed

    total_score = exp_score + pet_score
    breakdown = [f"{exp:,} Taming EXP → +{exp_score}", f"{num_sacrificed} Pets Sacrificed → +{pet_score}"]

    return total_score, breakdown

def generic_skill_weight(profile, uuid):
    weights = []

    alc_score, alc_desc = alchemy_weight(profile, uuid)
    weights.append([alc_desc, alc_score])

    carp_score, carp_desc = carpentry_weight(profile, uuid)
    weights.append([carp_desc, carp_score])

    ench_score, ench_desc = enchanting_weight(profile, uuid)
    weights.append([ench_desc, ench_score])

    taming_score, taming_desc = taming_weight(profile, uuid)
    weights.append([taming_desc, taming_score])

    total = sum(score for _, score in weights)
    breakdown = [desc for desc, _ in weights]

    return total, breakdown
