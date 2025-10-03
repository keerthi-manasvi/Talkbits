import os
import json
from deep_translator import GoogleTranslator

# Define source and target languages
source_lang = 'en'
target_langs = ['ta', 'hi', 'te', 'en']  # Add more if needed

# Path to your lessons folder
lessons_dir = os.path.join('app', 'lessons')

# Loop through all JSON files
for filename in os.listdir(lessons_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(lessons_dir, filename)
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)

        for lesson in data.get('lessons', []):
            for item in lesson.get('content', []):
                source_text = item.get('word') or item.get('text')
                if source_text:
                    item['translations'] = {}
                    for lang in target_langs:
                        try:
                            translated = GoogleTranslator(source=source_lang, target=lang).translate(source_text)
                            item['translations'][f'{lang}-IN'] = translated
                        except Exception:
                            item['translations'][f'{lang}-IN'] = source_text  # fallback

        # Save translated version
        translated_filename = filename.replace('.json', '_translated.json')
        translated_path = os.path.join(lessons_dir, translated_filename)
        with open(translated_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Translated: {translated_filename}")
