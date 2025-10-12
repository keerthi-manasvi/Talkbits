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

/* ------------------------------
   Voice Exercise enhancer
   Appends mic + recognition to any exercise with format == 'voice'
   Works without backend changes. Uses Web Speech API (Chrome best).
   ------------------------------ */

(function () {
  // Only run on pages with exercises
  if (!document.querySelector) return;

  // Helper: normalize strings (remove punctuation, spaces, lowercase)
  function normalizeText(s) {
    if (!s) return '';
    return s.replace(/[^\p{L}\p{N}\s]/gu, '') // remove punctuation (unicode-aware)
            .replace(/\s+/g, ' ')
            .trim()
            .toLowerCase();
  }

  // Levenshtein distance (for similarity)
  function levenshtein(a, b) {
    if (a === b) return 0;
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;
    const matrix = [];
    for (let i = 0; i <= b.length; i++) {
      matrix[i] = [i];
    }
    for (let j = 0; j <= a.length; j++) {
      matrix[0][j] = j;
    }
    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j] + 1,    // deletion
            matrix[i][j - 1] + 1,    // insertion
            matrix[i - 1][j - 1] + 1 // substitution
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

  // Feature detection for Web Speech API
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  const speechSupported = !!SpeechRecognition;

  // Find voice-format exercise blocks: we rely on the template structure
  // Each exercise block in the template contains the prompt and expected text.
  // We'll scan for nodes that contain text like "Say: <expected>" or where ex.format == 'voice'
  // To be robust we search for elements that contain the expected text inside
const exerciseContainers = Array.from(document.querySelectorAll('.voice-exercise'));
  if (!exerciseContainers.length) return; // nothing to do

  exerciseContainers.forEach((container) => {
    // Try to detect if this is a voice exercise block by looking for "Say:" label or <strong> expected text
    const italicNode = container.querySelector('p.italic') || container.querySelector('p');
    let expectedText = null;

    // If the template used <p class="mt-2 italic">Say: <strong>{{ ex.expected }}</strong></p>
    const strong = container.querySelector('strong');
    if (strong && strong.textContent && strong.textContent.trim().length > 0) {
      expectedText = strong.textContent.trim();
    } else {
      // fallback: try to parse any "Say:" prefix
      const p = container.querySelector('p');
      if (p && p.textContent && /say[:\s]/i.test(p.textContent)) {
        expectedText = p.textContent.replace(/say[:\s]/i, '').trim();
      }
    }

    if (!expectedText) {
      // not a voice exercise block
      return;
    }

    // Avoid double-inserting if we ran already
    if (container.getAttribute('data-voice-enhanced') === '1') return;
    container.setAttribute('data-voice-enhanced', '1');

    // Build UI elements
    const controlsWrap = document.createElement('div');
    controlsWrap.style.marginTop = '0.5rem';

    const playBtn = document.createElement('button');
    playBtn.type = 'button';
    playBtn.textContent = '▶ Play Prompt';
    playBtn.className = 'play-prompt-btn bg-white-500 text-white px-3 py-1 rounded mr-2';

    const startBtn = document.createElement('button');
    startBtn.type = 'button';
    startBtn.textContent = '🎤 Start Speaking';
    startBtn.className = 'start-rec-btn bg-white-600 text-white px-3 py-1 rounded mr-2';

    const stopBtn = document.createElement('button');
    stopBtn.type = 'button';
    stopBtn.textContent = '⏹ Stop';
    stopBtn.disabled = true;
    stopBtn.className = 'stop-rec-btn bg-red-500 text-white px-3 py-1 rounded';

    const resultP = document.createElement('p');
    resultP.textContent = '';
    resultP.style.marginTop = '0.5rem';

    const feedbackP = document.createElement('p');
    feedbackP.style.fontWeight = '600';
    feedbackP.style.marginTop = '0.25rem';

    // Append controls after the prompt area
    controlsWrap.appendChild(playBtn);
    controlsWrap.appendChild(startBtn);
    controlsWrap.appendChild(stopBtn);
    container.appendChild(controlsWrap);
    container.appendChild(resultP);
    container.appendChild(feedbackP);

    // Play prompt using speechSynthesis (if available)
    playBtn.addEventListener('click', function () {
      if (!window.speechSynthesis) {
        alert('Speech synthesis is not supported in this browser.');
        return;
      }
      const utter = new SpeechSynthesisUtterance(expectedText || '');
      // Attempt to pick language from container: if the template stored lang attribute somewhere, use it.
      // If not available, default to en-IN (change as needed).
      let lang = container.getAttribute('data-lang') || '';
      if (!lang) {
        // if expected text contains Telugu characters, set te-IN heuristically
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
      feedbackP.textContent = 'Speech recognition not supported in this browser. Use Chrome.';
      return;
    }

    // Build recognition instance
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    // Try to pick language: check data-lang attribute, otherwise infer
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
      try {
        resultP.textContent = 'Listening...';
        feedbackP.textContent = '';
        startBtn.disabled = true;
        stopBtn.disabled = false;
        recognition.start();
      } catch (e) {
        console.error('Recognition start error', e);
        resultP.textContent = 'Could not start recognition: ' + (e.message || e);
        startBtn.disabled = false;
        stopBtn.disabled = true;
      }
    });

    stopBtn.addEventListener('click', function () {
      try {
        recognition.stop();
      } catch (e) {
        console.warn('stop error', e);
      }
    });

    recognition.onresult = function (evt) {
      const transcript = Array.from(evt.results)
                              .map(r => r[0].transcript)
                              .join(' ')
                              .trim();
      resultP.textContent = 'You said: "' + transcript + '"';

      // Compute similarity client-side
      const score = similarity(transcript, expectedText);
      const percent = Math.round(score * 100);

      if (score >= 0.80) {
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

      // Optional: send to backend scoring endpoint if you have /api/check_answer/
      // If you DO have that endpoint uncomment the fetch below:
      /*
      fetch('/api/check_answer/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          transcript: transcript,
          expected: expectedText,
          lang: recognition.lang,
          exercise_id: container.getAttribute('data-ex-id') || ''
        })
      }).then(r => r.json()).then(data => {
        // handle server score if you want to use that instead
        console.log('server scoring result', data);
      }).catch(err => console.warn('server scoring failed', err));
      */
    };

    recognition.onerror = function (ev) {
      console.error('Recognition error', ev);
      resultP.textContent = 'Recognition error: ' + (ev.error || 'unknown');
      feedbackP.textContent = '';
      startBtn.disabled = false;
      stopBtn.disabled = true;
    };

    recognition.onend = function () {
      // ensure buttons state consistent
      stopBtn.disabled = true;
      startBtn.disabled = false;
    };
  });

})();