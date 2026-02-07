document.addEventListener("DOMContentLoaded", () => {

    const form = document.querySelector("form");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const result = calculateScore();
        document.getElementById("score-display").innerText =
            `Score: ${result.score} / ${result.total}`;

        await sendScore(result);
    });

    function normalizeText(text) {
        return text.trim().normalize("NFC");
    }

    function isCorrect(user, correct) {
        return normalizeText(user) === normalizeText(correct);
    }

    function calculateScore() {
        let score = 0;
        let total = 0;

        /* ---- FILL-IN / TYPE ---- */
        document.querySelectorAll(".excercise-input").forEach(input => {
            total++;
            if (isCorrect(input.value, input.dataset.answer)) score++;
        });

        /* ---- QUIZ ---- */
        document.querySelectorAll(".excercise-quiz").forEach(quiz => {
            total++;
            const selected = quiz.querySelector("input[type=radio]:checked");
            if (selected && isCorrect(selected.value, quiz.dataset.answer)) {
                score++;
            }
        });

        /* ---- MATCH ---- */
        document.querySelectorAll(".matched").forEach(pair => {
            total++;
            if (pair.dataset.correct === "true") score++;
        });

        return { score, total };
    }

    async function sendScore({ score, total }) {
        const meta = document.getElementById("excercise-meta");

        const payload = {
            language: meta.dataset.language,
            unit: meta.dataset.unit,
            lesson: meta.dataset.lesson,
            score,
            total
        };
        console.log("score" + score)

        await fetch(`/api/submit-score/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector(
                    "[name=csrfmiddlewaretoken]"
                ).value
            },
            body: JSON.stringify(payload)
        });
    }
});
