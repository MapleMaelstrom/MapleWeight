import math
from ..individual_weights.mw_utils.Crimson_Calc import score_crimson_set

def r(x):  # Rev
    return int((2/3) * (1100 * math.log(((x + 300000) / 30000), 100) - 400))

def s(x):  # Spider
    return r(x) / 4

def w(x):  # Wolf
    return r(x) * 1.5

def e(x):  # Enderman
    base = r(min(x, 1_000_000)) * 2.25
    if x <= 1_000_000:
        return base
    else:
        extra = r(x) - r(1_000_000)
        return base + extra * 1.125  # Half of 2.25

def b(x): # Blaze
    base = r(min(x, 1_000_000)) * 3
    if x <= 1_000_000:
        return base
    else:
        extra = r(x) - r(1_000_000)
        return base + extra * 3 * 0.75

def score_slayer_weapon(item, slayer_id):
    extra = item.get("tag", {}).get("ExtraAttributes", {})
    enchants = extra.get("enchantments", {})
    if not enchants:
        return 0, "No enchantments"

    score = 0
    breakdown = []

    # Universal Ultimate Enchants
    ultimate_scores = {
        "ultimate_chimera": (20, "Chimera"),
        "ultimate_soul_eater": (10, "Soul Eater"),
        "ultimate_swarm": (10, "Swarm"),
        "ultimate_combo": (2, "Combo"),
        "ultimate_wise": (3, "Ultimate Wise"),
        "ultimate_inferno": (15, "Inferno")
    }

    for key, (per_level, label) in ultimate_scores.items():
        if key in enchants:
            lvl = enchants[key]
            val = lvl * per_level
            score += val
            breakdown.append(f"{label} {int(lvl)} (+{val})")

    # Universal Regular Enchants
    flat_enchants = {
        "sharpness": (7, 25),
        "giant_killer": (7, 25),
        "scavenger": (6, 10),
        "venomous": (6, 15),
        "triple_strike": (5, 20),
        "first_strike": (5, 20),
        "thunderlord": (7, 5),
        "champion": (10, 25),
        "syphon": (5, 15),
        "prosecute": (6, 15),
        "execute": (6, 15),
        "critical": (7, 15),
        "divine_gift": (3, 10),  # Per tier
    }

    for ench, (max_tier, value) in flat_enchants.items():
        lvl = enchants.get(ench, 0)
        if lvl >= max_tier:
            points = value if ench != "divine_gift" else value * lvl
            score += points
            breakdown.append(f"{ench.replace('_', ' ').title()} {int(lvl)} (+{points})")

    # Slayer-Specific Enchants
    slayer_enchants = {
        0: [("smite", 7, 25)],
        1: [("bane_of_arthropods", 7, 25)],
        3: [("ender_slayer", 7, 50)],
        4: [("smoldering", 1, 10)],  # per tier
    }

    for ench, max_tier, points in slayer_enchants.get(slayer_id, []):
        lvl = enchants.get(ench, 0)
        if lvl >= max_tier:
            val = points * lvl if ench == "smoldering" else points
            score += val
            breakdown.append(f"{ench.replace('_', ' ').title()} {int(lvl)} (+{val})")

    return score, ", ".join(breakdown) or "No qualifying enchants"

# Define tier mapping for gemstones
gem_tiers = {
    "ROUGH": 1,
    "FLAWED": 2,
    "FINE": 3,
    "FLAWLESS": 4,
    "PERFECT": 5
}

# Define gemstone bonuses
gem_bonus = {
    "JASPER": 2,
    "ONYX": 1
}

def gemstone_score(gems):
    score = 0
    unlocked = gems.get("unlocked_slots", [])
    score += 5 * len(unlocked)
    for slot in unlocked:
        gem_type = gems.get(slot + "_gem", None)
        if not gem_type:
            gem_type = slot.split("_")[0]  # fallback, e.g., "JASPER_0"
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

def enhancement_score(extra):
    score = 0
    if extra.get("hot_potato_count", 0) > 10:
        score += extra["hot_potato_count"] - 10
    if extra.get("upgrade_level", 0) == 5:
        score += 1
    if extra.get("art_of_war_count", 0) == 1:
        score += 1
    if extra.get("rarity_upgrades", 0) == 1:
        score += 1
    return score

