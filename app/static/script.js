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
  const form = document.querySelector('form');
  const scoreDisplay = document.getElementById('score-display');

  form.addEventListener('submit', (e) => {
    e.preventDefault(); // prevent actual form submission

    let score = 0;
    let total = 0;
    let scoresData = {};

    document.querySelectorAll('[id^="input_"], [id^="input_"]').forEach(input => {
      total++;
      const expected = input.dataset.expected.trim().toLowerCase();
      const correct = input.value.trim().toLowerCase() === expected;
      if (correct) score++;
      scoresData[input.name] = correct ? 1 : 0;
    });


    document.querySelectorAll('input[type="radio"][data-expected]').forEach(radio => {
      if (radio.checked) {
        total++;
        const correct = radio.value === radio.dataset.expected;
        if (correct) score++;
        scoresData[radio.name] = correct ? 1 : 0;
      }
      fetch("", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: new URLSearchParams({ scores: JSON.stringify(scoresData) })
      }).then(res => res.json())
        .then(data => console.log("Scores saved:", data))
        .catch(err => console.error(err));
    });



    scoreDisplay.textContent = `Your score: ${score} / ${total}`;
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

/* ------------------------------
   Voice excercise enhancer
   Appends mic + recognition to any excercise with format == 'voice'
   Works without backend changes. Uses Web Speech API (Chrome best).
   ------------------------------ */
(function () {
  if (!document.querySelector) return;

  function normalizeText(s) {
    if (!s) return '';
    return s.replace(/[^\p{L}\p{N}\s]/gu, '')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  function levenshtein(a, b) {
    if (a === b) return 0;
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;
    const matrix = [];
    for (let i = 0; i <= b.length; i++) matrix[i] = [i];
    for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j] + 1,
            matrix[i][j - 1] + 1,
            matrix[i - 1][j - 1] + 1
          );
        }
      }
    }
    return matrix[b.length][a.length];
  }

  function similarity(a, b) {
    a = normalizeText(a);
    b = normalizeText(b);
    if (!a && !b) return 1;
    if (!a || !b) return 0;
    const dist = levenshtein(a, b);
    const maxLen = Math.max(a.length, b.length);
    return (maxLen === 0) ? 1 : (1 - dist / maxLen);
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  const speechSupported = !!SpeechRecognition;
  const excerciseContainers = Array.from(document.querySelectorAll('.voice-excercise'));
  if (!excerciseContainers.length) return;

  excerciseContainers.forEach((container) => {
    const strong = container.querySelector('strong');
    const p = container.querySelector('p');
    let expectedText = strong?.textContent?.trim() || '';
    if (!expectedText && p && /say[:\s]/i.test(p.textContent))
      expectedText = p.textContent.replace(/say[:\s]/i, '').trim();
    if (!expectedText) return;
    if (container.getAttribute('data-voice-enhanced') === '1') return;
    container.setAttribute('data-voice-enhanced', '1');

    const controlsWrap = document.createElement('div');
    controlsWrap.style.marginTop = '0.5rem';

    const playBtn = document.createElement('button');
    playBtn.type = 'button';
    playBtn.textContent = '▶ Play Prompt';
    playBtn.className = 'play-prompt-btn bg-yellow-500 text-white px-3 py-1 rounded mr-2';

    const startBtn = document.createElement('button');
    startBtn.type = 'button';
    startBtn.textContent = '🎤 Start Speaking';
    startBtn.className = 'start-rec-btn bg-lime-400 text-white px-3 py-1 rounded mr-2';

    const stopBtn = document.createElement('button');
    stopBtn.type = 'button';
    stopBtn.textContent = '⏹ Stop';
    stopBtn.disabled = true;
    stopBtn.className = 'stop-rec-btn bg-red-500 text-white px-3 py-1 rounded';

    const resultP = document.createElement('p');
    resultP.style.marginTop = '0.5rem';

    const feedbackP = document.createElement('p');
    feedbackP.style.fontWeight = '600';
    feedbackP.style.marginTop = '0.25rem';

    controlsWrap.append(playBtn, startBtn, stopBtn);
    container.append(controlsWrap, resultP, feedbackP);

    playBtn.addEventListener('click', function () {
      if (!window.speechSynthesis) return alert('Speech synthesis not supported.');
      const utter = new SpeechSynthesisUtterance(expectedText || '');
      let lang = container.getAttribute('data-lang') || '';
      if (!lang) {
        if (/[ఁ-ఱ]/.test(expectedText)) lang = 'te-IN';
        else if (/[அ-ஔ]/.test(expectedText)) lang = 'ta-IN';
        else if (/[क-ह]/.test(expectedText)) lang = 'hi-IN';
        else lang = 'en-IN';
      }
      utter.lang = lang;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
    });

    if (!speechSupported) {
      startBtn.disabled = true;
      feedbackP.textContent = 'Speech recognition not supported in this browser.';
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    const detectedLang = container.getAttribute('data-lang') || '';
    if (detectedLang) recognition.lang = detectedLang;
    else {
      if (/[ఁ-ఱ]/.test(expectedText)) recognition.lang = 'te-IN';
      else if (/[அ-ஔ]/.test(expectedText)) recognition.lang = 'ta-IN';
      else if (/[क-ह]/.test(expectedText)) recognition.lang = 'hi-IN';
      else recognition.lang = 'en-IN';
    }
    recognition.maxAlternatives = 3;

    startBtn.addEventListener('click', function () {
      resultP.textContent = 'Listening...';
      feedbackP.textContent = '';
      startBtn.disabled = true;
      stopBtn.disabled = false;
      recognition.start();
    });

    stopBtn.addEventListener('click', function () {
      recognition.stop();
    });

    recognition.onresult = function (evt) {
      const transcript = Array.from(evt.results).map(r => r[0].transcript).join(' ').trim();
      resultP.textContent = 'You said: "' + transcript + '"';
      const score = similarity(transcript, expectedText);
      const percent = Math.round(score * 100);

      if (score >= 0.8) {
        feedbackP.textContent = '✅ Correct — ' + percent + '%';
        feedbackP.style.color = 'white';
      } else if (score >= 0.6) {
        feedbackP.textContent = '⚠️ Close — ' + percent + '%';
        feedbackP.style.color = '#b8860b';
      } else {
        feedbackP.textContent = '❌ Try again — ' + percent + '%';
        feedbackP.style.color = 'red';
      }

      startBtn.disabled = false;
      stopBtn.disabled = true;

      // --- Save score to backend ---
      try {
        const meta = document.getElementById('excercise-meta');
        const language = meta ? meta.dataset.language : (document.body.dataset.language || '');
        const lesson = meta ? meta.dataset.lesson : (document.body.dataset.lesson || '');
        fetch('/api/save_score/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || ''
          },
          body: JSON.stringify({
            language: language,
            lesson: lesson,
            prompt: expectedText,
            score: percent
          })
        })
          .then(res => res.json())
          .then(data => {
            if (data && data.success) {
              console.log('✅ Score saved:', data);
            } else {
              console.warn('Save score response:', data);
            }
          })
          .catch(err => console.error('❌ Failed to save score:', err));
      } catch (e) {
        console.error('Error while saving score:', e);
      }
    };

    recognition.onerror = function (ev) {
      resultP.textContent = 'Recognition error: ' + (ev.error || 'unknown');
      feedbackP.textContent = '';
      startBtn.disabled = false;
      stopBtn.disabled = true;
    };

    recognition.onend = function () {
      stopBtn.disabled = true;
      startBtn.disabled = false;
    };
  });
})();

