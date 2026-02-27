import re
import string

from utils import punct

L_consonant_list = [
    'p','t','k','b','d','g','c','č','ʒ','ǯ','f','s','š','x','v','z','ž',
    'm','n','ɲ','ŋ','m̥','n̥','r','l','r̥','l̥'
]

L_vowel_proper_list = ['i','ɨ','u','e','o','a','ɒ']
L_j_list = ['j','j̥']
L_vowel_list = L_vowel_proper_list + L_j_list

SOFTNESS_SYMBOLS = {"'", "’"}
ALLOWED_SYMBOLS_INSIDE = SOFTNESS_SYMBOLS | {"\u0325"}


def split_into_clusters_with_softness(word, consonants, vowels):
    clusters = []
    i = 0
    n = len(word)

    while i < n:
        print(word[i])
        if (
            word[i] in consonants or
            (word[i] in SOFTNESS_SYMBOLS and i + 1 < n and word[i + 1] in consonants)
        ):
            base = []
            soft = False

            while i < n and (word[i] in consonants or word[i] in SOFTNESS_SYMBOLS):
                if word[i] in {"'", "’"}:
                    soft = True
                else:
                    base.append(word[i])
                i += 1

            clusters.append(("C", "".join(base), soft))

        # === ГЛАСНЫЙ КЛАСТЕР ===
        elif word[i] in vowels:
            base = []
            while i < n and word[i] in vowels:
                base.append(word[i])
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
LONG_A_CYR = 'ā'
LONG_I_CYR = 'ӣ'
LONG_IE_CYR = 'ӭ̄'
LONG_U_CYR = 'ӯ'
LONG_E_CYR = 'э̄'
LONG_O_CYR = 'ō'
LONG_Y_CYR = 'ы̄'
LONG_O_DIPHT_CYR = 'оā'

YA_CYR = 'я'
YO_CYR = 'ё'
YU_CYR = 'ю'
YE_CYR = 'е'
LONG_YA_CYR = 'я̄'
LONG_YO_CYR = 'ё̄'
LONG_YU_CYR = 'ю̄'

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
            'ii': LONG_IE_CYR, 'i': Y_CYR, # тут нельзя просто заменить 
            'uu': LONG_U_CYR, 'u': U_CYR,
            'ee': LONG_E_CYR, 'e': E_CYR,
            'oo': LONG_O_CYR, 'o': O_CYR,
            'ɨɨ': LONG_Y_CYR, 'ɨ': Y_CYR,
            'ɒɒ': LONG_O_DIPHT_CYR, 'ɒ': O_DIPHT_CYR,
            'j': J_CYR,
        }

        self.soft_vowel_map = {
            'ee': LONG_E_CYR, 'e': E_CYR,
            'aa': LONG_YA_CYR, 'a': YA_CYR,
            'oo': LONG_YO_CYR, 'o': YO_CYR,
            'uu': LONG_YU_CYR, 'u': YU_CYR,
            'ɨɨ': LONG_I_CYR, 'ɨ': I_CYR,
            # потому что первый кластер, если он начинается с j, мы маркируем как мягкий
            'ja': YA_CYR, 'je': YE_CYR, 'ji': I_CYR,
            'ii': LONG_I_CYR, 'i': I_CYR,
        }

        print(self.vowel_map)
        print(self.soft_vowel_map)

        self.consonant_map = {
            'pp':'пп','p':'п',
            'tt':'тт','t':'т',
            'kk':'кк','k':'к',
            'bb':'бп','b':'б',
            'dd':'дт','d':'д',
            'gg':'гк','g':'г',
            'cc':'дц','c':'ц',
            'čč':'чч','č':'ч',
            'ǯ':'дж','ʒ':'ж',
            'ff':'фф','f':'ф',
            'ss':'сс','s':'с',
            'šš':'шш','š':'ш',
            'x':'х',
            'v':'в',
            'zz':'зз','z':'з',
            'žž':'жж','ž':'ж',
            'mm':'мм','m':'м',
            'nn':'нн','n':'н',
            'ɲɲ':'ннь','ɲ':'нь',
            'ŋŋ':'ӈӈ','ŋ':'ӈ',
            'm̥m̥':'ӎӎ','m̥':'ӎ',
            'n̥n̥':'ӊӊ','n̥':'ӊ',
            'rr':'рр','r':'р',
            'll':'лл','l':'л',
            'r̥r̥':'ҏҏ','r̥':'ҏ',
            'l̥l̥':'ӆӆ','l̥':'ӆ',
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

                if i == len(clusters) - 1 and soft:
                    if cyr and cyr[-1] in self.semi_soft_consonants:
                        if len(cyr) == 2:
                            cyr = cyr[0] + 'ҍ' + cyr[1]
                        else:
                            cyr += 'ҍ'
                    else:
                        cyr += 'ь'

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
                    )
                )

                v = base
                if prev_soft:
                    # нет j перед гласными в начале
                    # print(v)
                    pat = f"^j(?=[{''.join(L_vowel_proper_list)}]{'{2}'})"
                    v = re.sub(pat, "", v)
                    # print(v, pat)

                    for k, v2 in sorted(self.soft_vowel_map.items(), key=lambda x: -len(x[0])):
                        v = v.replace(k, v2)
                        # print(k, v2)
                else:
                    for k, v2 in sorted(self.vowel_map.items(), key=lambda x: -len(x[0])):
                        v = v.replace(k, v2)

                # print("result:", v)           

                result.append(v)
        return result


    def transliterate_word(self, word):
        print(word)
        word = self.clean_word(word).replace('’', "'")
        clusters = split_into_clusters_with_softness(
            word, L_consonant_list, L_vowel_list
        )
        return ''.join(self.transliterate_clusters(clusters))


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
        "kaallas ja aakaj jiil’l’en’ jiil’l’en’",
        "mann mɨjje ejj šaan't’ al'ke",
        "vɨjjl’em mɨjj    jeek’na    sijd’es’ čaar       paaj̥k’    gɒrre    ɒd’d’emvuajvaeel",
        "sijd’es’  m’iinet    pood’d’en    pravažat jeen’    až’    i  v’iil’j    tɒɒvvrež vuep’s’ej    i  mudda  oollme",
        "uccak", "uhce", "uhc'e"
    ]

    for t in tests:
        print("Оригинал:", t)
        print("Транслит:", tr.transliterate_text(t))
