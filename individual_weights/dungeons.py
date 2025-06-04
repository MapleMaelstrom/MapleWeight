import re
import math
import json
# Define scoring helpers used across wither armor scoring

gem_tier_points = {
    "ROUGH": 1,
    "FLAWED": 2,
    "FINE": 4,
    "FLAWLESS": 6,
    "PERFECT": 11,
}

def score_wither_armor_piece(extra):
    score = 0
    desc = []

    # Master stars
    upgrade_level = extra.get("upgrade_level", 0)
    upgrade_bonus = {6: 5, 7: 5, 8: 20, 9: 30, 10: 40}
    bonus = sum(v for lvl, v in upgrade_bonus.items() if upgrade_level >= lvl)
    score += bonus
    if bonus > 0:
        desc.append(f"+{bonus} from {upgrade_level - 5} Master Stars")

    # Gemstones
    gems = extra.get("gems", {})
    unlocked = gems.get("unlocked_slots", [])
    gem_score = len(unlocked) * 10
    for gslot in unlocked:
        gem_type = gems.get(f"{gslot}_gem")
        tier = gems.get(gslot)
        if tier and gem_type:
            base_score = gem_tier_points.get(str(tier).upper(), 0)
            if gem_type == "JASPER":
                base_score += 4
            elif gem_type == "ONYX":
                base_score += 2
            gem_score += base_score
    score += gem_score
    if gem_score > 0:
        desc.append(f"+{gem_score} from Gemstones")

    # Enchantments
    enchants = extra.get("enchantments", {})
    ench_score = 0
    if enchants.get("protection", 0) == 7:
        ench_score += 10
    if enchants.get("growth", 0) == 7:
        ench_score += 10
    if enchants.get("ultimate_legion"):
        ench_score += enchants["ultimate_legion"] * 5
    if enchants.get("big_brain", 0) == 5:
        ench_score += 20
    if enchants.get("smarty_pants", 0) == 5:
        ench_score += 1
    if enchants.get("hecatomb"):
        ench_score += enchants["hecatomb"]
    if enchants.get("strong_mana"):
        sm = enchants["strong_mana"]
        if sm == 5:
            ench_score += 1
        elif sm == 6:
            ench_score += 2
        elif sm == 7:
            ench_score += 5
        elif sm >= 8:
            ench_score += 10
    if enchants.get("mana_vampire"):
        mv = enchants["mana_vampire"]
        if mv == 5:
            ench_score += 1
        elif mv == 6:
            ench_score += 2
        elif mv == 7:
            ench_score += 5
        elif mv >= 8:
            ench_score += 10
    if enchants.get("transylvanian", 0) == 5:
        ench_score += 1
    score += ench_score
    if ench_score > 0:
        desc.append(f"+{ench_score} from Enchantments")

    # Upgrades
    if extra.get("hot_potato_count", 0) == 15:
        score += 2
        desc.append("+2 from Fuming Potato Books")
    elif extra.get("hot_potato_count", 0) > 10:
        score += 1
        desc.append("+1 from Fuming Potato Books")
    if extra.get("rarity_upgrades", 0) == 1:
        score += 2
        desc.append("+2 from Rarity Upgrade")

    return score, desc

# Score all wither pieces and return the best per slot
def score_dungeon_armors(items):
    slot_best = {}

    for item in items:
        tag = item.get("tag", {})
        extra = tag.get("ExtraAttributes", {})
        item_id = extra.get("id", "")

        # Wither Armor
        wither_match = re.fullmatch(r"(?:\w+_)?WITHER_(HELMET|CHESTPLATE|LEGGINGS|BOOTS)", item_id)
        if wither_match:
            slot = wither_match.group(1)
            score, desc = score_wither_armor_piece(extra)
            name = tag.get("display", {}).get("Name", "Unnamed")
            if slot not in slot_best or score > slot_best[slot][0]:
                slot_best[slot] = (score, name, desc)
            continue

        # Skeleton Master Chestplate (only score if it meets strict conditions)
        if item_id == "SKELETON_MASTER_CHESTPLATE":
            if extra.get("dungeon_skill_req") == "CATACOMBS:36" and extra.get("baseStatBoostPercentage") == 50:
                score, desc = score_wither_armor_piece(extra)
                score += 11
                name = tag.get("display", {}).get("Name", "Unnamed")
                if "SM_CHEST" not in slot_best or score > slot_best["SM_CHEST"][0]:
                    slot_best["SM_CHEST"] = (score, name, desc)

        if item_id == "WITHER_GOGGLES":
            score, desc = score_wither_armor_piece(extra)
            name = tag.get("display", {}).get("Name", "Unnamed")
            if "GOGGLES" not in slot_best or score > slot_best["GOGGLES"][0]:
                slot_best["GOGGLES"] = (score, name, desc)

        # Golden/Diamond Boss Heads
        head_match = re.fullmatch(r"(DIAMOND|GOLD)_(\w+)_HEAD", item_id)
        if head_match:
            tier, boss = head_match.groups()
            slot = f"{boss}_HEAD"

            score, desc = score_wither_armor_piece(extra)
            name = tag.get("display", {}).get("Name", "Unnamed")

            # Add +20 for diamond heads
            if tier == "DIAMOND":
                score += 20

                if boss == "NECRON":
                    score = int(score * 1.25)
                    desc.append("Necron Diamond 1.25x Multiplier")

            if (slot not in slot_best or score > slot_best[slot][0]) and score > 25:
                slot_best[slot] = (score, name, desc)
            continue

    total = sum(score for score, _, _ in slot_best.values())
    breakdown = [
        f"{slot.title()}: {name} → +{score} ({'; '.join(desc)})"
        for slot, (score, name, desc) in slot_best.items()
    ]

    return total, breakdown

