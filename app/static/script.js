document.addEventListener("DOMContentLoaded", function () {
    const languageSelect = document.getElementById("languageSelect");

    if (!languageSelect) return;

    languageSelect.addEventListener("change", function () {
        const selectedLang = this.value;

        document.querySelectorAll("[data-translatable]").forEach(el => {
            try {
                const translations = JSON.parse(el.getAttribute("data-translations"));
                const translatedText = translations[selectedLang];

                if (translatedText) {
                    el.innerText = translatedText;
                } else {
                    el.innerText = el.getAttribute("data-original") || el.innerText;
                }
            } catch (e) {
                console.warn("Invalid translation data:", e);
            }
        });
    });
});