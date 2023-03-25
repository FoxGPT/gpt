document.addEventListener('DOMContentLoaded', function () {
    var tabs = document.querySelectorAll('.tab-list a');
    var tabContents = document.querySelectorAll('.tab-content > div');

    function displayTab(tabIndex) {
        tabs.forEach(function (tab) {
            tab.classList.remove('active');
        });
        tabContents.forEach(function (tabContent) {
            tabContent.style.display = 'none';
        });

        tabs[tabIndex].classList.add('active');
        tabContents[tabIndex].style.display = 'block';
        Prism.highlightAll();
    }

    tabs.forEach(function (tab, i) {
        tab.addEventListener('click', function (event) {
            event.preventDefault();
            displayTab(i);
        });
    });

    displayTab(0);

    // copy button

    var copyButton = document.getElementById('copy-button');

    copyButton.addEventListener('click', function (event) {
        copyButton.children[0].classList = 'bi bi-clipboard-check';

        // set code to the pre where the parent is display: block
        var code = document.querySelector('.tab-content > div[style="display: block;"] pre').innerText;

        navigator.clipboard.writeText(code);
    });

    // counter
    // find all elements starting with stats-
    function updateCounter() {
        var stats = document.querySelectorAll('[id^="stats-"]');

        // for each element, get the id and use it to get the value from the API
        stats.forEach(function (stat) {
            var id = stat.id;
            var url = '/stats/' + id.replace('stats-', '');
            fetch(url)
                .then(function (response) {
                    return response.json();
                })
                .then(function (data) {
                    document.getElementById(id).innerText = data.value;
                });
        });
    };

    updateCounter();
    setInterval(updateCounter, 1000);
});