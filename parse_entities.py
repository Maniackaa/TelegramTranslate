from pyrogram.enums import MessageEntityType
from pyrogram.types import MessageEntity

formats = {'bold': ('**', '**'),
           'italic': ('_', '_'),
           'underline': ('<u>', '</u>'),
           'strikethrough': ('~~', '~~'),
           'code': ('`', '`'),
           }


def from_u16(text: bytes) -> str:
    return text.decode('utf-16-le')


# returns index of a first non ws character in a string
def content_index(c: str) -> int:
    ret = 0
    for i in c:
        if not i.isspace():
            return ret
        ret += 1
    return -1


def partition_string(text: str) -> tuple:
    start = content_index(text)
    if start == -1:
        return (text, '', '')
    end = content_index(text[::-1])
    end = len(text) if end == -1 else len(text) - end
    return (text[:start], text[start:end], text[end:])


def parse_entities(text: bytes,
                   entities: list,
                   offset: int,
                   end: int) -> str:
    formatted_note = ''

    for entity_index, entity in enumerate(entities):
        entity_start = entity['offset'] * 2
        if entity_start < offset:
            continue
        if entity_start > offset:
            formatted_note += from_u16(text[offset:entity_start])
        offset = entity_end = entity_start + entity['length'] * 2

        format = entity['type']
        if format == 'pre':
            pre_content = from_u16(text[entity_start:entity_end])
            content_parts = partition_string(pre_content)
            formatted_note += '```'
            if (len(content_parts[0]) == 0 and
                    content_parts[1].find('\n') == -1):
                formatted_note += '\n'
            formatted_note += pre_content
            if content_parts[2].find('\n') == -1:
                formatted_note += '\n'
            formatted_note += '```'
            if (len(text) - entity_end < 2 or
                    from_u16(text[entity_end:entity_end + 2])[0] != '\n'):
                formatted_note += '\n'
            continue
        # parse nested entities for exampe: "**bold _italic_**
        sub_entities = [e for e in entities[entity_index + 1:] if e['offset'] * 2 < entity_end]
        parsed_entity = parse_entities(text, sub_entities, entity_start, entity_end)
        content_parts = partition_string(parsed_entity)
        content = content_parts[1]
        if format in formats:
            format_code = formats[format]
            formatted_note += content_parts[0]
            i = 0
            while i < len(content):
                index = content.find('\n\n', i)  # inline formatting acros paragraphs, need to split
                if index == -1:
                    formatted_note += format_code[0] + content[i:] + format_code[1]
                    break
                formatted_note += format_code[0] + content[i:index] + format_code[1]
                i = index
                while i < len(content) and content[i] == '\n':
                    formatted_note += '\n'
                    i += 1
            formatted_note += content_parts[2]
            continue
        if format == 'mention':
            formatted_note += f'{content_parts[0]}[{content}](https://t.me/{content[1:]}){content_parts[2]}'
            continue
        if format == 'text_link':
            formatted_note += f'{content_parts[0]}[{content}]({entity["url"]}){content_parts[2]}'
            continue
        # Not processed (makes no sense): url, hashtag, cashtag, bot_command, email, phone_number
        # Not processed (hard to visualize using Markdown): spoiler, text_mention, custom_emoji
        formatted_note += parsed_entity

    if offset < end:
        formatted_note += from_u16(text[offset:end])
    return formatted_note


def message_to_html(og_text, entities, cmd_offset=0):
    text = og_text
    entity_types = {
        MessageEntityType.BOLD: "b",
        MessageEntityType.ITALIC: "i",
        MessageEntityType.UNDERLINE: "u",
        MessageEntityType.STRIKETHROUGH: "s",
        MessageEntityType.CODE: "code",
        MessageEntityType.PRE: "pre",
        MessageEntityType.SPOILER: "spoiler",
    }
    last_end = 0
    counter = 0
    last_end_length = 0
    for e in entities:
        print(e)

        if e.type in entity_types:
            print(f'last_end: {last_end}, counter: {counter}, last_end_length: {last_end_length}')
            if last_end > e.offset:
                counter -= last_end_length
            tag = entity_types[e.type]
            text = text[:e.offset + counter - cmd_offset] + "<" + tag + ">" + text[
                                                                              e.offset + counter - cmd_offset:e.offset + e.length + counter - cmd_offset] + "</" + tag + ">" + text[
                                                                                                                                                                               e.offset + counter + e.length - cmd_offset:]
            counter += 5 + (len(tag) * 2)
            if last_end > e.offset:
                counter += last_end_length
            last_end_length = 3 + len(tag)
        elif e.type == MessageEntityType.TEXT_LINK and e.url and len(e.url) > 0:
            print("text_link")
            print(e)
            if last_end > e.offset:
                counter -= last_end_length
            url = e.url
            # text = text[:e.offset + counter - cmd_offset] + "".format(url) + text[
            #                                                                  e.offset + counter - cmd_offset:e.offset + e.length + counter - cmd_offset] + "" + text[
            #                                                                                                                                                     e.offset + counter + e.length - cmd_offset:]
            url_name = text[e.offset + counter: e.offset+e.length + counter]
            print(url_name)
            text = text[:e.offset + counter] + f'<a href="{url}">{url_name}</a>' + text[e.offset + e.length + counter:]
            counter += 15 + len(url)
            # if last_end > e.offset:
            #     counter += last_end_length
            last_end_length += 15

        elif e.type == "text_mention":
            if last_end > e.offset:
                counter -= last_end_length
            user = e.user
            url = "tg://user?id={}".format(user["id"])
            text = text[:e.offset + counter - cmd_offset] + "".format(url) + text[
                                                                             e.offset + counter - cmd_offset:e.offset + e.length + counter - cmd_offset] + "" + text[
                                                                                                                                                                e.offset + counter + e.length - cmd_offset:]
            counter += 15 + len(url)
            if last_end > e.offset:
                counter += last_end_length
            last_end_length = 4
        last_end = e.offset + e.length
    return text


import re

def replace_key(text1, text2):
    keys1 = re.findall(r'\{([^}]*)\}', text1)  # Находим ключи в первом тексте
    keys2 = re.findall(r'\{([^}]*)\}', text2)  # Находим ключи во втором тексте
    for key1, key2 in zip(keys1, keys2):
        text2 = text2.replace('{' + key2 + '}', '{' + key1 + '}')  # Заменяем ключи во втором тексте на соответствующие ключи из первого текста
    return text2

text1 = "Some text {six} with key {one} and {two}"
text2 = "Как{afaf}ой-то текст с ключом {один} и {два}"

result = replace_key(text1, text2)
print(result)  # Вывод: "Какой-то текст с ключом {one} и {two}"