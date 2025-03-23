import json

# Функция для преобразования одного элемента
def transform_data(data):
    key = list(data.keys())[0]
    lines = data[key]
    
    # Разделяем строки на слова
    words = lines[0].split()
    glosses = lines[1].split()
    
    if len(words) != len(glosses):
        # print('Они не умеют глоссировать!')
        raise ValueError('Они не умеют глоссировать!')
    
    # Создаем список словарей для слов и их значений
    word_list = [{"word": word.strip(','), "gloss": gloss.strip(',')} for word, gloss in zip(words, glosses)]
    
    # Формируем итоговый словарь
    transformed_data = {
        "translation": lines[2].strip(),
        "words": word_list
    }
    
    return transformed_data

# Функция для обработки всего JSON-файла
def process_json_file(input_file, output_file):
    # Чтение данных из исходного JSON-файла
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Преобразование каждого элемента
    transformed_data = {}
    for key, value in data.items():
        try:
            transformed_data[key] = transform_data({key: value})
        except ValueError as e:
            print(f"Ошибка в айтеме ({key}, {value})")
            raise e
    
    # Запись преобразованных данных в новый JSON-файл
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, ensure_ascii=False, indent=4)

# Пример использования
input_file = 'input.json'  # Путь к исходному JSON-файлу
output_file = 'output.json'  # Путь к новому JSON-файлу
process_json_file(input_file, output_file)