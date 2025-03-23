from flask import Flask
from flask import render_template, request
from sqlalchemy import and_, text

top_glosses = """
SELECT pg.meaning, pg.allomorph, COUNT(g.possible_gloss_id) AS frequency
FROM glosses g
JOIN possible_glosses pg ON g.possible_gloss_id = pg.possible_gloss_id
GROUP BY pg.meaning, pg.allomorph
ORDER BY frequency DESC
LIMIT 10;
"""
count_stems = """
SELECT COUNT(*) AS total_possible_stems FROM possible_stems;
"""

count_words = """
SELECT COUNT(*) AS total_words FROM words;
"""

count_texts = """
SELECT COUNT(*) AS total_texts FROM texts;
"""

top_word_by_pos = """
WITH RankedWords AS (
    SELECT 
        w.pos,
        w.form,
        COUNT(w.form) AS frequency,
        ROW_NUMBER() OVER (PARTITION BY w.pos ORDER BY COUNT(w.form) DESC) AS rank
    FROM words w
    GROUP BY w.pos, w.form
)
SELECT pos, form, frequency
FROM RankedWords
WHERE rank <= 5
ORDER BY pos, rank;
"""