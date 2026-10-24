/**
 * Interactive exercise engine.
 * Renders every exercise format from the safe (answer-stripped) JSON payload
 * the server embedded in the page, collects the learner's answers, and posts
 * them to the server for grading. The server is the only place that ever
 * sees the correct answers -- this file never compares against a key.
 */
(function () {
  const meta = document.getElementById('exercise-meta');
  const dataEl = document.getElementById('exercises-data');
  const root = document.getElementById('exercise-root');
  if (!meta || !dataEl || !root) return;

  const submitUrl = meta.dataset.submitUrl;
  const exercises = JSON.parse(dataEl.textContent || '[]');

  // answer store: index -> value (string, or {word: chosenMatch} for 'match')
  const answers = {};

  function csrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function renderFillIn(ex) {
    const card = el('div', 'bg-white border-2 border-brand-brown/15 p-4 rounded-lg');
    card.append(el('p', 'font-medium text-brand-brown', ex.prompt));
    const input = el('input', 'border-2 border-brand-brown/20 rounded-lg px-3 py-2 w-full mt-2');
    input.type = 'text';
    input.placeholder = ex.hint || 'Your answer';
    input.addEventListener('input', () => { answers[ex.index] = input.value; });
    card.append(input);
    return card;
  }

  function renderType(ex) {
    const card = el('div', 'bg-white border-2 border-brand-brown/15 p-4 rounded-lg');
    card.append(el('p', 'font-medium text-brand-brown', ex.prompt));
    const input = el('input', 'border-2 border-brand-brown/20 rounded-lg px-3 py-2 w-full mt-2');
    input.type = 'text';
    input.placeholder = 'Type what you hear/read above';
    input.addEventListener('input', () => { answers[ex.index] = input.value; });
    card.append(input);
    return card;
  }

  function renderQuiz(ex) {
    const card = el('div', 'bg-white border-2 border-brand-brown/15 p-4 rounded-lg');
    card.append(el('p', 'font-medium text-brand-brown', ex.question));
    (ex.options || []).forEach((opt, i) => {
      const label = el('label', 'block mt-2 cursor-pointer text-brand-brown');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = `quiz_${ex.index}`;
      radio.value = opt;
      radio.className = 'mr-2';
      radio.addEventListener('change', () => { answers[ex.index] = opt; });
      label.append(radio, document.createTextNode(opt));
      card.append(label);
    });
    return card;
  }

  function renderDialogue(ex) {
    const card = el('div', 'bg-white border-2 border-brand-brown/15 p-4 rounded-lg');
    card.append(el('p', 'font-medium text-brand-brown', ex.prompt));
    const input = el('input', 'border-2 border-brand-brown/20 rounded-lg px-3 py-2 w-full mt-2');
    input.type = 'text';
    input.placeholder = ex.hint || 'Complete the dialogue';
    input.addEventListener('input', () => { answers[ex.index] = input.value; });
    card.append(input);
    return card;
  }

  function renderMatch(ex) {
    const card = el('div', 'bg-cream border-2 border-brand-brown/15 p-4 rounded-lg');
    card.append(el('p', 'font-medium text-brand-brown mb-2', ex.prompt));
    const chosen = {};
    answers[ex.index] = chosen;

    (ex.words || []).forEach((word) => {
      const row = el('div', 'flex items-center justify-between gap-3 mt-2 bg-white p-2 rounded-lg');
      row.append(el('span', 'text-brand-brown', word));
      const select = document.createElement('select');
      select.className = 'border-2 border-brand-brown/20 rounded-lg px-2 py-1';
      select.append(el('option', '', '-- choose --'));
      (ex.options || []).forEach((opt) => select.append(el('option', '', opt)));
      select.addEventListener('change', () => { chosen[word] = select.value; });
      row.append(select);
      card.append(row);
    });
    return card;
  }

  function renderVoice(ex) {
    const card = el('div', 'voice-exercise bg-cream border-2 border-brand-brown/15 p-4 rounded-lg');
    card.setAttribute('data-index', ex.index);
    card.setAttribute('data-lang', ex.lang || '');
    card.append(el('p', 'italic text-brand-brown', 'Say: ' + (ex.expected || '')));
    // Playback / recording controls + Web Speech scoring are attached by
    // enhanceVoiceExercises() below (kept separate since it depends on
    // browser Speech APIs that may not exist).
    return card;
  }

  const RENDERERS = {
    'fill-in': renderFillIn,
    'type': renderType,
    'quiz': renderQuiz,
    'dialogue': renderDialogue,
    'match': renderMatch,
    'voice': renderVoice,
  };

  exercises.forEach((ex) => {
    const renderer = RENDERERS[ex.format];
    if (renderer) root.append(renderer(ex));
  });

  enhanceVoiceExercises();
  enableSingleAudioPlayback();

  // ---- Submission -----------------------------------------------------
  const submitBtn = document.getElementById('submit-exercises-btn');
  submitBtn.addEventListener('click', () => {
    const payload = {
      answers: Object.keys(answers).map((idx) => ({
        index: Number(idx),
        value: answers[idx],
      })),
    };

    submitBtn.disabled = true;
    submitBtn.textContent = 'Grading...';

    fetch(submitUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
      },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Exercises';
        if (data.error) {
          alert(data.error);
          return;
        }
        showScoreModal(data);
      })
      .catch((err) => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Exercises';
        console.error('Failed to submit exercises:', err);
        alert('Something went wrong submitting your answers. Please try again.');
      });
  });

  function showScoreModal(data) {
    const modal = document.getElementById('score-modal');
    document.getElementById('score-modal-percent').textContent = data.score_percent;
    document.getElementById('score-modal-detail').textContent =
      `${data.correct} / ${data.total} correct`;
    document.getElementById('score-modal-emoji').textContent =
      data.score_percent >= 80 ? '🎉' : data.score_percent >= 50 ? '👍' : '💪';
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  document.getElementById('score-modal-close').addEventListener('click', () => {
    const modal = document.getElementById('score-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  });

  // ---- Shared helpers (audio + voice recognition) ----------------------
  function enableSingleAudioPlayback() {
    const audios = Array.from(document.querySelectorAll('audio'));
    audios.forEach((a) => {
      a.addEventListener('play', () => {
        audios.forEach((other) => { if (other !== a) other.pause(); });
      });
    });
  }

  function normalizeText(s) {
    if (!s) return '';
    return s.replace(/[^\p{L}\p{N}\s]/gu, '').replace(/\s+/g, ' ').trim().toLowerCase();
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
        matrix[i][j] = b.charAt(i - 1) === a.charAt(j - 1)
          ? matrix[i - 1][j - 1]
          : Math.min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + 1);
      }
    }
    return matrix[b.length][a.length];
  }

  function similarity(a, b) {
    a = normalizeText(a); b = normalizeText(b);
    if (!a && !b) return 1;
    if (!a || !b) return 0;
    const dist = levenshtein(a, b);
    return 1 - dist / Math.max(a.length, b.length);
  }

  function enhanceVoiceExercises() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
    const speechSupported = !!SpeechRecognition;
    const containers = Array.from(document.querySelectorAll('.voice-exercise'));

    containers.forEach((container) => {
      const idx = container.getAttribute('data-index');
      const expectedText = exercises[idx] ? (exercises[idx].expected || '') : '';
      if (!expectedText) return;

      const controlsWrap = el('div', 'mt-2 flex gap-2 flex-wrap');
      const playBtn = el('button', 'btn-start text-sm px-3 py-1', '▶ Play Prompt');
      playBtn.type = 'button';
      const startBtn = el('button', 'bg-brand-yellow text-brand-brown font-semibold px-3 py-1 rounded-full text-sm hover:scale-105 transition-all', '🎤 Start Speaking');
      startBtn.type = 'button';
      const stopBtn = el('button', 'bg-brand-brown text-cream font-semibold px-3 py-1 rounded-full text-sm opacity-50', '⏹ Stop');
      stopBtn.type = 'button';
      stopBtn.disabled = true;

      const resultP = el('p', 'mt-2 text-brand-brown');
      const feedbackP = el('p', 'font-semibold mt-1');

      controlsWrap.append(playBtn, startBtn, stopBtn);
      container.append(controlsWrap, resultP, feedbackP);

      playBtn.addEventListener('click', () => {
        if (!window.speechSynthesis) return alert('Speech synthesis not supported.');
        const utter = new SpeechSynthesisUtterance(expectedText);
        utter.lang = container.getAttribute('data-lang') || 'en-IN';
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
      recognition.lang = container.getAttribute('data-lang') || 'en-IN';
      recognition.maxAlternatives = 3;

      startBtn.addEventListener('click', () => {
        resultP.textContent = '';
        feedbackP.textContent = '';
        startBtn.disabled = true;
        stopBtn.disabled = false;
        recognition.start();
      });

      stopBtn.addEventListener('click', () => recognition.stop());

      recognition.onresult = (evt) => {
        const transcript = Array.from(evt.results).map((r) => r[0].transcript).join(' ').trim();
        resultP.textContent = `You said: "${transcript}"`;
        const score = similarity(transcript, expectedText);
        const percent = Math.round(score * 100);

        if (score >= 0.8) { feedbackP.textContent = ` Correct — ${percent}%`; feedbackP.style.color = 'green'; }
        else if (score >= 0.6) { feedbackP.textContent = ` Close — ${percent}%`; feedbackP.style.color = '#b8860b'; }
        else { feedbackP.textContent = ` Try again — ${percent}%`; feedbackP.style.color = 'red'; }

        startBtn.disabled = false;
        stopBtn.disabled = true;

        // Record this exercise's score so it's included in the lesson submission.
        answers[idx] = percent;
      };

      recognition.onerror = (ev) => {
        resultP.textContent = 'Recognition error: ' + (ev.error || 'unknown');
        feedbackP.textContent = '';
        startBtn.disabled = false;
        stopBtn.disabled = true;
      };

      recognition.onend = () => { stopBtn.disabled = true; startBtn.disabled = false; };
    });
  }
})();
