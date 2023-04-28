// I haven't tested this.
// Let me know if it works.

import { Configuration, OpenAIApi } from "azure-openai"; 

openAiApi = new OpenAIApi(
    new Configuration({
       apiKey: '', // set this to the key you get when running /key in the discord
       azure: {
          apiKey: '' , //get a free key in our discord server by running the slash command /key!
          endpoint: 'https://api.hypere.app',
       }
    }),
);

const response = await openAiApi.createCompletion({
    prompt: 'Roses are red, '
});

console.log(response.data.choices[0].text);