def slayer_weapon_score(items, slayer_id, base_weapon_score_maps, slayer_name="Slayer"):
    if isinstance(base_weapon_score_maps, dict):
        base_weapon_score_maps = [base_weapon_score_maps]

    total_score = 0
    combined_breakdowns = []

    for base_weapon_scores in base_weapon_score_maps:
        best_score = 0
        best_breakdown = ""

        for item in items:
            extra = item.get("tag", {}).get("ExtraAttributes", {})
            item_id = extra.get("id", "")
            base_score = base_weapon_scores.get(item_id)
            if base_score is None:
                continue

            enchant_score, ench_breakdown = score_slayer_weapon(item, slayer_id)
            gem_score = gemstone_score(extra.get("gems", {}))
            book_score = enhancement_score(extra)

            total = base_score + enchant_score + gem_score + book_score
            breakdown = (
                f"{item_id}: Base {base_score}, Enchants {enchant_score}, "
                f"Gems {gem_score}, Upgrades {book_score} → Total {total}. "
                f"Details: {ench_breakdown}"
            )

            if total > best_score:
                best_score = total
                best_breakdown = breakdown

        total_score += best_score
        if best_breakdown:
            combined_breakdowns.append(best_breakdown)

    return total_score, " + ".join(combined_breakdowns) if combined_breakdowns else f"No valid {slayer_name.lower()} slayer weapons found"

def revenant_points(profile, uuid, pets, items):
    slayer = profile["members"][uuid].get("slayer", {}).get("slayer_bosses", {})
    zombie_data = slayer.get("zombie", {})
    xp = zombie_data.get("xp", 0)
    is_rev8 = xp >= 400_000

    # Base values for weapons
    zombie_weapon_base_scores = {
        "AXE_OF_THE_SHREDDED": 40,
        "REAPER_SWORD": 10,
        "REVENANT_SWORD": 5
    }

    weapon_score, weapon_breakdown = slayer_weapon_score(items, slayer_id=0, base_weapon_score_maps=zombie_weapon_base_scores, slayer_name="Zombie")

    score = 0
    desc = [f"{xp:,} Total Revenant Slayer Experience"]

    cutoff = 400_000
    cutoff_weight = r(cutoff)
    if xp >= cutoff:
        xp_weight = r(xp)
    else:
        xp_weight = (cutoff_weight / cutoff) * xp
    score += int(xp_weight)

    if is_rev8:
        score += 200
        desc.append("Revenant Horror 8")

    ghoul_score = 0
    for pet in pets:
        if pet["type"] == "GHOUL" and pet["tier"] in {"EPIC", "LEGENDARY"}:
            exp = min(max(pet.get("exp", 0), 0), 25353230)
            ghoul_score = max(ghoul_score, 1 + 9 * (exp / 25353230))
    ghoul_score = round(ghoul_score)
    if ghoul_score > 0:
        score += ghoul_score
        progress = round(100 * (exp / 25353230))
        desc.append(f"Ghoul Pet – {progress}% to Lvl 100 {pet['tier']}")

    score += weapon_score  # Adjust based on your system
    desc.append(f"Weapon Score: {weapon_score} ({weapon_breakdown})")

    return score, [" + ".join(desc), score]


def auto_slayer_points(profile, uuid):
    slayer = profile["members"][uuid].get("slayer", {}).get("slayer_bosses", {})
    return 100 if all(slayer.get(b, {}).get("xp", 0) >= 20000 for b in ["zombie", "spider", "wolf"]) else 0


def spider_points(profile, uuid, pets, items):
    slayer = profile["members"][uuid].get("slayer", {}).get("slayer_bosses", {})
    spider_data = slayer.get("spider", {})
    xp = spider_data.get("xp", 0)

    score = 0
    desc = [f"{xp:,} Total Spider Slayer Experience"]

    cutoff = 400_000
    cutoff_weight = s(cutoff)
    if xp < cutoff:
        xp_weight = (cutoff_weight / cutoff) * xp
    else:
        xp_weight = s(xp)

    score += int(xp_weight)

    pet_score = 0
    for pet in pets:
        if pet["type"] == "TARANTULA" and pet["tier"] in {"LEGENDARY", "MYTHIC"}:
            exp = min(max(pet.get("exp", 0), 0), 25353230)
            progress = round(100 * (exp / 25353230))
            pet_score = max(pet_score, 1 + 9 * (exp / 25353230))
            pet_desc = f"Tarantula Pet – {progress}% to Lvl 100 {pet['tier']}"
    pet_score = round(pet_score)
    if pet_score > 0:
        score += round(pet_score)
        desc.append(pet_desc)

    spider_weapon_base_scores = {
        "SCORPION_FOIL": 15,
        "RECLUSE_FANG": 5
    }
    spider_score, spider_breakdown = slayer_weapon_score(
        items,
        slayer_id=1,
        base_weapon_score_maps=spider_weapon_base_scores,
        slayer_name="Spider"
    )
    score += spider_score  # Adjust based on your system
    desc.append(f"Weapon Score: {spider_score} ({spider_breakdown})")
    return score, [" + ".join(desc), score]


