import math

def rod_weight(items):
    water_rods = {
        "CHALLENGE_ROD": 5,
        "CHAMP_ROD": 10,
        "LEGEND_ROD": 20,
        "ROD_OF_THE_SEA": 40
    }
    trophy_rods = {
        "MAGMA_ROD": 5,
        "INFERNO_ROD": 20,
        "HELLFIRE_ROD": 80
    }

    def bonus_from_attr_level(level):
        if level <= 2:
            return level - 1
        return 2 ** (level - 2) if level < 10 else 250

    def score_rod(item):
        ea = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = ea.get("id", "")
        base = 0

        # Determine base rod type and attribute
        attr_data = ea.get("attributes", {})
        trophy_hunter = attr_data.get("trophy_hunter", 0)

        # Water rod
        if item_id in water_rods:
            base += water_rods[item_id]
        # Trophy rod
        elif item_id in trophy_rods:
            if trophy_hunter > 0:
                base += trophy_rods[item_id]
                base += bonus_from_attr_level(trophy_hunter)
            else:
                base += trophy_rods[item_id]
                base += bonus_from_attr_level(0)

        # Enchantments
        enchants = ea.get("enchantments", {})
        piscary = enchants.get("piscary", 0)
        if piscary == 6:
            base += 5
        elif piscary == 7:
            base += 10
        base += 5 * enchants.get("ultimate_flash", 0)
        base += 5 * enchants.get("quick_bite", 0)

        # Upgrade level
        upgrade_level = ea.get("upgrade_level", 0)
        if upgrade_level == 8:
            base += 5
        elif upgrade_level == 9:
            base += 20
        elif upgrade_level == 10:
            base += 50

        # Components
        components = ea.get("line", {}), ea.get("sinker", {}), ea.get("hook", {})
        for comp in components:
            if comp.get("part") == "titan_line":
                base += 50
            elif comp.get("part") == "hotspot_sinker":
                base += 5
            elif comp.get("part") == "hotspot_hook":
                base += 5

        # Gemstones
        gem_map = {
            "ROUGH": 1,
            "FLAWED": 1,
            "FINE": 2,
            "FLAWLESS": 4,
            "PERFECT": 7
        }
        gems = ea.get("gems", {})
        for gem_data in gems.values():
            if isinstance(gem_data, dict):
                base += gem_map.get(gem_data.get("quality", ""), 0)

        base += len(gems)  # 1 point per gemstone slot unlocked

        return base

    best_water = 0
    best_trophy = 0
    best_lava = 0

    for item in items:
        ea = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = ea.get("id", "")
        if item_id in water_rods:
            best_water = max(best_water, score_rod(item))
        elif item_id in trophy_rods:
            if ea.get("attributes", {}).get("trophy_hunter", 0) > 0:
                best_trophy = max(best_trophy, score_rod(item))
            else:
                best_lava = max(best_lava, score_rod(item))

    total = best_water + best_trophy + best_lava
    desc = f"Fishing Rods: {total} (water={best_water}, trophy={best_trophy}, lava={best_lava})"
    return total, desc

