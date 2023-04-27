// Example for using FoxGPT API with OpenAI's official NodeJS package
const { Configuration, OpenAIApi } = require("openai");

const configuration = new Configuration({
  apiKey: "", //get a free key in our discord server!
  basePath: "https://api.hypere.app"

});
const openai = new OpenAIApi(configuration);
// for chat completion
const completion = await openai.createChatCompletion({
  model: "gpt-3.5-turbo",
  messages: [{role: "user", content: "Hello world"}],
});
console.log(completion.data.choices[0].message);

// for text completion
const response = await openai.createCompletion({
  model: "text-davinci-003",
  prompt: "Say this is a test",
  max_tokens: 7,
  temperature: 0,
});
console.log(response.data.choices[0].text);