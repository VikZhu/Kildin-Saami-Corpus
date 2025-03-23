import json
import re
import spacy

# Загружаем модель SpaCy для русского языка
nlp = spacy.load("ru_core_news_sm")

def clean_gloss(gloss):
    """Удаляет часть после `-` или `,` в глоссе"""
    return re.split("[-.?]", gloss)[0]

def get_pos(word):
    """Определяет часть речи слова"""
    doc = nlp(word)
    return doc[0].pos_ if doc else "unknown"

def convert_output_to_flex(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        output_data = json.load(f)
    
    converted_data = {
        "meta": {
            "title": "Переведенный корпус",
            "filename": "corpus/xml/output_converted.xml"
        },
        "sentences": []
    }
    
    for key, sentence in output_data.items():
        sentence_obj = {
            "lang": 0,
            "words": [],
            "text": sentence["translation"],
            "para_alignment": [{"off_start": 0, "off_end": len(sentence["translation"]), "para_id": int(key)}]
        }

        offset = 0
        for word_data in sentence["words"]:
            word = word_data["word"]
            gloss = word_data["gloss"]
            
            # Разделяем части слова и глоссы по дефису
            _word_parts = re.split("([=-])", word)
            _gloss_parts = re.split("([=-])", gloss)

            word_parts, word_seps = [], []
            for word_part in _word_parts:
                if word_part not in ("-", "="):
                    word_parts.append(word_part)
                else:
                    word_seps.append(word_part)

            gloss_parts, gloss_seps = [], []
            for gloss_part in _gloss_parts:
                if gloss_part not in ("-", "="):
                    gloss_parts.append(gloss_part)       

            # Склеиваем части слова для "wf"
            wf = "".join(word_parts)

            # Создаем gloss_index с капсом в названиях глосс
            gloss_index_parts = []
            for i, (wp, gp) in enumerate(zip(word_parts, gloss_parts)):
                gloss_name = gp.upper() if i > 0 else "STEM"
                gloss_index_parts.append(f"{gloss_name}{{{wp}}}")
            
            # gloss_index = "-".join(gloss_index_parts) + "-"
            gloss_index = ""
            seps = iter(word_seps)
            for gloss_index_part in gloss_index_parts:
                gloss_index += gloss_index_part + next(seps, "-")

            cleaned_gloss = clean_gloss(gloss)

            # Анализируем часть речи
            pos = get_pos(cleaned_gloss)

            word_obj = {
                "wtype": "word",
                "wf": wf,
                "ana": [{
                    "parts": word,
                    "gloss": "",  # gloss всегда пустая строка
                    "gloss_index": gloss_index,
                    "lex": word_parts[0],
                    "trans_ru": gloss,
                    "gloss_ru": gloss,
                    "gloss_index_ru": gloss_index,
                    "gr.pos": pos
                }],
                "off_start": offset,
                "off_end": offset + len(wf),
                "next_word": len(sentence_obj["words"]) + 1,
                "sentence_index": len(sentence_obj["words"]),
                "sentence_index_neg": len(sentence["words"]) - len(sentence_obj["words"]) - 1
            }

            # Проверяем на пунктуацию
            if re.match(r'^[.,:;!?\"\'()-]$', wf):
                word_obj = {
                    "wtype": "punct",
                    "wf": wf,
                    "off_start": offset,
                    "off_end": offset + len(wf),
                    "next_word": len(sentence_obj["words"]) + 1
                }
            
            offset += len(wf) + 1  # +1 для пробела между словами
            sentence_obj["words"].append(word_obj)

        converted_data["sentences"].append(sentence_obj)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=4)

# Применяем функцию к файлу output.json и сохраняем результат в final.json
input_file = "output.json"
output_file = "final.json"
convert_output_to_flex(input_file, output_file)