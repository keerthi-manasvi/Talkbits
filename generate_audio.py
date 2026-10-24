import os
import json
from pathlib import Path
from gtts import gTTS

# CONFIGURATION

BASE_DIR = Path(__file__).resolve().parent.parent  
LESSONS_PATH = BASE_DIR / "app" / "languages" / "lessons"
STATIC_AUDIO_PATH = BASE_DIR / "static" / "audio"
os.makedirs(STATIC_AUDIO_PATH, exist_ok=True)

LANGUAGE_MAP = {
    "english": "en",
    "hindi": "hi",
    "tamil": "ta",
    "telugu": "te",
    "kannada": "kn",
    "malayalam": "ml"
}

# AUDIO GENERATION FUNCTION
def generate_audio_for_text(text, lang_folder, filename, lang_code):
    """Generate an audio file if it doesn't already exist."""
    if not text or text.strip() == "":
        return

    os.makedirs(lang_folder, exist_ok=True)
    filepath = os.path.join(lang_folder, filename)

    if os.path.exists(filepath):
        print(f"Already exists: {filename}")
        return

    try:
        tts = gTTS(text=text.strip(), lang=lang_code)
        tts.save(filepath)
        print(f"Saved: {filename}")
    except Exception as e:
        print(f"Error generating '{filename}' for '{lang_code}': {e}")

# PROCESS SINGLE LESSON FILE
def process_lesson_file(filepath):
    """Generate audio for vocab, phrases, and dialogues per line."""
    language_name = os.path.splitext(os.path.basename(filepath))[0]
    lang_code = LANGUAGE_MAP.get(language_name.lower())

    if not lang_code:
        print(f" Skipping '{language_name}' — language code not found.")
        return

    print(f"\n Generating audio for {language_name} ({lang_code})...")
    lang_folder = os.path.join(STATIC_AUDIO_PATH, language_name)
    os.makedirs(lang_folder, exist_ok=True)

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f" Invalid JSON format in {filepath}")
            return

    lessons = data.get("lessons", [])
    for lesson_index, lesson in enumerate(lessons, start=1):
        for item_index, item in enumerate(lesson.get("content", []), start=1):

            # For vocab and phrase items
            if item.get("type") in ["vocab", "phrase"]:
                text_to_speak = item.get("word") or item.get("text") or item.get("example", "")
                filename = item.get("audio") or f"lesson{lesson_index}_item{item_index}.mp3"
                generate_audio_for_text(text_to_speak, lang_folder, filename, lang_code)
                continue

            # For dialogue items
            if item.get("type") == "dialogue":
                for line_index, line in enumerate(item.get("lines", []), start=1):
                    text = line.get("text")
                    audio_file = line.get("audio") or f"lesson{lesson_index}_item{item_index}_line{line_index}.mp3"
                    generate_audio_for_text(text, lang_folder, audio_file, lang_code)

# MAIN FUNCTION
def main():
    print(" Starting audio generation for all languages...")

    if not os.path.exists(LESSONS_PATH):
        print(f" Lessons folder not found: {LESSONS_PATH}")
        return

    json_files = [f for f in os.listdir(LESSONS_PATH) if f.endswith(".json")]
    if not json_files:
        print(f" No JSON lesson files found in {LESSONS_PATH}")
        return

    for filename in json_files:
        filepath = os.path.join(LESSONS_PATH, filename)
        process_lesson_file(filepath)

    print("\n Audio generation complete!")

# ENTRY POINT
if __name__ == "__main__":
    main()
