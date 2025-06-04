import asyncio
from .mapleWeight import main

def run_maple_weight(username, api_key, *, profile=None, infodump=False):
    return asyncio.run(main(username, api_key, profile=profile, infodump=infodump))
