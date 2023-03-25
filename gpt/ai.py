import os
import json
import httpx
import random

from dotenv import load_dotenv
load_dotenv()

WORKING_FILE = os.getenv('WORKING_FILE')
INVALID_FILE = os.getenv('INVALID_FILE')

TAKE_LONG = []

def parse_key(key: str) -> str:
    return f'sk-{key.replace(",", "T3BlbkFJ")}'

def unparse(key: str) -> str:
    return key.replace('sk-', '').replace('T3BlbkFJ', ',')

def get_key() -> str:
    with open(WORKING_FILE, encoding='utf8') as keys_file:
        keys = keys_file.read().splitlines()

    while 1:
        key = random.choice(keys)

        if ',' in key and not key.startswith('#'):
            return parse_key(key)

def invalidate_key(invalid_key: str) -> None:
    with open(WORKING_FILE, 'r') as source:
        lines = source.read().splitlines()

    with open(WORKING_FILE, 'w') as empty:
        empty.write('')

    print(lines)

    with open(WORKING_FILE, 'a') as working:
        line_count = 0
        for line in lines:
            if unparse(invalid_key) not in line:
                newline = '\n' if line_count else '' 
                working.write(f'{newline}{line}')
                line_count += 1

    with open(INVALID_FILE, 'a') as invalid:
        print(3, invalid_key)
        invalid.write(f'{unparse(invalid_key)}\n')

def add_stat(key: str):
    with open('stats.json', 'r') as stats_file:
        stats = json.loads(stats_file.read())

    with open('stats.json', 'w') as stats_file:
        if not stats.get(key):
            stats[key] = 0

        stats[key] += 1
        json.dump(stats, stats_file)

def respond_to_request(request, path):
    params = request.args.copy()
    params.pop('request-method', None)

    actual_path = path.replace('v1/', '')
    add_stat('*')
    add_stat(actual_path)

    while 1:
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
