// for node.js, just un-comment the following line:
// import fetch from 'node-fetch';

fetch('https://api.hypere.app/engines/text-davinci-003/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' //get a free key in our discord server!
  },
  // body: '{\n      "prompt": "Roses are red, "\n   }',
  body: JSON.stringify({
    'prompt': 'Roses are red, '
  })
});