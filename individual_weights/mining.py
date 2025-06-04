import math

gem_tiers = {
    "ROUGH": 1,
    "FLAWED": 1,
    "FINE": 2,
    "FLAWLESS": 5,
    "PERFECT": 10,
}

gem_bonus = {
    "TOPAZ": 1.5,
    "JADE": 1.0,
    "AMBER": 1.0,
}

def gemstone_score(gems, slot_multiplier):
    score = 0
    unlocked = gems.get("unlocked_slots", [])
    score += slot_multiplier * len(unlocked)

    for slot in unlocked:
        gem_type = gems.get(f"{slot}_gem", None)
        if not gem_type:
            gem_type = slot.split("_")[0]
        gem_type = gem_type.upper()

        quality = gems.get(slot, None)
        if quality is not None:
            if isinstance(quality, dict) or hasattr(quality, "get"):
                quality_str = str(quality.get("quality", ""))
            else:
                quality_str = str(quality)
            base = gem_tiers.get(quality_str.upper(), 0)
            multiplier = gem_bonus.get(gem_type, 0.5)
            score += (base + slot_multiplier) * multiplier

    return score

def score_mining_armor(items):
    sets = {
        "DIVAN": {"base": 10, "slot_value": 6},
        "SORROW": {"base": 7, "slot_value": 3},
        "ARMOR_OF_YOG": {"base": 3, "slot_value": 3},
        "FLAME_BREAKER": {"base": 2, "slot_value": 3},
        "HEAT": {"base": 1, "slot_value": 3},
        "GLACITE": {"base": 1, "slot_value": 1},
    }

    valid_slots = {"HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS"}
    best_per_slot = {}

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        for set_name in sets:
            if item_id.startswith(set_name):
                parts = item_id.split("_")
                slot = parts[-1]
                if slot not in valid_slots:
                    continue  # skip things like chisel, gauntlet, etc.

                base_score = sets[set_name]["base"]
                slot_score = gemstone_score(extra.get("gems", {}), sets[set_name]["slot_value"])

                # Modifiers & upgrades
                mods = 0
                if extra.get("rarity_upgrades", 0) >= 1:
                    mods += 2
                modifier = extra.get("modifier", "").lower()
                if modifier == "jaded":
                    mods += 7
                if modifier == "dimensional":
                    mods += 2

                enchants = extra.get("enchantments", {})
                ice_cold = enchants.get("ice_cold", 0)
                ultimate_wisdom = enchants.get("ultimate_wisdom", 0)

                mods += ice_cold * 5
                if ice_cold >= 5:
                    mods += 5
                mods += ultimate_wisdom

                total_score = base_score + slot_score + mods
                readable_name = f"{set_name.title()} {slot.title()} +{int(total_score)}"

                if slot not in best_per_slot or best_per_slot[slot][0] < total_score:
                    best_per_slot[slot] = (total_score, readable_name)

    total = int(sum(score for score, _ in best_per_slot.values()))
    parts = [desc for _, desc in best_per_slot.values()]
    breakdown = ["Armor: " + ", ".join(parts)]
    return total, breakdown

def score_mineral_armor(items):
    sets = {
        "GLOSSY_MINERAL": 30,
        "MINERAL": 10,
    }

    valid_slots = {"HELMET", "CHESTPLATE", "LEGGINGS", "BOOTS"}
    best_per_slot = {}

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        for set_name in sets:
            if item_id.startswith(set_name):
                parts = item_id.split("_")
                slot = parts[-1]
                if slot not in valid_slots:
                    continue

                base_score = sets[set_name]
                mods = 0

                # Ice Cold and Ultimate Wisdom only
                enchants = extra.get("enchantments", {})
                ice_cold = enchants.get("ice_cold", 0)
                ultimate_wisdom = enchants.get("ultimate_wisdom", 0)

                mods += ice_cold * 5
                if ice_cold >= 5:
                    mods += 5
                mods += ultimate_wisdom

                if extra.get("rarity_upgrades", 0) >= 1:
                    mods += 2
                modifier = extra.get("modifier", "").lower()
                if modifier == "jaded":
                    mods += 7
                if modifier == "dimensional":
                    mods += 2

                total_score = base_score + mods
                readable = f"{set_name.replace('_', ' ').title()} {slot.title()} +{int(total_score)}"

                if slot not in best_per_slot or best_per_slot[slot][0] < total_score:
                    best_per_slot[slot] = (total_score, readable)

    total = sum(score for score, _ in best_per_slot.values())
    parts = [desc for _, desc in best_per_slot.values()]
    breakdown = [f"Mineral Armor: {', '.join(parts)}"] if parts else []
    return total, breakdown

