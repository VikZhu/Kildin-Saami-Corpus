import os
import csv
import io
import math

from flask import Flask, send_file, render_template, request, make_response
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import joinedload
import sqlalchemy.orm.query

from flask_db import db, Text, Sentence, Word, Gloss, PossibleGloss, PossibleStem
from bd_requests import top_glosses, count_stems, count_words, count_texts, top_word_by_pos
from final_converter import SaamiTransliterator
from parse_saami_dict import get_lemma_forms


st = SaamiTransliterator()


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'saami.db')

db.app = app
db.init_app(app)

# Константа для количества результатов на странице
ITEMS_PER_PAGE = 20

with app.app_context():
    db.create_all()

@app.context_processor
def utility_processor():
    def get_unique_pos():
        with app.app_context():
            pos_list = db.session.query(Word.pos).distinct().filter(Word.pos != '').order_by(Word.pos).all()
            return [p[0] for p in pos_list if p[0]]
    return dict(get_unique_pos=get_unique_pos)

@app.route('/')
def index():
    return render_template('index.html')
    

def do_wordform_search(part_stem):
    part_stem_results = (
        db.session.query(Word).options(joinedload(Word.sentence).joinedload(Sentence.words))
        .join(Gloss, Word.word_id == Gloss.word_id)
        .join(PossibleStem, Gloss.possible_stem_id == PossibleStem.possible_stem_id)
        .join(Sentence, Sentence.sentence_id == Word.sentence_id)
        .join(Text, Text.text_id == Sentence.text_id)
        .filter(PossibleStem.allomorph_cyr == part_stem)
        .all()
    )

    return part_stem_results


def transliterate_before_search(s: str):
    orig_s = None
    if not st.is_cyr(s):
        orig_s = s
        s = st.transliterate_text(s)
        print(f"transliterated `{orig_s}` --> `{s}`")

    return s, orig_s


def build_search_query(meaning_to_find, pos_to_find, part_stem, lemma_word):
    """Строит запрос и возвращает (query, total_count, conditions_info)"""
    
    # Флаги для определения необходимых JOIN-ов
    needs_gloss_join = False
    needs_possible_gloss_join = False
    needs_possible_stem_join = False
    needs_text_join = False
    
    # Список условий для фильтрации
    conditions = []
    
    # Обработка поиска по глоссе (значению)
    if meaning_to_find:
        needs_gloss_join = True
        needs_possible_gloss_join = True
        conditions.append(PossibleGloss.meaning.ilike(f"%{meaning_to_find}%"))
    
    # Обработка поиска по части речи
    if pos_to_find:
        conditions.append(Word.pos == pos_to_find)
    
    # Обработка поиска по основе (словоформе)
    if part_stem:
        part_stem, orig_part_stem = transliterate_before_search(part_stem)
        needs_gloss_join = True
        needs_possible_stem_join = True
        conditions.append(PossibleStem.allomorph_cyr == part_stem)
    
    # Обработка поиска по лемме
    if lemma_word:
        lemma_word, orig_lemma_word = transliterate_before_search(lemma_word)
        
        analyses = get_lemma_forms(lemma_word)
        print(f"Lemma search: {lemma_word}, analyses: {analyses}")
        
        if analyses is not None and analyses:
            all_forms = set()
            for a in analyses:
                all_forms |= a["forms"]
            
            print(f"All forms for lemma: {all_forms}")
            
            if all_forms:
                conditions.append(Word.form_cyr.in_(all_forms))
            else:
                # Если форм нет, ищем как словоформу
                needs_gloss_join = True
                needs_possible_stem_join = True
                conditions.append(PossibleStem.allomorph_cyr == lemma_word)
        else:
            # Если лемма не найдена, ищем как словоформу
            print(f"Lemma not found, searching as wordform: {lemma_word}")
            needs_gloss_join = True
            needs_possible_stem_join = True
            conditions.append(PossibleStem.allomorph_cyr == lemma_word)
    
    # Строим базовый запрос
    query = db.session.query(Word).options(
        joinedload(Word.sentence).joinedload(Sentence.words)
    )
    
    # Всегда нужен JOIN с Sentence для доступа к контексту
    query = query.join(Sentence, Sentence.sentence_id == Word.sentence_id)
    
    # Добавляем необходимые JOIN-ы
    if needs_gloss_join:
        query = query.join(Gloss, Word.word_id == Gloss.word_id)
    
    if needs_possible_gloss_join:
        query = query.join(PossibleGloss, Gloss.possible_gloss_id == PossibleGloss.possible_gloss_id)
    
    if needs_possible_stem_join:
        query = query.join(PossibleStem, Gloss.possible_stem_id == PossibleStem.possible_stem_id)
    
    # Если нужен Text (для статистики или дополнительных данных)
    if needs_text_join:
        query = query.join(Text, Text.text_id == Sentence.text_id)
    
    return query, conditions


