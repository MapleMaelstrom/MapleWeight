import json
from ..get_data import to_json_safe
import math

# Define tier values
tier_values = {
    "MYTHIC": 6,
    "LEGENDARY": 5,
    "EPIC": 4,
    "RARE": 3,
    "UNCOMMON": 2,
    "COMMON": 1
}

# Define pet names to normalize
wisp_variants = {"DROPLET_WISP", "FROST_WISP", "GLACIAL_WISP", "SUBZERO_WISP"}


def score_golden_dragons(pets, profile_data, uuid):
    valid_items = {
        "MINOS_RELIC": "Minos Relic",
        "DWARF_TURTLE_SHELMET": "Dwarf Turtle Shelmet",
        "ANTIQUE_REMEDIES": "Antique Remedies"
    }
    total_score = 0
    breakdown = []
    valid_gdrag_found = False
    fallback_gdrag = None

    for pet in pets:
        if pet.get("type") != "GOLDEN_DRAGON":
            continue

        held_item = pet.get("heldItem")
        level = min(int(((pet.get("exp", 0)) - 25358785) / 1886700) + 102, 200)
        item_name = valid_items.get(held_item)

        if item_name and level >= 100:
            score = round(500 * (level - 100) / 100)
            total_score += score
            breakdown.append(f"{item_name} GDrag (Level {level}) — {score} points")
            valid_gdrag_found = True
        elif not valid_gdrag_found and level >= 100:
            fallback_gdrag = (level, f"Plain GDrag (Level {level}) — {round(500 * (level - 100) / 100)} points (no valid item)")

    if not valid_gdrag_found and fallback_gdrag:
        level, text = fallback_gdrag
        score = round(500 * (level - 100) / 100)
        total_score += score
        breakdown.append(text)
    # Score based on gold collection
    gold = profile_data.get("members", {}).get(uuid, {}).get("collection", {}).get("GOLD_INGOT", 0)
    if gold >= 100_000_000:
        total_score += 100
        breakdown.append("Gold Collection ≥ 100M — 100 points")
    elif gold >= 10_000_000:
        total_score += 10
        breakdown.append("Gold Collection ≥ 10M — 10 points")

    # Score based on bank coins
    bank = profile_data.get("banking", {}).get("balance", 0)
    if bank >= 1_000_000_000:
        total_score += 50
        breakdown.append("Bank Balance ≥ 1B — 50 points")
    elif bank >= 900_000_000:
        total_score += 40
        breakdown.append("Bank Balance ≥ 900M — 40 points")

    return total_score, breakdown

def pet_score_weight(all_pets):
    # Track highest-tier pet per type
    best_pets = {}
    for pet in all_pets:
        pet_type = pet.get("type")
        if pet_type in wisp_variants:
            pet_type = "WISP"

        tier = pet.get("tier")
        exp = pet.get("exp", 0)

        if pet_type not in best_pets or tier_values[tier] > tier_values[best_pets[pet_type]["tier"]]:
            best_pets[pet_type] = {
                "tier": tier,
                "exp": exp
            }

    # Calculate raw pet score
    pet_score = 0
    for pet_type, info in best_pets.items():
        tier_score = tier_values[info["tier"]]
        bonus = 1 if info["tier"] in {"LEGENDARY", "MYTHIC"} and info["exp"] >= 25353230 else 0
        pet_score += tier_score + bonus


    return pet_weight_function(pet_score), f"Pet Score Estimate of {pet_score}"

def pet_weight_function(x):
    return int(max((x - 150) / 5, 0) ** 1.62)

def score_black_cat(pets):
    for pet in pets:
        if pet.get("type") != "BLACK_CAT":
            continue
        if pet.get("heldItem") != "MINOS_RELIC":
            continue
        if pet.get("tier") not in {"LEGENDARY", "MYTHIC"}:
            continue
        if pet.get("exp", 0) >= 25353230:  # Level 100 threshold
            return 50, "Level 100 Black Cat with Minos Relic — 50 points"
    return 0, None

def score_phoenix(pets):
    best_phoenix = None
    tier_order = {"COMMON": 1, "UNCOMMON": 2, "RARE": 3, "EPIC": 4, "LEGENDARY": 5, "MYTHIC": 6}

    for pet in pets:
        if pet.get("type") != "PHOENIX":
            continue
        if not best_phoenix or tier_order[pet["tier"]] > tier_order[best_phoenix["tier"]]:
            best_phoenix = pet

    if not best_phoenix:
        return 0, None

    exp = best_phoenix.get("exp", 0)
    tier = best_phoenix.get("tier")

    if tier == "EPIC":
        return (50, "Phoenix Level 81+ (EPIC) — 50 points") if exp > 4234500 else (40, "Phoenix ≤ 80 (EPIC) — 40 points")
    elif tier in {"LEGENDARY", "MYTHIC"}:
        return (50, "Phoenix Level 81+ (LEGENDARY) — 50 points") if exp > 5619230 else (40, "Phoenix ≤ 80 (LEGENDARY) — 40 points")
    else:
        return 0, "Phoenix found, but tier is too low to count"

