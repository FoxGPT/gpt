document.getElementById('input').addEventListener('keyup', function (event) {
    if (event.key === 'Enter') {
        const output = document.querySelector('#output');
        const prompt = document.getElementById('input').value;

        output.innerHTML = '<img class="loading" src="/static/img/loading.svg" alt="Loading..."/>';

        fetch('/playground/api/image?prompt=' + prompt)
        .then(response => response.text())
        .then(data => {
            output.innerHTML = `<img src="${data}" alt="${prompt}"/>`
        });
    }
});