# Catacombs formula
def catacombs_weight(cata_exp):
    value = (cata_exp + 20_000_000) / 2_000_000
    log_term = math.log(value, 45)
    return max(0, int(1400 * log_term - 847))


def dungeon_experience_weight(profile, uuid):

    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})

    dungeons = member.get("dungeons", {})

    player_classes = dungeons.get("player_classes", {})

    cata_exp = dungeons.get("dungeon_types", {}).get("catacombs", {}).get("experience", 0)

    class_cap = 569_809_640
    class_total = 0
    class_breakdown = []

    for cls in ["healer", "mage", "berserk", "archer", "tank"]:
        exp = player_classes.get(cls, {}).get("experience", 0)
        progress = min(exp / class_cap, 1.0)
        points = int(progress * 150)
        class_total += points
        class_breakdown.append(f"{int(progress * 100)}% to {cls.title()} 50 → +{points}")

    access_bonus = 100 if cata_exp > 488_640 else 0
    cata_score = catacombs_weight(cata_exp)

    total_score = class_total + access_bonus + cata_score
    breakdown = class_breakdown + [
        f"Floor 7 Access Bonus → +{access_bonus}",
        f"{int(cata_exp):,} Cata EXP → +{cata_score}"
    ]

    return total_score, breakdown

def collection_bonus_weight(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})
    tutorial_flags = member.get("objectives", {}).get("tutorial", [])

    total = 0
    breakdown = []

    for flag in tutorial_flags:
        if not flag.startswith("boss_collection_claimed_"):
            continue

        parts = flag.split("_")
        if len(parts) < 5:
            continue  # malformed entry

        boss = parts[3]
        tier = parts[4].upper()  # "gold" or "diamond"

        if tier == "GOLD":
            base_points = 20
        elif tier == "DIAMOND":
            base_points = 80
        else:
            continue

        if boss == "necron":
            base_points *= 2
            label = f"{tier.title()} {boss.title()} Head (Double Bonus)"
        else:
            label = f"{tier.title()} {boss.title()} Head"

        total += base_points
        breakdown.append(f"{label} → +{base_points}")

    return total, breakdown

def general_dungeon_items(items):
    total = 0
    breakdown = []

    # Mapping of item sets to labels and scores
    target_items = {
        frozenset(["SPRING_BOOTS"]): ("Spring Boots", 25),
        frozenset(["SPIRIT_MASK", "STARRED_SPIRIT_MASK"]): ("Spirit Mask", 25),
        frozenset(["INFINITE_SPIRIT_LEAP"]): ("Infinite Spirit Leap", 15),
        frozenset(["INFINITE_SUPERBOOM_TNT"]): ("Infinite Superboom TNT", 20),
        frozenset(["ICE_SPRAY_WAND", "STARRED_ICE_SPRAY_WAND"]): ("Ice Spray Wand", 10),
        frozenset(["GYROKINETIC_WAND"]): ("Gyrokinetic Wand", 5),
        frozenset(["BONZO_MASK", "STARRED_BONZO_MASK"]): ("Bonzo Mask", 2),
        frozenset(["DEATH_BOW"]): ("Death Bow", 5),
    }

    found_keys = set()
    best_last_breath_score = 0
    best_last_breath_level = 0

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")

        # Special-case: Last Breath (evaluate best one only)
        if item_id == "LAST_BREATH":
            enchants = extra.get("enchantments", {})
            level = enchants.get("ultimate_reiterate", 0)
            score = 10 if level >= 1 else 5
            if score > best_last_breath_score:
                best_last_breath_score = score
                best_last_breath_level = level
            continue

        # Standard target items
        for key in list(target_items.keys() - found_keys):
            if item_id in key:
                label, score = target_items[key]
                breakdown.append(f"{label} → +{score}")
                total += score
                found_keys.add(key)
                break

    # Add best Last Breath if one was found
    if best_last_breath_score:
        breakdown.append(f"Last Breath (Duplex {int(best_last_breath_level)}) → +{best_last_breath_score}")
        total += best_last_breath_score

    return total, breakdown


def dungeon_weight(profile, uuid, all_pets, items):
    weights = []

    armor_score, armor_desc = score_dungeon_armors(items)
    weights.append([armor_desc, armor_score])

    exp_score, exp_desc = dungeon_experience_weight(profile, uuid)
    weights.append([exp_desc, exp_score])

    collection_score, collection_desc = collection_bonus_weight(profile, uuid)
    weights.append([collection_desc, collection_score])

    general_score, general_desc = general_dungeon_items(items)
    weights.append([general_desc, general_score])

    total = sum(score for _, score in weights)
    breakdown = [desc for desc, _ in weights]

    return total, breakdown
