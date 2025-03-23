import re
import json

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

def parse_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    data = {}
    i = 0
    while i < len(lines):
        # Ищем либо числовую метку (например, "2."), либо метку в скобках (например, "(1)")
        match = re.search(r'^(?:(\d+)\.|\((\d+)\))', lines[i])
        if not match:
            i += 1
            continue
        
        # Извлекаем номер предложения
        sentence_number = match.group(1) or match.group(2)
        
        # Очищаем строку от ненужных символов и извлекаем саамский текст
        saam = re.sub(r'^[^a-zA-Zа-яА-Яɒɨʎǯ̥ŋšɲčž…]*', '', lines[i]).strip()
        gloss = ''
        transl = ''
        i += 1
        
        # Читаем глоссы
        gloss = lines[i].strip()
        i += 1
        
        # Читаем продолжение саамского текста и глоссов, если они есть
        while i + 1 < len(lines) and not re.match(r'^(?:\d+\.|\(\d+\))', lines[i + 1]):
            saam += ' ' + lines[i].strip()
            i += 1
            gloss += ' ' + lines[i].strip()
            i += 1 
        
        # Читаем перевод
        transl = clean_string(lines[i])
        i += 1

        # Преобразуем капитель в нормальные заглавные буквы
        saam = anti_small_caps(saam)
        gloss = anti_small_caps(gloss)
        transl = anti_small_caps(transl)

        # Сохраняем данные в словарь
        data[sentence_number] = [
            saam.strip(),  # Саамский текст
            gloss.strip(),  # Глоссы
            transl.strip()  # Перевод
        ]
    return data

# Парсинг файла
parsed_data = parse_file('texts/kld_txt_Lehtiranta_3_kɒn’t’_moajnas.txt') #сюда подставлять название файла
output_file = 'input.json'

# Сохранение данных в JSON
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=4)

print(f"Данные сохранены в файл: {output_file}")