import os
import json
import random
import requests
import re
from dotenv import load_dotenv
load_dotenv()
from flask import Flask,request,redirect,Response

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
GPT4_FILE = os.getenv('GPT4_FILE')

# This file will be used to store the invalid keys.
# Don't worry about it, it will be created automatically.
INVALID_FILE = os.getenv('INVALID_FILE')
USERKEYS_FILE = os.getenv('USERKEYS_FILE')

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
        return key
def get_key_gpt4() -> str:
    """Get a random key from the working file."""
    with open(GPT4_FILE, encoding='utf8') as keys_file:
        keys = keys_file.read().splitlines()

    while True:
        key = random.choice(keys)
        return key
def invalidate_key(invalid_key: str) -> None:
    """Moves an invalid key to another file for invalid keys."""
    with open(WORKING_FILE, 'r') as source:
        lines = source.read().splitlines()
    with open(GPT4_FILE, 'r') as source2:
        lines2 = source2.read().splitlines()
    with open(WORKING_FILE, 'w') as empty:
        empty.write('')
    with open(GPT4_FILE, 'w') as empty2:
        empty2.write('')

    with open(WORKING_FILE, 'a') as working:
        line_count = 0
        for line in lines:
            if unparse(invalid_key) not in line:
                newline = '\n' if line_count else '' 
                working.write(f'{newline}{line}')
                line_count += 1

    with open(INVALID_FILE, 'a') as invalid:
        invalid.write(f'{unparse(invalid_key)}\n')
    with open(GPT4_FILE, 'a') as working2:
        line_count = 0
        for line in lines2:
            if unparse(invalid_key) not in line:
                newline = '\n' if line_count else '' 
                working2.write(f'{newline}{line}')
                line_count += 1
def add_stat(key: str, num = 1):
    """Add +1 to the specified statistic"""
    with open('stats.json', 'r') as stats_file:
        stats = json.loads(stats_file.read())

    with open('stats.json', 'w') as stats_file:
        if not stats.get(key):
            stats[key] = 0

        stats[key] += num
        json.dump(stats, stats_file)
def add_tokens(key: str, tokensnum: int):
    """Add +1 to the specified statistic"""
    with open('tokens.json', 'r') as tokens_file:
        tokens = json.load(tokens_file)
    if not tokens.get(key):
        tokens[key] = 0
    tokens[key] += tokensnum
    with open('tokens.json', 'w') as tokens_out_file:
        json.dump(tokens, tokens_out_file)

def check_token(key):
    with open(USERKEYS_FILE, 'r') as f:
        data = json.load(f)
    for user_id, values in data.items():
        if values['key'] == key:
            return user_id
    
    return False

def add_usage(key:str, prompt, completion):
    """Add the completion and prompt tokens to the user's GPT-4 key usage"""
    with open(USERKEYS_FILE, 'r') as f:
        data = json.load(f)
    for user_id, values in data.items():
        if values['key'] == key:
            values['prompttokens'] += int(prompt)
            values['completiontokens'] += int(completion)
            break  # Exit loop once we have updated the user's data

    with open(USERKEYS_FILE, 'w') as keys_out_file:
        json.dump(data, keys_out_file)  # Write the updated data back to the file
    
def proxy_stream(resp):
    def generate_lines():
        for line in resp.iter_lines():
            if line:
                yield f'{line.decode("utf8")}\n\n'
    return resp.status_code, generate_lines()


def proxy_api(method, content, path, json_data, params, is_stream: bool=False, files=None, auth=None):
    """Makes a request to the official API"""
    actual_path = path.replace('v1/', '')

    if '/' in actual_path:
        try:
            add_stat('*')
            pattern = r"generation(s)?"
            matches = re.findall(pattern, actual_path)
            if not files:
                contentjson = json.loads(content)
                print(contentjson)
                if matches and contentjson.get('prompt'):
                    if 'n' in contentjson:
                        print(contentjson['n'])
                        add_stat(actual_path, contentjson['n'])
                    else:
                        add_stat(actual_path)
                else:
                    add_stat(actual_path)
            else:
                add_stat(actual_path)

                
        except json.JSONDecodeError:
            pass

    while True:
        if not files:
            contentjson = json.loads(content)
        key = get_key_gpt4() if ('gpt-4' in actual_path) or (not files and 'model' in contentjson and 'gpt-4' in contentjson['model']) else get_key()

        try:
            if files:
                print("hi")
                resp = requests.post(f'https://api.openai.com/v1/{actual_path}', headers={
                        'Authorization': f'Bearer {key}',
                }, files=files, params=params)
            else:
                resp = requests.request(
                    method=method,
                    url=f'https://api.openai.com/v1/{actual_path}', 
                    headers={
                        'Authorization': f'Bearer {key}',
                        'Content-Type': 'application/json'
                    },
                    data=content,
                    json=json_data,
                    params=params,
                    
                    timeout=90,
                    stream=is_stream
                )
                print(resp)


        except NotADirectoryError:
            continue

        if is_stream:
            return proxy_stream(resp)
 
        else:
            respjs = resp.json()

            if respjs.get('error'):
                if respjs['error']['code'] == 'invalid_api_key' or 'exceeded' in respjs['error']['message'] or respjs['error']['code'] == 'account_deactivated' or 'Your account is not active' in respjs['error']['message']:
                    invalidate_key(key)
                    return proxy_api(method, content, path, json_data, params, is_stream, files)
            pattern = r"completion(s)?"
            matches = re.findall(pattern, actual_path)
            if not files:
                contentjson = json.loads(content)
                if matches and respjs.get('usage'):
                    patternchat = r"/?chat/?"
                    matcheschat = re.findall(patternchat, actual_path)
                    if 'model' in contentjson:
                        pattern4 = r"gpt-4"
                        matches4 = re.findall(pattern4, contentjson['model'])
                        if matches4:
                            add_tokens('gpt4', respjs['usage']['total_tokens'])
                            if auth:
                                add_usage(auth, respjs['usage']['prompt_tokens'], respjs['usage']['completion_tokens'])
                        elif matcheschat:
                            add_tokens('chat', respjs['usage']['total_tokens'])
                        else:
                            add_tokens('text', respjs['usage']['total_tokens'])

            resp = Response(resp.content, resp.status_code)
            return resp