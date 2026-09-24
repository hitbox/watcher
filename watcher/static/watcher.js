'use scrict';

document.addEventListener("DOMContentLoaded", function() {
    document.querySelector("[data-href]").addEventListener("click", function(event) {
        const target = event.currentTarget;
        window.location.href = target.dataset.href;
    });
});
