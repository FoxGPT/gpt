import os
import json
import httpx
import random

from dotenv import load_dotenv
load_dotenv()

# In the file defined as "WORKING_FILE", you should have a list of OpenAI API keys, one per line.
# Not all of them have to be valid, but it will make the script run faster.
# The more, the better.

# IMPORTANT:
# The keys have to follow the following format:
# NORMAL OPENAI FORMAT: 
# sk-XXXXXXXXXXXXXXXXXXXXT3BlbkFJXXXXXXXXXXXXXXXXXXXX
# HOW YOU SHOULD SAVE THEM:
# XXXXXXXXXXXXXXXXXXXX,XXXXXXXXXXXXXXXXXXXX

# You can comment out keys by adding a # at the beginning of the line.

WORKING_FILE = os.getenv('WORKING_FILE')

# This file will be used to store the invalid keys.
# Don't worry about it, it will be created automatically.
INVALID_FILE = os.getenv('INVALID_FILE')

# By default, the file paths for the WOR

def parse_key(key: str) -> str:
    """Parse a key to the format that OpenAI expects."""
    return f'sk-{key.replace(",", "T3BlbkFJ")}'

def unparse(key: str) -> str:
    """Unparse a key to the format that we use."""
    return key.replace('sk-', '').replace('T3BlbkFJ', ',')

def get_key() -> str:
    """Get a random key from the working file."""
    with open(WORKING_FILE, encoding='utf8') as keys_file:
        keys = keys_file.read().splitlines()

    while True:
        key = random.choice(keys)

        if ',' in key and not key.startswith('#'):
            return parse_key(key)

def invalidate_key(invalid_key: str) -> None:
    """Moves an invalid key to another file for invalid keys."""
    with open(WORKING_FILE, 'r') as source:
        lines = source.read().splitlines()

    with open(WORKING_FILE, 'w') as empty:
        empty.write('')

    with open(WORKING_FILE, 'a') as working:
        line_count = 0
        for line in lines:
            if unparse(invalid_key) not in line:
                newline = '\n' if line_count else '' 
                working.write(f'{newline}{line}')
                line_count += 1

    with open(INVALID_FILE, 'a') as invalid:
        invalid.write(f'{unparse(invalid_key)}\n')

def add_stat(key: str):
    """Add +1 to the specified statistic"""
    with open('stats.json', 'r') as stats_file:
        stats = json.loads(stats_file.read())

    with open('stats.json', 'w') as stats_file:
        if not stats.get(key):
            stats[key] = 0

        stats[key] += 1
        json.dump(stats, stats_file)

def proxy_api(request, path):
    """Makes a request to the official API"""
    params = request.args.copy()
    params.pop('request-method', None)

    actual_path = path.replace('v1/', '')

    if '/' in actual_path:
        add_stat('*')
        add_stat(actual_path)

    while True:
        key = get_key()

        try:
            resp = httpx.request(
                method=request.args.get('request-method', request.method),
                url=f'https://api.openai.com/v1/{actual_path}',
                headers={
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json'
                },
                data=request.data,
                json=request.get_json(silent=True),
                params=params,
                timeout=30,
            )
        except httpx.ReadTimeout:
            continue
        
        if not isinstance(resp, dict):
            resp = resp.json()

        if resp.get('error'):
            if resp['error']['code'] == 'invalid_api_key':
                invalidate_key(key)
                continue

        return resp
