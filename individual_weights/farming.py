import math
import json
import re
from collections import defaultdict

def farming_exp_weight(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})

    farming_exp = (
        member.get("player_data", {})
              .get("experience", {})
              .get("SKILL_FARMING", 0)
    )

    if not isinstance(farming_exp, (int, float)) or farming_exp <= 0:
        return 0, []

    base = (farming_exp + 20000000) / 2000
    log_term = math.log(base, 200)
    weighted = (5000 * log_term) - 8700
    weight = max(0, round(weighted / 3.5))

    return weight, [f"{int(farming_exp):,} Farming Exp", f"{weight} Weight"]

def medal_score(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    medals = (
        profile.get("members", {})
        .get(normalized_uuid, {})
        .get("jacobs_contest", {})
        .get("unique_brackets", {})
    )

    # Priority from highest to lowest
    tiers = [("diamond", 5), ("platinum", 2), ("gold", 1)]
    crop_score = {}
    seen = set()

    # Custom name replacements
    name_map = {
        "INK_SACK:3": "Cactus",
        "MUSHROOM_COLLECTION": "Mushroom",
        "NETHER_STALK": "Nether Wart",
    }

    for tier_name, points in tiers:
        for crop in medals.get(tier_name, []):
            if crop not in seen:
                seen.add(crop)
                display_name = name_map.get(crop, crop)

                # Clean generic formatting
                display_name = display_name.replace("_", " ").replace(" Item", "").title()

                crop_score[display_name] = (tier_name.upper(), points)

    total = sum(points for _, points in crop_score.values())
    breakdown = ", ".join(f"{name} {tier} +{points}" for name, (tier, points) in crop_score.items())

    return total, [breakdown] if breakdown else []

def farming_pet_weight(profile, uuid, all_pets):
    max_exp = 25353230
    hedgehog_cap = 5619230

    # Define scoring rules
    scoring = {
        "ELEPHANT": {"LEGENDARY": 20, "exp_cap": max_exp},
        "MOOSHROOM_COW": {"LEGENDARY": 25, "exp_cap": max_exp},
        "SLUG": {"EPIC": 5, "LEGENDARY": 10, "exp_cap": max_exp},
        "HEDGEHOG": {"LEGENDARY": 15, "exp_cap": hedgehog_cap}
    }

    bandana_bonus = {
        "GREEN_BANDANA": 5,
        "BROWN_BANDANA": 5,
        "YELLOW_BANDANA": 1
    }

    best_by_type = {}

    for pet in all_pets:
        pet_type = pet.get("type")
        tier = pet.get("tier")
        exp = pet.get("exp", 0)
        item = pet.get("heldItem")

        if pet_type not in scoring or tier not in scoring[pet_type]:
            continue

        cap = scoring[pet_type].get("exp_cap", max_exp)
        cap_exp = min(exp, cap)
        base_score = scoring[pet_type][tier]
        scaled_score = (cap_exp / cap) * base_score

        bonus = bandana_bonus.get(item, 0)
        total_score = scaled_score + bonus

        if pet_type not in best_by_type or total_score > best_by_type[pet_type][0]:
            best_by_type[pet_type] = (total_score, f"{pet_type.title()} {tier.title()} +{round(total_score)}")

    total = round(sum(score for score, _ in best_by_type.values()))
    breakdown = ", ".join(desc for _, desc in best_by_type.values())

    return total, [breakdown] if breakdown else []

def visitor_weight(garden_data):
    commission = garden_data.get("commission_data", {})
    completed = commission.get("completed", {})
    total_completed = commission.get("total_completed", 0)

    score = 0
    unique_visitor_count = 0
    milestone_bonus = 0
    spaceman_bonus = 0

    for visitor, count in completed.items():
        if count >= 1:
            if visitor.lower() == "spaceman":
                spaceman_bonus = 20
            else:
                unique_visitor_count += 1

    score += int(max(0, unique_visitor_count - 50) ** 1.25)  # +1 per unique visitor
    score += spaceman_bonus

    # Determine milestone bonus
    milestone_thresholds = [
        1, 5, 10, 20, 50, 75, 100, 150, 250,
        500, 1000, 2000, 3000, 4000, 5000
    ]

    milestone_level = 0
    for i, threshold in enumerate(milestone_thresholds):
        if total_completed >= threshold:
            milestone_level = i + 1  # +1 since thresholds are 1-indexed
            if i >= 10:
                milestone_bonus += 4
            elif i >= 6:
                milestone_bonus += 2

    score += int(3 * milestone_bonus)

    breakdown = [
        f"{unique_visitor_count} Unique Visitors +{int(max(0, unique_visitor_count - 50) ** 1.25)}",
        f"Visitor Milestone {milestone_level} Reached +{int(1.5 * milestone_bonus)}",
        f"Spaceman Served +{spaceman_bonus}" if spaceman_bonus > 0 else None
    ]

    return score, [", ".join(filter(None, breakdown))]

def crop_upgrade_weight(garden_data):
    upgrades = garden_data.get("crop_upgrade_levels", {})
    score = 0

    for crop, level in upgrades.items():
        for i in range(3, level + 1, 2):  # Odd levels only starting at 3
            score += 1
        if level >= 8:
            score += 1  # Level 8 bonus

    breakdown = f"Crop Upgrade Weight +{score}"
    return score, breakdown

def crop_milestone_weight(garden_data):
    collected = garden_data.get("resources_collected", {})
    score = 0
    breakdown = []

    # Mapping of API crop names to display names
    crop_name_map = {
        "WHEAT": "Wheat",
        "POTATO_ITEM": "Potato",
        "CARROT_ITEM": "Carrot",
        "MELON": "Melon",
        "SUGAR_CANE": "Sugar Cane",
        "INK_SACK:3": "Cocoa Beans",
        "PUMPKIN": "Pumpkin",
        "NETHER_STALK": "Nether Wart",
        "CACTUS": "Cactus",
        "MUSHROOM_COLLECTION": "Mushroom"
    }

    milestone_totals = {
        "Wheat": 64143160,
        "Potato": 208747500,
        "Carrot": 208747500,
        "Melon": 320715800,
        "Sugar Cane": 128286320,
        "Cocoa Beans": 192665490,
        "Pumpkin": 64143160,
        "Nether Wart": 192665490,
        "Cactus": 128286320,
        "Mushroom": 64143160
    }

    for api_name, display_name in crop_name_map.items():
        harvested = collected.get(api_name, 0)
        total_required = milestone_totals.get(display_name)

        if total_required:
            percent = min(harvested / total_required, 1.0)
            crop_score = int(percent * 175)
            if percent == 1.0:
                crop_score += 25  # Bonus for full completion
                breakdown.append(f"{display_name}: 100% Complete ✅ +{crop_score}")
            else:
                breakdown.append(f"{display_name}: {percent:.0%} Complete +{crop_score}")
            score += crop_score

    return score, breakdown

def get_mathematical_hoes_by_crop(items):
    hoes_by_crop = defaultdict(list)

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")

        match = re.match(r"THEORETICAL_HOE_([A-Z_]+)_\d", item_id)
        if match:
            raw_crop = match.group(1)
            crop_key = {
                "WHEAT": "Wheat",
                "CARROT": "Carrot",
                "POTATO": "Potato",
                "CANE": "Sugar Cane",
                "NETHER_WART": "Nether Wart",
                "WARTS": "Nether Wart"
            }.get(raw_crop, raw_crop.title().replace("_", " "))

            hoes_by_crop[crop_key].append(item)

    return hoes_by_crop

# Define the gem tiers and a placeholder for gem bonus logic (can be customized)
gem_tiers = {
    "ROUGH": 1,
    "FLAWED": 1,
    "FINE": 2,
    "FLAWLESS": 4,
    "PERFECT": 7
}

gem_bonus = {}  # Placeholder if needed, assumed zero bonus per type for now

# Function to score gemstones
def gemstone_score(gems):
    score = 0
    unlocked = gems.get("unlocked_slots", [])
    score += 3 * len(unlocked)
    for slot in unlocked:
        gem_type = gems.get(slot + "_gem", None)
        if not gem_type:
            gem_type = slot.split("_")[0]
        quality = gems.get(slot, None)
        if quality is not None:
            if isinstance(quality, dict) or hasattr(quality, "get"):
                quality_str = str(quality.get("quality", ""))
            else:
                quality_str = str(quality)
            if quality_str.upper() in gem_tiers:
                base = gem_tiers[quality_str.upper()]
                bonus = gem_bonus.get(gem_type, 0)
                score += base + bonus
    return score

# Updated function to find and score the best mathematical hoe per crop
def score_best_mathematical_hoes(items):
    hoes_by_crop = get_mathematical_hoes_by_crop(items)
    scored = {}

    for crop, tools in hoes_by_crop.items():
        best_score = 0
        best_tool_name = "None"

        for tool in tools:
            score = 0
            extra = tool.get("tag", {}).get("ExtraAttributes", {})

            # Tier score
            item_id = extra.get("id", "")
            if "_1" in item_id:
                score += 1
            elif "_2" in item_id:
                score += 5
            elif "_3" in item_id:
                score += 20

            # Mined crops score
            counter = extra.get("counter", 0)
            if counter >= 100_000_000:
                digits = len(str(counter)) - 5
                score += 5 * min(4, digits - 1) + 10 * max(0, digits - 4)
            elif counter >= 100_000:
                digits = len(str(counter)) - 5
                score += 5 * digits

            # Recomb score
            recomb = extra.get("rarity_upgrades", 0)
            if recomb == 1:
                score += 2

            cultivating_level = extra.get("enchantments", {}).get("cultivating", 0)
            if cultivating_level == 9:
                score += 5
            elif cultivating_level == 10:
                score += 15

            # Farming for Dummies
            ffd = extra.get("farming_for_dummies_count", 0)
            if ffd > 1:
                score += 1
            if ffd == 5:
                score += 1  # Additional bonus

            # Gemstone score
            gems = extra.get("gems", {})
            score += gemstone_score(gems)

            # Track best
            if score > best_score:
                best_score = score
                best_tool_name = tool.get("tag", {}).get("display", {}).get("Name", "Unnamed")

        scored[crop] = (best_tool_name, best_score)

    return scored

def mathematical_hoe_weight(items):
    scored = score_best_mathematical_hoes(items)
    total_score = 0
    breakdown = []

    for crop, (name, score) in scored.items():
        total_score += score
        breakdown.append(f"{crop} Hoe → +{score}")

    return total_score, [", ".join(breakdown)]

# Define function to score dicers and return best per crop
def score_best_dicers(items):
    dicer_scores = {}
    dicer_id_map = {
        "MELON_DICER": "Melon Dicer",
        "PUMPKIN_DICER": "Pumpkin Dicer"
    }

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        name = item.get("tag", {}).get("display", {}).get("Name", "Unnamed")

        match = re.match(r"(MELON_DICER|PUMPKIN_DICER)_(\d)", item_id)
        if not match:
            continue

        base_id, tier_str = match.groups()
        tier = int(tier_str)
        crop_name = dicer_id_map.get(base_id, base_id.title().replace("_", " "))

        # Base score by tier
        if tier == 1:
            score = 1
        elif tier == 2:
            score = 7
        elif tier == 3:
            score = 20
        else:
            score = 0

        # Cultivating bonus
        cultivating_level = extra.get("enchantments", {}).get("cultivating", 0)
        if base_id == "PUMPKIN_DICER":
            if cultivating_level == 9:
                score += 10
            elif cultivating_level == 10:
                score += 20
        else:
            if cultivating_level == 9:
                score += 5
            elif cultivating_level == 10:
                score += 15

        # Rarity upgrade
        if extra.get("rarity_upgrades", 0) == 1:
            score += 2

        # Farming for Dummies
        ffd = extra.get("farming_for_dummies_count", 0)
        if ffd > 1:
            score += 1
        if ffd == 5:
            score += 1  # Additional bonus

        # Hot Potato Book
        hp = extra.get("hot_potato_count", 0)
        if hp == 10:
            score += 1
        elif hp == 15:
            score += 2

        # Art of War
        if extra.get("art_of_war_count", 0) == 1:
            score += 1

        # Gemstones
        gems = extra.get("gems", {})
        score += gemstone_score(gems)

        # Store best per crop
        current_best = dicer_scores.get(crop_name, (None, -1))
        if score > current_best[1]:
            dicer_scores[crop_name] = (name, score)

    return dicer_scores

# Wrapper function to compute total weight and breakdown for dicers
def dicer_weight(items):
    scored = score_best_dicers(items)
    total_score = 0
    breakdown = []

    for crop, (name, score) in scored.items():
        total_score += score
        breakdown.append(f"{crop} → +{score}")

    return total_score, [", ".join(breakdown)]

# Function to score special farming tools: cactus knife, fungi cutter, and cocoa chopper
def score_best_special_farming_tools(items):
    tool_ids = {
        "CACTUS_KNIFE": "Cactus Knife",
        "FUNGI_CUTTER": "Fungi Cutter",
        "COCO_CHOPPER": "Cocoa Chopper"
    }

    tool_scores = {}

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        name = item.get("tag", {}).get("display", {}).get("Name", "Unnamed")

        if item_id not in tool_ids:
            continue

        crop_name = tool_ids[item_id]
        score = 0

        # Cultivating
        cultivating_level = extra.get("enchantments", {}).get("cultivating", 0)
        if cultivating_level == 9:
            score += 5
        elif cultivating_level == 10:
            score += 15

        # Rarity upgrade
        if extra.get("rarity_upgrades", 0) == 1:
            score += 2

        # Farming for Dummies
        ffd = extra.get("farming_for_dummies_count", 0)
        if ffd > 1:
            score += 1
        if ffd == 5:
            score += 1  # Additional bonus

        # Only for COCO_CHOPPER: hot potato book and art of war bonuses
        if item_id == "COCO_CHOPPER":
            hp = extra.get("hot_potato_count", 0)
            if hp == 10:
                score += 1
            elif hp == 15:
                score += 2

            if extra.get("art_of_war_count", 0) == 1:
                score += 1

        # Gemstones
        gems = extra.get("gems", {})
        score += gemstone_score(gems)

        # Only keep best-scoring of each tool
        current_best = tool_scores.get(crop_name, (None, -1))
        if score > current_best[1]:
            tool_scores[crop_name] = (name, score)

    return tool_scores

# Wrap into weight function
def special_farming_tool_weight(items):
    scored = score_best_special_farming_tools(items)
    total_score = 0
    breakdown = []

    for crop, (name, score) in scored.items():
        total_score += score
        breakdown.append(f"{crop} → +{score}")

    return total_score, [", ".join(breakdown)]

# Function to score the best pair of Rancher's Boots
def ranchers_boots_weight(items):
    best_score = 0
    best_name = None

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        name = item.get("tag", {}).get("display", {}).get("Name", "Unnamed")

        if item_id != "RANCHERS_BOOTS":
            continue

        score = 5  # Base score for owning Rancher's Boots

        # Reforge bonus
        if extra.get("modifier", "").lower() == "mossy":
            score += 15

        # Pesterminator enchantment score
        enchants = extra.get("enchantments", {})
        pest_level = enchants.get("pesterminator", 0)
        score += (pest_level - 3) if pest_level > 3 else 0

        # Gemstone score
        gems = extra.get("gems", {})
        score += gemstone_score(gems)

        # Keep highest scoring
        if score > best_score:
            best_score = score
            best_name = name

    if best_score > 0:
        return best_score, [f"Rancher's Boots → +{best_score}"]
    else:
        return 0, []

# Define armor scoring function
def farming_armor_weight(items):
    armor_slots = ["HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS"]
    base_points = {
        "MELON": 3,
        "CROPIE": 7,
        "SQUASH": 15,
        "FERMENTO": 30
    }

    best_by_slot = {}

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        name = item.get("tag", {}).get("display", {}).get("Name", "Unnamed")

        # Match valid farming armor
        match = re.match(r"(MELON|CROPIE|SQUASH|FERMENTO)_(HELMET|CHESTPLATE|LEGGINGS|BOOTS)", item_id)
        if not match:
            continue

        piece_type, slot = match.groups()
        score = base_points.get(piece_type, 0)

        # Rarity upgrade
        if extra.get("rarity_upgrades", 0) == 1:
            score += 2

        # Reforge bonus
        if extra.get("modifier", "").lower() == "mossy":
            score += 15

        # Pesterminator
        enchants = extra.get("enchantments", {})
        pest_level = enchants.get("pesterminator", 0)
        if pest_level > 3:
            score += pest_level - 3

        # Gemstones
        gems = extra.get("gems", {})
        gem_score = gemstone_score(gems)

        # Special cases
        if slot == "BOOTS":
            if piece_type == "FERMENTO":
                gem_score = int(gem_score * 1.2)
            score += gem_score
            if piece_type in {"MELON", "CROPIE", "SQUASH"}:
                score = min(score, 5)
            score = round(score * 0.8)
        else:
            score += gem_score

        # Track best per slot
        if slot not in best_by_slot or score > best_by_slot[slot][1]:
            best_by_slot[slot] = (name, score)

    # Summarize
    total_score = sum(score for _, score in best_by_slot.values())
    breakdown = [f"{slot.title()} → +{score}" for slot, (_, score) in best_by_slot.items()]
    return total_score, [", ".join(breakdown)]

# Updated function with green thumb curve applied if total books exceed threshold
def green_thumb_weight(x):
    return (200 * math.log(x + 200, 1.2) - 5800) / 3

# Updated version: only count the best-scoring version of each equipment piece
def farming_equipment_weight(items):
    equipment_ids = {
        "LOTUS_BELT", "LOTUS_NECKLACE", "LOTUS_BRACELET", "LOTUS_CLOAK",
        "ZORROS_CAPE", "PEST_VEST", "PESTHUNTERS_GLOVES",
        "PESTHUNTERS_BELT", "PESTHUNTERS_NECKLACE", "PESTHUNTERS_CLOAK"
    }

    best_by_id = {}

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")

        if item_id not in equipment_ids:
            continue

        enchants = extra.get("enchantments", {})
        modifier = extra.get("modifier", "").lower()

        # Equipment bonus (only for these two)
        equipment_score = 3 if item_id == "PEST_VEST" else 5 if item_id == "ZORROS_CAPE" else 0

        # Green Thumb calculation
        gt_level = enchants.get("green_thumb", 0)
        gt_books = 2 ** (gt_level - 1) if gt_level else 0
        green_thumb_score = gt_books * 9
        green_thumb_bonus = 6 if gt_level == 5 else 0
        green_thumb_total = green_thumb_score + green_thumb_bonus

        # Reforges
        reforge_score = 5 if modifier == "squeaky" else 6 if modifier == "rooted" else 0

        # Other enchantments
        other_score = 10 if enchants.get("ultimate_the_one", 0) == 5 else 0

        # Total score for this item
        total = equipment_score + green_thumb_total + reforge_score + other_score

        # Keep highest score per equipment ID
        if item_id not in best_by_id or total > best_by_id[item_id][0]:
            best_by_id[item_id] = (total, equipment_score, green_thumb_score, green_thumb_bonus, green_thumb_total, reforge_score, other_score)

    # Summing up best scores per category
    equipment_bonus = sum(v[1] for v in best_by_id.values())
    raw_green_score = sum(v[2] + v[3] for v in best_by_id.values())
    adjusted_green_score = (
        green_thumb_weight(raw_green_score) if raw_green_score > 414 else raw_green_score
    )
    green_thumb_final = int(adjusted_green_score)
    reforge_points = sum(v[5] for v in best_by_id.values())
    other_bonus = sum(v[6] for v in best_by_id.values())

    total_score = int(equipment_bonus + green_thumb_final + reforge_points + other_bonus)
    breakdown = [f"equipment bonus +{equipment_bonus}",
                 f"green thumb bonus +{green_thumb_final}",
                 f"reforges +{reforge_points}",
                 f"other bonuses +{other_bonus}"]

    return total_score, [", ".join(breakdown)]

def farming_weight(profile, uuid, all_pets, items, garden_data):
    farming_weights = []

    farm_score, farm_desc = farming_exp_weight(profile, uuid)
    farming_weights.append([farm_desc, farm_score])

    med_score, med_breakdown = medal_score(profile, uuid)
    farming_weights.append([med_breakdown, med_score])

    pet_score, pet_desc = farming_pet_weight(profile, uuid, all_pets)
    farming_weights.append([pet_desc, pet_score])

    visitor_score, visitor_desc = visitor_weight(garden_data)
    farming_weights.append([visitor_desc, visitor_score])

    upgrade_score, upgrade_desc = crop_upgrade_weight(garden_data)
    farming_weights.append([upgrade_desc, upgrade_score])

    crop_score, crop_breakdown = crop_milestone_weight(garden_data)
    farming_weights.append([crop_breakdown, crop_score])

    hoe_score, hoe_desc = mathematical_hoe_weight(items)
    farming_weights.append([hoe_desc, hoe_score])

    dicer_score, dicer_desc = dicer_weight(items)
    farming_weights.append([dicer_desc, dicer_score])

    tool_score, tool_desc = special_farming_tool_weight(items)
    farming_weights.append([tool_desc, tool_score])

    boots_score, boots_desc = ranchers_boots_weight(items)
    farming_weights.append([boots_desc, boots_score])

    armor_score, armor_desc = farming_armor_weight(items)
    farming_weights.append([armor_desc, armor_score])

    equip_score, equip_desc = farming_equipment_weight(items)
    farming_weights.append([equip_desc, equip_score])

    total = sum(score for _, score in farming_weights)
    breakdown = [entry for entry in farming_weights if entry[1] != 0]

    return total, breakdown
