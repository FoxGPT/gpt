// I haven't tested this.
// Let me know if it works.

import { Configuration, OpenAIApi } from "azure-openai"; 

openAiApi = new OpenAIApi(
    new Configuration({
       apiKey: '',
       azure: {
          apiKey: '',
          endpoint: 'https://gpt.bot.nu',
       }
    }),
);

const response = await openAiApi.createCompletion({
    prompt: 'Roses are red, '
});

console.log(response.data.choices[0].text);