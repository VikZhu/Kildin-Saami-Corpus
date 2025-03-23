import json
from pathlib import Path

from parse_text import parse_file
from make_pre_dict import process_json_file

# Парсинг файла
texts_dir = Path("./texts")

def parse_single_text(text_filename):
    parsed_data = parse_file(text_filename)

    output_filename_1 = "test_parse_text.json"
    output_filename_2 = "test_make_pre_dict.json"

    with open(output_filename_1, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
    
    print("parse 1 ok")
    process_json_file(output_filename_1, output_filename_2)
    print("parse 2 ok")

    for filename in (output_filename_1, output_filename_2):
        Path(filename).unlink()


for text_filename in texts_dir.iterdir():
    print(f"trying {text_filename}")
    parse_single_text(text_filename)