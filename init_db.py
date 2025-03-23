import json
import re
from pathlib import Path

from sqlalchemy import and_

from flask_db import db, Text, Sentence, Word, Gloss, PossibleGloss, PossibleStem
from myapp import app


STEMS = {}
GLOSSES = {}


def parse_annotation(annotation):
    gloss_parts = re.split("[=-]", annotation["gloss_index"].strip("-"))
    transl_parts = re.split("[=-]", annotation["trans_ru"].strip("-"))
    
    glosses = []
    for i, part in enumerate(gloss_parts):
        try:
            meaning, allomorph = part.strip("}").split("{")
        except ValueError:
            print(part)
        
        is_stem = meaning == "STEM"
        if is_stem:
            meaning = transl_parts[i]
        
        glosses.append({"meaning": meaning, "allomorph": allomorph, "is_stem": is_stem})
    
    return glosses


def add_new_possible_glosses_or_stems(new_possible_list, model, session):
    added_items = []
    for new_possible_item in new_possible_list:
        meaning = new_possible_item["meaning"]
        allomorph = new_possible_item["allomorph"]

        maybe_item = session.query(model).filter(
            model.meaning == meaning,
            model.allomorph == allomorph
        ).first()

        if not maybe_item:
            new_item = model(meaning=meaning, allomorph=allomorph)
            session.add(new_item)
            added_items.append(new_item)
    
    session.commit()

    for item in added_items:
        if model is PossibleStem:
            STEMS[(item.meaning, item.allomorph)] = item.possible_stem_id
        else:
            GLOSSES[(item.meaning, item.allomorph)] = item.possible_gloss_id


def add_file(filename):
    '''Читает файл формата Цакорпуса и добавляет данные из него к базе данных'''
    new_possible_glosses = []
    new_possible_stems = []

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["meta"]
    title = meta["title"]
    filename = meta["filename"]
    text = Text(title=title, filename=filename)

    sentences_data = data["sentences"]
    for sent_data in sentences_data:
        lang = sent_data["lang"]
        translation = sent_data["text"]

        words_data = sent_data["words"]
        full_text = ' '.join([word["wf"] for word in words_data])
        full_gloss = ' '.join([word['ana'][0]['gloss_ru'] for word in words_data])

        sent = Sentence(lang=lang, translation=translation, full_gloss=full_gloss, full_text=full_text)
        text.sentences.append(sent)

        for word_data in words_data:
            wtype = word_data.pop("wtype")
            if wtype == "punct":
                continue

            form = word_data.pop("wf")
            # в 'ana' хранятся анализы, берём всегда первый из них (он и так всегда один, потому что это глоссированные нами тексты)
            _annotation = word_data.pop("ana")[0]
            pos = _annotation["gr.pos"]
            word_gloss = _annotation["gloss_ru"]

            word = Word(form=form, pos=pos, word_gloss=word_gloss, **word_data)
            sent.words.append(word)

            glosses = parse_annotation(_annotation)
            maybe_new_glosses = [gloss_dict for gloss_dict in glosses if not gloss_dict["is_stem"]]
            maybe_new_stems = [gloss_dict for gloss_dict in glosses if gloss_dict["is_stem"]]

            new_possible_glosses.extend(maybe_new_glosses)
            new_possible_stems.extend(maybe_new_stems)
            
            word.temp_glosses = glosses
            # for gloss in glosses:
    
    with app.app_context():
        add_new_possible_glosses_or_stems(new_possible_glosses, PossibleGloss, db.session)
        add_new_possible_glosses_or_stems(new_possible_stems, PossibleStem, db.session)
        db.session.commit()

        for sent in text.sentences:
            for word in sent.words:
                for gloss in word.temp_glosses:
                    meaning = gloss["meaning"]
                    if gloss["is_stem"]:
                        possible_stem_id = STEMS[(meaning, gloss["allomorph"])]
                        gl = Gloss(possible_stem_id=possible_stem_id)
                    else:
                        possible_gloss_id = GLOSSES[(meaning, gloss["allomorph"])]
                        gl = Gloss(possible_gloss_id=possible_gloss_id)

                    word.glosses.append(gl)
        
        db.session.add(text)
        db.session.commit()
    
    return text

for file in Path("./tsacorp_files").iterdir():
    add_file(file)