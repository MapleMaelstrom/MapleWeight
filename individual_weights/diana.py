import math

def daedalus_axe_weight(items):
    max_score = 0
    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        if item_id not in {"DAEDALUS_AXE", "STARRED_DAEDALUS_AXE"}:
            continue

        score = 0
        enchants = extra.get("enchantments", {})
        if enchants.get("looting", 0) == 5:
            score += 50

        chimera_level = enchants.get("ultimate_chimera", 0)
        if 1 <= chimera_level <= 5:
            score += {1: 20, 2: 40, 3: 80, 4: 160, 5: 320}[chimera_level]

        div_gift = enchants.get("divine_gift", 0)
        if 1 <= div_gift <= 3:
            score += 10

        if item_id == "DAEDALUS_AXE":
            score += 10
        elif item_id == "STARRED_DAEDALUS_AXE":
            score += 40

        max_score = max(max_score, score)
    return max_score

def mythos_kill_weight(x):
    return max(0, int(293 * math.log(x + 2000, 23) - 711))

def bestiary_weight(profile, uuid):
    kills_data = profile.get("members", {}).get(uuid, {}).get("bestiary", {}).get("kills", {})
    mythos_kills = profile.get("members", {}).get(uuid, {}).get("player_stats", {}).get("mythos", {}).get("kills", 0)

    groups = [
        (["minos_inquisitor_750"], "Inquisitor", 500),
        (["minotaur_45", "minotaur_210", "minotaur_120"], "Minotaur", 3000),
        (["minos_hunter_15", "minos_hunter_125", "minos_hunter_60"], "Hunter", 1000),
        (["gaia_construct_140", "gaia_construct_260"], "Gaia Construct", 3000),
        (["minos_champion_310", "minos_champion_175"], "Champion", 1000),
        (["siamese_lynx_155", "siamese_lynx_25", "siamese_lynx_85"], "Siamese Lynx", 3000),
    ]

    total_weight = 0
    desc_parts = []

    for keys, label, max_kills in groups:
        total_kills = sum(kills_data.get(k, 0) for k in keys)
        percent = min(total_kills / max_kills, 1.0)
        weight = percent * 50
        if percent == 1.0:
            weight += 25
        total_weight += weight
        desc_parts.append(f"{label}: {int(percent * 100)}%")

    # Add mythos contribution
    mythos_score = mythos_kill_weight(mythos_kills)
    total_weight += mythos_score
    desc_parts.append(f"{int(mythos_kills)} Total Kills: +{mythos_score}")

    return round(total_weight), ", ".join(desc_parts)

def clover_helmet_weight(items):
    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        if extra.get("id") == "CLOVER_HELMET":
            return 500, "Clover Helmet"
    return 0, ""

def magic_find_armor_weight(items):
    scored_pieces = []

    magic_find_ids = {
        "SORROW_HELMET", "SORROW_CHESTPLATE", "SORROW_LEGGINGS", "SORROW_BOOTS", "CLOVER_HELMET",
        "CROWN_OF_AVARICE", "CRIMSON_HELMET", "CRIMSON_CHESTPLATE", "CRIMSON_LEGGINGS", "CRIMSON_BOOTS",
        "HOT_CRIMSON_HELMET", "HOT_CRIMSON_CHESTPLATE", "HOT_CRIMSON_LEGGINGS", "HOT_CRIMSON_BOOTS",
        "BURNING_CRIMSON_HELMET", "BURNING_CRIMSON_CHESTPLATE", "BURNING_CRIMSON_LEGGINGS", "BURNING_CRIMSON_BOOTS",
        "FIERY_CRIMSON_HELMET", "FIERY_CRIMSON_CHESTPLATE", "FIERY_CRIMSON_LEGGINGS", "FIERY_CRIMSON_BOOTS",
        "INFERNAL_CRIMSON_HELMET", "INFERNAL_CRIMSON_CHESTPLATE", "INFERNAL_CRIMSON_LEGGINGS", "INFERNAL_CRIMSON_BOOTS"
    }

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        if item_id not in magic_find_ids:
            continue
        if extra.get("modifier", "").lower() != "renowned":
            continue

        piece_score = 10
        enchants = extra.get("enchantments", {})
        desc = f"{item_id}: +10"

        legion_level = enchants.get("ultimate_legion", 0)
        if legion_level > 0:
            bonus = 3 * legion_level
            if legion_level == 5:
                bonus += 5
            piece_score += bonus
            desc += f", Legion {int(legion_level)} (+{bonus})"

        bobbin_level = enchants.get("ultimate_bobbin_time", 0)
        if bobbin_level > 0:
            bonus = 5 * bobbin_level
            piece_score += bonus
            desc += f", Bobbin Time {int(bobbin_level)} (+{bonus})"

        scored_pieces.append((piece_score, desc))

    # Sort by score, take top 4
    scored_pieces.sort(reverse=True, key=lambda x: x[0])
    top_pieces = scored_pieces[:4]

    total_score = sum(score for score, _ in top_pieces)
    breakdown = "; ".join(desc for _, desc in top_pieces)

    return total_score, breakdown

def diana_weight(profile, uuid, items):
    weights = []

    axe_score = daedalus_axe_weight(items)
    weights.append(["Daedalus Axe", axe_score])

    bestiary_score, bestiary_desc = bestiary_weight(profile, uuid)
    weights.append([bestiary_desc, bestiary_score])

    mf_score, mf_desc = magic_find_armor_weight(items)
    if mf_score > 0:
        weights.append([mf_desc, mf_score])

    clover_score, clover_desc = clover_helmet_weight(items)
    if clover_score > 0:
        weights.append([clover_desc, clover_score])

    total = sum(score for _, score in weights)
    breakdown = [f"{desc}: {score}" for desc, score in weights if score > 0]

    return total, breakdown
