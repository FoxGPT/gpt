import json
import os
import random


with open('config.json', 'r') as file:
    config = json.load(file)

class Key:

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

    WORKING_FILE = os.getenv('WORKING_FILE') or config.get('WORKING_FILE')
    GPT4_FILE = os.getenv('GPT4_FILE') or config.get('GPT4_FILE')

    # This file will be used to store the invalid keys.
    # Don't worry about it, it will be created automatically.
    INVALID_FILE = os.getenv('INVALID_FILE') or config.get('INVALID_FILE')
    USERKEYS_FILE = os.getenv('USERKEYS_FILE') or config.get('USERKEYS_FILE')
    STATS_AUTH = os.getenv('STATS_AUTH') or config.get('STATS_AUTH')
    BLOCK_AUTH = os.getenv('BLOCK_AUTH') or config.get('BLOCK_AUTH')
    PLAYGROUND_KEY = os.getenv('PLAYGROUND_KEY') or config.get('PLAYGROUND_KEY')

    def __init__(self, key: str):
        self.key = key
            
    def invalidate_key(self) -> None:
        """Moves an invalid key to another file for invalid keys."""

        with open(Key.WORKING_FILE, 'w') as file:
            pass

        with open(Key.GPT4_FILE, 'w') as file:
            pass

        with open(Key.WORKING_FILE, 'a+') as file:
            lines = file.read().splitlines()
            for line in lines:
                if self.key not in line:
                    newline = '\n' if lines.index(line) != 0 else ''
                    file.write(f'{newline}{line}')

        with open(Key.GPT4_FILE, 'a+') as file:
            lines = file.read().splitlines()
            for line in lines:
                if self.key not in line:
                    newline = '\n' if lines.index(line) != 0 else ''
                    file.write(f'{newline}{line}')

        with open(Key.INVALID_FILE, 'a') as invalid:
            invalid.write(f'{self.key}\n')

    def lock_key(self):
        """Lock a key in a .lock file so that it can't be used for another request at the same time."""
        with open(f'locks/{self.key}.lock', 'w') as lock_file:
            lock_file.write('locked')
            print(f'Locked {self.key}!')

    def unlock_key(self):
        """Unlock a key in a .lock file so that it can be used for another request. if the file doesn't exist, ignore it."""
        try:
            os.remove(f'locks/{self.key}.lock')
        # catch error if file doesn't exist.
        except FileNotFoundError:
            pass

    def check_lock(self) -> bool:
        """Check if a key is locked."""
        return os.path.exists(f'locks/{self.key}.lock')

    def add_stat(self, num = 1):
        """Add +1 to the specified statistic"""
        with open('stats.json', 'r') as stats_file:
            stats = json.loads(stats_file.read())

        with open('stats.json', 'w') as stats_file:
            if not stats.get(self.key):
                stats[self.key] = 0

            stats[self.key] += num
            json.dump(stats, stats_file)

    def add_tokens(self, tokensnum: int):
        """Add +1 to the specified statistic"""
        with open('tokens.json', 'r') as tokens_file:
            tokens = json.load(tokens_file)
        if not tokens.get(self.key):
            tokens[self.key] = 0
        tokens[self.key] += tokensnum
        with open('tokens.json', 'w') as tokens_out_file:
            json.dump(tokens, tokens_out_file)

    def check_token(self):
        with open(Key.USERKEYS_FILE, 'r') as f:
            data = json.load(f)
        for user_id, values in data.items():
            if values['key'] == self.key:
                return user_id
        
        return False

    def add_usage(self, prompt, completion):
        """Add the completion and prompt tokens to the user's GPT-4 key usage"""
        with open(Key.USERKEYS_FILE, 'r') as f:
            data = json.load(f)
        for user_id, values in data.items():
            if values['key'] == self.key:
                values['prompttokens'] += int(prompt)
                values['completiontokens'] += int(completion)
                break  # Exit loop once we have updated the user's data

        with open(Key.USERKEYS_FILE, 'w') as keys_out_file:
            json.dump(data, keys_out_file)  # Write the updated data back to the file

    def get_key(type: str) -> str:
        """Get a random key from the working file."""

        if type == 'gpt3':
            with open(Key.WORKING_FILE, encoding='utf8') as keys_file:
                keys = keys_file.read().splitlines()

            while True:
                key: Key = random.choice(keys)
                if not key.check_lock():
                    key.lock_key()
                    return key
        elif type == 'gpt4':
            with open(Key.GPT4_FILE, encoding='utf8') as keys_file:
                keys = keys_file.read().splitlines()
            return random.choice(keys)
        