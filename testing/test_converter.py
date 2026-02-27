import pytest

import csv
from string import punctuation
import re

from final_converter import (
    split_into_clusters_with_softness,
    SaamiTransliterator,
)

from utils import punct

print(punctuation)
print(punct)

class Sentence:
    def __init__(self, gloss, cyrillic, source, sent_index):
        self.gloss = gloss
        self.cyrillic = cyrillic
        self.source = source
        self.sent_index = sent_index
    def __repr__(self):
        return f"Sentence({self.gloss!r}, {self.cyrillic!r}, {self.source!r}, {self.sent_index!r})"


def saami_tests():
    sents = []
    with open('./testing/saami_converter_tests.csv', 'r', encoding="utf-8", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            print(row)
            # if i == 6:
            sents.append(Sentence(row["gloss"], row["cyrillic"], row['source'], row['sent_index']))
    yield from sents

sents = saami_tests()


def remove_punct(s: str):
    # return pat.sub("", s)
    # return re.sub(r'''[!"#$%&'()*+,-‐‑\./:;<=>?@\[\\\]^_`{|}~]''', "", s)
    translator = str.maketrans('', '', ''.join(punct))
    clean_text = s.translate(translator)
    return clean_text


@pytest.mark.parametrize("sent", saami_tests())
def test_converter(sent):
    transliterator = SaamiTransliterator()
    
    cyr_no_punct = remove_punct(sent.cyrillic)

    res = transliterator.transliterate_text(sent.gloss)
    # print(res)
    res_no_punct = remove_punct(res)
    # print(res_no_punct)

    assert res_no_punct.split() == cyr_no_punct.lower().split()
