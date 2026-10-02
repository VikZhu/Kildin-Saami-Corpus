import re
import json

import unicodedata as ud

def clean_string(s):
    # Определяем все возможные кавычки (включая нестандартные)
    quotes = {'"', "'", '„', '‘', '’', '‹', '›', '“', '”', '❝', '❞', '❮', '❯', '〝', '〞', '`', '´'}
    
    # Удаляем пробелы, табуляции и невидимые символы с обоих концов строки
    s = s.strip(' \t\n\r\x0b\x0c')  # \n, \r, \x0b, \x0c — невидимые символы
    
    # Удаляем кавычки с начала строки, если они есть
    while len(s) > 0 and s[0] in quotes:
        s = s[1:]
    
    # Удаляем кавычки с конца строки, если они есть
    while len(s) > 0 and s[-1] in quotes:
        s = s[:-1]
    
    return s

def anti_small_caps(s):
    # Создаем таблицу перевода для капители
    small_caps_to_normal = str.maketrans({
        'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ꜰ': 'f', 'ɢ': 'g', 'ʜ': 'h', 'ɪ': 'i', 'ᴊ': 'j',
        'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p', 'ǫ': 'q', 'ʀ': 'r', 'ꜱ': 's', 'ᴛ': 't',
        'u': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'x': 'x', 'ʏ': 'y', 'ᴢ': 'z', 's': 's',
        'ᴬ': 'a', 'ᴮ': 'b', 'ᶜ': 'c', 'ᴰ': 'd', 'ᴱ': 'e', 'ᶠ': 'f', 'ᴳ': 'g', 'ᴴ': 'h', 'ᴵ': 'i', 'ᴶ': 'j',
        'ᴷ': 'k', 'ᴸ': 'l', 'ᴹ': 'm', 'ᴺ': 'n', 'ᴼ': 'o', 'ᴾ': 'p', 'ᵀ': 't', 'ᵁ': 'u', 'ᵂ': 'w'
    })
    
    # Применяем таблицу перевода к строке
    return s.translate(small_caps_to_normal)



def parse_file(file_path, number_regex=r'^(?:\s|\uFEFF)*(?:(\d+)\.|\((\d+)\))'):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    data = {}
    i = 0
    while i < len(lines):
        # if i > 10:
        #     break
        # print(i, lines[i])
        # Ищем либо числовую метку (например, "2."), либо метку в скобках (например, "(1)")
        # for j, symb in enumerate(lines[i]):
        #     if j >= 10:
        #         break
        #     print(symb, ord(symb), ud.name(symb, "<UNK>"))

        # TODO: maybe implement more robust matching
        match = re.search(number_regex, lines[i])
        if not match:
            i += 1
            continue
        # print("matched")
        
        # Извлекаем номер предложения
        sentence_number = match.group(1) or match.group(2)
        
        # Очищаем строку от ненужных символов и извлекаем саамский текст
        saam = re.sub(r'^[^a-zA-Zа-яА-Яɒɨʎǯ̥ŋšɲčž…]*', '', lines[i]).strip()
        # print("saam", saam)
        gloss = ''
        transl = ''
        i += 1
        
        # Читаем глоссы
        gloss = lines[i].strip()
        # print("gl", gloss)
        i += 1
        
        # Читаем продолжение саамского текста и глоссов, если они есть
        while i+1 < len(lines) and not re.search(number_regex, lines[i+1]):
            saam += ' ' + lines[i].strip()
            # print("saam+", lines[i])
            i += 1
            gloss += ' ' + lines[i].strip()
            # print("gl+", lines[i])
            i += 1
        
        # Читаем перевод
        print("tr", lines[i])
        transl = clean_string(lines[i])
        i += 1

        # Преобразуем капитель в нормальные заглавные буквы
        saam = anti_small_caps(saam)
        gloss = anti_small_caps(gloss)
        transl = anti_small_caps(transl)

        print(saam, gloss, transl, sep="\n\n")

        # Сохраняем данные в словарь
        data[sentence_number] = [
            saam.strip(),  # Саамский текст
            gloss.strip(),  # Глоссы
            transl.strip()  # Перевод
        ]
    return data

# Парсинг файла
parsed_data = parse_file('texts/kld_txt_Itkonen1931_8_page259.txt') #сюда подставлять название файла
output_file = 'kld_txt_Itkonen1931_8_page259.json'

# Сохранение данных в JSON
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=4)

print(f"Данные сохранены в файл: {output_file}")