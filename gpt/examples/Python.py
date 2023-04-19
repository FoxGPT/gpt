# Run the following to command to make sure
# you have the latest version of the OpenAI Python library:
# pip install --upgrade openai

import openai

openai.api_key = '' # set this to the key you get when running /key in the discord
openai.api_base = 'https://api.hypere.app' # really important

# use the OpenAI API like you normally would

completion = openai.Completion.create(
    engine='text-davinci-003',
    prompt='Roses are red, '
)

print(completion.choices[0].text)
