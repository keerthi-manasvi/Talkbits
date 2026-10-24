import os
import json
from deep_translator import GoogleTranslator
from pathlib import Path

# Config
# use : build_index from_language to_language
FROM_LANG = sys.argv[1].lower() if len(sys.argv) > 2 
TO_LANG = sys.argv[2].lower() if len(sys.argv) > 2 

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INPUT_FILE = BASE_DIR / "languages" / "lessons" / f"{FROM_LANG}.json"
TARGET_LANG = TO_LANG
OUTPUT_FILE = BASE_DIR / "languages" / "lessons" / f"{FROM_LANG}_translated_to_{TO_LANG}.json"

# Fields that are normally text fields
TEXT_FIELDS = ["word", "prompt", "text", "response", "example", "question", "answer"]

# Corresponding flags that determine if they should be translated
TRANSLATABLE_FLAGS = {
    "word": "translatable",
    "prompt": "prompt_translatable",
    "text": "translatable",
    "response": "translatable",
    "example": "example_translatable",
    "question": "translatable",
    "answer": "translatable"
}

# Helper function
def translate_text(text, src_lang="auto", target_lang=TARGET_LANG):
    """Translate a single string using GoogleTranslator."""
    try:
        translated = GoogleTranslator(source=src_lang, target=target_lang).translate(text)
        return translated
    except Exception as e:
        print(f"Failed to translate '{text}': {e}")
        return text  # fallback to original text

def translate_item(item):
    """Translate only the fields marked as translatable."""
    for field in TEXT_FIELDS:
        flag = TRANSLATABLE_FLAGS.get(field)
        if flag and item.get(flag) and field in item and item[field]:
            item[field] = translate_text(item[field])

    # Handle dialogue lines
    if item.get("type") == "dialogue" and "lines" in item:
        for line in item["lines"]:
            # Translate only if line is marked translatable
            if line.get("translatable") and "text" in line and line["text"]:
                line["text"] = translate_text(line["text"])
    return item

# Main logic
if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        exit(1)

    # Load original lesson file
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Translate each lesson item
    for lesson in data.get("lessons", []):
        for idx, item in enumerate(lesson.get("content", [])):
            lesson["content"][idx] = translate_item(item)

    # Save translated file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f" Translation completed! Saved to {OUTPUT_FILE}")
