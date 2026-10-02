import re
import unicodedata as u

from utils import punct

L_token_consonant_list = [
    'p','t','k','b','d','g','c','č','ʒ','ǯ','f','s','š','x','v','z','ž',
    'm','n','ɲ','ŋ','r','l', 'h'
]
# _L_combined_consonants_before_comb_list = ['m','n', 'r','l']
_L_combined_consonants_before_comb_list = ['m','n', 'r','l', 'ʒ']
L_combined_consonants_list = ['m̥','n̥', 'r̥','l̥']
L_consonant_list = L_combined_consonants_list + L_token_consonant_list
_L_token_consonant_list_str = ''.join(L_token_consonant_list)
_L_combined_consonants_before_comb_list_str = ''.join(_L_combined_consonants_before_comb_list)

L_vowel_proper_list = ['i','ɨ','u','e','o','a','ɒ']
L_j_list = ['j','j̥']
L_vowel_list = L_vowel_proper_list + L_j_list
_L_vowel_list_str = ''.join(L_vowel_list)

SOFTNESS_SYMBOLS = ["'", "’"]
COMBINING_SYMBOLS = ["\u0325", "\u030C"]
ALLOWED_SYMBOLS_INSIDE = SOFTNESS_SYMBOLS + COMBINING_SYMBOLS
_SOFTNESS_SYMBOLS_STR = ''.join(SOFTNESS_SYMBOLS)
_COMBINING_SYMBOLS_STR = ''.join(COMBINING_SYMBOLS)


def split_into_clusters_with_softness(
    word, consonants, vowels,
    symb_re = re.compile(
        rf"""[{_L_combined_consonants_before_comb_list_str}][\u0325\u030C]
             |[{_L_token_consonant_list_str + _L_vowel_list_str}]
             |[{_SOFTNESS_SYMBOLS_STR}]
        """, re.VERBOSE)
):
    clusters = []
    i = 0

    symbs = symb_re.findall(word)

    n = len(symbs)

    while i < n:
        if (
            symbs[i] in consonants or
            (symbs[i] in SOFTNESS_SYMBOLS and i + 1 < n and symbs[i + 1] in consonants)
        ):
            base = []
            soft = False

            while i < n and (symbs[i] in consonants or symbs[i] in SOFTNESS_SYMBOLS):
                if symbs[i] in {"'", "’"}:
                    soft = True
                else:
                    base.append(symbs[i])
                i += 1

            clusters.append(("C", "".join(base), soft))

        # === ГЛАСНЫЙ КЛАСТЕР ===
        elif symbs[i] in vowels:
            base = []
            while i < n and symbs[i] in vowels:
                base.append(symbs[i])
                i += 1
            clusters.append(("V", "".join(base), False))

        else:
            i += 1

    return clusters


A_CYR = 'а'
I_CYR = 'и'
IE_CYR = 'ӭ'
U_CYR = 'у'
E_CYR = 'э'
O_CYR = 'о'
Y_CYR = 'ы'
O_DIPHT_CYR = 'оа'
LONG_A_CYR = 'а\u0304'
LONG_I_CYR = 'ӣ'
LONG_IE_CYR = 'ӭ̄'
LONG_U_CYR = 'у\u0304'
LONG_E_CYR = 'э̄'
LONG_O_CYR = 'о\u0304'
LONG_Y_CYR = 'ы̄'
LONG_O_DIPHT_CYR = 'оа\u0304'

YA_CYR = 'я'
YO_CYR = 'ё'
YU_CYR = 'ю'
YE_CYR = 'е'
LONG_YA_CYR = 'я̄'
LONG_YO_CYR = 'ё̄'
LONG_YU_CYR = 'ю̄'
LONG_YE_CYR = 'ē'

J_CYR = 'й'

SHORT_VOWELS = set([A_CYR, I_CYR, U_CYR, E_CYR, O_CYR, Y_CYR])
SHORT_VOWELS_SOFT = set([YA_CYR, YO_CYR, YU_CYR, YE_CYR])

LONGS = set([LONG_A_CYR, LONG_I_CYR, LONG_U_CYR, LONG_E_CYR, LONG_O_CYR, LONG_Y_CYR])
LONGS_SOFT = set([LONG_YA_CYR, LONG_YO_CYR, LONG_YU_CYR])

DIPHTONGS = set([O_DIPHT_CYR])
DIPHTONGS_LONG = set([LONG_O_DIPHT_CYR])

