document.addEventListener('DOMContentLoaded', function () {
    // Blur the date picker input fields after selection
    document.querySelectorAll('.DateInput_input').forEach(function (el) {
        el.addEventListener('focus', function () {
            el.blur();
        });
    });

    // Blur the dropdown input fields after selection
    document.querySelectorAll('.Select-input').forEach(function (el) {
        el.addEventListener('focus', function () {
            el.blur();
        });
    });
});