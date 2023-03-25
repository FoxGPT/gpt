# Run the following to command to make sure
# you have the latest version of the OpenAI Python library:
# pip install --upgrade openai

import openai

openai.api_key = '' # leave this empty or set it to anything
openai.api_base = 'https://gpt.bot.nu' # really important

# use the OpenAI API like you normally would

completion = openai.Completion.create(
    engine='text-davinci-003',
    prompt='Roses are red, '
)

print(completion.choices[0].text)
