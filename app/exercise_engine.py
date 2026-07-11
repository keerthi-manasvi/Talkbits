"""
Server-side grading for every exercise format.

This intentionally replaces the previous approach of rendering the correct
answer into a `data-expected` / `data-correct-option` HTML attribute and
grading it in JavaScript: that exposed every answer in plain view-source,
so anyone could "solve" an exercise without knowing the language. Grading
now happens here, using the same lesson JSON the server already loads --
the client only ever sends what the learner typed/selected/matched, never
sees the key, and gets back a score.
"""
import re


def _normalize(text: str) -> str:
    """Case/whitespace/punctuation-insensitive comparison key."""
    if text is None:
        return ""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _expected_for_type_format(exercise: dict) -> str:
    """
    The 'type' exercise format has no explicit answer field in the content
    JSON -- the expected phrase is encoded directly in the prompt, e.g.
    "Type: How are you?" -> expected = "How are you?"
    """
    prompt = exercise.get('prompt', '')
    if ':' in prompt:
        return prompt.split(':', 1)[1].strip()
    return prompt.strip()


def exercise_key(exercise: dict, index: int) -> str:
    """Stable identifier for storing a score against this exercise within a lesson."""
    return exercise.get('prompt') or exercise.get('question') or f"exercise_{index}"


def grade_exercise(exercise: dict, submitted) -> dict:
    """
    Grade one exercise submission against the server's copy of the lesson data.
    Returns {"correct": bool, "score": 0-100, "detail": str}.
    `submitted` is either a string (fill-in/type/quiz/dialogue) or a dict
    mapping word -> chosen match (for 'match' format).
    """
    fmt = exercise.get('format')

    if fmt in ('fill-in',):
        expected = exercise.get('answer', '')
        correct = _normalize(submitted) == _normalize(expected)
        return {"correct": correct, "score": 100 if correct else 0}

    if fmt == 'type':
        expected = _expected_for_type_format(exercise)
        correct = _normalize(submitted) == _normalize(expected)
        return {"correct": correct, "score": 100 if correct else 0}

    if fmt == 'quiz':
        expected = exercise.get('answer', '')
        correct = _normalize(submitted) == _normalize(expected)
        return {"correct": correct, "score": 100 if correct else 0}

    if fmt == 'dialogue':
        expected = exercise.get('answer', '')
        correct = _normalize(submitted) == _normalize(expected)
        return {"correct": correct, "score": 100 if correct else 0}

    if fmt == 'match':
        pairs = exercise.get('pairs', [])
        if not pairs:
            return {"correct": False, "score": 0}
        correct_map = {p['word']: p['match'] for p in pairs}
        submitted_map = submitted if isinstance(submitted, dict) else {}
        correct_count = sum(
            1 for word, match in correct_map.items()
            if _normalize(submitted_map.get(word, '')) == _normalize(match)
        )
        score = round((correct_count / len(correct_map)) * 100, 1)
        return {"correct": score == 100, "score": score}

    if fmt == 'voice':
        # Speech-to-text scoring happens client-side (Web Speech API) since
        # it needs the microphone/browser recognition result, which the
        # server never receives. The client posts back its own similarity
        # score for aggregation only -- there is no hidden "answer" to leak
        # here, the target phrase is the exercise prompt itself.
        try:
            score = max(0, min(100, float(submitted)))
        except (TypeError, ValueError):
            score = 0
        return {"correct": score >= 80, "score": score}

    return {"correct": False, "score": 0}


def grade_submission(exercises: list, answers: list) -> dict:
    """
    exercises: full list of exercise dicts for the lesson (server-loaded, trusted)
    answers: [{"index": int, "value": <str|dict>}] from the client (untrusted)
    Returns {"results": [...], "score_percent": float, "correct": int, "total": int}
    """
    results = []
    correct_count = 0
    total_score = 0.0

    for answer in answers:
        idx = answer.get('index')
        if idx is None or not (0 <= idx < len(exercises)):
            continue
        exercise = exercises[idx]
        graded = grade_exercise(exercise, answer.get('value'))
        key = exercise_key(exercise, idx)
        results.append({
            "index": idx,
            "prompt": key,
            "correct": graded["correct"],
            "score": graded["score"],
        })
        if graded["correct"]:
            correct_count += 1
        total_score += graded["score"]

    total = len(results)
    score_percent = round(total_score / total, 1) if total else 0.0

    return {
        "results": results,
        "score_percent": score_percent,
        "correct": correct_count,
        "total": total,
    }