VOWELS_PROPER = SHORT_VOWELS | SHORT_VOWELS_SOFT | LONGS | LONGS_SOFT | DIPHTONGS | DIPHTONGS_LONG


class SaamiTransliterator:
    def __init__(self):
        self.vowel_map = {
            'aa': LONG_A_CYR, 'a': A_CYR,
            'ii': LONG_I_CYR, 'i': Y_CYR, # тут нельзя просто заменить 
            'uu': LONG_U_CYR, 'u': U_CYR,
            'ee': LONG_E_CYR, 'e': E_CYR,
            'oo': LONG_O_CYR, 'o': O_CYR,
            'ɨɨ': LONG_Y_CYR, 'ɨ': Y_CYR,
            'ɒɒ': LONG_O_DIPHT_CYR, 'ɒ': O_DIPHT_CYR,
            'j': J_CYR,
        }

        self.soft_vowel_map = {
            'ee': LONG_YE_CYR, 'e': YE_CYR,
            'aa': LONG_YA_CYR, 'a': YA_CYR,
            'oo': LONG_YO_CYR, 'o': YO_CYR,
            'uu': LONG_YU_CYR, 'u': YU_CYR,
            'ɨɨ': LONG_I_CYR, 'ɨ': I_CYR,
            # потому что первый кластер, если он начинается с j, мы маркируем как мягкий
            'ja': YA_CYR, 'je': YE_CYR, 'ji': I_CYR,
            'ii': LONG_I_CYR, 'i': I_CYR, 'j': J_CYR
        }
        
        self.semi_soft_vowel = {'ä', 'ё̄', 'ӭ'}

        #print(self.vowel_map)
        #print(self.soft_vowel_map)

        self.consonant_map = {
            'pp':'пп','p':'п',
            'tt':'тт','t':'т',
            'kk':'кк','k':'к',
            'bb':'бп','b':'б',
            'dd':'дт','d':'д',
            'gg':'гк','g':'г',
            'cc':'дц','c':'ц',
            'čč':'чч','č':'ч',
            'ǯ':'дж', 
                'ʒ':'дж',
            'ff':'фф','f':'ф',
            'ss':'сс','s':'с',
            'šš':'шш','š':'ш',
            'h':'хх',
            'x':'х',
            'v':'в',
            'zz':'зз','z':'з',
            'žž':'жж','ž':'ж',
            'mm':'мм','m':'м',
            'nn':'нн','n':'н',
            'ɲɲ':'нн','ɲ':'н',
            'ŋŋ':'ӈӈ','ŋ':'ӈ',
            'm̥m̥':'ӎӎ','m̥':'ӎ',
            'n̥n̥':'ӊӊ','n̥':'ӊ',
            'rr':'рр','r':'р',
            'll':'лл','l':'л',
            'r̥r̥':'ҏҏ','r̥':'ҏ',
            'l̥l̥':'ӆӆ','l̥':'ӆ',
            'j':J_CYR
        }

        self.semi_soft_consonants = {'д', 'т', 'н'}

        self.punctuation = punct


    def clean_word(self, word):
        word = word.strip()
        while word and word[0] in self.punctuation:
            word = word[1:]
        while word and word[-1] in self.punctuation:
            word = word[:-1]
        return word


    def split_text(self, text):
        pattern = re.compile(r'([\w\'’\u0300-\u036F]+|[^\w\'’\u0300-\u036F]+)', re.UNICODE)
        return pattern.findall(text)


    def transliterate_clusters(self, clusters):
        result = []

        for i, (kind, base, soft) in enumerate(clusters):
            print((kind, base, soft))

            if kind == "C":
                cyr = base
                for k, v in sorted(self.consonant_map.items(), key=lambda x: -len(x[0])):
                    cyr = cyr.replace(k, v)

                print("Before softness", f"{cyr=}, {bool(cyr)=}, {i=}, {len(clusters)=}")
                if soft:
                    if (cyr 
                        and (
                            (len(cyr) >= 2 and cyr[-2] in self.semi_soft_consonants and cyr != 'дж'))
                            or (len(cyr) == 1 and cyr[-1] in self.semi_soft_consonants)
                        ):
                        softness_sign = 'ҍ'
                    elif cyr:
                        softness_sign = 'ь'
                   
                    if len(cyr) > 1 and cyr not in ["бп", "дт", "гк", "дж"] and cyr[-2] != cyr[-1]:
                        if len(cyr) > 2:
                            if cyr[-3] != cyr[-2]:
                                cyr = cyr[:-1] + softness_sign + cyr[-1]
                        cyr = cyr[:-1] + softness_sign + cyr[-1]
                    # only add softness sign after the last single-letter consonant cluster
                    #  (not before vowels!)
                    elif i == len(clusters) - 1:
                        cyr += softness_sign   

                result.append(cyr)

            else:  
                prev_cluster = clusters[i-1]
                prev_soft = (
                    (
                        i > 0 and
                        prev_cluster[0] == "C" and
                        prev_cluster[2]
                    ) or (
                        i == 0 and base[0] in L_j_list
                    ) or (
                        len(clusters) == 1 and base == 'i'
                    )
                )
                #print(f"{prev_soft=}")

                v = base
                if prev_soft:
                    # нет j перед гласными в начале
                    # print(v)
                    pat = f"^j(?=[{''.join(L_vowel_list)}]{ '{2}'})"
                    v = re.sub(pat, "", v)
                    # print(v, pat)

                    for k, v2 in sorted(self.soft_vowel_map.items(), key=lambda x: -len(x[0])):
                        v = v.replace(k, v2)
                        # print(k, v2)
                else:
                    for k, v2 in sorted(self.vowel_map.items(), key=lambda x: -len(x[0])):
                        if 'jj' in base and not((i+1) == len(clusters)):
                            v = v.replace('jj', 'йй')
                            v = v.replace(k, v2)
                        else:
                            v = v.replace(k, v2)
                #print("result:", v)           

                result.append(v)
        return result
    
    def is_cyr(self, word):
        # for symb in u.normalize("NFD", word):
        #     print(symb, hex(ord(symb)), u.name(symb))
        for symb in word:
            print(symb, hex(ord(symb)), u.name(symb))
        return re.fullmatch(r"[а-яё'\u0300-\u036F\u048a-\u04f9]+", word, re.IGNORECASE)

    @staticmethod
    def normalize(word):
        return u.normalize("NFD", word)

    def transliterate_word(self, word):
        word = self.clean_word(word).replace('’', "'")
        if self.is_cyr(word):
            return word

        clusters = split_into_clusters_with_softness(
            word, L_consonant_list, L_vowel_list
        )
        # print(f"{word=}, {clusters=}")
        res = ''.join(self.transliterate_clusters(clusters))
        self.is_cyr(res)
        res_normalized = self.normalize(res)
        self.is_cyr(res_normalized)
        return res_normalized


    def transliterate_text(self, text):
        parts = []
        for token in self.split_text(text):
            if re.match(r'^[\w\'’\u0300-\u036F]+$', token):
                parts.append(self.transliterate_word(token))
            else:
                parts.append(token)
        return ''.join(parts)
    

