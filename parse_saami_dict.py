import typing as T

from urllib.parse import quote

from bs4 import BeautifulSoup, Tag
import requests
import certifi

from final_converter import SaamiTransliterator
unicode_normalize = SaamiTransliterator.normalize


WEBSITE = "https://sanj.oahpa.no"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0"
HEADERS = {"User-Agent": USER_AGENT}

BASE_CATEGORY_NAME = "base"
BASE_MEANING = "<NO_MEANING>"

VERBAL_CATEGORY_NAME_MAP = {
    BASE_CATEGORY_NAME: "V.BASE",
    "отриц.": "V.CNG",
    "прош. слож.": (COMPLEX_PAST := "V.PST"),
}


PERSON_NUMBER_MAP = {
    "мунн": (FIRST_SG := "1SG"),
    "то̄нн": (SECOND_SG := "2SG"),
    "со̄нн": (THIRD_SG := "3SG"),
    "мыйй": (FIRST_PL := "1PL"),
    "тыйй": (SECOND_PL := "2PL"),
    "сыйй": (THIRD_PL := "3PL"),
}
PERSON_NUMBERS = {FIRST_SG, SECOND_SG, THIRD_SG, FIRST_PL, SECOND_PL, THIRD_PL}


CASES_MAP = {
    "Кто? Что?": (NOM := "NOM"),
    "Чей?": (GEN := "GEN"),
    "Кого? Чего?": (ACC := "ACC"),
    "кому? чему? куда?": (DAT := "DAT"),
    "У (от) кого? У (от) чего?": (ABL := "ABL"),
    "С кем? С чем?": (COM := "COM"),
    "Без кого? Без чего?": (ABESS := "ABESS"),
    "при сравнении": (CMPR := "CMPR"),
    "много, мало": (MANY := "MANY"),
    "В кого? Во что?": (ESS := "ESS"),
}
CASES = {NOM, GEN, ACC, DAT, ABL, COM, ABESS, CMPR, MANY, ESS}

TENSES_MAP = {
    "наст.": (PRS := "PRS"),
    "прош.": (PST := "PST"),
    "повел.": (IMP := "IMP"),
    "законч.": (TERM := "TERM"),
    "давно законч.": (PQTERM := "PQTERM"),
    "прич.": (PTCP := "PTCP"),
}
TENSES = {PRS, PST, IMP, TERM, PQTERM, PTCP}

NUMBERS_MAP = {
    "ед. число": (SG := "SG"),
    "мн. число": (PL := "PL"),
}
NUMBERS = {SG, PL}

COMPLEX_PAST_AUX = {

}


def convert_col_header(header: str) -> str:
    for category in (TENSES_MAP, NUMBERS_MAP):
        res = category.get(header, None)
        if res is not None:
            return res
    return header


def convert_cat_value(value: str) -> str:
    for category in (PERSON_NUMBER_MAP, CASES_MAP):
        res = category.get(value, None)
        if res is not None:
            return res
        elif (res2 := category.get(value.split()[0], None)) is not None:
            return res2
    return value


def get_tag_children(tag: Tag):
    return [child for child in tag.children if not isinstance(child, str)]


def is_header_row(tag: Tag, n_cols = None) -> bool:
    children = get_tag_children(tag)
    # print(f"is_header_row: {len(children)=}, {n_cols=}, {children=}")
    return (
        tag.name == "tr"
        # the condition on columns number below worked for simple paradigms, like `аббръе`
        #  (equal number of categories in each verb form)
        #  but doesn't work with `лӣйе` for example (extra "future tense" category value in few subparadigms)
        # and (n_cols is None or len(children) == n_cols)
        and all(child.name == "th" for child in children)
    )



def is_empty_separator_row(tag: Tag):
    return tag.td and "separatingcell" in tag.td.attrs.get("class", [])