def main_drill_weight(items):
    drill_values = {
        "TITANIUM_DRILL_1": 10,
        "TITANIUM_DRILL_2": 20,
        "TITANIUM_DRILL_3": 75,
        "TITANIUM_DRILL_4": 200,
        "DIVAN_DRILL": 1500,
    }

    drill_names = {
        "TITANIUM_DRILL_1": "Titanium Drill DR-X355",
        "TITANIUM_DRILL_2": "Titanium Drill DR-X455",
        "TITANIUM_DRILL_3": "Titanium Drill DR-X555",
        "TITANIUM_DRILL_4": "Titanium Drill DR-X655",
        "DIVAN_DRILL": "Divan's Drill"
    }

    reforge_values = {
        "heated": 2,
        "lustrous": 20,
        "stellar": 2,
        "auspicious": 10,
        "glacial": 10,
    }

    engine_values = {
        "MITHRIL_DRILL_ENGINE": 7,
        "TITANIUM_DRILL_ENGINE": 20,
        "RUBY_POLISHED_DRILL_ENGINE": 50,
        "SAPPHIRE_POLISHED_DRILL_ENGINE": 100,
        "AMBER_POLISHED_DRILL_ENGINE": 215,
    }

    fuel_tank_values = {
        "MITHRIL_FUEL_TANK": 5,
        "TITANIUM_FUEL_TANK": 10,
        "GEMSTONE_FUEL_TANK": 20,
        "PERFECTLY_CUT_FUEL_TANK": 95,
    }

    upgrade_module_values = {
        "GOBLIN_OMELETTE": 5,
        "GOBLIN_OMELETTE_PESTO": 10,
        "GOBLIN_OMELETTE_SPICY": 10,
        "GOBLIN_OMELETTE_SUNNY_SIDE": 40,
        "GOBLIN_OMELETTE_BLUE_CHEESE": 0,
    }

    best_score = 0
    best_desc = []

    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        drill_id = extra.get("id", "")
        if drill_id not in drill_values:
            continue

        score = 0
        breakdown = []

        # Base drill
        base_val = drill_values[drill_id]
        score += base_val
        breakdown.append(f"{drill_names[drill_id]} +{base_val}")

        # Reforge
        reforge = extra.get("modifier", "").lower()
        if reforge in reforge_values:
            val = reforge_values[reforge]
            score += val
            breakdown.append(f"{reforge.title()} Reforge +{val}")

        # Enchantments
        enchants = extra.get("enchantments", {})
        if enchants.get("efficiency", 0) == 10:
            score += 5
            breakdown.append("Efficiency 10 +5")
        lapidary = enchants.get("lapidary", 0)
        if lapidary > 0:
            val = lapidary * 4
            if lapidary >= 5:
                val += 25
            score += val
            breakdown.append(f"Lapidary {lapidary} +{val}")
        pristine = enchants.get("pristine", 0)
        if pristine > 0:
            val = pristine * 4
            if pristine >= 5:
                val += 25
            score += val
            breakdown.append(f"Prismatic {pristine} +{val}")
        paleontologist = enchants.get("paleontologist", 0)
        if paleontologist > 0:
            val = paleontologist * 2
            score += val
            breakdown.append(f"Paleontologist {paleontologist} +{val}")
        compact = enchants.get("compact", 0)
        if compact >= 10:
            score += 15
            breakdown.append("Compact 10 +15")
        elif compact == 9:
            score += 3
            breakdown.append("Compact 9 +3")
        elif compact >= 1:
            score += 1
            breakdown.append(f"Compact {compact} +1")

        # Polarvoid
        polarvoid = extra.get("polarvoid", 0)
        if polarvoid == 5:
            score += 5
            breakdown.append("Polarvoid 5 +5")
        elif polarvoid >= 1:
            score += 3
            breakdown.append(f"Polarvoid {polarvoid} +3")

        # Rarity upgrade
        if extra.get("rarity_upgrades", 0) >= 1:
            score += 2
            breakdown.append("Rarity Upgrade +2")

        # Gemstones
        gems = extra.get("gems", {})
        gem_score = gemstone_score(gems, 3)
        if gem_score > 0:
            score += gem_score
            breakdown.append(f"Gemstones +{int(gem_score)}")

        # Drill parts
        fuel = extra.get("drill_part_fuel_tank", "")
        engine = extra.get("drill_part_engine", "")
        module = extra.get("drill_part_upgrade_module", "")

        fuel_score = fuel_tank_values.get(fuel.upper(), 0)
        if fuel_score:
            score += fuel_score
            breakdown.append(f"{fuel.replace('_', ' ').title()} +{fuel_score}")

        engine_score = engine_values.get(engine.upper(), 0)
        if engine_score:
            score += engine_score
            breakdown.append(f"{engine.replace('_', ' ').title()} +{engine_score}")

        module_score = upgrade_module_values.get(module.upper(), 0)
        if module_score:
            score += module_score
            breakdown.append(f"{module.replace('_', ' ').title()} +{module_score}")

        if score > best_score:
            best_score = score
            best_desc = [f"Main Drill:"] + breakdown

    return int(best_score), " ".join(best_desc) + f" | {int(best_score)}"

