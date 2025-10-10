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

// --- Audio Playback Control: ensure only one audio plays at a time ---
(function () {
  function enableSingleAudioPlayback() {
    const audios = Array.from(document.querySelectorAll('audio'));
    audios.forEach(a => {
      a.addEventListener('play', () => {
        audios.forEach(other => {
          if (other !== a) other.pause();
        });
      });
    });
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    enableSingleAudioPlayback();
  } else {
    document.addEventListener('DOMContentLoaded', enableSingleAudioPlayback);
  }
})();