def sven_points(profile, uuid, pets, items):
    slayer = profile["members"][uuid].get("slayer", {}).get("slayer_bosses", {})
    wolf_data = slayer.get("wolf", {})
    xp = wolf_data.get("xp", 0)

    score = 0
    desc = [f"{xp:,} Total Wolf Slayer Experience"]

    cutoff = 400_000
    cutoff_weight = w(cutoff)
    if xp < cutoff:
        xp_weight = (cutoff_weight / cutoff) * xp
    else:
        xp_weight = w(xp)

    score += int(xp_weight)

    if xp >= 100_000:
        score += 100
        desc.append("Sven 7")
    if xp >= 250:
        score += 10
        desc.append("Sven 3")

    hound_score = 0
    for pet in pets:
        if pet["type"] == "HOUND" and pet["tier"] == "LEGENDARY":
            exp = min(max(pet.get("exp", 0), 0), 25353230)
            progress = round(100 * (exp / 25353230))
            hound_score = max(hound_score, 1 + 14 * (exp / 25353230))
            hound_desc = f"Hound Pet – {progress}% to Lvl 100 {pet['tier']}"
    hound_score = round(hound_score)
    if hound_score > 0:
        score += round(hound_score)
        desc.append(hound_desc)

    wolf_weapon_base_scores = {
        "POOCH_SWORD": 15,
        "SHAMAN_SWORD": 5
    }

    wolf_score, wolf_breakdown = slayer_weapon_score(
        items,
        slayer_id=2,
        base_weapon_score_maps=wolf_weapon_base_scores,
        slayer_name="Wolf"
    )
    score += wolf_score  # Adjust based on your system
    desc.append(f"Weapon Score: {wolf_score} ({wolf_breakdown})")

    return score, [" + ".join(desc), score]


def enderman_points(profile, uuid, pets, items):
    slayer = profile["members"][uuid].get("slayer", {}).get("slayer_bosses", {})
    ender_data = slayer.get("enderman", {})
    xp = ender_data.get("xp", 0)

    score = 0
    desc = [f"{xp:,} Total Enderman Slayer Experience"]

    cutoff = 400_000
    cutoff_weight = e(cutoff)
    if xp < cutoff:
        xp_weight = (cutoff_weight / cutoff) * xp
    else:
        xp_weight = e(xp)
    score += int(xp_weight)

    if xp >= 5_000:
        score += 30
        desc.append("Enderman Slayer 5")
    if xp >= 20_000:
        score += 20
        desc.append("Enderman Slayer 6")
    if xp >= 100_000:
        score += 100
        desc.append("Enderman Slayer 7")
    if xp >= 400_000:
        score += 50
        desc.append("Enderman Slayer 8")
    if xp >= 1_000_000:
        score += 100
        desc.append("Enderman Slayer 9")

    pet_score = 0
    for pet in pets:
        if pet["type"] == "ENDERMAN" and pet["tier"] == "MYTHIC":
            exp = min(max(pet.get("exp", 0), 0), 25353230)
            progress = round(100 * (exp / 25353230))
            pet_score = max(pet_score, 1 + 24 * (exp / 25353230))
            pet_desc = f"Mythic Enderman Pet – {progress}% to Lvl 100 {pet['tier']}"
    pet_score = round(pet_score)
    if pet_score > 0:
        score += round(pet_score)
        desc.append(pet_desc)

    enderman_weapon_base_scores = {
        "ATOMSPLIT_KATANA": 50,
        "VORPAL_KATANA": 15,
        "VOIDEDGE_KATANA": 5,
        "VOIDWALKER_KATANA": 2
    }

    enderman_score, enderman_breakdown = slayer_weapon_score(
        items,
        slayer_id=3,
        base_weapon_score_maps=enderman_weapon_base_scores,
        slayer_name="Enderman"
    )

    score += enderman_score  # Adjust based on your system
    desc.append(f"Weapon Score: {enderman_score} ({enderman_breakdown})")

    # Check for Ender Artifact or Relic
    has_artifact = False
    has_relic = False

    for item in items:
        item_id = item.get("tag", {}).get("ExtraAttributes", {}).get("id", "")
        if item_id == "ENDER_RELIC":
            has_relic = True
            break
        elif item_id == "ENDER_ARTIFACT":
            has_artifact = True

    if has_relic:
        score += 50
        desc.append("Ender Relic (+50)")
    elif has_artifact:
        score += 40
        desc.append("Ender Artifact (+40)")

    return score, [" + ".join(desc), score]

