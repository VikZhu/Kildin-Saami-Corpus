import pytest

import csv
from string import punctuation
import re

from final_converter import (
    split_into_clusters_with_softness,
    SaamiTransliterator,
)

print(punctuation)

class Sentence:
    def __init__(self, gloss, cyrillic):
        self.gloss = gloss
        self.cyrillic = cyrillic


def saami_tests():
    sents = []
    with open('./testing/saami_converter_tests.csv', 'r', encoding="utf-8", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row)
            sents.append(Sentence(row["gloss"], row["cyrillic"]))
    return sents

sents = saami_tests()


def remove_punct(s: str, pat=re.compile(r'''!"#$%&'()*+,-./:;<=>?@\[\\\]^_`{|}~''')):
    return pat.sub("", s)


# def test_converter(saami_tests):
#     transliterator = SaamiTransliterator()
#     print(saami_tests)
#     for sent in saami_tests:
#         cyr_no_punct = remove_punct(sent.cyrillic)

#         res = transliterator.transliterate_text(sent.gloss)
#         print(res)
#         res_no_punct = remove_punct(res)
#         print(res_no_punct)

#         assert res_no_punct == cyr_no_punct.lower()

# @pytest.mark.parametrize("saami_tests", indirect=True)
def test_converter(saami_tests):
    transliterator = SaamiTransliterator()
    
    for i, sent in enumerate(saami_tests, start=1):
        cyr_no_punct = remove_punct(sent.cyrillic)

        res = transliterator.transliterate_text(sent.gloss)
        print(res)
        res_no_punct = remove_punct(res)
        print(res_no_punct)

        with pytest.subtests.test(i=i):
            assert res_no_punct == cyr_no_punct.lower()


import pytest

def gen_lines():
    with open('file_that_does_not_exist') as f:
        yield from f

def create_file():
    with open('file_that_does_not_exist', 'w') as f:
        print('ABC', file=f)
        print('DEF', file=f)

create_file()

@pytest.fixture(params=gen_lines())
def line_fixture(request):
    return request.param

def test_line(line_fixture):
    assert True
