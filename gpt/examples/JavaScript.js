// for node.js, just un-comment the following line:
// import fetch from 'node-fetch';

fetch('https://gpt.bot.nu/engines/text-davinci-003/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  // body: '{\n      "prompt": "Roses are red, "\n   }',
  body: JSON.stringify({
    'prompt': 'Roses are red, '
  })
});