def trophy_fish_weight(profile, uuid):
    trophy = profile["members"][uuid].get("trophy_fish", {})
    bronze = set()
    diamond_bonus = {"vanille", "slugfish", "skeleton_fish", "moldfin", "obfuscated_fish_3"}
    diamond_points = 0
    base_diamond = base_gold = base_silver = base_bronze = 0
    fish_names = set()

    for key in trophy:
        if key in {"last_caught", "rewards", "total_caught"}:
            continue
        name = key.rsplit("_", 1)[0] if "_" in key and key.rsplit("_", 1)[1] in {"bronze", "silver", "gold", "diamond"} else key
        fish_names.add(name)

    if all((f + "_gold" in trophy or f + "_diamond" in trophy or f + "_silver" in trophy or f + "_bronze" in trophy) for f in fish_names):
        base_bronze = 25
    if all((f + "_gold" in trophy or f + "_diamond" in trophy or f + "_silver" in trophy) for f in fish_names):
        base_silver = 75
    if all((f + "_gold" in trophy or f + "_diamond" in trophy) for f in fish_names):
        base_gold = 150
    if all(f + "_diamond" in trophy for f in fish_names):
        base_diamond = 500

    for name in diamond_bonus:
        count = trophy.get(name + "_diamond", 0)
        for i in range(1, count + 1):
            bonus = max(0, 10 - (i - 1) // 5)
            diamond_points += bonus

    if len(fish_names) != 18:
        return diamond_points, f"Trophy Fish: {diamond_points}"

    total = base_gold + base_diamond + diamond_points + base_silver + base_bronze
    desc = f"Trophy Fish: {total} (Bronze Hunter: +{base_bronze}, Silver Gunter: +{base_silver}, Gold Hunter: +{base_gold}, Diamond Hunter: +{base_diamond}, Bonus Fish: +{diamond_points})"
    return total, desc

def best_full_set(items):
    set_scores = {
        "MAGMA_LORD": 50,
        "THUNDER": 30,
        "SHARK_SCALE": 10,
        "DIVER": 7,
        "SPONGE": 5,
        "SALMON": 3
    }
    lava_sc_lookup = {
        "TAURUS_HELMET": "helmet",
        "FLAMING_CHESTPLATE": "chestplate",
        "MOOGMA_LEGGINGS": "leggings",
        "SLUG_BOOTS": "boots"
    }
    piece_slots = {"helmet", "chestplate", "leggings", "boots"}

    from collections import defaultdict
    set_coverage = defaultdict(set)

    for item in items:
        ea = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = ea.get("id", "")

        slot = None
        for suf in ["_HELMET", "_CHESTPLATE", "_LEGGINGS", "_BOOTS"]:
            if item_id.endswith(suf):
                slot = suf.lower().strip("_")
                break
        if not slot and item_id in lava_sc_lookup:
            slot = lava_sc_lookup[item_id]
        if not slot:
            continue

        set_name = "lava_sc" if item_id in lava_sc_lookup else "_".join(item_id.split("_")[:-1])
        set_coverage[set_name].add(slot)

    full_sets = [s for s in set_coverage if set_coverage[s] == piece_slots]
    if not full_sets:
        return None
    best = max(full_sets, key=lambda s: set_scores.get(s, 0) if s != "lava_sc" else 20)
    return best

def attr_weight(attrs, set_name):
    relevant_keys = {"blazing_fortune", "magic_find", "fishing_experience"}
    present_keys = frozenset(attrs.keys())

    base = 0
    if present_keys == frozenset(["blazing_fortune", "magic_find"]):
        base = 100 if set_name == "MAGMA_LORD" else 50 if set_name == "THUNDER" else 10 if set_name == "lava_sc" else 0
    elif present_keys == frozenset(["blazing_fortune", "fishing_experience"]):
        base = 75 if set_name == "MAGMA_LORD" else 45 if set_name == "THUNDER" else 5 if set_name == "lava_sc" else 0
    elif present_keys == frozenset(["magic_find", "fishing_experience"]):
        base = 20 if set_name in {"MAGMA_LORD", "THUNDER"} else 1 if set_name == "lava_sc" else 0
    else:
        return 0

    def tier_weight(tier):
        if tier <= 2:
            return tier - 1
        return 250 if tier >= 10 else 2 ** (tier - 2)

    tier_sum = sum(tier_weight(attrs.get(key, 0)) for key in relevant_keys if key in attrs)

    mult = 1
    if set_name == "lava_sc":
        mult = 0.25
    elif set_name == "THUNDER":
        mult = 0.75

    return int((base + tier_sum) * mult)

def best_armor_pieces(items):
    lava_sc_lookup = {
        "TAURUS_HELMET": "helmet",
        "FLAMING_CHESTPLATE": "chestplate",
        "MOOGMA_LEGGINGS": "leggings",
        "SLUG_BOOTS": "boots"
    }
    piece_slots = ["helmet", "chestplate", "leggings", "boots"]
    gemstones = {
        "ROUGH": 1,
        "FLAWED": 1,
        "FINE": 2,
        "FLAWLESS": 4,
        "PERFECT": 7
    }
    reforges = {"festive", "renowned", "submerged"}
    best_pieces = {}
    magma_sets = {"bf_fe": [], "bf_mf": []}

    for item in items:
        ea = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = ea.get("id", "")
        ench = ea.get("enchantments", {})
        attrs = ea.get("attributes", {})
        gems = ea.get("gems", {})
        reforge = ea.get("modifier", "")

        slot = None
        score = 0
        desc = []
        tiki = False
        for suf in ["_HELMET", "_CHESTPLATE", "_LEGGINGS", "_BOOTS"]:
            if item_id.endswith(suf):
                slot = suf.lower().strip("_")
                break
        if not slot and item_id in lava_sc_lookup:
            slot = lava_sc_lookup[item_id]
        if not slot and item_id == "TIKI_MASK":
            score = 50
            slot = "helmet"
            tiki = True
        if not slot:
            continue

        set_name = "lava_sc" if item_id in lava_sc_lookup else "_".join(item_id.split("_")[:-1])

        if reforge in reforges:
            score += 5
            desc.append("Reforge +5")

        if (u := ench.get("ultimate_bobbin_time", 0)):
            score += 5 * u
            desc.append(f"Bobbin Time +{5 * u}")

        gscore = 0
        for gem in gems.values():
            if isinstance(gem, dict):
                quality = gem.get("quality", "")
                gval = gemstones.get(quality, 0)
                gscore += gval if gem.get("type") == "AQUAMARINE" else gval / 2
        gscore += len(gems)
        if gscore:
            score += gscore
            desc.append(f"Gemstones +{int(gscore)}")

        filtered_attrs = {k: v for k, v in attrs.items() if k in {"magic_find", "blazing_fortune", "fishing_experience"}}
        if len(filtered_attrs) == 2:
            abonus = attr_weight(filtered_attrs, set_name)
            if abonus:
                score += abonus
                desc.append(f"Attributes +{abonus}")

            if set_name == "MAGMA_LORD":
                key = "_".join(sorted(filtered_attrs))
                if key == "blazing_fortune_fishing_experience":
                    magma_sets["bf_fe"].append((slot, score, desc))
                elif key == "blazing_fortune_magic_find":
                    magma_sets["bf_mf"].append((slot, score, desc))

        if tiki:
            desc.append(f"Tiki Bonus +50")

        if slot not in best_pieces or score > best_pieces[slot][0]:
            best_pieces[slot] = (score, desc)

    results = []
    total = 0
    for slot in piece_slots:
        if slot in best_pieces:
            score, desc = best_pieces[slot]
            total += score
            results.append(f"{slot.capitalize()} ({', '.join(desc)})")

    covered = set()
    if magma_sets["bf_fe"] and magma_sets["bf_mf"]:
        total = 0
        results = []
    for key in ["bf_fe", "bf_mf"]:
        for slot, score, desc in magma_sets[key]:
            if slot not in covered:
                covered.add(slot+key)
                total += score
                results.append(f"{slot.capitalize()} {key.upper()} ({', '.join(desc)})")

    return total, "; ".join(results) if results else "No valid armor pieces found"

def armor_weight(items):
    set_scores = {
        "MAGMA_LORD": 50,
        "THUNDER": 30,
        "SHARK_SCALE": 10,
        "DIVER": 7,
        "SPONGE": 5,
        "SALMON": 3
    }

    base_set = best_full_set(items)
    set_bonus = set_scores.get(base_set, 20 if base_set == "lava_sc" else 0) if base_set else 0
    base_text = f"Set Bonus: +{set_bonus} ({base_set})" if base_set else "No full set bonus"

    piece_score, piece_desc = best_armor_pieces(items)
    total = set_bonus + piece_score
    breakdown = [base_text] + ([piece_desc] if piece_desc else [])

    return total, "; ".join(breakdown)

def equipment_weight(items):
    slot_map = {
        "belt": {"ICHTHYIC_BELT": 5, "FINWAVE_BELT": 10, "GILLSPLASH_BELT": 20, "BACKWATER_BELT": 1},
        "cloak": {"ICHTHYIC_CLOAK": 5, "FINWAVE_CLOAK": 10, "GILLSPLASH_CLOAK": 20, "BACKWATER_CLOAK": 1},
        "gloves": {"ICHTHYIC_GLOVES": 5, "FINWAVE_GLOVES": 10, "GILLSPLASH_GLOVES": 20, "BACKWATER_GLOVES": 1, "MAGMA_LORD_GAUNTLET": 10},
        "necklace": {"BACKWATER_NECKLACE": 1, "DELIRIUM_NECKLACE": 2, "THUNDERBOLT_NECKLACE": 3}
    }

    def star_bonus(stars, scaling):
        return sum(1 if i < 5 else scaling for i in range(stars))

    best_by_slot = {}

    for item in items:
        ea = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = ea.get("id", "")
        stars = ea.get("upgrade_level", 0)
        rarity_up = ea.get("rarity_upgrades", 0)
        reforge = ea.get("modifier", "")
        attrs = ea.get("attributes", {})

        for slot, ids in slot_map.items():
            if item_id in ids:
                base = ids[item_id]
                score = base

                # star scaling
                if "DELIRIUM_NECKLACE" == item_id:
                    score += star_bonus(stars, 4)
                else:
                    score += star_bonus(stars, 3)

                # rarity upgrade
                if rarity_up >= 1:
                    score += 2

                # reforge
                if reforge == "snowy":
                    score += 2

                # attribute logic
                if item_id == "THUNDERBOLT_NECKLACE":
                    score += attr_weight(attrs, "THUNDER")
                elif item_id == "MAGMA_LORD_GAUNTLET":
                    score += attr_weight(attrs, "MAGMA_LORD")

                if slot not in best_by_slot or score > best_by_slot[slot][0]:
                    best_by_slot[slot] = (score, item_id)

    total = sum(score for score, _ in best_by_slot.values())
    breakdown = [f"{slot.capitalize()}: {item_id} ({score})" for slot, (score, item_id) in best_by_slot.items()]

    return total, "; ".join(breakdown)

# Fishing weight function based on EXP
def fishing_exp_weight(profile, uuid):
    normalized_uuid = uuid.replace("-", "")
    member = profile.get("members", {}).get(normalized_uuid, {})

    # EXP-based weight
    exp = member.get("player_data", {}).get("experience", {}).get("SKILL_FISHING", 0)
    value = ((exp + 10_000_000) / 30_000_000)
    log_term = math.log(value, 200)
    exp_score = int((1000 * log_term + 208) * 0.75)

    total_score = exp_score
    breakdown = f"{exp:,} Fishing EXP → +{exp_score}"

    return total_score, breakdown

def pet_weight(pets):
    pet_caps = 25353230
    pet_points = {
        "HERMIT_CRAB": {"common": 3, "uncommon": 3, "rare": 3, "epic": 5, "legendary": 10, "mythic": 30},
        "FLYING_FISH": {"common": 3, "uncommon": 3, "rare": 3, "epic": 3, "legendary": 10, "mythic": 40},
        "AMMONITE": 10,
        "PENGUIN": 10,
        "SQUID": {"common": 3, "uncommon": 3, "rare": 3, "epic": 3, "legendary": 15},
        "MEGALODON": {"common": 5, "uncommon": 5, "rare": 5, "epic": 5, "legendary": 10},
        "REINDEER": 10,
        "SPINOSAURUS": 10
    }

    best_by_type = {}

    for pet in pets:
        pet_type = pet.get("type")
        rarity = pet.get("tier", "common").lower()
        exp = pet.get("exp", 0)
        held = pet.get("heldItem", "")

        if pet_type not in pet_points:
            continue

        base = 0
        if isinstance(pet_points[pet_type], int):
            base = pet_points[pet_type]
        else:
            base = pet_points[pet_type].get(rarity, 0)

        weight = base * min(exp / pet_caps, 1)

        if held == "BURNT_TEXTS":
            weight += 15

        if pet_type not in best_by_type or weight > best_by_type[pet_type]:
            best_by_type[pet_type] = weight

    total = int(sum(best_by_type.values()))
    breakdown = [f"{ptype}: {int(score)}" for ptype, score in best_by_type.items()]
    return total, "; ".join(breakdown)

def bestiary_weight(profile, uuid):
    kills_data = profile.get("members", {}).get(uuid, {}).get("bestiary", {}).get("kills", {})

    groups = [
        (["ragnarok_666"], "Ragnarok", 100),
        (["lord_jawbus_600"], "Lord Jawbus", 100),
        (["reindrake_100"], "Reindrake", 100),
        (["zombie_miner_150"], "Abyssal Miner", 250),
        (["wiki_tiki_400"], "Wiki Tiki", 100),
        (["grim_reaper_190"], "Grim Reaper", 100),
    ]

    total_weight = 0
    desc_parts = []

    for keys, label, max_kills in groups:
        total_kills = sum(kills_data.get(k, 0) for k in keys)
        percent = min(total_kills / max_kills, 10)
        weight = int(min(percent, 1) * 75 + max(percent - 1, 0) * (75 / 3))
        total_weight += weight
        if percent != 10:
            desc_parts.append(f"{label}: {int(percent * 100)}% | +{weight}")
        else:
            desc_parts.append(f"{label}: CAPPED! | +{weight}")

    return round(total_weight), "Fishing Diversity Value [judged via bestiaries]:" + ", ".join(desc_parts) + f" | Total FDV Weight: +{round(total_weight)}"

def fishing_weight(profile, uuid, all_pets, items):
    weights = []

    exp_score, exp_desc = fishing_exp_weight(profile, uuid)
    weights.append([exp_desc, exp_score])

    rod_score, rod_desc = rod_weight(items)
    weights.append([rod_desc, rod_score])

    trophy_score, trophy_desc = trophy_fish_weight(profile, uuid)
    weights.append([trophy_desc, trophy_score])

    armor_score, armor_desc = armor_weight(items)
    weights.append([armor_desc, armor_score])

    equipment_score, equipment_desc = equipment_weight(items)
    weights.append([equipment_desc, equipment_score])

    pet_score, pet_desc = pet_weight(all_pets)
    weights.append([pet_desc, pet_score])

    be_score, be_desc = bestiary_weight(profile, uuid)
    weights.append([be_desc, be_score])

    total = int(sum(score for _, score in weights))
    breakdown = [desc for desc, _ in weights]
    return total, breakdown
