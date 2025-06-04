import aiohttp
import json
import base64, zlib
import nbtlib
from nbtlib.tag import ByteArray
import gzip
import io
import time
import os

_profile_cache = {}  # username -> (profiles, last_updated_time)
_uuid_cache = {}     # username -> (uuid, last_updated_time)
CACHE_PATH = os.path.join(os.path.dirname(__file__), "profile_cache.json")

CACHE_TTL = 300     # how long data is trusted (used on access)
CACHE_MAX_AGE = 600 # how long we keep data before purging on access

CACHE_PATH = os.path.join(os.path.dirname(__file__), "profile_cache.json")
_last_saved = 0

if os.path.exists(CACHE_PATH):
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
            _uuid_cache = raw.get("uuid_cache", {})
            _profile_cache = {
                k: (v[0], float(v[1])) for k, v in raw.get("profile_cache", {}).items()
            }
            _last_saved = float(raw.get("last_saved", 0))
    except Exception as e:
        print("Failed to load persistent cache:", e)


def _save_profile_cache():
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "uuid_cache": _uuid_cache,
                "profile_cache": {k: [v[0], v[1]] for k, v in _profile_cache.items()},
                "last_saved": time.time()
            }, f)
    except Exception as e:
        print("Failed to save profile cache:", e)

def purge_expired_cache():
    now = time.time()
    expired_users = [
        user for user, (_, last_updated) in _profile_cache.items()
        if now - last_updated > CACHE_MAX_AGE
    ]
    for user in expired_users:
        print(f"{user} has been deleted from cache")
        del _profile_cache[user]
        if user in _uuid_cache:
            del _uuid_cache[user]

def decode_nbt_base64(data_string):
    try:
        raw = base64.b64decode(data_string)

        try:
            decompressed = zlib.decompress(raw)
        except zlib.error:
            decompressed = gzip.decompress(raw)

        stream = io.BytesIO(decompressed)
        nbt = nbtlib.File.parse(stream)

        # ✅ Access directly as a dict
        return nbt['i'] if 'i' in nbt else []
    except Exception as e:
        print(f"Error decoding item data: {e}")
        return []

def to_json_safe(obj):
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_safe(i) for i in obj]
    elif isinstance(obj, ByteArray):
        return list(obj)  # Convert ByteArray to a normal list of ints
    elif hasattr(obj, 'value'):
        return obj.value  # Handle Int, String, etc.
    else:
        return obj

async def get_uuid(username: str):
    now = time.time()
    if username in _uuid_cache:
        uuid, cached_at = _uuid_cache[username]
        if now - cached_at < CACHE_TTL:
            return uuid

    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 204:
                print(f"Username '{username}' not found.")
                return None
            data = await resp.json()
            uuid = data.get("id")
            if uuid:
                _uuid_cache[username] = (uuid, now)
                _save_profile_cache()
            return uuid