@app.route("/search", methods=['GET', 'POST'])
def search():
    meaning_to_find = request.args.get('meaning', '')
    pos_to_find = request.args.get('pos', '')
    part_stem = request.args.get('stem', '')
    lemma_word = request.args.get('lemma_word', '')
    page = request.args.get('page', 1, type=int)
    
    # Строим запрос
    query, conditions = build_search_query(meaning_to_find, pos_to_find, part_stem, lemma_word)
    
    # Получаем общее количество результатов
    if conditions:
        # Создаем запрос для подсчета количества
        count_query = db.session.query(db.func.count(Word.word_id.distinct()))
        count_query = count_query.join(Sentence, Sentence.sentence_id == Word.sentence_id)
        
        # Добавляем те же JOIN-ы, что и в основном запросе
        current_query = query
        # Извлекаем все JOIN из основного запроса и добавляем их в count_query
        # Простой способ: используем тот же query для подсчета, но убираем options
        from sqlalchemy.sql import func
        
        # Более простой подход: создаем отдельный запрос для подсчета
        count_subquery = db.session.query(Word.word_id)
        count_subquery = count_subquery.join(Sentence, Sentence.sentence_id == Word.sentence_id)
        
        # Определяем, какие JOIN-ы были добавлены
        if any('Gloss' in str(c) for c in conditions) or meaning_to_find or part_stem or lemma_word:
            count_subquery = count_subquery.join(Gloss, Word.word_id == Gloss.word_id)
        
        if meaning_to_find:
            count_subquery = count_subquery.join(PossibleGloss, Gloss.possible_gloss_id == PossibleGloss.possible_gloss_id)
        
        if part_stem or (lemma_word and not get_lemma_forms(lemma_word)):
            count_subquery = count_subquery.join(PossibleStem, Gloss.possible_stem_id == PossibleStem.possible_stem_id)
        
        # Применяем условия
        if conditions:
            count_subquery = count_subquery.filter(and_(*conditions))
        
        total_count = count_subquery.distinct().count()
    else:
        total_count = 0
    
    # Вычисляем пагинацию
    total_pages = math.ceil(total_count / ITEMS_PER_PAGE) if total_count > 0 else 1
    
    # Убеждаемся, что страница в допустимых пределах
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Получаем результаты для текущей страницы
    if conditions and total_count > 0:
        # Применяем пагинацию к основному запросу
        page_results = query.filter(and_(*conditions)).offset((page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()
        # Убираем дубликаты (если есть)
        seen = set()
        unique_results = []
        for r in page_results:
            if r.word_id not in seen:
                seen.add(r.word_id)
                unique_results.append(r)
        page_results = unique_results
    else:
        page_results = []
    
    # Вычисляем отображаемые индексы
    start_index = (page - 1) * ITEMS_PER_PAGE + 1 if page_results else 0
    end_index = min(page * ITEMS_PER_PAGE, total_count)
    
    print(f"Search completed: total={total_count}, page={page}/{total_pages}, showing {len(page_results)} results")
    
    return render_template(
        'search.html', 
        results=page_results,
        total_count=total_count,
        total_pages=total_pages,
        page=page,
        start_index=start_index,
        end_index=end_index,
        meaning=meaning_to_find, 
        pos=pos_to_find, 
        stem=part_stem, 
        lemma_word=lemma_word
    )


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


@app.route("/download_results", methods=['GET'])
def download_results():
    print("=== DOWNLOAD RESULTS CALLED ===")
    print(f"Args: {request.args}")
    
    # Получаем параметры поиска (без пагинации)
    meaning_to_find = request.args.get('meaning', '')
    pos_to_find = request.args.get('pos', '')
    part_stem = request.args.get('stem', '')
    lemma_word = request.args.get('lemma_word', '')
    
    print(f"Search params: meaning={meaning_to_find}, pos={pos_to_find}, stem={part_stem}, lemma={lemma_word}")
    
    # Флаги для JOIN-ов
    needs_gloss_join = False
    needs_possible_gloss_join = False
    needs_possible_stem_join = False
    
    # Условия фильтрации
    conditions = []
    
    # Поиск по глоссе
    if meaning_to_find:
        needs_gloss_join = True
        needs_possible_gloss_join = True
        conditions.append(PossibleGloss.meaning.ilike(f"%{meaning_to_find}%"))
    
    # Поиск по части речи
    if pos_to_find:
        conditions.append(Word.pos == pos_to_find)
    
    # Поиск по стеблю
    if part_stem:
        if not st.is_cyr(part_stem):
            orig_part_stem = part_stem
            part_stem = st.transliterate_text(part_stem)
            print(f"transliterated `{orig_part_stem}` --> `{part_stem}`")
        
        needs_gloss_join = True
        needs_possible_stem_join = True
        conditions.append(PossibleStem.allomorph_cyr == part_stem)
    
    # Поиск по лемме
    if lemma_word:
        if not st.is_cyr(lemma_word):
            orig_lemma_word = lemma_word
            lemma_word = st.transliterate_word(lemma_word)
            print(f"transliterated `{orig_lemma_word}` --> `{lemma_word}`")
        
        analyses = get_lemma_forms(lemma_word)
        print(f"Lemma search: {lemma_word}, analyses found: {analyses is not None}")
        
        if analyses is not None and analyses:
            all_forms = set()
            for a in analyses:
                all_forms |= a["forms"]
            
            print(f"Forms found: {all_forms}")
            
            if all_forms:
                conditions.append(Word.form_cyr.in_(all_forms))
            else:
                needs_gloss_join = True
                needs_possible_stem_join = True
                conditions.append(PossibleStem.allomorph_cyr == lemma_word)
        else:
            needs_gloss_join = True
            needs_possible_stem_join = True
            conditions.append(PossibleStem.allomorph_cyr == lemma_word)
    
    results = []
    
    try:
        with app.app_context():
            if conditions:
                # Строим запрос для получения ВСЕХ результатов (без пагинации)
                query = db.session.query(Word).options(
                    joinedload(Word.sentence).joinedload(Sentence.words)
                )
                
                # JOIN с Sentence всегда нужен
                query = query.join(Sentence, Sentence.sentence_id == Word.sentence_id)
                
                # Добавляем необходимые JOIN-ы
                if needs_gloss_join:
                    query = query.join(Gloss, Word.word_id == Gloss.word_id)
                
                if needs_possible_gloss_join:
                    query = query.join(PossibleGloss, Gloss.possible_gloss_id == PossibleGloss.possible_gloss_id)
                
                if needs_possible_stem_join:
                    query = query.join(PossibleStem, Gloss.possible_stem_id == PossibleStem.possible_stem_id)
                
                # Применяем фильтры
                query = query.filter(and_(*conditions))
                
                # Убираем возможные дубликаты
                query = query.distinct(Word.word_id)
                
                # Выполняем запрос для получения ВСЕХ результатов
                results = query.all()
                print(f"Found {len(results)} total results for download")
            else:
                print("No search parameters for download")
                results = []
            
            # Создаем CSV файл в памяти
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            
            # Записываем заголовки (расширенные для комбинированного поиска)
            writer.writerow(['Word_lat', 'Word_cyr', 'PoS', 'Gloss_meaning', 'Sentence_text', 'Sentence_translation'])
            
            # Записываем все данные
            for word in results:
                # Получаем глоссу слова (если есть)
                gloss_meaning = ''
                if hasattr(word, 'glosses') and word.glosses:
                    gloss_meaning = ', '.join([g.possible_gloss.meaning for g in word.glosses if g.possible_gloss])
                
                writer.writerow([
                    word.form if hasattr(word, 'form') else '',
                    word.form_cyr if hasattr(word, 'form_cyr') else '',
                    word.pos if hasattr(word, 'pos') else '',
                    gloss_meaning,
                    word.sentence.text if word.sentence and hasattr(word.sentence, 'text') else '',
                    word.sentence.translation if word.sentence and hasattr(word.sentence, 'translation') else ''
                ])
            
            # Подготавливаем файл для отправки
            output.seek(0)
            
            filename = "saami_corpus_results.csv"
            
            # Отправляем файл с правильной кодировкой для Excel
            response = make_response(output.getvalue().encode('utf-8-sig'))
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            
            print("=== FILE SENT SUCCESSFULLY ===")
            return response
            
    except Exception as e:
        print(f"ERROR in download_results: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error generating download: {str(e)}", 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)