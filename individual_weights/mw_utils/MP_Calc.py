import re
import json
import aiofiles
import asyncio
import os

ACCESSORY_GROUPS = {}

async def load_accessory_groups():
    global ACCESSORY_GROUPS
    current_dir = os.path.dirname(__file__)
    path = os.path.join(current_dir, "Accessory_Lines.json")
    async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
        content = await f.read()
        ACCESSORY_GROUPS = json.loads(content)


RARITY_MP = {
    "COMMON": 3,
    "UNCOMMON": 5,
    "RARE": 8,
    "EPIC": 12,
    "LEGENDARY": 16,
    "MYTHIC": 22,
    "SPECIAL": 3,
    "VERY SPECIAL": 5
}

deny_mp = {"RIFT_PRISM"}
double_mp = {"HEGEMONY_ARTIFACT"}
abicase_ids = {"ABICASE", "ACTUALLY_BLUE_ABICASE", "BLUE_BUT_GREEN_ABICASE", "BLUE_BUT_RED_ABICASE", "BLUE_BUT_YELLOW_ABICASE", "SUMSUNG_G3_ABICASE", "SUMSUNG_GG_ABICASE"}

# flatten group values to map item_id -> group name
ID_TO_GROUP = {}
for group_name, entries in ACCESSORY_GROUPS.items():
    for _, item_id in entries:
        ID_TO_GROUP[item_id] = group_name

def is_accessory(item):
    lore = item.get("tag", {}).get("display", {}).get("Lore", [])
    for line in reversed(lore[-2:]):  # Only check last few lines
        if any(keyword in line.upper() for keyword in ["ACCESSORY", "HATCCESSORY"]):
            return True
    return False

def strip_lore_rarity(item):
    lore = item.get("tag", {}).get("display", {}).get("Lore", [])
    for line in reversed(lore):
        match = re.search(r"§.\s*(COMMON|UNCOMMON|RARE|EPIC|LEGENDARY|MYTHIC|SPECIAL|VERY SPECIAL)", line)
        if match:
            return match.group(1)
    return None

def calc_contact_mp(profile, uuid):
    try:
        members = profile.get("members", {})
        member_data = members.get(uuid, {})
        nether_data = member_data.get("nether_island_player_data", {})
        abiphone = nether_data.get("abiphone", {})
        contact_data = abiphone.get("contact_data", {})

        contact_count = len(contact_data)

        return contact_count // 2
    except Exception as e:
        print(f"Abiphone MP error: {e}")
        return 0

def has_given_rift_prism(profile, uuid):
    return profile.get("members", {}).get(uuid, {}).get("rift", {}).get("access", {}).get("consumed_prism", False)


def calculate_magical_power(items, profile, uuid): # Accurate to within 10 points based on testing.
    best_in_group = {}

    for item in items:
        item_id = item.get("tag", {}).get("ExtraAttributes", {}).get("id")

        if not item_id:
            continue

        if not is_accessory(item) and item_id not in abicase_ids:
            continue

        # Abicase special handling
        if any(abi in item_id for abi in abicase_ids):
            rarity = strip_lore_rarity(item)
            if not rarity:
                continue
            base_mp = RARITY_MP.get(rarity.upper(), 0)
            bonus_mp = calc_contact_mp(profile, uuid)
            total_mp = base_mp + bonus_mp
            best_in_group[item_id] = ("ABICASE", total_mp)
            continue

        if item_id in deny_mp:
            continue

        rarity = strip_lore_rarity(item)
        if not rarity:
            continue

        base_mp = RARITY_MP.get(rarity.upper(), 0)
        if item_id in double_mp:
            base_mp *= 2

        group = ID_TO_GROUP.get(item_id, item_id)
        current = best_in_group.get(group, (None, -1))
        if base_mp > current[1]:
            best_in_group[group] = (item_id, base_mp)
        else:
            continue

    total = sum(mp for _, mp in best_in_group.values())

    prism_consumed = has_given_rift_prism(profile, uuid)
    if prism_consumed:
        total += 11

    return total
