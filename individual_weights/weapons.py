from ..get_data import roman
from ..individual_weights.mw_utils.MP_Calc import calculate_magical_power, load_accessory_groups

def count_chimera_books(all_items):
    total_books = 0

    for item in all_items:
        # Get the enchantments dictionary if it exists
        enchantments = item.get('tag', {}).get('ExtraAttributes', {}).get('enchantments', {})

        if 'ultimate_chimera' in enchantments:
            level = enchantments['ultimate_chimera']
            # Number of books required = 2^(level - 1)
            total_books += 2 ** (level - 1)

    return total_books

def chimera_score(n):
    return int(sum(100 if i <= 8 else round(100 - ((i - 8) / (48 - 8)) * 50) if i <= 48 else 50 for i in range(1, n + 1))/2)

def score_terminators(all_items):
    highest_ultimates = {}
    explanations = []

    for item in all_items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        if extra.get("id") != "TERMINATOR":
            continue

        enchants = extra.get("enchantments", {})

        for k, v in enchants.items():
            if k.startswith("ultimate_"):
                if k not in highest_ultimates or v > highest_ultimates[k][0]:
                    highest_ultimates[k] = (v, enchants, extra)

    total_score = 0

    for level, enchants, extra in highest_ultimates.values():
        score = 500
        ultimate_name = [k for k in enchants if k.startswith("ultimate_") and enchants[k] == level][0]
        formatted_name = ultimate_name.replace("ultimate_", "").replace("_", " ").title()
        desc = f"{formatted_name.replace('Reiterate', 'Duplex')} {roman(level)}"

        if enchants.get("power") == 7:
            score += 50
            desc += " + Power VII"
        if enchants.get("cubism") == 6:
            score += 10
            desc += " + Cubism VI"
        if enchants.get("snipe") == 4:
            score += 10
            desc += " + Snipe IV"

        upgrade_level = extra.get("upgrade_level", 0)
        upgrade_bonus = {
            6: 5, 7: 5, 8: 20, 9: 30, 10: 40
        }
        bonus = sum(v for lvl, v in upgrade_bonus.items() if upgrade_level >= lvl)
        score += bonus
        if bonus > 0:
            desc += f" + {str(upgrade_level - 5)} Master Stars"

        explanations.append(f"Terminator ({desc}) +{score}")

        total_score += score

    return total_score, "; ".join(explanations)

def score_hyperions(all_items):
    scroll_set = {"IMPLOSION_SCROLL", "SHADOW_WARP_SCROLL", "WITHER_SHIELD_SCROLL"}
    scroll_hype = None
    chimera_hype = None
    chimera_level = 0

    for item in all_items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        if extra.get("id") not in ["HYPERION", "ASTRAEA", "SCYLLA", "VALKYRIE"]:
            continue

        enchants = extra.get("enchantments", {})
        chimera = enchants.get("ultimate_chimera", 0)

        if not scroll_hype:
            scrolls = set(extra.get("ability_scroll", []))
            if scroll_set.issubset(scrolls) and chimera < 5:
                scroll_hype = item
                continue

        if not chimera_hype and chimera > 0:
            chimera_hype = item
            chimera_level = chimera

        if scroll_hype and chimera_hype:
            break

    score = 0
    desc = []

    if scroll_hype:
        score += 750
        desc.append("Scrolled Wither Blade")

    if chimera_hype:
        chimera_scores = {1: 25, 2: 50, 3: 100, 4: 200, 5: 500}
        val = chimera_scores.get(chimera_level, 0)
        score += val
        desc.append(f"Chimera Wither Blade {roman(chimera_level)}")

    return score, " + ".join(desc) if desc else "No qualifying Wither Blade"

