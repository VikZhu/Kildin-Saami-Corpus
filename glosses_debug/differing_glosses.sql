SELECT texts.title, sentences.full_text, meaning, allomorph, allomorph_cyr, count(*) FROM possible_glosses
JOIN glosses on glosses.possible_gloss_id = possible_glosses.possible_gloss_id
JOIN words on words.word_id = glosses.word_id
JOIN sentences on sentences.sentence_id = words.sentence_id
JOIN texts on texts.text_id = sentences.text_id
GROUP BY meaning, allomorph
ORDER BY meaning ASC