def parse_subtable(
    subtable_rows: T.Iterable[Tag], n_cols: int
) -> T.Tuple[str, T.Dict[T.Tuple[str], str]]:
    print(f"<started new subtable>")
    header_row, *subtable_rows = subtable_rows
    print(f"{header_row=}")
    # print(*subtable_rows, sep="\n")
    category_name, *category_values = [next(h.stripped_strings, None) for h in header_row.find_all("th")]
    category_name = category_name or BASE_CATEGORY_NAME

    print(f"{category_name=}, {category_values=}")

    spanned = {}

    catval2cell = {}
    
    n_paradigm_rows = len(subtable_rows)
    for i, row in enumerate(subtable_rows):
        row_header = next(row.th.stripped_strings)
        cell_values = row.find_all("td")

        print(f"{i=} {row=}, {row_header=},")

        for j, column_header in enumerate(category_values):
            if j in spanned:
                strings = spanned[j].pop()
                if not spanned[j]:
                    spanned.pop(j)
            else:
                cell_value = cell_values.pop(0)
                # TODO: imperatives: remove `!`, set to lower
                # TODO: negatives: remove `!`, remove negative aux
                strings = list(cell_value.stripped_strings)

                if "rowspan" in cell_value.attrs:
                    rowspan = int(cell_value.attrs["rowspan"])
                    spanned.setdefault(j, [strings] * (rowspan - 1))

                if "colspan" in cell_value.attrs:
                    colspan = int(cell_value.attrs["colspan"])
                    spanned.update({k: [strings] for k in range(j, j+colspan)})
            
            # print(f"{column_header=}, {j=}, {cell_value=}, {spanned=}, {strings=}")

            ch = convert_col_header(column_header)
            if ch in TENSES:
                category_name = VERBAL_CATEGORY_NAME_MAP.get(category_name, category_name)

            rh = convert_cat_value(row_header)
            catval2cell[(ch, rh)] = strings

    return category_name, catval2cell


def postprocess_subtable(category_name, catval2cell):
    if category_name == COMPLEX_PAST:
        catval2cell_new = {}

        participle_forms = set()
        for (catval, pers), forms in catval2cell.items() :
            if catval == PTCP:
                participle_forms.update(forms)
            # no else: other forms in Complex past paradigm
            #   are actually forms of 'to be', the same for any verb
            
        catval2cell_new[PTCP] = sorted(participle_forms)

        return category_name, catval2cell_new
    
    else:
        return category_name, catval2cell


def parse_table(table: Tag):
    # assert table.tbody
    print(table)
    if table.tbody:
        table_tag = table.tbody
    else:
        table_tag = table
    
    cur_subtable_rows = []
    subtables = [cur_subtable_rows]

    rows = table_tag.find_all("tr")
    # print(f"{table_tag.name=} {len(rows)=}")
    
    header_row = rows[0]
    n_cols = len(get_tag_children(header_row))

    for i, row in enumerate(rows):
        # print(i, row, row.name, end="\nROW END\n\n")
        if is_header_row(row, n_cols=n_cols):
            # print("is_header_row=True")
            # previous subtable is finished
            if cur_subtable_rows:
                cur_subtable_rows = [row]
                subtables.append(cur_subtable_rows)
            else:
                cur_subtable_rows.append(row)
        elif not is_empty_separator_row(row):
            cur_subtable_rows.append(row)

    # print(f"{len(subtables)=}")

    res = {}
    for subtable in subtables:
        paradigm_name, paradigm = parse_subtable(subtable, n_cols=n_cols)
        print(paradigm_name, paradigm)
        paradigm_name, paradigm = postprocess_subtable(paradigm_name, paradigm)
        print(paradigm_name, paradigm)
        res[paradigm_name] = paradigm
        
    return res


def make_entry_link(lemma: str, lang="rus") -> str:
    print(lemma)
    return f"{WEBSITE}/detail/sjd/{lang}/{quote(lemma)}.html"


def load_entry(lemma: str):
    link = make_entry_link(lemma)
    print(link)
    response = requests.get(link, headers=HEADERS, verify=False)
    if not response.ok:
        return None
    
    soup = BeautifulSoup(response.text, features="lxml")
    return soup


def invert_paradigm(full_paradigm: T.Dict[str, T.Any]) -> T.Dict[str, T.List[T.Tuple[str]]]:
    if full_paradigm is None:
        return None

    form2feats = {}
    if len(full_paradigm) == 1:
        one_paradigm = full_paradigm[BASE_CATEGORY_NAME]
        for feats, forms in one_paradigm.items():
            for form in forms:
                form2feats.setdefault(form, []).append(feats)
    else:
        for paradigm_type, one_paradigm in full_paradigm.items():
            for feats, forms in one_paradigm.items():
                for form in forms:
                    if isinstance(feats, str):
                        full_feats = feats
                    else:
                        full_feats = (paradigm_type, *feats)
                    form2feats.setdefault(form, []).append(full_feats)
    
    return form2feats


