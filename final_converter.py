import re
import string

L_consonant_list = [
    'p','t','k','b','d','g','c','č','ʒ','ǯ','f','s','š','x','v','z','ž',
    'm','n','ɲ','ŋ','m̥','n̥','r','l','r̥','l̥'
]

L_vowel_list = ['i','ɨ','u','e','o','a','ɒ','j','j̥']



def split_into_clusters_with_softness(word, consonants, vowels):
    clusters = []
    i = 0
    n = len(word)

    while i < n:

        
        if (
            word[i] in consonants or
            (word[i] in {"'", "’"} and i + 1 < n and word[i + 1] in consonants)
        ):
            base = []
            soft = False

            while i < n and (word[i] in consonants or word[i] in {"'", "’"}):
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


class SaamiTransliterator:

    def __init__(self):

        self.vowel_map = {
            'aa': 'ā', 'a': 'а',
            'ii': 'ӣ', 'i': 'и',
            'uu': 'ӯ', 'u': 'у',
            'ee': 'э̄', 'e': 'э',
            'oo': 'ō', 'o': 'о',
            'ɨɨ': 'ы̄', 'ɨ': 'ы',
            'ɒɒ': 'оā', 'ɒ': 'оа',
            'j': 'й'
        }

        self.soft_vowel_map = {
            'ee': 'ē', 'e': 'е',
            'aa': 'я̄', 'a': 'я',
            'oo': 'ё̄', 'o': 'ё',
            'uu': 'ю̄', 'u': 'ю',
            'ɨɨ': 'ӣ', 'ɨ': 'и'
        }

        self.consonant_map = {
            'pp':'пп','p':'п',
            'tt':'тт','t':'т',
            'kk':'кк','k':'к',
            'bb':'бб','b':'б',
            'dd':'дд','d':'д',
            'gg':'гг','g':'г',
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
            'l̥l̥':'ӆӆ','l̥':'ӆ'
        }

        self.semi_soft_consonants = {'д', 'т'}

        self.punctuation = set(c for c in (string.punctuation + '«»—–−‐-‒–—―‖‗‘’‚‛“”„‟…') if c not in {"'", "’"}
)


    def clean_word(self, word):
        word = word.strip()
        while word and word[0] in self.punctuation:
            word = word[1:]
        while word and word[-1] in self.punctuation:
            word = word[:-1]
        return word


    def split_text(self, text):
        pattern = re.compile(r'([\w\'’]+|[^\w\'’]+)', re.UNICODE)
        return pattern.findall(text)


    def transliterate_clusters(self, clusters):
        result = []

        for i, (kind, base, soft) in enumerate(clusters):

            if kind == "C":
                cyr = base
                for k, v in sorted(self.consonant_map.items(), key=lambda x: -len(x[0])):
                    cyr = cyr.replace(k, v)

                if i == len(clusters) - 1 and soft:
                    if cyr and cyr[-1] in self.semi_soft_consonants:
                        cyr += 'ҍ'
                    else:
                        cyr += 'ь'


                result.append(cyr)

            else:  
                prev_soft = (
                    i > 0 and
                    clusters[i-1][0] == "C" and
                    clusters[i-1][2]
                )

                v = base
                if prev_soft:
                    for k, v2 in sorted(self.soft_vowel_map.items(), key=lambda x: -len(x[0])):
                        v = v.replace(k, v2)
                else:
                    for k, v2 in sorted(self.vowel_map.items(), key=lambda x: -len(x[0])):
                        v = v.replace(k, v2)

                result.append(v)

        return result


    def transliterate_word(self, word):
        word = self.clean_word(word).replace('’', "'")
        clusters = split_into_clusters_with_softness(
            word, L_consonant_list, L_vowel_list
        )
        return ''.join(self.transliterate_clusters(clusters))


    def transliterate_text(self, text):
        parts = []
        for token in self.split_text(text):
            if re.match(r'^[\w\'’]+$', token):
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
