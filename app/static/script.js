// Site-wide script (loaded on every page via layout.html).
// Exercise-specific rendering/grading now lives in exercise-engine.js,
// loaded only on the exercise page -- keeping this file free of any
// answer-checking logic (which used to run insecurely in the browser).

document.addEventListener("DOMContentLoaded", function () {
  const languageSelect = document.getElementById("languageSelect");
  if (!languageSelect) return;

  languageSelect.addEventListener("change", function () {
    const selectedLang = this.value;
    document.querySelectorAll("[data-translatable]").forEach((el) => {
      try {
        const translations = JSON.parse(el.getAttribute("data-translations"));
        const translatedText = translations[selectedLang];
        el.innerText = translatedText || el.getAttribute("data-original") || el.innerText;
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
        audios.forEach(other => { if (other !== a) other.pause(); });
      });
    });
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    enableSingleAudioPlayback();
  } else {
    document.addEventListener('DOMContentLoaded', enableSingleAudioPlayback);
  }
})();