def get_simple_meaning(meanings: T.List[str]):
    if meanings:
        return meanings[0].split()[0].strip(",")
    else:
        return


def parse_entry(soup: BeautifulSoup):
    # print(soup)
    meanings_tag = soup.find("ul", class_="meanings")
    paradigm_tag = soup.find("table", class_="miniparadigm")

    if meanings_tag:
        meanings = [next(m.span.stripped_strings, BASE_MEANING)
                    for m in meanings_tag.find_all("li")]
    else:
        meanings = None
    if paradigm_tag:
        full_paradigm = parse_table(paradigm_tag)
    else:
        full_paradigm = None
    return meanings, full_paradigm


def make_lookup_link(wordform: str, lang="rus") -> str:
    return f"{WEBSITE}/sjd/{lang}/?lookup={quote(wordform)}"


def load_lookup_page(wordform: str):
    link = make_lookup_link(wordform)
    print(link)
    response = requests.get(link, headers=HEADERS, verify=False)
    if not response.ok:
        return None
    
    soup = BeautifulSoup(response.text, features="lxml")
    return soup

def parse_lookup_page(soup: BeautifulSoup):
    lemmas_tags = soup.find_all("div", class_="entry_row")
    return [tag.find("span", attrs={'lang': 'sjd'}).get_text(strip=True)
            for tag in lemmas_tags
            if tag.find("span", attrs={'lang': 'sjd'}) is not None]

def analyze(wordform: str):
    analyses = []

    print(f"Ищем форму {wordform}")
    soup = load_lookup_page(wordform)
    lemmas = parse_lookup_page(soup)
    print(lemmas)
    for lemma in lemmas:
        print(f"Парсим лемму {lemma}...")
        soup2 = load_entry(lemma)
        meanings, full_paradigm = parse_entry(soup2)

        if full_paradigm is not None:
            form2feats = invert_paradigm(full_paradigm)
            print(meanings, full_paradigm, form2feats, sep="\n", end="\n"*2)
            analysis = form2feats[wordform]
        else:
            analysis = None
        
        simple_meaning = get_simple_meaning(meanings)
        print(f"analysis for {wordform}: {lemma}({simple_meaning})+{analysis}")

        analyses.append((lemma, simple_meaning, analysis))

    return analyses


def get_lemma_forms(wordform: str):
    """
    Возвращает анализ для всех лемм,
    соответствующих словоформе.

    [
        {
            "lemma": str,
            "meaning": str,
            "forms": set[str],
            "form2feats": dict
        }
    ]
    """

    results = []

    soup = load_lookup_page(wordform)
    lemmas = parse_lookup_page(soup)

    print(lemmas)

    for lemma in lemmas:
        soup2 = load_entry(lemma)
        meanings, full_paradigm = parse_entry(soup2)

        
        if full_paradigm is not None:
            form2feats = invert_paradigm(full_paradigm)
            forms = set(form2feats.keys())
        else:
            form2feats = None
            forms = {lemma}
        
        if meanings:
            meaning = get_simple_meaning(meanings)
        else:
            # no results
            return None

        # normalization
        lemma_norm = unicode_normalize(lemma)
        forms_norm = set(unicode_normalize(f) for f in forms)
        if form2feats: 
            form2feats_norm = {unicode_normalize(f): v
                            for f, v in form2feats.items()}
        else:
            form2feats_norm = None

        results.append({
            "lemma": lemma_norm,
            "meaning": meaning,
            "forms": forms_norm,
            "form2feats": form2feats_norm
        })

    return results


if __name__ == "__main__":
    requests.urllib3.disable_warnings()
    # wordforms = ["аббръе"]
    # for wordform in wordforms:
    #     print(wordform)
    #     soup = load_entry(wordform)
    #     # print(soup)
    #     result = parse_entry(soup)
    #     print(*result, sep="\n", end="\n"*2)

    wordforms = ["пэре"]
    for wordform in wordforms:
        # res = analyze(wordform)
        # print(res)

        res = get_lemma_forms(wordform)
        print(res)