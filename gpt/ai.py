import os
import json
import random
import requests
import re
from keys import Key
from dotenv import load_dotenv
load_dotenv()
from flask import Response

def proxy_stream(resp):
    def generate_lines():
        for line in resp.iter_lines():
            if line:
                yield f'{line.decode("utf8")}\n\n'
    return resp.status_code, generate_lines()

def add_ip_tokens(ip, num_tokens):
    with open('iptokens.json', 'r') as tokens_file:
        tokens = json.load(tokens_file)
    if not tokens.get(ip):
        tokens[ip] = {"tokens": 0, "requests": 0} # set default number of requests to 0
    tokens[ip]["tokens"] += num_tokens
    tokens[ip]["requests"] += 1
    with open('iptokens.json', 'w') as tokens_out_file:
        json.dump(tokens, tokens_out_file, separators=(',', ':'))

def proxy_api(method, content, path, json_data, params, is_stream: bool=False, files=None, auth=None, ip=None):
    """Makes a request to the official API"""
    actual_path = path.replace('v1/', '')

    if '/' in actual_path:
        try:
            Key('*').add_stat()
            pattern = r"generation(s)?"
            matches = re.findall(pattern, actual_path)
            key: Key = actual_path
            if not files:
                contentjson = json.loads(content)
                print(contentjson)
                if matches and contentjson.get('prompt'):
                    if 'n' in contentjson:
                        print(contentjson['n'])
                        key.add_stat(contentjson['n'])
                    else:
                        key.add_stat()
                else:
                    key.add_stat()
            else:
                key.add_stat()

                
        except json.JSONDecodeError:
            pass

    while True:
        if not files:
            contentjson = json.loads(content)
        key: Key = Key.get_key('gpt4') if ('gpt-4' in actual_path) or (not files and 'model' in contentjson and 'gpt-4' in contentjson['model']) else Key.get_key('gpt3')

        try:
            if files:
                resp = requests.post(f'https://api.openai.com/v1/{actual_path}', headers={
                        'Authorization': f'Bearer {key}',
                }, files=files, params=params, timeout=360)
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
                    
                    timeout=360,
                    stream=is_stream
                )


        except NotADirectoryError:
            continue

        if is_stream:
            key.unlock_key()
            return proxy_stream(resp)
        else:
            key.unlock_key()

            respjs = resp.json()
            if respjs.get('error'):
                if respjs['error']['code'] == 'invalid_api_key' or 'exceeded' in respjs['error']['message'] or respjs['error']['code'] == 'account_deactivated' or 'Your account is not active' in respjs['error']['message']:
                    key.invalidate_key()
                    return proxy_api(method, content, path, json_data, params, is_stream, files)
            matches = re.findall(r"completion(s)?", actual_path)
            if not files:
                contentjson = json.loads(content)
                if matches and respjs.get('usage'):
                    matcheschat = re.findall(r"/?chat/?", actual_path)
                    if auth:
                        key.add_usage(respjs['usage']['prompt_tokens'], respjs['usage']['completion_tokens'])
                    if 'model' in contentjson:
                        matchesgpt = re.findall(r"gpt-4", contentjson['model'])
                        if matchesgpt:
                            Key('gpt4').add_tokens(respjs['usage']['total_tokens'])
                        elif matcheschat:
                            Key('chat').add_tokens(respjs['usage']['total_tokens'])
                            if ip:
                                add_ip_tokens(ip, respjs['usage']['total_tokens'])
                        else:
                            Key('text').add_tokens(respjs['usage']['total_tokens'])
                            if ip:
                                add_ip_tokens(ip, respjs['usage']['total_tokens'])

            resp = Response(resp.content, resp.status_code)
            return resp
        