if __name__ == "__main__":
    tr = SaamiTransliterator()

    tests = [
        "значит я оусский",
        "ва̄ррь", *LONGS, *LONGS_SOFT,
        "n'es't'eres'	l'eev	kudd		al'k'",
        "iiǯ'	l'ii	lɨhke		laaš'š'k'",
        "a	suelne	l'ii		vaajmel'",
        "ejj		t'iid'		kooxxt	tenn		kud'd'		al'k' pajne",
        "nu	vot	tel'	i	vaan'n'c'el'		kuppce",
        "meene	kuppce	ja	kaaǯ'		rɒbot",
        "an't'		c'aal̥l̥k	mɨn'n'e	rɒbot",
        "a	kupec	c'aal̥l̥k	meenn	toonn	algax roobxušše",
        "a	munn	c'aal̥l̥k	l'aa..		portnoj	l'aa c'aal̥l̥k,	maata	kuarre	c'aal̥l̥k	ɒɒssket'",
        "vɨjjl’em mɨjj    jeek’na    sijd’es’ čaar       paaj̥k’    gɒrre    ɒd’d’emvuajvaeel",
        "sijd’es’  m’iinet    pood’d’en    pravažat jeen’    až’    i  v’iil’j    tɒɒvvrež vuep’s’ej    i  mudda  oollme",
        "uccak", "uhce", "uhc'e", "jil'l'en'", "kab'b'er'", "lɨhk'e"
    ]

    for t in tests:
        print("Оригинал:", t)
        print("Транслит:", tr.transliterate_text(t), end="\n\n")
