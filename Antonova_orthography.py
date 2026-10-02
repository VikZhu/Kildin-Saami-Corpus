A_vowel_list = [
    '\u0061',   # a
    '\u0101',   # ā
    '\u00E4',   # ä
    '\u0065',   # e
    '\u0113',   # ē	
    '\u0451',   # ё
    'ё̄',
    '\u0438',   # и
    '\u04E3',   # ӣ
    '\u043E',   # о
    '\u014D',   # ō
    '\u0443',   # у
    '\u04EF',   # ӯ
    '\u044B',   # ы
    'ы̄',        # ы̄
    '\u044D',   # э
    'э̄',        # э̄
    '\u04ED',   # ӭ
    '\u044E',   # ю
    'ю̄',        # ю̄
    '\u044F',   # я
    'я̄',        # я̄
     ]

A_consonant_list = [
    '\u0431',   # б
    '\u0432',   # в
    '\u0433',   # г
    '\u0434',   # д
    '\u0436',   # ж
    '\u0437',   # з
    '\u0439',   # й
    '\u043A',   # к
    '\u043B',   # л
    '\u04C6',   # ӆ
    '\u043C',   # м
    '\u04CE',   # ӎ
    '\u043D',   # н
    '\u04CA',   # ӊ
    '\u04C8',   # ӈ
    '\u043F',   # п
    '\u0440',   # р
    '\u048F',   # ҏ
    '\u0441',   # с
    '\u0442',   # т
    '\u0444',   # ф
    '\u0445',   # х
    '\u0446',   # ц
    '\u0447',   # ч
    '\u0448',   # ш
    '\u0449',   # щ
    '\u044A',   # ъ
    '\u044C',   # ь
    '\u048D'    # ҍ	
     ]

L_vowel_list = ['i', 'ɨ', 'u', 'e', 'o', 'a', 'ɒ', 'j̥', 'j']

L_consonant_list = ['p', 't', 'k', 'b', 'd', 'g', 'c', 'č', 'ʒ', 'ǯ', 'f', 's', 'š', 'x', 'v', 'z', 'ž', 'm', 'n', 'ɲ', 'ŋ', 'm̥', 'n̥', 'r', 'l', 'r̥', 'l̥', '\u0027', '\u2019']

dict_comp = {
    'i': '\u0438',
    'u': '\u0443',
    'e': '\u044D',
    'a': '\u0061',
    'o': '\u043E',
    'ɨ': '\u044B',
    'ɒ': '\u043E\u0061',
    'j̥': '\u0439',
    'j': '\u0439',
    'ii': '\u04E3',
    'uu': '\u04EF',
    'ee': 'э̄',
    'aa': '\u0101',
    'oo': '\u014D',
    'ɨɨ': 'ы̄',
    'ɒɒ': '\u043E\u0101',
    'ju': '\u044E',
    'juu': 'ю̄',
    'ja': '\u044F',
    'jaa': 'я̄',
    'je': '\u0065',
    'jee': '\u0113',
    'jo': '\u0451',
    'joo': 'ё̄',
    'p': '\u043F',
    't': '\u0442',
    'k': '\u043A',
    'b': '\u0431',
    'd': '\u0434',
    'g': '\u0433',
    'c': '\u0446',
    'č': '\u0447',
    'ʒ': '\u0436',
    'ǯ': '\u0434\u0436',
    'f': '\u0444',
    's': '\u0441',
    'š': '\u0448',
    'x': '\u0445',
    'v': '\u0432',
    'z': '\u0437',
    'ž': '\u0436',
    'm': '\u043C',
    'n': '\u043D',
    'ɲ': 'хуй',
    'ŋ': '\u04C8',
    'm̥': '\u04CE',
    'n̥': '\u04CA',
    'r': '\u0440',
    'l': '\u043B',
    'r̥': '\u048F',
    'l̥': '\u04C6'
    }


def split_into_clusters(word, consonants=L_consonant_list, vowels=L_vowel_list):

    word = word.lower()
    
    clusters = []
    i = 0
    n = len(word)

    looking_for_consonants = True if word[0] in consonants else False
    
    while i < n:
        current_cluster = []
        
        if looking_for_consonants:
            while i < n and word[i] in consonants:
                current_cluster.append(word[i])
                i += 1
            if current_cluster:
                clusters.append(''.join(current_cluster))

            looking_for_consonants = False

        else:
            while i < n and word[i] in vowels:
                current_cluster.append(word[i])
                i += 1

            if current_cluster:
                clusters.append(''.join(current_cluster))

            looking_for_consonants = True

        if i < n and not current_cluster:
            # looking_for_consonants = not looking_for_consonants
            print('mistake!!!')
    
    return clusters


def split_into_clusters_simple(word, consonants=L_consonant_list, vowels=L_vowel_list):

    word = word.lower()
    clusters = []
    n = len(word)
    i = 0
    
    while i < n:
        if word[i] in consonants:
            cluster = []
            while i < n and word[i] in consonants:
                cluster.append(word[i])
                i += 1
            clusters.append(''.join(cluster))
        else:
            cluster = []
            while i < n and word[i] in vowels:
                cluster.append(word[i])
                i += 1
            clusters.append(''.join(cluster))
    
    return clusters


text_example = "kaallas ja aakaj jiil’l’en’ jiil’l’en’"
a ="с'eel̥’l̥'k’-en' mann mɨjj-e ejj šaan't’ al'k-e. " \
"sɨjj-e šan't'-e al'k-e lahk’e-olma lahk’e-taall. " \
"voal't-e(j) s'irr-e(δ) paarn-a(j)n' vuejv-e(j)t’ rɒdd. aǯ-es' jenn-es’ moakks-en' moakks-en'. " \
"ja t’eeŋ'k pud'd-en'. sonn paarn-a men-e(j) jaavvr-a jordan. " \
"jus't'-e kukx-el'l'-e čaaʒ'-jell-e."

for word in text_example.split():
    print(split_into_clusters_simple(word))