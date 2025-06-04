def score_crimson_set(all_items):
    tier_weights = {
        "CRIMSON": 5,
        "HOT_CRIMSON": 10,
        "BURNING_CRIMSON": 20,
        "FIERY_CRIMSON": 40,
        "INFERNAL_CRIMSON": 100
    }

    attr_pairs_score = {
        frozenset(["veteran", "vitality"]): 150,
        frozenset(["veteran", "magic_find"]): 200,
        frozenset(["vitality", "magic_find"]): 90,
    }

    gem_tier_points = {
        "ROUGH": 1,
        "FLAWED": 2,
        "FINE": 4,
        "FLAWLESS": 6,
        "PERFECT": 10,
    }

    def attribute_score(attr_data):
        # Map attribute names
        remap = {
            "mending": "vitality",
            "veteran": "veteran",
            "magic_find": "magic_find"
        }

        # Remap attributes to scoring ones
        mapped = {remap[k]: v for k, v in attr_data.items() if k in remap}
        key = frozenset(mapped.keys())
        gr_bonus = attr_pairs_score.get(key, 0)  # good roll bonus only if valid pair
        tier_bonus = sum(2 ** (v - 1) for v in mapped.values())

        return gr_bonus + tier_bonus

    def enhancement_score(i):
        score = 0
        enchants = i.get("tag", {}).get("ExtraAttributes", {}).get("enchantments", {})
        if enchants.get("protection") == 7:
            score += 10
        if enchants.get("growth") == 7:
            score += 10
        ultimate_hab = enchants.get("ultimate_habanero_tactics", 0)
        ultimate_legion = enchants.get("ultimate_legion", 0)
        if ultimate_hab == 4:
            score += 50
        elif ultimate_hab == 5:
            score += 100
        elif ultimate_legion > 0:
            score += 5 * ultimate_legion

        gems = ea.get("gems", {})
        unlocked = gems.get("unlocked_slots", [])
        score += len(unlocked) * 10
        for gslot in unlocked:
            gem_type = gems.get(f"{gslot}_gem")
            tier = gems.get(gslot)
            if tier and gem_type:
                base_score = gem_tier_points.get(str(tier).upper(), 0)
                if gem_type == "JASPER":
                    base_score += 4
                elif gem_type == "ONYX":
                    base_score += 2
                score += base_score

        return score

    best_per_piece = {}

    for item in all_items:
        ea = item.get("tag", {}).get("ExtraAttributes", {})
        item_id = ea.get("id", "")
        if not any(tier in item_id for tier in tier_weights):
            continue

        for tier, tier_val in tier_weights.items():
            if item_id.startswith(tier):
                slot = item_id.replace(tier + "_", "")
                base = tier_val
                attr = attribute_score(ea.get("attributes", {}))
                upgrade = enhancement_score(item)
                total = base + attr + upgrade

                if "HELMET" in slot:
                    total *= 0.75 if total * 0.75 > 50 else 0

                if total > 1000:
                    total = (total - (total - 1000)) + ((total - 1000) / 2)

                if (slot not in best_per_piece or total > best_per_piece[slot]["score"]) and total != 0:
                    best_per_piece[slot] = {
                        "id": item_id,
                        "tier": tier,
                        "score": total,
                        "base": base,
                        "attr": attr,
                        "upgrade": upgrade,
                        "helmet_adjusted": "HELMET" in slot
                    }

    total_score = round(sum(piece["score"] for piece in best_per_piece.values()))
    breakdown = [
        f"{data['id']}: Tier {data['tier']} ({data['base']} base), {data['attr']} Attribute Points, Upgrades {data['upgrade']}{', ×0.75 (helmet multiplier)' if data['helmet_adjusted'] else ''}{', ×0.5 for weight past 1000' if data['score'] > 1000 else ''} → {round(data['score'])}"
        for data in best_per_piece.values()
    ]
    return total_score, breakdown