def get_data_from_info_string(info: str) -> dict:
    # info:137:ru
    splitted = info.split(':')
    index = splitted[1]
    lang_code = splitted[2]
    return {
        'index': index,
        'lang_code': lang_code
    }


def get_info_string_from_message(text: str):
    split = text.split('\n')
    info_string = split[-1]
    if info_string.startswith('info:'):
        return info_string
