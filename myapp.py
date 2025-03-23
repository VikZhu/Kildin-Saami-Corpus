import os
from flask import Flask, render_template, request
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from flask_db import db, Text, Sentence, Word, Gloss, PossibleGloss, PossibleStem

from bd_requests import top_glosses, count_stems, count_words, count_texts, top_word_by_pos

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'saami.db')

db.app = app
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/search", methods=['GET', 'POST'])
def search():
    meaning_to_find = request.args.get('meaning', '')  # Получаем значение meaning из формы
    pos_to_find = request.args.get('pos', '')  # Получаем значение pos из формы
    part_stem = request.args.get('stem', '')  # Получаем значение stem из формы

    # Результаты поиска
    results = []

    with app.app_context():
        if meaning_to_find:
            # Поиск по meaning
            words_with_gloss = (
                db.session.query(Word).options(joinedload(Word.sentence).joinedload(Sentence.words))
                .join(Gloss)
                .join(Sentence)
                .join(PossibleGloss)
                .filter(PossibleGloss.meaning.ilike(f"%{meaning_to_find}%"))
                .all()
            )
            results = words_with_gloss
        
        elif pos_to_find:
            # Поиск по части речи
            words_with_context = (
                db.session.query(Word).options(joinedload(Word.sentence).joinedload(Sentence.words))
                .join(Sentence)
                .filter(Word.pos == pos_to_find)
                .all()
            )
            results = words_with_context

        elif part_stem:
            part_stem_results = (
                db.session.query(Word).options(joinedload(Word.sentence).joinedload(Sentence.words))
                .join(Gloss, Word.word_id == Gloss.word_id)
                .join(PossibleStem, Gloss.possible_stem_id == PossibleStem.possible_stem_id)
                .join(Sentence, Sentence.sentence_id == Word.sentence_id)
                .join(Text, Text.text_id == Sentence.text_id)
                .filter(PossibleStem.allomorph.ilike(f"%{part_stem}%"))
                .all()
            )
            results = part_stem_results
    return render_template('search.html', results=results, meaning=meaning_to_find, pos=pos_to_find, stem=part_stem)

@app.route("/statistics")
def bd_statistics():
    with app.app_context():
        # Выполняем SQL-запросы, используя engine.connect()
        with db.engine.connect() as conn:
            # Выполняем запросы и получаем результаты
            top_glosses_result = conn.execute(text(top_glosses)).all()
            total_possible_stems_result = conn.execute(text(count_stems)).scalars().one()
            total_words_result = conn.execute(text(count_words)).scalars().one()
            total_texts_result = conn.execute(text(count_texts)).scalars().one()
            top_word_by_pos_result = conn.execute(text(top_word_by_pos)).all()
    
    # Передаем результаты в шаблон
    return render_template('statistics.html',
                           top_glosses=top_glosses_result,
                           total_possible_stems=total_possible_stems_result,
                           total_words=total_words_result,
                           total_texts=total_texts_result,
                           top_word_by_pos=top_word_by_pos_result)


if __name__ == '__main__':
    app.run(debug=True)