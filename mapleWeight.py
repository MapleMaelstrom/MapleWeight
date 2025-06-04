import json
from .get_data import *
from .individual_weights.weapons import weapon_weight
from .individual_weights.pets import pet_weight
from .individual_weights.slayers import slayer_weight
from .individual_weights.farming import farming_weight
from .individual_weights.dungeons import dungeon_weight
from .individual_weights.generic_skills import generic_skill_weight
from .individual_weights.mw_utils.MP_Calc import load_accessory_groups
from .individual_weights.foraging import foraging_weight
from .individual_weights.diana import diana_weight
from .individual_weights.fishing import fishing_weight
from .individual_weights.mining import mining_weight

async def main(username, api_key, *, profile: str = None, infodump: bool = False):
    uuid = await get_uuid(username)
    profiles = await get_skyblock_profiles(api_key, username)

    if profile:
        # lowercase match for user-supplied profile name
        matching = [p for p in profiles if p.get("cute_name", "").lower() == profile.lower()]

        if not matching:
            # Collect all available profile names for error message
            available = [p.get("cute_name") or "[Unnamed]" for p in profiles if "cute_name" in p]

            raise ValueError(
                f"No profile found with name '{profile}'. "
                f"Available profiles: {', '.join(available) if available else '[none found]'}"
            )

        profile = matching[0]
    else:
        profile = [p for p in profiles if p.get("selected")][0]
    profile_id = profile.get("profile_id")
    museum_data = await get_museum_data(api_key, profile_id)
    garden_data = await get_garden_data(api_key, profile_id)
    all_items = extract_all_items(profile, uuid, museum_data=museum_data)

    if infodump:
        with open("profile_dump_full.json", "w") as f:
            json.dump(to_json_safe(profile), f, indent=2)

    all_pets = extract_pets(profile, uuid)

    weight = 0

    # Weapons
    await load_accessory_groups()
    ld_breakdown = []
    weapons, weapon_desc = weapon_weight(all_items, profile, uuid)
    weight += weapons
    print(f"↳ Weapons: {weapons}")
    ld_breakdown.append(f"↳ Weapons: {weapons}")
    print(f"  Weapon Score Breakdown: {weapon_desc}")

    # Pets
    pets, pets_desc = pet_weight(all_pets, profile, uuid)
    weight += pets
    print(f"↳ Pets: {pets}")
    ld_breakdown.append(f"↳ Pets: {pets}")
    print(f"  Pet Score Breakdown: {pets_desc}")

    # Slayers
    slayers, slayer_desc, crimson_armor = slayer_weight(profile, uuid, all_pets, all_items)
    weight += slayers
    print(f"↳ Slayers: {slayers}")
    ld_breakdown.append(f"↳ Slayers: {slayers}")
    print(f"  Slayer Score Breakdown: {slayer_desc}")
    if crimson_armor:
        print(f"  Crimson Score Breakdown: {crimson_armor}")

    # Farming
    farming, farming_desc = farming_weight(profile, uuid, all_pets, all_items, garden_data)
    weight += farming
    print(f"↳ Farming: {farming}")
    ld_breakdown.append(f"↳ Farming: {farming}")
    print(f"  Farming Score Breakdown: {farming_desc}")

    # Generic Skills
    generic_skills, generic_skills_desc = generic_skill_weight(profile, uuid)
    weight += generic_skills
    print(f"↳ Generic Skills (Alchemy, Carpentry, Enchanting, Taming): {generic_skills}")
    ld_breakdown.append(f"↳ Generic Skills (Alchemy, Carpentry, Enchanting, Taming): {generic_skills}")
    print(f"  Generic Skill Score Breakdown: {generic_skills_desc}")

    # Dungeons
    dungeons, dungeon_desc = dungeon_weight(profile, uuid, all_pets, all_items)
    weight += dungeons
    print(f"↳ Dungeon Weight: {dungeons}")
    ld_breakdown.append(f"↳ Dungeon Weight: {dungeons}")
    print(f"  Dungeon Score Breakdown: {dungeon_desc}")

    # Foraging
    foraging, foraging_desc = foraging_weight(profile, uuid, all_items)
    weight += foraging
    print(f"↳ Foraging Weight: {foraging}")
    ld_breakdown.append(f"↳ Foraging Weight: {foraging}")
    print(f"  Foraging Score Breakdown: {foraging_desc}")

    # Diana Event
    diana, diana_desc = diana_weight(profile, uuid, all_items)
    weight += diana
    print(f"↳ Diana Weight: {diana}")
    ld_breakdown.append(f"↳ Diana Weight: {diana}")
    print(f"  Diana Score Breakdown: {diana_desc}")

    # Fishing
    fishing, fishing_desc = fishing_weight(profile, uuid, all_pets, all_items)
    weight += fishing
    print(f"↳ Fishing Weight: {fishing}")
    ld_breakdown.append(f"↳ Fishing Weight: {fishing}")
    print(f"  Fishing Score Breakdown: {fishing_desc}")

    # Mining
    mining, mining_desc = mining_weight(profile, uuid, all_items, all_pets)
    weight += mining
    print(f"↳ Mining Weight: {mining}")
    ld_breakdown.append(f"↳ Mining Weight: {mining}")
    print(f"  Mining Score Breakdown: {mining_desc}")

    # Total
    print(f"{username}'s MapleWeight{str(' (' + profile.get('cute_name', '') + ')') if profile.get('cute_name', '') != '' else ''}: {weight}")
    print(uuid)

    # Infodump
    '''
    if infodump:
        with open("pet_dump2.txt", "w") as f:
            json.dump(to_json_safe(all_pets), f, indent=2)
    '''

    return weight, ld_breakdown