async def get_skyblock_profiles(api_key: str, username: str):
    purge_expired_cache()
    now = time.time()

    # Use cached profile data
    if username in _profile_cache:
        profiles, cached_at = _profile_cache[username]
        if now - cached_at < CACHE_TTL:
            return profiles

    # Ensure UUID is fresh
    uuid = await get_uuid(username)
    if not uuid:
        raise ValueError(f"Unable to resolve UUID for username '{username}'")

    url = f'https://api.hypixel.net/v2/skyblock/profiles?uuid={uuid}'
    headers = {'API-Key': api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            if not data.get("success"):
                raise ValueError(f"Failed to fetch profiles: {data}")
            profiles = data.get("profiles", [])
            _profile_cache[username] = (profiles, now)
            _save_profile_cache()
            return profiles

item_sources = [
    "inv_contents",
    "inv_armor",
    "vault_contents",
    "ender_chest_contents",
    "backpack_contents",
    "wardrobe_contents",
    "equipment_contents"
]

def extract_talisman_bag(profile, uuid):
    members = profile.get("members", {})
    member_data = members.get(uuid, {})
    inventory = member_data.get("inventory", {})
    bag_contents = inventory.get("bag_contents", {})

    talisman_bag = bag_contents.get("talisman_bag", {})
    items = []

    if not talisman_bag:
        return items

    if isinstance(talisman_bag, dict) and "data" in talisman_bag:
        try:
            decoded = decode_nbt_base64(talisman_bag["data"])

            if hasattr(decoded, 'tags'):
                if 'i' in decoded:
                    items.extend(decoded['i'].tags)
                elif 'Items' in decoded:
                    items.extend(decoded['Items'].tags)
                else:
                    print("No 'i' or 'Items' tag in decoded NBT structure.")
            elif isinstance(decoded, list):
                items.extend(decoded)
            else:
                print("Decoded structure is not usable.")
        except Exception as e:
            print(f"Failed to decode talisman bag: {e}")
    else:
        print("talisman_bag is missing or improperly structured.")

    return items

def filter_zero_worth(decoded_items):
    def is_worth_item(item):
        if item.get("Count", 1) != 1:
            return False

        lore = item.get("tag", {}).get("display", {}).get("Lore", [])
        if not lore:
            return True

        # Normalize lore lines
        lore_lines = [line.lower() for line in lore]
        first_line = lore_lines[0] if lore_lines else ""
        last_line = lore_lines[-1] if lore_lines else ""

        if "furniture" in first_line or "cosmetic" in last_line or "dye" in last_line or "pickaxe" in last_line:
            return False

        return True

    if isinstance(decoded_items, list):
        return [item for item in decoded_items if is_worth_item(item)]
    elif hasattr(decoded_items, "tags"):
        return [item for item in decoded_items.tags if is_worth_item(item)]
    return []

def extract_all_items(profile, uuid, museum_data):
    items = []

    members = profile.get("members", {})
    member_data = members.get(uuid, {})
    inventory_data = member_data.get("inventory", {})
    items.extend(extract_talisman_bag(profile, uuid))

    for key in item_sources:

        field = inventory_data.get(key, None)
        if field is None:
            continue

        if isinstance(field, dict) and "data" in field:
            decoded = decode_nbt_base64(field["data"])
            if isinstance(decoded, list):
                items.extend(filter_zero_worth(decoded))
            elif hasattr(decoded, 'get') and 'Items' in decoded:
                # Fallback: NBT root with .get("Items")
                items.extend(filter_zero_worth(decoded['Items'].tags))
        elif isinstance(field, dict):
            # Multiple entries (like backpack_contents)
            for entry in field.values():
                if isinstance(entry, dict) and "data" in entry:
                    items.extend(filter_zero_worth(decode_nbt_base64(entry["data"])))
                elif isinstance(entry, str):
                    items.extend(filter_zero_worth(decode_nbt_base64(entry)))
        elif isinstance(field, str):
            items.extend(filter_zero_worth(decode_nbt_base64(field)))

    if museum_data:
        if uuid in museum_data:
            member_museum = museum_data[uuid]
            museum_items = member_museum.get("items", {})

            all_decoded_items = []

            if isinstance(museum_items, dict):
                for val in museum_items.values():
                    nbt_data = val.get("items", {}).get("data")
                    if nbt_data:
                        try:
                            decoded_items = decode_nbt_base64(nbt_data)
                            if hasattr(decoded_items, "tags") and "Items" in decoded_items:
                                items_to_add = decoded_items["Items"].tags
                                items.extend(items_to_add)
                                all_decoded_items.extend(items_to_add)
                            elif isinstance(decoded_items, list):
                                items.extend(decoded_items)
                                all_decoded_items.extend(decoded_items)
                            else:
                                print("[Museum Debug] Unknown structure in decoded museum item.")
                        except Exception as e:
                            print(f"[Museum Debug] Failed to decode museum item: {e}")
            else:
                print("[Museum Debug] 'items' key is not a dict.")
        else:
            print(f"[Museum Debug] UUID {uuid} not found in museum data.")
    else:
        print("[Museum Debug] No museum data provided.")

    with open(f"item_dump_{uuid}.json", "w+", encoding='utf-8') as f:
        json.dump(to_json_safe(items), f)
    return items


def extract_pets(profile, uuid):
    members = profile.get("members", {})
    member_data = members.get(uuid, {})

    # Correct path to pet data
    return member_data.get("pets_data", {}).get("pets", [])

def roman(num):
    return ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"][num - 1] if 1 <= num <= 10 else str(num)

def get_profile_bank(profile_data):
    """Extracts the bank balance from the profile."""
    try:
        return profile_data["banking"]["balance"]
    except KeyError:
        return None

def get_personal_gold_collection(profile_data):
    """Returns the amount of GOLD_INGOT collected by the player."""
    try:
        return profile_data["collection"]["GOLD_INGOT"]
    except KeyError:
        return 0

async def get_museum_data(api_key, profile_id):
    url = f"https://api.hypixel.net/v2/skyblock/museum?profile={profile_id}"
    headers = {"API-Key": api_key}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"[Museum Debug] Failed to fetch museum data: HTTP {resp.status}")
                    return {}

                data = await resp.json()
                return data.get("members", {})
        except Exception as e:
            print(f"[Museum Debug] Exception while fetching museum data: {e}")
            return {}

async def get_garden_data(api_key, profile_id):
    url = f"https://api.hypixel.net/v2/skyblock/garden?profile={profile_id}"
    headers = {"API-Key": api_key}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"[Garden Debug] Failed to fetch garden data: HTTP {resp.status}")
                    return {}

                data = await resp.json()

                return data.get("garden", {})
        except Exception as e:
            print(f"[Garden Debug] Exception while fetching garden data: {e}")
            return {}