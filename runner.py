import asyncio
from .mapleWeight import main

def run_maple_weight(username, api_key, *, profile=None, infodump=False):
    return asyncio.run(main(username, api_key, profile=profile, infodump=infodump))

# This is the entrypoint to the project. To use the entire software, you must run this function.

# For the code to be run, set up another project, import this project, and then use the following:
'''
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import MapleWeight.runner
import asyncio
import functools

loop = asyncio.get_event_loop()
fn = functools.partial(MapleWeight.runner.run_maple_weight, username, API_KEY, profile=profile)
weight_val, ld_breakdown = await loop.run_in_executor(None, fn)
'''
# I'm not the best programmer so this project may have some faults. Some unoptimal stuff. Etc.