def blegg_weight(items):
    for item in items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        if extra.get("drill_part_upgrade_module", "").lower() == "goblin_omelette_blue_cheese":
            return 100, ["Blegg Drill: Goblin Omelette Blue Cheese +100"]
    return 0, []

def m_weight(x):
    return int(1300 * math.log((x + 2_000_000) / 2_000_000, 300))

def g_weight(x):
    return int(1900 * math.log((x + 2_000_000) / 2_000_000, 300))

def hotm_weight(profile, uuid):
    weights = []

    mining_core = profile.get("members", {}).get(uuid, {}).get("mining_core", {})
    nodes = mining_core.get("nodes", {})

    # COTM score
    cotm = nodes.get("special_0", 0)
    cotm_score = min(cotm ** 3, 1000)
    if cotm > 0:
        weights.append([f"COTM {cotm} +{cotm_score}", cotm_score])

    # Powder values
    mithril = mining_core.get("powder_glacite", 0) + mining_core.get("powder_spent_glacite", 0)
    gemstone = mining_core.get("powder_gemstone", 0) + mining_core.get("powder_spent_gemstone", 0)
    glacite = mining_core.get("powder_glacite", 0) + mining_core.get("powder_spent_glacite", 0)

    m_score = m_weight(mithril)
    g_score_gem = g_weight(gemstone)
    g_score_glacite = g_weight(glacite)

    if m_score > 0:
        weights.append(["Mithril Powder +{}".format(m_score), m_score])
    if g_score_gem > 0:
        weights.append(["Gemstone Powder +{}".format(g_score_gem), g_score_gem])
    if g_score_glacite > 0:
        weights.append(["Glacite Powder +{}".format(g_score_glacite), g_score_glacite])

    total = sum(score for _, score in weights)
    breakdown = [entry[0] for entry in weights if entry[1] != 0]
    return total, ', '.join(breakdown) + f" | +{total}"

def mining_weight(profile, uuid, items, pets):
    weights = []

    armor_score, armor_desc = score_mining_armor(items)
    weights.append([armor_desc, armor_score])

    mineral_score, mineral_desc = score_mineral_armor(items)
    weights.append([mineral_desc, mineral_score])

    drill_score, drill_desc = main_drill_weight(items)
    weights.append([drill_desc, drill_score])

    blegg_score, blegg_desc = blegg_weight(items)
    weights.append([blegg_desc, blegg_score])

    hotm_score, hotm_desc = hotm_weight(profile, uuid)
    weights.append([hotm_desc, hotm_score])

    total = sum(score for _, score in weights)
    breakdown = [entry for entry in weights if entry[1] != 0]

    return total, breakdown