def score_aote_aotv(all_items):
    best_score = 0
    best_desc = ""

    for item in all_items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id")

        if item_id not in {"ASPECT_OF_THE_END", "ASPECT_OF_THE_VOID"}:
            continue

        name = "AOTE" if item_id == "ASPECT_OF_THE_END" else "AOTV"
        score = 5 if item_id == "ASPECT_OF_THE_END" else 6
        desc = [name]

        tuned = extra.get("tuned_transmission", 0)
        if isinstance(tuned, int) and tuned > 0:
            score += tuned
            desc.append(f"{int(tuned)} Tuners")

        if extra.get("ethermerge") == 1:
            score += 10
            desc.append("Ethermerge")

        if score > best_score:
            best_score = score
            best_desc = f"{' + '.join(desc)}"

    return best_score, best_desc or "No AOTE/AOTV found"

def score_power_orbs(all_items):
    orb_scores = {
        "RADIANT_POWER_ORB": 10,
        "MANA_FLUX_POWER_ORB": 20,
        "OVERFLUX_POWER_ORB": 100,
        "PLASMAFLUX_POWER_ORB": 300
    }

    best_score = 0
    best_desc = ""

    for item in all_items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        if item_id not in orb_scores:
            continue

        score = orb_scores[item_id]
        desc = [item_id.replace("_", " ").title()]

        if extra.get("jalapeno_count") == 1:
            score += 10
            desc.append("Jalapeño")

        count = extra.get("mana_disintegrator_count", 0)
        if isinstance(count, int) and count > 0:
            score += count * 2
            desc.append(f"{int(count)} Disintegrators")

        if score > best_score:
            best_score = score
            best_desc = " + ".join(desc)

    return best_score, best_desc or "No Power Orb"

def score_sos_flares(all_items):
    flare_scores = {
        "WARNING_FLARE": 25,
        "ALERT_FLARE": 50,
        "SOS_FLARE": 200
    }

    best_score = 0
    best_desc = ""

    for item in all_items:
        extra = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = extra.get("id", "")
        if item_id not in flare_scores:
            continue

        score = flare_scores[item_id]
        desc = [item_id.replace("_", " ").title()]

        if extra.get("jalapeno_count") == 1:
            score += 5
            desc.append("Jalapeño")

        count = extra.get("mana_disintegrator_count", 0)
        if isinstance(count, int) and count > 0:
            score += count
            desc.append(f"{int(count)} Disintegrators")

        if score > best_score:
            best_score = score
            best_desc = " + ".join(desc)

    return best_score, best_desc or "No Flare"

def score_magical_power(profile, uuid, items):
    try:
        mp = calculate_magical_power(items, profile, uuid)
        score = int((mp / 30) ** 2.1)
        return score, f"Magical Power: {mp} → +{score} points"
    except Exception as e:
        return 0, f"Magical Power error: {e}"


def weapon_weight(all_items, profile, uuid):
    weapon_weights = []

    chimera_books = count_chimera_books(all_items)
    weapon_weights.append([f"{chimera_books} Chimera Books", chimera_score(chimera_books)])

    term_score, term_desc = score_terminators(all_items)
    weapon_weights.append([f"Terminator Score: {term_desc}", term_score])

    hype_score, hype_desc = score_hyperions(all_items)
    weapon_weights.append([f"Hyperion Score: {hype_desc}", hype_score])

    aote_score, aote_desc = score_aote_aotv(all_items)
    weapon_weights.append([f"AOTE/AOTV Score: {aote_desc}", aote_score])

    orb_score, orb_desc = score_power_orbs(all_items)
    weapon_weights.append([f"Power Orb Score: {orb_desc}", orb_score])

    flare_score, flare_desc = score_sos_flares(all_items)
    weapon_weights.append([f"Flare Score: {flare_desc}", flare_score])

    mp_score, mp_desc = score_magical_power(profile, uuid, all_items)
    weapon_weights.append([mp_desc, mp_score])

    total = sum(score for _, score in weapon_weights)
    return total, [i for i in weapon_weights if i[1] != 0]