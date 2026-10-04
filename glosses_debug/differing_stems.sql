SELECT texts.title, sentences.full_text, meaning, allomorph, count(*) FROM possible_stems
JOIN glosses on glosses.possible_stem_id = possible_stems.possible_stem_id
JOIN words on words.word_id = glosses.word_id
JOIN sentences on sentences.sentence_id = words.sentence_id
JOIN texts on texts.text_id = sentences.text_id
GROUP BY meaning, allomorph
ORDER BY meaning ASC