def score_parrot(pets):
    best_parrot = None
    tier_order = {"COMMON": 1, "UNCOMMON": 2, "RARE": 3, "EPIC": 4, "LEGENDARY": 5, "MYTHIC": 6}

    for pet in pets:
        if pet.get("type") != "PARROT":
            continue
        if not best_parrot or tier_order[pet["tier"]] > tier_order[best_parrot["tier"]]:
            best_parrot = pet

    if not best_parrot:
        return 0, None

    score = 20
    desc = ["Parrot Pet — 20 points"]

    if best_parrot["exp"] >= 25353230:
        score += 10
        desc.append("Level 100 — +10")

    if best_parrot["tier"] in {"LEGENDARY", "MYTHIC"}:
        score += 5
        desc.append("Legendary or higher — +5")

    return score, ", ".join(desc)

def score_guardian(pets):
    for pet in pets:
        if pet.get("type") == "GUARDIAN" and pet.get("tier") == "MYTHIC":
            exp = pet.get("exp", 0)
            capped_exp = min(max(exp, 0), 25_353_230)
            weight = 1 + 9 * (capped_exp / 25_353_230)
            return int(weight), f"Mythic Guardian — +{int(weight)} points" if int(weight) == 10 else f"Mythic Guardian Sub Lvl 100 — +{int(weight)} points"
    return 0, None

def score_endermite(pets):
    for pet in pets:
        if pet.get("type") == "ENDERMITE" and pet.get("tier") == "MYTHIC":
            exp = pet.get("exp", 0)
            capped_exp = min(max(exp, 0), 25_353_230)
            weight = 1 + 9 * (capped_exp / 25_353_230)
            return int(weight), f"Mythic Endermite — +{int(weight)} points" if int(weight) == 10 else f"Mythic Endermite Sub Lvl 100 — +{int(weight)} points"
    return 0, None

def score_grandma_wolf(pets):
    for pet in pets:
        if pet.get("type") == "GRANDMA_WOLF" and pet.get("tier") == "LEGENDARY":
            exp = pet.get("exp", 0)
            capped_exp = min(max(exp, 0), 25_353_230)
            weight = 1 + 4 * (capped_exp / 25_353_230)
            return int(weight), f"Legendary Grandma Wolf — +{int(weight)} points" if int(weight) == 10 else f"Legendary Grandma Wolf Sub Lvl 100 — +{int(weight)} points"
    return 0, None


def score_ender_dragon(pets):
    best_score = 0
    best_desc = None

    for pet in pets:
        if pet.get("type") != "ENDER_DRAGON":
            continue

        tier = pet.get("tier")
        held_item = pet.get("heldItem")
        exp = pet.get("exp", 0)

        # Determine if it's tier boosted
        is_tier_boosted = tier == "EPIC" and held_item == "PET_ITEM_TIER_BOOST"
        is_legendary = tier == "LEGENDARY"
        is_epic = tier == "EPIC"

        if is_tier_boosted:
            base = 400 - 25  # tier boosted epic uses legendary base minus penalty
            level_progress = min(exp / 18_608_500, 1.0)
            level_score = 25 * level_progress
            desc = f"Tier-Boosted Ender Dragon (EPIC → LEGENDARY base) — {base + round(level_score)} points"
        elif is_legendary:
            base = 400
            level_progress = min(exp / 25_353_230, 1.0)
            level_score = 25 * level_progress
            desc = f"Legendary Ender Dragon — {base + round(level_score)} points"
        elif is_epic:
            base = 300
            level_progress = min(exp / 18_608_500, 1.0)
            level_score = 25 * level_progress
            desc = f"Epic Ender Dragon — {base + round(level_score)} points"
        else:
            continue

        total = base + round(level_score)
        if total > best_score:
            best_score = total
            best_desc = desc

    if best_score > 0:
        return best_score, best_desc
    return 0, None

def pet_weight(all_pets, profile, uuid):
    pet_weights = []

    gdrag_score, gdrag_desc = score_golden_dragons(all_pets, profile, uuid)
    if gdrag_score > 0:
        pet_weights.append(["Golden Dragon Score: " + ", ".join(gdrag_desc), gdrag_score])

    e_drag_score, e_drag_desc = score_ender_dragon(all_pets)
    if e_drag_score > 0:
        pet_weights.append([e_drag_desc, e_drag_score])

    pet_score, score_desc = pet_score_weight(all_pets)
    pet_weights.append([score_desc, pet_score])

    black_cat_score, black_cat_desc = score_black_cat(all_pets)
    if black_cat_score > 0:
        pet_weights.append([black_cat_desc, black_cat_score])

    phoenix_score, phoenix_desc = score_phoenix(all_pets)
    if phoenix_score > 0:
        pet_weights.append([phoenix_desc, phoenix_score])

    parrot_score, parrot_desc = score_parrot(all_pets)
    if parrot_score > 0:
        pet_weights.append([parrot_desc, parrot_score])

    guardian_score, guardian_desc = score_guardian(all_pets)
    if guardian_score > 0:
        pet_weights.append([guardian_desc, guardian_score])

    endermite_score, endermite_desc = score_endermite(all_pets)
    if endermite_score > 0:
        pet_weights.append([endermite_desc, endermite_score])

    total = sum(score for _, score in pet_weights)
    return total, pet_weights