def blaze_points(profile, uuid, pets, items):
    slayer = profile["members"][uuid].get("slayer", {}).get("slayer_bosses", {})
    blaze_data = slayer.get("blaze", {})
    xp = blaze_data.get("xp", 0)

    score = 0
    desc = [f"{xp:,} Total Blaze Slayer Experience"]

    # Slayer XP weight
    cutoff = 400_000
    cutoff_weight = b(cutoff)
    if xp < cutoff:
        xp_weight = (cutoff_weight / cutoff) * xp
    else:
        xp_weight = b(xp)

    score += int(xp_weight)

    if xp >= 100_000:
        score += 100
        desc.append("Blaze Slayer 7")

    # Wisp variants
    wisp_scores = {
        "DROPLET_WISP": 5,
        "FROST_WISP": 10,
        "GLACIAL_WISP": 25,
        "SUBZERO_WISP": 50
    }

    best_score = 0
    best_name = None
    for pet in pets:
        pet_type = pet.get("type", "")
        if pet_type in wisp_scores:
            if wisp_scores[pet_type] > best_score:
                best_score = wisp_scores[pet_type]
                best_name = pet_type.replace("_", " ").title()

    if best_score > 0:
        score += best_score
        desc.append(f"{best_name} Pet (+{best_score})")

    deathripper_line_base_scores = {
        "HEARTMAW_DAGGER": 50,  # Deathripper Dagger
        "BURSTMAW_DAGGER": 20,  # Mawdredge Dagger
        "MAWDUST_DAGGER": 10    # Twilight Dagger
    }
    pyrochaos_line_base_scores = {
        "HEARTFIRE_DAGGER": 50,  # Pyrochaos Dagger
        "BURSTFIRE_DAGGER": 20,  # Kindlebane Dagger
        "FIREDUST_DAGGER": 10    # Firedust Dagger
    }

    blaze_weapon_score, blaze_breakdown = slayer_weapon_score(
        items,
        slayer_id=4,
        base_weapon_score_maps=[deathripper_line_base_scores, pyrochaos_line_base_scores],
        slayer_name="Blaze"
    )
    score += blaze_weapon_score  # Adjust based on your system
    desc.append(f"Weapon Score: {blaze_weapon_score} ({blaze_breakdown})")

    # Blaze-specific accessory bonuses
    has_nether_artifact = False
    has_burststopper_artifact = False
    has_burststopper_talisman = False

    for item in items:
        item_id = item.get("tag", {}).get("ExtraAttributes", {}).get("id", "")
        if item_id == "NETHER_ARTIFACT":
            has_nether_artifact = True
        elif item_id == "BURSTSTOPPER_ARTIFACT":
            has_burststopper_artifact = True
        elif item_id == "BURSTSTOPPER_TALISMAN":
            has_burststopper_talisman = True

    if has_nether_artifact:
        score += 10
        desc.append("Nether Artifact (+10)")

    if has_burststopper_artifact:
        score += 10
        desc.append("Burststopper Artifact (+10)")
    elif has_burststopper_talisman:
        score += 5
        desc.append("Burststopper Talisman (+5)")

    return score, [" + ".join(desc), score]

def slayer_weight(profile, uuid, all_pets, items):
    slayer_weights = []

    auto_score = auto_slayer_points(profile, uuid)
    if auto_score > 0:
        slayer_weights.append(["Auto Slayer Unlock", auto_score])

    rev_score, rev_desc = revenant_points(profile, uuid, all_pets, items)
    slayer_weights.append(rev_desc)

    spider_score, spider_desc = spider_points(profile, uuid, all_pets, items)
    slayer_weights.append(spider_desc)

    sven_score, sven_desc = sven_points(profile, uuid, all_pets, items)
    slayer_weights.append(sven_desc)

    end_score, end_desc = enderman_points(profile, uuid, all_pets, items)
    slayer_weights.append(end_desc)

    blaze_score, blaze_desc = blaze_points(profile, uuid, all_pets, items)
    slayer_weights.append(blaze_desc)

    crimson_score, crimson_desc = score_crimson_set(items)
    if crimson_score > 0:
        slayer_weights.append([f"Crimson Armor Score: {crimson_score}", crimson_score])
        for line in crimson_desc:
            slayer_weights.append([f"↳ {line}", 0])

        total = sum(score for _, score in slayer_weights)
        return total, [entry for entry in slayer_weights if entry[1] != 0], crimson_desc

    total = sum(score for _, score in slayer_weights)
    return total, [entry for entry in slayer_weights if entry[1] != 0], None


