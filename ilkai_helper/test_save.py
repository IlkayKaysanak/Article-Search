import json

def save_json_to_txt(json_data):
    try:
        file_path = 'C:/Users/BILGIISLEM-ILKAY/Desktop/articles.txt'
        with open(file_path, 'a', encoding='utf-8') as txt_file:
            json_string = json.dumps(json_data, ensure_ascii=False, indent=4)
            txt_file.write(json_string + "\n")
            txt_file.write("New Data\n")
        print("Success.")
    except Exception as e:
        print(f"Error!!!!!!!!!!!!!: {e}")